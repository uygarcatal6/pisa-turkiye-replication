# -*- coding: utf-8 -*-
"""
01_build_panel.py  —  PISA score-inflation research: build analysis panels.

Reproducible builder for TASK 2. Every value is read from a source file; nothing
is hard-coded from memory. Every output row carries provenance (source_file / sheet
/ cell_ref where applicable).

Outputs (all under data/derived/):
  (a) pisa_scores_long.csv , pisa_scores_wide.csv
  (b) governance_annual.csv
  (c) analysis_panel.csv
  (d) validation printed to stdout (PASS/FAIL)
  (e) PANEL_README.md  (Turkish)

Sources:
  PISA mean-score trend tables : data/pisa/2025/annex_tables/mrq53f.xlsx
      Table I.B1.2a.36 = science 2006->2025
      Table I.B1.2a.37 = reading 2000->2025
      Table I.B1.2a.38 = mathematics 2003->2025
      Table I.B1.2a.4  = computational problem solving (CPS), 2025 only
  Coverage/exclusion/response : data/derived/annex_extract.csv
  WGI (governance)            : data/governance/wgi/wgidataset_with_sourcedata-2025.xlsx (sheets cc, rl)
  CPI                         : data/governance/cpi/CPI2025_Results.xlsx (sheet "CPI Timeseries 2012 - 2025")

NOTE: never execute anything from the QUARANTINE folder. This script lives under
analysis/ and reads only from data/.
"""
import os, csv, zipfile, re
import xml.etree.ElementTree as ET
import openpyxl

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))).replace("\\", "/")
DERIVED = os.path.join(ROOT, "data", "derived")
TREND_XLSX = os.path.join(ROOT, "data/pisa/2025/annex_tables/mrq53f.xlsx")
TREND_REL = "data/pisa/2025/annex_tables/mrq53f.xlsx"
WGI_XLSX = os.path.join(ROOT, "data/governance/wgi/wgidataset_with_sourcedata-2025.xlsx")
WGI_REL = "data/governance/wgi/wgidataset_with_sourcedata-2025.xlsx"
CPI_XLSX = os.path.join(ROOT, "data/governance/cpi/CPI2025_Results.xlsx")
CPI_REL = "data/governance/cpi/CPI2025_Results.xlsx"
CPI_TS_SHEET_XML = "xl/worksheets/sheet2.xml"   # "CPI Timeseries 2012 - 2025"
CPI_TS_SHEET_NAME = "CPI Timeseries 2012 - 2025"
ANNEX = os.path.join(DERIVED, "annex_extract.csv")

# ---------------------------------------------------------------- ISO3 / OECD map
# 38 current OECD members (name as printed in the PISA workbooks).
OECD_MEMBERS = {
    "Australia","Austria","Belgium","Canada","Chile","Colombia","Costa Rica","Czechia",
    "Denmark","Estonia","Finland","France","Germany","Greece","Hungary","Iceland","Ireland",
    "Israel","Italy","Japan","Korea","Latvia","Lithuania","Luxembourg","Mexico","Netherlands",
    "New Zealand","Norway","Poland","Portugal","Slovak Republic","Slovenia","Spain","Sweden",
    "Switzerland","T\u00fcrkiye","United Kingdom","United States",
}

