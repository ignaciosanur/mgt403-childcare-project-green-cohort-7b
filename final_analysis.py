"""
MGT 403 - Pre-analysis (prices vs. costs) and Final Project: where should we open center-based preschools?

Inputs:
  ps5_output/county_year_metro_2015_2022.csv   metro county x year panel: OEWS wage, ACS covariates (ps5_analysis.py)
  ps4_output/ndcp_metro_2015_2022.csv          NDCP center-based median prices, nominal and real 2022 $ (ps4_analysis.py)

Method (final project):
  1. Cost model, estimated separately for each year on metro counties:
        preschool price ($/week) = a + b * childcare wage ($1,000/yr) + c * median gross rent ($100/month) + e
  2. Premium = actual price - cost-predicted price (the residual e), in real 2022 $/week.
  3. Screens: market size (>= 5,000 children under 6 with all parents in the labor force) and persistence
     (positive premium in every year observed 2019-2022, observed in at least 3 of the 4 years).
  4. Rank screened counties by their 2022 premium -> top 10.

Outputs: final_output/ (tables, figures, results.json).  Run:  python3 final_analysis.py
"""
import json
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import statsmodels.formula.api as smf
from scipy import stats

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "final_output")
os.makedirs(OUT, exist_ok=True)

MIN_KIDS_NEED_CARE = 5000          # market-size screen
PERSIST_YEARS = [2019, 2020, 2021, 2022]

INK, INK2, GRID = "#0b0b0b", "#52514e", "#e4e3df"
BLUE, ORANGE, AQUA, RED = "#2a78d6", "#eb6834", "#1baf7a", "#e34948"
plt.rcParams.update({"font.family": "Helvetica", "font.size": 10, "axes.edgecolor": INK2,
                     "axes.labelcolor": INK, "xtick.color": INK2, "ytick.color": INK2,
                     "axes.spines.top": False, "axes.spines.right": False})

# ------------------------------------------------------------------ pre-analysis 1: analysis dataset
panel = pd.read_csv(os.path.join(HERE, "ps5_output", "county_year_metro_2015_2022.csv"),
                    dtype={"county_fips": str, "oews_area": str})
ndcp = pd.read_csv(os.path.join(HERE, "ps4_output", "ndcp_metro_2015_2022.csv"), dtype={"COUNTY_FIPS_CODE": str})
ndcp = ndcp.rename(columns={"COUNTY_FIPS_CODE": "county_fips", "STATE_ABBREVIATION": "state"})
d = panel.merge(ndcp[["county_fips", "year", "state", "MCPRESCHOOL", "MCPRESCHOOL_real2022"]],
                on=["county_fips", "year"], how="left", validate="one_to_one")

PREDICTORS = ["wage_childcare", "median_gross_rent", "per_capita_income", "pop_total", "kids_under6",
              "kids_under6_allpar_lf", "female_college_share", "female_ftyr_share", "under6_share",
              "under6_careneed_share"]
a = d.dropna(subset=["MCPRESCHOOL"] + PREDICTORS).copy()
a["price"] = a.MCPRESCHOOL_real2022                         # real 2022 $/week (= nominal in 2022)
a["wage_k"] = a.wage_childcare_real2022 / 1000              # $1,000 per year
a["rent_100"] = a.median_gross_rent_real2022 / 100          # $100 per month
a.to_csv(os.path.join(OUT, "analysis_dataset_2015_2022.csv"), index=False)
sample_n = a.groupby("year").size().to_dict()
dropped_2022 = {
    "metro_counties": int((d.year == 2022).sum()),
    "no_price": int(((d.year == 2022) & d.MCPRESCHOOL.isna()).sum()),
    "price_but_missing_predictor": int(((d.year == 2022) & d.MCPRESCHOOL.notna()
                                        & d[PREDICTORS].isna().any(axis=1)).sum()),
}

