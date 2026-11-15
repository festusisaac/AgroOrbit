"""Deterministic scoring engine for evaluating candidate crop rotations against criteria.

Strictly adheres to Section 8 of AGROORBIT_PLAN_v2.md:
- 8.1 Eight criteria scored 0-100 per rotation (averaged across sequence).
- 8.2 Priority-to-criteria mapping, 10% safety weight on season_fit, equal weights on all-zero.
- 8.2 Feasibility gate (<50% season completion caps category at weak; modifiers cannot override).
- 8.3 Fit categories (strong >= 75, moderate 55-74, weak < 55), similarity flag (< 5 pts).
- Deterministic: Identical inputs strictly produce identical outputs.
"""

from typing import Any, Dict, List, Optional, Tuple
from app.config import (
    FEASIBILITY_COMPLETION_MIN_PCT,
    SAFETY_WEIGHT_SEASON_FIT,
    SCORE_MODERATE_MIN,
    SCORE_SIMILARITY_THRESHOLD,
    SCORE_STRONG_MIN,
)
from app.models import CriteriaScores, PrioritiesInput, SoilInput

CRITERIA_KEYS = [
    "water_fit",
    "season_fit",
    "heat_drought_resilience",
    "soil_health",
    "pest_break",
    "erosion_protection",
    "market_preference_fit",
    "forage_value",
]


def compute_criteria_weights(
    priorities: PrioritiesInput,
    safety_weight: float = SAFETY_WEIGHT_SEASON_FIT,
) -> Dict[str, float]:
    """Computes normalized criteria weights from farmer priorities with safety weighting.

    Rules (Section 8.2):
    - water_saving -> water_fit (100%)
    - soil_health -> soil_health (50%) + pest_break (50%)
    - erosion -> erosion_protection (100%)
    - market_preference -> market_preference_fit (100%)
    - forage -> forage_value (100%)
    - resilience -> season_fit (50%) + heat_drought_resilience (50%)
    - If all priorities are 0, use equal weights (never divide by zero).
    - Apply fixed safety weight (default 10%) to season_fit.
    """
    raw_weights: Dict[str, float] = {k: 0.0 for k in CRITERIA_KEYS}

    raw_weights["water_fit"] += float(priorities.water_saving)
    raw_weights["soil_health"] += float(priorities.soil_health) * 0.50
    raw_weights["pest_break"] += float(priorities.soil_health) * 0.50
    raw_weights["erosion_protection"] += float(priorities.erosion)
    raw_weights["market_preference_fit"] += float(priorities.market_preference)
    raw_weights["forage_value"] += float(priorities.forage)
    raw_weights["season_fit"] += float(priorities.resilience) * 0.50
    raw_weights["heat_drought_resilience"] += float(priorities.resilience) * 0.50

    total_priority_sum = sum(raw_weights.values())

    if total_priority_sum <= 0.0:
        # Equal weights fallback when all priorities are 0
        equal_weight = 1.0 / len(CRITERIA_KEYS)
        base_weights = {k: equal_weight for k in CRITERIA_KEYS}
    else:
        # Normalized weights
        base_weights = {k: v / total_priority_sum for k, v in raw_weights.items()}

    # Apply fixed safety weight to season_fit:
    # W_final = (1 - safety) * base_w + (safety if season_fit else 0)
    final_weights: Dict[str, float] = {}
    for k, w in base_weights.items():
        if k == "season_fit":
            final_weights[k] = round(w * (1.0 - safety_weight) + safety_weight, 4)
        else:
            final_weights[k] = round(w * (1.0 - safety_weight), 4)

    # Normalize slight rounding drift to sum exactly to 1.0
    weight_sum = sum(final_weights.values())
    final_weights = {k: round(v / weight_sum, 4) for k, v in final_weights.items()}

    return final_weights


