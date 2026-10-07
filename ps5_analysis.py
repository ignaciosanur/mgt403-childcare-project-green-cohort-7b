"""
MGT 403 - Problem Set 5, Question 3: Cost Drivers in Childcare.

Inputs (all in this folder):
  county_oews_crosswalk.csv     course crosswalk, county x year -> OEWS area (year-specific)
  oews_39-9011_areas.csv        BLS OEWS childcare-worker wages by area, 2015-2022 (extract_oews.py)
  acs_county_2015_2022.csv      Census ACS 5-year county covariates, 2015-2022 (pull_acs.py)
  cpi_u_annual.csv              CPI-U annual averages (written by ps4_analysis.py)

Outputs (ps5_output/):
  county_year_metro_2015_2022.csv   year x county panel: metro counties, OEWS wage, ACS covariates, real $
  table_wage_missing.csv            step 3 sanity check: metro counties with/without a wage, by year
  table_2022_predictors.csv         step 4: mean / SD / N of each predictor, 2022
  table_real_trends.csv             step 5: mean real wage and rent by year
  fig_real_wage_rent.png            step 5 chart
  fig_wage_vs_college.png           step 7 chart
  results.json                      every number quoted in the write-up

Run:  python3 ps5_analysis.py
"""
import json
import math
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import statsmodels.api as sm
from scipy import stats

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "ps5_output")
os.makedirs(OUT, exist_ok=True)

CPI = pd.read_csv(os.path.join(HERE, "cpi_u_annual.csv")).set_index("year").cpi_u_annual_avg.to_dict()
LEGACY_FIPS = {"12025", "51515"}  # old codes for Miami-Dade (now 12086) and Bedford city VA (merged into 51019)

INK, INK2, GRID = "#0b0b0b", "#52514e", "#e4e3df"
BLUE, ORANGE = "#2a78d6", "#eb6834"
plt.rcParams.update({"font.family": "Helvetica", "font.size": 10, "axes.edgecolor": INK2,
                     "axes.labelcolor": INK, "xtick.color": INK2, "ytick.color": INK2,
                     "axes.spines.top": False, "axes.spines.right": False})

# ---------------------------------------------------------------- step 3: build the year x county panel
cw = pd.read_csv(os.path.join(HERE, "county_oews_crosswalk.csv"), dtype={"county_fips": str, "oews_area": str})
oews = pd.read_csv(os.path.join(HERE, "oews_39-9011_areas.csv"), dtype={"oews_area": str})
acs = pd.read_csv(os.path.join(HERE, "acs_county_2015_2022.csv"), dtype={"county_fips": str})
assert cw.oews_area.str.len().eq(7).all() and oews.oews_area.str.len().eq(7).all()
assert cw.county_fips.str.len().eq(5).all() and acs.county_fips.str.len().eq(5).all()

metro = cw[cw.oews_area.str.startswith("00")].copy()                      # hard rule: metro sample only
metro = metro[~metro.county_fips.isin(LEGACY_FIPS)]                      # duplicates of current codes
panel = metro.merge(oews[["year", "oews_area", "A_MEAN", "A_MEAN_RAW", "TOT_EMP"]],
                    on=["year", "oews_area"], how="left", validate="many_to_one")
acs_vars = ["per_capita_income", "pop_total", "kids_under6", "kids_under6_allpar_lf", "median_gross_rent",
            "female_college_share", "female_ftyr_share", "under6_share", "under6_careneed_share"]
panel = panel.merge(acs[["year", "county_fips", "NAME"] + acs_vars], on=["year", "county_fips"],
                    how="left", validate="one_to_one", indicator="acs_merge")
panel = panel.rename(columns={"A_MEAN": "wage_childcare", "NAME": "county_name"})
panel["cpi_factor"] = CPI[2022] / panel.year.map(CPI)
for c in ["wage_childcare", "median_gross_rent", "per_capita_income"]:
    panel[c + "_real2022"] = panel[c] * panel.cpi_factor
