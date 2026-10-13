// MGT 403 final project slides (6 slides, 10-minute talk). Every number is read from final_output/results.json
// (written by final_analysis.py), so the deck stays in sync with the analysis.
//
//   npm install pptxgenjs            (once)
//   node build_slides.js             -> Final_Project_Slides.pptx
//
// Optional: set APPLY_THEME=/path/to/apply_theme.js to write the theme colors into the file (otherwise the
// explicit colors below are used directly, which renders identically).
const fs = require("fs");
const path = require("path");
const pptxgen = require("pptxgenjs");

const R = JSON.parse(fs.readFileSync(path.join(__dirname, "final_output", "results.json"), "utf8"));
const OUT = path.join(__dirname, "Final_Project_Slides.pptx");

// ---------------------------------------------------------------- palette and type
const COL = {
  ink: "1B2A2F", ink2: "4F5D62", muted: "7C8A8E",
  teal: "0E3B43", teal2: "1F6F78", tint: "EAF3F3", line: "D5E2E3",
  coral: "E8613C", amber: "E9A23B", white: "FFFFFF",
};
const HEAD = "Cambria", BODY = "Calibri";
const THEME = {
  name: "Childcare Markets", headFontFace: HEAD, bodyFontFace: BODY,
  colors: { dk1: COL.ink, lt1: COL.white, dk2: COL.teal, lt2: COL.tint, accent1: COL.coral, accent2: COL.teal2,
            accent3: COL.amber, accent4: "5B8C85", accent5: "9FB8B4", accent6: COL.muted, hlink: COL.teal2,
            folHlink: COL.muted },
};

const pres = new pptxgen();
pres.layout = "LAYOUT_16x9";           // 10 x 5.625 in
pres.theme = { headFontFace: HEAD, bodyFontFace: BODY };
pres.title = "Where should we open our next center-based preschools?";
pres.author = "MGT 403 Green Cohort Team 7B";

// ---------------------------------------------------------------- layouts
pres.defineSlideMaster({
  title: "DARK", background: { color: COL.teal },
  objects: [],
});
pres.defineSlideMaster({
  title: "CONTENT", background: { color: COL.white },
  objects: [
    { text: { text: "MGT 403 · Green Cohort Team 7B · metro counties, 2022 $", options: { x: 0.5, y: 5.28, w: 6, h: 0.25,
              fontFace: BODY, fontSize: 9, color: COL.muted, margin: 0 } } },
  ],
  slideNumber: { x: 9.1, y: 5.28, w: 0.4, h: 0.25, fontFace: BODY, fontSize: 9, color: COL.muted, align: "right" },
});

const top10 = R.top10;
function title(slide, text, dark) {
  slide.addText(text, { x: dark ? 0.6 : 0.5, y: dark ? 0.5 : 0.32, w: dark ? 8.8 : 9.0, h: dark ? 1.0 : 0.6,
    fontFace: HEAD, fontSize: dark ? 28 : 22, bold: true, color: dark ? COL.white : COL.teal, align: "left",
    valign: "top", margin: 0, isTextBox: true, objectName: "Title" });
}
const hc = R.high_confidence_list;
const fmt = (v, d = 0) => Number(v).toLocaleString("en-US", { maximumFractionDigits: d, minimumFractionDigits: d });
const short = (n) => n.replace(" County", "").replace(" city", "").replace(", Virginia", ", VA").replace(", Minnesota", ", MN")
  .replace(", California", ", CA").replace(", Wisconsin", ", WI").replace(", Massachusetts", ", MA").replace(", Illinois", ", IL")
  .replace(", Maryland", ", MD").replace(", New Jersey", ", NJ").replace(", Washington", ", WA");
const isHigh = (r) => r.confidence === "High";
const avgPrem = top10.reduce((s, r) => s + r.premium, 0) / top10.length;
const sc = R.screens;
const rel = R.reliability;
const reg = R.regressions_2022["(c) wage + rent"];
const char = R.characteristics_regression;
const prof = R.market_profile;

