"""
MGT 403 - Problem Set 4, Question 2: The Distribution of Childcare Prices.

Inputs (all in this folder):
  NDCP2015_2022_center_median.csv   from make_slim.py (NDCP median weekly center-based prices, nominal $)
  county_oews_crosswalk.csv          course-provided county x year -> OEWS area crosswalk
  cpi_u_annual.csv                   CPI-U CUUR0000SA0 annual averages (written by this script, from BLS)

Outputs (folder ps4_output/):
  ndcp_metro_2015_2022.csv           cleaned metro-sample panel, nominal + real 2022 $ prices
  table_2022_summary.csv             Q2.2 mean / SD / N / 95% CI by age group
  table_trends_real.csv              Q2.3 yearly mean real price by age group
  fig_hist_2022.png, fig_trends_real.png
  results.json                       every number quoted in the write-up

Run:  python3 ps4_analysis.py
Methods: large-sample z procedures (CLT). 95% CI = mean +/- 1.96 * s/sqrt(n);
two-sided p = 2 * (1 - Phi(|z|)). A one-sample t-test is run alongside as a check.
"""
import json
import math
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import stats

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "ps4_output")
os.makedirs(OUT, exist_ok=True)

# CPI-U, U.S. city average, all items, NSA (CUUR0000SA0), annual average.
# Verified 2026-09-30: mean of the 12 monthly values returned by the BLS Public Data API v1.
CPI = {2015: 237.017, 2016: 240.007, 2017: 245.120, 2018: 251.107,
       2019: 255.657, 2020: 258.811, 2021: 270.970, 2022: 292.655}
pd.Series(CPI, name="cpi_u_annual_avg").rename_axis("year").to_csv(os.path.join(HERE, "cpi_u_annual.csv"))

# NDCP standard age groups (Technical Report, Appendix C data dictionary)
AGES = {"MCINFANT": "Infant (0-23 mo)", "MCTODDLER": "Toddler (24-35 mo)", "MCPRESCHOOL": "Preschool (36-54 mo)"}
WEEKS_PER_MONTH = 4.33
VOUCHER = {2022: 706.0, 2015: 473.0}  # CCDF monthly voucher, center-based preschool, nominal $

# Chart styling (reference palette slots 1-3; text in neutral ink)
COLORS = dict(zip(AGES.values(), ["#2a78d6", "#eb6834", "#1baf7a"]))
INK, INK2, GRID = "#0b0b0b", "#52514e", "#e4e3df"
plt.rcParams.update({"font.family": "Helvetica", "font.size": 10, "axes.edgecolor": INK2,
                     "axes.labelcolor": INK, "xtick.color": INK2, "ytick.color": INK2,
                     "axes.spines.top": False, "axes.spines.right": False})

# ---------------------------------------------------------------- 1. metro sample
ndcp = pd.read_csv(os.path.join(HERE, "NDCP2015_2022_center_median.csv"), dtype={"COUNTY_FIPS_CODE": str})
cw = pd.read_csv(os.path.join(HERE, "county_oews_crosswalk.csv"), dtype={"county_fips": str, "oews_area": str})
assert ndcp.COUNTY_FIPS_CODE.str.len().eq(5).all() and cw.oews_area.str.len().eq(7).all()
assert not cw.duplicated(["county_fips", "year"]).any()

df = ndcp.merge(cw, left_on=["COUNTY_FIPS_CODE", "STUDYYEAR"], right_on=["county_fips", "year"],
                how="left", validate="one_to_one", indicator=True)
n_unmatched = int((df._merge != "both").sum())
df = df.drop(columns=["_merge", "county_fips", "year"]).rename(columns={"STUDYYEAR": "year"})
df["metro"] = df.oews_area.str.startswith("00")
sample_counts = pd.DataFrame({"ndcp_counties": df.groupby("year").size(),
                              "metro_counties": df[df.metro].groupby("year").size()})
metro = df[df.metro].copy()

for col in AGES:
    metro[col + "_real2022"] = metro[col] * CPI[2022] / metro.year.map(CPI)
metro.to_csv(os.path.join(OUT, "ndcp_metro_2015_2022.csv"), index=False)


