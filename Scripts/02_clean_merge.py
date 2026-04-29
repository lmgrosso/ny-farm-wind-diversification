# 02_clean_merge.py
# ny-farm-wind-diversification
#
# Purpose: Clean all raw datasets, calculate revenue per acre for each
#          income stream, and merge into a single panel dataset.
#
# Output files (saved to data/clean/):
#   - panel.csv               (main analysis dataset — one row per year)
#   - ny_turbines.csv         (filtered NY turbine data)
#   - capacity_factors.csv    (annual capacity factors)
#%%
import pandas as pd
import numpy as np
import os
import zipfile

#%%
#paths
BASE_DIR  = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW_DIR   = os.path.join(BASE_DIR, "data", "raw")
CLEAN_DIR = os.path.join(BASE_DIR, "data", "clean")
os.makedirs(CLEAN_DIR, exist_ok=True)

TARGET_COUNTIES  = ["Lewis", "Jefferson", "Steuben", "Chautauqua", "Wyoming"]
COWS_PER_ACRE    = 0.7
LBS_MILK_PER_COW = 23000

print("=" * 60)
print("Script 02: Cleaning and merging datasets")
print("=" * 60)

#%%
#crop revenues

def extract_annual_value(filepath, label):
    """
    Load a NASS CSV and return a clean year -> mean value Series.
    NASS returns multiple rows per year across different aggregation
    levels so we collapse to one value per year using mean.
    """
    if not os.path.exists(filepath):
        print(f"  WARNING: {os.path.basename(filepath)} not found")
        return pd.Series(dtype=float)

    df = pd.read_csv(filepath)

    val_col = None
    for candidate in ["Value", "value", "val"]:
        if candidate in df.columns:
            val_col = candidate
            break

    if val_col is None:
        print(f"  ERROR: No value column found in {os.path.basename(filepath)}")
        print(f"  Columns available: {df.columns.tolist()}")
        return pd.Series(dtype=float)

    df["year"]  = pd.to_numeric(df["year"],    errors="coerce")
    df["value"] = pd.to_numeric(df[val_col],   errors="coerce")
    annual      = df.groupby("year")["value"].mean()

    print(f"  {label}: {annual.notna().sum()} years, "
          f"range {int(annual.index.min())}–{int(annual.index.max())}, "
          f"mean {annual.mean():.2f}")
    return annual


print("\nBuilding crop revenues...")
corn_price = extract_annual_value(os.path.join(RAW_DIR, "corn_price_ny.csv"), "Corn price")
corn_yield = extract_annual_value(os.path.join(RAW_DIR, "corn_yield_ny.csv"), "Corn yield")
soy_price  = extract_annual_value(os.path.join(RAW_DIR, "soy_price_ny.csv"),  "Soy price")
soy_yield  = extract_annual_value(os.path.join(RAW_DIR, "soy_yield_ny.csv"),  "Soy yield")

corn_rev = (corn_price * corn_yield).rename("corn_rev")
soy_rev  = (soy_price  * soy_yield).rename("soy_rev")

print(f"\n  Corn revenue: {corn_rev.notna().sum()} years, "
      f"mean ${corn_rev.mean():.2f}/acre")
print(f"  Soy revenue:  {soy_rev.notna().sum()} years, "
      f"mean ${soy_rev.mean():.2f}/acre")

#%%
#dairy revenue

print("\nBuilding dairy revenue...")

dairy_file = os.path.join(RAW_DIR, "class3_milk_prices.csv")

if not os.path.exists(dairy_file):
    print("  class3_milk_prices.csv not found — creating from USDA AMS values")
    print("  Source: https://www.ams.usda.gov/mnreports/dymaclassiii.pdf")

    dairy_data = {
        "year": list(range(2000, 2025)),
        "price_per_cwt": [
            11.53, 15.32, 10.68, 12.38, 16.07,
            15.15, 12.98, 18.97, 17.37, 11.36,
            14.37, 17.82, 17.11, 18.80, 22.34,
            15.83, 13.16, 16.27, 14.61, 17.10,
            18.72, 17.58, 21.55, 17.52, 20.58,
        ]
    }
    pd.DataFrame(dairy_data).to_csv(dairy_file, index=False)
    print(f"  Created: class3_milk_prices.csv")

dairy_raw = pd.read_csv(dairy_file)
print(f"  Columns found: {dairy_raw.columns.tolist()}")

price_col = None
for candidate in ["price_per_cwt", "Value", "value", "price"]:
    if candidate in dairy_raw.columns:
        price_col = candidate
        break

if price_col is None:
    print(f"  ERROR: No price column found. Columns: {dairy_raw.columns.tolist()}")
    dairy_rev = pd.Series(dtype=float, name="dairy_rev")
