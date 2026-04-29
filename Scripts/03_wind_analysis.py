# 03_wind_analysis.py
# ny-farm-wind-diversification
#
# Purpose: Analyze wind turbine capacity factors across the four target
#          counties. Produces county comparison chart, trend over time,
#          and a spatial map of turbine locations within New York State.
#

# Output figures (saved to output/figures/):
#   - fig00_turbine_location_map.png
#   - fig01_county_capacity_factors.png
#   - fig02_capacity_factor_trend.png
#%%
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import matplotlib.patches as mpatches
from matplotlib.lines import Line2D
import os
import zipfile
#%%
#paths
BASE_DIR  = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CLEAN_DIR = os.path.join(BASE_DIR, "data", "clean")
RAW_DIR   = os.path.join(BASE_DIR, "data", "raw")
FIG_DIR   = os.path.join(BASE_DIR, "output", "figures")
os.makedirs(FIG_DIR, exist_ok=True)

TARGET_COUNTIES = ["Lewis", "Wyoming", "Steuben", "Chautauqua"]

COUNTY_COLORS = {
    "Lewis":      "#2196a8",
    "Wyoming":    "#3a9e6e",
    "Steuben":    "#5c7abf",
    "Chautauqua": "#b86b3c",
}

COUNTY_CF = {
    "Lewis":      0.365,
    "Wyoming":    0.290,
    "Steuben":    0.305,
    "Chautauqua": 0.300,
}

print("=" * 60)
print("Script 03: Wind capacity factor analysis")
print("=" * 60)

#%%
#load turbine and CF data
turbine_file = os.path.join(CLEAN_DIR, "ny_turbines.csv")
cf_file      = os.path.join(CLEAN_DIR, "capacity_factors.csv")

if not os.path.exists(turbine_file):
    print("ERROR: ny_turbines.csv not found. Run 02_clean_merge.py first.")
    exit(1)

turbines = pd.read_csv(turbine_file, low_memory=False)
print(f"  Loaded {len(turbines)} turbines")

cf_df = pd.read_csv(cf_file) if os.path.exists(cf_file) else None
if cf_df is None:
    print("  WARNING: capacity_factors.csv not found — fig02 will be skipped")

print()

county_summary = (
    turbines.groupby("t_county_clean")
    .agg(
        turbine_count=("t_cap",   "count"),
        total_capacity_kw=("t_cap", "sum"),
        mean_hub_height=("t_hh",  "mean"),
        mean_rotor_diameter=("t_rd", "mean"),
        mean_install_year=("p_year", "mean")
    )
    .reset_index()
)
county_summary["total_capacity_mw"]   = county_summary["total_capacity_kw"] / 1000
county_summary["est_capacity_factor"] = (
    county_summary["t_county_clean"].map(COUNTY_CF)
)


#%%
#FIGURE 00: New York State map with real county shapes and turbine locations

print("  Building Figure 00: NYS turbine location map...")

