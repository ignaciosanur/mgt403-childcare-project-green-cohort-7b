# Data-handling decisions — source for the final-project appendix

Team: Ignacio Sanchez Urdaneta, Beck Jamilov, Claudia Palacios Surco, Gary Chen.
Guiding rule (team decision, 2026-09-30): this is a "blue sky" site-selection exercise, so records that
do not merge cleanly are **dropped**, unless they are large in population or are influential outliers.
Each drop is sized below.

## 1. Metro analysis sample
- Metro = county-years whose year-specific `oews_area` in `county_oews_crosswalk.csv` begins with `00`.
  About 1,235 metro counties per year, with 288.1M people in 2022.
- All 25,763 NDCP county-year rows (2015–2022) match the crosswalk.
- Two crosswalk metro codes have no NDCP or ACS row: **12025** (old code for Miami-Dade, now 12086) and
  **51515** (Bedford city VA, merged into Bedford County 51019 in 2013). NDCP and ACS report these counties
  under their current codes, which do match, so **no population is lost**. The legacy rows are dropped.

## 2. Connecticut 2022 (ACS geography change) — DROPPED
- From 2022 the ACS 5-year reports Connecticut by 9 planning regions (FIPS 09110–09190) instead of 8 counties.
  NDCP and the crosswalk still use the old counties (09001–09015) in 2022, so 7 metro CT counties get no ACS
  covariates in 2022. CT merges normally for 2015–2021.
- Size: **3.42M people, 1.2% of the 2022 metro population.**
- Outlier check (2022 NDCP center-based preschool median): CT counties are expensive but not extreme. They rank
  between the 85th and 96th percentile of 1,013 metro counties; Fairfield is the highest at \$306/week (rank 42),
  followed by New Haven and Middlesex at \$285 (rank 65). Dropping them changes the 2022 mean prices by less than
  \$1.02 (infant −0.82, toddler −1.02, preschool −0.60) and the PS4 voucher z-statistic from 6.39 to 6.08. No
  conclusion changes.
- **Decision: drop CT county-years in 2022 from every analysis that needs ACS variables** (PS5, pre-analysis,
  final model). NDCP-only analyses (PS4) keep CT 2022, since they don't use ACS.
- Caveat for the talk: Fairfield County (Stamford/Greenwich) is a plausible high-price market that the 2022 model
  cannot score. It can still be discussed using 2015–2021.

