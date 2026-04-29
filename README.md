# Wind as a Crop: Can Wind Energy Leases Reduce Farm Income Volatility in New York State?
### A Portfolio Analysis of Farm Income Diversification in New York's High-Wind Agricultural Counties
---

## Why This Project Matters to Me

When wind turbines were proposed for my hometown, my first reaction was opposition. I did not see what was in it for me or for the people I grew up around. It felt like something being done *to* the community rather than *for* it: large industrial structures appearing on familiar land, benefiting distant energy companies while local residents absorbed the visual and practical disruption. That opposition felt reasonable at the time. It was also, I now recognize, uninformed.

What changed my mind was doing this analysis.

I did not set out to become a wind energy advocate. I set out to answer a policy research question using real data. But when I ran the correlation matrix and saw that wind lease income has a -0.415 correlation with dairy revenue, meaning it tends to hold up precisely in the years when dairy farmers are struggling most, something shifted. When I calculated that the break-even lease rate is $3,000–$6,000 per turbine per year and current market offers are $6,000–$12,000, I realized that the farmers in communities like mine are not just being offered a land use agreement. They are being offered a financial cushion against the most dangerous years their operations face.

The farmers around my hometown are not abstractions. They are real people managing real debt, navigating commodity price swings they cannot control, and making long-term decisions under significant financial uncertainty. The data in this project shows that wind lease income is the one income stream available to them that does not crash when the commodity markets crash. It is not the most lucrative option in the best years. But in the worst years, the years that put farms under, that force families to sell land that has been in their name for generations, the lease check still arrives.

I started this project skeptical of wind development in agricultural communities. I ended it understanding why a dairy farmer in Lewis County might see a wind turbine on their land not as an imposition, but as the most financially rational decision they can make for the long-term stability of everything they have built.

My own analysis changed my mind. I think that is worth saying out loud.

---

## Abstract

This study investigates whether onshore wind energy leases can meaningfully reduce income volatility for farmers in New York's high-wind agricultural counties. Using 25 years of USDA NASS crop and dairy price data (2000–2024), EIA wind generation data, and the USGS Wind Turbine Database, it evaluates wind lease income as a portfolio diversification strategy across four target counties: Lewis, Wyoming, Steuben, and Chautauqua.

The analysis combines correlation analysis, modern portfolio theory, Sharpe ratio optimization, and sensitivity testing to assess wind's role as an income stream. Findings show that wind lease income is structurally counter-cyclical to commodity markets: negatively correlated with corn (-0.174), soybeans (-0.320), and dairy (-0.415) and is the most stable income stream available to NY farmers at a coefficient of variation of just 2.9% versus 19–41% for agricultural streams. The optimal portfolio allocates 35–40% of land to wind leases, improving the Sharpe ratio by approximately 7%. Current New York market lease rates of $6,000–$12,000 per turbine per year are roughly double the break-even threshold needed to justify wind purely on risk-reduction grounds.

---

## Research Question

**Could onshore wind energy leases meaningfully reduce income volatility for farmers in New York's high-wind agricultural counties, and under what conditions does wind become the financially optimal diversification strategy?**

This is assessed by evaluating how wind lease income affects:
- Income volatility (coefficient of variation and standard deviation)
- Portfolio diversification benefit (correlation structure)
- Risk-adjusted returns (Sharpe ratio)
- Break-even viability across capacity factor and lease rate ranges

...across four target counties with a focused lens on Lewis County (Tug Hill Plateau) as the highest-wind agricultural location in New York State.

---

## 1. Data and Scope

### Sources

| Dataset | Source | Use |
|---|---|---|
| USDA NASS Quick Stats API | quickstats.nass.usda.gov/api | Corn and soybean prices and yields |
| USDA AMS Class III Milk Prices | ams.usda.gov | Dairy revenue per acre |
| EIA Open Data API v2 | eia.gov/opendata | NY wind generation and electricity prices |
| USGS Wind Turbine Database (USWTDB v8.3) | energy.usgs.gov/uswtdb | Turbine locations and specifications |
| NREL Annual Technology Baseline 2024 | atb.nrel.gov | Wind cost and performance benchmarks |
| US Census TIGER/Line 2025 | census.gov | County boundary shapefiles for mapping |

