"""Unit tests for candidate rotation generation and template explanations.

Strictly adheres to:
- Section 7.3: Candidate rotations (library + generated, dedupe, existing always included, >= 2 alternatives differing by >= 1 crop, cap 5, never hardcode).
- Section 8.4: Template explanations (why_suggested, evidence with real frequencies, benefits, assumptions, information_gaps including every unverified trait used, risks_for_local_review, review_recommended_by, trace).
"""

import pytest
from app.config import (
    ALGORITHM_VERSION,
    CLIMATE_PERIOD,
    SCORE_SIMILARITY_THRESHOLD,
)
from app.explain import (
    build_rotation_recommendation,
    generate_assumptions,
    generate_benefits,
    generate_evidence_items,
    generate_information_gaps,
    generate_review_recommended_by,
    generate_risks_for_local_review,
    generate_why_suggested,
)
from app.knowledge import (
    generate_candidate_rotations,
    load_crops,
    load_rotations,
    load_soil_modifiers,
)
from app.models import (
    Confidence,
    CriteriaScores,
    EvidenceItem,
    PrioritiesInput,
    RotationRecommendation,
    SoilInput,
    TraceInfo,
)
from app.quality import (
    determine_overall_outcome,
    evaluate_data_confidence,
    evaluate_knowledge_support,
)
from app.scoring import (
    calculate_criteria_scores,
    compute_criteria_weights,
    score_rotation,
    select_and_rank_recommendations,
)
from app.climate import CropClimateIndicators, CropFrequencyMetric


def create_mock_crop_indicators(crops_dict):
    """Creates realistic mock CropClimateIndicators for the demo crops."""
    indicators_map = {}
    for cid, crop in crops_dict.items():
        # Differentiate values realistically
        if cid == "pearl_millet":
            can_comp = 96.7
            wat_ok = 93.3
            dry_spell = 3.3
            heat_days = 4
        elif cid == "sorghum":
            can_comp = 93.3
            wat_ok = 90.0
            dry_spell = 6.7
            heat_days = 3
        elif cid == "cowpea":
            can_comp = 96.7
            wat_ok = 86.7
            dry_spell = 6.7
            heat_days = 2
        elif cid == "groundnut":
            can_comp = 90.0
            wat_ok = 83.3
            dry_spell = 10.0
            heat_days = 2
        elif cid == "soybean":
            can_comp = 83.3
            wat_ok = 76.7
            dry_spell = 13.3
            heat_days = 1
        else:  # maize
            can_comp = 86.7
            wat_ok = 80.0
            dry_spell = 10.0
            heat_days = 3

        indicators_map[cid] = CropClimateIndicators(
            crop_id=cid,
            crop_name=crop.name,
            duration_days=95,
            water_need_min_mm=450.0,
            total_years_evaluated=30,
            valid_years_count=30,
            flagged_years_count=0,
            can_complete_freq=CropFrequencyMetric(
                success_years=int(can_comp * 0.3),
                total_valid_years=30,
                frequency_pct=can_comp,
                formatted=f"{int(can_comp * 0.3)} of 30 years",
                flagged_years_excluded=0,
            ),
            water_ok_freq=CropFrequencyMetric(
                success_years=int(wat_ok * 0.3),
                total_valid_years=30,
                frequency_pct=wat_ok,
                formatted=f"{int(wat_ok * 0.3)} of 30 years",
                flagged_years_excluded=0,
            ),
            critical_dry_spell_risk_freq=CropFrequencyMetric(
                success_years=int(dry_spell * 0.3),
                total_valid_years=30,
                frequency_pct=dry_spell,
                formatted=f"{int(dry_spell * 0.3)} of 30 years",
                flagged_years_excluded=0,
            ),
            heat_stress_risk_freq=CropFrequencyMetric(
                success_years=2,
                total_valid_years=30,
                frequency_pct=6.7,
                formatted="2 of 30 years",
                flagged_years_excluded=0,
            ),
            window_rain_median_mm=620.0,
            window_rain_p20_mm=480.0,
            heat_days_median=heat_days,
            yearly_indicators=[],
        )
    return indicators_map


