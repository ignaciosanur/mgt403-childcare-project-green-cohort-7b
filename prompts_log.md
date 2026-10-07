# Prompt log — MGT 403 childcare data project

Team: Ignacio Sanchez Urdaneta, Beck Jamilov, Claudia Palacios Surco, Gary Chen.
AI tools: Claude (Cowork session, then Claude Code). Prompts are listed as typed, with a short note on what the AI did in response.

## Session 1 — Claude Cowork, 2026-09-30 (data preparation)
Produced `trim_ndcp.py`, `make_slim.py`, `extract_oews.py`, `pull_acs.py` and the handoff notes in `CLAUDE.md`
(the prompts from that session were not exported; its output is summarized in `CLAUDE.md`, "Work done so far").

## Session 2 — Claude Code, 2026-09-30 (Problem Set 4, Question 2)

**Prompt 1:**
> hi we are working on the group part section of homework 4, which is cleaning data for the last assessment
> (team work). Do you have anything you need to start working on it? What things have I done already in terms
> of getting you the data vs. what do I still need to do?

AI: read `HW_4.pdf` and the project assignment PDF, listed the data files already in the folder, and identified
what was missing: team names, verified CPI values, and the output format.

**Prompt 2:**
> team members are Ignacio Sanchez Urdaneta, Beck Jamilov, Claudia Palacios Surco, and Gary Chen
> yes please check for inflation
> good with what you said on output format

AI actions:
1. Pulled CPI-U series CUUR0000SA0 for 2015–2022 from the BLS Public Data API v1 and averaged the 12 months of
   each year. All 8 annual averages matched the values in `CLAUDE.md`, which are saved in `cpi_u_annual.csv`.
2. Merged NDCP to the crosswalk on county × year (all rows matched) and kept `oews_area` starting with `00`.
   Checked the 2 crosswalk metro counties that are absent from NDCP; they are legacy FIPS codes (12025, 51515)
   whose current codes are present.
3. Read the NDCP Technical Report to interpret the `_flag` columns. They mark age-band aggregation, not
   imputation, so all non-missing values were kept.
4. Wrote and ran `ps4_analysis.py`, which produces the histograms, summary table with 95% CIs, real-price
   trends, a balanced-panel check (after finding that state coverage changes by year, notably in 2021), and the
   voucher z-tests for 2022 and 2015 with a scipy t-test check and a metro-area-level robustness check.
5. Wrote `PS4_Q2_writeup.md` and rendered it to `PS4_Q2_writeup.pdf`.

**Prompt 3:**
> were you able to download the data from this step with the API that I gave you in the folder?
> Childcare demand – U.S. Census American Community Survey (ACS), 5-year estimates

AI: ran `python3 pull_acs.py <key>` (the Census API key is kept out of this log). It returned 3,220–3,222 counties
per year for 2015–2022 (25,764 rows) and wrote `acs_county_2015_2022.csv`. Checks: FIPS are 5-character text with
no duplicates, all shares lie in [0, 1], and blanks are few (38 missing rents, 1 county-year missing most
variables). Merged to metro crosswalk counties, only CT 2022 fails to match because the ACS uses planning regions
09110–09190, plus the 2 legacy FIPS codes.

**Prompts 4–6 (data coverage):**
> Since this is a "blue sky" type of project, you can probably kill the entries that do not match UNLESS they are
> huge population wise. What is the impact? ...
> why is there no data for these state/populations? is it just in the underlying data
> ok so that info is very interesting. Then let's have those reasons saved ... For connectic, just kill the data
> that doesn't work since it's very small UNLESS it's all outliers that really change the population

AI: measured the population of every unmatched or missing group (CT 2022 = 1.2% of metro population; no-price
metro counties = 9.8%), confirmed the blanks are in the original NDCP file, pulled the per-state reasons from the
NDCP Technical Report, checked whether CT counties are influential (no: means move by under \$1.02), and recorded
every decision in `data_decisions.md`.

**Prompts 7–10 (Q2 review):** asked how the age groups are defined (answer: NDCP standard groups, Tech Report
App. C) and to label every table and chart with the age range in months; asked whether counties should be
population-weighted (decision: unweighted main results, since the county is the unit of choice and the course CI
formula assumes a simple mean); asked to add a brief child-weighted comparison to Q2. Implemented in
`ps4_analysis.py` (`weighted_means_2022_kids_under6` in `results.json`) and the write-up.

**Prompt 11:** asked whether the data are a sample or a population (to choose the right SD and CI tools), and to
redo Q2 with age-range labels plus the median. AI: compared sample and population SD (0.05% difference), checked
the finite-population correction (not applied, because missing counties drop out by whole state), added a
"Sample or population?" note to Methods, added median lines and values to the histograms, and moved Median next
to Mean in the Q2 table.