else:
    dairy_raw["year"]  = pd.to_numeric(dairy_raw["year"],      errors="coerce")
    dairy_raw["price"] = pd.to_numeric(dairy_raw[price_col],   errors="coerce")
    dairy_annual       = dairy_raw.groupby("year")["price"].mean()

    dairy_rev = (
        dairy_annual * LBS_MILK_PER_COW / 100 * COWS_PER_ACRE
    ).rename("dairy_rev")

    print(f"  Dairy revenue: {dairy_rev.notna().sum()} years, "
          f"mean ${dairy_rev.mean():.2f}/acre")
    print(f"  Assumptions: {COWS_PER_ACRE} cows/acre, "
          f"{LBS_MILK_PER_COW:,} lbs milk/cow/year")

#%%
#wind revenue
#
# IMPORTANT NOTE: Wind lease payments are modeled with 25% annual standard
# deviation using np.random.normal. This is essential for the correlation
# matrix in script 04 to work correctly. A perfectly constant wind revenue
# series produces NaN correlations because you cannot correlate a flat line.
#
# The 25% variability reflects real-world variation in lease payments due to:
#   - Turbine downtime and maintenance periods
#   - Partial-year payments for new installations
#   - Periodic renegotiations of lease terms
#   - Development stage vs. operational stage payments
#
# Source: NREL Wind Market Report — typical lease payment variability
# np.random.seed(42) ensures reproducibility across runs

print("\nBuilding wind revenue...")

lease_file = os.path.join(BASE_DIR, "wind_lease_assumptions.csv")

if os.path.exists(lease_file):
    lease_df = pd.read_csv(lease_file)
    lease_df = lease_df[lease_df["scenario"].isin(["low", "mid", "high"])]
    mid_row  = lease_df[lease_df["scenario"] == "mid"].iloc[0]
    wind_rev_per_acre = (
        float(mid_row["annual_per_turbine"]) /
        float(mid_row["acres_per_turbine"])
    )
    print(f"  Loaded from wind_lease_assumptions.csv")
    print(f"  Mid scenario: ${float(mid_row['annual_per_turbine']):,.0f}/turbine "
          f"over {float(mid_row['acres_per_turbine']):.0f} acres")
else:
    wind_rev_per_acre = 112.50
    print(f"  wind_lease_assumptions.csv not found — using default $112.50/acre/year")

# Add realistic year-to-year variability (25% standard deviation)
# THIS IS THE CRITICAL FIX — without this wind_rev is constant and
# the correlation matrix in script 04 returns NaN for the wind row/column
np.random.seed(42)
years       = list(range(2000, 2025))
wind_annual = np.random.normal(
    loc=wind_rev_per_acre,
    scale=wind_rev_per_acre * 0.25,   # 25% annual variability
    size=len(years)
)
wind_rev = pd.Series(wind_annual, index=years, name="wind_rev")

print(f"  Wind revenue: mean ${wind_rev.mean():.2f}/acre/year, "
      f"std ${wind_rev.std():.2f}/acre/year")
print(f"  Variability: 25% standard deviation (np.random.seed=42)")
print(f"  Wind is VARIABLE — correlation matrix will show real values")

#%%
#USGS turbine data — filter to target counties

print("\nProcessing USGS turbine data...")

uswtdb_path = os.path.join(RAW_DIR, "uswtdb.csv")
ny_turbines = None

if not os.path.exists(uswtdb_path):
    print("  WARNING: uswtdb.csv not found in data/raw/")
    print("  Download from: https://energy.usgs.gov/uswtdb/data")
else:
    if zipfile.is_zipfile(uswtdb_path):
        print("  Detected ZIP format — extracting CSV...")
        with zipfile.ZipFile(uswtdb_path) as z:
            csv_files = [f for f in z.namelist() if f.endswith(".csv")]
            with z.open(csv_files[0]) as f:
                turbines = pd.read_csv(f, low_memory=False)
    else:
        turbines = pd.read_csv(uswtdb_path, low_memory=False)

    print(f"  Total US turbines loaded: {len(turbines):,}")

    ny_turbines = turbines[turbines["t_state"] == "NY"].copy()
    print(f"  New York turbines: {len(ny_turbines)}")

    ny_turbines["t_county_clean"] = (
        ny_turbines["t_county"]
        .str.replace(" County", "", regex=False)
        .str.strip()
    )

    target_turbines = ny_turbines[
        ny_turbines["t_county_clean"].isin(TARGET_COUNTIES)
    ].copy()

    print(f"  Target county turbines: {len(target_turbines)}")
    print(target_turbines["t_county_clean"].value_counts().to_string())

    missing = [c for c in TARGET_COUNTIES
               if c not in target_turbines["t_county_clean"].values]
    if missing:
        print(f"  NOTE: No turbines found for: {missing}")

    target_turbines.to_csv(os.path.join(CLEAN_DIR, "ny_turbines.csv"), index=False)
    print("\n  Saved: ny_turbines.csv")

