# AgroOrbit — Assumptions Log

This document tracks every assumption, heuristic constant, unverified agronomic parameter, and data choice in AgroOrbit.

| Item | Value | Reason | Verified | Owner |
|---|---|---|---|---|
| NASA POWER Parameters in Single Request | `PRECTOTCORR, T2M, T2M_MAX, T2M_MIN, RH2M, ALLSKY_SFC_SW_DWN, GWETTOP, GWETROOT` | All 8 parameters queried together in a single request for `community=AG` returned HTTP 200 without needing separate requests. | true | backend |
| NASA POWER Missing Fill Value | `-999.0` | Header `fill_value` returned by POWER API. Must always be mapped to `NaN` and never converted to `0`. | true | NASA POWER API |
| `PRECTOTCORR` parameter & units | `mm/day` | Daily precipitation corrected, confirmed via NASA POWER API metadata. | true | NASA POWER API |
| `T2M`, `T2M_MAX`, `T2M_MIN` units | `C` | Daily mean, max, and min 2-meter air temperature. | true | NASA POWER API |
| `RH2M` units | `%` | Daily relative humidity at 2 meters. | true | NASA POWER API |
| `ALLSKY_SFC_SW_DWN` units | `MJ/m^2/day` | All-sky surface shortwave downward irradiance. | true | NASA POWER API |
| `GWETTOP`, `GWETROOT` units | `1` (dimensionless fraction 0–1) | Regional surface and root-zone soil wetness estimates. | true | NASA POWER API |
| `GRID_RESOLUTION_DEG` | `0.25°` (~27 km) | Spatial rounding grid for cache keys to avoid redundant API downloads within the same coarse satellite grid cell. | true | backend |
| `START_YEAR` default | `1991` | Provides >= 30 complete calendar years of historical daily agroclimatology as required by WMO and NASA climate standards. | true | backend |
| Historical Record End Year | `current_year - 1` | Recent days/months are incomplete in satellite processing. The current partial calendar year is strictly excluded to prevent bias. | true | backend |
| `DRY_DAY_THRESHOLD_MM` | `1.0 mm` | Daily precipitation threshold below which a day is classified as rainless/dry. Standard agronomic convention. | false | backend |
| `ONSET_RAIN_3DAY_MM` | `20.0 mm` | Minimum 3 consecutive days cumulative rainfall required to initiate false-break screening for planting. | false | backend |
| `ONSET_POST_WINDOW_DAYS` | `30 days` | Post-onset observation window to check for crop-killing false breaks. | false | backend |
| `ONSET_MAX_DRY_SPELL_DAYS` | `7 days` | Maximum allowable run of consecutive dry days in the 30-day post-window. If exceeded, planting rain is discarded as a false start. | false | backend |
| `CESSATION_RAIN_WINDOW_MM` | `15.0 mm` over `5 days` | Minimum 5-day cumulative rainfall for the final wet window between Aug 15 and Dec 31. End of this window marks season cessation. | false | backend |
| Mid-September Dry Spell Rule | Redesigned last-wet-window | Cessation is anchored to the *last* 5-day wet window, ensuring erratic September dry spells do not prematurely end the season if rains return in October. | false | backend |
| `HEAT_STRESS_THRESHOLD_C` | `35.0 °C` | Daily T2M_MAX threshold above which crop anthesis / pollination is severely damaged in cereals. | false | backend |
| `DRY_SPELL_CRITICAL_DAYS` | `7 days` | Duration of consecutive rainless days inside the growing season considered a significant stress event. | false | backend |
| `BARE_FIELD_RAIN_P50_MAX_MM` | `10.0 mm` | Monthly median rainfall ceiling to classify a dry-season month into the bare-field proxy window. | false | backend |
| `BARE_FIELD_WETNESS_MAX` | `0.30` | Regional root-zone wetness ceiling to classify a month into the bare-field proxy window. | false | backend |
