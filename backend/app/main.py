"""Main FastAPI application entrypoint for AgroOrbit.

Provides endpoints for health checking, preset locations, crop knowledge summaries,
historical NASA climate indicators, and crop-rotation recommendations.
"""

import logging
from typing import List, Optional
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware

from app.climate import compute_climate_summary
from app.config import CORS_ORIGINS
from app.knowledge import get_crops_api_summary, load_locations
from app.mock_data import get_mock_climate, get_mock_recommendations
from app.models import (
    ClimateResponse,
    CropItem,
    HealthResponse,
    LocationItem,
    RecommendRequest,
    RecommendResponse,
)
from app.nasa_power import NasaPowerClient

logger = logging.getLogger(__name__)

app = FastAPI(
    title="AgroOrbit API",
    description="Decision-support web tool for crop-rotation strategies using NASA Earth observations.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Persistent client instance (uses CACHE_DIR automatically)
nasa_power_client = NasaPowerClient()


def find_preset_location_label(lat: float, lon: float) -> Optional[str]:
    """Finds if given coordinates correspond closely to a preset demo location."""
    for loc in load_locations():
        if abs(loc.lat - lat) < 0.25 and abs(loc.lon - lon) < 0.25:
            return f"{loc.name} ({loc.zone})"
    return None


@app.get("/health", response_model=HealthResponse)
def health_check() -> HealthResponse:
    """Health check endpoint to verify backend service status."""
    return HealthResponse(status="ok")


@app.get("/locations", response_model=List[LocationItem])
def get_locations() -> List[LocationItem]:
    """Return preset demo locations for northern Nigeria and the Middle Belt."""
    return load_locations()


@app.get("/crops", response_model=List[CropItem])
def get_crops() -> List[CropItem]:
    """Return catalog of supported crops with trait summaries and verification status."""
    return get_crops_api_summary()


@app.get("/climate", response_model=ClimateResponse)
def get_climate(
    lat: float = Query(..., description="Latitude of the field point"),
    lon: float = Query(..., description="Longitude of the field point"),
) -> ClimateResponse:
    """Return real NASA climate indicators for the specified point.

    Falls back to mock data only when both NASA POWER API and local cache fail.
    """
    preset_label = find_preset_location_label(lat, lon)
    label = preset_label or f"Coordinates ({lat:.2f}, {lon:.2f})"

    try:
        # Fetch real daily data from NASA POWER or local disk cache
        df, meta = nasa_power_client.fetch_daily_data(lat=lat, lon=lon)
        return compute_climate_summary(
            df=df,
            lat=lat,
            lon=lon,
            location_label=label,
            from_cache=meta.get("from_cache", False),
            missing_pct=meta.get("overall_missing_pct", 0.0),
            flags=meta.get("quality_flags", []),
        )
    except Exception as e:
        logger.warning(
            f"Failed to fetch live NASA POWER data or cache for ({lat}, {lon}): {e}. "
            "Falling back to mock data."
        )
        fallback = get_mock_climate(lat=lat, lon=lon)
        fallback.data_quality.flags.append("nasa_and_cache_failed_mock_fallback")
        fallback.data_quality.from_cache = False
        if preset_label:
            fallback.location.label = f"{preset_label} (Mock Fallback)"
        return fallback


@app.post("/recommend", response_model=RecommendResponse)
def recommend_rotations(payload: RecommendRequest) -> RecommendResponse:
    """Evaluate and compare at least 3 crop-rotation strategies against climate indicators.

    NOTE: Phase 1 returns realistic mock data. Rule-based scoring engine follows in Phase 4.
    """
    return get_mock_recommendations(payload)