# ------------------------------------------------------------------ pre-analysis 2: 2022 table
LABELS = {
    "MCPRESCHOOL": "Median weekly price, center-based preschool (36-54 mo), $",
    "wage_childcare": "Childcare-worker mean annual wage, $",
    "median_gross_rent": "Median gross rent, $/month",
    "per_capita_income": "Per-capita income, $",
    "pop_total": "Total population",
    "kids_under6": "Own children under 6",
    "kids_under6_allpar_lf": "Children under 6, all parents in labor force",
    "female_college_share": "Share of women 25+ with bachelor's+",
    "female_ftyr_share": "Share of women 16-64 full-time year-round",
    "under6_share": "Share of population under 6",
    "under6_careneed_share": "Share of population under 6 with all parents working",
}
a22 = a[a.year == 2022].copy()
desc = pd.DataFrame({LABELS[c]: {"N": a22[c].notna().sum(), "mean": a22[c].mean(), "sd": a22[c].std(),
                                 "min": a22[c].min(), "max": a22[c].max()} for c in LABELS}).T
desc.to_csv(os.path.join(OUT, "table_2022_analysis_sample.csv"), float_format="%.4f")

# ------------------------------------------------------------------ pre-analysis 3-4: scatters and regressions
specs = {"(a) wage only": "price ~ wage_k", "(b) rent only": "price ~ rent_100",
         "(c) wage + rent": "price ~ wage_k + rent_100"}
fits = {k: smf.ols(f, a22).fit() for k, f in specs.items()}
reg_table = {k: {"params": m.params.to_dict(), "se": m.bse.to_dict(), "t": m.tvalues.to_dict(),
                 "p": m.pvalues.to_dict(), "r2": m.rsquared, "n": int(m.nobs)} for k, m in fits.items()}
corr_wage_rent = a22[["wage_k", "rent_100"]].corr().iloc[0, 1]
aux = smf.ols("rent_100 ~ wage_k", a22).fit()               # for the omitted-variable explanation

fig, axes = plt.subplots(1, 2, figsize=(10.5, 4.2), sharey=True)
for ax, xvar, key, color, xlab in [
        (axes[0], "wage_k", "(a) wage only", BLUE, "Childcare-worker mean annual wage ($1,000s), 2022"),
        (axes[1], "rent_100", "(b) rent only", ORANGE, "Median gross rent ($100s per month), 2022")]:
    m = fits[key]
    ax.scatter(a22[xvar], a22.price, s=12, color=color, alpha=0.45, lw=0)
    xs = np.linspace(a22[xvar].min(), a22[xvar].max(), 50)
    ax.plot(xs, m.params.Intercept + m.params[xvar] * xs, color=INK, lw=2)
    ax.set_xlabel(xlab)
    ax.grid(color=GRID, lw=0.8)
    ax.set_axisbelow(True)
    ax.text(0.03, 0.97, f"slope = ${m.params[xvar]:.2f}/week per unit\nR² = {m.rsquared:.2f},  N = {int(m.nobs)}",
            transform=ax.transAxes, va="top", fontsize=9, color=INK,
            bbox=dict(boxstyle="round,pad=0.35", facecolor="white", edgecolor=GRID))
axes[0].set_ylabel("Median weekly price, center-based\npreschool (36-54 mo), 2022 $")
fig.suptitle("Preschool prices vs. labor and rent costs, metro counties, 2022 (lines: OLS fit)", x=0.01,
             ha="left", color=INK, fontsize=11)
fig.tight_layout()
fig.savefig(os.path.join(OUT, "fig_price_vs_costs.png"), dpi=200)
plt.close(fig)

# ------------------------------------------------------------------ final 1-2: yearly cost model and premiums
yearly, parts = {}, []
for yr, g in a.groupby("year"):
    m = smf.ols("price ~ wage_k + rent_100", g).fit()
    yearly[int(yr)] = {"a": m.params.Intercept, "b_wage": m.params.wage_k, "c_rent": m.params.rent_100,
                       "se_wage": m.bse.wage_k, "se_rent": m.bse.rent_100, "r2": m.rsquared, "n": int(m.nobs),
                       "resid_sd": float(np.sqrt(m.scale))}
    parts.append(g.assign(predicted=m.fittedvalues, premium=m.resid,
                          premium_pct=100 * m.resid / m.fittedvalues))
P = pd.concat(parts)
prem = P.pivot(index="county_fips", columns="year", values="premium")
x = P[P.year == 2022].set_index("county_fips").copy()
x["rank_all"] = x.premium.rank(ascending=False).astype(int)

