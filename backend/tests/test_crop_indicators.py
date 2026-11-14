"""Unit tests for per-crop, per-year indicators and multi-year frequency aggregation.

Uses isolated synthetic series with known mathematical answers (no live data).
"""

import pandas as pd
import pytest

from app.climate import (
    CropClimateIndicators,
    CropFrequencyMetric,
    CropYearIndicator,
    compute_crop_climate_indicators,
    evaluate_crop_year,
    get_crop_agronomic_requirements,
)
from app.knowledge import load_crops


def make_synthetic_season(
    year: int,
    onset_str: str,
    cessation_str: str,
    daily_rain_val: float = 10.0,
    rain_freq: int = 2,
    dry_spell_range: tuple = None,
    tmax_val: float = 32.0,
    hot_days_count: int = 0,
    quality_flag: str = "ok",
) -> tuple:
    """Helper to generate known synthetic daily series and season row."""
    dates = pd.date_range(f"{year}-01-01", f"{year}-12-31", freq="D")
    df = pd.DataFrame(index=dates)
    df["PRECTOTCORR"] = 0.0
    df["T2M_MAX"] = tmax_val

    onset = pd.Timestamp(onset_str)
    cessation = pd.Timestamp(cessation_str)
    length_days = (cessation - onset).days

    if quality_flag == "ok":
        # Regular rain pattern between onset and cessation
        rain_dates = pd.date_range(onset, cessation, freq=f"{rain_freq}D")
        df.loc[rain_dates, "PRECTOTCORR"] = daily_rain_val

        # Insert a specific dry spell if requested
        if dry_spell_range:
            d_start, d_end = dry_spell_range
            df.loc[d_start:d_end, "PRECTOTCORR"] = 0.0

        # Insert hot days if requested
        if hot_days_count > 0:
            hot_dates = pd.date_range(onset, periods=hot_days_count, freq="D")
            df.loc[hot_dates, "T2M_MAX"] = 38.0

    season_row = pd.Series({
        "year": year,
        "onset_date": onset if quality_flag == "ok" else None,
        "cessation_date": cessation if quality_flag == "ok" else None,
        "length_days": length_days if quality_flag == "ok" else None,
        "quality_flag": quality_flag,
    })

    return df, season_row


def test_get_crop_agronomic_requirements():
    """Verify midpoint calculation for season_days and min extraction for water_need_mm."""
    crops = load_crops()
    cowpea = crops["cowpea"]  # 60-90 days, 300-500 mm
    cid, cname, duration, water_min, heat_th = get_crop_agronomic_requirements(cowpea)

    assert cid == "cowpea"
    assert cname == "Cowpea"
    assert duration == 75  # midpoint of 60 and 90
    assert water_min == 300.0  # min water need
    assert heat_th == 35.0


def test_evaluate_crop_year_ideal_conditions():
    """Verify ideal year where crop completes, water requirement is met, no dry spell, no heat stress."""
    # Cowpea: duration=75, water_min=300
    crop_def = {
        "id": "cowpea",
        "name": "Cowpea",
        "traits": {
            "season_days": {"value": {"min": 60, "max": 90}},
            "water_need_mm": {"value": {"min": 300, "max": 500}},
        },
    }

    # Available season is 140 days (onset May 15 to Oct 2)
    df, season_row = make_synthetic_season(
        year=2023,
        onset_str="2023-05-15",
        cessation_str="2023-10-02",
        daily_rain_val=10.0,
        rain_freq=2,  # Rains every 2 days: ~37 rain days * 10mm = ~370mm
        tmax_val=32.0,
        hot_days_count=0,
    )

    indicator = evaluate_crop_year(
        crop=crop_def,
        year=2023,
        rain=df["PRECTOTCORR"],
        t2m_max=df["T2M_MAX"],
        season_row=season_row,
        planting_delay_days=0,
        buffer_days=10,
    )

    assert isinstance(indicator, CropYearIndicator)
    assert indicator.can_complete is True  # 75 + 10 <= 140
    assert indicator.window_rain_mm >= 300.0
    assert indicator.water_ok is True
    assert indicator.mid_season_dry_spell is False
    assert indicator.heat_days == 0
    assert indicator.quality_flag == "ok"


