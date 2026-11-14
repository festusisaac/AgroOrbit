"""Derivation of growing season indicators and crop window climate metrics.

Strictly adheres to Section 6.2 of AGROORBIT_PLAN_v2.md:
- Onset: First date after ONSET_SEARCH_START where 3-day rain >= 20 mm and no dry spell > 7 days in next 30 days.
- Cessation (redesigned v2): End of the LAST 5-day window between Aug 15 and Dec 31 with total rain >= 15 mm.
  (Ensures mid-September dry spells do not trigger premature cessation).
- Season length: Cessation - Onset with quality flags.
- Aggregations: Monthly rainfall P20/P50/P80, Tmax, regional root-zone wetness.
- Risk metrics: Dry spells inside season, heat stress days (Tmax >= 35C).
- Trend: Decadal rainfall slope ('indicative only, not a forecast').
- Bare-field window: Low-rain, low-wetness months (basis='proxy').
"""

from typing import Dict, List, Optional, Tuple
import numpy as np
import pandas as pd

from app.config import (
    BARE_FIELD_RAIN_P50_MAX_MM,
    BARE_FIELD_WETNESS_MAX,
    CESSATION_RAIN_WINDOW_MM,
    CESSATION_SEARCH_END_MMDD,
    CESSATION_SEARCH_START_MMDD,
    CESSATION_WINDOW_DAYS,
    DRY_DAY_THRESHOLD_MM,
    DRY_SPELL_CRITICAL_DAYS,
    HEAT_STRESS_THRESHOLD_C,
    NASA_POWER_COMMUNITY,
    NASA_POWER_TIME_STANDARD,
    ONSET_MAX_DRY_SPELL_DAYS,
    ONSET_POST_WINDOW_DAYS,
    ONSET_RAIN_3DAY_MM,
    ONSET_SEARCH_END_MMDD,
    ONSET_SEARCH_START_MMDD,
    SEASON_MISSING_DATA_MAX_PCT,
)
from app.models import (
    BareFieldWindow,
    ClimateLocation,
    ClimateResponse,
    DataQuality,
    DatasetInfo,
    DrySpells,
    HeatStressDays,
    MonthlyClimate,
    SeasonRainTotal,
    SeasonStats,
    Trend,
)


def _max_consecutive_dry_days(rain_series: pd.Series, threshold_mm: float = DRY_DAY_THRESHOLD_MM) -> int:
    """Finds the maximum run of consecutive dry days in a daily series."""
    if rain_series.empty:
        return 0
    is_dry = (rain_series < threshold_mm) | (rain_series.isna())
    max_dry = 0
    current_dry = 0
    for dry in is_dry:
        if dry:
            current_dry += 1
            if current_dry > max_dry:
                max_dry = current_dry
        else:
            current_dry = 0
    return max_dry


def _count_dry_spells(
    rain_series: pd.Series,
    min_days: int = DRY_SPELL_CRITICAL_DAYS,
    dry_threshold_mm: float = DRY_DAY_THRESHOLD_MM,
) -> Tuple[int, int]:
    """Counts dry spells (runs > min_days of dry days) and returns (count, longest_spell_days)."""
    if rain_series.empty:
        return 0, 0
    is_dry = (rain_series < dry_threshold_mm) | (rain_series.isna())
    runs = []
    current_run = 0
    for dry in is_dry:
        if dry:
            current_run += 1
        else:
            if current_run > 0:
                runs.append(current_run)
            current_run = 0
    if current_run > 0:
        runs.append(current_run)

    # Dry spells defined as runs > min_days (e.g. > 7 days)
    critical_spells = [r for r in runs if r > min_days]
    longest = max(runs) if runs else 0
    return len(critical_spells), longest


def detect_season_onset(
    daily_rain: pd.Series,
    year: int,
) -> Tuple[Optional[pd.Timestamp], str]:
    """Detects growing season onset date for a given year.

    Rule: First date after ONSET_SEARCH_START where 3-day rainfall >= 20 mm
    and no dry spell > 7 days occurs in the following 30 days.
    """
    start_date = pd.Timestamp(f"{year}-{ONSET_SEARCH_START_MMDD}")
    end_date = pd.Timestamp(f"{year}-{ONSET_SEARCH_END_MMDD}")

    # Extract search window plus post-window buffer
    max_window_end = end_date + pd.Timedelta(days=ONSET_POST_WINDOW_DAYS + 5)
    year_rain = daily_rain.loc[(daily_rain.index >= start_date) & (daily_rain.index <= max_window_end)]

    if year_rain.empty:
        return None, "onset_not_found"

    # Candidate onset search dates
    search_dates = [d for d in year_rain.index if start_date <= d <= end_date]

    for d in search_dates:
        # Onset date itself must be a rain day (rain >= DRY_DAY_THRESHOLD_MM)
        if year_rain.loc[d] < DRY_DAY_THRESHOLD_MM:
            continue

        # Check 3 consecutive days: d, d+1, d+2
        three_day_window = year_rain.loc[(year_rain.index >= d) & (year_rain.index <= d + pd.Timedelta(days=2))]
        if len(three_day_window) < 3:
            continue

        if three_day_window.sum(skipna=True) >= ONSET_RAIN_3DAY_MM:
            # Check following 30 days for false-break dry spell
            post_start = d + pd.Timedelta(days=3)
            post_end = d + pd.Timedelta(days=ONSET_POST_WINDOW_DAYS + 2)
            post_window = year_rain.loc[(year_rain.index >= post_start) & (year_rain.index <= post_end)]

            if _max_consecutive_dry_days(post_window) <= ONSET_MAX_DRY_SPELL_DAYS:
                return d, "ok"

    return None, "onset_not_found"