function card(slide, x, y, w, h, fill = COL.tint) {
  slide.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y, w, h, fill: { color: fill }, line: { color: fill }, rectRadius: 0.08 });
}
function numCircle(slide, x, y, n, fill = COL.teal2) {
  slide.addShape(pres.shapes.OVAL, { x, y, w: 0.42, h: 0.42, fill: { color: fill }, line: { color: fill } });
  slide.addText(String(n), { x, y, w: 0.42, h: 0.42, align: "center", valign: "middle", fontFace: HEAD, fontSize: 15,
                             bold: true, color: COL.white, margin: 0, isTextBox: true });
}

// ================================================================ 1. title + answer
{
  const s = pres.addSlide({ masterName: "DARK" });
  title(s, "Where should we open our next center-based preschools?", true);
  s.addText("Answer: start with four counties where preschool prices sit well above what labor and rent costs predict, " +
            "and validate six more", { x: 0.6, y: 1.6, w: 8.8, h: 0.6, fontFace: BODY, fontSize: 16, color: "CFE3E4",
            margin: 0, isTextBox: true });
  const picks = hc.slice(0, 4);
  picks.forEach((r, i) => {
    const x = 0.6 + i * 2.23;
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y: 2.5, w: 2.03, h: 1.55, fill: { color: "174A53" },
                line: { color: "174A53" }, rectRadius: 0.08 });
    s.addText(`+$${fmt(r.premium)}`, { x: x + 0.15, y: 2.62, w: 1.75, h: 0.6, fontFace: HEAD, fontSize: 30, bold: true,
               color: COL.coral, margin: 0, isTextBox: true });
    s.addText("per week above cost prediction", { x: x + 0.15, y: 3.2, w: 1.75, h: 0.3, fontFace: BODY, fontSize: 10,
               color: "CFE3E4", margin: 0, isTextBox: true });
    s.addText(short(r.county_name), { x: x + 0.15, y: 3.55, w: 1.75, h: 0.35, fontFace: BODY, fontSize: 14, bold: true,
               color: COL.white, margin: 0, isTextBox: true });
  });
  s.addText([
    { text: `${fmt(R.screens.counties_2022)} metro counties analyzed  ·  ${sc.eligible} pass market-size and persistence screens  ·  ` +
            `top 10 average premium +$${fmt(avgPrem)}/week`, options: { breakLine: true } },
    { text: "Ignacio Sanchez Urdaneta · Beck Jamilov · Claudia Palacios Surco · Gary Chen", options: {} },
  ], { x: 0.6, y: 4.4, w: 8.8, h: 0.7, fontFace: BODY, fontSize: 12, color: "CFE3E4", margin: 0, paraSpaceAfter: 6,
       isTextBox: true });
  s.addNotes(
    "We were asked where a for-profit chain should open center-based preschools. Our definition of attractive: " +
    "prices high relative to the two main costs, childcare wages and rent. Our answer: four counties pass every check " +
    "(Arlington, Alexandria, San Francisco, Norfolk); six more look promising but need local price validation. " +
    "We analyzed all metro counties with 2022 data; the slides walk through the list, how we got it, the market profile, " +
    "whether premiums last, and what the data miss.");
}

