"""Unit tests for scoring engine, quality evaluation, and feasibility gate.

Adheres to Section 8 of AGROORBIT_PLAN_v2.md:
- 8.1 Eight criteria scored 0-100.
- 8.2 Priority-to-criteria mapping, 10% safety weight on season_fit, equal weights on all-zero.
- 8.2 Feasibility gate (<50% season completion caps category at weak; modifiers cannot override).
- 8.3 Fit categories (strong >= 75, moderate 55-74, weak < 55), similarity flag (< 5 pts).
- Deterministic scoring behavior.
"""

import pytest
from app.config import (
    FEASIBILITY_COMPLETION_MIN_PCT,
    SAFETY_WEIGHT_SEASON_FIT,
    SCORE_SIMILARITY_THRESHOLD,
)
from app.climate import CropClimateIndicators, CropFrequencyMetric
from app.knowledge import load_crops, load_soil_modifiers
from app.models import (
    Confidence,
    PrioritiesInput,
    SoilInput,
)
from app.quality import (
    determine_overall_outcome,
    evaluate_data_confidence,
    evaluate_knowledge_support,
)
from app.scoring import (
    calculate_criteria_scores,
    compute_criteria_weights,
    rank_and_mark_similar_rotations,
    score_rotation,
)


def create_mock_indicator(crop_id: str, can_complete_pct: float, water_ok_pct: float = 80.0):
    """Helper to create mock CropClimateIndicators."""
    success_complete = int(can_complete_pct * 0.3)
    success_water = int(water_ok_pct * 0.3)
    return CropClimateIndicators(
        crop_id=crop_id,
        crop_name=crop_id.capitalize(),
        duration_days=90,
        water_need_min_mm=400.0,
        total_years_evaluated=30,
        valid_years_count=30,
        flagged_years_count=0,
        can_complete_freq=CropFrequencyMetric(
            success_years=success_complete,
            total_valid_years=30,
            frequency_pct=can_complete_pct,
            formatted=f"{success_complete} of 30 years",
            flagged_years_excluded=0,
        ),
        water_ok_freq=CropFrequencyMetric(
            success_years=success_water,
            total_valid_years=30,
            frequency_pct=water_ok_pct,
            formatted=f"{success_water} of 30 years",
            flagged_years_excluded=0,
        ),
        critical_dry_spell_risk_freq=CropFrequencyMetric(
            success_years=3,
            total_valid_years=30,
            frequency_pct=10.0,
            formatted="3 of 30 years",
            flagged_years_excluded=0,
        ),
        heat_stress_risk_freq=CropFrequencyMetric(
            success_years=2,
            total_valid_years=30,
            frequency_pct=6.7,
            formatted="2 of 30 years",
            flagged_years_excluded=0,
        ),
        window_rain_median_mm=550.0,
        window_rain_p20_mm=420.0,
        heat_days_median=3,
        yearly_indicators=[],
    )


def test_compute_criteria_weights_all_zero():
    """Verify that all-zero priorities yield equal base weights with 10% safety weight on season_fit."""
    priorities = PrioritiesInput(
        water_saving=0,
        soil_health=0,
        erosion=0,
        market_preference=0,
        forage=0,
        resilience=0,
    )
    weights = compute_criteria_weights(priorities)

    # Must sum to 1.0
    assert pytest.approx(sum(weights.values()), 0.001) == 1.0

    # Season fit gets the safety weight boost
    # 8 criteria: equal base is 1/8 = 0.125
    # season_fit = 0.125 * 0.90 + 0.10 = 0.2125
    # others = 0.125 * 0.90 = 0.1125
    assert weights["season_fit"] > weights["water_fit"]
    assert weights["season_fit"] >= SAFETY_WEIGHT_SEASON_FIT
    # Other criteria should be equal to each other
    assert weights["water_fit"] == weights["erosion_protection"]
    assert weights["market_preference_fit"] == weights["forage_value"]