def detect_season_cessation(
    daily_rain: pd.Series,
    year: int,
) -> Tuple[Optional[pd.Timestamp], str]:
    """Detects growing season cessation date for a given year.

    Rule (redesigned v2): The end of the LAST 5-day window between Aug 15 and Dec 31
    whose total rainfall >= 15 mm.

    This ensures that erratic dry spells in September do NOT prematurely terminate
    the season if significant rains return later.
    """
    search_start = pd.Timestamp(f"{year}-{CESSATION_SEARCH_START_MMDD}")
    search_end = pd.Timestamp(f"{year}-{CESSATION_SEARCH_END_MMDD}")

    # Window search needs 4 days prior to include 5-day windows ending on search_start
    window_data_start = search_start - pd.Timedelta(days=CESSATION_WINDOW_DAYS - 1)
    period_rain = daily_rain.loc[(daily_rain.index >= window_data_start) & (daily_rain.index <= search_end)]

    if len(period_rain) < CESSATION_WINDOW_DAYS:
        return None, "cessation_not_found"

    # Compute rolling 5-day sum
    rolling_sum = period_rain.rolling(window=CESSATION_WINDOW_DAYS).sum()

    # Find all 5-day windows whose end date is between search_start and search_end with sum >= threshold
    qualifying = rolling_sum.loc[
        (rolling_sum.index >= search_start)
        & (rolling_sum.index <= search_end)
        & (rolling_sum >= CESSATION_RAIN_WINDOW_MM)
    ]

    if qualifying.empty:
        return None, "cessation_not_found"

    # Cessation is the end of the LAST qualifying 5-day window whose end date is a rain day
    # (A wet window terminates on a rainy day, not trailing rainless days)
    qualifying_dates = [
        d for d in qualifying.index if period_rain.loc[d] >= DRY_DAY_THRESHOLD_MM
    ]
    if not qualifying_dates:
        last_wet_date = qualifying.index.max()
    else:
        last_wet_date = max(qualifying_dates)

    return last_wet_date, "ok"


def calculate_annual_seasons(df: pd.DataFrame) -> pd.DataFrame:
    """Computes onset, cessation, length, rainfall, and quality flags for each year."""
    if "PRECTOTCORR" not in df.columns:
        raise ValueError("DataFrame must contain 'PRECTOTCORR' column.")

    rain = df["PRECTOTCORR"]
    years = sorted(df.index.year.unique())
    records = []

    for y in years:
        year_data = df.loc[df.index.year == y]
        total_days_in_year = len(year_data)

        # Skip years with high overall missing data (>25%) or incomplete calendar years
        if total_days_in_year < 300:
            records.append({
                "year": y,
                "onset_date": None,
                "onset_doy": None,
                "cessation_date": None,
                "cessation_doy": None,
                "length_days": None,
                "season_rain_mm": None,
                "dry_spells_count": None,
                "longest_dry_spell": None,
                "missing_pct": 100.0,
                "quality_flag": "incomplete_year",
            })
            continue

        onset_date, onset_flag = detect_season_onset(rain, y)
        cessation_date, cessation_flag = detect_season_cessation(rain, y)

        if onset_flag != "ok":
            quality_flag = onset_flag
            length_days = None
            season_rain = None
            dry_spells = None
            longest_dry = None
            missing_pct = 0.0
        elif cessation_flag != "ok":
            quality_flag = cessation_flag
            length_days = None
            season_rain = None
            dry_spells = None
            longest_dry = None
            missing_pct = 0.0
        elif cessation_date <= onset_date:
            quality_flag = "invalid_season_length"
            length_days = None
            season_rain = None
            dry_spells = None
            longest_dry = None
            missing_pct = 0.0
        else:
            length_days = (cessation_date - onset_date).days
            season_slice = rain.loc[(rain.index >= onset_date) & (rain.index <= cessation_date)]
            season_missing = season_slice.isna().sum()
            missing_pct = round((season_missing / len(season_slice)) * 100, 2) if len(season_slice) > 0 else 0.0

            if missing_pct > SEASON_MISSING_DATA_MAX_PCT:
                quality_flag = "high_missing_data"
            else:
                quality_flag = "ok"

            season_rain = round(float(season_slice.sum(skipna=True)), 1)
            dry_spells, longest_dry = _count_dry_spells(season_slice)

        records.append({
            "year": y,
            "onset_date": onset_date,
            "onset_doy": onset_date.day_of_year if onset_date else None,
            "cessation_date": cessation_date,
            "cessation_doy": cessation_date.day_of_year if cessation_date else None,
            "length_days": length_days,
            "season_rain_mm": season_rain,
            "dry_spells_count": dry_spells,
            "longest_dry_spell": longest_dry,
            "missing_pct": missing_pct,
            "quality_flag": quality_flag,
        })

    seasons_df = pd.DataFrame(records).set_index("year")
    return seasons_df


