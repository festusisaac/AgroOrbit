"""Quality and confidence evaluation for data completeness and knowledge support.

Strictly adheres to Section 8.3 of AGROORBIT_PLAN_v2.md:
- data_confidence: climate record completeness, missing data %, quality flags, unknown farmer inputs.
- knowledge_support: share of relevant crop traits that are verified.
- overall_outcome: clear_leader, similar_options, or no_clear_winner (with mandatory message).
"""

from typing import Any, Dict, List, Optional, Tuple
from app.config import SCORE_SIMILARITY_THRESHOLD
from app.models import Confidence, SoilInput


def evaluate_data_confidence(
    missing_pct: float,
    quality_flags: List[str],
    soil: Optional[SoilInput] = None,
) -> Confidence:
    """Evaluates data confidence based on NASA record quality and farmer soil inputs."""
    reasons: List[str] = []
    confidence_points = 100

    # 1. Spatial resolution honesty (always present per Section 6.1)
    reasons.append("NASA POWER meteorology is a coarse global grid (~27 km), not a field-level sensor")

    # 2. Soil inputs evaluation
    if soil:
        unknown_inputs = []
        if soil.texture == "unknown":
            unknown_inputs.append("texture")
            confidence_points -= 15
        if soil.drainage == "unknown":
            unknown_inputs.append("drainage")
            confidence_points -= 15
        if soil.organic_matter == "unknown":
            unknown_inputs.append("organic matter")
            confidence_points -= 10
        if soil.slope == "unknown":
            unknown_inputs.append("slope")
            confidence_points -= 10

        if unknown_inputs:
            reasons.append(f"Farmer soil context incomplete: {', '.join(unknown_inputs)} unknown")

    # 3. Climate completeness
    if missing_pct > 5.0:
        confidence_points -= 25
        reasons.append(f"Historical climate record contains {missing_pct:.1f}% missing days")

    if quality_flags:
        confidence_points -= 20
        reasons.append(f"Climate quality flags active: {', '.join(quality_flags)}")

    if confidence_points >= 75:
        level = "high"
    elif confidence_points >= 45:
        level = "medium"
    else:
        level = "low"

    return Confidence(level=level, reasons=reasons)


def evaluate_knowledge_support(
    crops: List[Any],
    priority_weights: Optional[Dict[str, float]] = None,
) -> Confidence:
    """Evaluates knowledge support confidence based on the proportion of verified traits."""
    reasons: List[str] = []

    if not crops:
        return Confidence(level="low", reasons=["No crops evaluated in sequence"])

    # Average verified share across crops in sequence
    verified_shares = []
    for c in crops:
        if hasattr(c, "get_verified_share"):
            verified_shares.append(c.get_verified_share())
        elif isinstance(c, dict):
            traits = c.get("traits", {})
            v_cnt = sum(1 for t in traits.values() if isinstance(t, dict) and t.get("verified"))
            verified_shares.append(v_cnt / len(traits) if traits else 0.0)
        else:
            verified_shares.append(0.0)

    avg_share = sum(verified_shares) / len(verified_shares) if verified_shares else 0.0

    if avg_share == 0.0:
        level = "low"
        reasons.append("All crop agronomic traits in this sequence are unverified working placeholders")
    elif avg_share < 0.50:
        level = "low"
        reasons.append(f"Only {int(avg_share * 100)}% of crop traits in this sequence are verified with citations")
    elif avg_share < 0.80:
        level = "medium"
        reasons.append(f"{int(avg_share * 100)}% of crop traits are verified from published extension literature")
    else:
        level = "high"
        reasons.append(f"High agronomic support: {int(avg_share * 100)}% of crop traits are verified with citations")

    return Confidence(level=level, reasons=reasons)


def determine_overall_outcome(
    ranked_rotations: List[Any],
    data_confidence: Confidence,
    knowledge_support: Confidence,
) -> Tuple[str, Optional[str]]:
    """Determines overall outcome: clear_leader, similar_options, or no_clear_winner."""
    if not ranked_rotations:
        return (
            "no_clear_winner",
            "None of the evaluated strategies has enough supporting evidence for a confident recommendation. Additional local soil and agronomic information is needed.",
        )

    best_rotation = ranked_rotations[0]

    # Rule per Section 8.3:
    # Use no_clear_winner when the best rotation is weak, OR both confidences are low.
    best_fit = getattr(best_rotation, "fit_category", None)
    if best_fit is None and isinstance(best_rotation, dict):
        best_fit = best_rotation.get("fit_category")

    if best_fit == "weak" or (data_confidence.level == "low" and knowledge_support.level == "low"):
        return (
            "no_clear_winner",
            "None of the evaluated strategies has enough supporting evidence for a confident recommendation. Additional local soil and agronomic information is needed.",
        )

    # Check for similar options (within SCORE_SIMILARITY_THRESHOLD points)
    if len(ranked_rotations) >= 2:
        r0 = ranked_rotations[0]
        r1 = ranked_rotations[1]
        score_1 = float(r0.score if hasattr(r0, "score") else (r0.get("score", 0.0) if isinstance(r0, dict) else 0.0))
        score_2 = float(r1.score if hasattr(r1, "score") else (r1.get("score", 0.0) if isinstance(r1, dict) else 0.0))
        if abs(score_1 - score_2) < SCORE_SIMILARITY_THRESHOLD:
            return (
                "similar_options",
                f"Multiple strategies perform within {SCORE_SIMILARITY_THRESHOLD} points of each other. Local farmer preference and seed availability should decide.",
            )

    return "clear_leader", None