# screens
x["big_market"] = x.kids_under6_allpar_lf >= MIN_KIDS_NEED_CARE
pers = prem.reindex(x.index)[PERSIST_YEARS]
x["years_positive_2019_22"] = (pers > 0).sum(axis=1)
x["years_observed_2019_22"] = pers.notna().sum(axis=1)
# persistent = positive premium in every year it is observed (2019-2022), observed in at least 3 of the 4 years.
# (Some states have no NDCP price in a year, e.g. VA/CA/NC/PA in 2021; missing data should not count as failure.)
x["persistent"] = (x.years_observed_2019_22 >= 3) & (x.years_positive_2019_22 == x.years_observed_2019_22)
x["avg_premium_2019_22"] = pers.mean(axis=1)
x["premium_2019"] = prem.reindex(x.index)[2019]
x["premium_2015"] = prem.reindex(x.index)[2015]
x["eligible"] = x.big_market & x.persistent
# price granularity: how many other metro counties in the same state report exactly the same 2022 price
# (several states' surveys publish regional rates, e.g. WI has 4 distinct prices across 26 metro counties)
x["n_sharing_price"] = x.groupby(["state", "price"]).price.transform("size") - 1
x["county_specific_price"] = x.n_sharing_price <= 2
# price-trend check: NDCP interpolates linearly between state surveys; flag counties whose 2018-2022 nominal price
# growth is above the 99th percentile of metro counties (an extreme trend, possibly an extrapolation artifact)
nom = d.pivot(index="county_fips", columns="year", values="MCPRESCHOOL")
x["growth_2018_22_pct"] = (100 * (nom[2022] / nom[2018] - 1)).reindex(x.index)
GROWTH_P99 = float(x.growth_2018_22_pct.quantile(0.99))
x["extreme_growth"] = x.growth_2018_22_pct > GROWTH_P99
x["confidence"] = np.where(x.county_specific_price & ~x.extreme_growth, "High",
                           np.where(~x.county_specific_price, "Verify: regional price", "Verify: extreme price trend"))
elig = x[x.eligible].sort_values("premium", ascending=False)
top10 = elig.head(10).copy()
top10["rank"] = range(1, 11)
next10 = elig.iloc[10:20]
elig_specific = elig[elig.county_specific_price].copy()
top10_specific = elig_specific.head(10)
in_specific = top10.index.isin(top10_specific.index)
cols = ["rank", "county_name", "state", "area_title", "price", "predicted", "premium", "premium_pct",
        "premium_2019", "avg_premium_2019_22", "wage_childcare", "median_gross_rent", "kids_under6_allpar_lf",
        "per_capita_income", "female_college_share", "rank_all", "n_sharing_price", "growth_2018_22_pct", "confidence"]
top10[cols].to_csv(os.path.join(OUT, "table_top10.csv"), float_format="%.2f")
next10[[c for c in cols if c != "rank"]].to_csv(os.path.join(OUT, "table_next10.csv"), float_format="%.2f")
unscreened = x.sort_values("premium", ascending=False).head(15)
unscreened[["county_name", "state", "price", "premium", "kids_under6_allpar_lf", "years_positive_2019_22",
            "years_observed_2019_22", "big_market", "persistent"]].to_csv(os.path.join(OUT, "table_unscreened_top15.csv"), float_format="%.2f")
screen_counts = {"counties_2022": int(len(x)), "big_market": int(x.big_market.sum()),
                 "persistent": int(x.persistent.sum()), "eligible": int(x.eligible.sum())}

# ------------------------------------------------------------------ reliability checks
bal = prem.dropna()
corr_with_2022 = bal.corr()[2022].to_dict()
dec = lambda s: s.rank(ascending=False) <= len(s) * 0.10
top_dec_22 = dec(bal[2022])
persistence_top_decile = {int(y): float(dec(bal[y])[top_dec_22].mean()) for y in bal.columns if y != 2022}
x["state_mean_premium"] = x.groupby("state").premium.transform("mean")
state_share_var = float(x.state_mean_premium.var() / x.premium.var())
log_m = smf.ols("np.log(price) ~ np.log(wage_k) + np.log(rent_100)", x).fit()
spearman_log = float(stats.spearmanr(x.premium, log_m.resid).correlation)
x["rank_log"] = pd.Series(log_m.resid, index=x.index).rank(ascending=False)
top10_rank_log = x.loc[top10.index, "rank_log"].astype(int).to_dict()
shared_price = float(x.groupby("state").price.transform(lambda s: s.duplicated(keep=False)).mean())
bp = __import__("statsmodels.stats.diagnostic", fromlist=["het_breuschpagan"]).het_breuschpagan(
    fits["(c) wage + rent"].resid, fits["(c) wage + rent"].model.exog)
