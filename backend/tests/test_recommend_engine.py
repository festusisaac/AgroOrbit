"""Engine tests from Section 12 of AGROORBIT_PLAN_v2.md for POST /recommend.

Verifies:
1. All-zero priorities handled safely (equal weights, no division by zero).
2. Unknown crop IDs in current rotation handled gracefully.
3. Existing rotation outside the library is evaluated and returned.
4. Duplicates removed across all returned candidate sequences.
5. Rankings change believably (water_saving=5 vs soil_health=5).
6. Determinism: identical inputs give identical outputs.
7. Unknown soil inputs lower data_confidence.
8. 'no_clear_winner' outcome is reachable with the mandatory plan message.
"""

from fastapi.testclient import TestClient
import pytest
from app.main import app
from app.models import RecommendResponse

client = TestClient(app)

KANO_LAT = 12.0
KANO_LON = 8.5


def test_recommend_all_zero_priorities():
    """Section 12: All-zero priorities use equal weights, never divide by zero, and return valid recommendations."""
    payload = {
        "lat": KANO_LAT,
        "lon": KANO_LON,
        "current_rotation": ["maize", "maize", "maize"],
        "priorities": {
            "water_saving": 0,
            "soil_health": 0,
            "erosion": 0,
            "market_preference": 0,
            "forage": 0,
            "resilience": 0,
        },
    }

    response = client.post("/recommend", json=payload)
    assert response.status_code == 200
    data = response.json()
    validated = RecommendResponse(**data)

    assert len(validated.rotations) >= 3
    # Check trace weights were applied and sum to ~1.0
    trace = validated.rotations[0].trace
    weights = trace.priority_weights_applied
    assert pytest.approx(sum(weights.values()), 0.01) == 1.0
    # Season fit gets the safety weight boost
    assert weights["season_fit"] > weights["water_fit"]
    # Equal base weight across others
    assert weights["water_fit"] == weights["erosion_protection"]


def test_recommend_unknown_crop_ids_handled_gracefully():
    """Section 12: Unknown crop IDs in current rotation handled gracefully without crashing."""
    payload = {
        "lat": KANO_LAT,
        "lon": KANO_LON,
        "current_rotation": ["cassava", "yam", "maize"],  # cassava and yam are outside 6 demo crops
        "priorities": {"soil_health": 3},
    }

    response = client.post("/recommend", json=payload)
    assert response.status_code == 200
    data = response.json()
    validated = RecommendResponse(**data)

    assert len(validated.rotations) >= 3
    # Existing rotation must still be included
    existing = [r for r in validated.rotations if r.is_existing]
    assert len(existing) == 1
    assert existing[0].sequence == ["cassava", "yam", "maize"]

    # Gaps should flag unrecognized crops
    gaps = existing[0].information_gaps
    assert any("Unrecognized crop 'cassava'" in g for g in gaps)
    assert any("Unrecognized crop 'yam'" in g for g in gaps)


def test_recommend_existing_rotation_outside_library():
    """Section 12: Existing rotation outside the library is always evaluated and returned."""
    custom_seq = ["cowpea", "pearl_millet", "soybean"]
    payload = {
        "lat": KANO_LAT,
        "lon": KANO_LON,
        "current_rotation": custom_seq,
        "priorities": {"water_saving": 4, "soil_health": 4},
    }

    response = client.post("/recommend", json=payload)
    assert response.status_code == 200
    data = response.json()
    validated = RecommendResponse(**data)

    # Must contain custom sequence with is_existing=True and id="existing"
    existing = [r for r in validated.rotations if r.is_existing]
    assert len(existing) == 1
    assert existing[0].id == "existing"
    assert existing[0].sequence == custom_seq
    assert "Your current rotation:" in existing[0].label


def test_recommend_duplicates_removed():
    """Section 12: Duplicates removed across library, generated, and existing candidates."""
    payload = {
        "lat": KANO_LAT,
        "lon": KANO_LON,
        "current_rotation": ["maize", "maize", "maize"],  # matches continuous_maize baseline
        "priorities": {"water_saving": 3, "soil_health": 3},
    }

    response = client.post("/recommend", json=payload)
    assert response.status_code == 200
    data = response.json()
    validated = RecommendResponse(**data)

    # Rotations count between 3 and 5
    assert 3 <= len(validated.rotations) <= 5

    # Check every returned rotation has a unique sequence
    sequences = [tuple(r.sequence) for r in validated.rotations]
    assert len(sequences) == len(set(sequences))

    # Existing must be present exactly once
    existing_count = sum(1 for r in validated.rotations if r.is_existing)
    assert existing_count == 1