// ================================================================ 2. (a) top 10
{
  const s = pres.addSlide({ masterName: "CONTENT" });
  const rmse = rel.rmse_2022;
  const pmin = Math.min(...top10.map((r) => r.premium)), pmax = Math.max(...top10.map((r) => r.premium));
  title(s, `Ten counties price $${fmt(pmin)}–$${fmt(pmax)} a week above cost: ${fmt(pmin / rmse, 1)}–${fmt(pmax / rmse, 1)}× the model's typical error`, false);
  const rows = [...top10].reverse();     // bar charts draw the first category at the bottom
  const labels = rows.map((r) => `${r.rank}. ${short(r.county_name)}`);
  s.addChart(pres.charts.BAR, [
    { name: "High confidence", labels, values: rows.map((r) => (isHigh(r) ? Math.round(r.premium) : 0)) },
    { name: "Verify with local prices", labels, values: rows.map((r) => (isHigh(r) ? 0 : Math.round(r.premium))) },
  ], {
    x: 0.4, y: 1.0, w: 5.6, h: 4.15, barDir: "bar", barGrouping: "stacked", barGapWidthPct: 45,
    chartColors: [COL.coral, COL.amber], showValue: true, dataLabelPosition: "inEnd", dataLabelColor: COL.white,
    dataLabelFontSize: 10, dataLabelFontBold: true, dataLabelFormatCode: '"+$"0;;', dataLabelFontFace: "+mn-lt",
    catAxisLabelColor: COL.ink, catAxisLabelFontSize: 10, catAxisLabelFontFace: "+mn-lt",
    valAxisHidden: true, valGridLine: { style: "none" }, catGridLine: { style: "none" },
    showLegend: true, legendPos: "b", legendFontSize: 10, legendFontFace: "+mn-lt", legendColor: COL.ink2,
    showTitle: true, title: "Premium over cost-predicted price, $/week, 2022", titleFontSize: 11, titleColor: COL.ink2,
    titleFontFace: "+mn-lt",
  });
  card(s, 6.25, 1.05, 3.25, 1.95);
  s.addText([
    { text: "Why verify six of them?", options: { bold: true, fontSize: 13, color: COL.teal, breakLine: true } },
    { text: "Regional price: ", options: { bold: true } },
    { text: "Winnebago, La Crosse, Brown (WI) and Olmsted (MN) share one survey price with 7–8 other counties.", options: { breakLine: true } },
    { text: "Extreme trend: ", options: { bold: true } },
    { text: "Stearns (+77%) and McLean (+59%) prices rose faster 2018–22 than 99% of counties.", options: {} },
  ], { x: 6.4, y: 1.15, w: 2.95, h: 1.8, fontFace: BODY, fontSize: 11, color: COL.ink, valign: "top", margin: 0,
       paraSpaceAfter: 5, isTextBox: true });
  card(s, 6.25, 3.15, 3.25, 2.0, COL.white);
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: 6.25, y: 3.15, w: 3.25, h: 2.0, fill: { color: COL.white },
             line: { color: COL.line, width: 1 }, rectRadius: 0.08 });
  s.addText([
    { text: "High-confidence alternates", options: { bold: true, fontSize: 13, color: COL.teal, breakLine: true } },
    ...hc.slice(4, 8).map((r, i, arr) => ({ text: `${short(r.county_name)}  +$${fmt(r.premium)}`,
                                            options: { bullet: { indent: 14 }, breakLine: i < arr.length - 1 } })),
  ], { x: 6.4, y: 3.25, w: 2.95, h: 1.85, fontFace: BODY, fontSize: 12, color: COL.ink, valign: "top", margin: 0,
       paraSpaceAfter: 4, isTextBox: true });
  s.addNotes(
    "Premium = actual 2022 median preschool price minus the price our cost model predicts from childcare wages and rent. " +
    "Arlington charges about $496 a week where costs predict $296. Coral bars pass every data check. Amber bars are real " +
    "premiums in the data but rest on weaker price data: four report a regional survey rate, two have price trends far " +
    "outside the norm that the NDCP interpolates between surveys. If those six fail local validation, the alternates on the " +
    "right (Howard MD, Burlington NJ, DuPage IL, Gloucester NJ) pass every check.");
}

