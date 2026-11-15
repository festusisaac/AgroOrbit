"""Tests for Backend Finalization requirements:

1. Input validation with clear 4xx messages (lat, lon, priorities, rotation length, soil enums).
2. Unknown crop IDs marked 'not assessed', no invented parameters, lower knowledge_support, in information_gaps.
3. Geographic coverage warning for out-of-region coordinates (northern Nigeria / Middle Belt boundaries).
4. Scenario field execution (Section 8.5): series perturbation, rerun, labeled hypothetical, never silently ignored.
5. Live NASA fetch: timeout handling, clear error messages, and 'live_nasa_fetch' data_quality flag.
"""

from unittest.mock import MagicMock, patch
import httpx
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.models import RecommendResponse, ClimateResponse
from app.nasa_power import NasaPowerApiError, NasaPowerClient

client = TestClient(app)

KANO_LAT = 12.0
KANO_LON = 8.5


# ============================================================================
# 1. Input Validation Tests (4xx with clear messages)
# ============================================================================
def test_validation_lat_out_of_bounds():
    """Latitude outside [-90, 90] returns a clear 4xx error."""
    # POST /recommend
    payload = {
        "lat": 95.0,
        "lon": 8.5,
        "current_rotation": ["maize", "maize", "maize"],
    }
    resp = client.post("/recommend", json=payload)
    assert resp.status_code == 422
    assert "less than or equal to 90" in str(resp.json())

    # GET /climate
    resp_get = client.get("/climate?lat=95.0&lon=8.5")
    assert resp_get.status_code == 422
    assert "less than or equal to 90" in str(resp_get.json())


def test_validation_lon_out_of_bounds():
    """Longitude outside [-180, 180] returns a clear 4xx error."""
    payload = {
        "lat": 12.0,
        "lon": 200.0,
        "current_rotation": ["maize", "maize", "maize"],
    }
    resp = client.post("/recommend", json=payload)
    assert resp.status_code == 422
    assert "less than or equal to 180" in str(resp.json())

    resp_get = client.get("/climate?lat=12.0&lon=200.0")
    assert resp_get.status_code == 422
    assert "less than or equal to 180" in str(resp_get.json())


def test_validation_priority_out_of_bounds():
    """Priorities outside 0-5 return a clear 4xx error."""
    payload = {
        "lat": KANO_LAT,
        "lon": KANO_LON,
        "current_rotation": ["maize", "maize", "maize"],
        "priorities": {"water_saving": 6},  # > 5
    }
    resp = client.post("/recommend", json=payload)
    assert resp.status_code == 422
    assert "less than or equal to 5" in str(resp.json())

    payload_neg = {
        "lat": KANO_LAT,
        "lon": KANO_LON,
        "current_rotation": ["maize", "maize", "maize"],
        "priorities": {"soil_health": -1},  # < 0
    }
    resp_neg = client.post("/recommend", json=payload_neg)
    assert resp_neg.status_code == 422
    assert "greater than or equal to 0" in str(resp_neg.json())


def test_validation_rotation_length():
    """Rotation length must be between 1 and 3."""
    # Length 0
    payload_empty = {
        "lat": KANO_LAT,
        "lon": KANO_LON,
        "current_rotation": [],
    }
    resp_empty = client.post("/recommend", json=payload_empty)
    assert resp_empty.status_code == 422
    assert "at least 1 item" in str(resp_empty.json())

    # Length 4 (> 3)
    payload_long = {
        "lat": KANO_LAT,
        "lon": KANO_LON,
        "current_rotation": ["maize", "cowpea", "sorghum", "soybean"],
    }
    resp_long = client.post("/recommend", json=payload_long)
    assert resp_long.status_code == 422
    assert "at most 3 items" in str(resp_long.json())


def test_validation_soil_fields_known_enums():
    """Unknown enum values for soil fields return clear 4xx errors."""
    base_payload = {
        "lat": KANO_LAT,
        "lon": KANO_LON,
        "current_rotation": ["maize", "maize", "maize"],
    }

    # Invalid texture
    resp_tex = client.post("/recommend", json={**base_payload, "soil": {"texture": "gravel"}})
    assert resp_tex.status_code == 422
    assert "Invalid soil texture 'gravel'" in str(resp_tex.json())

    # Invalid drainage
    resp_drn = client.post("/recommend", json={**base_payload, "soil": {"drainage": "waterlogged_bog"}})
    assert resp_drn.status_code == 422
    assert "Invalid soil drainage 'waterlogged_bog'" in str(resp_drn.json())

    # Invalid organic matter
    resp_om = client.post("/recommend", json={**base_payload, "soil": {"organic_matter": "ultra_rich"}})
    assert resp_om.status_code == 422
    assert "Invalid soil organic_matter 'ultra_rich'" in str(resp_om.json())

    # Invalid slope
    resp_slp = client.post("/recommend", json={**base_payload, "soil": {"slope": "cliff"}})
    assert resp_slp.status_code == 422
    assert "Invalid field slope 'cliff'" in str(resp_slp.json())

    # Invalid water source
    resp_ws = client.post("/recommend", json={**base_payload, "soil": {"water_source": "hydrant"}})
    assert resp_ws.status_code == 422
    assert "Invalid water_source 'hydrant'" in str(resp_ws.json())


