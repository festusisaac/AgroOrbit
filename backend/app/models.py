"""Pydantic data models for the AgroOrbit API contract and internal schemas.

Strictly adheres to Section 9 of AGROORBIT_PLAN_v2.md.
"""

from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Health Models
# ---------------------------------------------------------------------------
class HealthResponse(BaseModel):
    """Health check response."""
    status: str = "ok"


# ---------------------------------------------------------------------------
# Locations Models
# ---------------------------------------------------------------------------
class LocationItem(BaseModel):
    """Preset demo location."""
    id: str
    name: str
    lat: float
    lon: float
    zone: str


# ---------------------------------------------------------------------------
# Crops Models
# ---------------------------------------------------------------------------
class CropItem(BaseModel):
    """Crop summary item."""
    id: str
    name: str
    family: str
    traits_summary: Dict[str, Any]
    verified_share: float = Field(ge=0.0, le=1.0)


# ---------------------------------------------------------------------------
# Climate Models (GET /climate)
# ---------------------------------------------------------------------------
class ClimateLocation(BaseModel):
    lat: float
    lon: float
    label: str


class DatasetInfo(BaseModel):
    name: str
    community: str
    time_standard: str
    resolution_note: str
    period: str


class MonthlyClimate(BaseModel):
    month: int = Field(ge=1, le=12)
    rain_p20: float
    rain_p50: float
    rain_p80: float
    tmax: float
    regional_root_zone_wetness: float


class SeasonStats(BaseModel):
    onset_doy_median: int
    cessation_doy_median: int
    length_days_median: int
    length_days_p20: int
    method: str
    years_ok: int
    years_flagged: int


class SeasonRainTotal(BaseModel):
    median_mm: float
    p20_mm: float
    cv: float


class DrySpells(BaseModel):
    avg_per_season: float
    longest_median_days: int


class HeatStressDays(BaseModel):
    median: int
    threshold_c: float


class Trend(BaseModel):
    season_rain_mm_per_decade: float
    note: str


class BareFieldWindow(BaseModel):
    months: List[int]
    basis: Literal["proxy", "observed"]


class DataQuality(BaseModel):
    from_cache: bool
    missing_pct: float
    flags: List[str] = Field(default_factory=list)


class ClimateResponse(BaseModel):
    """Full climate indicators response for GET /climate."""
    location: ClimateLocation
    datasets: List[DatasetInfo]
    monthly: List[MonthlyClimate]
    season: SeasonStats
    season_rain_total: SeasonRainTotal
    dry_spells: DrySpells
    heat_stress_days: HeatStressDays
    trend: Trend
    bare_field_window: BareFieldWindow
    data_quality: DataQuality


# ---------------------------------------------------------------------------
# Recommend Models (POST /recommend)
# ---------------------------------------------------------------------------
class SoilInput(BaseModel):
    """Farmer-entered soil characteristics (all optional)."""
    texture: Optional[Literal["sandy", "loam", "clay", "unknown"]] = "unknown"
    drainage: Optional[str] = "unknown"
    organic_matter: Optional[Literal["low", "medium", "high", "unknown"]] = "unknown"
    water_source: Optional[Literal["rain_fed", "limited_irrigation", "irrigated"]] = "rain_fed"
    slope: Optional[Literal["flat", "gentle", "steep", "unknown"]] = "unknown"


class PrioritiesInput(BaseModel):
    """Farmer priorities on 0-5 scale."""
    water_saving: int = Field(default=0, ge=0, le=5)
    soil_health: int = Field(default=0, ge=0, le=5)
    erosion: int = Field(default=0, ge=0, le=5)
    market_preference: int = Field(default=0, ge=0, le=5)
    forage: int = Field(default=0, ge=0, le=5)
    resilience: int = Field(default=0, ge=0, le=5)


class ScenarioInput(BaseModel):
    """Hypothetical climate sensitivity scenario parameters (P1)."""
    rainfall_change_pct: float = 0.0
    temperature_change_c: float = 0.0


class RecommendRequest(BaseModel):
    """Request payload for POST /recommend."""
    lat: float
    lon: float
    current_rotation: List[str]
    soil: SoilInput = Field(default_factory=SoilInput)
    priorities: PrioritiesInput = Field(default_factory=PrioritiesInput)
    preferred_crops: List[str] = Field(default_factory=list)
    scenario: ScenarioInput = Field(default_factory=ScenarioInput)


class CriteriaScores(BaseModel):
    """Individual criteria scores (0-100)."""
    water_fit: float
    season_fit: float
    heat_drought_resilience: float
    soil_health: float
    pest_break: float
    erosion_protection: float
    market_preference_fit: float
    forage_value: float


class Confidence(BaseModel):
    """Confidence assessment with explanatory reasons."""
    level: Literal["low", "medium", "high"]
    reasons: List[str]


class EvidenceItem(BaseModel):
    """Specific empirical or factual evidence point for a recommendation."""
    source: Literal["NASA POWER", "farmer input", "crop knowledge base"]
    metric: str
    value: str
    meaning: str


class TraceInfo(BaseModel):
    """Audit trace documenting engine version and weighting."""
    algorithm_version: str
    climate_period: str
    priority_weights_applied: Dict[str, float]
    criteria_contributions: Dict[str, float]


class RotationRecommendation(BaseModel):
    """Evaluated crop rotation recommendation."""
    id: str
    label: str
    is_existing: bool
    sequence: List[str]
    score: float
    fit_category: Literal["strong", "moderate", "weak"]
    rank: int
    similar_to: List[str] = Field(default_factory=list)
    criteria: CriteriaScores
    data_confidence: Confidence
    knowledge_support: Confidence
    why_suggested: str
    evidence: List[EvidenceItem]
    benefits: List[str]
    assumptions: List[str]
    information_gaps: List[str]
    risks_for_local_review: List[str]
    review_recommended_by: List[str]
    trace: TraceInfo


class RecommendResponse(BaseModel):
    """Full recommendation response for POST /recommend."""
    overall_outcome: Literal["clear_leader", "similar_options", "no_clear_winner"]
    outcome_message: Optional[str] = None
    rotations: List[RotationRecommendation]
    disclaimer: str