def summarize(x):
    x = x.dropna()
    n, m, s = len(x), x.mean(), x.std(ddof=1)
    se = s / math.sqrt(n)
    return {"N": n, "mean": m, "sd": s, "se": se, "ci_lo": m - 1.96 * se, "ci_hi": m + 1.96 * se,
            "median": x.median(), "min": x.min(), "max": x.max()}


# ---------------------------------------------------------------- 2. 2022 distribution
m22 = metro[metro.year == 2022]
summ = pd.DataFrame({lab: summarize(m22[col]) for col, lab in AGES.items()}).T
summ.to_csv(os.path.join(OUT, "table_2022_summary.csv"), float_format="%.2f")

# context only: means weighted by children under 6 (ACS 2022 5-year, from pull_acs.py).
# CT 2022 has no ACS county match (planning regions), so it drops out of the weighted means.
acs22 = pd.read_csv(os.path.join(HERE, "acs_county_2015_2022.csv"), dtype={"county_fips": str})
acs22 = acs22[acs22.year == 2022].set_index("county_fips").kids_under6
w22 = m22.COUNTY_FIPS_CODE.map(acs22)
weighted_2022 = {}
for col, lab in AGES.items():
    ok = m22[col].notna() & w22.notna()
    weighted_2022[lab] = {"N": int(ok.sum()), "mean_weighted_kids_under6": float(np.average(m22.loc[ok, col], weights=w22[ok]))}

# paired differences (same counties) for the discussion
pairs = {}
for a, b in [("MCINFANT", "MCTODDLER"), ("MCTODDLER", "MCPRESCHOOL"), ("MCINFANT", "MCPRESCHOOL")]:
    d = (m22[a] - m22[b]).dropna()
    s = summarize(d)
    s["z"] = s["mean"] / s["se"]
    s["share_positive"] = float((d > 0).mean())
    s["share_tied"] = float((d == 0).mean())
    s["share_negative"] = float((d < 0).mean())
    pairs[f"{AGES[a]}-{AGES[b]}"] = s

fig, axes = plt.subplots(1, 3, figsize=(10.5, 3.9), sharey=True)
bins = np.arange(75, 625, 25)
for ax, (col, lab) in zip(axes, AGES.items()):
    r = summ.loc[lab]
    ax.hist(m22[col].dropna(), bins=bins, color=COLORS[lab], edgecolor="white", linewidth=1)
    ax.axvline(r["mean"], color=INK, lw=1.2, ls="--")
    ax.axvline(r["median"], color=INK2, lw=1.2, ls="-")
    ax.set_title(lab, color=INK, fontsize=11, loc="left", fontweight="bold")
    ax.text(0.97, 0.95, f"mean ${r['mean']:.2f}  (dashed)\nmedian ${r['median']:.2f}  (solid)\n"
            f"SD ${r['sd']:.2f}\nN = {int(r['N']):,}\n95% CI [{r['ci_lo']:.1f}, {r['ci_hi']:.1f}]",
            transform=ax.transAxes, ha="right", va="top", color=INK, fontsize=8.5, linespacing=1.4)
    ax.set_xlabel("Median weekly price, 2022 $")
    ax.grid(axis="y", color=GRID, lw=0.8)
    ax.set_axisbelow(True)
axes[0].set_ylabel("Number of metro counties")
fig.suptitle("Center-based childcare: distribution of county median weekly prices, 2022 (metro counties)\n"
             "Vertical lines: mean (dashed) and median (solid) across counties",
             x=0.01, ha="left", color=INK, fontsize=10.5, linespacing=1.5)
fig.tight_layout()
fig.savefig(os.path.join(OUT, "fig_hist_2022.png"), dpi=200)
plt.close(fig)

# ---------------------------------------------------------------- 3. real trends
rows = []
for (yr, g) in metro.groupby("year"):
    for col, lab in AGES.items():
        s = summarize(g[col + "_real2022"])
        s_nom = summarize(g[col])
        rows.append({"year": yr, "age": lab, "N": s["N"], "mean_real": s["mean"], "ci_lo": s["ci_lo"],
                     "ci_hi": s["ci_hi"], "median_real": s["median"], "mean_nominal": s_nom["mean"]})
trend = pd.DataFrame(rows)