panel = panel.sort_values(["year", "county_fips"])
panel.drop(columns=["acs_merge"]).to_csv(os.path.join(OUT, "county_year_metro_2015_2022.csv"), index=False)

miss = panel.groupby("year").agg(metro_counties=("county_fips", "size"),
                                 missing_wage=("wage_childcare", lambda s: int(s.isna().sum())),
                                 missing_acs=("acs_merge", lambda s: int((s != "both").sum())))
miss["pct_missing_wage"] = 100 * miss.missing_wage / miss.metro_counties
miss.to_csv(os.path.join(OUT, "table_wage_missing.csv"), float_format="%.2f")
missing_wage_areas_2022 = (panel[(panel.year == 2022) & panel.wage_childcare.isna()]
                           .groupby("area_title").size().to_dict())
missing_acs_2022 = sorted(panel[(panel.year == 2022) & (panel.acs_merge != "both")].county_fips)


# ---------------------------------------------------------------- step 4: 2022 descriptive table
def describe(x):
    x = x.dropna()
    return {"N": len(x), "mean": x.mean(), "sd": x.std(ddof=1), "min": x.min(), "max": x.max()}


LABELS = {
    "wage_childcare": "Childcare-worker mean annual wage (OEWS 39-9011), $",
    "per_capita_income": "Per-capita income, $",
    "pop_total": "Total population",
    "kids_under6": "Own children under 6",
    "kids_under6_allpar_lf": "Children under 6 with all parents in labor force",
    "median_gross_rent": "Median gross rent (rent + utilities), $/month",
    "female_college_share": "Share of women 25+ with bachelor's degree or higher",
    "female_ftyr_share": "Share of women 16-64 working full-time, year-round",
    "under6_share": "Share of population under 6",
    "under6_careneed_share": "Share of population under 6 with all parents working",
}
p22 = panel[panel.year == 2022]
desc = pd.DataFrame({LABELS[c]: describe(p22[c]) for c in LABELS}).T
desc.to_csv(os.path.join(OUT, "table_2022_predictors.csv"), float_format="%.4f")

# ---------------------------------------------------------------- step 5: real wage and rent trends
have = panel.dropna(subset=["wage_childcare_real2022", "median_gross_rent_real2022"]).groupby("county_fips").year.nunique()
balanced_ids = have[have == 8].index
rows = []
for yr, g in panel.groupby("year"):
    b = g[g.county_fips.isin(balanced_ids)]
    row = {"year": yr}
    for c in ["wage_childcare", "median_gross_rent"]:
        d = describe(g[c + "_real2022"])
        se = d["sd"] / math.sqrt(d["N"])
        row.update({f"{c}_real_mean": d["mean"], f"{c}_real_ci_lo": d["mean"] - 1.96 * se,
                    f"{c}_real_ci_hi": d["mean"] + 1.96 * se, f"{c}_N": d["N"],
                    f"{c}_real_mean_balanced": b[c + "_real2022"].mean(),
                    f"{c}_nominal_mean": g[c].mean()})
    rows.append(row)
trend = pd.DataFrame(rows)
trend.to_csv(os.path.join(OUT, "table_real_trends.csv"), index=False, float_format="%.2f")

