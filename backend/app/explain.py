"""Template-based explanation generator connecting recommendations to evidence.

Strictly adheres to Section 8.4 of AGROORBIT_PLAN_v2.md:
- why_suggested: tied to farmer's top priorities and sequence structure.
- evidence: labelled by source ('NASA POWER', 'farmer input', 'crop knowledge base') with real frequencies.
- benefits: concrete agronomic benefits from crop traits and sequence diversity.
- assumptions: transparent modeling and climate assumptions.
- information_gaps: includes EVERY unverified trait used in scoring, plus unknown farmer inputs.
- risks_for_local_review: actionable risks needing local extension review.
- review_recommended_by: relevant local agricultural advisers and specialists.
- trace: audit trace with algorithm version, climate period, weights, and contributions.
"""

from typing import Any, Dict, List, Optional
from app.config import (
    ALGORITHM_VERSION,
    CLIMATE_PERIOD,
    HEAT_STRESS_THRESHOLD_C,
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

# Agronomic traits evaluated during scoring that must be provenance-checked
EVALUATED_TRAIT_KEYS = [
    "season_days",
    "water_need_mm",
    "drought_tolerance",
    "heat_tolerance",
    "nitrogen_fixing",
    "residue_organic_matter",
    "root_depth",
    "ground_cover_erosion",
    "forage_value",
]


def generate_why_suggested(
    sequence: List[str],
    is_existing: bool,
    priorities: PrioritiesInput,
    crops_dict: Dict[str, Any],
    criteria: CriteriaScores,
) -> str:
    """Generates plain-language explanation of why this rotation was suggested, tied to top priorities."""
    crop_names = [
        crops_dict[c].name if c in crops_dict and hasattr(crops_dict[c], "name") else c.capitalize()
        for c in sequence
    ]

    if is_existing:
        base = f"Baseline current rotation ({' → '.join(crop_names)}) evaluated to benchmark your existing practice against 35-year NASA climate indicators and diversified alternatives."
        if criteria.pest_break < 50.0:
            base += " Continuous cereal cropping shows high pest and nutrient depletion risks over multi-year cycles."
        return base

    # Identify farmer's top stated priorities
    priority_map = {
        "water_saving": (priorities.water_saving, "water saving"),
        "soil_health": (priorities.soil_health, "soil health restoration"),
        "erosion": (priorities.erosion, "erosion control"),
        "market_preference": (priorities.market_preference, "market preference alignment"),
        "forage": (priorities.forage, "livestock fodder value"),
        "resilience": (priorities.resilience, "climate resilience"),
    }

    active_priorities = [
        desc for key, (val, desc) in sorted(priority_map.items(), key=lambda x: -x[1][0])
        if val >= 3
    ]

    # Check for agronomic features in sequence
    has_legume = any(
        c in crops_dict and hasattr(crops_dict[c], "traits") and
        crops_dict[c].traits.get("nitrogen_fixing") and
        crops_dict[c].traits["nitrogen_fixing"].value is True
        for c in sequence
    )
    has_drought_cereal = any(
        c in crops_dict and hasattr(crops_dict[c], "traits") and
        crops_dict[c].traits.get("drought_tolerance") and
        isinstance(crops_dict[c].traits["drought_tolerance"].value, (int, float)) and
        crops_dict[c].traits["drought_tolerance"].value >= 4
        for c in sequence
    )

    if active_priorities:
        priority_str = " and ".join(active_priorities[:2])
        if has_legume and "soil health restoration" in priority_str:
            return (
                f"Suggested because it directly advances your priority for {priority_str} by integrating "
                f"nitrogen-fixing legumes to restore soil fertility while maintaining grain production."
            )
        elif has_drought_cereal and ("water saving" in priority_str or "climate resilience" in priority_str):
            return (
                f"Suggested because it directly advances your priority for {priority_str}, pairing drought-hardy "
                f"staple cereals with moisture-efficient break crops to buffer against seasonal dry spells."
            )
        else:
            return (
                f"Suggested because it provides strong multi-criteria alignment with your priorities for {priority_str}, "
                f"balancing seasonal crop water fit, soil organic matter, and production stability."
            )

    # Neutral fallback when all priorities are low or zero
    return (
        f"Suggested as a balanced, agronomic 3-year sequence ({' → '.join(crop_names)}) providing diversified "
        f"staple food security, biological soil replenishment, and pest break benefits."
    )


def generate_evidence_items(
    sequence: List[str],
    crop_indicators_map: Dict[str, Any],
    crops_dict: Dict[str, Any],
    soil: Optional[SoilInput] = None,
    preferred_crops: Optional[List[str]] = None,
) -> List[EvidenceItem]:
    """Generates empirical evidence items, strictly labelled by data source."""
    evidence: List[EvidenceItem] = []
    seq_indicators = [crop_indicators_map.get(c) for c in sequence]
    seq_crops = [crops_dict.get(c) for c in sequence]

    # -----------------------------------------------------------------------
    # 1. Source: NASA POWER (Climate & Crop-window indicators)
    # -----------------------------------------------------------------------
    # Season completion
    completion_parts = []
    water_parts = []
    dry_spell_parts = []
    heat_days_list = []

    for cid, ind in zip(sequence, seq_indicators):
        cname = ind.crop_name if ind else cid.capitalize()
        if ind and hasattr(ind, "can_complete_freq"):
            completion_parts.append(f"{cname}: {ind.can_complete_freq.formatted} ({ind.can_complete_freq.frequency_pct:.0f}%)")
        if ind and hasattr(ind, "water_ok_freq"):
            water_parts.append(f"{cname}: {ind.water_ok_freq.formatted} ({ind.water_ok_freq.frequency_pct:.0f}%)")
        if ind and hasattr(ind, "critical_dry_spell_risk_freq"):
            dry_spell_parts.append(f"{cname}: {ind.critical_dry_spell_risk_freq.formatted}")
        if ind and hasattr(ind, "heat_days_median"):
            heat_days_list.append(ind.heat_days_median)

    if completion_parts:
        evidence.append(
            EvidenceItem(
                source="NASA POWER",
                metric="Historical season completion frequency",
                value="; ".join(completion_parts),
                meaning="Share of multi-decadal historical years where rainy season length accommodated full crop physiological maturity.",
            )
        )

    if water_parts:
        evidence.append(
            EvidenceItem(
                source="NASA POWER",
                metric="Crop-window rainfall sufficiency",
                value="; ".join(water_parts),
                meaning="Share of historical years where rainfall received during the crop growth window satisfied minimum crop water needs.",
            )
        )

    if dry_spell_parts:
        evidence.append(
            EvidenceItem(
                source="NASA POWER",
                metric="Critical flowering dry-spell risk (>7 rainless days)",
                value="; ".join(dry_spell_parts),
                meaning="Frequency of damaging dry spells occurring during sensitive flowering and grain-filling growth stages (25%-60% of duration).",
            )
        )

    if heat_days_list:
        median_heat = sum(heat_days_list) // len(heat_days_list)
        evidence.append(
            EvidenceItem(
                source="NASA POWER",
                metric=f"Extreme heat stress days (Tmax > {HEAT_STRESS_THRESHOLD_C:.0f}°C)",
                value=f"Median {median_heat} days per season across sequence",
                meaning=f"Daily maximum temperatures exceeding {HEAT_STRESS_THRESHOLD_C:.0f}°C during active growth windows, which can impair pollen viability.",
            )
        )

    # -----------------------------------------------------------------------
    # 2. Source: farmer input
    # -----------------------------------------------------------------------
    if soil:
        tex_val = soil.texture.capitalize() if soil.texture and soil.texture != "unknown" else "Unknown / unstated"
        evidence.append(
            EvidenceItem(
                source="farmer input",
                metric="Soil texture & water-holding capacity",
                value=tex_val,
                meaning=(
                    "Coarse sandy soils drain rapidly requiring frequent rains; loams and clays store water longer to buffer dry spells."
                    if tex_val != "Unknown / unstated"
                    else "Soil texture was not provided; neutral baseline water retention was applied."
                ),
            )
        )

        om_val = soil.organic_matter.capitalize() if soil.organic_matter and soil.organic_matter != "unknown" else "Unknown / unstated"
        evidence.append(
            EvidenceItem(
                source="farmer input",
                metric="Soil organic matter status",
                value=om_val,
                meaning=(
                    "Low organic matter limits nutrient buffering, making legume residues and biomass replenishment critical."
                    if om_val != "Unknown / unstated"
                    else "Organic matter was not specified; default baseline fertility assumed."
                ),
            )
        )

    if preferred_crops:
        matched = [c for c in sequence if c in preferred_crops]
        evidence.append(
            EvidenceItem(
                source="farmer input",
                metric="Alignment with farmer preferred crops",
                value=f"{len(matched)} of {len(sequence)} crops match preferred list ({', '.join(matched) if matched else 'none'})",
                meaning="Directly aligns cropping choices with your household dietary preferences and local commercial market intent.",
            )
        )

    # -----------------------------------------------------------------------
    # 3. Source: crop knowledge base
    # -----------------------------------------------------------------------
    legume_names = []
    families = []
    root_depths = []

    for cid, crop in zip(sequence, seq_crops):
        cname = crop.name if crop else cid.capitalize()
        if crop and hasattr(crop, "traits"):
            t = crop.traits
            if t.get("nitrogen_fixing") and t["nitrogen_fixing"].value is True:
                legume_names.append(cname)
            families.append(crop.family)
            rd = t.get("root_depth").value if "root_depth" in t else "medium"
            root_depths.append(f"{cname} ({rd})")
        else:
            families.append("Unknown")
            root_depths.append(f"{cname} (medium)")

    evidence.append(
        EvidenceItem(
            source="crop knowledge base",
            metric="Biological nitrogen fixation",
            value=f"{len(legume_names)} of {len(sequence)} years ({', '.join(legume_names) if legume_names else 'none'})",
            meaning="Symbiotic rhizobia in legume root nodules fix atmospheric nitrogen, replenishing soil nitrogen reserves for subsequent cereal crops.",
        )
    )

    evidence.append(
        EvidenceItem(
            source="crop knowledge base",
            metric="Botanical family diversity & pest break",
            value=" → ".join(families),
            meaning="Rotating across distinct botanical families (e.g. Poaceae vs Fabaceae) breaks lifecycles of host-specific pests, root rots, and parasitic Striga weeds.",
        )
    )

    evidence.append(
        EvidenceItem(
            source="crop knowledge base",
            metric="Root depth architecture profile",
            value=", ".join(root_depths),
            meaning="Multi-tiered root depths tap moisture and nutrients from diverse soil depths and improve soil pore channels.",
        )
    )

    return evidence


def generate_benefits(
    sequence: List[str],
    crops_dict: Dict[str, Any],
    criteria: CriteriaScores,
    preferred_crops: Optional[List[str]] = None,
) -> List[str]:
    """Generates plain-language agronomic benefits."""
    benefits: List[str] = []
    seq_crops = [crops_dict.get(c) for c in sequence]

    legumes = [
        crop.name for crop in seq_crops
        if crop and hasattr(crop, "traits") and crop.traits.get("nitrogen_fixing") and crop.traits["nitrogen_fixing"].value is True
    ]
    if legumes:
        benefits.append(
            f"Soil fertility enhancement: Biological nitrogen fixation from {', '.join(legumes)} provides natural nitrogen enrichment, reducing chemical fertilizer costs for subsequent cereals."
        )

    if criteria.pest_break >= 65.0:
        benefits.append(
            "Pest and disease suppression: Alternating cereal and legume families interrupts the host cycles of stem borers, fungal foliar blights, and parasitic Striga hermonthica."
        )
    elif criteria.pest_break < 40.0:
        benefits.append(
            "Staple cereal concentration: Focuses on staple grain output in favorable weather, though requiring careful chemical or manual pest control."
        )

    drought_hardy = [
        crop.name for crop in seq_crops
        if crop and hasattr(crop, "traits") and crop.traits.get("drought_tolerance") and
        isinstance(crop.traits["drought_tolerance"].value, (int, float)) and crop.traits["drought_tolerance"].value >= 4
    ]
    if drought_hardy:
        benefits.append(
            f"Drought buffering: Deep-rooted {', '.join(drought_hardy)} provides dependable grain yield security during erratic rainfall or early season cessation."
        )

    if criteria.forage_value >= 60.0:
        benefits.append(
            "Nutritious livestock fodder: High-quality crop haulms and stover provide valuable dry-season feed for cattle, sheep, and goats."
        )

    if preferred_crops:
        matched = [crops_dict[c].name if c in crops_dict else c.capitalize() for c in sequence if c in preferred_crops]
        if matched:
            benefits.append(
                f"Household & market alignment: Directly produces crops ({', '.join(matched)}) aligned with your stated market and household consumption preferences."
            )

    if not benefits:
        benefits.append("Cropping diversity: Multi-crop sequence provides balanced food security and risk distribution across growing seasons.")

    return benefits


def generate_assumptions(
    soil: Optional[SoilInput] = None,
) -> List[str]:
    """Documents transparent modeling assumptions applied during evaluation."""
    assumptions: List[str] = [
        "Main-season planting is assumed to occur within 7 days of verified climatological rainy season onset.",
        "NASA POWER meteorological data represents a 0.25° (~27 km) spatial grid cell capturing regional climate rather than field-level microclimate.",
        "Rain-fed farming conditions are assumed without major supplemental irrigation.",
        "Crop maturity durations, water needs, and stress thresholds reflect regional savanna cultivars.",
    ]

    if soil:
        unstated = []
        if soil.texture == "unknown":
            unstated.append("soil texture")
        if soil.drainage == "unknown":
            unstated.append("soil drainage")
        if soil.organic_matter == "unknown":
            unstated.append("organic matter")
        if soil.slope == "unknown":
            unstated.append("slope")

        if unstated:
            assumptions.append(
                f"Unstated farmer soil parameters ({', '.join(unstated)}) were evaluated with neutral heuristic weights without bonuses or penalties."
            )

    return assumptions


def generate_information_gaps(
    sequence: List[str],
    crops_dict: Dict[str, Any],
    soil: Optional[SoilInput] = None,
    preferred_crops: Optional[List[str]] = None,
) -> List[str]:
    """Generates comprehensive information gaps including EVERY unverified trait used in scoring."""
    gaps: List[str] = []

    # 1. Unverified crop traits check
    for cid in sequence:
        crop = crops_dict.get(cid)
        if not crop or not hasattr(crop, "traits"):
            gaps.append(
                f"Unrecognized crop '{cid}': Not cataloged in regional savanna knowledge base; neutral default agronomic parameters were applied."
            )
            continue

        cname = crop.name
        for trait_key in EVALUATED_TRAIT_KEYS:
            trait_obj = crop.traits.get(trait_key)
            if trait_obj is not None:
                # Check verified flag and source
                if not trait_obj.verified or trait_obj.source is None:
                    val_str = trait_obj.value
                    if isinstance(val_str, dict) and "min" in val_str and "max" in val_str:
                        val_str = f"{val_str['min']}-{val_str['max']}"
                    gaps.append(
                        f"Unverified crop trait: {cname} '{trait_key}' (working value: {val_str}) is an unverified placeholder pending extension literature citation."
                    )

    # 2. Unknown farmer inputs check
    if soil:
        if soil.texture == "unknown":
            gaps.append("Field soil texture is unknown; local water percolation and moisture retention could not be modeled precisely.")
        if soil.drainage == "unknown":
            gaps.append("Field soil drainage is unknown; waterlogging and root aeration stress risks could not be verified.")
        if soil.organic_matter == "unknown":
            gaps.append("Soil organic matter status is unknown; baseline nutrient retention capacity was estimated neutrally.")
        if soil.slope == "unknown":
            gaps.append("Field slope is unknown; runoff velocity and water erosion hazards were defaulted to neutral.")

    if not preferred_crops:
        gaps.append("No preferred marketable crops were stated; market preference criterion was evaluated at neutral 50%.")

    return gaps


def generate_risks_for_local_review(
    sequence: List[str],
    criteria: CriteriaScores,
    feasibility_passed: bool,
    feasibility_risks: List[str],
    crop_indicators_map: Dict[str, Any],
    crops_dict: Dict[str, Any],
    soil: Optional[SoilInput] = None,
) -> List[str]:
    """Identifies actionable agronomic and climate risks needing local extension review."""
    risks: List[str] = []

    # Feasibility gate failures
    if not feasibility_passed and feasibility_risks:
        risks.extend(feasibility_risks)

    # Unrecognized crop warning
    for cid in sequence:
        if cid not in crops_dict:
            risks.append(
                f"Unrecognized crop '{cid}': Growth duration, water requirements, and regional savanna suitability cannot be validated without local extension consultation."
            )

    # Monoculture / pest risk
    if criteria.pest_break < 50.0:
        risks.append(
            "Monoculture / pest risk: Consecutive years of cereal planting significantly increases susceptibility to parasitic Striga weed, root rot fungi, and stem borer buildup."
        )

    # Mid-season dry spells risk
    for cid in sequence:
        ind = crop_indicators_map.get(cid)
        if ind and hasattr(ind, "critical_dry_spell_risk_freq"):
            freq = ind.critical_dry_spell_risk_freq
            if freq.frequency_pct >= 15.0:
                risks.append(
                    f"Flowering dry-spell hazard: Historical records show severe dry spells (>7 rainless days) during {ind.crop_name}'s flowering stage in {freq.formatted} ({freq.frequency_pct:.0f}%). Water conservation practices (e.g. tied ridges) are advised."
                )

    # Heat stress risk
    for cid in sequence:
        ind = crop_indicators_map.get(cid)
        if ind and hasattr(ind, "heat_stress_risk_freq"):
            freq = ind.heat_stress_risk_freq
            if freq.frequency_pct >= 15.0:
                risks.append(
                    f"Thermal stress risk: {ind.crop_name} experiences extreme temperatures (>35°C) during reproductive stages in {freq.formatted}. Verify local certified heat-tolerant cultivars."
                )

    # Soil-specific risk heuristics
    if soil:
        if soil.slope == "steep" and criteria.erosion_protection < 65.0:
            risks.append(
                "Erosion risk: Steep field slope combined with moderate ground cover canopy poses topsoil wash-away risk during heavy early-season thunderstorms."
            )
        if soil.texture == "sandy" and criteria.water_fit < 65.0:
            risks.append(
                "Leaching & drought sensitivity: Sandy soil drains quickly, accentuating moisture deficits between rainfall events."
            )

    # Market and seed input verification
    risks.append(
        "Local input & market availability: Certified seeds of adapted maturity, Rhizobium inoculants (for legumes), and local buyer market prices should be confirmed locally prior to planting."
    )

    return risks


def generate_review_recommended_by(
    criteria: CriteriaScores,
    soil: Optional[SoilInput] = None,
) -> List[str]:
    """Recommends local specialists who should review this recommendation."""
    reviewers: List[str] = [
        "Local Agricultural Extension Officer (ADP / State Ministry of Agriculture)",
        "Community Farm Cooperative Lead Agronomist",
    ]

    if soil and soil.slope == "steep":
        reviewers.append("Soil & Water Conservation Specialist")

    if criteria.pest_break < 50.0:
        reviewers.append("Crop Protection & Integrated Pest Management (IPM) Specialist")

    return reviewers


def build_rotation_recommendation(
    candidate: Dict[str, Any],
    criteria: CriteriaScores,
    weights: Dict[str, float],
    contributions: Dict[str, float],
    feasibility_passed: bool,
    feasibility_risks: List[str],
    data_confidence: Confidence,
    knowledge_support: Confidence,
    crop_indicators_map: Dict[str, Any],
    crops_dict: Dict[str, Any],
    priorities: PrioritiesInput,
    soil: Optional[SoilInput] = None,
    preferred_crops: Optional[List[str]] = None,
) -> RotationRecommendation:
    """Builds a complete, validated RotationRecommendation instance."""
    sequence = candidate["sequence"]
    is_existing = candidate.get("is_existing", False)

    why_suggested = generate_why_suggested(
        sequence=sequence,
        is_existing=is_existing,
        priorities=priorities,
        crops_dict=crops_dict,
        criteria=criteria,
    )

    evidence = generate_evidence_items(
        sequence=sequence,
        crop_indicators_map=crop_indicators_map,
        crops_dict=crops_dict,
        soil=soil,
        preferred_crops=preferred_crops,
    )

    benefits = generate_benefits(
        sequence=sequence,
        crops_dict=crops_dict,
        criteria=criteria,
        preferred_crops=preferred_crops,
    )

    assumptions = generate_assumptions(soil=soil)

    information_gaps = generate_information_gaps(
        sequence=sequence,
        crops_dict=crops_dict,
        soil=soil,
        preferred_crops=preferred_crops,
    )

    risks = generate_risks_for_local_review(
        sequence=sequence,
        criteria=criteria,
        feasibility_passed=feasibility_passed,
        feasibility_risks=feasibility_risks,
        crop_indicators_map=crop_indicators_map,
        crops_dict=crops_dict,
        soil=soil,
    )

    reviewers = generate_review_recommended_by(criteria=criteria, soil=soil)

    trace = TraceInfo(
        algorithm_version=ALGORITHM_VERSION,
        climate_period=CLIMATE_PERIOD,
        priority_weights_applied=weights,
        criteria_contributions=contributions,
    )

    return RotationRecommendation(
        id=candidate["id"],
        label=candidate["label"],
        is_existing=is_existing,
        sequence=sequence,
        score=float(candidate["score"]),
        fit_category=candidate["fit_category"],
        rank=int(candidate["rank"]),
        similar_to=candidate.get("similar_to", []),
        criteria=criteria,
        data_confidence=data_confidence,
        knowledge_support=knowledge_support,
        why_suggested=why_suggested,
        evidence=evidence,
        benefits=benefits,
        assumptions=assumptions,
        information_gaps=information_gaps,
        risks_for_local_review=risks,
        review_recommended_by=reviewers,
        trace=trace,
    )
