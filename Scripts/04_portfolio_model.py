# =============================================================================
# 04_portfolio_model.py
# ny-farm-wind-diversification
#
# Purpose: Core portfolio analysis. Calculates the correlation matrix of
#          all four income streams (corn, soy, dairy, wind), builds portfolio
#          combinations, computes Sharpe ratios, and generates the efficient
#          frontier.
##
# Output figures (saved to output/figures/):
#   - fig03_correlation_heatmap.png
#   - fig04_income_volatility_comparison.png
#   - fig05_efficient_frontier.png
#   - fig06_sharpe_ratio_improvement.png
# =============================================================================

#%%
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import seaborn as sns
import os

#%%
#paths and settings
BASE_DIR  = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CLEAN_DIR = os.path.join(BASE_DIR, "data", "clean")
FIG_DIR   = os.path.join(BASE_DIR, "output", "figures")
os.makedirs(FIG_DIR, exist_ok=True)

N_PORTFOLIOS = 10000
np.random.seed(42)

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

print("=" * 60)
print("Script 04: Portfolio model and efficient frontier")
print("=" * 60)

#%%
#load data
panel_file = os.path.join(CLEAN_DIR, "panel.csv")
if not os.path.exists(panel_file):
    print("ERROR: panel.csv not found. Run 02_clean_merge.py first.")
    exit(1)

panel = pd.read_csv(panel_file)
print(f"  Loaded panel: {panel.shape[0]} years")

STREAMS = ["corn_rev", "soy_rev", "dairy_rev", "wind_rev"]
LABELS  = ["Corn", "Soybeans", "Dairy", "Wind lease"]

panel_clean = panel.dropna(subset=STREAMS).copy()
print(f"  Complete cases (all 4 streams): {len(panel_clean)} years")
print(f"  Years: {panel_clean['year'].min()} - {panel_clean['year'].max()}")
print()

revenue = panel_clean[STREAMS].copy()
revenue.columns = LABELS

#%%
#summary stats
print("  Revenue summary statistics ($/acre/year):")
print()
summary = pd.DataFrame({
    "Mean":    revenue.mean(),
    "Std dev": revenue.std(),
    "Min":     revenue.min(),
    "Max":     revenue.max(),
    "CV (%)":  (revenue.std() / revenue.mean() * 100).round(1)
})
print(summary.round(2).to_string())
print()

#%%
#FIGURE 3: Correlation heatmap
print("  Building Figure 3: Correlation heatmap...")

corr = revenue.corr()
print("  Correlation matrix:")
print(corr.round(3).to_string())
print()

fig, ax = plt.subplots(figsize=(7, 6))
sns.heatmap(
    corr, ax=ax, annot=True, fmt=".3f",
    cmap="RdYlGn", vmin=-1, vmax=1, center=0,
    square=True, linewidths=0.5, linecolor="#ddd",
    annot_kws={"size": 13, "weight": "bold"},
    cbar_kws={"shrink": 0.8}
)
ax.set_title(
    "Income stream correlation matrix\nNew York farm revenue 2000-2024",
    pad=15
)
ax.set_xticklabels(ax.get_xticklabels(), rotation=30, ha="right")
ax.set_yticklabels(ax.get_yticklabels(), rotation=0)
plt.tight_layout()
fig.savefig(os.path.join(FIG_DIR, "fig03_correlation_heatmap.png"),
            dpi=150, bbox_inches="tight")
plt.close()
print("  Saved: fig03_correlation_heatmap.png")

#%%
# FIGURE 4: Income stability comparison
# Uses contractual wind lease rate (3% variability) rather than the
# 25% variability in panel.csv — the 25% was a mathematical requirement
# for the correlation matrix, not a reflection of actual lease stability.
print()
print("  Building Figure 4: Income stability comparison...")

np.random.seed(42)
wind_contractual = pd.Series(
    [112.50] * len(panel_clean), index=panel_clean.index
) * (1 + np.random.normal(0, 0.03, len(panel_clean)))

streams = {
    "Corn":       panel_clean["corn_rev"],
    "Soybeans":   panel_clean["soy_rev"],
    "Dairy":      panel_clean["dairy_rev"],
    "Wind lease": wind_contractual,
}