# balanced panel: counties with all three prices observed in every year 2015-2022
have = metro.dropna(subset=list(AGES)).groupby("COUNTY_FIPS_CODE").year.nunique()
bal_ids = have[have == 8].index
bal = metro[metro.COUNTY_FIPS_CODE.isin(bal_ids)]
bal_mean = bal.groupby("year")[[c + "_real2022" for c in AGES]].mean()
for col, lab in AGES.items():
    trend.loc[trend.age == lab, "mean_real_balanced"] = trend.loc[trend.age == lab, "year"].map(bal_mean[col + "_real2022"]).values
trend.to_csv(os.path.join(OUT, "table_trends_real.csv"), index=False, float_format="%.2f")

fig, ax = plt.subplots(figsize=(7.8, 5.2))
for lab in AGES.values():
    t = trend[trend.age == lab]
    ax.fill_between(t.year, t.ci_lo, t.ci_hi, color=COLORS[lab], alpha=0.15, lw=0)
    ax.plot(t.year, t.mean_real, color=COLORS[lab], lw=2, marker="o", ms=5,
            markeredgecolor="white", markeredgewidth=1.5)
    ax.plot(t.year, t.mean_real_balanced, color=COLORS[lab], lw=1.6, ls=(0, (2, 2)))
    ax.text(2022.12, t.mean_real.iloc[-1], lab.replace(" (", "\n("), color=INK, va="center", fontsize=9.5)
ax.set_xlim(2014.7, 2022.9)
ax.set_ylabel("Mean of county median weekly price\n(constant 2022 $)")
ax.grid(axis="y", color=GRID, lw=0.8)
ax.set_axisbelow(True)
ax.set_title("Real center-based childcare prices by age group, metro counties, 2015-2022",
             loc="left", color=INK, fontsize=11)
# legend for line styles (color = age group, labelled at the line ends)
from matplotlib.lines import Line2D
from matplotlib.patches import Patch
handles = [Line2D([], [], color=INK2, lw=2, marker="o", ms=5, markeredgecolor="white"),
           Patch(facecolor=INK2, alpha=0.18, lw=0),
           Line2D([], [], color=INK2, lw=1.6, ls=(0, (2, 2)))]
labels = ["All metro counties with a price that year (mean)",
          "95% confidence interval for that mean",
          f"Balanced panel: {len(bal_ids)} metro counties with all three prices in every year (mean)"]
leg = ax.legend(handles, labels, loc="upper left", bbox_to_anchor=(0, -0.1), ncol=1, frameon=True,
                fontsize=8.5, title="How to read the lines (colour = age group)", title_fontsize=8.5,
                borderpad=0.7, edgecolor=GRID)
leg._legend_box.align = "left"
leg.get_title().set_color(INK)
for txt in leg.get_texts():
    txt.set_color(INK)
ax.text(1, -0.1, "Deflator: CPI-U (CUUR0000SA0),\nannual average, 2022 = base", transform=ax.transAxes,
        ha="right", va="top", fontsize=8, color=INK2)
fig.tight_layout()
fig.savefig(os.path.join(OUT, "fig_trends_real.png"), dpi=200)
plt.close(fig)

# ---------------------------------------------------------------- 4. voucher test
def voucher_test(yr):
    x = metro.loc[metro.year == yr, "MCPRESCHOOL"].dropna()
    mu0 = VOUCHER[yr] / WEEKS_PER_MONTH
    s = summarize(x)
    z = (s["mean"] - mu0) / s["se"]
    p = 2 * (1 - stats.norm.cdf(abs(z)))
    t = stats.ttest_1samp(x, mu0)
    return {"year": yr, "voucher_monthly": VOUCHER[yr], "mu0_weekly": mu0, **s, "z": z, "p_z": p,
            "t_scipy": float(t.statistic), "p_t_scipy": float(t.pvalue),
            "z_crit": stats.norm.ppf(0.975),
            "t_crit": float(stats.t.ppf(0.975, s["N"] - 1)), "df": s["N"] - 1,
            "mean_monthly": s["mean"] * WEEKS_PER_MONTH, "sd_monthly": s["sd"] * WEEKS_PER_MONTH,
            "se_monthly": s["se"] * WEEKS_PER_MONTH,
            "share_counties_above_voucher": float((x > mu0).mean())}

tests = {yr: voucher_test(yr) for yr in (2022, 2015)}


