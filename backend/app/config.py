"""Configuration settings and constants for AgroOrbit."""

import os
from typing import List

# Allowed CORS origins for local frontend development
CORS_ORIGINS: List[str] = os.getenv(
    "CORS_ORIGINS",
    "http://localhost:3000,http://localhost:5173,http://127.0.0.1:3000,http://127.0.0.1:5173",
).split(",")