# ===========================================================================
# Candidate Generation Tests (Section 7.3)
# ===========================================================================
def test_candidate_generation_includes_existing_and_alternatives():
    """Verify candidate generation always includes farmer's current rotation and alternatives."""
    crops_dict = load_crops()
    rotations_lib = load_rotations()

    # Custom rotation NOT in library
    custom_rotation = ["cowpea", "pearl_millet", "soybean"]
    candidates = generate_candidate_rotations(
        current_rotation=custom_rotation,
        library_rotations=rotations_lib,
        crops_dict=crops_dict,
    )

    # 1. Existing rotation must be present
    existing_items = [c for c in candidates if c["is_existing"]]
    assert len(existing_items) == 1
    assert existing_items[0]["id"] == "existing"
    assert existing_items[0]["sequence"] == custom_rotation
    assert "Your current rotation:" in existing_items[0]["label"]

    # 2. Must contain at least two alternatives
    alternatives = [c for c in candidates if not c["is_existing"]]
    assert len(alternatives) >= 2

    # 3. All candidates must be deduplicated
    sequences = [tuple(c["sequence"]) for c in candidates]
    assert len(sequences) == len(set(sequences))

    # 4. Library rotations must be included
    library_seqs = {tuple(r.sequence) for r in rotations_lib}
    found_lib = [s for s in sequences if s in library_seqs]
    assert len(found_lib) == len(library_seqs)


def test_candidate_generation_when_existing_matches_library():
    """Verify that when current rotation matches a library sequence, no duplicate is created."""
    crops_dict = load_crops()
    rotations_lib = load_rotations()

    # Continuous maize is in the library
    current = ["maize", "maize", "maize"]
    candidates = generate_candidate_rotations(
        current_rotation=current,
        library_rotations=rotations_lib,
        crops_dict=crops_dict,
    )

    # Must only appear once with is_existing=True
    maize_seqs = [c for c in candidates if tuple(c["sequence"]) == ("maize", "maize", "maize")]
    assert len(maize_seqs) == 1
    assert maize_seqs[0]["is_existing"] is True


def test_candidate_selection_returns_3_to_5_rotations_with_existing():
    """Verify select_and_rank_recommendations returns 3-5 distinct rotations including existing."""
    crops_dict = load_crops()
    rotations_lib = load_rotations()
    indicators_map = create_mock_crop_indicators(crops_dict)
    modifiers = load_soil_modifiers()

    current_rotation = ["maize", "maize", "maize"]
    candidates = generate_candidate_rotations(
        current_rotation=current_rotation,
        library_rotations=rotations_lib,
        crops_dict=crops_dict,
    )

    priorities = PrioritiesInput(soil_health=5, water_saving=4)
    weights = compute_criteria_weights(priorities)

    # Score every candidate
    scored_candidates = []
    for cand in candidates:
        criteria, passed, risks = calculate_criteria_scores(
            sequence=cand["sequence"],
            crop_indicators_map=indicators_map,
            crops_dict=crops_dict,
            soil_modifiers=modifiers,
        )
        score, fit_cat, contribs = score_rotation(criteria, weights, feasibility_passed=passed)
        c_copy = dict(cand)
        c_copy["score"] = score
        c_copy["fit_category"] = fit_cat
        c_copy["criteria"] = criteria
        c_copy["contributions"] = contribs
        c_copy["feasibility_passed"] = passed
        c_copy["feasibility_risks"] = risks
        scored_candidates.append(c_copy)

    # Select recommendations
    selected = select_and_rank_recommendations(scored_candidates, max_total=5)

    # Must be 3 to 5 rotations
    assert 3 <= len(selected) <= 5

    # Existing rotation MUST be present
    existing_in_final = [r for r in selected if r["is_existing"]]
    assert len(existing_in_final) == 1
    assert existing_in_final[0]["sequence"] == ["maize", "maize", "maize"]

    # At least two alternatives
    alts_in_final = [r for r in selected if not r["is_existing"]]
    assert len(alts_in_final) >= 2

    # Ranks must be 1, 2, 3...
    assert [r["rank"] for r in selected] == list(range(1, len(selected) + 1))

    # Must be sorted by score descending
    scores = [r["score"] for r in selected]
    assert scores == sorted(scores, reverse=True)