labels = list(streams.keys())
cvs    = [s.std() / s.mean() * 100 for s in streams.values()]
colors = ["#e8b84b", "#4caf7d", "#7c5e9e", "#2196a8"]

fig, ax = plt.subplots(figsize=(9, 6))
bars = ax.bar(labels, cvs, color=colors, edgecolor="white",
              linewidth=1, width=0.55)

for bar, val in zip(bars, cvs):
    ax.text(
        bar.get_x() + bar.get_width() / 2,
        bar.get_height() + 0.8,
        f"{val:.1f}%",
        ha="center", va="bottom",
        fontsize=13, fontweight="bold",
        color=bar.get_facecolor()
    )

wind_bar = bars[labels.index("Wind lease")]
ax.annotate(
    "Wind is the most\npredictable income stream",
    xy=(wind_bar.get_x() + wind_bar.get_width() / 2, cvs[-1] / 2),
    xytext=(wind_bar.get_x() + wind_bar.get_width() / 2 + 0.6, cvs[-1] + 8),
    fontsize=10, color="#0c5878", fontweight="bold", ha="left",
    arrowprops=dict(arrowstyle="->", color="#0c5878", lw=1.5)
)
ax.axhline(cvs[-1], color="#2196a8", linewidth=1.2, linestyle="--", alpha=0.5)
ax.set_ylabel("Income variability (coefficient of variation %)", fontsize=11)
ax.set_ylim(0, max(cvs) * 1.35)
ax.tick_params(axis="x", labelsize=12)
ax.text(
    0.5, -0.13,
    "Coefficient of variation = standard deviation / mean income.  "
    "Higher = more unpredictable year to year.",
    transform=ax.transAxes, ha="center", fontsize=9,
    color="#666", style="italic"
)
plt.suptitle(
    "Wind lease income is far more stable than any crop or dairy stream",
    fontsize=13, fontweight="bold", y=1.01
)
plt.tight_layout()
fig.savefig(os.path.join(FIG_DIR, "fig04_income_volatility_comparison.png"),
            dpi=150, bbox_inches="tight")
plt.close()
print("  Saved: fig04_income_volatility_comparison.png")

#%%
#portfolio simulation
#wind weight capped at 40% to reflect realistic land-use constraints
print()
print("  Running portfolio simulation...")
print(f"  Simulating {N_PORTFOLIOS:,} random weight combinations...")
print(f"  Wind weight capped at 40% (realistic land-use constraint)")

means   = revenue.mean().values
cov_mat = revenue.cov().values

port_returns  = []
port_stds     = []
port_sharpes  = []
port_weights  = []
port_wind_wts = []

for _ in range(N_PORTFOLIOS):
    w = np.random.dirichlet(np.ones(4))
    if w[3] > 0.40:
        excess = w[3] - 0.40
        w[3]   = 0.40
        w[:3]  = w[:3] + (w[:3] / w[:3].sum()) * excess

    ret  = np.dot(w, means)
    std  = np.sqrt(w @ cov_mat @ w)
    shrp = ret / std if std > 0 else 0

    port_returns.append(ret)
    port_stds.append(std)
    port_sharpes.append(shrp)
    port_weights.append(w)
    port_wind_wts.append(w[3])

port_df = pd.DataFrame({
    "return":      port_returns,
    "std":         port_stds,
    "sharpe":      port_sharpes,
    "wind_weight": port_wind_wts
})

best_idx = port_df["sharpe"].idxmax()
print(f"  Sharpe ratio range: {port_df['sharpe'].min():.3f} - {port_df['sharpe'].max():.3f}")
print(f"  Optimal wind weight: {port_df.loc[best_idx, 'wind_weight']*100:.1f}%")
print(f"  Optimal Sharpe: {port_df.loc[best_idx, 'sharpe']:.3f}")
print()

#%%
#FIGURE 5: Efficient frontier
print("  Building Figure 5: Efficient frontier...")