# out-of-time check: does the 2019 premium predict the 2022 premium?
oot = smf.ols("p22 ~ p19", pd.DataFrame({"p22": bal[2022], "p19": bal[2019]})).fit()

# ------------------------------------------------------------------ market characteristics
x["log_pop"] = np.log(x.pop_total)
x["inc_k"] = x.per_capita_income_real2022 / 1000
char = smf.ols("premium ~ inc_k + female_college_share + female_ftyr_share + under6_careneed_share + log_pop",
               x).fit()
char_cols = {"price": "Preschool price, $/week", "predicted": "Cost-predicted price, $/week",
             "premium": "Premium, $/week", "wage_childcare": "Childcare wage, $/yr",
             "median_gross_rent": "Median gross rent, $/month", "per_capita_income": "Per-capita income, $",
             "female_college_share": "Women 25+ with bachelor's+", "female_ftyr_share": "Women full-time year-round",
             "kids_under6_allpar_lf": "Children under 6, all parents working",
             "under6_careneed_share": "Share of pop. under 6 needing care", "pop_total": "Population"}
profile = pd.DataFrame({"Top 10": top10[list(char_cols)].mean(), "Eligible (screened)": elig[list(char_cols)].mean(),
                        "All metro counties": x[list(char_cols)].mean()}).rename(index=char_cols)
profile.to_csv(os.path.join(OUT, "table_market_profile.csv"), float_format="%.4f")

# ------------------------------------------------------------------ figures
# (1) actual vs predicted, top 10 highlighted
fig, ax = plt.subplots(figsize=(7.8, 5.6))
ax.scatter(x.predicted, x.price, s=12, color=INK2, alpha=0.25, lw=0, label="All metro counties, 2022")
ax.scatter(elig.predicted, elig.price, s=16, color=BLUE, alpha=0.5, lw=0, label="Pass both screens")
ax.scatter(top10.predicted, top10.price, s=60, color=RED, edgecolor="white", lw=1.5, zorder=3, label="Top 10")
lim = [x.predicted.min() - 10, x.price.max() + 15]
ax.plot(lim, lim, color=INK, lw=1.2, ls="--")
ax.text(lim[1] - 5, lim[1] - 40, "price = cost prediction", ha="right", fontsize=8.5, color=INK2)
offsets = {}
for _, r in top10.iterrows():
    k = int(r["rank"])
    dx, dy = (7, 4) if k not in (5, 7) else ((-14, -12) if k == 5 else (2, -14))
    ax.annotate(str(k), (r.predicted, r.price), xytext=(dx, dy), textcoords="offset points", fontsize=8.5,
                color=INK, fontweight="bold")
key = "\n".join(f"{int(r['rank'])}. {r.county_name.split(',')[0].replace(' County', '').replace(' city', '')}, {r.state}"
                for _, r in top10.iterrows())
ax.text(0.02, 0.98, "Top 10\n" + key, transform=ax.transAxes, va="top", fontsize=8, color=INK, linespacing=1.35,
        bbox=dict(boxstyle="round,pad=0.4", facecolor="white", edgecolor=GRID))
ax.set_xlabel("Cost-predicted weekly price (from childcare wage and rent), 2022 $")
ax.set_ylabel("Actual median weekly preschool price, 2022 $")
ax.set_title("Premium = how far a county's price sits above its cost prediction", loc="left", fontsize=11, color=INK)
ax.grid(color=GRID, lw=0.8)
ax.set_axisbelow(True)
ax.legend(loc="lower right", frameon=False, fontsize=8.5)
fig.tight_layout()
fig.savefig(os.path.join(OUT, "fig_actual_vs_predicted.png"), dpi=200)
plt.close(fig)

# (2) top-10 premium bars
fig, ax = plt.subplots(figsize=(7.8, 4.4))
lab = [f"{int(r['rank'])}. {r.county_name.replace(' County', '').replace(' city', ' (city)')}" for _, r in top10.iterrows()]
yy = np.arange(len(top10))[::-1]
ax.barh(yy, top10.premium, color=BLUE, height=0.62)
ax.scatter(top10.premium_2019, yy, color=ORANGE, s=34, zorder=3, edgecolor="white", lw=1, label="2019 premium")
for yv, (_, r) in zip(yy, top10.iterrows()):
    ax.text(max(r.premium, r.premium_2019 if pd.notna(r.premium_2019) else 0) + 5, yv,
            f"+${r.premium:.0f}/wk  ({r.premium_pct:+.0f}%)", va="center", fontsize=8.5, color=INK)