def calculate_criteria_scores(
    sequence: List[str],
    crop_indicators_map: Dict[str, Any],
    crops_dict: Dict[str, Any],
    soil: Optional[SoilInput] = None,
    preferred_crops: Optional[List[str]] = None,
    soil_modifiers: Optional[Dict[str, Any]] = None,
) -> Tuple[CriteriaScores, bool, List[str]]:
    """Calculates the eight criteria (0-100) and checks feasibility gate.

    Returns:
        Tuple of (CriteriaScores, feasibility_passed, feasibility_risks)
    """
    if preferred_crops is None:
        preferred_crops = []

    seq_crops = [crops_dict.get(cid) for cid in sequence]
    seq_indicators = [crop_indicators_map.get(cid) for cid in sequence]

    feasibility_passed = True
    feasibility_risks: List[str] = []

    # -----------------------------------------------------------------------
    # 1. Season Fit & Feasibility Gate
    # -----------------------------------------------------------------------
    season_fits = []
    for cid, ind in zip(sequence, seq_indicators):
        if ind and hasattr(ind, "can_complete_freq"):
            pct = ind.can_complete_freq.frequency_pct
        else:
            pct = 70.0  # fallback
        season_fits.append(pct)

        # FEASIBILITY GATE: crop completes season in < 50% of years
        if pct < FEASIBILITY_COMPLETION_MIN_PCT:
            feasibility_passed = False
            crop_name = ind.crop_name if ind else cid.capitalize()
            feasibility_risks.append(
                f"Feasibility gate triggered: {crop_name} completes the season in only {pct:.1f}% of historical years (<50% threshold)."
            )

    season_fit_score = round(sum(season_fits) / len(season_fits), 1)

    # -----------------------------------------------------------------------
    # 2. Water Fit (with soil texture and drainage modifiers)
    # -----------------------------------------------------------------------
    water_fits = []
    # Soil texture modifier heuristic
    texture_mod = 0
    if soil and soil_modifiers and "texture" in soil_modifiers:
        texture_data = soil_modifiers["texture"].get(soil.texture, {})
        texture_mod = texture_data.get("water_fit_modifier", 0)

    # Soil OM buffer modifier heuristic
    om_mod = 0
    if soil and soil_modifiers and "organic_matter" in soil_modifiers:
        om_data = soil_modifiers["organic_matter"].get(soil.organic_matter, {})
        om_mod = om_data.get("water_buffer_penalty", 0) or om_data.get("water_buffer_bonus", 0)

    for ind in seq_indicators:
        if ind and hasattr(ind, "water_ok_freq") and hasattr(ind, "critical_dry_spell_risk_freq"):
            # Base water fit: frequency of water sufficiency minus critical dry spell penalty
            water_ok_pct = ind.water_ok_freq.frequency_pct
            dry_spell_pct = ind.critical_dry_spell_risk_freq.frequency_pct
            base_water = max(0.0, water_ok_pct - 0.40 * dry_spell_pct)
        else:
            base_water = 65.0

        # Apply heuristic modifiers
        adjusted_water = max(0.0, min(100.0, base_water + texture_mod + om_mod))
        water_fits.append(adjusted_water)

    water_fit_score = round(sum(water_fits) / len(water_fits), 1)

    # -----------------------------------------------------------------------
    # 3. Heat & Drought Resilience
    # -----------------------------------------------------------------------
    resilience_scores = []
    for crop, ind in zip(seq_crops, seq_indicators):
        if ind and ind.valid_years_count > 0:
            # Exposure = share of years with critical dry spell OR heat days
            exp_count = sum(1 for y in ind.yearly_indicators if y.quality_flag == "ok" and (y.mid_season_dry_spell or y.heat_days > 0))
            exposure = exp_count / ind.valid_years_count
        else:
            exposure = 0.35

        # Tolerance factor from traits
        traits = crop.traits if crop and hasattr(crop, "traits") else {}
        d_val = traits.get("drought_tolerance").value if "drought_tolerance" in traits else 3
        h_val = traits.get("heat_tolerance").value if "heat_tolerance" in traits else 3
        d_val = d_val if isinstance(d_val, (int, float)) else 3
        h_val = h_val if isinstance(h_val, (int, float)) else 3

        tolerance_factor = max(0.20, min(1.0, (d_val + h_val) / 10.0))
        crop_resilience = 100.0 * (1.0 - exposure * (1.0 - tolerance_factor))
        resilience_scores.append(max(0.0, min(100.0, crop_resilience)))

    heat_drought_resilience_score = round(sum(resilience_scores) / len(resilience_scores), 1)

    # -----------------------------------------------------------------------
    # 4. Soil Health
    # -----------------------------------------------------------------------
    # a) Nitrogen fixing share (up to 40 pts)
    n_fixing_count = 0
    residue_vals = []
    root_depths = set()

    for crop in seq_crops:
        if crop and hasattr(crop, "traits"):
            t = crop.traits
            if t.get("nitrogen_fixing") and t["nitrogen_fixing"].value is True:
                n_fixing_count += 1
            r_val = t.get("residue_organic_matter").value if "residue_organic_matter" in t else 3
            residue_vals.append(r_val if isinstance(r_val, (int, float)) else 3)
            rd = t.get("root_depth").value if "root_depth" in t else "medium"
            root_depths.add(rd)
        else:
            residue_vals.append(3)

    n_fix_pts = (n_fixing_count / len(sequence)) * 40.0

    # b) Residue score (scale 1-5 -> up to 40 pts)
    avg_residue = sum(residue_vals) / len(residue_vals) if residue_vals else 3.0
    residue_pts = (avg_residue / 5.0) * 40.0

    # c) Root depth diversity (up to 20 pts)
    unique_depths = len(root_depths)
    if unique_depths >= 3:
        root_pts = 20.0
    elif unique_depths == 2:
        root_pts = 12.0
    else:
        root_pts = 5.0

    raw_soil_health = n_fix_pts + residue_pts + root_pts

    # Adjust if farmer organic matter is low (OM multiplier heuristic)
    if soil and soil.organic_matter == "low":
        raw_soil_health *= 1.15

    soil_health_score = round(max(0.0, min(100.0, raw_soil_health)), 1)

    # -----------------------------------------------------------------------
    # 5. Pest Break (Crop family diversity across consecutive years)
    # -----------------------------------------------------------------------
    families = []
    for crop in seq_crops:
        fam = crop.family if crop and hasattr(crop, "family") else "unknown"
        families.append(fam)

    pest_break_pts = 100.0
    for i in range(len(families) - 1):
        if families[i] == families[i + 1] and families[i] != "unknown":
            pest_break_pts -= 35.0  # Monoculture family penalty

    pest_break_score = round(max(0.0, min(100.0, pest_break_pts)), 1)

    # -----------------------------------------------------------------------
    # 6. Erosion Protection (Ground cover trait + slope adjustment)
    # -----------------------------------------------------------------------
    cover_vals = []
    for crop in seq_crops:
        if crop and hasattr(crop, "traits"):
            t = crop.traits
            c_val = t.get("ground_cover_erosion").value if "ground_cover_erosion" in t else 3
            cover_vals.append(c_val if isinstance(c_val, (int, float)) else 3)
        else:
            cover_vals.append(3)

    avg_cover = sum(cover_vals) / len(cover_vals) if cover_vals else 3.0
    base_erosion = (avg_cover / 5.0) * 100.0

    # Slope modifier heuristic: steep slope penalizes poor cover
    if soil and soil.slope == "steep" and base_erosion < 65.0:
        base_erosion -= 15.0
    elif soil and soil.slope == "flat":
        base_erosion = min(100.0, base_erosion + 5.0)

    erosion_protection_score = round(max(0.0, min(100.0, base_erosion)), 1)

    # -----------------------------------------------------------------------
    # 7. Market Preference Fit
    # -----------------------------------------------------------------------
    if not preferred_crops:
        market_preference_score = 50.0  # Neutral when no preferences stated
    else:
        matched = sum(1 for cid in sequence if cid in preferred_crops)
        market_preference_score = round((matched / len(sequence)) * 100.0, 1)

    # -----------------------------------------------------------------------
    # 8. Forage Value
    # -----------------------------------------------------------------------
    forage_vals = []
    for crop in seq_crops:
        if crop and hasattr(crop, "traits"):
            t = crop.traits
            f_val = t.get("forage_value").value if "forage_value" in t else 3
            forage_vals.append(f_val if isinstance(f_val, (int, float)) else 3)
        else:
            forage_vals.append(3)

    avg_forage = sum(forage_vals) / len(forage_vals) if forage_vals else 3.0
    forage_value_score = round((avg_forage / 5.0) * 100.0, 1)

    criteria = CriteriaScores(
        water_fit=water_fit_score,
        season_fit=season_fit_score,
        heat_drought_resilience=heat_drought_resilience_score,
        soil_health=soil_health_score,
        pest_break=pest_break_score,
        erosion_protection=erosion_protection_score,
        market_preference_fit=market_preference_score,
        forage_value=forage_value_score,
    )

    return criteria, feasibility_passed, feasibility_risks


