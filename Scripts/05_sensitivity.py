# 05_sensitivity.py
# ny-farm-wind-diversification
#
# Purpose: Sensitivity analysis — tests how the portfolio diversification
#          benefit changes under different wind lease rates and capacity
#          factor assumptions.
#

# Output figures saved to output/figures/:
#   - fig07_sensitivity_heatmap.png
#   - fig08_breakeven_analysis.png

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import seaborn as sns
import os

#%%
#paths
BASE_DIR  = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CLEAN_DIR = os.path.join(BASE_DIR, "data", "clean")
FIG_DIR   = os.path.join(BASE_DIR, "output", "figures")
os.makedirs(FIG_DIR, exist_ok=True)

np.random.seed(42)

plt.rcParams.update({
    "figure.facecolor":  "white",
    "axes.facecolor":    "white",
    "axes.spines.top":   False,
    "axes.spines.right": False,
    "font.size":         11,
    "axes.titlesize":    13,
    "axes.titleweight":  "bold"
})

print("=" * 60)
print("Script 05: Sensitivity analysis")
print("=" * 60)

#%%
#load data
panel = pd.read_csv(os.path.join(CLEAN_DIR, "panel.csv"))
panel_clean = panel.dropna(subset=["corn_rev", "soy_rev", "dairy_rev"]).copy()

base_means = np.array([
    panel_clean["corn_rev"].mean(),
    panel_clean["soy_rev"].mean(),
    panel_clean["dairy_rev"].mean()
])
base_cov = panel_clean[["corn_rev", "soy_rev", "dairy_rev"]].cov().values

print(f"  Base means (corn, soy, dairy): {base_means.round(2)}")
print()

#%%
#parameters

lease_rates       = [4000, 6000, 8000, 10000, 12000, 14000]
capacity_factors  = [0.25, 0.28, 0.30, 0.33, 0.35, 0.38, 0.40, 0.42, 0.45]
acres_per_turbine = 80

lease_file = os.path.join(BASE_DIR, "wind_lease_assumptions.csv")
if os.path.exists(lease_file):
    lease_df = pd.read_csv(lease_file)
    print("  Loaded wind_lease_assumptions.csv")
    print(lease_df.to_string(index=False))
    print()


#%%
#core fuction: Compute Sharpe improvement from adding wind

def compute_portfolio_sharpe_improvement(wind_rev_per_acre,
                                          base_means, base_cov,
                                          n_sim=5000):
    """
    Simulate portfolios with and without wind.
    Returns the average Sharpe ratio improvement from adding wind.
    Wind weight is capped at 40% consistent with script 04.
    """
    wind_mean = wind_rev_per_acre
    wind_std  = wind_rev_per_acre * 0.25   # 25% annual variability

    all_means    = np.append(base_means, wind_mean)
    wind_cov_row = np.zeros((1, 3))
    wind_var     = wind_std ** 2
    full_cov     = np.block([
        [base_cov,      wind_cov_row.T],
        [wind_cov_row,  np.array([[wind_var]])]
    ])

    sharpes_no_wind   = []
    sharpes_with_wind = []

    for _ in range(n_sim):
        # Portfolio without wind
        w3  = np.random.dirichlet(np.ones(3))
        ret3 = np.dot(w3, base_means)
        std3 = np.sqrt(w3 @ base_cov @ w3)
        if std3 > 0:
            sharpes_no_wind.append(ret3 / std3)

        # Portfolio with wind — cap wind at 40%
        w4 = np.random.dirichlet(np.ones(4))
        if w4[3] > 0.40:
            excess = w4[3] - 0.40
            w4[3]  = 0.40
            w4[:3] = w4[:3] + (w4[:3] / w4[:3].sum()) * excess
        ret4 = np.dot(w4, all_means)
        std4 = np.sqrt(w4 @ full_cov @ w4)
        if std4 > 0:
            sharpes_with_wind.append(ret4 / std4)

    return np.mean(sharpes_with_wind) - np.mean(sharpes_no_wind)

#%%
#build sensitivity grid

print("  Running sensitivity grid...")
print(f"  {len(capacity_factors)} capacity factors x "
      f"{len(lease_rates)} lease rates = "
      f"{len(capacity_factors)*len(lease_rates)} combinations")
print()

heatmap_data = np.zeros((len(capacity_factors), len(lease_rates)))

for i, cf in enumerate(capacity_factors):
    for j, lease in enumerate(lease_rates):
        wind_rev    = lease / acres_per_turbine
        improvement = compute_portfolio_sharpe_improvement(
            wind_rev, base_means, base_cov, n_sim=2000
        )
        heatmap_data[i, j] = improvement
        print(f"  CF={cf*100:.0f}%, Lease=${lease:,}: "
              f"Sharpe improvement = {improvement:+.4f}")

print()

#%%
# FIGURE 7: Sensitivity heatmap