ax.set_yticks(yy)
ax.set_yticklabels(lab, fontsize=9)
ax.set_xlabel("Premium over cost-predicted price, 2022 $ per week (bar = 2022, dot = 2019)")
ax.set_xlim(0, top10.premium.max() * 1.35)
ax.grid(axis="x", color=GRID, lw=0.8)
ax.set_axisbelow(True)
ax.set_title("Top 10 recommended counties: preschool price premium over cost", loc="left", fontsize=11, color=INK)
ax.legend(loc="lower right", frameon=False, fontsize=8.5)
fig.tight_layout()
fig.savefig(os.path.join(OUT, "fig_top10_premium.png"), dpi=200)
plt.close(fig)

# (3) stability: 2019 vs 2022 premium + correlation by year
fig, axes = plt.subplots(1, 2, figsize=(10.5, 4.2))
ax = axes[0]
ax.scatter(bal[2019], bal[2022], s=10, color=INK2, alpha=0.3, lw=0)
t_in = top10.index.intersection(bal.index)
ax.scatter(bal.loc[t_in, 2019], bal.loc[t_in, 2022], s=40, color=RED, edgecolor="white", lw=1, zorder=3,
           label="Top-10 counties observed every year")
xs = np.linspace(bal[2019].min(), bal[2019].max(), 20)
ax.plot(xs, oot.params.Intercept + oot.params.p19 * xs, color=INK, lw=1.6)
ax.axhline(0, color=GRID, lw=1)
ax.axvline(0, color=GRID, lw=1)
ax.set_xlabel("Premium in 2019, 2022 $/week")
ax.set_ylabel("Premium in 2022, 2022 $/week")
ax.set_title(f"2019 premium predicts 2022 premium (r = {bal[[2019, 2022]].corr().iloc[0, 1]:.2f})", loc="left",
             fontsize=10.5, color=INK)
ax.legend(loc="upper left", frameon=False, fontsize=8.5)
ax.grid(color=GRID, lw=0.6)
ax.set_axisbelow(True)
ax = axes[1]
yrs = [y for y in sorted(corr_with_2022) if y != 2022]
ax.plot(yrs, [corr_with_2022[y] for y in yrs], color=BLUE, lw=2, marker="o", ms=5, markeredgecolor="white",
        label="Correlation with 2022 premium")
ax.plot(yrs, [persistence_top_decile[y] for y in yrs], color=ORANGE, lw=2, marker="o", ms=5,
        markeredgecolor="white", label="Share of 2022 top-decile counties\nalso top decile that year")
ax.set_ylim(0, 1.05)
ax.set_xticks(yrs)
ax.set_title(f"Premiums fade slowly over time ({len(bal)} counties, all years)", loc="left", fontsize=10.5, color=INK)
ax.legend(loc="lower right", frameon=False, fontsize=8.5)
ax.grid(axis="y", color=GRID, lw=0.6)
ax.set_axisbelow(True)
fig.tight_layout()
fig.savefig(os.path.join(OUT, "fig_premium_stability.png"), dpi=200)
plt.close(fig)

# (4) residual diagnostics
m = fits["(c) wage + rent"]
fig, ax = plt.subplots(figsize=(7.5, 3.8))
ax.scatter(m.fittedvalues, m.resid, s=10, color=BLUE, alpha=0.4, lw=0)
ax.axhline(0, color=INK, lw=1.2)
ax.set_xlabel("Cost-predicted weekly price, 2022 $")
ax.set_ylabel("Residual (premium), $/week")
ax.set_title("Residuals vs. fitted values, 2022 cost model (wage + rent)", loc="left", fontsize=11, color=INK)
ax.grid(color=GRID, lw=0.6)
ax.set_axisbelow(True)
fig.tight_layout()
fig.savefig(os.path.join(OUT, "fig_residuals.png"), dpi=200)
plt.close(fig)

top10_specific[["county_name", "state", "premium", "n_sharing_price", "kids_under6_allpar_lf"]].to_csv(
    os.path.join(OUT, "table_top10_county_specific_prices.csv"), float_format="%.2f")