def score_rotation(
    criteria: CriteriaScores,
    weights: Dict[str, float],
    feasibility_passed: bool = True,
) -> Tuple[float, str, Dict[str, float]]:
    """Computes overall score (0-100), fit category, and criteria contributions.

    Rule (Section 8.2 & 8.3):
    - Feasibility gate failure strictly caps fit_category at 'weak'.
    - Soil modifiers must never override this gate.
    """
    crit_dict = criteria.model_dump()
    contributions: Dict[str, float] = {}
    total_score = 0.0

    for k in CRITERIA_KEYS:
        w = weights.get(k, 0.0)
        c_val = crit_dict.get(k, 0.0)
        contrib = round(c_val * w, 2)
        contributions[k] = contrib
        total_score += contrib

    score = round(max(0.0, min(100.0, total_score)), 1)

    # Categorization
    if not feasibility_passed:
        fit_category = "weak"
    elif score >= SCORE_STRONG_MIN:
        fit_category = "strong"
    elif score >= SCORE_MODERATE_MIN:
        fit_category = "moderate"
    else:
        fit_category = "weak"

    return score, fit_category, contributions


def rank_and_mark_similar_rotations(
    evaluated_rotations: List[Dict[str, Any]],
    similarity_threshold: float = SCORE_SIMILARITY_THRESHOLD,
) -> List[Dict[str, Any]]:
    """Ranks rotations by score descending and flags rotations within similarity threshold."""
    # Deterministic sort: primarily by score descending, secondarily by id for reproducibility
    sorted_rotations = sorted(
        evaluated_rotations,
        key=lambda r: (-float(r["score"]), str(r["id"])),
    )

    # Assign ranks
    for rank_idx, r in enumerate(sorted_rotations, start=1):
        r["rank"] = rank_idx
        if "similar_to" not in r:
            r["similar_to"] = []

    # Identify similar pairs
    for i in range(len(sorted_rotations)):
        for j in range(i + 1, len(sorted_rotations)):
            diff = abs(float(sorted_rotations[i]["score"]) - float(sorted_rotations[j]["score"]))
            if diff < similarity_threshold:
                id_i = sorted_rotations[i]["id"]
                id_j = sorted_rotations[j]["id"]
                if id_j not in sorted_rotations[i]["similar_to"]:
                    sorted_rotations[i]["similar_to"].append(id_j)
                if id_i not in sorted_rotations[j]["similar_to"]:
                    sorted_rotations[j]["similar_to"].append(id_i)

    return sorted_rotations


