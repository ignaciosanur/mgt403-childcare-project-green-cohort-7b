---
title: "Final Project Presentation: Presenter Guide"
subtitle: "MGT 403 · Green Cohort Team 7B · 6 slides, 10-minute limit"
---

# Run of show

| Slide | Topic | Time | Speaker |
|---|---|---|---|
| 1 | Where should we open our next center-based preschools? | 1:15 | Speaker A |
| 2 | Top 10 counties and confidence tiers | 2:00 | Speaker A |
| 3 | Method and reliability | 2:00 | Speaker B |
| 4 | Market characteristics | 1:30 | Speaker C |
| 5 | Are premiums stable? | 1:30 | Speaker C |
| 6 | What we miss and next steps | 1:15 | Speaker D (then lead Q&A) |
| | **Total** | **9:30** (30-second buffer) | |

Speakers A–D are placeholders; assign them to team members. Each speaker gives one short hand-off line to
the next. The script below is the same text as the speaker notes in `Final_Project_Slides.pptx` (Presenter View shows
it on your screen). Read it once aloud with a timer; most groups run long on slides 2 and 3.

# Script

## Slide 1: Where should we open our next center-based preschools? (1:15, Speaker A)

* **SAY:** We were asked where a for-profit chain should open center-based preschools. We call a market attractive when families pay much more than the two main costs, childcare wages and rent, would predict.
* Our answer: start with four counties, Arlington, VA, Alexandria, VA, San Francisco, CA, Norfolk, MA. In each, the median preschool price is \$116 to \$201 a week above what local labor and rent costs predict. Six more counties look promising but need a local price check.
* We looked at all 998 metro counties with 2022 data; 155 passed our market-size and persistence screens.
* **HAND-OFF:** Here is the full top 10.

## Slide 2: Top 10 counties and confidence tiers (2:00, Speaker A)

* **SAY:** Each bar is a county's premium: its actual 2022 preschool price minus the price our cost model predicts.
* Example: Arlington charges about \$496 a week where wages and rent predict \$296, a premium of \$201.
* Our model's typical miss is \$37 a week, so these premiums are 2.7 to 5.4 times bigger than normal noise.
* Coral bars pass every data check. Amber bars are real in the data but rest on weaker price data: four use one regional survey price shared by many counties, and two show price jumps faster than 99% of counties (+77% and +59%, 2018-22).
* If the amber six fail a local check, the alternates on the right pass every check.
* **HAND-OFF:** How did we get these numbers? [Speaker B]
* **LIKELY Q:** Why not just pick the most expensive counties? A: Expensive places also cost more to run; we want price HIGH RELATIVE TO COST.

## Slide 3: Method and reliability (2:00, Speaker B)

* **SAY:** Four steps. (1) Across metro counties we regress the preschool price on childcare-worker wages and rent. Each \$1,000 of annual wages adds \$7.09 a week; each \$100 of monthly rent adds \$5.91. (2) The premium is the gap between actual and predicted price. (3) We keep markets with at least 5,000 young children whose parents all work, and premiums that were positive in every year we observe since 2019. (4) We rank and flag weaker price data.
* **RELIABILITY (bottom row):** the 2019 premium predicts the 2022 premium (slope 0.88); a log-price model gives the same ranking (0.98); the typical miss is \$37. Caveat in amber: 43% of premium differences are between states, partly because some states publish regional prices. But even comparing counties only within their own state, our four high-confidence picks stay in the top 8.
* **HAND-OFF:** What do these markets look like? [Speaker C]
* **LIKELY Q:** R² of 0.61 is low? A: The unexplained part IS the premium we rank on; a perfect fit would leave nothing to find.

## Slide 4: Market characteristics (1:30, Speaker C)

* **SAY:** We pick locations on four measured characteristics: the premium, the two costs that define it, and demand depth.
* Our top 10 are affluent and dual-earner: per-capita income about \$56k vs \$38k, and 49% of women hold a bachelor's degree vs 31%.
* Important nuance: demographics alone explain only 7% of premiums. So we rank on the measured premium, and use demographics only as a sanity check.
* **HAND-OFF:** Will these premiums last?

## Slide 5: Are premiums stable? (1:30, Speaker C)

* **SAY:** Yes. We rebuilt the cost model every year. A dollar of premium in 2019 was still worth about 88 cents in 2022, right through the pandemic.
* The lines show the link fading slowly: of today's top-10% counties, 69% were already top 10% in 2019.
* The lasting part of a premium (about \$31 a week) is twice the year-to-year noise (\$15). Premiums are a market feature, not luck.
* Caveat: states survey prices every 2-3 years and the database fills in between, so neighbouring years look more alike than they are; we therefore lean on the 2019 vs 2022 comparison.
* **HAND-OFF:** What would we still check before investing? [Speaker D]

## Slide 6: What we miss and next steps (1:15, Speaker D (then lead Q&A))

* **SAY:** Our model sees prices and two costs, not supply. Five gaps matter: competition and licensed capacity; labor cost (our wage data cover childcare workers, not preschool teachers, and ratio rules differ by state); commercial rents rather than residential; six states with no 2022 prices, including Philadelphia and St. Louis; and survey-based posted prices.
* **NEXT STEPS:** site and competitor scan in Arlington, VA, Alexandria, VA, San Francisco, CA, Norfolk, MA; collect local prices for the six amber counties; add capacity and commercial rents; rerun when newer data arrive.
* **CLOSE:** Four counties are ready for diligence today; six more after a local price check. Data-handling details are in our appendix and GitHub repository.

# Q&A cheat sheet

| If asked… | Answer in one breath |
|---|---|
| Why not just pick the most expensive counties? | Expensive places also cost more. We want price high **relative to** wages and rent. That gap is the premium. |
| R² of 0.61 seems low. | It is solid for county data with two predictors, and the unexplained part **is** the premium we rank on. Typical miss (RMSE) is \$37/week; our top 10 sit 2.7–5.4× above it. |
| Why are six counties "verify"? | Four use one regional survey price shared with 7–8 counties (WI, Olmsted MN); two had 2018–22 price growth above the 99th percentile (Stearns +77%, McLean +59%), likely interpolation between surveys. |
| Is this just a state effect? | 43% of premium variation is between states, but with state effects added the four high-confidence picks still rank 1, 2, 3 and 8. |
| Will the premium last? | 2019 premiums predict 2022 premiums with slope 0.88 (712 counties; 0.90 across 974). The lasting part (\$31/wk) is about twice the yearly noise (\$15). |
| Why the county, when wages are per metro area? | We recommend counties, so the county is the unit; counties in one metro share its OEWS wage. |
| What about Philadelphia, St. Louis, Indianapolis…? | No usable 2022 NDCP prices for PA, IN, MO, NM, AR or PR, so they cannot be ranked. This is a data gap, not a judgment. |
| Why not weight by population? | Each county is one candidate site, so every county counts equally. |
| Where can we check the numbers? | GitHub repo `mgt403-childcare-project-green-cohort-7b`; every slide number comes from `final_output/results.json`. The appendix lists all data-handling decisions. |

# Before you present

* Open the `.pptx` in PowerPoint and use **Slide Show → Presenter View** to see notes and the timer.
* Rehearse once end to end with a stopwatch; the target is 9:30.
* Point at the chart while saying the number on slides 2 and 5. The audience follows your pointer.
* Keep the appendix (`Final_Project_Analysis.docx`) open in case a data-handling question comes up.