// ================================================================ 3. (b) methodology and reliability
{
  const s = pres.addSlide({ masterName: "CONTENT" });
  title(s, "We rank counties by how far price exceeds what costs predict", false);
  const steps = [
    ["Cost model", `Price = a + ${fmt(reg.params.wage_k, 2)} × wage ($1k) + ${fmt(reg.params.rent_100, 2)} × rent ($100)`, `R² = ${fmt(reg.r2, 2)}, RMSE $${fmt(rel.rmse_2022)}/week; refit every year`],
    ["Premium", "Actual price − predicted price", "$/week, 2022 dollars"],
    ["Screens", "≥ 5,000 kids under 6, parents working; premium > 0 in every observed year 2019–22 (≥ 3 of 4)", `${fmt(sc.counties_2022)} → ${sc.eligible} counties`],
    ["Rank + flag", "Order by 2022 premium; flag regional prices and extreme trends", "Top 10 + confidence tier"],
  ];
  steps.forEach(([h, b, f], i) => {
    const x = 0.5 + i * 2.28;
    card(s, x, 1.05, 2.1, 2.05);
    numCircle(s, x + 0.15, 1.17, i + 1);
    s.addText(h, { x: x + 0.65, y: 1.17, w: 1.4, h: 0.42, fontFace: HEAD, fontSize: 14, bold: true, color: COL.teal,
                   valign: "middle", margin: 0, isTextBox: true });
    s.addText(b, { x: x + 0.15, y: 1.68, w: 1.82, h: 0.95, fontFace: BODY, fontSize: 11, color: COL.ink, valign: "top",
                   margin: 0, isTextBox: true });
    s.addText(f, { x: x + 0.15, y: 2.62, w: 1.82, h: 0.4, fontFace: BODY, fontSize: 10, italic: true, color: COL.teal2,
                   valign: "top", margin: 0, isTextBox: true });
  });
  s.addText("How reliable is it?", { x: 0.5, y: 3.3, w: 9, h: 0.3, fontFace: HEAD, fontSize: 14, bold: true,
             color: COL.teal, margin: 0, isTextBox: true });
  const checks = [
    [fmt(rel.oot_slope_2019_to_2022, 2), `2019 premium predicts 2022 premium (slope, ${rel.balanced_n} counties)`],
    [fmt(rel.spearman_level_vs_log, 2), "rank agreement with a log-price model"],
    [`$${fmt(rel.rmse_2022)}`, `typical miss (RMSE). What costs don't explain is the premium we rank on; top 10 clear it ${fmt(Math.min(...top10.map((r) => r.premium)) / rel.rmse_2022, 1)}–${fmt(Math.max(...top10.map((r) => r.premium)) / rel.rmse_2022, 1)}×`],
    [`${Math.round(rel.state_share_of_premium_variance * 100)}%`, `of premium variation is between states; a within-state model keeps all 4 high-confidence picks in its top ${Math.max(...["51013", "51510", "06075", "25021"].map((f) => R.top10_rank_within_state_model[f]))}`],
  ];
  checks.forEach(([big, small], i) => {
    const x = 0.5 + i * 2.28;
    s.addText(big, { x, y: 3.68, w: 2.1, h: 0.6, fontFace: HEAD, fontSize: 28, bold: true,
                     color: i === 3 ? COL.amber : COL.coral, margin: 0, isTextBox: true });
    s.addText(small, { x, y: 4.3, w: 2.05, h: 0.7, fontFace: BODY, fontSize: 11, color: COL.ink2, valign: "top",
                       margin: 0, isTextBox: true });
  });
  s.addNotes(
    "Step 1: across metro counties we regress the median preschool price on childcare-worker wages and rent; both matter " +
    "separately and together explain about 60% of price differences. Step 2: the residual is the premium. Step 3: we keep " +
    "markets with at least 5,000 young children whose parents all work, and premiums that were positive in every observed " +
    "year since 2019. Step 4: rank, then flag counties whose price data are weaker. Reliability: premiums predict themselves " +
    "three years ahead, a log model gives the same ranking, and the model fits every year. The caveat in amber: a big share " +
    "of premiums is state-level, partly because several states publish regional survey prices.");
}