granularity = (x.groupby("state").agg(metro_counties=("price", "size"), distinct_prices=("price", "nunique"))
               .sort_values("metro_counties", ascending=False))
results = {
    "sample_n_by_year": sample_n, "dropped_2022": dropped_2022, "descriptives_2022": desc.to_dict(orient="index"),
    "regressions_2022": reg_table, "corr_wage_rent_2022": corr_wage_rent,
    "aux_rent_on_wage": {"slope": aux.params.wage_k, "r2": aux.rsquared},
    "yearly_cost_model": yearly, "screens": {"min_kids_need_care": MIN_KIDS_NEED_CARE, "persist_years": PERSIST_YEARS,
                                             **screen_counts},
    "top10": top10[cols].reset_index().to_dict(orient="records"),
    "next10": next10[[c for c in cols if c != "rank"]].reset_index().to_dict(orient="records"),
    "unscreened_top15": unscreened[["county_name", "state", "price", "premium", "kids_under6_allpar_lf",
                                    "years_positive_2019_22"]].reset_index().to_dict(orient="records"),
    "reliability": {"corr_with_2022": corr_with_2022, "persistence_top_decile": persistence_top_decile,
                    "balanced_n": int(len(bal)), "state_share_of_premium_variance": state_share_var,
                    "shared_exact_price_within_state": shared_price, "spearman_level_vs_log": spearman_log,
                    "log_model_r2": log_m.rsquared, "top10_rank_in_log_model": top10_rank_log,
                    "breusch_pagan_p": float(bp[1]), "oot_slope_2019_to_2022": oot.params.p19,
                    "oot_r2": oot.rsquared},
    "characteristics_regression": {"params": char.params.to_dict(), "t": char.tvalues.to_dict(), "r2": char.rsquared,
                                   "n": int(char.nobs)},
    "market_profile": profile.to_dict(orient="index"),
    "top10_county_specific_prices": top10_specific[["county_name", "state", "premium", "n_sharing_price"]]
        .reset_index().to_dict(orient="records"),
    "top10_also_in_specific_list": dict(zip(top10.index, in_specific.tolist())),
    "price_granularity_by_state": granularity.to_dict(orient="index"),
    "growth_2018_22": {"median": float(x.growth_2018_22_pct.median()), "p99": GROWTH_P99},
    "high_confidence_list": elig[(elig.county_specific_price) & (elig.growth_2018_22_pct <= GROWTH_P99)]
        .head(10)[["county_name", "state", "premium"]].reset_index().to_dict(orient="records"),
}
with open(os.path.join(OUT, "results.json"), "w") as f:
    json.dump(results, f, indent=2, default=float)

pd.set_option("display.width", 250)
pd.set_option("display.max_colwidth", 45)
print("sample", sample_n, dropped_2022)
for k, mm in fits.items():
    print(k, {n: round(v, 3) for n, v in mm.params.items()}, {n: round(v, 1) for n, v in mm.tvalues.items()},
          "R2 %.3f" % mm.rsquared)
print("corr wage-rent %.2f; aux slope %.2f" % (corr_wage_rent, aux.params.wage_k))
print("screens", screen_counts)
print(top10[cols].round(1).to_string())
print(next10[["county_name", "state", "premium", "kids_under6_allpar_lf"]].round(1).to_string())
print(unscreened[["county_name", "state", "premium", "kids_under6_allpar_lf", "years_positive_2019_22", "years_observed_2019_22"]].round(1).to_string())
print(json.dumps(results["reliability"], indent=1, default=float))
print(char.params.round(2).to_dict(), char.tvalues.round(1).to_dict(), "R2 %.3f" % char.rsquared)
print(profile.round(3).to_string())
print(top10[["county_name", "n_sharing_price", "growth_2018_22_pct", "confidence"]].round(1).to_string())
print("growth p99 %.1f" % GROWTH_P99)
hc = elig[(elig.county_specific_price) & (elig.growth_2018_22_pct <= GROWTH_P99)].head(10)
print(hc[["county_name", "state", "premium", "kids_under6_allpar_lf", "growth_2018_22_pct"]].round(1).to_string())
print("county-specific-price top 10:"); print(top10_specific[["county_name", "state", "premium", "n_sharing_price"]].round(1).to_string())