# Clean name (strip caution asterisk) -> ISO3.
# Standard ISO3 where a sovereign match exists; Q-prefixed pseudo-codes for sub/supra
# entities that must NOT falsely join national governance series.
ISO3 = {
    "Argentina":"ARG","Armenia":"ARM","Australia":"AUS","Austria":"AUT","Azerbaijan":"AZE",
    "Belgium":"BEL","Brazil":"BRA","Brunei Darussalam":"BRN","B-S-J-Z (China)":"QCI",
    "Bulgaria":"BGR","Cambodia":"KHM","Canada":"CAN","Chile":"CHL","Colombia":"COL",
    "Costa Rica":"CRI","Croatia":"HRV","Cyprus":"CYP","Czechia":"CZE","Denmark":"DNK",
    "Dominican Republic":"DOM","Dushanbe (Tajikistan)":"QDT","Ecuador":"ECU","El Salvador":"SLV",
    "Estonia":"EST","Finland":"FIN","France":"FRA","Georgia":"GEO","Germany":"DEU","Greece":"GRC",
    "Guatemala":"GTM","Hong Kong (China)":"HKG","Hungary":"HUN","Iceland":"ISL","Indonesia":"IDN",
    "Ireland":"IRL","Israel":"ISR","Italy":"ITA","Japan":"JPN","Jordan":"JOR","Kazakhstan":"KAZ",
    "Kenya":"KEN","Korea":"KOR","Kosovo":"XKX","Kurdistan Region (Iraq)":"QKI","Kyrgyzstan":"KGZ",
    "Latvia":"LVA","Lebanon":"LBN","Lithuania":"LTU","Luxembourg":"LUX","Macao (China)":"MAC",
    "Malaysia":"MYS","Malta":"MLT","Mauritius":"MUS","Mexico":"MEX","Moldova":"MDA","Mongolia":"MNG",
    "Montenegro":"MNE","Morocco":"MAR","Netherlands":"NLD","New Zealand":"NZL","North Macedonia":"MKD",
    "Norway":"NOR","Palestinian Authority":"PSE","Paraguay":"PRY","Peru":"PER","Philippines":"PHL",
    "Poland":"POL","Portugal":"PRT","Qatar":"QAT","Romania":"ROU","Rwanda":"RWA","Saudi Arabia":"SAU",
    "Serbia":"SRB","Singapore":"SGP","Slovak Republic":"SVK","Slovenia":"SVN","Spain":"ESP",
    "Sweden":"SWE","Switzerland":"CHE","Chinese Taipei":"TWN","Thailand":"THA","T\u00fcrkiye":"TUR",
    "Ukrainian regions (17 of 27)":"QUA","United Arab Emirates":"ARE","United Kingdom":"GBR",
    "United States":"USA","Uruguay":"URY","Uzbekistan":"UZB","Viet Nam":"VNM","Zambia":"ZMB",
    "Albania":"ALB",
    # supranational aggregates (kept for the OECD-average benchmark rows)
    "OECD average":"OECD","OECD average-23":"OECD_A23","OECD average-35":"OECD_A35",
    "OECD total":"OECD_TOT",
}
AGG = {"OECD","OECD_A23","OECD_A35","OECD_TOT"}

# annex_extract country-name aliases -> canonical PISA name (for the wide merge join)
ANNEX_ALIAS = {"Turkey":"T\u00fcrkiye","Czech Republic":"Czechia"}

def clean_name(nm):
    return nm.strip().rstrip("*").strip()

def col_letter(idx0):
    """0-based column index -> spreadsheet letter."""
    n = idx0 + 1; s = ""
    while n:
        n, r = divmod(n-1, 26); s = chr(65+r) + s
    return s

def isnum(x):
    return isinstance(x, (int, float)) and not isinstance(x, bool)

# ---------------------------------------------------------------- strict-OOXML reader
# CPI workbook uses the purl.oclc.org OOXML namespace which openpyxl/calamine reject.
def read_strict_xlsx_sheet(path, sheet_xml):
    z = zipfile.ZipFile(path)
    lname = lambda t: t.split("}")[-1]
    ss = []
    if "xl/sharedStrings.xml" in z.namelist():
        root = ET.fromstring(z.read("xl/sharedStrings.xml"))
        for si in root:
            if lname(si.tag) != "si":
                continue
            ss.append("".join(t.text or "" for t in si.iter() if lname(t.tag) == "t"))
    root = ET.fromstring(z.read(sheet_xml))
    rows = {}
    for r in root.iter():
        if lname(r.tag) != "row":
            continue
        for c in r:
            if lname(c.tag) != "c":
                continue
            ref = c.get("r"); t = c.get("t")
            ci = 0
            for ch in re.match(r"([A-Z]+)", ref).group(1):
                ci = ci*26 + (ord(ch)-64)
            ci -= 1
            ri = int(re.match(r"[A-Z]+(\d+)", ref).group(1))
            v = None
            for ch in c:
                if lname(ch.tag) == "v":
                    v = ch.text
                elif lname(ch.tag) == "is":
                    v = "".join(x.text or "" for x in ch.iter() if lname(x.tag) == "t")
            if t == "s" and v is not None:
                v = ss[int(v)]
            elif t not in ("str",) and v is not None:
                try: v = float(v)
                except (TypeError, ValueError): pass
            rows.setdefault(ri, {})[ci] = v
    maxr = max(rows) if rows else 0
    out = []
    for i in range(1, maxr+1):
        rd = rows.get(i, {})
        mc = max(rd) if rd else -1
        out.append([rd.get(j) for j in range(mc+1)])
    return out