fig, axes = plt.subplots(1, 2, figsize=(10.5, 4.3))
for ax, c, color, title, ylab in [
        (axes[0], "wage_childcare", BLUE, "Childcare-worker mean annual wage", "Constant 2022 $ per year"),
        (axes[1], "median_gross_rent", ORANGE, "Median gross rent", "Constant 2022 $ per month")]:
    ax.fill_between(trend.year, trend[f"{c}_real_ci_lo"], trend[f"{c}_real_ci_hi"], color=color, alpha=0.15, lw=0)
    ax.plot(trend.year, trend[f"{c}_real_mean"], color=color, lw=2, marker="o", ms=5,
            markeredgecolor="white", markeredgewidth=1.5)
    ax.plot(trend.year, trend[f"{c}_real_mean_balanced"], color=color, lw=1.6, ls=(0, (2, 2)))
    ax.plot(trend.year, trend[f"{c}_nominal_mean"], color=INK2, lw=1.2, ls=(0, (1, 2)))
    ax.set_title(title, loc="left", color=INK, fontsize=11, fontweight="bold")
    ax.set_ylabel(ylab)
    ax.grid(axis="y", color=GRID, lw=0.8)
    ax.set_axisbelow(True)
    ax.yaxis.set_major_formatter(matplotlib.ticker.StrMethodFormatter("${x:,.0f}"))
    first, last = trend.iloc[0], trend.iloc[-1]
    ax.annotate(f"${last[f'{c}_real_mean']:,.0f}", (2022, last[f"{c}_real_mean"]), xytext=(6, 0),
                textcoords="offset points", va="center", fontsize=9, color=INK)
    ax.annotate(f"${first[f'{c}_real_mean']:,.0f}", (2015, first[f"{c}_real_mean"]), xytext=(-6, 0),
                textcoords="offset points", va="center", ha="right", fontsize=9, color=INK)
    ax.set_xlim(2013.6, 2022.9)
    ax.set_xticks(range(2015, 2023))
from matplotlib.lines import Line2D
from matplotlib.patches import Patch
handles = [Line2D([], [], color=INK2, lw=2, marker="o", ms=5, markeredgecolor="white"),
           Patch(facecolor=INK2, alpha=0.18, lw=0),
           Line2D([], [], color=INK2, lw=1.6, ls=(0, (2, 2))),
           Line2D([], [], color=INK2, lw=1.2, ls=(0, (1, 2)))]
labels = ["Real (2022 $), mean across metro counties", "95% CI for that mean",
          f"Real, balanced panel ({len(balanced_ids)} counties with data every year)", "Nominal $ (not inflation-adjusted)"]
fig.legend(handles, labels, loc="lower center", ncol=2, frameon=False, fontsize=8.5, bbox_to_anchor=(0.5, -0.01))
fig.suptitle("Childcare-worker wages and rents in metro counties, 2015-2022 (deflated with CPI-U, 2022 = base)",
             x=0.01, ha="left", color=INK, fontsize=11)
fig.tight_layout(rect=(0, 0.08, 1, 1))
fig.savefig(os.path.join(OUT, "fig_real_wage_rent.png"), dpi=200)
plt.close(fig)

# ---------------------------------------------------------------- step 6: real wage 2022 vs 2019
w19 = panel.loc[panel.year == 2019, ["county_fips", "oews_area", "wage_childcare_real2022"]].dropna()
w22 = panel.loc[panel.year == 2022, ["county_fips", "oews_area", "wage_childcare_real2022"]].dropna()
x22, x19 = w22.wage_childcare_real2022, w19.wage_childcare_real2022
n22, n19 = len(x22), len(x19)
m22, m19, s22, s19 = x22.mean(), x19.mean(), x22.std(ddof=1), x19.std(ddof=1)
se_diff = math.sqrt(s22 ** 2 / n22 + s19 ** 2 / n19)
t_two = (m22 - m19) / se_diff
df_welch = se_diff ** 4 / ((s22 ** 2 / n22) ** 2 / (n22 - 1) + (s19 ** 2 / n19) ** 2 / (n19 - 1))
welch = stats.ttest_ind(x22, x19, equal_var=False)
two_sample = {"n2022": n22, "n2019": n19, "mean2022": m22, "mean2019": m19, "sd2022": s22, "sd2019": s19,
              "diff": m22 - m19, "pct_diff": 100 * (m22 / m19 - 1), "se_diff": se_diff, "t": t_two,
              "df_welch": df_welch, "p_t": float(2 * stats.t.sf(abs(t_two), df_welch)),
              "p_z": float(2 * stats.norm.sf(abs(t_two))), "t_scipy": float(welch.statistic),
              "p_scipy": float(welch.pvalue), "t_crit": float(stats.t.ppf(0.975, df_welch)),
              "ci_lo": (m22 - m19) - stats.t.ppf(0.975, df_welch) * se_diff,
              "ci_hi": (m22 - m19) + stats.t.ppf(0.975, df_welch) * se_diff}

