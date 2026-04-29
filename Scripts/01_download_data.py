# 01_download_data.py
# ny-farm-wind-diversification
#
# Purpose: Pull all raw data from the USDA NASS API and EIA API.
#          Saves raw CSV files to data/raw/ for use
#
# APIs required:
#   - USDA NASS: https://quickstats.nass.usda.gov/api
#   - EIA:       https://www.eia.gov/opendata
#
# Output files saved to data/raw/:
#   - corn_price_ny.csv
#   - corn_yield_ny.csv
#   - soy_price_ny.csv
#   - soy_yield_ny.csv
#   - ny_wind_generation.csv
#   - nyiso_electricity_prices.csv
#
# Manual downloads also required before running:
#   - uswtdb.csv         from https://energy.usgs.gov/uswtdb/data
#   - nrel_atb_2024.xlsx from https://atb.nrel.gov/electricity/2024/data
#%%
import requests
import pandas as pd
import os
import time
#%%
#API Keys
#replace with your own key

NASS_API_KEY = "your_own_key"
EIA_API_KEY  = "your_own_key"
#%%
#paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW_DIR  = os.path.join(BASE_DIR, "data", "raw")
os.makedirs(RAW_DIR, exist_ok=True)

print("=" * 60)
print("Script 01: Downloading raw data")
print("=" * 60)
#%%
#crop prices and yields
def fetch_nass(params, label):
    """
    Fetch data from the USDA NASS Quick Stats API.
    Returns a pandas DataFrame or None if the request fails.
    """
    base_url = "https://quickstats.nass.usda.gov/api/api_GET/"
    params["key"]    = NASS_API_KEY
    params["format"] = "JSON"

    print(f"  Fetching NASS: {label}...")
    response = requests.get(base_url, params=params)

    if response.status_code != 200:
        print(f"  ERROR: NASS request failed — status {response.status_code}")
        print(f"  Response: {response.text[:200]}")
        return None

    data = response.json()

    if "data" not in data:
        print(f"  ERROR: No data returned for {label}")
        print(f"  Response keys: {list(data.keys())}")
        return None

    df = pd.DataFrame(data["data"])
    print(f"  Success: {len(df)} rows returned")
    return df


#corn price $/bushel (New York state — annual — 2000 to present)
corn_price = fetch_nass({
    "commodity_desc":    "CORN",
    "statisticcat_desc": "PRICE RECEIVED",
    "unit_desc":         "$ / BU",
    "state_alpha":       "NY",
    "freq_desc":         "ANNUAL",
    "year__GE":          "2000",
    "agg_level_desc":    "STATE"
}, "Corn price NY")
if corn_price is not None:
    corn_price.to_csv(os.path.join(RAW_DIR, "corn_price_ny.csv"), index=False)
    print("  Saved: corn_price_ny.csv")
time.sleep(1)

#corn yield bushels/acre (New York state — annual)
corn_yield = fetch_nass({
    "commodity_desc":    "CORN",
    "statisticcat_desc": "YIELD",
    "unit_desc":         "BU / ACRE",
    "state_alpha":       "NY",
    "freq_desc":         "ANNUAL",
    "year__GE":          "2000",
    "agg_level_desc":    "STATE"
}, "Corn yield NY")
if corn_yield is not None:
    corn_yield.to_csv(os.path.join(RAW_DIR, "corn_yield_ny.csv"), index=False)
    print("  Saved: corn_yield_ny.csv")
time.sleep(1)

#soybean price $/bushel (New York state — annual)
soy_price = fetch_nass({
    "commodity_desc":    "SOYBEANS",
    "statisticcat_desc": "PRICE RECEIVED",
    "unit_desc":         "$ / BU",
    "state_alpha":       "NY",
    "freq_desc":         "ANNUAL",
    "year__GE":          "2000",
    "agg_level_desc":    "STATE"
}, "Soybean price NY")
if soy_price is not None:
    soy_price.to_csv(os.path.join(RAW_DIR, "soy_price_ny.csv"), index=False)
    print("  Saved: soy_price_ny.csv")