def sign_test(yr):
    """Alternative reading: median across counties = voucher. Share above ~ Binomial(n, 0.5) under H0."""
    x = metro.loc[metro.year == yr, "MCPRESCHOOL"].dropna()
    mu0 = VOUCHER[yr] / WEEKS_PER_MONTH
    above, below = int((x > mu0).sum()), int((x < mu0).sum())
    n = above + below
    phat = above / n
    z = (phat - 0.5) / math.sqrt(0.25 / n)
    p_exact = stats.binom_test(above, n, 0.5) if hasattr(stats, "binom_test") else stats.binomtest(above, n, 0.5).pvalue
    return {"median": float(x.median()), "above": above, "below": below, "n": n, "phat": phat, "z": z,
            "p_z": float(2 * stats.norm.sf(abs(z))), "p_exact": float(p_exact)}


def clustered_test(yr):
    """Same t-test on the mean, but SE allows correlation among counties in the same state (CR1, df = G-1)."""
    x = metro[(metro.year == yr) & metro.MCPRESCHOOL.notna()]
    mu0 = VOUCHER[yr] / WEEKS_PER_MONTH
    n, xbar = len(x), x.MCPRESCHOOL.mean()
    g = (x.MCPRESCHOOL - xbar).groupby(x.STATE_ABBREVIATION).sum()
    G = len(g)
    se = math.sqrt((g ** 2).sum()) / n * math.sqrt(G / (G - 1))
    t = (xbar - mu0) / se
    tc = stats.t.ppf(0.975, G - 1)
    return {"G_states": G, "se_clustered": se, "se_naive": x.MCPRESCHOOL.std() / math.sqrt(n), "t": t,
            "df": G - 1, "t_crit": float(tc), "p": float(2 * stats.t.sf(abs(t), G - 1)),
            "ci_lo": xbar - tc * se, "ci_hi": xbar + tc * se}


signs = {yr: sign_test(yr) for yr in (2022, 2015)}
clustered = {yr: clustered_test(yr) for yr in (2022, 2015)}

# Q4 figures: (1) county price distribution vs the voucher, (2) mean with 95% CI vs the voucher
YEAR_COLORS = {2015: "#2a78d6", 2022: "#eb6834"}
fig, axes = plt.subplots(1, 2, figsize=(10.5, 4.0), sharey=True)
bins = np.arange(50, 525, 12.5)
for ax, yr in zip(axes, (2015, 2022)):
    r = tests[yr]
    x = metro.loc[metro.year == yr, "MCPRESCHOOL"].dropna()
    ax.hist(x, bins=bins, color=YEAR_COLORS[yr], edgecolor="white", linewidth=0.8)
    ax.axvline(r["median"], color=INK2, lw=1.3, zorder=2)
    ax.axvline(r["mean"], color=INK, lw=1.3, ls="--", zorder=2)
    ax.axvline(r["mu0_weekly"], color="#e34948", lw=2.2, zorder=3, alpha=0.9)
    ax.set_title(f"{yr}: voucher \\${r['voucher_monthly']:.0f}/month = \\${r['mu0_weekly']:.2f}/week",
                 loc="left", color=INK, fontsize=10.5, fontweight="bold")
    ax.text(0.97, 0.95,
            f"mean ${r['mean']:.2f} (dashed)\nmedian ${r['median']:.2f} (solid)\n"
            f"voucher ${r['mu0_weekly']:.2f} (red)\n\nt = {r['t_scipy']:.2f},  df = {r['df']:,}\n"
            f"p = {r['p_t_scipy']:.1e}\n{100 * r['share_counties_above_voucher']:.0f}% of counties above voucher",
            transform=ax.transAxes, ha="right", va="top", color=INK, fontsize=8.5, linespacing=1.4)
    ax.set_xlabel("County median weekly price, center-based preschool (36-54 mo), nominal $")
    ax.grid(axis="y", color=GRID, lw=0.8)
    ax.set_axisbelow(True)
axes[0].set_ylabel("Number of metro counties")
fig.suptitle("Q4: CCDF voucher vs. county median preschool prices, metro counties", x=0.01, ha="left",
             color=INK, fontsize=11)
fig.tight_layout()
fig.savefig(os.path.join(OUT, "fig_voucher_hist.png"), dpi=200)
plt.close(fig)