# robustness 1: paired (same county both years)
pair = w22.merge(w19, on="county_fips", suffixes=("_22", "_19"))
d = pair.wage_childcare_real2022_22 - pair.wage_childcare_real2022_19
paired = {"n": len(d), "mean_diff": d.mean(), "sd_diff": d.std(ddof=1), "se": d.std(ddof=1) / math.sqrt(len(d)),
          "t": d.mean() / (d.std(ddof=1) / math.sqrt(len(d))), "p": float(stats.ttest_rel(
              pair.wage_childcare_real2022_22, pair.wage_childcare_real2022_19).pvalue),
          "share_counties_up": float((d > 0).mean())}
# robustness 2: metro area as the unit (wages are measured per area, so counties in one area share a wage)
a22 = oews[(oews.year == 2022) & oews.oews_area.str.startswith("00")].set_index("oews_area").A_MEAN.dropna() * CPI[2022] / CPI[2022]
a19 = oews[(oews.year == 2019) & oews.oews_area.str.startswith("00")].set_index("oews_area").A_MEAN.dropna() * CPI[2022] / CPI[2019]
wt = stats.ttest_ind(a22, a19, equal_var=False)
common = a22.index.intersection(a19.index)
area_level = {"n2022": len(a22), "n2019": len(a19), "mean2022": a22.mean(), "mean2019": a19.mean(),
              "diff": a22.mean() - a19.mean(), "t_welch": float(wt.statistic), "p_welch": float(wt.pvalue),
              "n_paired": len(common),
              "t_paired": float(stats.ttest_rel(a22[common], a19[common]).statistic),
              "p_paired": float(stats.ttest_rel(a22[common], a19[common]).pvalue),
              "share_areas_up": float((a22[common] > a19[common]).mean())}
nominal_change_pct = 100 * (panel.loc[panel.year == 2022, "wage_childcare"].mean()
                            / panel.loc[panel.year == 2019, "wage_childcare"].mean() - 1)

# context: NDCP real preschool price change 2019 -> 2022 in the same metro counties (from ps4 output)
ctx = {}
ndcp_path = os.path.join(HERE, "ps4_output", "ndcp_metro_2015_2022.csv")
if os.path.exists(ndcp_path):
    nd = pd.read_csv(ndcp_path, dtype={"COUNTY_FIPS_CODE": str})
    pre = nd.pivot_table(index="COUNTY_FIPS_CODE", columns="year", values="MCPRESCHOOL_real2022")
    both = pre[[2019, 2022]].dropna()
    ctx = {"n": len(both), "preschool_real_2019": both[2019].mean(), "preschool_real_2022": both[2022].mean(),
           "pct_change": 100 * (both[2022].mean() / both[2019].mean() - 1)}

# ---------------------------------------------------------------- step 7: wage on female college share, 2022
reg = p22[["wage_childcare", "female_college_share", "oews_area", "STATE" if "STATE" in p22 else "state_abbr"]].dropna()
X = sm.add_constant(reg.female_college_share)
ols = sm.OLS(reg.wage_childcare, X).fit()
ols_cl = sm.OLS(reg.wage_childcare, X).fit(cov_type="cluster", cov_kwds={"groups": reg.oews_area})
b, se_b = ols.params.female_college_share, ols.bse.female_college_share
t_crit = stats.t.ppf(0.975, ols.df_resid)
regression = {"n": int(ols.nobs), "intercept": ols.params.const, "se_intercept": ols.bse.const, "slope": b,
              "se_slope": se_b, "t_slope": ols.tvalues.female_college_share,
              "p_slope": float(ols.pvalues.female_college_share), "df_resid": ols.df_resid, "t_crit": t_crit,
              "ci_lo": b - t_crit * se_b, "ci_hi": b + t_crit * se_b, "r2": ols.rsquared,
              "slope_per_10pp": b / 10, "mean_share": reg.female_college_share.mean(),
              "sd_share": reg.female_college_share.std(), "slope_per_1sd": b * reg.female_college_share.std(),
              "se_slope_cluster_area": ols_cl.bse.female_college_share,
              "t_slope_cluster_area": ols_cl.tvalues.female_college_share,
              "p_slope_cluster_area": float(ols_cl.pvalues.female_college_share),
              "n_areas": int(reg.oews_area.nunique())}