## 3. Metro counties with no NDCP childcare price (source-data gaps, cannot be fixed)
In 2022, **222 metro counties with 28.3M people (9.8% of the metro population, 9.2% of children under 6)** have
no center-based price. We verified that the prices are blank in the original `NDCP2022.xlsx` in every price
column, so our cleaning did not cause this. NDCP prices come from state market-rate surveys (MRS), and the gaps
are states whose surveys could not be turned into county market prices. Reasons are from the NDCP Technical
Report (Women's Bureau/ICF, Sept 2024), Appendix A state notes and the "Alternative Price Methodology" section:

| State | Metro pop. with no 2022 price | Years without prices (2015–22) | Reason given in the NDCP Technical Report |
|---|---|---|---|
| Pennsylvania | 11.55M | 2021–2022 | "The 2020 reports provided statewide median rate but did not include anything by county or by 75th percentile. The 2022 report also did not include any usable data." Full county data exist for 2015–2020. |
| Indiana | 5.32M | all years | "Indiana's data could not be used because the state only provides reimbursement rates. Reimbursement rate data cannot be used to calculate market rate data." |
| Missouri | 4.64M | 2021–2022, and only 7–15 counties before | Missouri's MRS "only has data for 75th percentile" prices (no medians); response rates as low as 3.6%–45% in some years. |
| Puerto Rico | 3.14M | all years except 2021 | Added only in the 2019–2022 update; a price is recorded only for 2021. The territory's MRS groups municipalities into rate regions. |
| Arkansas | 1.91M | 2022 only | No specific reason stated; county data exist for 2015–2021 (68–75 counties). Most likely no usable 2022 survey. |
| New Mexico | 1.41M | all years | NM moved from an MRS to a cost-estimation model (federal waiver); "no price estimates for New Mexico, because price data were not available and no imputation methods were feasible." |
| Other (VT, IL, FL) | 0.30M | scattered | Isolated county gaps. |

Largest affected metro counties (2022): Philadelphia PA (1.59M), Allegheny/Pittsburgh PA (1.25M),
St. Louis County MO (1.00M), Marion/Indianapolis IN (0.97M), Montgomery PA (0.86M), Jackson/Kansas City MO
(0.72M), Bernalillo/Albuquerque NM (0.67M), Delaware PA (0.65M).

Implications:
- The 2022 top-10 cannot include PA, IN, MO, AR, NM or PR markets. State this as a limitation of the source,
  not a team choice.
- PA, MO and AR do have earlier years, so they can enter the "is the premium stable over time" analysis for
  2015–2020/21.
- Coverage also changes year to year (e.g. 2021 lacks CA, NC, PA, VA; NY enters in 2017; CO has prices only
  in 2015 and 2022). Trend comparisons therefore use a **balanced panel** (740 metro counties with all three
  prices in every year) alongside the full sample.

## 4. NDCP `_flag` columns
Values 1/2/3 are **not imputation markers**. They record how NDCP collapsed its detailed age bands into one
age-group price (1 = all bands had the same price, 2 = the mode, 3 = the highest of several modes; Technical
Report Appendix C, county data dictionary, p. 66). All non-missing prices are kept.

## 5. ACS pull (2015–2022, 5-year)
- 3,220–3,222 counties per year, 25,764 rows; FIPS are 5-character text with no duplicates; all derived shares
  lie in [0, 1].
- Median gross rent is missing for 38 county-years, only 3 of them metro: Cameron Parish LA 2021–2022
  (pop. 5,447) and Storey County NV 2015. Rio Arriba NM 2018 is missing most variables. **Dropped** from
  analyses needing those variables (negligible population).

## 6. Inflation
CPI-U, CUUR0000SA0, annual average (the mean of the 12 monthly values from the BLS API, checked 2026-09-30):
2015 237.017 · 2016 240.007 · 2017 245.120 · 2018 251.107 · 2019 255.657 · 2020 258.811 · 2021 270.970 ·
2022 292.655. Real 2022 \$ = nominal × CPI₂₀₂₂ / CPI_year.

## 7. OEWS wages (to be completed in PS5)
- 2022: 20 of 1,237 metro counties (1.6%) have no SOC 39-9011 wage because BLS publishes no row for 11 metro
  areas. This is within the roughly 1% the assignment expects. 2015–2021 not yet processed.

## 7b. OEWS aggregate-MSA files, 2015–2017 (thanks to Claudia's review)
- For 2015–2017 the OEWS zips include `aMSA_M20YY_dl.xlsx`. In those years the MSA file reports the 11 largest metro
  areas (New York, Los Angeles, Chicago, Dallas, Washington, Miami, Philadelphia, Boston, San Francisco, Detroit,
  Seattle) only by metropolitan division, while the crosswalk maps counties to the whole metro area. The aMSA file
  has the whole-area wage, so `extract_oews.py` reads it. These areas cover 114 metro counties (9.2%) per year; no
  area appears in both files.

## 8. Unit of analysis: the county (team decision, 2026-10-07)
- All analyses are run at the **county** level (year × county), because the deliverable is a ranked list of
  counties. This holds even for variables measured at a coarser level: the OEWS childcare wage is published per
  metro area, so every county in the same metro area gets the same wage.
- Consequence to keep in mind: counties in one metro area are not independent observations for the wage variable
  (2022: 1,215 counties share about 380 distinct area wages), so textbook standard errors are optimistic. The team
  chose not to switch to metro-area-level tests; where it matters it can be noted as a caveat.

## 9. PS5 step 6 test choice
- Main test: Welch two-sample *t* on real county wages, 2022 vs. 2019 (OEWS 2019 and 2022 estimates come from
  non-overlapping survey panels). With two groups, one-way ANOVA is identical to the pooled-variance *t*
  (F = t² = 8.45, p = 0.0037); Welch gives t = 2.90, p = 0.0037. Variance checks are mixed (Bartlett p = 0.0002,
  Levene p = 0.12), so Welch is the safe default and ANOVA gives the same answer. Mann–Whitney (non-parametric)
  also rejects (p = 0.008). Paired test on the same counties: t = 8.58.
