"""Script to pre-fetch and cache historical NASA POWER data for demo locations.

Demo locations (from Section 9):
- Kano (Sudan Savanna): lat 12.0022, lon 8.5920
- Kaduna (Northern Guinea Savanna): lat 10.5105, lon 7.4165
- Jos (Jos Plateau): lat 9.8965, lon 8.8583
- Makurdi (Southern Guinea Savanna): lat 7.7322, lon 8.5391

Ensures offline reliability and fast responses during judging and development.
"""

import sys
import time
from pathlib import Path

# Add backend to sys.path so app imports resolve
BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_DIR))

from app.config import CACHE_DIR
from app.mock_data import MOCK_LOCATIONS
from app.nasa_power import NasaPowerClient, get_default_record_range


def prefetch_all():
    client = NasaPowerClient(cache_dir=CACHE_DIR)
    start, end = get_default_record_range()
    
    print(f"Pre-fetching NASA POWER daily climatology ({start} to {end})")
    print(f"Target Cache Directory: {CACHE_DIR}")
    print("-" * 65)

    for loc in MOCK_LOCATIONS:
        print(f"\nProcessing {loc.name} ({loc.zone}) at lat={loc.lat}, lon={loc.lon}...")
        t0 = time.time()
        try:
            df, meta = client.fetch_daily_data(
                lat=loc.lat,
                lon=loc.lon,
                start=start,
                end=end,
            )
            elapsed = time.time() - t0
            cached_status = "FROM CACHE" if meta.get("from_cache") else "DOWNLOADED & CACHED"
            print(f"  Status: {cached_status} in {elapsed:.2f}s")
            print(f"  Days retrieved: {len(df)} days ({meta['start_date']} to {meta['end_date']})")
            print(f"  Missing data: {meta['overall_missing_pct']}%")
            print(f"  Cache key: {meta.get('cache_key')}")
        except Exception as e:
            print(f"  ERROR fetching {loc.name}: {e}")

    print("\n" + "=" * 65)
    print("Pre-fetch complete. Verified cached files in data/cache:")
    for f in CACHE_DIR.glob("*.json"):
        size_kb = f.stat().st_size / 1024
        print(f"  - {f.name} ({size_kb:.1f} KB)")


if __name__ == "__main__":
    prefetch_all()