with open(os.path.join(OUT, "regression_2022_wage_on_college.txt"), "w") as f:
    f.write(ols.summary().as_text())

fig, ax = plt.subplots(figsize=(7.5, 4.6))
ax.scatter(reg.female_college_share * 100, reg.wage_childcare, s=14, color=BLUE, alpha=0.45, lw=0)
xs = np.linspace(reg.female_college_share.min(), reg.female_college_share.max(), 50)
ax.plot(xs * 100, ols.params.const + b * xs, color=INK, lw=2)
ax.set_xlabel("Share of women 25+ with a bachelor's degree or higher (%), ACS 2018-2022")
ax.set_ylabel("Childcare-worker mean annual wage, 2022 $")
ax.yaxis.set_major_formatter(matplotlib.ticker.StrMethodFormatter("${x:,.0f}"))
ax.grid(color=GRID, lw=0.8)
ax.set_axisbelow(True)
ax.set_title("Childcare-worker wages vs. female college share, metro counties, 2022", loc="left",
             color=INK, fontsize=11)
ax.text(0.02, 0.97, f"wage = {ols.params.const:,.0f} + {b:,.0f} x share\n"
        f"+10 pp share -> +${b / 10:,.0f}/yr  (t = {ols.tvalues.female_college_share:.1f})\n"
        f"R² = {ols.rsquared:.2f},  N = {int(ols.nobs):,} counties", transform=ax.transAxes, va="top",
        fontsize=9, color=INK, bbox=dict(boxstyle="round,pad=0.4", facecolor="white", edgecolor=GRID, alpha=0.95))
fig.tight_layout()
fig.savefig(os.path.join(OUT, "fig_wage_vs_college.png"), dpi=200)
plt.close(fig)

results = {"missing": miss.reset_index().to_dict(orient="records"),
           "missing_wage_areas_2022": missing_wage_areas_2022, "missing_acs_2022": missing_acs_2022,
           "descriptives_2022": desc.to_dict(orient="index"), "trend": trend.to_dict(orient="records"),
           "balanced_panel_n": int(len(balanced_ids)), "wage_test_two_sample": two_sample,
           "wage_test_paired": paired, "wage_test_area_level": area_level,
           "nominal_wage_change_pct_2019_2022": nominal_change_pct, "cpi_change_pct_2019_2022": 100 * (CPI[2022] / CPI[2019] - 1),
           "preschool_price_context": ctx, "regression": regression}
with open(os.path.join(OUT, "results.json"), "w") as f:
    json.dump(results, f, indent=2, default=float)

pd.set_option("display.width", 200)
print(miss)
print(desc.round(3))
print(trend[["year", "wage_childcare_real_mean", "wage_childcare_real_mean_balanced", "wage_childcare_nominal_mean",
             "median_gross_rent_real_mean", "median_gross_rent_real_mean_balanced", "median_gross_rent_nominal_mean"]].round(1))
print(json.dumps({k: results[k] for k in ["wage_test_two_sample", "wage_test_paired", "wage_test_area_level",
                                          "nominal_wage_change_pct_2019_2022", "cpi_change_pct_2019_2022",
                                          "preschool_price_context", "regression"]}, indent=1, default=float))