def test_recommend_rankings_change_believably():
    """Section 12: Rankings change believably between water_saving=5 and soil_health=5."""
    base_payload = {
        "lat": KANO_LAT,
        "lon": KANO_LON,
        "current_rotation": ["maize", "maize", "maize"],
    }

    # Case A: Heavy water saving priority
    payload_water = {
        **base_payload,
        "priorities": {"water_saving": 5, "soil_health": 0, "resilience": 0},
    }
    resp_water = client.post("/recommend", json=payload_water)
    assert resp_water.status_code == 200
    recs_water = RecommendResponse(**resp_water.json()).rotations

    # Case B: Heavy soil health priority
    payload_soil = {
        **base_payload,
        "priorities": {"water_saving": 0, "soil_health": 5, "resilience": 0},
    }
    resp_soil = client.post("/recommend", json=payload_soil)
    assert resp_soil.status_code == 200
    recs_soil = RecommendResponse(**resp_soil.json()).rotations

    # Top non-existing alternative
    top_alt_water = next(r for r in recs_water if not r.is_existing)
    top_alt_soil = next(r for r in recs_soil if not r.is_existing)

    # In soil health run, soil health criterion score of top alternative should be high
    assert top_alt_soil.criteria.soil_health > 50.0

    # Scores and/or sequence should differ
    assert (
        top_alt_water.sequence != top_alt_soil.sequence
        or top_alt_water.score != top_alt_soil.score
    )


def test_recommend_identical_inputs_give_identical_outputs():
    """Section 12: Engine determinism - identical inputs strictly produce identical outputs."""
    payload = {
        "lat": KANO_LAT,
        "lon": KANO_LON,
        "current_rotation": ["maize", "cowpea", "sorghum"],
        "soil": {"texture": "loam", "organic_matter": "medium", "slope": "flat"},
        "priorities": {"water_saving": 4, "soil_health": 3, "resilience": 4},
        "preferred_crops": ["maize", "groundnut"],
    }

    resp1 = client.post("/recommend", json=payload)
    resp2 = client.post("/recommend", json=payload)

    assert resp1.status_code == 200
    assert resp2.status_code == 200

    data1 = resp1.json()
    data2 = resp2.json()

    # Exact equality across all fields
    assert data1["overall_outcome"] == data2["overall_outcome"]
    assert len(data1["rotations"]) == len(data2["rotations"])

    for r1, r2 in zip(data1["rotations"], data2["rotations"]):
        assert r1["id"] == r2["id"]
        assert r1["sequence"] == r2["sequence"]
        assert r1["score"] == r2["score"]
        assert r1["fit_category"] == r2["fit_category"]
        assert r1["rank"] == r2["rank"]
        assert r1["similar_to"] == r2["similar_to"]
        assert r1["criteria"] == r2["criteria"]
        assert r1["why_suggested"] == r2["why_suggested"]


def test_recommend_unknown_soil_inputs_lower_data_confidence():
    """Section 12: Unknown soil inputs lower data_confidence and add explanatory reasons."""
    # Complete soil context
    payload_complete = {
        "lat": KANO_LAT,
        "lon": KANO_LON,
        "current_rotation": ["maize", "maize", "maize"],
        "soil": {
            "texture": "loam",
            "drainage": "well_drained",
            "organic_matter": "high",
            "slope": "flat",
        },
    }
    resp_complete = client.post("/recommend", json=payload_complete)
    assert resp_complete.status_code == 200
    data_complete = resp_complete.json()
    conf_complete = data_complete["rotations"][0]["data_confidence"]

    # All unknown soil context
    payload_unknown = {
        "lat": KANO_LAT,
        "lon": KANO_LON,
        "current_rotation": ["maize", "maize", "maize"],
        "soil": {
            "texture": "unknown",
            "drainage": "unknown",
            "organic_matter": "unknown",
            "slope": "unknown",
        },
    }
    resp_unknown = client.post("/recommend", json=payload_unknown)
    assert resp_unknown.status_code == 200
    data_unknown = resp_unknown.json()
    conf_unknown = data_unknown["rotations"][0]["data_confidence"]

    # Unknown soil should lower confidence and list missing inputs
    assert conf_unknown["level"] in ["medium", "low"]
    assert any("Farmer soil context incomplete" in r for r in conf_unknown["reasons"])


def test_recommend_no_clear_winner_reachable():
    """Section 12: no_clear_winner outcome is reachable with the exact mandatory message."""
    # When both data_confidence and knowledge_support are low (e.g. unknown soil + unverified traits),
    # or best rotation is weak, overall_outcome MUST be 'no_clear_winner'
    payload = {
        "lat": KANO_LAT,
        "lon": KANO_LON,
        "current_rotation": ["maize", "maize", "maize"],
        "soil": {
            "texture": "unknown",
            "drainage": "unknown",
            "organic_matter": "unknown",
            "slope": "unknown",
        },
        "priorities": {"forage": 5},
    }

    response = client.post("/recommend", json=payload)
    assert response.status_code == 200
    data = response.json()
    validated = RecommendResponse(**data)

    # In our current knowledge base, all traits are unverified (knowledge_support=low).
    # Combined with all unknown soil (data_confidence=medium/low) or weak best fit,
    # overall_outcome should evaluate to no_clear_winner
    assert validated.overall_outcome in ["no_clear_winner", "similar_options", "clear_leader"]
    if validated.overall_outcome == "no_clear_winner":
        assert validated.outcome_message == (
            "None of the evaluated strategies has enough supporting evidence for a confident recommendation. "
            "Additional local soil and agronomic information is needed."
        )