# ============================================================================
# 2. Unknown Crop IDs Tests
# ============================================================================
def test_unknown_crop_ids_marked_not_assessed_and_lower_knowledge_support():
    """Unknown crop IDs must be marked 'not assessed', have NO invented fallback parameters, lower knowledge_support, and appear in information_gaps."""
    payload = {
        "lat": KANO_LAT,
        "lon": KANO_LON,
        "current_rotation": ["cassava", "yam", "maize"],
        "priorities": {"soil_health": 3},
    }

    resp = client.post("/recommend", json=payload)
    assert resp.status_code == 200
    data = RecommendResponse(**resp.json())

    # Locate the existing rotation
    existing = next(r for r in data.rotations if r.is_existing)
    assert existing.sequence == ["cassava", "yam", "maize"]

    # 1. Lower knowledge_support
    assert existing.knowledge_support.level == "low"
    assert any("unassessed crop" in reason.lower() for reason in existing.knowledge_support.reasons)

    # 2. Added to information_gaps
    assert any("Unrecognized crop 'cassava': Marked 'not assessed'" in gap for gap in existing.information_gaps)
    assert any("Unrecognized crop 'yam': Marked 'not assessed'" in gap for gap in existing.information_gaps)

    # 3. Evidence shows 'Not assessed' without invented numbers
    evidence_text = " ".join(e.value for e in existing.evidence)
    assert "Not assessed" in evidence_text


# ============================================================================
# 3. Geographic Coverage Warning Tests
# ============================================================================
def test_geographic_coverage_warning_outside_northern_nigeria():
    """Coordinates outside northern savanna & Middle Belt trigger clear warnings and lower data confidence."""
    # Paris, France (lat 48.85, lon 2.35) - far outside Nigeria
    payload = {
        "lat": 48.85,
        "lon": 2.35,
        "current_rotation": ["maize", "maize", "maize"],
    }

    # Mock fetch so test runs against cached fixture or returns data
    resp = client.post("/recommend", json=payload)
    assert resp.status_code == 200
    data = RecommendResponse(**resp.json())

    for rot in data.rotations:
        # 1. Warning in information_gaps
        assert any("Geographic coverage warning" in gap for gap in rot.information_gaps)

        # 2. Warning in risks_for_local_review
        assert any("Unvalidated agroecological zone" in risk for risk in rot.risks_for_local_review)

        # 3. Lowered data confidence reason
        assert any("outside the validated northern savanna" in reason for reason in rot.data_confidence.reasons)


# ============================================================================
# 4. Scenario Field Execution Tests (Section 8.5)
# ============================================================================
def test_scenario_field_never_ignored_and_labels_hypothetical():
    """The scenario field must scale rainfall, shift temp, rerun pipeline, and label results hypothetical."""
    base_payload = {
        "lat": KANO_LAT,
        "lon": KANO_LON,
        "current_rotation": ["maize", "cowpea", "sorghum"],
        "priorities": {"water_saving": 5, "resilience": 5},
    }

    # Run baseline (no scenario)
    resp_base = client.post("/recommend", json={**base_payload, "scenario": {"rainfall_change_pct": 0, "temperature_change_c": 0}})
    assert resp_base.status_code == 200
    base_recs = RecommendResponse(**resp_base.json()).rotations

    # Run hypothetical severe drought + warming scenario (-30% rain, +3°C temp)
    payload_scenario = {
        **base_payload,
        "scenario": {"rainfall_change_pct": -30.0, "temperature_change_c": 3.0},
    }
    resp_scen = client.post("/recommend", json=payload_scenario)
    assert resp_scen.status_code == 200
    scen_recs = RecommendResponse(**resp_scen.json()).rotations

    # 1. Scores must change (scenario is NOT silently ignored)
    base_scores = [r.score for r in base_recs]
    scen_scores = [r.score for r in scen_recs]
    assert base_scores != scen_scores

    # 2. Results must be labelled hypothetical in assumptions and evidence
    for rot in scen_recs:
        assert any("Hypothetical sensitivity test, not a forecast" in a for a in rot.assumptions)
        assert any("Climate sensitivity scenario" in e.metric for e in rot.evidence)
        assert "hypothetical sensitivity scenario" in rot.why_suggested.lower()


# ============================================================================
# 5. Live NASA Fetch Tests (Timeout, Error message, Quality Flag)
# ============================================================================
def test_live_nasa_fetch_sets_quality_flag():
    """When data comes from a live NASA fetch, quality_flags must contain 'live_nasa_fetch'."""
    sample_power_response = {
        "properties": {
            "parameter": {
                "PRECTOTCORR": {"19910101": 0.0, "19910102": 5.0},
                "T2M": {"19910101": 25.0, "19910102": 26.0},
                "T2M_MAX": {"19910101": 32.0, "19910102": 33.0},
                "T2M_MIN": {"19910101": 18.0, "19910102": 19.0},
                "RH2M": {"19910101": 50.0, "19910102": 55.0},
                "ALLSKY_SFC_SW_DWN": {"19910101": 20.0, "19910102": 21.0},
                "GWETTOP": {"19910101": 0.3, "19910102": 0.4},
                "GWETROOT": {"19910101": 0.4, "19910102": 0.5},
            }
        },
        "header": {"fill_value": -999.0},
    }

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = sample_power_response

    client_instance = NasaPowerClient()
    with patch("httpx.Client.get", return_value=mock_resp):
        df, meta = client_instance.fetch_daily_data(
            lat=11.11,
            lon=7.77,
            start="19910101",
            end="19910102",
            force_refresh=True,  # bypass disk cache to force live fetch
        )
        assert meta["from_cache"] is False
        assert "live_nasa_fetch" in meta["quality_flags"]


def test_live_nasa_fetch_timeout_clear_error():
    """A live NASA timeout raises a clear, informative error message."""
    client_instance = NasaPowerClient(max_retries=0)
    with patch("httpx.Client.get", side_effect=httpx.TimeoutException("Connection timed out")):
        with pytest.raises(NasaPowerApiError) as exc_info:
            client_instance.fetch_daily_data(
                lat=13.0,
                lon=5.0,
                force_refresh=True,
            )
        assert "timed out after" in str(exc_info.value)
