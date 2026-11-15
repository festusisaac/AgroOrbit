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
| `PLANTING_DELAY_DAYS` | `0 days` (configurable 0–7) | Days elapsed between the detected onset date and field sowing/tillage. Default 0 assumes immediate planting on safe onset. | false | backend |
| `CROP_SEASON_BUFFER_DAYS` | `10 days` | Safety buffer required between crop physiological maturity and season cessation to allow grain drying and harvest. | false | backend |
| `CRITICAL_WINDOW_START_PCT` | `0.25` (25% of duration) | Assumed onset of crop reproductive / flowering phase where moisture stress causes irreversible floret abortion. | false | backend |
| `CRITICAL_WINDOW_END_PCT` | `0.60` (60% of duration) | Assumed termination of flowering and early grain-filling sensitive phase. | false | backend |
| `MID_SEASON_DRY_SPELL_MAX_DAYS` | `7 days` | Consecutive rainless days during the flowering window (25–60% duration) that constitutes a critical yield-damaging dry spell. | false | backend |
| `SAFETY_WEIGHT_SEASON_FIT` | `0.10` (10%) | Fixed safety weighting applied to season_fit regardless of farmer priorities to prevent unfeasible rotations from ranking well. | false | backend |
| `FEASIBILITY_COMPLETION_MIN_PCT` | `50.0%` | Hard gate: any sequence with a crop failing season completion in >50% of years is capped at 'weak' fit category. | false | backend |
| `SCORE_STRONG_MIN` | `75.0` | Lower score threshold for 'strong' fit category. | false | backend |
| `SCORE_MODERATE_MIN` | `55.0` | Lower score threshold for 'moderate' fit category (scores < 55 are 'weak'). | false | backend |
| `SCORE_SIMILARITY_THRESHOLD` | `5.0 points` | Maximum score delta below which two rotations are classified as similar options rather than declaring a clear winner. | false | backend |
| `ALGORITHM_VERSION` | `0.2.0` | Recommendation engine version tracked in rotation trace metadata for auditability. | true | backend |
| `CLIMATE_PERIOD` | `1991-2025` | 35-year historical climate baseline period used for empirical frequency distributions. | true | backend |
| Candidate Return Caps | Min 3, Max 5 | The engine always returns the farmer's existing rotation plus at least 2 distinct alternatives, capped at 5 total recommendations. | false | backend |
| Maize Trait Placeholders | Duration: 90–120d, Water: 500–800mm, Drought: 2/5, Heat: 2/5, Residue: 3/5, Cover: 2/5, Forage: 3/5, Root: medium | Plausible placeholder agronomic traits for unimodal savanna maize. Unverified pending national extension citation. | false | agronomy placeholder |
| Sorghum Trait Placeholders | Duration: 100–140d, Water: 400–650mm, Drought: 4/5, Heat: 4/5, Residue: 4/5, Cover: 3/5, Forage: 3/5, Root: deep | Plausible placeholder agronomic traits for savanna grain sorghum varieties. | false | agronomy placeholder |
| Pearl Millet Trait Placeholders | Duration: 75–100d, Water: 300–500mm, Drought: 5/5, Heat: 5/5, Residue: 3/5, Cover: 2/5, Forage: 3/5, Root: deep | Plausible placeholder agronomic traits for drought-tolerant Sahelian pearl millet. | false | agronomy placeholder |
| Cowpea Trait Placeholders | Duration: 60–90d, Water: 300–500mm, Drought: 4/5, Heat: 4/5, Nitrogen Fixing: true, Cover: 4/5, Forage: 4/5, Root: shallow | Plausible placeholder agronomic traits for short-season grain/fodder cowpea. | false | agronomy placeholder |
| Groundnut Trait Placeholders | Duration: 90–120d, Water: 450–650mm, Drought: 3/5, Heat: 3/5, Nitrogen Fixing: true, Cover: 4/5, Forage: 4/5, Root: medium | Plausible placeholder agronomic traits for upright/runner groundnut cultivars. | false | agronomy placeholder |
| Soybean Trait Placeholders | Duration: 95–125d, Water: 450–700mm, Drought: 2/5, Heat: 3/5, Nitrogen Fixing: true, Cover: 3/5, Forage: 3/5, Root: medium | Plausible placeholder agronomic traits for medium-duration savanna soybean. | false | agronomy placeholder |
| Soil Texture Modifiers | Sandy: -15 water fit, 1.25 erosion risk; Loam: baseline 0; Clay: +5 water fit, waterlogging risk | Heuristic adjustments reflecting soil moisture retention and erosion risks across soil classes. | false | agronomy placeholder |
| Soil Drainage Modifiers | Poor: -20 waterlogging penalty; Moderate: 0; Well: 0, -5 water loss | Heuristics penalizing waterlogging-sensitive crops under poor internal drainage. | false | agronomy placeholder |
| Soil Organic Matter Modifiers | Low: 1.30 soil health priority multiplier, -10 water buffer; High: 0.80 multiplier, +10 water buffer | Heuristic adjustments reflecting moisture buffering and residue demands. | false | agronomy placeholder |
| Slope Modifiers | Flat: 0.70 erosion weight; Gentle: 1.0; Steep: 1.50 erosion weight | Heuristic adjustments weighting ground cover traits on sloping fields. | false | agronomy placeholder |
| Input Validation Bounds | Lat: `[-90, 90]`, Lon: `[-180, 180]`, Priorities: `0–5`, Rotation length: `1–3` | Strict geographic coordinate ranges, 0–5 priority scales, and 1–3 crop sequence limits enforced with 4xx validation errors. | true | backend |
| Soil Enum Validation | Texture: `sandy, loam, clay, unknown`; Drainage: `poor, moderate, well, well_drained, unknown`; OM: `low, medium, high, unknown`; Water: `rain_fed, limited_irrigation, irrigated, unknown`; Slope: `flat, gentle, steep, unknown` | Enforces known categorical enum values matching soil modifier heuristics with clear 4xx validation messages. | true | backend |
| Regional Knowledge Boundary | `6.5°N – 14.0°N`, `2.5°E – 14.5°E` | Delineates northern Nigeria savanna and Middle Belt agroecological zones. Coordinates outside trigger warnings in information_gaps and risks, and lower data confidence. | true | backend |
| Unknown Crop Policy | Marked "not assessed" | Unrecognized crops have NO invented parameters (0 duration, 0 water need), lower knowledge_support to 'low', and are documented in information_gaps and risks. | true | backend |
| Scenario Perturbation (Section 8.5) | Scaled rainfall (`1 + pct/100`), shifted temperature (`+ delta_C`) | Daily meteorological series perturbed and entire pipeline rerun for hypothetical sensitivity analysis. Results labeled hypothetical in assumptions, evidence, and why_suggested. | true | backend |
| Live NASA POWER Fetch | Timeout: `30.0s`, Quality Flag: `live_nasa_fetch` | Live fetches use 30s timeout with retries and clear error messages. Successful live queries set `live_nasa_fetch` flag in data quality. | true | backend |