try:
    import geopandas as gpd
    from shapely.geometry import Point

    zip_path = os.path.join(RAW_DIR, "tl_2025_us_county.zip")
    shp_dir  = os.path.join(RAW_DIR, "us_county_shapes")
    shp_path = os.path.join(shp_dir, "tl_2025_us_county.shp")

    if not os.path.exists(shp_path):
        if not os.path.exists(zip_path):
            print(f"  ERROR: Shapefile not found at {zip_path}")
            print()
            print("  To fix this:")
            print("  1. Download tl_2025_us_county.zip from the Census Bureau")
            print("     or use the copy you already have")
            print(f"  2. Place it at: {zip_path}")
            print("  3. Re-run this script")
            raise FileNotFoundError(f"Missing: {zip_path}")

        print(f"  Extracting shapefile from zip...")
        os.makedirs(shp_dir, exist_ok=True)
        with zipfile.ZipFile(zip_path, "r") as z:
            z.extractall(shp_dir)
        print(f"  Extracted to: {shp_dir}")
    else:
        print(f"  Using cached shapefile")

    print("  Loading shapefile...")
    us_counties = gpd.read_file(shp_path)
    print(f"  Total US counties: {len(us_counties)}")
    print(f"  Columns: {us_counties.columns.tolist()}")

    ny_all = us_counties[us_counties["STATEFP"] == "36"].copy()
    print(f"  New York counties: {len(ny_all)}")

    ny_target = ny_all[ny_all["NAME"].isin(TARGET_COUNTIES)].copy()
    ny_other  = ny_all[~ny_all["NAME"].isin(TARGET_COUNTIES)].copy()
    print(f"  Target counties found: {ny_target['NAME'].tolist()}")

    ny_all    = ny_all.to_crs("EPSG:32618")
    ny_target = ny_target.to_crs("EPSG:32618")
    ny_other  = ny_other.to_crs("EPSG:32618")

    map_df = turbines.dropna(subset=["xlong", "ylat"]).copy()
    map_df = map_df[
        map_df["xlong"].between(-80, -71) &
        map_df["ylat"].between(40, 46)
    ].copy()

    turbine_gdf = gpd.GeoDataFrame(
        map_df,
        geometry=gpd.points_from_xy(map_df["xlong"], map_df["ylat"]),
        crs="EPSG:4326"
    ).to_crs("EPSG:32618")

    print(f"  Turbines with valid coordinates: {len(turbine_gdf)}")

    fig, ax = plt.subplots(1, 1, figsize=(15, 11))
    fig.patch.set_facecolor("white")
    ax.set_facecolor("#cfe0ed")  # soft blue lake/background color

    ny_other.plot(
        ax=ax,
        color="#ede8df",
        edgecolor="#aaa49a",
        linewidth=0.5,
        zorder=1
    )

    for _, row in ny_target.iterrows():
        county_name = row["NAME"]
        color       = COUNTY_COLORS.get(county_name, "#888888")

        single = gpd.GeoDataFrame(
            [row], geometry="geometry", crs=ny_target.crs
        )

        # Transparent color fill
        single.plot(
            ax=ax,
            color=color,
            alpha=0.28,
            edgecolor="none",
            zorder=2
        )
        # Bold colored border
        single.plot(
            ax=ax,
            color="none",
            edgecolor=color,
            linewidth=2.8,
            zorder=4
        )

    ny_all.plot(
        ax=ax,
        color="none",
        edgecolor="#8a8478",
        linewidth=0.4,
        zorder=3
    )

    for county in TARGET_COUNTIES:
        subset = turbine_gdf[turbine_gdf["t_county_clean"] == county]
        if len(subset) == 0:
            continue
        color = COUNTY_COLORS.get(county, "#555555")

        cap_vals = pd.to_numeric(subset["t_cap"], errors="coerce").fillna(1500)
        sizes    = 16 + ((cap_vals - 500) / (3500 - 500)).clip(0, 1) * 60

        ax.scatter(
            subset.geometry.x,
            subset.geometry.y,
            c=color,
            s=sizes,
            alpha=0.85,
            edgecolors="white",
            linewidths=0.4,
            zorder=6
        )

    LABEL_OFFSETS = {
        "Lewis":      ( 140000,   55000),   # upper-right into Adirondack gap
        "Wyoming":    ( -95000,   65000),   # upper-left above turbine cluster
        "Steuben":    (  10000,  -90000),   # below county near PA border
        "Chautauqua": (-120000,  -15000),   # left of county off western edge
    }

    for _, row in ny_target.iterrows():
        county_name = row["NAME"]
        color       = COUNTY_COLORS.get(county_name, "#888")
        cf_val      = COUNTY_CF.get(county_name, 0)
        centroid    = row.geometry.centroid
        dx, dy      = LABEL_OFFSETS.get(county_name, (80000, 60000))
        # Use count from ny_turbines.csv (same source as bar chart)
        # turbines is loaded from ny_turbines.csv at the top of the script
        n_turb = int(
            county_summary.loc[
                county_summary["t_county_clean"] == county_name,
                "turbine_count"
            ].values[0]
        ) if county_name in county_summary["t_county_clean"].values else 0

        ax.annotate(
            f"{county_name} County\nCF: {cf_val*100:.1f}%  |  {n_turb} turbines",
            xy=(centroid.x, centroid.y),
            xytext=(centroid.x + dx, centroid.y + dy),
            ha="center", va="center",
            fontsize=9, fontweight="bold",
            color="white",
            zorder=8,
            bbox=dict(
                boxstyle="round,pad=0.42",
                facecolor=color,
                edgecolor="white",
                alpha=0.93,
                linewidth=1.4
            ),
            arrowprops=dict(
                arrowstyle="-|>",
                color=color,
                lw=1.8,
                connectionstyle="arc3,rad=0.15"
            )
        )

    #Syracuse reference point
    syr = gpd.GeoDataFrame(
        geometry=gpd.points_from_xy([-76.147], [43.048]),
        crs="EPSG:4326"
    ).to_crs("EPSG:32618")
    sx, sy = syr.geometry.x[0], syr.geometry.y[0]

    ax.plot(sx, sy, marker="*", color="#cc0000",
            markersize=14, zorder=9)
    ax.annotate(
        "Syracuse",
        xy=(sx, sy),
        xytext=(sx + 28000, sy - 22000),
        fontsize=8.5, color="#cc0000", fontweight="bold",
        arrowprops=dict(arrowstyle="-", color="#cc0000", lw=0.8),
        zorder=9
    )

    xlim = ax.get_xlim()
    ylim = ax.get_ylim()
    xw   = xlim[1] - xlim[0]
    yw   = ylim[1] - ylim[0]
    nx   = xlim[0] + xw * 0.955
    nb   = ylim[0] + yw * 0.055
    nt   = ylim[0] + yw * 0.110
    ax.annotate(
        "", xy=(nx, nt), xytext=(nx, nb),
        arrowprops=dict(arrowstyle="-|>", color="#333", lw=2.2)
    )
    ax.text(nx, nt + yw * 0.012, "N",
            ha="center", va="bottom",
            fontsize=13, fontweight="bold", color="#333")

    legend_elements = []

    for county in TARGET_COUNTIES:
        n_turb = (turbine_gdf["t_county_clean"] == county).sum()
        cf     = COUNTY_CF.get(county, 0)
        col    = COUNTY_COLORS.get(county)
        legend_elements.append(
            mpatches.Patch(
                facecolor=col, alpha=0.55,
                edgecolor=col, linewidth=2,
                label=f"{county} County  |  {n_turb} turbines  |  CF {cf*100:.0f}%"
            )
        )

    legend_elements += [
        mpatches.Patch(
            facecolor="#ede8df", edgecolor="#aaa49a",
            linewidth=0.8, label="Other NY counties"
        ),
        Line2D([0], [0], marker="o", color="w",
               markerfacecolor="#888", markersize=5,
               label="Turbine  < 1.5 MW"),
        Line2D([0], [0], marker="o", color="w",
               markerfacecolor="#888", markersize=10,
               label="Turbine ≥ 2.5 MW"),
        Line2D([0], [0], marker="*", color="#cc0000",
               markersize=12, linestyle="None",
               label="Syracuse (reference city)"),
    ]

    ax.legend(
        handles=legend_elements,
        loc="lower left",
        fontsize=9,
        framealpha=0.96,
        title="Legend",
        title_fontsize=9.5,
        edgecolor="#cccccc"
    )

    ax.set_axis_off()
    ax.set_title(
        "Wind turbine locations within New York State\n"
        "Four target counties highlighted  |  "
        "Dot size proportional to rated turbine capacity (MW)",
        fontsize=13, fontweight="bold", pad=16
    )
    ax.text(
        0.01, 0.01,
        "County boundaries: US Census TIGER/Line 2025  |  "
        "Turbine locations: USGS USWTDB v8.3 (2026)  |  "
        "Projection: UTM Zone 18N (EPSG:32618)",
        transform=ax.transAxes,
        fontsize=7.5, color="#888", va="bottom"
    )

    plt.tight_layout()
    fig_path = os.path.join(FIG_DIR, "fig00_turbine_location_map.png")
    plt.savefig(fig_path, dpi=150, bbox_inches="tight")
    plt.close()
    print("  Saved: fig00_turbine_location_map.png")