# ---------------------------------------------------------------- (a) PISA scores
# domain -> (sheet, {cycle: mean_col_idx0})   SE column = mean_col+1
TREND = {
    "science":  ("Table I.B1.2a.36", {2006:1,2009:3,2012:5,2015:7,2018:9,2022:11,2025:13}),
    "reading":  ("Table I.B1.2a.37", {2000:1,2003:3,2006:5,2009:7,2012:9,2015:11,2018:13,2022:15,2025:17}),
    "math":     ("Table I.B1.2a.38", {2003:1,2006:3,2009:5,2012:7,2015:9,2018:11,2022:13,2025:15}),
    "cps2025":  ("Table I.B1.2a.4",  {2025:1}),
}

def build_scores_long():
    wb = openpyxl.load_workbook(TREND_XLSX, read_only=True, data_only=True)
    long_rows = []
    unmapped = set()
    for domain, (sheet, cyc_col) in TREND.items():
        ws = wb[sheet]
        started = False
        for rnum, row in enumerate(ws.iter_rows(values_only=True), start=1):
            c0 = row[0]
            if not (isinstance(c0, str) and c0.strip()):
                continue
            name = c0.strip()
            if name == "OECD average":
                started = True
            if not started:
                continue
            cname = clean_name(name)
            if cname not in ISO3:
                # footnotes / notes paragraphs fall here and are skipped
                if len(cname) < 60:
                    unmapped.add(cname)
                continue
            iso3 = ISO3[cname]
            for cycle, mcol in cyc_col.items():
                mean = row[mcol] if mcol < len(row) else None
                se   = row[mcol+1] if mcol+1 < len(row) else None
                if not isnum(mean):
                    continue  # 'm'/'c'/blank -> not a participation with a numeric mean
                cell = "%s!%s%d" % (sheet, col_letter(mcol), rnum)
                oflag = "" if iso3 in AGG else (1 if cname in OECD_MEMBERS else 0)
                long_rows.append({
                    "country_name": cname,
                    "iso3": iso3,
                    "oecd_member": oflag,
                    "cycle": cycle,
                    "domain": domain,
                    "mean": round(float(mean), 3),
                    "se": (round(float(se), 4) if isnum(se) else ""),
                    "source_file": TREND_REL,
                    "sheet": sheet,
                    "cell_ref": cell,
                })
    return long_rows, unmapped