**Prompts 12–15 (Q3):** asked for the Q3 chart to be shown (then for a line-style legend), a footnote on how Q2
changes with CPI-U prices, the team's interpretation (a COVID dip in 2021, a rebound in 2022, a widening infant
gap, prices expected to keep rising) with % changes for each group, and a check of state COVID restrictions. AI:
added the legend, the note and footnote, and a period-change table. It flagged that the 2021 dip, the 2022 rebound
and the widening infant gap come from changes in which states report; the balanced panel shows nominal prices up
about 3–4% a year and real declines driven by inflation. The discussion was rewritten accordingly (team framing kept
where the data support it). The COVID check (`covid_check.py`, OxCGRT data) found no relationship between restriction
stringency and price changes across 34 states (footnote 3).

**Prompt 16 (Q4):** stated that the claim is two-sided ("no difference"), asked for clean LaTeX formulas and a
one-sample *t*-statistic, and pasted a list of elements to compute separately (weekly and monthly μ0, X̄, s, n, SE).
AI: rewrote Q4 around the one-sample *t* with LaTeX for every element, a weekly/monthly equivalence table, the
p-value formula from the *t* CDF (df = n−1), and the scipy `ttest_1samp` check. The *z* result is kept as a
cross-check. Added t critical values and monthly figures to `ps4_analysis.py`.

**Prompts 17–19 (Q4d and final document):** asked for 4(d) results with charts for a live team discussion; asked
whether H0 is about the median rather than the mean; confirmed keeping the *t*-test on the mean and adding the
median nuance; asked to treat the metro sample as a hard rule, add the state-clustering caveat as a footnote,
confirm the source of the weighting data, and deliver the final write-up as a Word document. AI: made two voucher
charts, added a sign test (median across counties vs. voucher: 2022 p = 0.53, fail to reject; 2015 rejects),
confirmed the area-level check uses exactly the metro-sample counties, added state-clustered SEs (2022 t = 1.48,
p = 0.15), and built `PS4_Q2_writeup.docx` with pandoc (native Word equations and footnotes), checked by exporting
it to PDF from Microsoft Word.

**Prompts 20–22 (formatting and GitHub):** asked for dark-grey, smaller footnotes, a more descriptive H0 in Q4(a),
and a separate documentation file, with the data-handling decisions kept in the write-up. Then asked for a public
GitHub repo (`mgt403-childcare-project-green-cohort-7b`) holding only clean, essential, replicable files, with no
personal data, and teammates beckjamilov, claups1 and garychen836 as collaborators. AI: restyled the footnotes,
expanded the hypotheses, wrote `README.md`, `.gitignore` and `requirements.txt`, and audited all files. It kept
out `CLAUDE.md` (API key), the raw downloads and the course PDFs, used GitHub's no-reply commit email instead of
the Yale address, and replaced the Word-stamped PDF author with the team name. It tested replication from a fresh
clone (`results.json` and all figures byte-identical; `covid_check.py` reproduces), pushed, and invited the
teammates.

## Session 3 — Claude Code, 2026-10-07 (Problem Set 5, Question 3)

**Prompt 23:** clarified that the team is doing PS5 Question 3 (Cost Drivers in Childcare), building on the PS4 work.
AI: ran `extract_oews.py` for 2015–2022 and checked that older-year headers parse (all codes 7 characters,
plausible wage ranges). Wrote `ps5_analysis.py`: a year × county metro panel with OEWS wages and ACS covariates
(0.4–1.6% of metro counties missing a wage each year, in line with the expected ~1%), a 2022 descriptive table, real
wage and rent trends, the 2019-vs-2022 real wage test (Welch, with paired and metro-area checks), and the 2022
regression of wages on female college share.

**Prompt 24:** asked how Welch differs from ANOVA, whether Welch is non-parametric, and whether a residual test ruled
out ANOVA; decided the county stays the unit of analysis even though OEWS wages are per metro area. AI: showed that
with two groups ANOVA F = pooled t² (8.45 = 2.906², same p = 0.0037), explained that Welch is parametric (Mann–Whitney
is the non-parametric analogue; p = 0.008), and said no residual test drove the choice: Welch was chosen because the
SDs differ (Bartlett p = 0.0002; Levene p = 0.12). Recorded the county-unit decision (`data_decisions.md` §8–9) and
dropped metro-area tests from the write-up.

**Prompt 25:** asked to state why ANOVA was not used (different spreads) and to footnote that ANOVA gives the same
conclusion. AI: wrote `PS5_Q3_writeup.md` (built to `.docx`/`.pdf` with `build_docx.py`, now usable for any write-up),
with the Welch-vs-ANOVA sentence in step 6 and the ANOVA result in a footnote.

**Prompt 26 (team review by Claudia):** section 2 said only the MSA_ and BOS_ files were read, but the 426 metro
areas in 2015–2017 only add up if the aggregate-MSA (aMSA_) files were read too; without them about 10% of counties
lose their wage. AI: confirmed that the code already reads aMSA (11 areas per year, 415 + 11 = 426, no duplicates;
114 metro counties = 9.2%), adopted Claudia's wording in section 2, added aMSA counts to the table, and updated
`extract_oews.py`'s docstring and `data_decisions.md`.

## How to reproduce
See `README.md` ("Reproducing Problem Set 4, Q2").