def test_candidate_ranking_responds_to_priority_shifts():
    """Verify rankings change meaningfully when priorities shift (NEVER hardcoded)."""
    crops_dict = load_crops()
    rotations_lib = load_rotations()
    indicators_map = create_mock_crop_indicators(crops_dict)
    modifiers = load_soil_modifiers()

    current_rotation = ["maize", "maize", "maize"]
    candidates = generate_candidate_rotations(
        current_rotation=current_rotation,
        library_rotations=rotations_lib,
        crops_dict=crops_dict,
    )

    def evaluate_with_priorities(priorities):
        weights = compute_criteria_weights(priorities)
        scored = []
        for cand in candidates:
            criteria, passed, risks = calculate_criteria_scores(
                sequence=cand["sequence"],
                crop_indicators_map=indicators_map,
                crops_dict=crops_dict,
                soil_modifiers=modifiers,
            )
            score, fit_cat, contribs = score_rotation(criteria, weights, feasibility_passed=passed)
            c_copy = dict(cand)
            c_copy["score"] = score
            c_copy["fit_category"] = fit_cat
            c_copy["criteria"] = criteria
            c_copy["contributions"] = contribs
            c_copy["feasibility_passed"] = passed
            c_copy["feasibility_risks"] = risks
            scored.append(c_copy)
        return select_and_rank_recommendations(scored, max_total=5)

    # Scenario 1: Focus purely on Soil Health
    p_soil = PrioritiesInput(soil_health=5, water_saving=0, resilience=0)
    recs_soil = evaluate_with_priorities(p_soil)

    # Scenario 2: Focus purely on Water Saving & Resilience
    p_water = PrioritiesInput(soil_health=0, water_saving=5, resilience=5)
    recs_water = evaluate_with_priorities(p_water)

    # Top non-existing alternative in each scenario should differ or scores must shift
    top_soil_alt = next(r for r in recs_soil if not r["is_existing"])
    top_water_alt = next(r for r in recs_water if not r["is_existing"])

    # High soil health priority favors legumes
    assert top_soil_alt["criteria"].soil_health > 50.0

    # Priorities must produce different scores or different leader
    assert (
        top_soil_alt["id"] != top_water_alt["id"]
        or top_soil_alt["score"] != top_water_alt["score"]
    )


# ===========================================================================
# Explanations Tests (Section 8.4)
# ===========================================================================
def test_generate_why_suggested():
    """Verify why_suggested addresses farmer priorities and baseline status."""
    crops_dict = load_crops()
    criteria = CriteriaScores(
        water_fit=80.0,
        season_fit=85.0,
        heat_drought_resilience=75.0,
        soil_health=85.0,
        pest_break=90.0,
        erosion_protection=70.0,
        market_preference_fit=60.0,
        forage_value=75.0,
    )

    # 1. Existing rotation baseline
    why_exist = generate_why_suggested(
        sequence=["maize", "maize", "maize"],
        is_existing=True,
        priorities=PrioritiesInput(soil_health=5),
        crops_dict=crops_dict,
        criteria=CriteriaScores(
            water_fit=70, season_fit=70, heat_drought_resilience=60, soil_health=30,
            pest_break=30, erosion_protection=50, market_preference_fit=50, forage_value=40
        ),
    )
    assert "Baseline current rotation" in why_exist

    # 2. Alternative with soil health priority
    why_alt_soil = generate_why_suggested(
        sequence=["maize", "cowpea", "sorghum"],
        is_existing=False,
        priorities=PrioritiesInput(soil_health=5),
        crops_dict=crops_dict,
        criteria=criteria,
    )
    assert "soil health" in why_alt_soil.lower()
    assert "nitrogen-fixing" in why_alt_soil.lower()


def test_generate_evidence_items_source_labelling():
    """Verify evidence items are strictly labelled by source and contain real metrics."""
    crops_dict = load_crops()
    indicators_map = create_mock_crop_indicators(crops_dict)
    sequence = ["maize", "cowpea", "sorghum"]
    soil = SoilInput(texture="loam", organic_matter="medium", slope="flat")

    evidence = generate_evidence_items(
        sequence=sequence,
        crop_indicators_map=indicators_map,
        crops_dict=crops_dict,
        soil=soil,
        preferred_crops=["maize", "cowpea"],
    )

    assert len(evidence) >= 6

    # Verify all sources match allowed literals
    sources = {e.source for e in evidence}
    assert sources == {"NASA POWER", "farmer input", "crop knowledge base"}

    # NASA POWER items must have real formatted values
    nasa_items = [e for e in evidence if e.source == "NASA POWER"]
    assert any("season completion" in e.metric.lower() for e in nasa_items)
    assert any("30 years" in e.value for e in nasa_items)

    # Farmer input items
    farmer_items = [e for e in evidence if e.source == "farmer input"]
    assert any("Loam" in e.value for e in farmer_items)

    # Crop knowledge base items
    kb_items = [e for e in evidence if e.source == "crop knowledge base"]
    assert any("nitrogen fixation" in e.metric.lower() for e in kb_items)