def test_evaluate_crop_year_stress_conditions():
    """Verify stressed year: short season failure, water shortage, critical dry spell, and heat days."""
    # Maize: duration=105 (midpoint of 90-120), water_min=500
    crop_def = {
        "id": "maize",
        "name": "Maize",
        "traits": {
            "season_days": {"value": {"min": 90, "max": 120}},
            "water_need_mm": {"value": {"min": 500, "max": 800}},
        },
    }

    # Short season: only 80 days available (onset June 1 to Aug 20)
    # Maize needs 105 + 10 = 115 days -> can_complete must be False!
    # Crop window: June 1 + 105 days = ~Sept 13
    # Critical window: 25% (day 26 = June 27) to 60% (day 63 = Aug 3)
    # Insert 10-day dry spell inside critical window: July 5 to July 16
    df, season_row = make_synthetic_season(
        year=2023,
        onset_str="2023-06-01",
        cessation_str="2023-08-20",
        daily_rain_val=5.0,  # Low rain
        rain_freq=3,
        dry_spell_range=("2023-07-05", "2023-07-16"),  # 12 consecutive dry days > 7
        tmax_val=33.0,
        hot_days_count=6,  # 6 days with 38 C
    )

    indicator = evaluate_crop_year(
        crop=crop_def,
        year=2023,
        rain=df["PRECTOTCORR"],
        t2m_max=df["T2M_MAX"],
        season_row=season_row,
        planting_delay_days=0,
        buffer_days=10,
    )

    assert indicator.can_complete is False  # 115 > 80
    assert indicator.water_ok is False      # Window rain < 500 mm
    assert indicator.mid_season_dry_spell is True  # 12 days > 7 days threshold
    assert indicator.heat_days == 6         # 6 days >= 35 C
    assert indicator.quality_flag == "ok"


def test_evaluate_crop_year_flagged_exclusion():
    """Verify that a year flagged as incomplete_year produces an uncompleted record marked accordingly."""
    crop_def = {"id": "maize", "traits": {"season_days": {"value": 100}, "water_need_mm": {"value": 500}}}
    df, season_row = make_synthetic_season(
        year=2022,
        onset_str="2022-05-01",
        cessation_str="2022-09-01",
        quality_flag="incomplete_year",
    )

    indicator = evaluate_crop_year(
        crop=crop_def,
        year=2022,
        rain=df["PRECTOTCORR"],
        t2m_max=df["T2M_MAX"],
        season_row=season_row,
    )

    assert indicator.quality_flag == "incomplete_year"
    assert indicator.can_complete is False
    assert indicator.water_ok is False
    assert indicator.window_start is None


def test_compute_crop_climate_indicators_multi_year_aggregation():
    """Verify multi-year frequency aggregation and strict exclusion of flagged years."""
    crop_def = {
        "id": "cowpea",
        "name": "Cowpea",
        "traits": {
            "season_days": {"value": {"min": 60, "max": 90}},
            "water_need_mm": {"value": {"min": 300, "max": 500}},
        },
    }

    # Construct 3 years of daily data:
    # Year 1 (2021): Perfect year (can_complete=True, water_ok=True, dry_spell=False, heat_days=0)
    df1, srow1 = make_synthetic_season(2021, "2021-05-15", "2021-10-15", daily_rain_val=15.0, rain_freq=2)
    # Year 2 (2022): Bad drought year (can_complete=False, water_ok=False, dry_spell=True, heat_days=5)
    df2, srow2 = make_synthetic_season(
        2022, "2022-06-01", "2022-07-20",  # 50 days (too short for 75+10)
        daily_rain_val=2.0, rain_freq=4,
        dry_spell_range=("2022-06-20", "2022-07-05"), # 16 dry days
        hot_days_count=5,
    )
    # Year 3 (2023): Incomplete calendar year (flagged)
    df3, srow3 = make_synthetic_season(2023, "2023-05-01", "2023-09-01", quality_flag="incomplete_year")

    combined_df = pd.concat([df1, df2, df3])
    seasons_df = pd.DataFrame([srow1, srow2, srow3]).set_index("year")

    result = compute_crop_climate_indicators(
        crop=crop_def,
        df=combined_df,
        seasons_df=seasons_df,
    )

    assert isinstance(result, CropClimateIndicators)
    assert result.crop_id == "cowpea"
    assert result.total_years_evaluated == 3
    assert result.valid_years_count == 2
    assert result.flagged_years_count == 1

    # Check can_complete: 1 of 2 valid years (50.0%)
    assert result.can_complete_freq.success_years == 1
    assert result.can_complete_freq.total_valid_years == 2
    assert result.can_complete_freq.frequency_pct == 50.0
    assert result.can_complete_freq.formatted == "1 of 2 years"
    assert result.can_complete_freq.flagged_years_excluded == 1

    # Check water_ok: 1 of 2 valid years (50.0%)
    assert result.water_ok_freq.success_years == 1
    assert result.water_ok_freq.total_valid_years == 2
    assert result.water_ok_freq.frequency_pct == 50.0
    assert result.water_ok_freq.formatted == "1 of 2 years"

    # Check dry spell risk: 1 of 2 valid years had a critical dry spell
    assert result.critical_dry_spell_risk_freq.success_years == 1
    assert result.critical_dry_spell_risk_freq.formatted == "1 of 2 years"

    # Check heat stress risk: 1 of 2 valid years had heat stress days
    assert result.heat_stress_risk_freq.success_years == 1
    assert result.heat_stress_risk_freq.formatted == "1 of 2 years"
