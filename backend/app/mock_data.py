"""MOCK DATA FOR PHASE 1 CONTRACT & FRONTEND DEVELOPMENT.

NOTE: All data in this file is synthetic mock data strictly adhering to Section 9
of AGROORBIT_PLAN_v2.md. No live NASA APIs or agronomic engines are called here.
"""

from typing import List
from app.models import (
    BareFieldWindow,
    ClimateLocation,
    ClimateResponse,
    Confidence,
    CriteriaScores,
    CropItem,
    DataQuality,
    DatasetInfo,
    DrySpells,
    EvidenceItem,
    HeatStressDays,
    LocationItem,
    MonthlyClimate,
    RecommendRequest,
    RecommendResponse,
    RotationRecommendation,
    SeasonRainTotal,
    SeasonStats,
    TraceInfo,
    Trend,
)

# ============================================================================
# MOCK PRESET LOCATIONS (Section 9)
# ============================================================================
MOCK_LOCATIONS: List[LocationItem] = [
    LocationItem(id="kano", name="Kano", lat=12.0022, lon=8.5920, zone="Sudan Savanna"),
    LocationItem(id="kaduna", name="Kaduna", lat=10.5105, lon=7.4165, zone="Northern Guinea Savanna"),
    LocationItem(id="jos", name="Jos", lat=9.8965, lon=8.8583, zone="Jos Plateau"),
    LocationItem(id="makurdi", name="Makurdi", lat=7.7322, lon=8.5391, zone="Southern Guinea Savanna"),
]

# ============================================================================
# MOCK CROPS (Section 9)
# ============================================================================
MOCK_CROPS: List[CropItem] = [
    CropItem(
        id="maize",
        name="Maize",
        family="cereal",
        traits_summary={"season_days": "90-120", "water_need_mm": "500-800", "drought_tolerance": 2},
        verified_share=0.44,
    ),
    CropItem(
        id="sorghum",
        name="Sorghum",
        family="cereal",
        traits_summary={"season_days": "100-140", "water_need_mm": "400-650", "drought_tolerance": 4},
        verified_share=0.55,
    ),
    CropItem(
        id="pearl_millet",
        name="Pearl Millet",
        family="cereal",
        traits_summary={"season_days": "75-100", "water_need_mm": "300-500", "drought_tolerance": 5},
        verified_share=0.44,
    ),
    CropItem(
        id="cowpea",
        name="Cowpea",
        family="legume",
        traits_summary={"season_days": "60-90", "water_need_mm": "300-500", "drought_tolerance": 4},
        verified_share=0.33,
    ),
    CropItem(
        id="groundnut",
        name="Groundnut",
        family="legume",
        traits_summary={"season_days": "90-120", "water_need_mm": "450-650", "drought_tolerance": 3},
        verified_share=0.44,
    ),
    CropItem(
        id="soybean",
        name="Soybean",
        family="legume",
        traits_summary={"season_days": "95-125", "water_need_mm": "450-700", "drought_tolerance": 2},
        verified_share=0.33,
    ),
]