def select_and_rank_recommendations(
    evaluated_candidates: List[Dict[str, Any]],
    max_total: int = 5,
    similarity_threshold: float = SCORE_SIMILARITY_THRESHOLD,
) -> List[Dict[str, Any]]:
    """Selects and ranks candidate rotations adhering strictly to Section 7.3:

    1. Always includes the farmer's existing rotation (even if not in library).
    2. Includes at least 2 genuinely different alternatives (differing by >= 1 crop).
    3. Capped at max_total (default 5, min 3).
    4. Deterministically sorted by score descending (with id tie-breaker).
    5. Flags rotations within similarity_threshold (< 5 points).
    """
    existing_cand = None
    alternatives: List[Dict[str, Any]] = []

    for cand in evaluated_candidates:
        if cand.get("is_existing"):
            existing_cand = cand
        else:
            alternatives.append(cand)

    if existing_cand is None:
        raise ValueError("Evaluated candidates must include the farmer's existing rotation.")

    # Sort all alternatives deterministically by score descending, then by id
    alternatives.sort(key=lambda c: (-float(c["score"]), str(c["id"])))

    # Select top distinct alternatives differing by >= 1 crop in sequence
    selected_alts: List[Dict[str, Any]] = []
    existing_seq = tuple(c.lower() for c in existing_cand["sequence"])

    for alt in alternatives:
        alt_seq = tuple(c.lower() for c in alt["sequence"])
        if alt_seq == existing_seq:
            continue
        # Ensure distinct from previously selected alternatives
        if any(alt_seq == tuple(c.lower() for c in s["sequence"]) for s in selected_alts):
            continue
        selected_alts.append(alt)
        if len(selected_alts) >= (max_total - 1):
            break

    # Must guarantee at least 2 alternatives
    if len(selected_alts) < 2:
        for alt in alternatives:
            if alt not in selected_alts and tuple(c.lower() for c in alt["sequence"]) != existing_seq:
                selected_alts.append(alt)
                if len(selected_alts) >= 2:
                    break

    # Combine existing + selected alternatives
    final_selection = [existing_cand] + selected_alts

    # Rank and mark similar
    return rank_and_mark_similar_rotations(
        evaluated_rotations=final_selection,
        similarity_threshold=similarity_threshold,
    )