except ImportError:
    print("  SKIPPED: geopandas not installed")
    print("  Run:  pip install geopandas")
    print("  Then re-run this script")
except FileNotFoundError as e:
    print(f"  SKIPPED: {e}")
except Exception as e:
    import traceback
    print(f"  ERROR: {e}")
    traceback.print_exc()
    print("  Map skipped — other figures will still be produced")

print()

#%%
#FIGURE 1: County bar charts

plt.rcParams.update({
    "figure.facecolor":  "white",
    "axes.facecolor":    "white",
    "axes.spines.top":   False,
    "axes.spines.right": False,
    "axes.grid":         True,
    "grid.alpha":        0.3,
    "grid.linestyle":    "--",
    "font.size":         11,
    "axes.titlesize":    13,
    "axes.titleweight":  "bold"
})

print("  Building Figure 1: County capacity bar charts...")

colors = [
    COUNTY_COLORS.get(c, "#888888")
    for c in county_summary["t_county_clean"]
]

fig, axes = plt.subplots(1, 2, figsize=(12, 5))

bars = axes[0].bar(
    county_summary["t_county_clean"],
    county_summary["total_capacity_mw"],
    color=colors, edgecolor="white", linewidth=0.8
)
axes[0].set_title("Installed wind capacity by county")
axes[0].set_ylabel("Rated capacity (MW)")
axes[0].tick_params(axis="x", rotation=15)
for bar, row in zip(bars, county_summary.itertuples()):
    axes[0].text(
        bar.get_x() + bar.get_width() / 2,
        bar.get_height() + 0.5,
        f"{row.turbine_count} turbines",
        ha="center", va="bottom", fontsize=9, color="#555"
    )

