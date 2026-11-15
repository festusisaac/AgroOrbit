"""Pydantic data models for the AgroOrbit API contract and internal schemas.

Strictly adheres to Section 9 of AGROORBIT_PLAN_v2.md.
"""

from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, Field, ValidationInfo, field_validator
from app.config import (
    ALLOWED_SOIL_DRAINAGES,
    ALLOWED_SOIL_ORGANIC_MATTERS,
    ALLOWED_SOIL_SLOPES,
    ALLOWED_SOIL_TEXTURES,
    ALLOWED_SOIL_WATER_SOURCES,
)


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
    humidity: float = 0.0
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
    texture: Optional[str] = "unknown"
    drainage: Optional[str] = "unknown"
    organic_matter: Optional[str] = "unknown"
    water_source: Optional[str] = "rain_fed"
    slope: Optional[str] = "unknown"

    @field_validator("texture")
    @classmethod
    def validate_texture(cls, v: Optional[str]) -> str:
        val = str(v).lower().strip() if v is not None else "unknown"
        if val not in ALLOWED_SOIL_TEXTURES:
            raise ValueError(f"Invalid soil texture '{v}'. Allowed values are: {sorted(ALLOWED_SOIL_TEXTURES)}.")
        return val

    @field_validator("drainage")
    @classmethod
    def validate_drainage(cls, v: Optional[str]) -> str:
        val = str(v).lower().strip() if v is not None else "unknown"
        if val not in ALLOWED_SOIL_DRAINAGES:
            raise ValueError(f"Invalid soil drainage '{v}'. Allowed values are: {sorted(ALLOWED_SOIL_DRAINAGES)}.")
        return val

    @field_validator("organic_matter")
    @classmethod
    def validate_organic_matter(cls, v: Optional[str]) -> str:
        val = str(v).lower().strip() if v is not None else "unknown"
        if val not in ALLOWED_SOIL_ORGANIC_MATTERS:
            raise ValueError(f"Invalid soil organic_matter '{v}'. Allowed values are: {sorted(ALLOWED_SOIL_ORGANIC_MATTERS)}.")
        return val

    @field_validator("water_source")
    @classmethod
    def validate_water_source(cls, v: Optional[str]) -> str:
        val = str(v).lower().strip() if v is not None else "rain_fed"
        if val not in ALLOWED_SOIL_WATER_SOURCES:
            raise ValueError(f"Invalid water_source '{v}'. Allowed values are: {sorted(ALLOWED_SOIL_WATER_SOURCES)}.")
        return val

    @field_validator("slope")
    @classmethod
    def validate_slope(cls, v: Optional[str]) -> str:
        val = str(v).lower().strip() if v is not None else "unknown"
        if val not in ALLOWED_SOIL_SLOPES:
            raise ValueError(f"Invalid field slope '{v}'. Allowed values are: {sorted(ALLOWED_SOIL_SLOPES)}.")
        return val


class PrioritiesInput(BaseModel):
    """Farmer priorities on 0-5 scale."""
    water_saving: int = Field(default=0, ge=0, le=5)
    soil_health: int = Field(default=0, ge=0, le=5)
    erosion: int = Field(default=0, ge=0, le=5)
    market_preference: int = Field(default=0, ge=0, le=5)
    forage: int = Field(default=0, ge=0, le=5)
    resilience: int = Field(default=0, ge=0, le=5)

    @field_validator("water_saving", "soil_health", "erosion", "market_preference", "forage", "resilience")
    @classmethod
    def validate_priority_range(cls, v: int, info: ValidationInfo) -> int:
        if v < 0 or v > 5:
            raise ValueError(f"Priority '{info.field_name}' must be an integer between 0 and 5, got {v}.")
        return v


class ScenarioInput(BaseModel):
    """Hypothetical climate sensitivity scenario parameters (P1)."""
    rainfall_change_pct: float = 0.0
    temperature_change_c: float = 0.0


class RecommendRequest(BaseModel):
    """Request payload for POST /recommend."""
    lat: float = Field(..., ge=-90.0, le=90.0, description="Latitude between -90 and 90")
    lon: float = Field(..., ge=-180.0, le=180.0, description="Longitude between -180 and 180")
    current_rotation: List[str] = Field(..., min_length=1, max_length=3, description="List of 1 to 3 crop names")
    soil: SoilInput = Field(default_factory=SoilInput)
    priorities: PrioritiesInput = Field(default_factory=PrioritiesInput)
    preferred_crops: List[str] = Field(default_factory=list)
    scenario: ScenarioInput = Field(default_factory=ScenarioInput)

    @field_validator("lat")
    @classmethod
    def validate_lat(cls, v: float) -> float:
        if not (-90.0 <= v <= 90.0):
            raise ValueError(f"Latitude must be between -90 and 90 degrees, got {v}.")
        return v

    @field_validator("lon")
    @classmethod
    def validate_lon(cls, v: float) -> float:
        if not (-180.0 <= v <= 180.0):
            raise ValueError(f"Longitude must be between -180 and 180 degrees, got {v}.")
        return v

    @field_validator("current_rotation")
    @classmethod
    def validate_current_rotation(cls, v: List[str]) -> List[str]:
        if not (1 <= len(v) <= 3):
            raise ValueError(f"current_rotation must contain between 1 and 3 crop names, got {len(v)}.")
        for item in v:
            if not isinstance(item, str) or not item.strip():
                raise ValueError("Crop IDs in current_rotation must be non-empty strings.")
        return [item.strip() for item in v]


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
