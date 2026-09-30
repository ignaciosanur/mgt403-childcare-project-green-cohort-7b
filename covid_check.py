"""
Footnote check for PS4 Q3: did stricter state COVID restrictions go with larger childcare price changes?

Source: Oxford COVID-19 Government Response Tracker (OxCGRT), subnational compact file, US state totals.
  https://github.com/OxCGRT/covid-policy-dataset  (data/OxCGRT_compact_subnational_v1.csv)
Writes covid_state_restrictions_oxcgrt.csv (one row per state, Mar 2020 - Dec 2021) and prints correlations with
state-average real price changes in the balanced panel of metro counties (from ps4_analysis.py output).

Run after ps4_analysis.py:  python3 covid_check.py
"""
import os
import urllib.request

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
URL = "https://raw.githubusercontent.com/OxCGRT/covid-policy-dataset/main/data/OxCGRT_compact_subnational_v1.csv"
RAW = os.path.join(HERE, "oxcgrt_raw", "OxCGRT_compact_subnational_v1.csv")

if not os.path.exists(RAW):
    os.makedirs(os.path.dirname(RAW), exist_ok=True)
    urllib.request.urlretrieve(URL, RAW)

o = pd.read_csv(RAW, low_memory=False)
o = o[(o.CountryCode == "USA") & (o.Jurisdiction == "STATE_TOTAL")].copy()
o["state"] = o.RegionCode.str[3:]
o["date"] = pd.to_datetime(o.Date.astype(str))
w = o[(o.date >= "2020-03-01") & (o.date <= "2021-12-31")]

# OxCGRT ordinal codes: >= 2 means a *required* measure (not just recommended)
g = w.groupby("state").agg(
    stay_home_days=("C6M_Stay.at.home.requirements", lambda s: int((s >= 2).sum())),
    workplace_close_days=("C2M_Workplace.closing", lambda s: int((s >= 2).sum())),
    school_close_days=("C1M_School.closing", lambda s: int((s >= 2).sum())),
)
g["stringency_mar_dec_2020"] = w[w.date <= "2020-12-31"].groupby("state").StringencyIndex_Average.mean()
g["stringency_2021"] = w[w.date >= "2021-01-01"].groupby("state").StringencyIndex_Average.mean()
g.round(1).to_csv(os.path.join(HERE, "covid_state_restrictions_oxcgrt.csv"))

# state-average real price change within the balanced panel (same counties every year)
m = pd.read_csv(os.path.join(HERE, "ps4_output", "ndcp_metro_2015_2022.csv"), dtype={"COUNTY_FIPS_CODE": str})
real = ["MCINFANT_real2022", "MCTODDLER_real2022", "MCPRESCHOOL_real2022"]
have = m.dropna(subset=real).groupby("COUNTY_FIPS_CODE").year.nunique()
bal = m[m.COUNTY_FIPS_CODE.isin(have[have == 8].index)]
s = bal.groupby(["STATE_ABBREVIATION", "year"])[real].mean().unstack("year")
res = pd.DataFrame(index=s.index)
for c in real:
    k = c.split("_")[0]
    res[k + "_chg_2019_2022"] = 100 * (s[(c, 2022)] / s[(c, 2019)] - 1)
    res[k + "_chg_2020_2021"] = 100 * (s[(c, 2021)] / s[(c, 2020)] - 1)
res = res.join(g, how="inner")

print(f"{len(res)} states with balanced-panel counties")
print(g.describe().round(1))
for x in ["stringency_mar_dec_2020", "stringency_2021", "stay_home_days", "school_close_days"]:
    print(x, {c: round(res[[x, c]].corr().iloc[0, 1], 2)
              for c in ["MCPRESCHOOL_chg_2019_2022", "MCPRESCHOOL_chg_2020_2021", "MCINFANT_chg_2019_2022"]})
res["strict_half"] = res.stringency_mar_dec_2020 > res.stringency_mar_dec_2020.median()
print(res.groupby("strict_half")[["MCPRESCHOOL_chg_2019_2022", "MCINFANT_chg_2019_2022",
                                  "MCPRESCHOOL_chg_2020_2021"]].mean().round(2))
