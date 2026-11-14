"""Client for fetching, caching, and handling NASA POWER daily agroclimatology data.

Strictly adheres to Section 6.1 of AGROORBIT_PLAN_v2.md:
- Endpoint: NASA POWER daily point API (community=AG, time-standard=UTC)
- Robustness: Timeouts, 2 retries with exponential backoff, cache fallback
- Missing data: -999 / -999.0 converted to NaN (never zero)
- Cache key: includes rounded lat/lon (0.25° grid), sorted parameters, start, end,
  community, and time-standard. Stores raw response and fetch timestamp.
- Default record: 1991 to the last complete calendar year (>= 30 years).
"""

from datetime import datetime, timezone
import hashlib
import json
import logging
from pathlib import Path
import time
from typing import Any, Dict, List, Optional, Tuple

import httpx
import numpy as np
import pandas as pd

from app.config import (
    CACHE_DIR,
    GRID_RESOLUTION_DEG,
    NASA_POWER_BASE_URL,
    NASA_POWER_COMMUNITY,
    NASA_POWER_DEFAULT_PARAMS,
    NASA_POWER_FILL_VALUE,
    NASA_POWER_MAX_RETRIES,
    NASA_POWER_RETRY_BACKOFF_FACTOR,
    NASA_POWER_TIMEOUT_SECONDS,
    NASA_POWER_TIME_STANDARD,
    START_YEAR,
)

logger = logging.getLogger(__name__)


class NasaPowerError(Exception):
    """Base exception for NASA POWER API interactions."""
    pass


class NasaPowerApiError(NasaPowerError):
    """Raised when the NASA POWER API returns an error or request fails."""
    pass


class NasaPowerParsingError(NasaPowerError):
    """Raised when parsing or cleaning NASA POWER response fails."""
    pass


def round_to_grid(coord: float, resolution: float = GRID_RESOLUTION_DEG) -> float:
    """Rounds coordinates to the nearest documented spatial grid resolution (default 0.25 deg)."""
    return round(round(coord / resolution) * resolution, 4)


def get_default_record_range(reference_year: Optional[int] = None) -> Tuple[str, str]:
    """Computes the default date range from START_YEAR (1991) to last complete calendar year.

    Never includes the current incomplete calendar year.
    """
    if reference_year is None:
        reference_year = datetime.now(timezone.utc).year
    end_year = reference_year - 1
    start_date = f"{START_YEAR}0101"
    end_date = f"{end_year}1231"
    return start_date, end_date


def generate_cache_key(
    lat: float,
    lon: float,
    parameters: List[str],
    start: str,
    end: str,
    community: str = NASA_POWER_COMMUNITY,
    time_standard: str = NASA_POWER_TIME_STANDARD,
    grid_resolution: float = GRID_RESOLUTION_DEG,
) -> str:
    """Generates a deterministic cache key string based on query parameters.

    Key includes:
    - Rounded lat & lon (nearest grid resolution)
    - Sorted parameter list
    - start and end dates
    - community and time_standard
    """
    grid_lat = round_to_grid(lat, grid_resolution)
    grid_lon = round_to_grid(lon, grid_resolution)
    sorted_params = sorted(parameters)
    params_str = ",".join(sorted_params)

    # Hash the params string to keep filename manageable while perfectly deterministic
    params_hash = hashlib.sha256(params_str.encode("utf-8")).hexdigest()[:12]

    # Deterministic file name
    return f"power_lat{grid_lat:+.4f}_lon{grid_lon:+.4f}_{start}_{end}_{community}_{time_standard}_{params_hash}"


def get_cache_file_path(cache_key: str, cache_dir: Path = CACHE_DIR) -> Path:
    """Returns absolute file path for a cache key."""
    return cache_dir / f"{cache_key}.json"


def read_from_cache(cache_key: str, cache_dir: Path = CACHE_DIR) -> Optional[Dict[str, Any]]:
    """Reads and returns cached JSON payload if present, else None."""
    file_path = get_cache_file_path(cache_key, cache_dir)
    if not file_path.exists():
        return None

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data
    except Exception as e:
        logger.warning(f"Failed reading cache file {file_path}: {e}")
        return None


def write_to_cache(
    cache_key: str,
    raw_response: Dict[str, Any],
    cache_dir: Path = CACHE_DIR,
) -> Path:
    """Writes raw NASA POWER response and metadata to disk cache."""
    cache_dir.mkdir(parents=True, exist_ok=True)
    file_path = get_cache_file_path(cache_key, cache_dir)

    payload = {
        "cache_key": cache_key,
        "fetch_timestamp": datetime.now(timezone.utc).isoformat(),
        "raw_response": raw_response,
    }

    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)

    return file_path


