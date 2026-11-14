"""Tests for nasa_power.py using saved fixtures and mocked requests (no live calls)."""

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import numpy as np
import pandas as pd
import pytest

from app.nasa_power import (
    NasaPowerApiError,
    NasaPowerClient,
    NasaPowerParsingError,
    generate_cache_key,
    get_default_record_range,
    parse_power_response,
    read_from_cache,
    round_to_grid,
    write_to_cache,
)

FIXTURES_DIR = Path(__file__).parent / "fixtures"
SAMPLE_RESPONSE_PATH = FIXTURES_DIR / "sample_power_response.json"


@pytest.fixture
def sample_response_json():
    """Loads saved small sample NASA POWER response."""
    with open(SAMPLE_RESPONSE_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def test_round_to_grid():
    """Verify coordinate rounding to documented 0.25 degree grid."""
    assert round_to_grid(12.01, 0.25) == 12.0
    assert round_to_grid(12.13, 0.25) == 12.25
    assert round_to_grid(8.48, 0.25) == 8.5
    assert round_to_grid(8.63, 0.25) == 8.75


def test_get_default_record_range():
    """Verify date range starts at START_YEAR (1991) and ends at last complete calendar year."""
    start, end = get_default_record_range(reference_year=2026)
    assert start == "19910101"
    assert end == "20251231"
    # Never include current year
    assert "2026" not in end


def test_generate_cache_key_determinism():
    """Verify cache key includes rounded lat/lon, sorted params, dates, community, and time-standard."""
    params_a = ["T2M", "PRECTOTCORR", "GWETTOP"]
    params_b = ["PRECTOTCORR", "GWETTOP", "T2M"]

    key_a = generate_cache_key(
        lat=12.02, lon=8.49, parameters=params_a, start="19910101", end="20251231"
    )
    key_b = generate_cache_key(
        lat=12.00, lon=8.50, parameters=params_b, start="19910101", end="20251231"
    )

    # Identical rounded coords (12.00, 8.50) and permuted params must yield exact same key
    assert key_a == key_b
    assert "19910101" in key_a
    assert "20251231" in key_a
    assert "AG" in key_a
    assert "UTC" in key_a


def test_parse_power_response_replaces_fill_with_nan(sample_response_json):
    """CRITICAL: -999.0 must be converted to NaN and NEVER to 0.0."""
    df, meta = parse_power_response(sample_response_json)

    assert isinstance(df, pd.DataFrame)
    assert len(df) == 5
    assert "PRECTOTCORR" in df.columns
    assert "T2M" in df.columns

    # Check normal valid day
    assert df.loc["2023-06-01", "PRECTOTCORR"] == 0.15
    assert df.loc["2023-06-01", "T2M"] == 31.68

    # Day 2023-06-03 had -999.0 in fixture
    precip_missing = df.loc["2023-06-03", "PRECTOTCORR"]
    t2m_missing = df.loc["2023-06-03", "T2M"]

    assert np.isnan(precip_missing), "-999.0 was not converted to NaN!"
    assert precip_missing != 0.0, "-999.0 was erroneously converted to 0.0!"
    assert np.isnan(t2m_missing), "-999.0 was not converted to NaN!"
    assert t2m_missing != 0.0

    # Check that a true 0.0 value (2023-06-05) remains 0.0
    assert df.loc["2023-06-05", "PRECTOTCORR"] == 0.0

    # Check missing data metadata tracking
    assert meta["overall_missing_pct"] > 0.0
    assert meta["missing_per_param"]["PRECTOTCORR"]["missing_days"] == 1
    assert meta["missing_per_param"]["T2M"]["missing_days"] == 1


def test_cache_read_write(tmp_path, sample_response_json):
    """Verify cache writing and reading with timestamp and raw response."""
    cache_key = "test_key_123"
    written_path = write_to_cache(cache_key, sample_response_json, cache_dir=tmp_path)
    assert written_path.exists()

    loaded = read_from_cache(cache_key, cache_dir=tmp_path)
    assert loaded is not None
    assert loaded["cache_key"] == cache_key
    assert "fetch_timestamp" in loaded
    assert loaded["raw_response"] == sample_response_json


def test_client_fetch_from_cache(tmp_path, sample_response_json):
    """When cache is present, NasaPowerClient must NOT make any network request."""
    cache_key = generate_cache_key(
        lat=12.0,
        lon=8.5,
        parameters=["PRECTOTCORR", "T2M"],
        start="20230601",
        end="20230605",
    )
    write_to_cache(cache_key, sample_response_json, cache_dir=tmp_path)

    client = NasaPowerClient(cache_dir=tmp_path)

    # Patch httpx to ensure no HTTP call is made
    with patch("httpx.Client.get") as mock_get:
        df, meta = client.fetch_daily_data(
            lat=12.0,
            lon=8.5,
            parameters=["PRECTOTCORR", "T2M"],
            start="20230601",
            end="20230605",
        )
        mock_get.assert_not_called()
        assert meta["from_cache"] is True
        assert len(df) == 5


def test_client_fetch_live_mocked_success(tmp_path, sample_response_json):
    """When cache is missing, client fetches over network (mocked) and saves to cache."""
    client = NasaPowerClient(cache_dir=tmp_path)

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = sample_response_json

    with patch("httpx.Client.get", return_value=mock_resp):
        df, meta = client.fetch_daily_data(
            lat=12.0,
            lon=8.5,
            parameters=["PRECTOTCORR", "T2M"],
            start="20230601",
            end="20230605",
        )
        assert meta["from_cache"] is False
        assert len(df) == 5

        # Check that it was saved to cache
        cache_key = meta["cache_key"]
        cached = read_from_cache(cache_key, cache_dir=tmp_path)
        assert cached is not None


def test_client_fetch_fallback_to_cache_on_failure(tmp_path, sample_response_json):
    """When live call fails after retries, client falls back to existing cache."""
    cache_key = generate_cache_key(
        lat=12.0,
        lon=8.5,
        parameters=["PRECTOTCORR", "T2M"],
        start="20230601",
        end="20230605",
    )
    write_to_cache(cache_key, sample_response_json, cache_dir=tmp_path)

    client = NasaPowerClient(cache_dir=tmp_path, max_retries=1)

    mock_resp = MagicMock()
    mock_resp.status_code = 503
    mock_resp.text = "NASA POWER Service Unavailable"

    with patch("httpx.Client.get", return_value=mock_resp), patch("time.sleep"):
        df, meta = client.fetch_daily_data(
            lat=12.0,
            lon=8.5,
            parameters=["PRECTOTCORR", "T2M"],
            start="20230601",
            end="20230605",
            force_refresh=True,  # Force it to attempt network
        )
        assert meta["from_cache"] is True
        assert meta["cached_fallback"] is True
        assert "network_failed_fallback_to_cache" in meta["quality_flags"]


def test_client_raises_error_when_no_cache_and_network_fails(tmp_path):
    """When live call fails and there is no cache, NasaPowerApiError is raised."""
    client = NasaPowerClient(cache_dir=tmp_path, max_retries=1)

    mock_resp = MagicMock()
    mock_resp.status_code = 500
    mock_resp.text = "Internal Server Error"

    with patch("httpx.Client.get", return_value=mock_resp), patch("time.sleep"):
        with pytest.raises(NasaPowerApiError) as exc_info:
            client.fetch_daily_data(
                lat=12.0,
                lon=8.5,
                parameters=["PRECTOTCORR"],
                start="20230601",
                end="20230605",
            )
        assert "Failed to fetch data from NASA POWER" in str(exc_info.value)
