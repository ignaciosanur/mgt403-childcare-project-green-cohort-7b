# MGT 403 — Childcare Data Project

Yale SOM, MGT 403 Probability Modeling & Statistics (Fall 2026).
Team: Ignacio Sanchez Urdaneta, Beck Jamilov, Claudia Palacios Surco, Gary Chen.

Scenario: a national for-profit childcare chain choosing counties for new center-based preschool locations.
A county is attractive when prices are high relative to costs (mainly labor and rent).

This repository is our documentation of how the work was done: code, the outputs it produces, the
data-handling decisions, and the full AI prompt history.

| Deliverable | Status | Main files |
|---|---|---|
| Problem Set 4, Q2: The Distribution of Childcare Prices | done | `PS4_Q2_writeup.docx` / `.pdf`, `ps4_analysis.py`, `ps4_output/` |
| Problem Set 5, Q3: Cost Drivers in Childcare | done | `PS5_Q3_writeup.docx` / `.pdf`, `ps5_analysis.py`, `ps5_output/` |
| Final project (slides + appendix) | not started | |

## How the work was done

All analysis is in Python, written with **Claude Code** (Anthropic) as the AI assistant. The team directed each
step, questioned the results live and made the judgment calls. Every prompt and what the AI did in response is
logged in [`prompts_log.md`](prompts_log.md). Data-handling decisions, and the reasoning behind them, are in
[`data_decisions.md`](data_decisions.md) and in the "Data-handling decisions" section of the write-up.

## Data sources

| Source | What we use | Where to get it | In this repo? |
|---|---|---|---|
| DOL National Database of Childcare Prices (NDCP), 2024 release | county median weekly center-based prices, 2015–2022 (`MCINFANT`, `MCTODDLER`, `MCPRESCHOOL`) | [dol.gov/agencies/wb/topics/featured-childcare](https://www.dol.gov/agencies/wb/topics/featured-childcare), file `NDCP2022.xlsx` | slim extract only (`NDCP2015_2022_center_median.csv`); raw file is 97 MB |
| County × year → OEWS area crosswalk | metro sample (`oews_area` starts with `00`) and the wage merge key | course Canvas (Files/Project) | yes (`county_oews_crosswalk.csv`) |
| BLS CPI-U, CUUR0000SA0, annual average | deflator to constant 2022 $ | BLS Public Data API | values hard-coded and in `cpi_u_annual.csv` |
| Census ACS 5-year, county | children under 6 (weights in Q2); PS5 covariates | Census API, needs a free key: [api.census.gov/data/key_signup.html](https://api.census.gov/data/key_signup.html) | yes (`acs_county_2015_2022.csv`, `acs_raw/`) |
| BLS OEWS, SOC 39-9011 childcare workers | area wages (PS5) | `https://www.bls.gov/oes/special-requests/oesmYYma.zip` (YY = 15…22) | 2022 extract only |
| Oxford COVID-19 Government Response Tracker | state restriction stringency (Q3 footnote) | [github.com/OxCGRT/covid-policy-dataset](https://github.com/OxCGRT/covid-policy-dataset) | summary only (`covid_state_restrictions_oxcgrt.csv`) |

## Reproducing Problem Set 4, Q2

```bash
pip install -r requirements.txt

# 1. NDCP: place NDCP2022.xlsx in this folder, then
python3 trim_ndcp.py          # keep 2015-2022, FIPS as 5-char text  -> NDCP2015_2022.csv/.xlsx
python3 make_slim.py          # IDs + center-based medians + flags   -> NDCP2015_2022_center_median.csv (+ .xlsx copy)

# 2. ACS (only needed for the child-weighted means in Q2)
python3 pull_acs.py YOUR_CENSUS_API_KEY   # -> acs_county_2015_2022.csv

# 3. Analysis: metro sample, CPI conversion, all tables, figures and tests
python3 ps4_analysis.py       # -> ps4_output/ (figures, tables, results.json)
python3 covid_check.py        # Q3 footnote: downloads OxCGRT, writes covid_state_restrictions_oxcgrt.csv

# 4. Write-up (needs pandoc; the PDF export uses Microsoft Word on macOS)
python3 build_docx.py         # PS4_Q2_writeup.md -> PS4_Q2_writeup.docx (+ .pdf)
```

## Reproducing Problem Set 5, Q3

```bash
# 1. ACS 5-year county data, 2015-2022 (committed; rerun only to re-pull)
python3 pull_acs.py YOUR_CENSUS_API_KEY        # -> acs_county_2015_2022.csv

# 2. BLS OEWS childcare-worker wages (committed extract; rerun needs the oesmYYma.zip files)
python3 extract_oews.py oesm15ma.zip oesm16ma.zip oesm17ma.zip oesm18ma.zip \
                        oesm19ma.zip oesm20ma.zip oesm21ma.zip oesm22ma.zip   # -> oews_39-9011_areas.csv

# 3. Merge, descriptives, real trends, 2019-vs-2022 wage test, regression (needs ps4_analysis.py run first
#    for cpi_u_annual.csv and the preschool-price context)
python3 ps5_analysis.py                        # -> ps5_output/

# 4. Write-up
python3 build_docx.py PS5_Q3_writeup.md        # -> PS5_Q3_writeup.docx (+ .pdf)
```

Steps 1–2 can be skipped: their outputs (`NDCP2015_2022_center_median.csv`, `acs_county_2015_2022.csv`) are
committed. `ps4_output/results.json` contains every number quoted in the write-up, so any figure can be traced
to the code that produced it.

## Files

| File | Purpose |
|---|---|
| `trim_ndcp.py`, `make_slim.py` | NDCP extraction (2015–2022, center-based medians) |
| `ps4_analysis.py` | PS4 Q2: metro merge, CPI-U conversion, Q2 statistics and CIs, Q3 trends and balanced panel, Q4 voucher *t*-test, sign test, state-clustered and metro-area robustness checks, all figures |
| `covid_check.py` | state COVID restrictions (OxCGRT) vs. price changes |
| `build_docx.py`, `reference_ps4.docx` | builds a Word write-up (native equations and footnotes) from a markdown file |
| `pull_acs.py` | Census ACS 5-year pull and derived shares (PS5) |
| `extract_oews.py` | BLS OEWS 39-9011 extraction for 2015–2022 and merge check (PS5) |
| `ps5_analysis.py` | PS5 Q3: year × county metro panel (wages + ACS), 2022 descriptives, real wage/rent trends, Welch test 2022 vs 2019 (ANOVA, paired, Mann–Whitney checks), wage-on-college regression, figures |
| `data_decisions.md` | every data-handling decision, sized in population terms, with reasons |
| `prompts_log.md` | prompt history |
| `ps4_output/` | figures, summary tables, cleaned metro panel `ndcp_metro_2015_2022.csv`, `results.json` |

## Key conventions

* Metro analysis sample = counties whose year-specific `oews_area` begins with `00`. This is applied as a hard
  rule in every analysis.
* FIPS codes are 5-character strings and OEWS areas 7-character strings; leading zeros are never dropped.
* Dollar values in constant 2022 $ use CPI-U annual averages: real = nominal × CPI₂₀₂₂ / CPI_year.
* The county is the unit of analysis everywhere, including for OEWS wages (published per metro area).
* Statistics are unweighted county averages; 95% CIs use mean ± 1.96·s/√n; the voucher test is a one-sample *t*;
  the 2019-vs-2022 wage test is a Welch two-sample *t*.