def parse_power_response(raw_json: Dict[str, Any]) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """Parses raw NASA POWER response into a cleaned pandas DataFrame and metadata.

    MANDATORY RULES (Section 6.1):
    - Values live under properties.parameter.<NAME>.<YYYYMMDD>
    - -999 / -999.0 MUST be converted to NaN (never converted to 0)
    - missing_pct calculated per parameter and overall
    """
    props = raw_json.get("properties", {})
    parameters_data = props.get("parameter", {})
    if not parameters_data:
        raise NasaPowerParsingError("NASA POWER response contains no 'properties.parameter' data.")

    # Convert nested dict {PARAM: {YYYYMMDD: val}} to DataFrame
    df = pd.DataFrame(parameters_data)
    if df.empty:
        raise NasaPowerParsingError("Extracted parameter data is empty.")

    # Convert index (YYYYMMDD strings) to DatetimeIndex
    df.index = pd.to_datetime(df.index, format="%Y%m%d")
    df = df.sort_index()

    # Convert columns to float and replace NASA fill values with NaN
    # Header fill value from response if available, falling back to constant
    header_fill = float(raw_json.get("header", {}).get("fill_value", NASA_POWER_FILL_VALUE))

    # CRITICAL: -999.0 -> np.nan (NEVER 0.0)
    for col in df.columns:
        df[col] = pd.to_numeric(df[col], errors="coerce")
        df.loc[df[col] == header_fill, col] = np.nan
        df.loc[df[col] == NASA_POWER_FILL_VALUE, col] = np.nan

    # Calculate data quality metrics
    total_slots = df.shape[0] * df.shape[1]
    total_missing = int(df.isna().sum().sum())
    overall_missing_pct = round((total_missing / total_slots) * 100, 2) if total_slots > 0 else 0.0

    missing_per_param = {}
    for col in df.columns:
        col_missing = int(df[col].isna().sum())
        missing_per_param[col] = {
            "missing_days": col_missing,
            "missing_pct": round((col_missing / len(df)) * 100, 2) if len(df) > 0 else 0.0,
        }

    flags = []
    if overall_missing_pct > 10.0:
        flags.append("high_missing_data")

    metadata = {
        "start_date": df.index.min().strftime("%Y-%m-%d"),
        "end_date": df.index.max().strftime("%Y-%m-%d"),
        "total_days": len(df),
        "overall_missing_pct": overall_missing_pct,
        "missing_per_param": missing_per_param,
        "quality_flags": flags,
        "parameters": list(df.columns),
    }

    return df, metadata


class NasaPowerClient:
    """Client for fetching and caching NASA POWER daily data."""

    def __init__(
        self,
        base_url: str = NASA_POWER_BASE_URL,
        timeout: float = NASA_POWER_TIMEOUT_SECONDS,
        max_retries: int = NASA_POWER_MAX_RETRIES,
        cache_dir: Path = CACHE_DIR,
    ):
        self.base_url = base_url
        self.timeout = timeout
        self.max_retries = max_retries
        self.cache_dir = cache_dir

    def fetch_daily_data(
        self,
        lat: float,
        lon: float,
        parameters: Optional[List[str]] = None,
        start: Optional[str] = None,
        end: Optional[str] = None,
        force_refresh: bool = False,
    ) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """Fetches daily data for a point location, with caching, retries, and fallback.

        Returns:
            Tuple of (cleaned_df, metadata_dict)
            metadata_dict includes 'from_cache' (bool) and 'cached_fallback' (bool).
        """
        if parameters is None:
            parameters = list(NASA_POWER_DEFAULT_PARAMS)
        if start is None or end is None:
            default_start, default_end = get_default_record_range()
            start = start or default_start
            end = end or default_end

        cache_key = generate_cache_key(
            lat=lat,
            lon=lon,
            parameters=parameters,
            start=start,
            end=end,
            community=NASA_POWER_COMMUNITY,
            time_standard=NASA_POWER_TIME_STANDARD,
        )

        # 1. Check disk cache
        if not force_refresh:
            cached_entry = read_from_cache(cache_key, self.cache_dir)
            if cached_entry and "raw_response" in cached_entry:
                df, meta = parse_power_response(cached_entry["raw_response"])
                meta["from_cache"] = True
                meta["fetch_timestamp"] = cached_entry.get("fetch_timestamp")
                meta["cache_key"] = cache_key
                return df, meta

        # 2. Live HTTP request with retries
        query_params = {
            "parameters": ",".join(parameters),
            "community": NASA_POWER_COMMUNITY,
            "longitude": lon,
            "latitude": lat,
            "start": start,
            "end": end,
            "format": "JSON",
            "time-standard": NASA_POWER_TIME_STANDARD,
        }

        raw_response = None
        last_exception = None

        for attempt in range(self.max_retries + 1):
            try:
                with httpx.Client(timeout=self.timeout) as client:
                    resp = client.get(self.base_url, params=query_params)
                    if resp.status_code == 200:
                        raw_response = resp.json()
                        break
                    else:
                        logger.warning(
                            f"NASA POWER attempt {attempt + 1} returned status {resp.status_code}: {resp.text[:200]}"
                        )
                        last_exception = NasaPowerApiError(
                            f"HTTP {resp.status_code}: {resp.text[:200]}"
                        )
            except Exception as e:
                logger.warning(f"NASA POWER attempt {attempt + 1} failed with exception: {e}")
                last_exception = e

            if attempt < self.max_retries:
                backoff = NASA_POWER_RETRY_BACKOFF_FACTOR * (2 ** attempt)
                time.sleep(backoff)

        # 3. Handle success or fallback to cache
        if raw_response:
            write_to_cache(cache_key, raw_response, self.cache_dir)
            df, meta = parse_power_response(raw_response)
            meta["from_cache"] = False
            meta["cache_key"] = cache_key
            meta["fetch_timestamp"] = datetime.now(timezone.utc).isoformat()
            return df, meta

        # If live call failed, check if ANY cache is available as fallback
        cached_fallback = read_from_cache(cache_key, self.cache_dir)
        if cached_fallback and "raw_response" in cached_fallback:
            logger.warning(f"Live fetch failed ({last_exception}); falling back to cache.")
            df, meta = parse_power_response(cached_fallback["raw_response"])
            meta["from_cache"] = True
            meta["cached_fallback"] = True
            meta["fetch_timestamp"] = cached_fallback.get("fetch_timestamp")
            meta["quality_flags"].append("network_failed_fallback_to_cache")
            return df, meta

        raise NasaPowerApiError(
            f"Failed to fetch data from NASA POWER after {self.max_retries + 1} attempts, and no cache available. Error: {last_exception}"
        )