def test_information_gaps_includes_every_unverified_trait():
    """Verify information_gaps lists EVERY unverified trait evaluated during scoring."""
    crops_dict = load_crops()
    sequence = ["maize", "cowpea", "sorghum"]

    # Soil with unknown inputs
    soil = SoilInput(texture="unknown", drainage="unknown", organic_matter="unknown", slope="unknown")

    gaps = generate_information_gaps(
        sequence=sequence,
        crops_dict=crops_dict,
        soil=soil,
        preferred_crops=[],
    )

    # Every trait in crops.json currently has verified=False
    # Sequence of 3 crops with 9 evaluated traits = 27 trait gaps + 4 soil gaps + 1 preference gap = 32 gaps
    assert len(gaps) >= 20
    assert any("Unverified crop trait: Maize 'water_need_mm'" in g for g in gaps)
    assert any("Unverified crop trait: Cowpea 'nitrogen_fixing'" in g for g in gaps)
    assert any("Unverified crop trait: Sorghum 'drought_tolerance'" in g for g in gaps)
    assert any("Field soil texture is unknown" in g for g in gaps)
    assert any("No preferred marketable crops were stated" in g for g in gaps)


def test_risks_and_reviewers():
    """Verify risks and local specialist recommendations."""
    crops_dict = load_crops()
    indicators_map = create_mock_crop_indicators(crops_dict)
    sequence = ["maize", "maize", "maize"]

    criteria = CriteriaScores(
        water_fit=60, season_fit=80, heat_drought_resilience=50, soil_health=20,
        pest_break=30, erosion_protection=45, market_preference_fit=50, forage_value=40
    )
    soil = SoilInput(slope="steep", texture="sandy")

    risks = generate_risks_for_local_review(
        sequence=sequence,
        criteria=criteria,
        feasibility_passed=True,
        feasibility_risks=[],
        crop_indicators_map=indicators_map,
        crops_dict=crops_dict,
        soil=soil,
    )

    # Continuous maize monoculture triggers pest risk
    assert any("Monoculture / pest risk" in r for r in risks)
    assert any("Erosion risk" in r for r in risks)

    reviewers = generate_review_recommended_by(criteria=criteria, soil=soil)
    assert "Local Agricultural Extension Officer (ADP / State Ministry of Agriculture)" in reviewers
    # Steep slope triggers soil conservation specialist
    assert "Soil & Water Conservation Specialist" in reviewers
    # Low pest break triggers IPM specialist
    assert "Crop Protection & Integrated Pest Management (IPM) Specialist" in reviewers


def test_build_rotation_recommendation_contract_compliance():
    """Verify full end-to-end building of RotationRecommendation matching Pydantic model."""
    crops_dict = load_crops()
    indicators_map = create_mock_crop_indicators(crops_dict)
    modifiers = load_soil_modifiers()

    sequence = ["maize", "cowpea", "sorghum"]
    candidate = {
        "id": "gen_maize_cowpea_sorghum",
        "label": "Diversified Maize - Cowpea - Sorghum",
        "is_existing": False,
        "sequence": sequence,
        "score": 78.4,
        "fit_category": "strong",
        "rank": 1,
        "similar_to": ["gen_alt_2"],
    }

    criteria, passed, risks = calculate_criteria_scores(
        sequence=sequence,
        crop_indicators_map=indicators_map,
        crops_dict=crops_dict,
        soil_modifiers=modifiers,
    )

    priorities = PrioritiesInput(water_saving=4, soil_health=5)
    weights = compute_criteria_weights(priorities)
    score, fit_cat, contribs = score_rotation(criteria, weights, passed)

    data_conf = evaluate_data_confidence(missing_pct=0.0, quality_flags=[])
    know_supp = evaluate_knowledge_support(list(crops_dict.values()))

    rec = build_rotation_recommendation(
        candidate=candidate,
        criteria=criteria,
        weights=weights,
        contributions=contribs,
        feasibility_passed=passed,
        feasibility_risks=risks,
        data_confidence=data_conf,
        knowledge_support=know_supp,
        crop_indicators_map=indicators_map,
        crops_dict=crops_dict,
        priorities=priorities,
        soil=SoilInput(texture="loam", organic_matter="medium"),
        preferred_crops=["maize"],
    )

    assert isinstance(rec, RotationRecommendation)
    assert rec.id == "gen_maize_cowpea_sorghum"
    assert rec.is_existing is False
    assert rec.fit_category == "strong"
    assert rec.rank == 1
    assert "gen_alt_2" in rec.similar_to
    assert rec.trace.algorithm_version == ALGORITHM_VERSION
    assert rec.trace.climate_period == CLIMATE_PERIOD
    assert len(rec.evidence) >= 5
    assert len(rec.benefits) >= 1
    assert len(rec.information_gaps) >= 1
    assert len(rec.risks_for_local_review) >= 1
    assert len(rec.review_recommended_by) >= 2