def test_compute_criteria_weights_custom():
    """Verify criteria weight mappings with specific priorities."""
    priorities = PrioritiesInput(
        water_saving=5,
        soil_health=0,
        erosion=0,
        market_preference=0,
        forage=0,
        resilience=0,
    )
    weights = compute_criteria_weights(priorities)

    assert pytest.approx(sum(weights.values()), 0.001) == 1.0
    # water_fit gets the dominant share, season_fit retains safety weight
    assert weights["water_fit"] > 0.70
    assert weights["season_fit"] >= SAFETY_WEIGHT_SEASON_FIT
    assert weights["forage_value"] == 0.0


def test_feasibility_gate_failure_caps_rotation_at_weak():
    """Feasibility gate: crop completing season in <50% of years strictly caps fit_category at 'weak'."""
    crops_dict = load_crops()
    modifiers = load_soil_modifiers()

    # Sequence with maize, cowpea, sorghum
    sequence = ["maize", "cowpea", "sorghum"]

    # Maize fails feasibility gate: 40% completion (< 50%)
    indicators_map = {
        "maize": create_mock_indicator("maize", can_complete_pct=40.0, water_ok_pct=90.0),
        "cowpea": create_mock_indicator("cowpea", can_complete_pct=90.0, water_ok_pct=95.0),
        "sorghum": create_mock_indicator("sorghum", can_complete_pct=85.0, water_ok_pct=90.0),
    }

    criteria, passed, risks = calculate_criteria_scores(
        sequence=sequence,
        crop_indicators_map=indicators_map,
        crops_dict=crops_dict,
        soil_modifiers=modifiers,
    )

    assert passed is False
    assert len(risks) >= 1
    assert "Feasibility gate triggered" in risks[0]
    assert "Maize" in risks[0]

    # Score with all-high weights
    priorities = PrioritiesInput(water_saving=5, soil_health=5, erosion=5, market_preference=5, forage=5, resilience=5)
    weights = compute_criteria_weights(priorities)

    score, fit_category, contributions = score_rotation(
        criteria=criteria,
        weights=weights,
        feasibility_passed=passed,
    )

    # Even if mathematical score is high (e.g. > 70), fit_category MUST be 'weak'
    assert fit_category == "weak"


def test_soil_modifiers_cannot_override_feasibility_gate():
    """Verify soil modifiers adjust scores but cannot override a failed feasibility gate."""
    crops_dict = load_crops()
    modifiers = load_soil_modifiers()

    sequence = ["maize", "cowpea", "groundnut"]
    indicators_map = {
        "maize": create_mock_indicator("maize", can_complete_pct=30.0),  # FAILS GATE
        "cowpea": create_mock_indicator("cowpea", can_complete_pct=90.0),
        "groundnut": create_mock_indicator("groundnut", can_complete_pct=90.0),
    }

    # Best possible soil to give maximum bonuses
    soil = SoilInput(
        texture="loam",  # +5 water fit bonus
        drainage="well_drained",
        organic_matter="high",  # +5 bonus
        slope="flat",  # +5 erosion bonus
    )

    criteria, passed, risks = calculate_criteria_scores(
        sequence=sequence,
        crop_indicators_map=indicators_map,
        crops_dict=crops_dict,
        soil=soil,
        soil_modifiers=modifiers,
    )

    assert passed is False
    weights = compute_criteria_weights(PrioritiesInput())
    score, fit_category, _ = score_rotation(criteria, weights, feasibility_passed=passed)

    # Soil bonus may boost score, but category MUST remain 'weak'
    assert fit_category == "weak"


