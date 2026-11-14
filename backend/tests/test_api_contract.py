"""Contract tests checking that API responses match Section 9 of the AgroOrbit plan."""

from unittest.mock import patch
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.models import (
    ClimateResponse,
    CropItem,
    HealthResponse,
    LocationItem,
    RecommendResponse,
)
from app.nasa_power import NasaPowerApiError

client = TestClient(app)


def test_get_health():
    """Verify GET /health matches contract."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    validated = HealthResponse(**data)
    assert validated.status == "ok"


def test_get_locations():
    """Verify GET /locations returns preset locations matching contract."""
    response = client.get("/locations")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1

    locations = [LocationItem(**item) for item in data]
    ids = [loc.id for loc in locations]
    assert "kano" in ids
    assert "kaduna" in ids


def test_get_crops():
    """Verify GET /crops returns crop library matching contract."""
    response = client.get("/crops")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1

    crops = [CropItem(**item) for item in data]
    crop_ids = [c.id for c in crops]
    assert "maize" in crop_ids
    assert "cowpea" in crop_ids
    for crop in crops:
        assert 0.0 <= crop.verified_share <= 1.0
        assert isinstance(crop.traits_summary, dict)


def test_get_climate_real_cached_data():
    """Verify GET /climate returns real computed indicators from cached NASA POWER data for Kano."""
    response = client.get("/climate?lat=12.0022&lon=8.5920")
    assert response.status_code == 200
    data = response.json()

    # Pydantic validation ensures exact contract conformance
    validated = ClimateResponse(**data)
    assert validated.location.lat == 12.0022
    assert validated.location.lon == 8.5920
    assert "Kano" in validated.location.label
    assert validated.data_quality.from_cache is True
    assert len(validated.monthly) == 12
    # Verify realistic Savanna season parameters
    assert 130 <= validated.season.onset_doy_median <= 180  # Late May to June
    assert 250 <= validated.season.cessation_doy_median <= 300  # Late Sept to October
    assert validated.season.length_days_median >= 90
    assert validated.season_rain_total.median_mm > 400
    assert validated.bare_field_window.basis == "proxy"


def test_get_climate_fallback_to_mock_when_nasa_and_cache_fail():
    """Verify GET /climate falls back to mock data only when NASA and cache both fail."""
    with patch("app.main.nasa_power_client.fetch_daily_data", side_effect=NasaPowerApiError("Network timeout")):
        response = client.get("/climate?lat=12.0022&lon=8.5920")
        assert response.status_code == 200
        data = response.json()

        validated = ClimateResponse(**data)
        assert validated.data_quality.from_cache is False
        assert "nasa_and_cache_failed_mock_fallback" in validated.data_quality.flags
        assert "Mock Fallback" in validated.location.label


def test_post_recommend_schema():
    """Verify POST /recommend returns >= 3 rotations, confidences, evidence, and trace."""
    request_payload = {
        "lat": 12.0,
        "lon": 8.5,
        "current_rotation": ["maize", "maize", "maize"],
        "soil": {
            "texture": "sandy",
            "drainage": "unknown",
            "organic_matter": "low",
            "water_source": "rain_fed",
            "slope": "unknown",
        },
        "priorities": {
            "water_saving": 5,
            "soil_health": 4,
            "erosion": 2,
            "market_preference": 3,
            "forage": 1,
            "resilience": 4,
        },
        "preferred_crops": ["maize", "groundnut"],
        "scenario": {"rainfall_change_pct": 0, "temperature_change_c": 0},
    }

    response = client.post("/recommend", json=request_payload)
    assert response.status_code == 200
    data = response.json()

    # Validate against RecommendResponse schema
    validated = RecommendResponse(**data)
    assert validated.overall_outcome in ["clear_leader", "similar_options", "no_clear_winner"]
    assert "AgroOrbit supports decisions" in validated.disclaimer

    # At least 3 rotations must be returned
    assert len(validated.rotations) >= 3

    # The existing rotation must be included
    existing = [r for r in validated.rotations if r.is_existing]
    assert len(existing) == 1
    assert existing[0].sequence == ["maize", "maize", "maize"]

    # Check distinct sequences
    sequences = [tuple(r.sequence) for r in validated.rotations]
    assert len(set(sequences)) == len(validated.rotations)

    # Validate detailed attributes of each recommendation card
    for rot in validated.rotations:
        assert rot.fit_category in ["strong", "moderate", "weak"]
        assert 0 <= rot.score <= 100
        assert rot.data_confidence.level in ["low", "medium", "high"]
        assert len(rot.data_confidence.reasons) > 0
        assert rot.knowledge_support.level in ["low", "medium", "high"]
        assert len(rot.knowledge_support.reasons) > 0
        assert len(rot.evidence) >= 1
        for ev in rot.evidence:
            assert ev.source in ["NASA POWER", "farmer input", "crop knowledge base"]
            assert ev.metric
            assert ev.value
            assert ev.meaning
        assert len(rot.benefits) >= 1
        assert len(rot.assumptions) >= 1
        assert len(rot.information_gaps) >= 1
        assert len(rot.risks_for_local_review) >= 1
        assert len(rot.review_recommended_by) >= 1
        assert rot.trace.algorithm_version
        assert rot.trace.climate_period