# ============================================================================
# MOCK CLIMATE GENERATOR (Section 9 GET /climate)
# ============================================================================
def get_mock_climate(lat: float, lon: float) -> ClimateResponse:
    """Returns realistic mock climate indicators matching Section 9."""
    # Synthetic 12-month series representative of northern Nigeria
    monthly_data = [
        MonthlyClimate(month=1, rain_p20=0.0, rain_p50=0.0, rain_p80=0.5, tmax=31.2, regional_root_zone_wetness=0.21),
        MonthlyClimate(month=2, rain_p20=0.0, rain_p50=0.0, rain_p80=1.0, tmax=34.1, regional_root_zone_wetness=0.19),
        MonthlyClimate(month=3, rain_p20=0.0, rain_p50=1.2, rain_p80=4.5, tmax=37.5, regional_root_zone_wetness=0.18),
        MonthlyClimate(month=4, rain_p20=2.0, rain_p50=12.4, rain_p80=28.0, tmax=38.2, regional_root_zone_wetness=0.22),
        MonthlyClimate(month=5, rain_p20=22.0, rain_p50=54.0, rain_p80=95.0, tmax=36.0, regional_root_zone_wetness=0.35),
        MonthlyClimate(month=6, rain_p20=65.0, rain_p50=110.0, rain_p80=160.0, tmax=33.2, regional_root_zone_wetness=0.52),
        MonthlyClimate(month=7, rain_p20=140.0, rain_p50=205.0, rain_p80=280.0, tmax=30.5, regional_root_zone_wetness=0.74),
        MonthlyClimate(month=8, rain_p20=180.0, rain_p50=260.0, rain_p80=340.0, tmax=29.4, regional_root_zone_wetness=0.82),
        MonthlyClimate(month=9, rain_p20=70.0, rain_p50=125.0, rain_p80=180.0, tmax=31.0, regional_root_zone_wetness=0.68),
        MonthlyClimate(month=10, rain_p20=4.0, rain_p50=15.0, rain_p80=35.0, tmax=33.8, regional_root_zone_wetness=0.42),
        MonthlyClimate(month=11, rain_p20=0.0, rain_p50=0.0, rain_p80=1.0, tmax=32.9, regional_root_zone_wetness=0.28),
        MonthlyClimate(month=12, rain_p20=0.0, rain_p50=0.0, rain_p80=0.2, tmax=31.0, regional_root_zone_wetness=0.23),
    ]

    return ClimateResponse(
        location=ClimateLocation(lat=lat, lon=lon, label=f"Demo Point ({lat:.2f}, {lon:.2f})"),
        datasets=[
            DatasetInfo(
                name="NASA POWER daily",
                community="AG",
                time_standard="UTC",
                resolution_note="coarse global grid, not field-level",
                period="1991-2025",
            )
        ],
        monthly=monthly_data,
        season=SeasonStats(
            onset_doy_median=150,
            cessation_doy_median=275,
            length_days_median=125,
            length_days_p20=98,
            method="simplified_v1",
            years_ok=29,
            years_flagged=1,
        ),
        season_rain_total=SeasonRainTotal(median_mm=760.0, p20_mm=610.0, cv=0.18),
        dry_spells=DrySpells(avg_per_season=2.1, longest_median_days=11),
        heat_stress_days=HeatStressDays(median=34, threshold_c=35.0),
        trend=Trend(season_rain_mm_per_decade=-12.0, note="indicative only, not a forecast"),
        bare_field_window=BareFieldWindow(months=[12, 1, 2, 3], basis="proxy"),
        data_quality=DataQuality(from_cache=False, missing_pct=0.4, flags=[]),
    )


