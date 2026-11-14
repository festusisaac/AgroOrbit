"""Sanity check climate indicator numbers for all 4 demo locations."""

import sys
from pathlib import Path
from fastapi.testclient import TestClient

BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_DIR))

from app.main import app

client = TestClient(app)

locations = [
    ("Kano (Sudan Savanna)", 12.0022, 8.5920),
    ("Kaduna (Northern Guinea)", 10.5105, 7.4165),
    ("Jos (Jos Plateau)", 9.8965, 8.8583),
    ("Makurdi (Southern Guinea)", 7.7322, 8.5391),
]

print("=" * 110)
print(f"{'Location':<26} | {'Onset DOY':<10} | {'Cessation DOY':<13} | {'Length (days)':<13} | {'Rain Median':<12} | {'Rain P20':<10} | {'Years OK':<8} | {'Flagged':<8}")
print("-" * 110)

for name, lat, lon in locations:
    res = client.get(f"/climate?lat={lat}&lon={lon}")
    assert res.status_code == 200, f"Failed for {name}: {res.text}"
    data = res.json()
    s = data["season"]
    r = data["season_rain_total"]
    q = data["data_quality"]
    print(
        f"{name:<26} | "
        f"{s['onset_doy_median']:^10} | "
        f"{s['cessation_doy_median']:^13} | "
        f"{s['length_days_median']:^13} | "
        f"{r['median_mm']:>9.1f} mm | "
        f"{r['p20_mm']:>7.1f} mm | "
        f"{s['years_ok']:^8} | "
        f"{s['years_flagged']:^8}"
    )

print("=" * 110)

# Check detailed monthly breakdown
for name, lat, lon in locations:
    res = client.get(f"/climate?lat={lat}&lon={lon}")
    data = res.json()
    print(f"\nMonthly Profile for {name}:")
    print(f"{'Month':<6} | {'Rain P20 (mm)':<14} | {'Rain P50 (mm)':<14} | {'Rain P80 (mm)':<14} | {'Tmax (°C)':<10} | {'Root Wetness (0-1)':<18}")
    print("-" * 85)
    for m in data["monthly"]:
        print(f"{m['month']:^6} | {m['rain_p20']:>12.1f}  | {m['rain_p50']:>12.1f}  | {m['rain_p80']:>12.1f}  | {m['tmax']:>8.1f}  | {m['regional_root_zone_wetness']:>16.2f}")
