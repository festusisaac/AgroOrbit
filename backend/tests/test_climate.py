"""Tests for climate.py indicator algorithms, including onset, redesigned cessation,
dry spells, heat stress, and Pydantic response validation.
"""

import numpy as np
import pandas as pd
import pytest

from app.climate import (
    _max_consecutive_dry_days,
    calculate_annual_seasons,
    calculate_bare_field_window,
    calculate_monthly_climate,
    compute_climate_summary,
    detect_season_cessation,
    detect_season_onset,
)
from app.models import ClimateResponse


def create_synthetic_year(year: int = 2023) -> pd.DataFrame:
    """Creates a full 365-day synthetic dataset with typical northern Nigerian savanna seasonality."""
    dates = pd.date_range(start=f"{year}-01-01", end=f"{year}-12-31", freq="D")
    df = pd.DataFrame(index=dates)

    # Initialize zeros and defaults
    df["PRECTOTCORR"] = 0.0
    df["T2M"] = 30.0
    df["T2M_MAX"] = 36.0
    df["T2M_MIN"] = 24.0
    df["RH2M"] = 40.0
    df["ALLSKY_SFC_SW_DWN"] = 20.0
    df["GWETTOP"] = 0.20
    df["GWETROOT"] = 0.25

    # Onset in late May (May 20-22: 10 mm/day = 30 mm total)
    df.loc[f"{year}-05-20":f"{year}-05-22", "PRECTOTCORR"] = 10.0
    # Moderate regular rain across June, July, August (rain every 2-3 days)
    rainy_days = pd.date_range(start=f"{year}-05-25", end=f"{year}-08-31", freq="3D")
    df.loc[rainy_days, "PRECTOTCORR"] = 15.0

    # Wetness responds
    df.loc[f"{year}-06-01":f"{year}-09-30", "GWETROOT"] = 0.65
    df.loc[f"{year}-06-01":f"{year}-09-30", "T2M_MAX"] = 31.0

    return df


def test_onset_detection_rejects_false_start():
    """Verify onset algorithm rejects a planting rain followed by an 8-day dry spell."""
    df = create_synthetic_year(2023)

    # False start on April 10-12 (25 mm)
    df.loc["2023-04-10":"2023-04-12", "PRECTOTCORR"] = 8.5
    # Immediately followed by an 8-day dry spell (0 mm)
    df.loc["2023-04-13":"2023-04-20", "PRECTOTCORR"] = 0.0

    onset_date, flag = detect_season_onset(df["PRECTOTCORR"], 2023)

    # April false start should be rejected; real onset on May 20 should be accepted
    assert flag == "ok"
    assert onset_date == pd.Timestamp("2023-05-20")


def test_cessation_mid_september_dry_spell_does_not_end_season():
    """CRITICAL TEST (Plan v2 change #1 & Section 6.2):
    A severe mid-September dry spell must NOT end the season early if meaningful rain returns later.
    """
    df = create_synthetic_year(2023)

    # Establish an early wet window in late August
    df.loc["2023-08-20":"2023-08-24", "PRECTOTCORR"] = 4.0  # 20 mm in 5 days (qualifying)

    # SEVERE MID-SEPTEMBER DRY SPELL: Sept 5 to Sept 23 (19 days of complete drought 0.0 mm)
    df.loc["2023-09-05":"2023-09-23", "PRECTOTCORR"] = 0.0

    # MEANINGFUL RAIN RETURNS IN OCTOBER: Oct 2 to Oct 6 (20 mm over 5 days)
    df.loc["2023-10-02":"2023-10-06", "PRECTOTCORR"] = 4.0

    # Completely dry afterwards to Dec 31
    df.loc["2023-10-07":"2023-12-31", "PRECTOTCORR"] = 0.0

    cessation_date, flag = detect_season_cessation(df["PRECTOTCORR"], 2023)

    assert flag == "ok"
    assert cessation_date is not None

    # The cessation date MUST be the end of the October 2-6 wet window
    assert cessation_date == pd.Timestamp("2023-10-06")

    # The cessation date MUST NOT be before the September dry spell
    assert cessation_date > pd.Timestamp("2023-09-23")


