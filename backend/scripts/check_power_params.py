"""Verification script for NASA POWER API parameters.

Tests whether PRECTOTCORR, T2M, T2M_MAX, T2M_MIN, RH2M, ALLSKY_SFC_SW_DWN,
GWETTOP, and GWETROOT can be queried together for the AG community at the
daily point level, or whether soil wetness must be queried separately.
"""

import json
import sys
from typing import Dict, List, Optional
import httpx

POWER_URL = "https://power.larc.nasa.gov/api/temporal/daily/point"

ALL_TARGET_PARAMS = [
    "PRECTOTCORR",
    "T2M",
    "T2M_MAX",
    "T2M_MIN",
    "RH2M",
    "ALLSKY_SFC_SW_DWN",
    "GWETTOP",
    "GWETROOT",
]

METEO_PARAMS = [
    "PRECTOTCORR",
    "T2M",
    "T2M_MAX",
    "T2M_MIN",
    "RH2M",
    "ALLSKY_SFC_SW_DWN",
]

SOIL_PARAMS = [
    "GWETTOP",
    "GWETROOT",
]


def query_power(
    params: List[str],
    lat: float = 12.0,
    lon: float = 8.5,
    start: str = "20230601",
    end: str = "20260930",
) -> Optional[Dict]:
    """Query NASA POWER API daily point endpoint."""
    query_params = {
        "parameters": ",".join(params),
        "community": "AG",
        "longitude": lon,
        "latitude": lat,
        "start": start,
        "end": end,
        "format": "JSON",
        "time-standard": "UTC",
    }
    print(f"\nSending request for {len(params)} parameters:")
    print(f"  URL: {POWER_URL}")
    print(f"  Parameters: {','.join(params)}")
    
    try:
        with httpx.Client(timeout=30.0) as client:
            response = client.get(POWER_URL, params=query_params)
            print(f"  HTTP Status: {response.status_code}")
            
            if response.status_code == 200:
                return response.json()
            else:
                print(f"  Request failed: {response.status_code}")
                try:
                    err_json = response.json()
                    print(f"  Error payload: {json.dumps(err_json, indent=2)}")
                except Exception:
                    print(f"  Error text: {response.text[:500]}")
                return None
    except Exception as e:
        print(f"  Exception during request: {e}")
        return None


def extract_parameter_metadata(data: Dict):
    """Extract and print parameter metadata: presence, units, fill value, and sample value."""
    parameters_meta = data.get("parameters", {})
    props_param = data.get("properties", {}).get("parameter", {})
    header = data.get("header", {})
    fill_value = header.get("fill_value", "-999.0")
    
    print("\n--- PARAMETER DETAILS RETURNED BY NASA POWER ---")
    print(f"Header fill_value: {fill_value}")
    print(f"{'Parameter':<20} | {'Units':<15} | {'Long Name':<45} | {'Dates Returned'}")
    print("-" * 95)
    
    for param_name, meta in parameters_meta.items():
        units = meta.get("units", "N/A")
        longname = meta.get("longname", "N/A")
        dates_count = len(props_param.get(param_name, {}))
        print(f"{param_name:<20} | {units:<15} | {longname[:45]:<45} | {dates_count} days")

    # Sample data check
    print("\nSample values for 2023-06-01:")
    for param_name in parameters_meta.keys():
        val = props_param.get(param_name, {}).get("20230601")
        print(f"  {param_name}: {val}")


def main():
    print("================================================================")
    print("STEP 1: Testing all 8 parameters in ONE combined request")
    print("================================================================")
    combined_result = query_power(ALL_TARGET_PARAMS)
    
    if combined_result:
        print("\n>>> SUCCESS: All 8 parameters succeeded in a single request! <<<")
        extract_parameter_metadata(combined_result)
        return

    print("\n================================================================")
    print("STEP 2: Combined request failed. Testing groups separately.")
    print("================================================================")
    
    print("\nSub-test A: Meteorology parameters:")
    meteo_result = query_power(METEO_PARAMS)
    if meteo_result:
        print("\n>>> SUCCESS: Meteorology parameters succeeded! <<<")
        extract_parameter_metadata(meteo_result)
    else:
        print("\n>>> FAILED: Meteorology parameters failed. <<<")
        
    print("\nSub-test B: Soil wetness parameters:")
    soil_result = query_power(SOIL_PARAMS)
    if soil_result:
        print("\n>>> SUCCESS: Soil wetness parameters succeeded! <<<")
        extract_parameter_metadata(soil_result)
    else:
        print("\n>>> FAILED: Soil wetness parameters failed. <<<")


if __name__ == "__main__":
    main()