def test_score_fit_categories_and_similarity():
    """Verify fit category thresholds (>=75 strong, 55-74 moderate, <55 weak) and similarity flag."""
    crops_dict = load_crops()
    modifiers = load_soil_modifiers()

    sequence = ["sorghum", "cowpea", "pearl_millet"]
    indicators_map = {
        "sorghum": create_mock_indicator("sorghum", can_complete_pct=95.0),
        "cowpea": create_mock_indicator("cowpea", can_complete_pct=90.0),
        "pearl_millet": create_mock_indicator("pearl_millet", can_complete_pct=95.0),
    }

    criteria, passed, _ = calculate_criteria_scores(
        sequence=sequence,
        crop_indicators_map=indicators_map,
        crops_dict=crops_dict,
        soil_modifiers=modifiers,
    )
    assert passed is True

    weights = compute_criteria_weights(PrioritiesInput())
    score, fit_category, _ = score_rotation(criteria, weights, feasibility_passed=True)

    assert fit_category in ("strong", "moderate")

    # Test ranking and similarity (< 5.0 points apart)
    rotations = [
        {"id": "rot_1", "score": 78.5, "fit_category": "strong"},
        {"id": "rot_2", "score": 75.0, "fit_category": "strong"},  # diff = 3.5 (< 5) -> similar
        {"id": "rot_3", "score": 62.0, "fit_category": "moderate"},  # diff = 13.0 (>= 5) -> not similar
    ]

    ranked = rank_and_mark_similar_rotations(rotations)

    assert ranked[0]["id"] == "rot_1"
    assert ranked[0]["rank"] == 1
    assert "rot_2" in ranked[0]["similar_to"]
    assert "rot_3" not in ranked[0]["similar_to"]

    assert ranked[1]["id"] == "rot_2"
    assert ranked[1]["rank"] == 2
    assert "rot_1" in ranked[1]["similar_to"]
    assert "rot_3" not in ranked[1]["similar_to"]

    assert ranked[2]["id"] == "rot_3"
    assert ranked[2]["rank"] == 3
    assert ranked[2]["similar_to"] == []


def test_evaluate_data_confidence():
    """Verify data confidence logic penalizes missing soil context, missing days, and flags."""
    # 1. Complete high confidence
    conf_high = evaluate_data_confidence(missing_pct=0.0, quality_flags=[])
    assert conf_high.level == "high"
    assert any("~27 km" in r for r in conf_high.reasons)

    # 2. Incomplete soil context
    soil_unknown = SoilInput(
        texture="unknown",
        drainage="unknown",
        organic_matter="unknown",
        slope="unknown",
    )
    conf_soil = evaluate_data_confidence(missing_pct=0.0, quality_flags=[], soil=soil_unknown)
    assert conf_soil.level == "medium"
    assert any("Farmer soil context incomplete" in r for r in conf_soil.reasons)

    # 3. High missing days and flags
    conf_low = evaluate_data_confidence(
        missing_pct=10.0,
        quality_flags=["onset_late_risk", "high_missing_days"],
        soil=soil_unknown,
    )
    assert conf_low.level == "low"
    assert any("missing days" in r for r in conf_low.reasons)


def test_evaluate_knowledge_support():
    """Verify knowledge support evaluates proportion of verified traits."""
    crops_dict = load_crops()
    crop_list = list(crops_dict.values())

    # All traits currently have verified: false in data/crops.json
    conf = evaluate_knowledge_support(crop_list)
    assert conf.level == "low"
    assert any("unverified working placeholders" in r for r in conf.reasons)


def test_determine_overall_outcome():
    """Verify outcome determination: clear_leader, similar_options, or no_clear_winner."""
    high_conf = Confidence(level="high", reasons=[])
    low_conf = Confidence(level="low", reasons=[])

    # 1. Both confidences low -> no_clear_winner
    rot_strong = [{"id": "r1", "score": 85.0, "fit_category": "strong"}]
    outcome, note = determine_overall_outcome(rot_strong, low_conf, low_conf)
    assert outcome == "no_clear_winner"
    assert "None of the evaluated strategies" in note

    # 2. Best rotation is weak -> no_clear_winner
    rot_weak = [{"id": "r1", "score": 45.0, "fit_category": "weak"}]
    outcome, note = determine_overall_outcome(rot_weak, high_conf, high_conf)
    assert outcome == "no_clear_winner"

    # 3. Similar options (< 5 points apart)
    rot_similar = [
        {"id": "r1", "score": 82.0, "fit_category": "strong"},
        {"id": "r2", "score": 79.0, "fit_category": "strong"},
    ]
    outcome, note = determine_overall_outcome(rot_similar, high_conf, high_conf)
    assert outcome == "similar_options"
    assert "Multiple strategies perform within" in note

    # 4. Clear leader (>= 5 points apart)
    rot_leader = [
        {"id": "r1", "score": 85.0, "fit_category": "strong"},
        {"id": "r2", "score": 74.0, "fit_category": "moderate"},
    ]
    outcome, note = determine_overall_outcome(rot_leader, high_conf, high_conf)
    assert outcome == "clear_leader"
    assert note is None