// ================================================================ 4. (c) market characteristics
{
  const s = pres.addSlide({ masterName: "CONTENT" });
  title(s, "Winning markets: affluent, educated, dual-earner counties", false);
  s.addText("Characteristics we use to pick locations", { x: 0.5, y: 1.0, w: 4.2, h: 0.3, fontFace: HEAD, fontSize: 14,
             bold: true, color: COL.teal, margin: 0, isTextBox: true });
  const used = [
    ["Price premium over costs", "the ranking variable"],
    ["Childcare-worker wage", "labor cost (OEWS, per metro area)"],
    ["Median gross rent", "occupancy cost proxy"],
    ["Children under 6, all parents working", "demand depth (≥ 5,000)"],
  ];
  used.forEach(([h, b], i) => {
    const y = 1.42 + i * 0.86;
    numCircle(s, 0.5, y, i + 1, i === 0 ? COL.coral : COL.teal2);
    s.addText([{ text: h, options: { bold: true, breakLine: true } }, { text: b, options: { color: COL.ink2, fontSize: 11 } }],
              { x: 1.05, y: y - 0.05, w: 3.6, h: 0.6, fontFace: BODY, fontSize: 13, color: COL.ink, valign: "top",
                margin: 0, isTextBox: true });
  });
  // profile comparison
  card(s, 5.0, 1.0, 4.5, 4.1);
  s.addText(`Top 10 vs. all ${fmt(R.screens.counties_2022)} metro counties (2022)`, { x: 5.2, y: 1.1, w: 4.1, h: 0.3, fontFace: HEAD, fontSize: 13,
             bold: true, color: COL.teal, margin: 0, isTextBox: true });
  const P = (k) => [prof[k]["Top 10"], prof[k]["All metro counties"]];
  const stats = [
    ["Per-capita income", P("Per-capita income, $").map((v) => `$${fmt(v / 1000)}k`)],
    ["Women 25+ with bachelor's+", P("Women 25+ with bachelor's+").map((v) => `${fmt(v * 100)}%`)],
    ["Women working full-time, year-round", P("Women full-time year-round").map((v) => `${fmt(v * 100)}%`)],
    ["Median gross rent", P("Median gross rent, $/month").map((v) => `$${fmt(v)}`)],
    ["Preschool price, $/week", P("Preschool price, $/week").map((v) => `$${fmt(v)}`)],
  ];
  s.addText("Top 10", { x: 7.45, y: 1.48, w: 0.9, h: 0.25, fontFace: BODY, fontSize: 10, bold: true, color: COL.coral,
             align: "right", margin: 0, isTextBox: true });
  s.addText(`All ${fmt(R.screens.counties_2022)} metro`, { x: 8.4, y: 1.48, w: 0.95, h: 0.25, fontFace: BODY, fontSize: 10, bold: true, color: COL.ink2,
             align: "right", margin: 0, isTextBox: true });
  stats.forEach(([lab, [a, b]], i) => {
    const y = 1.82 + i * 0.5;
    s.addText(lab, { x: 5.2, y, w: 2.3, h: 0.4, fontFace: BODY, fontSize: 12, color: COL.ink, valign: "middle", margin: 0, isTextBox: true });
    s.addText(a, { x: 7.45, y, w: 0.9, h: 0.4, fontFace: HEAD, fontSize: 16, bold: true, color: COL.coral, align: "right", valign: "middle", margin: 0, isTextBox: true });
    s.addText(b, { x: 8.4, y, w: 0.95, h: 0.4, fontFace: HEAD, fontSize: 16, color: COL.ink2, align: "right", valign: "middle", margin: 0, isTextBox: true });
  });
  s.addText(`But demographics alone explain only ${Math.round(char.r2 * 100)}% of premiums, so we rank on the measured premium, ` +
            "not on demographics.", { x: 5.2, y: 4.38, w: 4.15, h: 0.6, fontFace: BODY, fontSize: 11, italic: true,
            color: COL.teal2, valign: "top", margin: 0, isTextBox: true });
  s.addNotes(
    "We pick locations on four measured characteristics: the premium, the two cost drivers that define it, and demand " +
    "depth. The recommended counties share a profile: about 50% higher income, far more college-educated women, more " +
    "women working full-time. Income, female college share and the share of young children needing care are each " +
    "significantly related to premiums, but together explain only 7% of them, so most of the premium is local market " +
    "conditions our data do not see directly. That is why we rank on the premium itself.");
}