# ============================================================================
# MOCK RECOMMENDATION GENERATOR (Section 9 POST /recommend)
# ============================================================================
def get_mock_recommendations(req: RecommendRequest) -> RecommendResponse:
    """Returns realistic mock recommendations with >= 3 distinct rotations matching Section 9."""
    current_seq = req.current_rotation if req.current_rotation else ["maize", "maize", "maize"]
    curr_label = " → ".join(current_seq)

    # 1. Existing rotation evaluation (baseline)
    existing_rec = RotationRecommendation(
        id="existing",
        label=f"Your current rotation: {curr_label}",
        is_existing=True,
        sequence=current_seq,
        score=52.0,
        fit_category="weak",
        rank=3,
        similar_to=[],
        criteria=CriteriaScores(
            water_fit=58.0,
            season_fit=80.0,
            heat_drought_resilience=45.0,
            soil_health=25.0,
            pest_break=10.0,
            erosion_protection=40.0,
            market_preference_fit=70.0,
            forage_value=30.0,
        ),
        data_confidence=Confidence(
            level="medium",
            reasons=["Slope and drainage unknown in farmer input", "NASA meteorology is gridded (0.5°)"],
        ),
        knowledge_support=Confidence(
            level="low",
            reasons=["Most crop traits not yet verified with national extension data"],
        ),
        why_suggested="Evaluated as your current farming practice baseline.",
        evidence=[
            EvidenceItem(
                source="NASA POWER",
                metric="crop window rainfall ≥ requirement",
                value="22 of 30 years",
                meaning="Water requirements met in ~73% of historical years, but vulnerable during dry spells.",
            ),
            EvidenceItem(
                source="farmer input",
                metric="continuous cereal rotation",
                value="3 consecutive cereal years",
                meaning="High pest and weed pressure buildup without a broadleaf break crop.",
            ),
        ],
        benefits=[
            "Familiarity with continuous maize agronomy and local market outlets.",
            "Higher market preference alignment if maize is your primary cash crop.",
        ],
        assumptions=[
            "Assuming standard 90-110 day maize maturity cycle.",
            "Assuming no supplemental irrigation.",
        ],
        information_gaps=[
            "Exact soil drainage and depth at field location.",
            "Local pest pressure history (Striga, fall armyworm).",
        ],
        risks_for_local_review=[
            "Soil nitrogen depletion from repetitive cereal uptake.",
            "Increased vulnerability to mid-season dry spells during flowering.",
        ],
        review_recommended_by=["Agricultural extension officer", "Local agronomic advisor"],
        trace=TraceInfo(
            algorithm_version="0.2.0-mock",
            climate_period="1991-2025",
            priority_weights_applied={
                "water_saving": 0.25,
                "soil_health": 0.20,
                "resilience": 0.20,
                "market_preference": 0.15,
                "erosion": 0.10,
                "forage": 0.10,
            },
            criteria_contributions={
                "water_fit": 14.5,
                "season_fit": 8.0,
                "heat_drought_resilience": 9.0,
                "soil_health": 5.0,
                "pest_break": 1.0,
                "erosion_protection": 4.0,
                "market_preference_fit": 10.5,
                "forage_value": 3.0,
            },
        ),
    )

    # 2. Alternative A: Maize -> Cowpea -> Sorghum (Diversified Legume-Cereal)
    alt_a = RotationRecommendation(
        id="alt_diversified_legume",
        label="Diversified rotation: maize → cowpea → sorghum",
        is_existing=False,
        sequence=["maize", "cowpea", "sorghum"],
        score=84.0,
        fit_category="strong",
        rank=1,
        similar_to=[],
        criteria=CriteriaScores(
            water_fit=86.0,
            season_fit=92.0,
            heat_drought_resilience=80.0,
            soil_health=85.0,
            pest_break=90.0,
            erosion_protection=75.0,
            market_preference_fit=80.0,
            forage_value=75.0,
        ),
        data_confidence=Confidence(
            level="medium",
            reasons=["Slope and drainage unknown in farmer input", "NASA meteorology is gridded (0.5°)"],
        ),
        knowledge_support=Confidence(
            level="low",
            reasons=["Cowpea nitrogen fixation values rely on unverified literature estimates"],
        ),
        why_suggested="Introduces a nitrogen-fixing legume to break pest cycles and adds drought-hardy sorghum.",
        evidence=[
            EvidenceItem(
                source="NASA POWER",
                metric="crop window rainfall ≥ requirement",
                value="28 of 30 years",
                meaning="Shorter-duration cowpea and drought-hardy sorghum successfully complete in 93% of years.",
            ),
            EvidenceItem(
                source="crop knowledge base",
                metric="biological nitrogen fixation",
                value="legume included in year 2",
                meaning="Cowpea nodulation leaves residual soil nitrogen for subsequent cereal crops.",
            ),
        ],
        benefits=[
            "Biological nitrogen fixation reduces synthetic fertilizer costs for the year 3 sorghum crop.",
            "Effective break in the cereal pest and Striga life cycle.",
            "High valuable cowpea fodder for livestock.",
        ],
        assumptions=[
            "Cowpea harvested before late dry spell onset.",
            "Farmer has access to viable cowpea and sorghum seeds.",
        ],
        information_gaps=[
            "Farmer access to local cowpea storage against post-harvest bruchids.",
            "Field specific slope and risk of runoff.",
        ],
        risks_for_local_review=[
            "Cowpea requires pest scouting during flowering.",
            "Ensure sorghum variety matches local grain market preference.",
        ],
        review_recommended_by=["Agricultural extension officer", "Local cooperative lead"],
        trace=TraceInfo(
            algorithm_version="0.2.0-mock",
            climate_period="1991-2025",
            priority_weights_applied={
                "water_saving": 0.25,
                "soil_health": 0.20,
                "resilience": 0.20,
                "market_preference": 0.15,
                "erosion": 0.10,
                "forage": 0.10,
            },
            criteria_contributions={
                "water_fit": 21.5,
                "season_fit": 9.2,
                "heat_drought_resilience": 16.0,
                "soil_health": 17.0,
                "pest_break": 9.0,
                "erosion_protection": 7.5,
                "market_preference_fit": 12.0,
                "forage_value": 7.5,
            },
        ),
    )

    # 3. Alternative B: Sorghum -> Groundnut -> Pearl Millet (Drought-Resilient)
    alt_b = RotationRecommendation(
        id="alt_drought_hardy",
        label="Drought-hardy rotation: sorghum → groundnut → pearl_millet",
        is_existing=False,
        sequence=["sorghum", "groundnut", "pearl_millet"],
        score=74.0,
        fit_category="moderate",
        rank=2,
        similar_to=[],
        criteria=CriteriaScores(
            water_fit=88.0,
            season_fit=90.0,
            heat_drought_resilience=88.0,
            soil_health=65.0,
            pest_break=80.0,
            erosion_protection=60.0,
            market_preference_fit=60.0,
            forage_value=70.0,
        ),
        data_confidence=Confidence(
            level="medium",
            reasons=["Slope and drainage unknown in farmer input", "NASA meteorology is gridded (0.5°)"],
        ),
        knowledge_support=Confidence(
            level="low",
            reasons=["Groundnut water requirements need local cultivar verification"],
        ),
        why_suggested="Maximizes climate resilience and drought buffering in lower rainfall seasons.",
        evidence=[
            EvidenceItem(
                source="NASA POWER",
                metric="critical flowering dry spell survival",
                value="27 of 30 years",
                meaning="Pearl millet and sorghum tolerate runs of >7 dry days during mid-season.",
            ),
            EvidenceItem(
                source="crop knowledge base",
                metric="crop diversity index",
                value="cereal-legume-cereal alternation",
                meaning="Varied root depths exploit different soil moisture horizons.",
            ),
        ],
        benefits=[
            "Exceptional buffering against shortened rainy seasons and mid-season droughts.",
            "Nutritious grain and groundnut haulm fodder.",
        ],
        assumptions=[
            "Groundnut rosette virus management is practiced.",
            "Local demand exists for pearl millet grain.",
        ],
        information_gaps=[
            "Local availability of certified short-duration groundnut seed.",
            "Local consumer preference for pearl millet vs maize.",
        ],
        risks_for_local_review=[
            "Market sale price for millet may fluctuate more than maize.",
            "Groundnut requires labor for pod harvest and drying.",
        ],
        review_recommended_by=["Agricultural extension officer"],
        trace=TraceInfo(
            algorithm_version="0.2.0-mock",
            climate_period="1991-2025",
            priority_weights_applied={
                "water_saving": 0.25,
                "soil_health": 0.20,
                "resilience": 0.20,
                "market_preference": 0.15,
                "erosion": 0.10,
                "forage": 0.10,
            },
            criteria_contributions={
                "water_fit": 22.0,
                "season_fit": 9.0,
                "heat_drought_resilience": 17.6,
                "soil_health": 13.0,
                "pest_break": 8.0,
                "erosion_protection": 6.0,
                "market_preference_fit": 9.0,
                "forage_value": 7.0,
            },
        ),
    )

    return RecommendResponse(
        overall_outcome="clear_leader",
        outcome_message=None,
        rotations=[alt_a, alt_b, existing_rec],
        disclaimer="AgroOrbit supports decisions. It does not replace local farmer knowledge or agricultural advisers.",
    )