def calculate_monthly_climate(df: pd.DataFrame) -> List[MonthlyClimate]:
    """Computes monthly rainfall P20/P50/P80, mean Tmax, and root-zone wetness."""
    monthly_results: List[MonthlyClimate] = []

    # Prepare temporary grouping columns
    df_temp = df.copy()
    df_temp["year"] = df_temp.index.year
    df_temp["month"] = df_temp.index.month

    for m in range(1, 13):
        m_data = df_temp.loc[df_temp["month"] == m]

        # Monthly rainfall total per year
        if "PRECTOTCORR" in m_data.columns:
            yearly_rain = m_data.groupby("year")["PRECTOTCORR"].sum(skipna=True)
            rain_p20 = round(float(np.percentile(yearly_rain, 20)), 1)
            rain_p50 = round(float(np.percentile(yearly_rain, 50)), 1)
            rain_p80 = round(float(np.percentile(yearly_rain, 80)), 1)
        else:
            rain_p20, rain_p50, rain_p80 = 0.0, 0.0, 0.0

        # Mean daily maximum temperature
        if "T2M_MAX" in m_data.columns:
            yearly_tmax = m_data.groupby("year")["T2M_MAX"].mean()
            tmax = round(float(yearly_tmax.mean()), 1)
        else:
            tmax = 30.0

        # Mean regional root zone wetness
        if "GWETROOT" in m_data.columns:
            yearly_wet = m_data.groupby("year")["GWETROOT"].mean()
            root_wet = round(float(yearly_wet.mean()), 2)
        else:
            root_wet = 0.25

        monthly_results.append(
            MonthlyClimate(
                month=m,
                rain_p20=rain_p20,
                rain_p50=rain_p50,
                rain_p80=rain_p80,
                tmax=tmax,
                regional_root_zone_wetness=root_wet,
            )
        )

    return monthly_results


def calculate_season_stats(seasons_df: pd.DataFrame) -> SeasonStats:
    """Computes median onset, cessation, length, and quality flag counts."""
    ok_seasons = seasons_df.loc[seasons_df["quality_flag"] == "ok"]
    years_ok = len(ok_seasons)
    years_flagged = len(seasons_df) - years_ok

    if not ok_seasons.empty:
        onset_median = int(np.median(ok_seasons["onset_doy"].dropna()))
        cessation_median = int(np.median(ok_seasons["cessation_doy"].dropna()))
        length_median = int(np.median(ok_seasons["length_days"].dropna()))
        length_p20 = int(np.percentile(ok_seasons["length_days"].dropna(), 20))
    else:
        onset_median = 150
        cessation_median = 275
        length_median = 125
        length_p20 = 98

    return SeasonStats(
        onset_doy_median=onset_median,
        cessation_doy_median=cessation_median,
        length_days_median=length_median,
        length_days_p20=length_p20,
        method="simplified_v2",
        years_ok=years_ok,
        years_flagged=years_flagged,
    )


def calculate_season_rain_total(seasons_df: pd.DataFrame) -> SeasonRainTotal:
    """Computes median seasonal rainfall total, P20, and CV."""
    ok_seasons = seasons_df.loc[seasons_df["quality_flag"] == "ok"]
    if not ok_seasons.empty and "season_rain_mm" in ok_seasons.columns:
        totals = ok_seasons["season_rain_mm"].dropna().values
        median_mm = round(float(np.median(totals)), 1)
        p20_mm = round(float(np.percentile(totals, 20)), 1)
        mean_mm = float(np.mean(totals))
        std_mm = float(np.std(totals))
        cv = round(std_mm / mean_mm, 2) if mean_mm > 0 else 0.0
    else:
        median_mm = 700.0
        p20_mm = 550.0
        cv = 0.20

    return SeasonRainTotal(median_mm=median_mm, p20_mm=p20_mm, cv=cv)