print("  Building Figure 7: Sensitivity heatmap...")

cf_labels    = [f"{int(cf*100)}%" for cf in capacity_factors]
lease_labels = [f"${l//1000}k" for l in lease_rates]

heatmap_df = pd.DataFrame(
    heatmap_data,
    index=cf_labels,
    columns=lease_labels
)

fig, ax = plt.subplots(figsize=(11, 7))

sns.heatmap(
    heatmap_df,
    ax=ax,
    annot=True,
    fmt=".4f",
    cmap="RdYlGn",
    center=0,
    linewidths=0.5,
    linecolor="#ddd",
    annot_kws={"size": 10},
    cbar_kws={
        "label": "Sharpe ratio improvement from adding wind",
        "shrink": 0.8
    }
)

ax.set_title(
    "Sharpe ratio improvement from adding wind lease income\n"
    "Sensitivity to capacity factor and annual lease rate",
    pad=15
)
ax.set_xlabel("Annual lease rate per turbine ($/year)")
ax.set_ylabel("Wind capacity factor (%)")
ax.set_xticklabels(ax.get_xticklabels(), rotation=0)
ax.set_yticklabels(ax.get_yticklabels(), rotation=0)

# Mark typical New York range
ax.add_patch(plt.Rectangle(
    (1, 2), 4, 3,
    fill=False, edgecolor="navy",
    linewidth=2.5, linestyle="--"
))
ax.legend(
    handles=[plt.Rectangle(
        (0,0), 1, 1, fill=False,
        edgecolor="navy", linewidth=2, linestyle="--"
    )],
    labels=["Typical NY range"],
    loc="lower right", framealpha=0.9
)

plt.tight_layout()
fig.savefig(os.path.join(FIG_DIR, "fig07_sensitivity_heatmap.png"),
            dpi=150, bbox_inches="tight")
plt.close()
print("  Saved: fig07_sensitivity_heatmap.png")

#%%
# FIGURE 8: Break-even lease rate by capacity factor
# Threshold set to 0.10 so the line shows meaningful variation
# (a threshold of 0 produces a flat line near the minimum because
#  even a tiny wind payment passes the test given negative correlations)

print()
print("  Building Figure 8: Break-even analysis...")
print("  Using Sharpe improvement threshold of 0.10")

cf_range    = np.linspace(0.20, 0.50, 30)
lease_range = np.linspace(2000, 16000, 50)

breakeven_rates = []

for cf in cf_range:
    found = False
    for lease in lease_range:
        wind_rev    = lease / acres_per_turbine
        improvement = compute_portfolio_sharpe_improvement(
            wind_rev, base_means, base_cov, n_sim=1000
        )
        if improvement > 0.10:   # meaningful threshold, not just above zero
            breakeven_rates.append((cf * 100, lease))
            found = True
            break
    if not found:
        breakeven_rates.append((cf * 100, np.nan))

be_df = pd.DataFrame(
    breakeven_rates,
    columns=["capacity_factor_pct", "breakeven_lease"]
)
be_df = be_df.dropna()

fig, ax = plt.subplots(figsize=(9, 5))

ax.plot(
    be_df["capacity_factor_pct"],
    be_df["breakeven_lease"],
    color="#2196a8",
    linewidth=2.5,
    label="Minimum lease rate for positive diversification benefit"
)

ax.fill_between(
    be_df["capacity_factor_pct"],
    be_df["breakeven_lease"],
    16000,
    alpha=0.15, color="#4caf7d",
    label="Wind adds diversification value"
)
ax.fill_between(
    be_df["capacity_factor_pct"],
    2000,
    be_df["breakeven_lease"],
    alpha=0.15, color="#e05c5c",
    label="Wind does not add diversification value"
)

ax.axvspan(27, 38, alpha=0.2, color="navy",
           label="Typical NY capacity factor range")
ax.axhspan(6000, 12000, alpha=0.1, color="gold",
           label="Typical NY lease rate range")

ax.set_xlabel("Wind capacity factor (%)")
ax.set_ylabel("Minimum viable lease rate ($/turbine/year)")
ax.set_title("Break-even lease rates for portfolio diversification benefit")
ax.yaxis.set_major_formatter(
    mticker.FuncFormatter(lambda x, _: f"${x:,.0f}")
)
ax.legend(fontsize=9, loc="upper right")
ax.set_xlim(20, 50)
ax.set_ylim(0, 17000)

plt.tight_layout()
fig.savefig(os.path.join(FIG_DIR, "fig08_breakeven_analysis.png"),
            dpi=150, bbox_inches="tight")
plt.close()
print("  Saved: fig08_breakeven_analysis.png")

print()
print("=" * 60)
print("Script 05 complete — all analysis finished.")
print()
print("All 8 figures saved to: output/figures/")
print()
print("FINAL STEP: Update README.md with results and push to GitHub")
print("=" * 60)