def test_cessation_without_late_rains():
    """Verify cessation ends at the last wet window when no late rains occur."""
    df = create_synthetic_year(2023)

    # Final rain of the year is Sept 10-14 (20 mm total over 5 days)
    df.loc["2023-09-10":"2023-09-14", "PRECTOTCORR"] = 4.0
    # Bone dry from Sept 15 to Dec 31
    df.loc["2023-09-15":"2023-12-31", "PRECTOTCORR"] = 0.0

    cessation_date, flag = detect_season_cessation(df["PRECTOTCORR"], 2023)
    assert flag == "ok"
    assert cessation_date == pd.Timestamp("2023-09-14")


def test_annual_seasons_calculation():
    """Verify calculate_annual_seasons computes length, rain total, and flags correctly."""
    df = create_synthetic_year(2023)
    # Add final September rain
    df.loc["2023-09-20":"2023-09-24", "PRECTOTCORR"] = 4.0
    df.loc["2023-09-25":"2023-12-31", "PRECTOTCORR"] = 0.0

    seasons = calculate_annual_seasons(df)
    assert len(seasons) == 1
    row = seasons.loc[2023]
    assert row["quality_flag"] == "ok"
    assert row["onset_doy"] == pd.Timestamp("2023-05-20").day_of_year
    assert row["cessation_doy"] == pd.Timestamp("2023-09-24").day_of_year
    assert row["length_days"] == (pd.Timestamp("2023-09-24") - pd.Timestamp("2023-05-20")).days
    assert row["season_rain_mm"] > 0


def test_monthly_climate_p20_p50_p80_order():
    """Verify that for every month, rain_p20 <= rain_p50 <= rain_p80."""
    # Create multi-year series (2020-2023)
    dfs = []
    for y in range(2020, 2024):
        df_y = create_synthetic_year(y)
        # Add random variations to test percentiles
        df_y["PRECTOTCORR"] *= (1.0 + (y - 2020) * 0.1)
        dfs.append(df_y)
    multi_df = pd.concat(dfs)

    monthly = calculate_monthly_climate(multi_df)
    assert len(monthly) == 12

    for m in monthly:
        assert m.rain_p20 <= m.rain_p50 <= m.rain_p80
        assert m.tmax > 0.0
        assert 0.0 <= m.regional_root_zone_wetness <= 1.0


def test_bare_field_window_proxy():
    """Verify that bare-field window identifies dry months with low wetness."""
    dfs = [create_synthetic_year(y) for y in range(2021, 2024)]
    multi_df = pd.concat(dfs)
    monthly = calculate_monthly_climate(multi_df)
    bare = calculate_bare_field_window(monthly)

    assert bare.basis == "proxy"
    # Months 1, 2, 12 should be identified as dry bare-field months
    assert 1 in bare.months
    assert 2 in bare.months
    assert 12 in bare.months
    # Peak rainy month (July/August) must NOT be in bare-field window
    assert 7 not in bare.months
    assert 8 not in bare.months


def test_compute_climate_summary_contract_fidelity():
    """Verify that compute_climate_summary returns a valid ClimateResponse model."""
    dfs = [create_synthetic_year(y) for y in range(2020, 2024)]
    multi_df = pd.concat(dfs)

    summary = compute_climate_summary(
        df=multi_df,
        lat=12.0,
        lon=8.5,
        location_label="Kano Test",
        from_cache=False,
        missing_pct=0.2,
    )

    assert isinstance(summary, ClimateResponse)
    assert summary.location.lat == 12.0
    assert summary.location.lon == 8.5
    assert summary.location.label == "Kano Test"
    assert len(summary.monthly) == 12
    assert summary.season.length_days_median > 0
    assert summary.season_rain_total.median_mm > 0
    assert summary.dry_spells.avg_per_season >= 0
    assert summary.trend.note == "indicative only, not a forecast"
    assert summary.bare_field_window.basis == "proxy"
    assert summary.data_quality.missing_pct == 0.2