time.sleep(1)

#soybean yield bushels/acre (New York state — annual)
soy_yield = fetch_nass({
    "commodity_desc":    "SOYBEANS",
    "statisticcat_desc": "YIELD",
    "unit_desc":         "BU / ACRE",
    "state_alpha":       "NY",
    "freq_desc":         "ANNUAL",
    "year__GE":          "2000",
    "agg_level_desc":    "STATE"
}, "Soybean yield NY")
if soy_yield is not None:
    soy_yield.to_csv(os.path.join(RAW_DIR, "soy_yield_ny.csv"), index=False)
    print("  Saved: soy_yield_ny.csv")
time.sleep(1)

print()
print("NASS downloads complete.")
print()

#%%
#Wind generation and electricity prices

def fetch_eia(url, label):
    """
    Fetch data from the EIA Open Data API v2.
    Accepts a fully constructed URL string with bracket notation intact.
    Returns a pandas DataFrame or None if the request fails.
    """
    print(f"  Fetching EIA: {label}...")
    response = requests.get(url)

    if response.status_code != 200:
        print(f"  ERROR: EIA request failed — status {response.status_code}")
        print(f"  URL tried: {url[:100]}...")
        print(f"  Response: {response.text[:200]}")
        return None

    data = response.json()

    if "response" not in data:
        print(f"  ERROR: Unexpected response structure")
        print(f"  Keys returned: {list(data.keys())}")
        return None

    records = data["response"].get("data", [])
    if len(records) == 0:
        print(f"  WARNING: 0 rows returned — check API key and parameters")
        return None

    df = pd.DataFrame(records)
    print(f"  Success: {len(df)} rows returned")
    return df


# NY wind generation — annual MWh — all sectors
wind_url = (
    f"https://api.eia.gov/v2/electricity/electric-power-operational-data/data/"
    f"?api_key={EIA_API_KEY}"
    f"&frequency=annual"
    f"&data[]=generation"
    f"&facets[location][]=NY"
    f"&facets[fueltypeid][]=WND"
    f"&facets[sectorid][]=99"
    f"&start=2000"
    f"&end=2024"
    f"&sort[0][column]=period"
    f"&sort[0][direction]=asc"
    f"&length=5000"
)
wind_gen = fetch_eia(wind_url, "NY wind generation")
if wind_gen is not None:
    wind_gen.to_csv(os.path.join(RAW_DIR, "ny_wind_generation.csv"), index=False)
    print("  Saved: ny_wind_generation.csv")
time.sleep(1)

# NY wholesale electricity prices — annual — all sectors
price_url = (
    f"https://api.eia.gov/v2/electricity/retail-sales/data/"
    f"?api_key={EIA_API_KEY}"
    f"&frequency=annual"
    f"&data[]=price"
    f"&facets[stateid][]=NY"
    f"&facets[sectorid][]=ALL"
    f"&start=2000"
    f"&end=2024"
    f"&sort[0][column]=period"
    f"&sort[0][direction]=asc"
    f"&length=5000"
)
elec_price = fetch_eia(price_url, "NY electricity prices")
if elec_price is not None:
    elec_price.to_csv(os.path.join(RAW_DIR, "nyiso_electricity_prices.csv"), index=False)
    print("  Saved: nyiso_electricity_prices.csv")

print(f"Raw files saved to: {RAW_DIR}")
print()
print("BEFORE running script 02, manually download these files")
print("and place them in data/raw/:")
print()
print("  uswtdb.csv")
print("  -> https://energy.usgs.gov/uswtdb/data")
print("  -> download CSV format, rename to uswtdb.csv")
print()
print("  nrel_atb_2024.xlsx")
print("  -> https://atb.nrel.gov/electricity/2024/data")
print("  -> download Excel file, rename to nrel_atb_2024.xlsx")