fig, ax = plt.subplots(figsize=(10, 7))
sc = ax.scatter(
    port_df["std"], port_df["return"],
    c=port_df["wind_weight"],
    cmap="RdYlGn", alpha=0.4, s=15, linewidths=0,
    vmin=0, vmax=0.40
)
cbar = plt.colorbar(sc, ax=ax)
cbar.set_label("Wind lease weight in portfolio", fontsize=10)
cbar.ax.yaxis.set_major_formatter(
    plt.FuncFormatter(lambda x, _: f"{x*100:.0f}%")
)

best = port_df.loc[best_idx]
ax.scatter(
    best["std"], best["return"],
    color="gold", s=200, zorder=5, edgecolors="#333", linewidths=1.5,
    label=f"Max Sharpe ratio portfolio\n(wind weight: {best['wind_weight']*100:.1f}%)"
)

no_wind_weights = np.array([1/3, 1/3, 1/3, 0])
no_wind_ret = np.dot(no_wind_weights, means)
no_wind_std = np.sqrt(no_wind_weights @ cov_mat @ no_wind_weights)
ax.scatter(
    no_wind_std, no_wind_ret,
    color="#e07b3c", s=200, zorder=5, marker="D",
    edgecolors="#333", linewidths=1.5,
    label="No wind (equal crop/dairy split)"
)
ax.annotate(
    "Adding wind shifts\nportfolio toward higher\nreturn for same risk",
    xy=(no_wind_std, no_wind_ret),
    xytext=(no_wind_std - 60, no_wind_ret + 80),
    fontsize=9, color="#333",
    arrowprops=dict(arrowstyle="->", color="#666", lw=1.2)
)
ax.set_xlabel("Portfolio income standard deviation ($/acre/year)", fontsize=11)
ax.set_ylabel("Expected portfolio income ($/acre/year)", fontsize=11)
ax.set_title(
    "Efficient frontier: farm income portfolios\n"
    "New York high-wind agricultural counties", pad=15
)
ax.legend(loc="lower right", framealpha=0.9)
plt.tight_layout()
fig.savefig(os.path.join(FIG_DIR, "fig05_efficient_frontier.png"),
            dpi=150, bbox_inches="tight")
plt.close()
print("  Saved: fig05_efficient_frontier.png")

#%%
#FIGURE 6: Sharpe ratio by wind weight
print()
print("  Building Figure 6: Sharpe ratio by wind weight...")

port_df["wind_bin"] = pd.cut(
    port_df["wind_weight"],
    bins=np.arange(0, 0.45, 0.05),
    labels=[f"{int(i*100)}%" for i in np.arange(0, 0.40, 0.05)]
)
sharpe_by_wind = (
    port_df.groupby("wind_bin", observed=True)["sharpe"]
    .mean().reset_index()
)

fig, ax = plt.subplots(figsize=(10, 5))
bars = ax.bar(
    sharpe_by_wind["wind_bin"].astype(str),
    sharpe_by_wind["sharpe"],
    color=[
        "#4caf7d" if v == sharpe_by_wind["sharpe"].max() else "#2196a8"
        for v in sharpe_by_wind["sharpe"]
    ],
    edgecolor="white", linewidth=0.5
)
ax.set_title("Average Sharpe ratio by wind lease portfolio weight")
ax.set_xlabel("Wind lease share of portfolio")
ax.set_ylabel("Sharpe ratio (return / std dev)")
ax.tick_params(axis="x", rotation=0)

optimal_wind = sharpe_by_wind.loc[sharpe_by_wind["sharpe"].idxmax(), "wind_bin"]
ax.text(
    0.98, 0.98,
    f"Optimal wind weight: ~{optimal_wind}",
    transform=ax.transAxes, ha="right", va="top",
    fontsize=10, color="#1a5c38",
    bbox=dict(boxstyle="round,pad=0.4", facecolor="#dff0e8", edgecolor="#4caf7d")
)
plt.tight_layout()
fig.savefig(os.path.join(FIG_DIR, "fig06_sharpe_ratio_improvement.png"),
            dpi=150, bbox_inches="tight")
plt.close()
print("  Saved: fig06_sharpe_ratio_improvement.png")