"""Configuration settings and constants for AgroOrbit."""

import os
from pathlib import Path
from typing import List

# Base filesystem directories
APP_DIR = Path(__file__).resolve().parent
BACKEND_DIR = APP_DIR.parent
DATA_DIR = BACKEND_DIR / "data"
CACHE_DIR = DATA_DIR / "cache"

# Ensure cache directory exists
CACHE_DIR.mkdir(parents=True, exist_ok=True)

# Allowed CORS origins for local frontend development
CORS_ORIGINS: List[str] = os.getenv(
    "CORS_ORIGINS",
    "http://localhost:3000,http://localhost:5173,http://127.0.0.1:3000,http://127.0.0.1:5173",
).split(",")

# ============================================================================
# NASA POWER API Settings (Section 6.1)
# ============================================================================
NASA_POWER_BASE_URL: str = "https://power.larc.nasa.gov/api/temporal/daily/point"
NASA_POWER_COMMUNITY: str = "AG"
NASA_POWER_TIME_STANDARD: str = "UTC"

# 8 parameters verified in Step A
NASA_POWER_DEFAULT_PARAMS: List[str] = [
    "PRECTOTCORR",
    "T2M",
    "T2M_MAX",
    "T2M_MIN",
    "RH2M",
    "ALLSKY_SFC_SW_DWN",
    "GWETTOP",
    "GWETROOT",
]

# Baseline climatology record start year (Section 6.1: default 1991 >= 30 years)
START_YEAR: int = int(os.getenv("START_YEAR", "1991"))

# Grid resolution for caching coordinates (0.25 deg ~= 27 km grid)
GRID_RESOLUTION_DEG: float = float(os.getenv("GRID_RESOLUTION_DEG", "0.25"))

# Fill value used by NASA POWER for missing data
NASA_POWER_FILL_VALUE: float = -999.0

# HTTP client parameters
NASA_POWER_TIMEOUT_SECONDS: float = 30.0
NASA_POWER_MAX_RETRIES: int = 2
NASA_POWER_RETRY_BACKOFF_FACTOR: float = 1.0

# ============================================================================
# Climate Indicator Thresholds (Section 6.2)
# ============================================================================
# Daily rain threshold to classify a day as 'rainy' vs 'dry' (mm)
DRY_DAY_THRESHOLD_MM: float = float(os.getenv("DRY_DAY_THRESHOLD_MM", "1.0"))

# Onset rule: search window
ONSET_SEARCH_START_MMDD: str = os.getenv("ONSET_SEARCH_START_MMDD", "04-01")
ONSET_SEARCH_END_MMDD: str = os.getenv("ONSET_SEARCH_END_MMDD", "08-15")
# 3 consecutive days rain total (mm)
ONSET_RAIN_3DAY_MM: float = float(os.getenv("ONSET_RAIN_3DAY_MM", "20.0"))
# Follow-up check window length (days)
ONSET_POST_WINDOW_DAYS: int = int(os.getenv("ONSET_POST_WINDOW_DAYS", "30"))
# Maximum allowable consecutive dry spell days in post-window
ONSET_MAX_DRY_SPELL_DAYS: int = int(os.getenv("ONSET_MAX_DRY_SPELL_DAYS", "7"))

# Cessation rule (redesigned v2): search window
CESSATION_SEARCH_START_MMDD: str = os.getenv("CESSATION_SEARCH_START_MMDD", "08-15")
CESSATION_SEARCH_END_MMDD: str = os.getenv("CESSATION_SEARCH_END_MMDD", "12-31")
# Window length for wet spell search (days)
CESSATION_WINDOW_DAYS: int = int(os.getenv("CESSATION_WINDOW_DAYS", "5"))
# Rainfall total required in window (mm)
CESSATION_RAIN_WINDOW_MM: float = float(os.getenv("CESSATION_RAIN_WINDOW_MM", "15.0"))

# Dry spell threshold inside growing season (consecutive dry days)
DRY_SPELL_CRITICAL_DAYS: int = int(os.getenv("DRY_SPELL_CRITICAL_DAYS", "7"))

# Heat stress threshold for daily maximum temperature (degrees C)
HEAT_STRESS_THRESHOLD_C: float = float(os.getenv("HEAT_STRESS_THRESHOLD_C", "35.0"))

# Bare-field proxy thresholds
BARE_FIELD_RAIN_P50_MAX_MM: float = float(os.getenv("BARE_FIELD_RAIN_P50_MAX_MM", "10.0"))
BARE_FIELD_WETNESS_MAX: float = float(os.getenv("BARE_FIELD_WETNESS_MAX", "0.30"))

# Missing data tolerance for flagging a season (%)
SEASON_MISSING_DATA_MAX_PCT: float = float(os.getenv("SEASON_MISSING_DATA_MAX_PCT", "10.0"))