def write_csv(path, fieldnames, rows):
    with open(path, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for r in rows:
            w.writerow(r)

# ---------------------------------------------------------------- annex_extract load
def load_annex():
    out = {}  # (iso3, cycle) -> dict
    with open(ANNEX, "r", encoding="utf-8-sig") as f:
        for r in csv.DictReader(f):
            nm = r["country"].strip()
            nm = ANNEX_ALIAS.get(nm, nm)
            iso3 = ISO3.get(nm)
            if not iso3:
                continue
            out[(iso3, int(r["cycle"]))] = {
                "coverage_index3": r["coverage_index3"],
                "overall_exclusion_pct": r["overall_exclusion_pct"],
                "school_rr_before": r["school_rr_before"],
                "school_rr_after": r["school_rr_after"],
                "student_rr": r["student_rr"],
                "asterisk_flag": r["asterisk_flag"],
            }
    return out

# ---------------------------------------------------------------- (a-wide)
CYCLES = [2000,2003,2006,2009,2012,2015,2018,2022,2025]
def build_wide(long_rows, annex):
    idx = {}  # (iso3,cycle) -> {name, oecd, domain:{mean,se}}
    for r in long_rows:
        key = (r["iso3"], r["cycle"])
        d = idx.setdefault(key, {"country_name": r["country_name"], "oecd_member": r["oecd_member"], "dom": {}})
        d["dom"][r["domain"]] = (r["mean"], r["se"])
    wide = []
    for (iso3, cycle), d in sorted(idx.items(), key=lambda kv: (kv[0][0], kv[0][1])):
        row = {
            "country_name": d["country_name"], "iso3": iso3, "oecd_member": d["oecd_member"],
            "cycle": cycle,
        }
        for dom in ("math","reading","science","cps2025"):
            m, s = d["dom"].get(dom, ("", ""))
            row[dom+"_mean"] = m
            row[dom+"_se"] = s
        a = annex.get((iso3, cycle), {})
        for col in ("coverage_index3","overall_exclusion_pct","school_rr_before",
                    "school_rr_after","student_rr","asterisk_flag"):
            row[col] = a.get(col, "")
        row["scores_source_file"] = TREND_REL
        row["annex_source"] = "data/derived/annex_extract.csv" if a else ""
        wide.append(row)
    return wide

# ---------------------------------------------------------------- (b) governance
def build_governance(iso3_set):
    # WGI cc + rl
    wgi = {}  # (iso3,year) -> dict
    wb = openpyxl.load_workbook(WGI_XLSX, read_only=True, data_only=True)
    for dim, prefix in (("cc","cc"), ("rl","rl")):
        ws = wb[dim]
        for rnum, r in enumerate(ws.iter_rows(values_only=True), start=1):
            code = r[2]; yr = r[5]
            if code not in iso3_set or not isinstance(yr, int):
                continue
            d = wgi.setdefault((code, yr), {})
            d[prefix+"_est"] = round(r[8], 6) if isnum(r[8]) else ""
            d[prefix+"_se"]  = round(r[9], 6) if isnum(r[9]) else ""
            if prefix == "cc":
                d["cc_pctrank"] = round(r[12], 4) if isnum(r[12]) else ""   # "Governance score (0-100)"
                d["wgi_cc_ref"] = "%s!%s%d" % (dim, col_letter(8), rnum)
            else:
                d["wgi_rl_ref"] = "%s!%s%d" % (dim, col_letter(8), rnum)
    # CPI timeseries
    cpi = {}  # (iso3,year) -> (score, cellref)
    data = read_strict_xlsx_sheet(CPI_XLSX, CPI_TS_SHEET_XML)
    hdr = data[3]
    year_col = {}
    for j, h in enumerate(hdr):
        m = re.match(r"CPI [Ss]core (\d{4})", str(h) if h else "")
        if m:
            year_col[int(m.group(1))] = j
    CPI_ALIAS = {"KSV":"XKX"}  # CPI Kosovo code -> canonical
    for rnum, r in enumerate(data[4:], start=5):
        if not r or not r[1]:
            continue
        code = CPI_ALIAS.get(r[1], r[1])
        if code not in iso3_set:
            continue
        for yr, j in year_col.items():
            v = r[j] if j < len(r) else None
            if isnum(v):
                cpi[(code, yr)] = (round(float(v), 2), "%s!%s%d" % (CPI_TS_SHEET_NAME, col_letter(j), rnum))
    # assemble annual rows
    rows = []
    for iso3 in sorted(iso3_set):
        for yr in range(1996, 2026):
            w = wgi.get((iso3, yr), {})
            c = cpi.get((iso3, yr))
            if not w and not c:
                continue
            rows.append({
                "iso3": iso3, "year": yr,
                "cc_est": w.get("cc_est",""), "cc_se": w.get("cc_se",""),
                "cc_pctrank": w.get("cc_pctrank",""),
                "rl_est": w.get("rl_est",""), "rl_se": w.get("rl_se",""),
                "cpi": (c[0] if c else ""),
                "wgi_source_file": (WGI_REL if w else ""),
                "wgi_cc_ref": w.get("wgi_cc_ref",""),
                "wgi_rl_ref": w.get("wgi_rl_ref",""),
                "cpi_source_file": (CPI_REL if c else ""),
                "cpi_ref": (c[1] if c else ""),
            })
    return rows

# ---------------------------------------------------------------- (c) analysis panel
CYCLE_INDEX = {2000:1,2003:2,2006:3,2009:4,2012:5,2015:6,2018:7,2022:8,2025:9}
def build_panel(wide, gov_rows):
    gov = {(g["iso3"], g["year"]): g for g in gov_rows}
    def gyear_wgi(cycle):   # WGI max year is 2024
        return min(cycle, 2024)
    panel = []
    for w in wide:
        iso3 = w["iso3"]; cycle = w["cycle"]
        y0w = gyear_wgi(cycle); y1w = y0w - 1
        g0 = gov.get((iso3, y0w), {}); g1 = gov.get((iso3, y1w), {})
        # CPI: use actual cycle year (2012-2025 available); prev = cycle-1
        cpi0 = gov.get((iso3, cycle), {}).get("cpi","")
        cpi1 = gov.get((iso3, cycle-1), {}).get("cpi","")
        row = dict(w)
        row["cycle_index"] = CYCLE_INDEX.get(cycle, "")
        row["gov_year"] = y0w
        row["gov_year_prev"] = y1w
        row["cc_est"] = g0.get("cc_est","");   row["cc_se"] = g0.get("cc_se","")
        row["cc_pctrank"] = g0.get("cc_pctrank","")
        row["rl_est"] = g0.get("rl_est","");   row["rl_se"] = g0.get("rl_se","")
        row["cc_est_prev"] = g1.get("cc_est",""); row["rl_est_prev"] = g1.get("rl_est","")
        row["cpi"] = cpi0; row["cpi_prev"] = cpi1
        panel.append(row)
    return panel

# ---------------------------------------------------------------- (d) validation
def approx(a, b, tol):
    try: return abs(float(a) - float(b)) <= tol
    except (TypeError, ValueError): return False

def lookup_long(long_rows, iso3, cycle, domain):
    for r in long_rows:
        if r["iso3"]==iso3 and r["cycle"]==cycle and r["domain"]==domain:
            return r["mean"]
    return None

def lookup_gov(gov_rows, iso3, year, field):
    for g in gov_rows:
        if g["iso3"]==iso3 and g["year"]==year:
            return g[field]
    return None

def validate(long_rows, gov_rows):
    checks = []
    def chk(label, cond):
        checks.append((label, "PASS" if cond else "FAIL"))
    # Turkiye math/read/sci (rounded to integer)
    exp = {2015:(420,428,425),2018:(454,466,468),2022:(453,456,476),2025:(462,472,494)}
    for yr,(m,r,s) in exp.items():
        chk("TUR math %d=%d"%(yr,m), round(lookup_long(long_rows,"TUR",yr,"math"))==m)
        chk("TUR read %d=%d"%(yr,r), round(lookup_long(long_rows,"TUR",yr,"reading"))==r)
        chk("TUR sci  %d=%d"%(yr,s), round(lookup_long(long_rows,"TUR",yr,"science"))==s)
    chk("TUR CPS 2025=473", round(lookup_long(long_rows,"TUR",2025,"cps2025"))==473)
    chk("OECD CPS 2025=500", round(lookup_long(long_rows,"OECD",2025,"cps2025"))==500)
    chk("OECD read 2025=461", round(lookup_long(long_rows,"OECD",2025,"reading"))==461)
    chk("OECD math 2025=463", round(lookup_long(long_rows,"OECD",2025,"math"))==463)
    chk("OECD sci  2025=482", round(lookup_long(long_rows,"OECD",2025,"science"))==482)
    chk("GEO 2025 math=416/read=384/sci=422",
        round(lookup_long(long_rows,"GEO",2025,"math"))==416 and
        round(lookup_long(long_rows,"GEO",2025,"reading"))==384 and
        round(lookup_long(long_rows,"GEO",2025,"science"))==422)
    chk("HUN 2025 math=459/read=452/sci=480",
        round(lookup_long(long_rows,"HUN",2025,"math"))==459 and
        round(lookup_long(long_rows,"HUN",2025,"reading"))==452 and
        round(lookup_long(long_rows,"HUN",2025,"science"))==480)
    chk("WGI cc TUR 2012~=0.1585", approx(lookup_gov(gov_rows,"TUR",2012,"cc_est"), 0.1585, 0.001))
    chk("WGI cc TUR 2024~=-0.5632", approx(lookup_gov(gov_rows,"TUR",2024,"cc_est"), -0.5632, 0.001))
    chk("CPI TUR 2013=50", approx(lookup_gov(gov_rows,"TUR",2013,"cpi"), 50, 0.001))
    chk("CPI TUR 2024=34", approx(lookup_gov(gov_rows,"TUR",2024,"cpi"), 34, 0.001))
    chk("CPI TUR 2025=31", approx(lookup_gov(gov_rows,"TUR",2025,"cpi"), 31, 0.001))
    return checks

# ---------------------------------------------------------------- main
def main():
    long_rows, unmapped = build_scores_long()
    annex = load_annex()
    # iso3 universe for governance = all real economies in the PISA scores (exclude aggregates)
    iso3_set = {r["iso3"] for r in long_rows if r["iso3"] not in AGG}
    gov_rows = build_governance(iso3_set)
    wide = build_wide(long_rows, annex)
    panel = build_panel(wide, gov_rows)

    write_csv(os.path.join(DERIVED,"pisa_scores_long.csv"),
              ["country_name","iso3","oecd_member","cycle","domain","mean","se",
               "source_file","sheet","cell_ref"], long_rows)
    wide_cols = ["country_name","iso3","oecd_member","cycle",
                 "math_mean","math_se","reading_mean","reading_se","science_mean","science_se",
                 "cps2025_mean","cps2025_se",
                 "coverage_index3","overall_exclusion_pct","school_rr_before","school_rr_after",
                 "student_rr","asterisk_flag","scores_source_file","annex_source"]
    write_csv(os.path.join(DERIVED,"pisa_scores_wide.csv"), wide_cols, wide)
    write_csv(os.path.join(DERIVED,"governance_annual.csv"),
              ["iso3","year","cc_est","cc_se","cc_pctrank","rl_est","rl_se","cpi",
               "wgi_source_file","wgi_cc_ref","wgi_rl_ref","cpi_source_file","cpi_ref"], gov_rows)
    panel_cols = wide_cols + ["cycle_index","gov_year","gov_year_prev",
                 "cc_est","cc_se","cc_pctrank","rl_est","rl_se","cc_est_prev","rl_est_prev",
                 "cpi","cpi_prev"]
    write_csv(os.path.join(DERIVED,"analysis_panel.csv"), panel_cols, panel)

    checks = validate(long_rows, gov_rows)
    print("=== VALIDATION ===")
    npass = sum(1 for _,s in checks if s=="PASS")
    for label, status in checks:
        print("  [%s] %s" % (status, label))
    print("  %d/%d PASS" % (npass, len(checks)))
    print("=== ROW COUNTS ===")
    print("  pisa_scores_long.csv :", len(long_rows))
    print("  pisa_scores_wide.csv :", len(wide))
    print("  governance_annual.csv:", len(gov_rows))
    print("  analysis_panel.csv   :", len(panel))
    print("  distinct economies (non-agg):", len(iso3_set))
    print("  economies w/ >=1 governance row:",
          len({g['iso3'] for g in gov_rows}))
    if unmapped:
        print("=== UNMAPPED name-like cells (skipped, expected footnotes) ===")
        for u in sorted(unmapped): print("   -", repr(u))
    return long_rows, wide, gov_rows, panel, checks

if __name__ == "__main__":
    main()
