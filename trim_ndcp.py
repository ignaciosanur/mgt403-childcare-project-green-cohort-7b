"""
Trim the DOL NDCP county-level workbook (NDCP2022.xlsx, study years 2008-2022)
down to study years 2015-2022.

What it does
- Keeps every column and the original cell formatting; only drops rows whose
  STUDYYEAR (column E) is outside 2015-2022.
- Stores COUNTY_FIPS_CODE (column D) as 5-character zero-padded text
  (1001 -> "01001") so it merges cleanly with county_fips in the OEWS crosswalk
  and no software drops the leading zero.
- Also writes the same data as a CSV (much smaller, fastest to load in pandas/R).

Why it works on the raw XML: the source file is ~92 MB zipped / ~566 MB of sheet
XML (48,308 rows x 370 cols), which is too slow to open with pandas/openpyxl.
An .xlsx is a zip of XML files, so we stream the sheet XML row by row, keep the
rows we want verbatim (renumbered), and re-zip.

Usage: python trim_ndcp.py NDCP2022.xlsx NDCP2015_2022.xlsx
"""
import csv, html, re, sys, zipfile

SRC = sys.argv[1] if len(sys.argv) > 1 else "NDCP2022.xlsx"
OUT = sys.argv[2] if len(sys.argv) > 2 else "NDCP2015_2022.xlsx"
OUT_CSV = OUT.replace(".xlsx", ".csv")
YEARS = range(2015, 2023)
SHEET = "xl/worksheets/sheet1.xml"

zin = zipfile.ZipFile(SRC)

# Shared strings (text cells store an index into this list)
ss_xml = zin.read("xl/sharedStrings.xml").decode("utf-8")
shared = [html.unescape(re.sub(r"<[^>]+>", "", si))
          for si in re.findall(r"<si>(.*?)</si>", ss_xml, re.S)]

year_re = re.compile(rb'<c r="E\d+"[^>]*><v>(\d+)</v></c>')
ref_re = re.compile(rb'(<c r="[A-Z]+)\d+"')
cell_re = re.compile(rb'<c r="([A-Z]+)\d+"([^>]*?)(?:/>|>(.*?)</c>)')
v_re = re.compile(rb"<v>(.*?)</v>")
fips_re = re.compile(rb'<c r="D(\d+)"([^>]*?)><v>(\d+)</v></c>')


def col_idx(letters):
    n = 0
    for ch in letters:
        n = n * 26 + (ch - 64)
    return n - 1


def row_values(row_xml, ncols=370):
    vals = [""] * ncols
    for col, attrs, inner in cell_re.findall(row_xml):
        if inner is None:
            continue
        if b't="inlineStr"' in attrs:
            vals[col_idx(col)] = html.unescape(re.sub(rb"<[^>]+>", b"", inner).decode())
            continue
        m = v_re.search(inner)
        if not m:
            continue
        v = m.group(1).decode()
        vals[col_idx(col)] = shared[int(v)] if b't="s"' in attrs else v
    return vals


kept, total, new_r = [], 0, 0
per_year = {}
csv_f = open(OUT_CSV, "w", newline="", encoding="utf-8")
writer = csv.writer(csv_f)

with zin.open(SHEET) as f:
    data = f.read()  # ~566 MB; fine in memory, far faster than an XML parser

start = data.index(b"<sheetData>") + len(b"<sheetData>")
end = data.index(b"</sheetData>")
head, tail = data[:start], data[end:]

pos = start
while pos < end:
    r_end = data.index(b"</row>", pos) + len(b"</row>")
    row = data[pos:r_end]
    pos = r_end
    total += 1
    if total == 1:  # header row
        keep = True
    else:
        m = year_re.search(row)
        yr = int(m.group(1)) if m else None
        keep = yr in YEARS
        if keep:
            per_year[yr] = per_year.get(yr, 0) + 1
    if not keep:
        continue
    new_r += 1
    rb = str(new_r).encode()
    row = re.sub(rb'^<row r="\d+"', b'<row r="' + rb + b'"', row)
    row = ref_re.sub(lambda m: m.group(1) + rb + b'"', row)
    if new_r > 1:  # FIPS -> 5-char text
        row = fips_re.sub(
            lambda m: b'<c r="D' + m.group(1) + b'"' + m.group(2)
            + b' t="inlineStr"><is><t>' + m.group(3).zfill(5) + b"</t></is></c>", row)
    kept.append(row)
    writer.writerow(row_values(row))
del data
csv_f.close()

# Fix the sheet header: dimension, and drop the saved scroll position/selection
head = re.sub(rb'<dimension ref="[^"]+"/>', b'<dimension ref="A1:NF' + str(new_r).encode() + b'"/>', head)
head = re.sub(rb"<sheetViews>.*?</sheetViews>",
              b'<sheetViews><sheetView tabSelected="1" workbookViewId="0"><pane ySplit="1" topLeftCell="A2" activePane="bottomLeft" state="frozen"/></sheetView></sheetViews>',
              head, flags=re.S)

with zipfile.ZipFile(OUT, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as zout:
    for item in zin.infolist():
        if item.filename.startswith("[trash]"):
            continue
        if item.filename == SHEET:
            zout.writestr(SHEET, head + b"".join(kept) + tail)
        else:
            zout.writestr(item, zin.read(item.filename))

print(f"Source rows (excl. header): {total - 1:,}")
print(f"Kept rows   (excl. header): {new_r - 1:,}")
for y in sorted(per_year):
    print(f"  {y}: {per_year[y]:,}")
print(f"Wrote {OUT} and {OUT_CSV}")