fig, ax = plt.subplots(figsize=(7.5, 2.9))
for k, yr in enumerate((2015, 2022)):
    r = tests[yr]
    y = 1 - k
    m_mo, lo_mo, hi_mo, v_mo = (r["mean"] * WEEKS_PER_MONTH, r["ci_lo"] * WEEKS_PER_MONTH,
                                r["ci_hi"] * WEEKS_PER_MONTH, r["voucher_monthly"])
    ax.plot([v_mo, m_mo], [y, y], color=GRID, lw=6, solid_capstyle="round", zorder=1)
    ax.plot([lo_mo, hi_mo], [y, y], color=YEAR_COLORS[yr], lw=2.5, zorder=2)
    ax.scatter([m_mo], [y], s=70, color=YEAR_COLORS[yr], edgecolor="white", linewidth=2, zorder=3)
    ax.scatter([v_mo], [y], s=70, marker="D", color="#e34948", edgecolor="white", linewidth=2, zorder=3)
    ax.text(v_mo - 6, y + 0.2, f"voucher ${v_mo:.0f}", ha="right", va="bottom", fontsize=8.5, color=INK)
    ax.text(m_mo + 6, y + 0.2, f"mean price ${m_mo:.0f}  [95% CI {lo_mo:.0f}-{hi_mo:.0f}]",
            ha="left", va="bottom", fontsize=8.5, color=INK)
    gap = m_mo - v_mo
    ax.text((v_mo + m_mo) / 2, y - 0.22, f"gap ${gap:.0f}/month ({100 * gap / v_mo:.0f}% of voucher)",
            ha="center", va="top", fontsize=8.5, color=INK2)
ax.set_yticks([1, 0])
ax.set_yticklabels(["2015", "2022"], fontsize=10)
ax.set_ylim(-0.7, 1.6)
ax.set_xlim(420, 900)
ax.set_xlabel("Monthly $ (nominal): weekly price x 4.33")
ax.grid(axis="x", color=GRID, lw=0.8)
ax.set_axisbelow(True)
ax.spines["left"].set_visible(False)
ax.tick_params(axis="y", length=0)
ax.set_title("Average metro county's median preschool price vs. the CCDF voucher", loc="left", color=INK, fontsize=11)
fig.tight_layout()
fig.savefig(os.path.join(OUT, "fig_voucher_gap.png"), dpi=200)
plt.close(fig)

# robustness: treat the metro AREA as the unit (mean of county prices within each OEWS area)
area_rob = {}
for yr in (2022, 2015):
    a = metro[metro.year == yr].groupby("oews_area").MCPRESCHOOL.mean().dropna()
    s = summarize(a)
    mu0 = VOUCHER[yr] / WEEKS_PER_MONTH
    area_rob[yr] = {"N_areas": s["N"], "mean": s["mean"], "sd": s["sd"], "se": s["se"],
                    "z": (s["mean"] - mu0) / s["se"], "p": 2 * (1 - stats.norm.cdf(abs((s["mean"] - mu0) / s["se"]))),
                    "p_t": float(2 * stats.t.sf(abs((s["mean"] - mu0) / s["se"]), s["N"] - 1))}

results = {
    "n_ndcp_rows_unmatched_in_crosswalk": n_unmatched,
    "sample_counts": sample_counts.to_dict(orient="index"),
    "nonmissing_by_year": metro.groupby("year")[list(AGES)].count().to_dict(orient="index"),
    "cpi": CPI,
    "summary_2022": summ.to_dict(orient="index"),
    "paired_differences_2022": pairs,
    "weighted_means_2022_kids_under6": weighted_2022,
    "trend": trend.to_dict(orient="records"),
    "balanced_panel_n": int(len(bal_ids)),
    "voucher_tests": tests,
    "voucher_tests_area_level": area_rob,
    "voucher_sign_test_median": signs,
    "voucher_tests_state_clustered": clustered,
}
with open(os.path.join(OUT, "results.json"), "w") as f:
    json.dump(results, f, indent=2, default=float)

pd.set_option("display.width", 160)
print(sample_counts)
print(summ.round(2))
print(pd.DataFrame(weighted_2022).T.round(2))
print(pd.DataFrame(pairs).T[["N", "mean", "se", "z", "share_positive"]].round(3))
print(trend.pivot(index="year", columns="age", values=["mean_real", "mean_real_balanced", "N"]).round(1))
print(pd.DataFrame(tests).T.drop(columns=["year"]).round(4).T)
print(pd.DataFrame(area_rob).round(4))