bars2 = axes[1].bar(
    county_summary["t_county_clean"],
    county_summary["est_capacity_factor"] * 100,
    color=colors, edgecolor="white", linewidth=0.8
)
axes[1].set_title("Estimated capacity factor by county")
axes[1].set_ylabel("Capacity factor (%)")
axes[1].tick_params(axis="x", rotation=15)
axes[1].yaxis.set_major_formatter(mticker.FormatStrFormatter("%.0f%%"))
axes[1].set_ylim(0, 50)
for bar, row in zip(bars2, county_summary.itertuples()):
    axes[1].text(
        bar.get_x() + bar.get_width() / 2,
        row.est_capacity_factor * 100 + 0.5,
        f"{row.est_capacity_factor*100:.1f}%",
        ha="center", va="bottom", fontsize=10, fontweight="bold"
    )

plt.suptitle(
    "Wind resources across New York target counties",
    fontsize=14, fontweight="bold", y=1.02
)
plt.tight_layout()
plt.savefig(
    os.path.join(FIG_DIR, "fig01_county_capacity_factors.png"),
    dpi=150, bbox_inches="tight"
)
plt.close()
print("  Saved: fig01_county_capacity_factors.png")

#%%
#FIGURE 2: Capacity factor trend over time
if cf_df is not None:
    print()
    print("  Building Figure 2: Capacity factor trend...")

    cf_clean = cf_df.dropna(subset=["capacity_factor"]).copy()
    cf_clean = cf_clean[cf_clean["year"] >= 2005]

    fig, ax = plt.subplots(figsize=(10, 5))

    ax.plot(
        cf_clean["year"],
        cf_clean["capacity_factor"] * 100,
        color="#2196a8", linewidth=2.5,
        marker="o", markersize=5,
        label="NY state average capacity factor"
    )

    if len(cf_clean) > 3:
        z = np.polyfit(
            cf_clean["year"],
            cf_clean["capacity_factor"] * 100, 1
        )
        p = np.poly1d(z)
        ax.plot(
            cf_clean["year"], p(cf_clean["year"]),
            color="#e07b3c", linewidth=1.5, linestyle="--",
            label=f"Trend ({z[0]:+.2f}% per year)"
        )

    ax.set_title("New York wind turbine capacity factors over time")
    ax.set_ylabel("Capacity factor (%)")
    ax.set_xlabel("Year")
    ax.yaxis.set_major_formatter(mticker.FormatStrFormatter("%.0f%%"))
    ax.legend()
    ax.set_xlim(cf_clean["year"].min() - 0.5,
                cf_clean["year"].max() + 0.5)

    plt.tight_layout()
    plt.savefig(
        os.path.join(FIG_DIR, "fig02_capacity_factor_trend.png"),
        dpi=150, bbox_inches="tight"
    )
    plt.close()
    print("  Saved: fig02_capacity_factor_trend.png")

print()
print("=" * 60)
print("Script 03 complete.")
print()
print("NEXT STEP: python scripts/04_portfolio_model.py")
print("=" * 60)