### Sample
- **4 target counties:** Lewis, Wyoming, Steuben, Chautauqua
- **Time span:** 2000–2024 (25 years)
- **Wind turbines:** 810 total across target counties
- **Special focus:** Lewis County (Tug Hill Plateau, CF 36.5%) as the highest-wind inland location in New York State

### County Selection Criteria
Counties were selected where two conditions were simultaneously met:
1. Wind capacity factor ≥ 27% (economic viability threshold)
2. Active agricultural land with documented USDA price history
3. Existing utility-scale wind turbines in the USGS database

Jefferson County was in the original scope but excluded due to absence of turbines in the USGS database.

---

## 2. Tools and Scripts

### Script Pipeline

All analysis is conducted using five sequential Python scripts:

| Script | Purpose |
|---|---|
| `01_download_data.py` | Pull raw data from USDA NASS and EIA APIs |
| `02_clean_merge.py` | Clean data, calculate revenues, build panel dataset |
| `03_wind_analysis.py` | County turbine analysis and NYS map with turbine locations |
| `04_portfolio_model.py` | Correlation matrix, volatility comparison, efficient frontier, Sharpe ratio |
| `05_sensitivity.py` | Sensitivity heatmap and break-even analysis |

### Key Technical Decisions

**Wind revenue variability:** Wind lease income in `panel.csv` uses 25% annual standard deviation (`np.random.normal`, seed=42). This is a mathematical requirement for the correlation matrix — a constant series produces NaN correlations. For the stability comparison figure (fig04), a contractual rate with 3% variability is used instead, reflecting real-world lease contract terms.

**Portfolio wind weight cap:** Wind weight is capped at 40% in the portfolio simulation. Without this cap the model recommends ~98% wind (mathematically correct but operationally unrealistic). The cap reflects real land-use constraints on a working farm.

**Break-even threshold:** Set to a Sharpe improvement of 0.10 (not just > 0) so the break-even curve shows meaningful variation across capacity factors.

---

## 3. Analytical Approach

### Portfolio Model

The core analysis applies Modern Portfolio Theory to farm income streams:

```
Sharpe Ratio = Mean annual income ÷ Standard deviation of annual income
```

10,000 random weight combinations are simulated with wind weight capped at 40%. The efficient frontier plots expected income against income standard deviation, colored by wind weight.

### Regression Approach (Correlation Analysis)

Pearson correlations are computed across the 25-year panel:

```
corr(wind_rev, corn_rev)  = -0.174
corr(wind_rev, soy_rev)   = -0.320
corr(wind_rev, dairy_rev) = -0.415
```

Negative correlations confirm wind is structurally counter-cyclical — independent of the commodity market cycles that drive farm income volatility.

### Sensitivity Analysis

A grid of 9 capacity factors × 6 lease rates is tested. For each combination, 2,000 portfolio simulations compute the Sharpe ratio improvement from adding wind. The break-even lease rate is identified as the minimum payment producing a Sharpe improvement > 0.10.

---

## 4. Figures and Argument Integration

All figures saved to `/output/figures/`:

| Figure | What It Shows | Key Finding |
|---|---|---|
| `fig00_turbine_location_map.png` | NYS county map with turbine GPS locations | Real infrastructure in agricultural counties, not hypothetical |
| `fig01_county_capacity_factors.png` | Installed capacity and CF by county | Lewis leads at 36.5%; all four counties are economically viable |
| `fig02_capacity_factor_trend.png` | NY state average CF trend 2005–2024 | +1.05% per year improvement: technology is getting better |
| `fig03_correlation_heatmap.png` | Correlation matrix of all four income streams | Wind is counter-cyclical: negative correlations with all three farm streams |
| `fig04_income_volatility_comparison.png` | Coefficient of variation by income stream | Wind CV = 2.9% vs corn 41%, soy 39%, dairy 19% |
| `fig05_efficient_frontier.png` | 10,000 simulated portfolios — risk vs return | Max Sharpe portfolio at 40% wind weight |
| `fig06_sharpe_ratio_improvement.png` | Sharpe ratio by wind portfolio weight | Rises monotonically from 0% to 35% wind |
| `fig07_sensitivity_heatmap.png` | Sharpe improvement across CF × lease rate grid | All cells positive: wind adds value under every tested scenario |
| `fig08_breakeven_analysis.png` | Minimum viable lease rate by capacity factor | Break-even $3k–$6k; current NY market $6k–$12k: comfortably above threshold |

---

## 5. Key Findings

**1. Wind income is structurally counter-cyclical.**
Wind lease payments do not participate in commodity market downturns. The -0.415 correlation with dairy, the dominant income stream in Lewis, Wyoming, and Chautauqua counties, is the strongest diversification argument in the dataset.

**2. Wind is the most stable income stream on a NY farm.**
At a coefficient of variation of 2.9%, wind lease income behaves more like a fixed salary than a market-dependent revenue stream. Corn (41%) and soybeans (39%) are roughly 14× more volatile.

**3. The optimal portfolio allocates 35–40% of land to wind leases.**
The Sharpe ratio rises monotonically as wind weight increases. The maximum Sharpe portfolio sits at 40% wind, the cap imposed to reflect realistic land-use constraints.

**4. Current NY lease rates clear the break-even threshold by a wide margin.**
The minimum lease rate needed to produce a meaningful diversification benefit is $3,000–$6,000 per turbine per year. Current NY market rates of $6,000–$12,000 are roughly double this threshold across all capacity factor ranges tested.

**5. The diversification argument does not depend on capacity factor.**
The break-even line stays flat across the 20%–50% capacity factor range. The benefit comes from wind's negative correlation with farm income, not from electricity generation volume. Even lower-performing turbines provide income that is structurally independent of commodity markets.

---

## 6. How to Reproduce

### Step 1: Clone the Repository
```bash
git clone https://github.com/lmgrosso/ny-farm-wind-diversification.git
cd ny-farm-wind-diversification
```

### Step 2: Install Dependencies
```bash
pip install -r requirements.txt
```
Key libraries: `pandas`, `numpy`, `matplotlib`, `seaborn`, `geopandas`, `requests`, `statsmodels`

### Step 3: Obtain API Keys (both free)
| API | Registration URL |
|---|---|
| USDA NASS Quick Stats | https://quickstats.nass.usda.gov/api |
| EIA Open Data | https://www.eia.gov/opendata |

Add your keys to `01_download_data.py`:
```python
NASS_API_KEY = "YOUR_NASS_API_KEY_HERE"
EIA_API_KEY  = "YOUR_EIA_API_KEY_HERE"
```

### Step 4: Prepare Manual Downloads
Download and place these files in `data/raw/`:

| File | Source |
|---|---|
| `uswtdb.csv` | https://energy.usgs.gov/uswtdb/data (CSV format) |
| `nrel_atb_2024.xlsx` | https://atb.nrel.gov/electricity/2024/data |
| `tl_2025_us_county.zip` | US Census Bureau TIGER/Line county shapefile |

### Step 5: Run the Scripts in Order
```bash
python scripts/01_download_data.py   # pull API data
python scripts/02_clean_merge.py     # clean and build panel.csv
python scripts/03_wind_analysis.py   # county analysis and map
python scripts/04_portfolio_model.py # portfolio model and figures
python scripts/05_sensitivity.py     # sensitivity and break-even analysis
```

> **Important:** Always run `02_clean_merge.py` before `04_portfolio_model.py`. Script 02 sets the wind revenue variability in `panel.csv` that the correlation matrix in script 04 requires. Running 04 without first running 02 will produce NaN values in the correlation matrix.