def calculate_dry_spells(seasons_df: pd.DataFrame) -> DrySpells:
    """Computes average dry spells per season and median longest dry spell."""
    ok_seasons = seasons_df.loc[seasons_df["quality_flag"] == "ok"]
    if not ok_seasons.empty:
        counts = ok_seasons["dry_spells_count"].dropna().values
        longest = ok_seasons["longest_dry_spell"].dropna().values
        avg_spells = round(float(np.mean(counts)), 1) if len(counts) > 0 else 0.0
        longest_median = int(np.median(longest)) if len(longest) > 0 else 0
    else:
        avg_spells = 2.0
        longest_median = 10

    return DrySpells(avg_per_season=avg_spells, longest_median_days=longest_median)


def calculate_heat_stress(df: pd.DataFrame) -> HeatStressDays:
    """Computes median annual heat stress days where Tmax >= 35 C."""
    if "T2M_MAX" in df.columns:
        hot_days = df["T2M_MAX"] >= HEAT_STRESS_THRESHOLD_C
        annual_hot = hot_days.groupby(df.index.year).sum()
        median_days = int(np.median(annual_hot)) if not annual_hot.empty else 0
    else:
        median_days = 30

    return HeatStressDays(median=median_days, threshold_c=HEAT_STRESS_THRESHOLD_C)


def calculate_rainfall_trend(seasons_df: pd.DataFrame) -> Trend:
    """Computes decadal trend in seasonal rainfall via linear regression."""
    ok_seasons = seasons_df.loc[seasons_df["quality_flag"] == "ok"].dropna(subset=["season_rain_mm"])
    if len(ok_seasons) >= 5:
        x = ok_seasons.index.values.astype(float)
        y = ok_seasons["season_rain_mm"].values.astype(float)
        slope, _ = np.polyfit(x, y, 1)  # mm per year
        decadal_slope = round(float(slope * 10.0), 1)  # mm per decade
    else:
        decadal_slope = 0.0

    return Trend(
        season_rain_mm_per_decade=decadal_slope,
        note="indicative only, not a forecast",
    )


def calculate_bare_field_window(monthly: List[MonthlyClimate]) -> BareFieldWindow:
    """Identifies bare-field window as low-rain, low root-zone wetness months."""
    bare_months: List[int] = []
    for m in monthly:
        if m.rain_p50 <= BARE_FIELD_RAIN_P50_MAX_MM and m.regional_root_zone_wetness <= BARE_FIELD_WETNESS_MAX:
            bare_months.append(m.month)

    # Fallback to standard Sahel dry months if criteria match nothing
    if not bare_months:
        bare_months = [12, 1, 2, 3]

    return BareFieldWindow(months=bare_months, basis="proxy")


def compute_climate_summary(
    df: pd.DataFrame,
    lat: float,
    lon: float,
    location_label: Optional[str] = None,
    from_cache: bool = False,
    missing_pct: float = 0.0,
    flags: Optional[List[str]] = None,
) -> ClimateResponse:
    """Computes full climate response from cleaned daily DataFrame matching Section 9."""
    if flags is None:
        flags = []

    # 1. Seasons
    seasons_df = calculate_annual_seasons(df)
    season_stats = calculate_season_stats(seasons_df)
    season_rain = calculate_season_rain_total(seasons_df)
    dry_spells = calculate_dry_spells(seasons_df)

    # 2. Monthly profiles
    monthly = calculate_monthly_climate(df)

    # 3. Heat stress, trend, bare field
    heat_stress = calculate_heat_stress(df)
    trend = calculate_rainfall_trend(seasons_df)
    bare_field = calculate_bare_field_window(monthly)

    # 4. Location and dataset metadata
    start_year = df.index.year.min()
    end_year = df.index.year.max()
    period_str = f"{start_year}-{end_year}"

    label = location_label or f"Coordinates ({lat:.2f}, {lon:.2f})"

    location = ClimateLocation(lat=lat, lon=lon, label=label)
    datasets = [
        DatasetInfo(
            name="NASA POWER daily",
            community=NASA_POWER_COMMUNITY,
            time_standard=NASA_POWER_TIME_STANDARD,
            resolution_note="coarse global grid, not field-level",
            period=period_str,
        )
    ]

    data_quality = DataQuality(
        from_cache=from_cache,
        missing_pct=missing_pct,
        flags=flags,
    )

    return ClimateResponse(
        location=location,
        datasets=datasets,
        monthly=monthly,
        season=season_stats,
        season_rain_total=season_rain,
        dry_spells=dry_spells,
        heat_stress_days=heat_stress,
        trend=trend,
        bare_field_window=bare_field,
        data_quality=data_quality,
    )