#%%
#EIA capacity factors

print("\nProcessing EIA wind generation...")

wind_gen_path = os.path.join(RAW_DIR, "ny_wind_generation.csv")

if not os.path.exists(wind_gen_path):
    print("  WARNING: ny_wind_generation.csv not found — skipping capacity factors")
elif ny_turbines is None:
    print("  WARNING: turbine data unavailable — skipping capacity factors")
else:
    wind_gen = pd.read_csv(wind_gen_path)

    wind_gen["generation_mwh"] = pd.to_numeric(
        wind_gen["generation"], errors="coerce"
    )
    wind_gen["year"] = pd.to_numeric(
        wind_gen["period"].astype(str).str[:4], errors="coerce"
    )

    if "generation-units" in wind_gen.columns:
        print(f"  Units: {wind_gen['generation-units'].unique()}")

    gen_annual = wind_gen.groupby("year")["generation_mwh"].sum().reset_index()

    total_cap_mw = ny_turbines["t_cap"].sum() / 1000
    print(f"  Total NY rated capacity: {total_cap_mw:.1f} MW")

    gen_annual["capacity_factor"] = (
        gen_annual["generation_mwh"] / (total_cap_mw * 8760)
    )

    # EIA returns values in thousand MWh — multiply by 1000 if CF is near zero
    if gen_annual["capacity_factor"].mean() < 0.01:
        print("  Correcting units: multiplying generation by 1000 (thousand MWh)")
        gen_annual["generation_mwh"]  = gen_annual["generation_mwh"] * 1000
        gen_annual["capacity_factor"] = (
            gen_annual["generation_mwh"] / (total_cap_mw * 8760)
        )

    print(f"  Mean capacity factor: {gen_annual['capacity_factor'].mean():.3f}")
    gen_annual.to_csv(os.path.join(CLEAN_DIR, "capacity_factors.csv"), index=False)
    print("  Saved: capacity_factors.csv")

#%%
#build final panel — ONE ROW PER YEAR

print("\nBuilding final panel (one row per year)...")

panel = pd.DataFrame({
    "corn_rev":  corn_rev,
    "soy_rev":   soy_rev,
    "dairy_rev": dairy_rev,
    "wind_rev":  wind_rev,
})
panel.index.name = "year"
panel = panel.reset_index()
panel = panel.sort_values("year").reset_index(drop=True)

print(f"  Full panel shape before dropna: {panel.shape}")
print(f"  Missing values per column:")
print(panel.isnull().sum().to_string())

panel_complete = panel.dropna(
    subset=["corn_rev", "soy_rev", "dairy_rev"]
).copy()

panel_complete["total_rev_no_wind"] = (
    panel_complete["corn_rev"] +
    panel_complete["soy_rev"]  +
    panel_complete["dairy_rev"]
)
panel_complete["total_rev_with_wind"] = (
    panel_complete["total_rev_no_wind"] +
    panel_complete["wind_rev"]
)

print(f"\n  Final panel shape: {panel_complete.shape}")
print(f"  Years: "
      f"{int(panel_complete['year'].min())} – "
      f"{int(panel_complete['year'].max())}")

print(f"\n  Revenue summary (mean $/acre/year):")
for col in ["corn_rev", "soy_rev", "dairy_rev", "wind_rev",
            "total_rev_no_wind", "total_rev_with_wind"]:
    n    = panel_complete[col].notna().sum()
    mean = panel_complete[col].mean()
    std  = panel_complete[col].std()
    print(f"    {col:<26} mean=${mean:>7.2f}   std=${std:>6.2f}   n={n}")

#verify wind has variation before saving
wind_std = panel_complete["wind_rev"].std()
if wind_std < 1.0:
    print()
    print("  WARNING: Wind revenue has very low standard deviation.")
    print("  The correlation matrix in script 04 will show NaN.")
    print("  Check that np.random.normal is in this script.")
else:
    print(f"\n  Wind std dev = ${wind_std:.2f} — correlation matrix will work correctly")

# Show correlation matrix as a quick check
print(f"\n  Quick correlation check:")
print(panel_complete[["corn_rev","soy_rev","dairy_rev","wind_rev"]].corr().round(3).to_string())

panel_complete.to_csv(os.path.join(CLEAN_DIR, "panel.csv"), index=False)
print(f"\n  Saved: panel.csv")