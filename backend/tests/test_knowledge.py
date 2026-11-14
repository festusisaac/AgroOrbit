"""Tests for knowledge.py: schema validation, provenance constraints, and API integration."""

import json
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

from app.knowledge import (
    CropRecord,
    KnowledgeValidationError,
    TraitValue,
    get_crops_api_summary,
    load_crops,
    load_locations,
    load_rotations,
    load_soil_modifiers,
)
from app.main import app

client = TestClient(app)


def test_trait_value_rejects_verified_without_source():
    """CRITICAL RULE: verified:true is strictly prohibited without a non-empty source citation."""
    # verified: true with null source must fail
    with pytest.raises(ValueError, match="must provide a valid citation"):
        TraitValue(value=4, verified=True, source=None)

    # verified: true with empty or blank source must fail
    with pytest.raises(ValueError, match="must provide a valid citation"):
        TraitValue(value=4, verified=True, source="   ")

    # verified: true with valid citation must succeed
    valid_cited = TraitValue(value=4, verified=True, source="FAO Irrigation and Drainage Paper 56")
    assert valid_cited.verified is True
    assert valid_cited.source == "FAO Irrigation and Drainage Paper 56"

    # verified: false with null source is the valid placeholder state
    unverified_ok = TraitValue(value=4, verified=False, source=None)
    assert unverified_ok.verified is False
    assert unverified_ok.source is None


def test_load_crops_real_file():
    """Verify crops.json contains the 6 required crops with 100% placeholder provenance."""
    crops = load_crops()
    expected_crops = {"maize", "sorghum", "pearl_millet", "cowpea", "groundnut", "soybean"}
    assert set(crops.keys()) == expected_crops

    required_traits = [
        "season_days",
        "water_need_mm",
        "drought_tolerance",
        "heat_tolerance",
        "nitrogen_fixing",
        "residue_organic_matter",
        "ground_cover_erosion",
        "forage_value",
        "root_depth",
    ]

    for crop_id, crop in crops.items():
        assert isinstance(crop, CropRecord)
        for trait_name in required_traits:
            assert trait_name in crop.traits, f"Missing trait '{trait_name}' in {crop_id}"
            trait = crop.traits[trait_name]
            # Must be unverified placeholder with null source
            assert trait.verified is False, f"Crop {crop_id} trait {trait_name} must have verified:false"
            assert trait.source is None, f"Crop {crop_id} trait {trait_name} must have source:null"

        # Pest disease notes must also be unverified
        assert crop.pest_disease_notes.verified is False
        assert crop.pest_disease_notes.source is None

        # Verified share must be 0.0 initially
        assert crop.get_verified_share() == 0.0


def test_load_crops_rejects_missing_mandatory_fields(tmp_path):
    """Verify validation fails if a trait omits 'value', 'verified', or 'source'."""
    invalid_data = [
        {
            "id": "bad_crop",
            "name": "Bad Crop",
            "family": "cereal",
            "traits": {
                "season_days": {"value": 90}  # Missing 'verified' and 'source'
            },
            "pest_disease_notes": {"value": "None", "verified": False, "source": None},
        }
    ]

    bad_file = tmp_path / "bad_crops.json"
    with open(bad_file, "w", encoding="utf-8") as f:
        json.dump(invalid_data, f)

    with pytest.raises(KnowledgeValidationError, match="missing mandatory field"):
        load_crops(bad_file)


def test_load_rotations():
    """Verify rotations.json contains 6-8 sequences including continuous baselines."""
    rotations = load_rotations()
    assert 6 <= len(rotations) <= 8

    sequences = [r.sequence for r in rotations]
    assert ["maize", "maize", "maize"] in sequences
    assert ["sorghum", "sorghum", "sorghum"] in sequences

    for r in rotations:
        assert len(r.sequence) == 3
        assert r.id
        assert r.name
        assert r.description


def test_load_soil_modifiers():
    """Verify soil_modifiers.json contains all required categories with verified:false."""
    modifiers = load_soil_modifiers()
    categories = ["texture", "drainage", "organic_matter", "water_source", "slope"]
    for cat in categories:
        assert cat in modifiers
        for item_key, item_val in modifiers[cat].items():
            assert item_val["verified"] is False
            assert item_val["source"] is None
            assert "notes" in item_val


def test_load_locations():
    """Verify locations.json contains the 4 preset demo locations."""
    locations = load_locations()
    assert len(locations) == 4
    ids = [loc.id for loc in locations]
    assert ids == ["kano", "kaduna", "jos", "makurdi"]


def test_get_crops_endpoint():
    """Verify GET /crops returns real file content with verified_share=0.0."""
    response = client.get("/crops")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 6

    for item in data:
        assert item["verified_share"] == 0.0
        assert "season_days" in item["traits_summary"]
        assert "water_need_mm" in item["traits_summary"]
