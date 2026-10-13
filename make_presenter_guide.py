"""
Build Presenter_Guide.md (-> .docx/.pdf with build_docx.py) from the speaker notes inside Final_Project_Slides.pptx,
so the printed script and the deck can never disagree. Adds a run-of-show table and a Q&A cheat sheet.

Run:  python3 make_presenter_guide.py && python3 build_docx.py Presenter_Guide.md
"""
import html
import json
import os
import re
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
R = json.load(open(os.path.join(HERE, "final_output", "results.json")))
rel, reg = R["reliability"], R["regressions_2022"]["(c) wage + rent"]

z = zipfile.ZipFile(os.path.join(HERE, "Final_Project_Slides.pptx"))
notes = []
for n in sorted((x for x in z.namelist() if re.match(r"ppt/notesSlides/notesSlide\d+\.xml$", x)),
                key=lambda x: int(re.search(r"(\d+)", x.split("/")[-1]).group(1))):
    xml = z.read(n).decode("utf8")
    paras = ["".join(re.findall(r"<a:t>([^<]*)</a:t>", p)) for p in re.findall(r"<a:p>(.*?)</a:p>", xml, re.S)]
    lines = []
    for p in paras:
        lines += html.unescape(p).split("\n")
    notes.append([l for l in lines if l.strip() and not l.strip().isdigit()])

TITLES = ["Where should we open our next center-based preschools?", "Top 10 counties and confidence tiers",
          "Method and reliability", "Market characteristics", "Are premiums stable?", "What we miss and next steps"]
rows, script = [], []
for i, paras in enumerate(notes):
    head = paras[0]  # "SLIDE n | m:ss min | Speaker X"
    _, time, who = [h.strip() for h in head.split("|")]
    rows.append(f"| {i + 1} | {TITLES[i]} | {time.replace(' min', '')} | {who} |")
    body = [p for p in paras[1:] if p.strip()]
    script.append(f"## Slide {i + 1}: {TITLES[i]} ({time.replace(' min', '')}, {who})\n")
    for p in body:
        p = p.replace("$", "\\$")
        m = re.match(r"^(SAY|HAND-OFF|LIKELY Q|RELIABILITY \(bottom row\)|NEXT STEPS|CLOSE):\s*(.*)$", p)
        script.append(f"* **{m.group(1)}:** {m.group(2)}" if m else f"* {p}")
    script.append("")

md = f"""---
title: "Final Project Presentation: Presenter Guide"
subtitle: "MGT 403 · Green Cohort Team 7B · 6 slides, 10-minute limit"
---

# Run of show

| Slide | Topic | Time | Speaker |
|---|---|---|---|
{chr(10).join(rows)}
| | **Total** | **9:30** (30-second buffer) | |

Speakers A–D are placeholders; assign them to team members. Each speaker gives one short hand-off line to
the next. The script below is the same text as the speaker notes in `Final_Project_Slides.pptx` (Presenter View shows
it on your screen). Read it once aloud with a timer; most groups run long on slides 2 and 3.

# Script

{chr(10).join(script)}
# Q&A cheat sheet

| If asked… | Answer in one breath |
|---|---|
| Why not just pick the most expensive counties? | Expensive places also cost more. We want price high **relative to** wages and rent. That gap is the premium. |
| R² of {reg['r2']:.2f} seems low. | It is solid for county data with two predictors, and the unexplained part **is** the premium we rank on. Typical miss (RMSE) is \\${rel['rmse_2022']:.0f}/week; our top 10 sit 2.7–5.4× above it. |
| Why are six counties "verify"? | Four use one regional survey price shared with 7–8 counties (WI, Olmsted MN); two had 2018–22 price growth above the 99th percentile (Stearns +77%, McLean +59%), likely interpolation between surveys. |
| Is this just a state effect? | {rel['state_share_of_premium_variance'] * 100:.0f}% of premium variation is between states, but with state effects added the four high-confidence picks still rank 1, 2, 3 and 8. |
| Will the premium last? | 2019 premiums predict 2022 premiums with slope {rel['oot_slope_2019_to_2022']:.2f} ({rel['balanced_n']} counties; {rel['oot_slope_all_2019_2022']:.2f} across {rel['oot_n_all']}). The lasting part (\\${rel['signal_sd']:.0f}/wk) is about twice the yearly noise (\\${rel['noise_sd']:.0f}). |
| Why the county, when wages are per metro area? | We recommend counties, so the county is the unit; counties in one metro share its OEWS wage. |
| What about Philadelphia, St. Louis, Indianapolis…? | No usable 2022 NDCP prices for PA, IN, MO, NM, AR or PR, so they cannot be ranked. This is a data gap, not a judgment. |
| Why not weight by population? | Each county is one candidate site, so every county counts equally. |
| Where can we check the numbers? | GitHub repo `mgt403-childcare-project-green-cohort-7b`; every slide number comes from `final_output/results.json`. The appendix lists all data-handling decisions. |

# Before you present

* Open the `.pptx` in PowerPoint and use **Slide Show → Presenter View** to see notes and the timer.
* Rehearse once end to end with a stopwatch; the target is 9:30.
* Point at the chart while saying the number on slides 2 and 5. The audience follows your pointer.
* Keep the appendix (`Final_Project_Analysis.docx`) open in case a data-handling question comes up.
"""
with open(os.path.join(HERE, "Presenter_Guide.md"), "w") as f:
    f.write(md)
print("wrote Presenter_Guide.md")