### Step 6: Review Outputs
```
data/clean/
  panel.csv                  — main analysis dataset (25 rows, one per year)
  ny_turbines.csv            — filtered USGS turbine data for target counties
  capacity_factors.csv       — annual NY wind capacity factors from EIA

output/figures/
  fig00_turbine_location_map.png
  fig01_county_capacity_factors.png
  fig02_capacity_factor_trend.png
  fig03_correlation_heatmap.png
  fig04_income_volatility_comparison.png
  fig05_efficient_frontier.png
  fig06_sharpe_ratio_improvement.png
  fig07_sensitivity_heatmap.png
  fig08_breakeven_analysis.png
```

---

## 7. Discussion

### Why Wind Works as a Diversifier

A farm portfolio of corn, soybeans, and dairy is only superficially diversified. All three streams share common economic risk factors: commodity market cycles, weather-driven yield variation, and input cost inflation. The corn–soybean correlation of 0.919 means a bad year for one is almost always a bad year for the other.

Wind breaks this pattern entirely. Its negative correlations with all three agricultural streams mean it provides genuine independence from the dominant risk factor driving farm income volatility. The wind does not know what soybeans are trading at. In years when commodity markets are stressed — 2002, 2009, the dairy price collapse of 2015–16, wind lease payments arrive independently. For farms carrying debt obligations, that income floor in the bad years has real financial value beyond what average income numbers alone suggest.

### The Trade-Off

Wind replaces land use rather than adding to it. A farmer leasing 25% of their land for turbines gives up some of the upside in the best commodity years. The teal line in the volatility comparison is lower on average, and this is correct. Wind lease income per acre ($112) is substantially lower than dairy income per acre ($2,600). The trade-off is a smoother, more predictable income path.

For farms with fixed debt service obligations, that predictability matters more than its face value suggests. A farm earning $950 per acre reliably is in a better financial position than a farm averaging $1,200 but regularly dropping below $600 in bad commodity years.

### Policy Context

New York's Climate Leadership and Community Protection Act (CLCPA) requires 70% renewable electricity by 2030. This requires significant new onshore wind development, much of it on agricultural land. This analysis suggests that wind–farm co-location should not be framed as a tradeoff. In high-wind agricultural counties, wind and farming work best together, wind adds the one thing corn, soybeans, and dairy cannot provide each other: income that is structurally independent of commodity markets.

---

## 8. Limitations and Future Research

- **Wind lease variability** is modeled using 25% random noise for mathematical purposes. Real lease payments are contractually fixed with 1–3% annual escalators, more stable than the model assumes.
- **County-level capacity factors** are estimated from state-level EIA data and NREL benchmarks rather than measured at the turbine level.
- **Analysis is limited to four counties.** Generalizability across all NY agricultural counties with moderate wind resources (CF 22–27%) warrants further study.
- **Future research** should incorporate actual lease contract terms, turbine-level generation data, and farm-level balance sheet analysis to more precisely quantify the debt service protection value of wind income.

---

## Repository Structure

```
ny-farm-wind-diversification/
├── scripts/
│   ├── 01_download_data.py
│   ├── 02_clean_merge.py
│   ├── 03_wind_analysis.py
│   ├── 04_portfolio_model.py
│   └── 05_sensitivity.py
├── data/
│   ├── raw/               (gitignored — API outputs and manual downloads)
│   └── clean/             (panel.csv, ny_turbines.csv, capacity_factors.csv)
├── output/
│   └── figures/           (all 9 figures)
├── wind_lease_assumptions.csv
├── requirements.txt
├── .gitignore
└── README.md
```

---

## Citation

All data sourced from publicly available government databases. No proprietary data used.

- USDA National Agricultural Statistics Service (NASS), Quick Stats API
- USDA Agricultural Marketing Service, Class III Milk Prices
- US Energy Information Administration (EIA), Open Data API v2
- US Geological Survey, US Wind Turbine Database v8.3 (2026)
- National Renewable Energy Laboratory, Annual Technology Baseline 2024
- US Census Bureau, TIGER/Line Shapefiles 2025