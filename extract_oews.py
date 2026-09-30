"""
Extract BLS OEWS childcare-worker wages (SOC 39-9011) at the
metropolitan / nonmetropolitan area level from the oesmYYma.zip files.

Source files: https://www.bls.gov/oes/special-requests/oesmYYma.zip  (YY = 15..22)
Each zip holds two workbooks (layout per their "Field Descriptions" sheet):
  MSA_M20YY_dl.xlsx  metropolitan areas   (AREA_TYPE 4, 5-digit MSA/NECTA code)
  BOS_M20YY_dl.xlsx  nonmetropolitan areas (AREA_TYPE 6, 7-digit OEWS code)

Rules applied
- Keep OCC_CODE == "39-9011" (Childcare Workers); cross-industry, all ownerships.
- AREA zero-padded to 7 characters (e.g. 10180 -> "0010180") so it matches
  `oews_area` in county_oews_crosswalk.csv. Metro codes then begin with "00".
- Wage cells: "*" = wage estimate not available, "#" = top-coded (>= $115/hr or
  $239,200/yr in 2022). Both become missing in the numeric columns; the raw code
  is kept in A_MEAN_RAW so nothing is silently lost.
- Main variable: A_MEAN = mean annual wage, nominal dollars.

Usage:  python extract_oews.py oesm15ma.zip oesm16ma.zip ... oesm22ma.zip
Writes: oews_39-9011_areas.csv (one row per year x area) and a sanity-check
        printout of the 2015-2022 merge to metro counties via the crosswalk.
Per-year results are cached in oews_cache/ so years can be processed one at a time.
"""
import io, os, re, sys, zipfile
import pandas as pd

SOC = "39-9011"
CROSSWALK = "county_oews_crosswalk.csv"
OUT = "oews_39-9011_areas.csv"
CACHE = "oews_cache"
KEEP = ["AREA", "AREA_TITLE", "AREA_TYPE", "PRIM_STATE", "OCC_CODE", "OCC_TITLE",
        "TOT_EMP", "EMP_PRSE", "H_MEAN", "A_MEAN", "MEAN_PRSE", "A_MEDIAN"]
RENAME = {"AREA_NAME": "AREA_TITLE", "ST": "PRIM_STATE"}  # older-year header variants


def year_from_name(name):
    m = re.search(r"oesm(\d{2})ma", os.path.basename(name).lower())
    return 2000 + int(m.group(1))


def read_zip(path):
    year = year_from_name(path)
    cache = os.path.join(CACHE, f"oews_{SOC}_{year}.csv")
    if os.path.exists(cache):
        return pd.read_csv(cache, dtype=str)
    frames = []
    with zipfile.ZipFile(path) as z:
        for name in z.namelist():
            base = os.path.basename(name)
            if base.startswith("~$") or not re.search(r"(MSA|BOS|aMSA|BOS_M).*\.xlsx?$", base, re.I):
                continue
            df = pd.read_excel(io.BytesIO(z.read(name)), sheet_name=0, dtype=str)
            df.columns = [RENAME.get(c.strip().upper(), c.strip().upper()) for c in df.columns]
            df = df[df["OCC_CODE"].str.strip() == SOC]
            df = df[[c for c in KEEP if c in df.columns]].copy()
            df["SOURCE_FILE"] = base
            frames.append(df)
            print(f"  {base}: {len(df)} rows for {SOC}")
    out = pd.concat(frames, ignore_index=True)
    out.insert(0, "year", year)
    os.makedirs(CACHE, exist_ok=True)
    out.to_csv(cache, index=False)
    return out


def clean(df):
    df = df.copy()
    df["oews_area"] = df["AREA"].str.strip().str.zfill(7)
    df["A_MEAN_RAW"] = df["A_MEAN"]
    for c in ["TOT_EMP", "EMP_PRSE", "H_MEAN", "A_MEAN", "MEAN_PRSE", "A_MEDIAN"]:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c].str.replace(",", ""), errors="coerce")
    df["metro"] = df["oews_area"].str.startswith("00")
    cols = ["year", "oews_area", "AREA_TITLE", "AREA_TYPE", "PRIM_STATE", "metro",
            "OCC_CODE", "OCC_TITLE", "TOT_EMP", "EMP_PRSE", "A_MEAN", "A_MEAN_RAW",
            "H_MEAN", "MEAN_PRSE", "A_MEDIAN", "SOURCE_FILE"]
    return df[[c for c in cols if c in df.columns]]


def sanity_check(areas):
    if not os.path.exists(CROSSWALK):
        print(f"(skip merge check: {CROSSWALK} not found)")
        return
    cw = pd.read_csv(CROSSWALK, dtype={"county_fips": str, "oews_area": str})
    cw = cw[cw["oews_area"].str.startswith("00") & cw["year"].isin(areas["year"].unique())]
    m = cw.merge(areas[["year", "oews_area", "A_MEAN"]], on=["year", "oews_area"], how="left")
    print("\nMetro counties with a childcare-worker mean annual wage (crosswalk merge):")
    s = m.groupby("year").agg(metro_counties=("county_fips", "size"),
                              missing_wage=("A_MEAN", lambda x: x.isna().sum()))
    s["pct_missing"] = (100 * s.missing_wage / s.metro_counties).round(1)
    print(s.to_string())
    return m


if __name__ == "__main__":
    zips = sys.argv[1:] or sorted(f for f in os.listdir(".") if re.match(r"oesm\d{2}ma\.zip", f))
    for z in zips:
        print(f"{z} -> {year_from_name(z)}")
        read_zip(z)
    cached = [pd.read_csv(os.path.join(CACHE, f), dtype=str) for f in sorted(os.listdir(CACHE))]
    areas = clean(pd.concat(cached, ignore_index=True))
    areas["year"] = areas["year"].astype(int)
    areas.to_csv(OUT, index=False)
    print(f"\nWrote {OUT}: {len(areas)} year x area rows")
    print(areas.groupby(["year", "metro"]).agg(areas=("oews_area", "size"),
                                                mean_A_MEAN=("A_MEAN", "mean"),
                                                missing=("A_MEAN", lambda x: x.isna().sum())).round(0).to_string())
    sanity_check(areas)