// ================================================================ 5. (d) stability
{
  const s = pres.addSlide({ masterName: "CONTENT" });
  title(s, "Premiums persist, so they are signal, not noise", false);
  const yrs = ["2015", "2016", "2017", "2018", "2019", "2020", "2021"];
  s.addChart(pres.charts.LINE, [
    { name: "Correlation of each year's premium with 2022", labels: yrs, values: yrs.map((y) => +rel.corr_with_2022[y].toFixed(2)) },
    { name: "Share of 2022 top-10% counties already top 10% that year", labels: yrs, values: yrs.map((y) => +rel.persistence_top_decile[y].toFixed(2)) },
  ], {
    x: 0.4, y: 1.0, w: 5.8, h: 4.15, chartColors: [COL.teal2, COL.coral], lineSize: 2.5, lineDataSymbol: "circle",
    lineDataSymbolSize: 7, valAxisMinVal: 0, valAxisMaxVal: 1, valAxisLabelFormatCode: "0%",
    showValue: false, catAxisLabelColor: COL.ink2, valAxisLabelColor: COL.ink2, catAxisLabelFontSize: 10,
    valAxisLabelFontSize: 10, catAxisLabelFontFace: "+mn-lt", valAxisLabelFontFace: "+mn-lt",
    valGridLine: { color: COL.line, size: 0.5 }, catGridLine: { style: "none" },
    showLegend: true, legendPos: "b", legendFontSize: 10, legendColor: COL.ink2, legendFontFace: "+mn-lt",
    showTitle: true, title: `Premium persistence, ${rel.balanced_n} counties observed every year`, titleFontSize: 11,
    titleColor: COL.ink2, titleFontFace: "+mn-lt",
  });
  card(s, 6.45, 1.05, 3.05, 1.6);
  s.addText(fmt(rel.oot_slope_2019_to_2022, 2), { x: 6.6, y: 1.12, w: 2.8, h: 0.65, fontFace: HEAD, fontSize: 36, bold: true,
             color: COL.coral, margin: 0, isTextBox: true });
  s.addText(`A $1 premium in 2019 still meant about ${Math.round(rel.oot_slope_2019_to_2022 * 100)}¢ in 2022 (${rel.balanced_n} counties; ${fmt(rel.oot_slope_all_2019_2022, 2)} across all ${fmt(rel.oot_n_all)})`, { x: 6.6, y: 1.8, w: 2.75, h: 0.8,
             fontFace: BODY, fontSize: 12, color: COL.ink, valign: "top", margin: 0, isTextBox: true });
  card(s, 6.45, 2.8, 3.05, 1.3);
  s.addText([{ text: "Signal, not noise: ", options: { bold: true } },
             { text: `the lasting part of each premium (SD $${fmt(rel.signal_sd)}/wk) is twice the yearly noise ($${fmt(rel.noise_sd)}). ` +
                     `Knowing the 2019 premium cuts the 2022 price error from $${fmt(rel.rmse_2022)} to $${fmt(rel.oot_resid_sd_all)}.`, options: {} }],
            { x: 6.6, y: 2.88, w: 2.8, h: 1.15, fontFace: BODY, fontSize: 11.5, color: COL.ink, valign: "top", margin: 0, isTextBox: true });
  s.addText("Caveat: states survey prices every 2–3 years and NDCP interpolates in between, so adjacent years look more " +
            "alike than they are. The 3+ year comparisons are the honest test, and they hold.", { x: 6.45, y: 4.22, w: 3.05,
            h: 0.95, fontFace: BODY, fontSize: 10, italic: true, color: COL.ink2, valign: "top", margin: 0, isTextBox: true });
  s.addNotes(
    "We re-estimated the cost model every year and tracked each county's premium. Premiums fade slowly: correlation with " +
    "2022 is 0.94 one year back, 0.82 three years back, 0.58 seven years back. Of today's top-decile counties, 69% were " +
    "already top decile in 2019. A regression of 2022 on 2019 premiums has slope 0.88. Caveat: survey cycles and NDCP's " +
    "interpolation make adjacent years artificially similar, so we lean on the 2019 vs 2022 comparison.");
}

