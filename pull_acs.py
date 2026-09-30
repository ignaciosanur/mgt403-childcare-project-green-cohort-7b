"""
Pull ACS 5-year county estimates (2015-2022) from the Census API and build the
project's demand/cost variables.  Standard-library Python 3 only (no installs).

Run (Mac Terminal, in the folder containing this file):
    python3 pull_acs.py YOUR_CENSUS_API_KEY
    (or: export CENSUS_API_KEY=...; python3 pull_acs.py)

Outputs
    acs_raw/acs5_YYYY.json         raw API responses (documentation / re-runs)
    acs_county_2015_2022.csv       one row per year x county

ACS codes (verified against the API variable labels, 2015 and 2022 vintages):
    B19301_001E  per capita income (past 12 months, nominal $ of the ACS year)
    B01001_001E  total population
    B23008_002E  own children under 6
    B23008_004E  under 6, two parents, both in labor force
    B23008_010E  under 6, living with father only, father in labor force
    B23008_013E  under 6, living with mother only, mother in labor force
    B25064_001E  median gross rent (rent + utilities, nominal $)
    B15002_019E  women 25+ (total);  _032E/_033E/_034E/_035E = bachelor's /
                 master's / professional / doctorate
    B23022_026E  women 16-64 (total); _029E = worked 35+ hrs/wk, 50-52 wks
Derived (names as in the assignment):
    per_capita_income, pop_total, kids_under6, kids_under6_allpar_lf,
    median_gross_rent, female_college_share, female_ftyr_share,
    under6_share = kids_under6 / pop_total,
    under6_careneed_share = kids_under6_allpar_lf / pop_total
Census "annotation" sentinels (large negative numbers, e.g. -666666666 = not
available) are written as blanks.  Dollar values are left NOMINAL here; the
CPI-U conversion to 2022 dollars happens in the analysis step.
"""
import csv, json, os, ssl, sys, time, urllib.parse, urllib.request

YEARS = range(2015, 2023)
VARS = ["B19301_001E", "B01001_001E",
        "B23008_002E", "B23008_004E", "B23008_010E", "B23008_013E",
        "B25064_001E",
        "B15002_019E", "B15002_032E", "B15002_033E", "B15002_034E", "B15002_035E",
        "B23022_026E", "B23022_029E"]
RAW_DIR = "acs_raw"
OUT = "acs_county_2015_2022.csv"


def fetch(year, key):
    params = {"get": "NAME," + ",".join(VARS), "for": "county:*", "in": "state:*", "key": key}
    url = f"https://api.census.gov/data/{year}/acs/acs5?" + urllib.parse.urlencode(params, safe=":*,")
    try:
        import certifi  # present in many Python installs; fixes macOS cert issues
        ctx = ssl.create_default_context(cafile=certifi.where())
    except ImportError:
        ctx = ssl.create_default_context()
    for attempt in range(3):
        try:
            with urllib.request.urlopen(url, timeout=120, context=ctx) as r:
                return json.loads(r.read().decode("utf-8"))
        except ssl.SSLError as e:
            sys.exit(f"SSL error: {e}\nOn a python.org install on Mac, run "
                     "'Install Certificates.command' in /Applications/Python 3.x/ and retry.")
        except Exception as e:
            if attempt == 2:
                raise
            print(f"  retrying {year} ({e})")
            time.sleep(3)


def num(x):
    if x in (None, "", "null"):
        return None
    v = float(x)
    return None if v <= -222222222 else v   # Census sentinel codes


def ratio(a, b):
    return None if a is None or b in (None, 0) else a / b


def ssum(*xs):
    return None if any(x is None for x in xs) else sum(xs)


def build_rows(year, data):
    header, rows = data[0], data[1:]
    ix = {h: i for i, h in enumerate(header)}
    out = []
    for r in rows:
        g = {v: num(r[ix[v]]) for v in VARS}
        kids = g["B23008_002E"]
        allpar = ssum(g["B23008_004E"], g["B23008_010E"], g["B23008_013E"])
        pop = g["B01001_001E"]
        coll = ssum(g["B15002_032E"], g["B15002_033E"], g["B15002_034E"], g["B15002_035E"])
        rec = {"year": year,
               "county_fips": r[ix["state"]] + r[ix["county"]],   # 5-char text, keeps zeros
               "NAME": r[ix["NAME"]]}
        rec.update(g)
        rec.update({
            "per_capita_income": g["B19301_001E"],
            "pop_total": pop,
            "kids_under6": kids,
            "kids_under6_allpar_lf": allpar,
            "median_gross_rent": g["B25064_001E"],
            "female_college_share": ratio(coll, g["B15002_019E"]),
            "female_ftyr_share": ratio(g["B23022_029E"], g["B23022_026E"]),
            "under6_share": ratio(kids, pop),
            "under6_careneed_share": ratio(allpar, pop),
        })
        out.append(rec)
    return out


def main():
    key = (sys.argv[1] if len(sys.argv) > 1 else os.environ.get("CENSUS_API_KEY", "")).strip()
    os.makedirs(RAW_DIR, exist_ok=True)
    all_rows = []
    for y in YEARS:
        raw_path = os.path.join(RAW_DIR, f"acs5_{y}.json")
        if os.path.exists(raw_path):
            data = json.load(open(raw_path))
            print(f"{y}: loaded cached {raw_path}")
        else:
            if not key:
                sys.exit("Usage: python3 pull_acs.py YOUR_CENSUS_API_KEY")
            print(f"{y}: requesting Census API ...")
            data = fetch(y, key)
            json.dump(data, open(raw_path, "w"))
        rows = build_rows(y, data)
        n_rent = sum(r["median_gross_rent"] is not None for r in rows)
        print(f"   {len(rows):,} counties; {n_rent:,} with median gross rent")
        all_rows.extend(rows)
    cols = list(all_rows[0].keys())
    with open(OUT, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        for r in all_rows:
            w.writerow({k: ("" if v is None else v) for k, v in r.items()})
    print(f"\nWrote {OUT}: {len(all_rows):,} year x county rows")


if __name__ == "__main__":
    main()