_BASELINE_INDICATORS_CACHE: Dict[Tuple[float, float], Tuple[Any, Dict[str, Any]]] = {}


def generate_recommendations(
    payload: Any,
    nasa_power_client: Optional[Any] = None,
    df: Optional[Any] = None,
    meta: Optional[Dict[str, Any]] = None,
) -> Any:
    """Full end-to-end recommendation pipeline.

    Computes multi-decadal indicators, generates candidate rotations,
    scores criteria, applies feasibility gate, evaluates confidences,
    and returns RecommendResponse with evidence-based explanations.
    """
    from app.climate import calculate_annual_seasons, compute_crop_climate_indicators
    from app.config import DISCLAIMER_TEXT
    from app.explain import build_rotation_recommendation
    from app.knowledge import (
        generate_candidate_rotations,
        load_crops,
        load_rotations,
        load_soil_modifiers,
    )
    from app.models import RecommendResponse
    from app.quality import (
        determine_overall_outcome,
        evaluate_data_confidence,
        evaluate_knowledge_support,
    )

    if df is None:
        if nasa_power_client is None:
            from app.nasa_power import NasaPowerClient
            nasa_power_client = NasaPowerClient()
        df, fetched_meta = nasa_power_client.fetch_daily_data(lat=payload.lat, lon=payload.lon)
        if meta is None:
            meta = fetched_meta

    if meta is None:
        meta = {}

    missing_pct = float(meta.get("overall_missing_pct", 0.0))
    quality_flags = list(meta.get("quality_flags", []))

    is_scenario = False
    if hasattr(payload, "scenario") and payload.scenario:
        scen = payload.scenario
        rain_chg = getattr(scen, "rainfall_change_pct", 0.0)
        temp_chg = getattr(scen, "temperature_change_c", 0.0)
        if rain_chg != 0.0 or temp_chg != 0.0:
            is_scenario = True
            df = df.copy()
            if rain_chg != 0.0 and "PRECTOTCORR" in df.columns:
                df["PRECTOTCORR"] = df["PRECTOTCORR"] * (1.0 + rain_chg / 100.0)
            if temp_chg != 0.0:
                if "T2M" in df.columns:
                    df["T2M"] = df["T2M"] + temp_chg
                if "T2M_MAX" in df.columns:
                    df["T2M_MAX"] = df["T2M_MAX"] + temp_chg
                if "T2M_MIN" in df.columns:
                    df["T2M_MIN"] = df["T2M_MIN"] + temp_chg

    crops_dict = load_crops()
    rotations_lib = load_rotations()
    soil_modifiers = load_soil_modifiers()

    # Fast in-memory memoization for baseline climate calculations
    coord_key = (round(float(payload.lat), 4), round(float(payload.lon), 4))
    if not is_scenario and coord_key in _BASELINE_INDICATORS_CACHE:
        cached_seasons, cached_indicators = _BASELINE_INDICATORS_CACHE[coord_key]
        seasons_df = cached_seasons
        crop_indicators_map = dict(cached_indicators)
        for c in payload.current_rotation:
            c_clean = c.strip().lower()
            if c_clean and c_clean not in crop_indicators_map:
                crop_obj = crops_dict.get(c_clean, c_clean)
                crop_indicators_map[c_clean] = compute_crop_climate_indicators(
                    crop=crop_obj, df=df, seasons_df=seasons_df
                )
    else:
        seasons_df = calculate_annual_seasons(df)
        all_needed_crops = set(crops_dict.keys())
        for c in payload.current_rotation:
            c_clean = c.strip().lower()
            if c_clean:
                all_needed_crops.add(c_clean)

        crop_indicators_map = {}
        for cid in all_needed_crops:
            crop_obj = crops_dict.get(cid, cid)
            crop_indicators_map[cid] = compute_crop_climate_indicators(
                crop=crop_obj,
                df=df,
                seasons_df=seasons_df,
            )
        if not is_scenario:
            _BASELINE_INDICATORS_CACHE[coord_key] = (seasons_df, crop_indicators_map)

    # 1. Generate all candidate sequences
    candidates = generate_candidate_rotations(
        current_rotation=payload.current_rotation,
        library_rotations=rotations_lib,
        crops_dict=crops_dict,
        preferred_crops=payload.preferred_crops,
    )

    # 2. Score every candidate
    weights = compute_criteria_weights(payload.priorities)
    scored_candidates = []
    for cand in candidates:
        criteria, passed, risks = calculate_criteria_scores(
            sequence=cand["sequence"],
            crop_indicators_map=crop_indicators_map,
            crops_dict=crops_dict,
            soil=payload.soil,
            preferred_crops=payload.preferred_crops,
            soil_modifiers=soil_modifiers,
        )
        score, fit_cat, contribs = score_rotation(
            criteria=criteria,
            weights=weights,
            feasibility_passed=passed,
        )
        cand_entry = dict(cand)
        cand_entry["score"] = score
        cand_entry["fit_category"] = fit_cat
        cand_entry["criteria"] = criteria
        cand_entry["contributions"] = contribs
        cand_entry["feasibility_passed"] = passed
        cand_entry["feasibility_risks"] = risks
        scored_candidates.append(cand_entry)

    # 3. Select recommendations (existing + >=2 distinct alternatives, max 5, sorted by score)
    selected = select_and_rank_recommendations(scored_candidates, max_total=5)

    # 4. Evaluate confidences & outcome
    unknown_crops = [c for c in payload.current_rotation if c.strip().lower() not in crops_dict]

    data_confidence = evaluate_data_confidence(
        missing_pct=missing_pct,
        quality_flags=quality_flags,
        soil=payload.soil,
        lat=payload.lat,
        lon=payload.lon,
    )
    knowledge_support = evaluate_knowledge_support(
        crops=list(crops_dict.values()),
        priority_weights=weights,
        unknown_crops=unknown_crops if unknown_crops else None,
    )
    overall_outcome, outcome_message = determine_overall_outcome(
        ranked_rotations=selected,
        data_confidence=data_confidence,
        knowledge_support=knowledge_support,
    )

    # 5. Build full recommendations with explanations
    recommendations = []
    for cand in selected:
        rec = build_rotation_recommendation(
            candidate=cand,
            criteria=cand["criteria"],
            weights=weights,
            contributions=cand["contributions"],
            feasibility_passed=cand["feasibility_passed"],
            feasibility_risks=cand["feasibility_risks"],
            data_confidence=data_confidence,
            knowledge_support=knowledge_support,
            crop_indicators_map=crop_indicators_map,
            crops_dict=crops_dict,
            priorities=payload.priorities,
            soil=payload.soil,
            preferred_crops=payload.preferred_crops,
            lat=payload.lat,
            lon=payload.lon,
            scenario=payload.scenario,
        )
        recommendations.append(rec)

    return RecommendResponse(
        overall_outcome=overall_outcome,
        outcome_message=outcome_message,
        rotations=recommendations,
        disclaimer=DISCLAIMER_TEXT,
    )