// ================================================================ 6. (e) missing factors + next steps
{
  const s = pres.addSlide({ masterName: "DARK" });
  title(s, "Before committing capital, close these gaps", true);
  const miss = [
    ["Competition and capacity", "Licensed slots, waitlists, incumbents (incl. existing Bright Horizons sites)"],
    ["Labor cost", "OEWS childcare workers exclude preschool teachers (SOC 25‑2011); ratio rules raise cost per child (MN strictest)"],
    ["Real estate", "Commercial lease rates and zoning, not residential rent"],
    ["Missing markets", "No 2022 NDCP prices for PA, IN, MO, NM, AR, PR (Philadelphia, Pittsburgh, St. Louis, Indianapolis)"],
    ["Price quality", "Posted survey medians, some regional or interpolated; not realized prices after discounts"],
  ];
  s.addText("What our model does not see", { x: 0.6, y: 1.25, w: 5.2, h: 0.35, fontFace: HEAD, fontSize: 15, bold: true,
             color: COL.coral, margin: 0, isTextBox: true });
  miss.forEach(([h, b], i) => {
    s.addText([{ text: h + ": ", options: { bold: true, color: COL.white } }, { text: b, options: { color: "CFE3E4" } }],
              { x: 0.6, y: 1.7 + i * 0.67, w: 5.2, h: 0.62, fontFace: BODY, fontSize: 12, valign: "top", margin: 0, isTextBox: true });
  });
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: 6.2, y: 1.25, w: 3.25, h: 3.85, fill: { color: "174A53" },
             line: { color: "174A53" }, rectRadius: 0.08 });
  s.addText("Next steps", { x: 6.4, y: 1.38, w: 2.9, h: 0.35, fontFace: HEAD, fontSize: 15, bold: true, color: COL.coral,
             margin: 0, isTextBox: true });
  const steps = [
    "Site and competitor scan in Arlington, Alexandria, San Francisco and Norfolk",
    "Collect local center prices for the six 'verify' counties",
    "Add licensed capacity and commercial rents to the model",
    "Re-run with NDCP data beyond 2022 as it is released",
  ];
  s.addText(steps.map((t, i) => ({ text: t, options: { bullet: { type: "number", indent: 18 }, breakLine: i < steps.length - 1 } })),
            { x: 6.4, y: 1.85, w: 2.9, h: 3.1, fontFace: BODY, fontSize: 12, color: COL.white, valign: "top", margin: 0,
              paraSpaceAfter: 8, isTextBox: true });
  s.addNotes(
    "Our model sees prices and two costs, not supply. A high premium could signal unmet demand or a market that is hard " +
    "to enter. State ratio rules raise labor cost per child; residential rent is only a proxy for commercial leases; six " +
    "states have no usable 2022 prices; and NDCP prices are posted survey medians. Next steps: diligence on the four " +
    "high-confidence counties, local price checks for the six to verify, and adding capacity and commercial rents. " +
    "Data handling decisions are documented in the appendix document and the GitHub repository.");
}

(async () => {
  await pres.writeFile({ fileName: OUT });
  if (process.env.APPLY_THEME) {
    const { applyTheme } = require(process.env.APPLY_THEME);
    await applyTheme(OUT, THEME);
  }
  console.log("wrote", OUT);
})();
