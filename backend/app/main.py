"""Main FastAPI application entrypoint for AgroOrbit.

Provides endpoints for health checking, preset locations, crop knowledge summaries,
historical NASA climate indicators, and crop-rotation recommendations.
"""

from typing import List
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware

from app.config import CORS_ORIGINS
from app.mock_data import MOCK_CROPS, MOCK_LOCATIONS, get_mock_climate, get_mock_recommendations
from app.models import (
    ClimateResponse,
    CropItem,
    HealthResponse,
    LocationItem,
    RecommendRequest,
    RecommendResponse,
)

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


@app.get("/health", response_model=HealthResponse)
def health_check() -> HealthResponse:
    """Health check endpoint to verify backend service status."""
    return HealthResponse(status="ok")


@app.get("/locations", response_model=List[LocationItem])
def get_locations() -> List[LocationItem]:
    """Return preset demo locations for northern Nigeria and the Middle Belt."""
    return MOCK_LOCATIONS


@app.get("/crops", response_model=List[CropItem])
def get_crops() -> List[CropItem]:
    """Return catalog of supported crops with trait summaries and verification status."""
    return MOCK_CROPS


@app.get("/climate", response_model=ClimateResponse)
def get_climate(
    lat: float = Query(..., description="Latitude of the field point"),
    lon: float = Query(..., description="Longitude of the field point"),
) -> ClimateResponse:
    """Return NASA climate indicators for the specified point.

    NOTE: Phase 1 returns realistic mock data. NASA POWER integration follows in Phase 2.
    """
    return get_mock_climate(lat=lat, lon=lon)


@app.post("/recommend", response_model=RecommendResponse)
def recommend_rotations(payload: RecommendRequest) -> RecommendResponse:
    """Evaluate and compare at least 3 crop-rotation strategies against climate indicators.

    NOTE: Phase 1 returns realistic mock data. Rule-based scoring engine follows in Phase 4.
    """
    return get_mock_recommendations(payload)
