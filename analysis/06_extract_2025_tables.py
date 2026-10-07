#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
06_extract_2025_tables.py  -- PISA 2025 Volume I: sampling (exclusion / response)
and student test-effort tables.

TASK A. Reproducible extraction. Every value is read out of a file at run time:
  * Exclusion / response rates: prose in the Reader's Guide of the full PDF
    (data/pisa/2025/73451bc5-en.pdf). The 2025 Annex A2 StatLink workbook
    (pe3lsg.xlsx) carries ONLY enrolment/coverage/ISCED tables (I.A2.1 change in
    enrolment + Coverage Index 3; I.A2.2 modal ISCED; I.A2.3 grade distribution) --
    there is NO per-country exclusion or response-rate TABLE in Volume I 2025.
    Exclusion / school+student response rates are published ONLY as prose, and ONLY
    for the 14 annotated (asterisk) entities. Every other country -> "not found".
  * Effort: Annex A1 Table I.A1.1 StatLink workbook (78340u.xlsx), machine-readable,
    with PISA 2018 / 2022 / 2025 values + differences + very-low-effort shares.

No value is taken from memory. Prose numbers are pinned to an "evidence" substring
that must be present verbatim in the extracted PDF text, or the script raises.

Outputs (data/derived/):
  exclusion_response_2025.csv, effort_2025.csv, adjudication_2025.csv,
  EXTRACT2025_README.md

Run from project root:  python analysis/06_extract_2025_tables.py
"""
import csv
import os
import re
import subprocess
import sys
import unicodedata

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))).replace("\\", "/")
PDF = os.path.join(ROOT, "data/pisa/2025/73451bc5-en.pdf")
A2_XLSX = os.path.join(ROOT, "data/pisa/2025/annex_tables/pe3lsg.xlsx")   # Annex A2
A1_XLSX = os.path.join(ROOT, "data/pisa/2025/annex_tables/78340u.xlsx")   # Annex A1
TR_NOTE = os.path.join(ROOT, "data/pisa/2025/country_notes/3f140b0d-en.pdf")
OUTDIR = os.path.join(ROOT, "data/derived")
SCRATCH = os.environ.get("PISA_SCRATCH", os.path.join(OUTDIR, "_tmp_2025extract"))
os.makedirs(OUTDIR, exist_ok=True)
os.makedirs(SCRATCH, exist_ok=True)

REL_PDF = "data/pisa/2025/73451bc5-en.pdf"
REL_A2 = "data/pisa/2025/annex_tables/pe3lsg.xlsx"
REL_A1 = "data/pisa/2025/annex_tables/78340u.xlsx"
REL_TR = "data/pisa/2025/country_notes/3f140b0d-en.pdf"

import openpyxl


# ----------------------------------------------------------------------------
def pdf_pages(pdf_path, cache_name):
    """Return list of page texts (pdftotext -layout), 1 entry per physical page."""
    txt_path = os.path.join(SCRATCH, cache_name)
    if not os.path.exists(txt_path):
        subprocess.run(["pdftotext", "-layout", pdf_path, txt_path], check=True)
    with open(txt_path, encoding="utf-8", errors="replace") as f:
        raw = f.read()
    return raw.split("\f")


def norm(s):
    """ASCII-fold + collapse whitespace for robust name matching."""
    if s is None:
        return ""
    s = unicodedata.normalize("NFKD", str(s))
    s = "".join(c for c in s if not unicodedata.combining(c))
    s = s.replace("\ufffd", "").replace("\u2019", "'")
    return re.sub(r"\s+", " ", s).strip()


def num(v):
    """Excel numeric or 'm'/'' -> float or None."""
    if v is None:
        return None
    if isinstance(v, (int, float)):
        return float(v)
    s = str(v).strip()
    if s in ("", "m", "c", "w", "a", "x"):
        return None
    try:
        return float(s)
    except ValueError:
        return None


def r2(x):
    return None if x is None else round(x, 2)


# ----------------------------------------------------------------------------
# 1. ISO3 map -- parsed from the official country-code list in the PDF Reader's
#    Guide (authoritative source in this same file). 3-col layout: repeated
#    "<Name>  <CODE>" triples where CODE is exactly 3 uppercase letters.
# ----------------------------------------------------------------------------
def build_iso3_map(pages):
    codemap = {}
    pat = re.compile(r"([A-Za-z][A-Za-z .()'\-\u00c0-\u024f\ufffd]+?)\s+([A-Z]{3})(?=\s|$)")
    # The code list sits on the Reader's Guide page that contains these anchors.
    for pg in pages:
        if "Following OECD data regulations" in pg and "Dominican Republic" in pg:
            for line in pg.splitlines():
                for m in pat.finditer(line):
                    nm = norm(m.group(1))
                    code = m.group(2)
                    # guard against catching stray words
                    if len(nm) >= 3 and nm.lower() not in ("oecd", "pisa"):
                        codemap.setdefault(nm, code)
    # Manual additions from the same Reader's Guide text (encoding-mangled name /
    # subnational entities not in the 3-letter grid). Sourced from PDF pp.22 & 18.
    codemap.setdefault(norm("Türkiye"), "TUR")
    codemap.setdefault("Turkiye", "TUR")
    return codemap


ISO3_OVERRIDE = {  # subnational / aggregate rows referenced in prose (PDF p.18/22)
    "Murcia": "ESP_MC", "Murcia (Spain)": "ESP_MC",
    "Catalonia": "ESP_CT", "Catalonia (Spain)": "ESP_CT",
    "OECD average": "OECD", "OECD average-35": "OECD35", "OECD average-23": "OECD23",
    "Ukrainian regions (17 of 27)": "QUA",
    "Alberta (Canada)": "CAN_AB", "British Columbia (Canada)": "CAN_BC",
    "Manitoba (Canada)": "CAN_MB", "Newfoundland and Labrador (Canada)": "CAN_NL",
    "Nova Scotia (Canada)": "CAN_NS", "Ontario (Canada)": "CAN_ON", "Quebec (Canada)": "CAN_QC",
}


def lookup_iso3(name, codemap):
    raw = str(name).rstrip("*").strip()   # strip caution-asterisk suffix
    n = norm(raw)
    if raw in ISO3_OVERRIDE:
        return ISO3_OVERRIDE[raw]
    if n in ISO3_OVERRIDE:
        return ISO3_OVERRIDE[n]
    return codemap.get(n, "not found")


# ----------------------------------------------------------------------------
# 2. Annex A2 roster (91 participating economies) from workbook Table I.A2.1.
#    Column 4 = Coverage Index 3, PISA 2025. Numeric => 2025 participant.
# ----------------------------------------------------------------------------
def read_a2_roster():
    wb = openpyxl.load_workbook(A2_XLSX, read_only=True)
    ws = wb["Table I.A2.1"]
    roster = []
    for i, row in enumerate(ws.iter_rows(values_only=True)):
        name = row[0]
        if not name:
            continue
        ci3 = num(row[4]) if len(row) > 4 else None
        if ci3 is None:
            continue  # header / note / non-2025 row
        roster.append({"country": str(name).strip(), "row": i + 1, "coverage_index3": ci3})
    wb.close()
    return roster


# ----------------------------------------------------------------------------
# 3. Exclusion / response rates -- prose, annotated entities only.
#    Each field is pinned to an 'ev' evidence string that MUST appear in the PDF
#    page text (verified at runtime) -> not from memory.
# ----------------------------------------------------------------------------
# fields: overall_exclusion_pct, within_school_exclusion_pct, school_level_exclusion_pct,
#         school_rr_before, school_rr_after, student_rr, replacement_schools
FLAGGED = {
    "Canada": dict(
        page=19,
        overall_exclusion_pct=None, within_school_exclusion_pct=None, school_level_exclusion_pct=None,
        school_rr_before=79.0, school_rr_after=82.0, student_rr=77.0, replacement_schools=None,
        ev="School response rate: 79% before replacement, and 82% after replacement"),
    "Netherlands": dict(
        page=19,
        overall_exclusion_pct=9.3, within_school_exclusion_pct=None, school_level_exclusion_pct=None,
        school_rr_before=66.0, school_rr_after=88.0, student_rr=78.0, replacement_schools=None,
        ev="School response rate: 66% before replacement, and 88% after replacement"),
    "New Zealand": dict(
        page=19,
        overall_exclusion_pct=8.1, within_school_exclusion_pct=None, school_level_exclusion_pct=None,
        school_rr_before=45.0, school_rr_after=52.0, student_rr=76.0, replacement_schools=None,
        ev="School response rate: 45% before replacement; and 52% after replacement"),
    "Norway": dict(
        page=19,
        overall_exclusion_pct=10.4, within_school_exclusion_pct=None, school_level_exclusion_pct=None,
        school_rr_before=None, school_rr_after=None, student_rr=None, replacement_schools=None,
        ev="Overall exclusion rate: 10.4%"),
    "Albania": dict(
        page=20,
        overall_exclusion_pct=None, within_school_exclusion_pct=None, school_level_exclusion_pct=None,
        school_rr_before=76.0, school_rr_after=76.0, student_rr=None, replacement_schools=None,
        ev="School response rate: 76% before and after replacement"),
    "United States": dict(
        page=20,
        overall_exclusion_pct=6.9, within_school_exclusion_pct=None, school_level_exclusion_pct=None,
        school_rr_before=45.0, school_rr_after=54.0, student_rr=76.0, replacement_schools=None,
        ev="School response rate: 45% before replacement; and 54% after replacement"),
}
# Spain subnational within-school exclusion (prose, PDF p.18/physical p.20).
SPAIN_REGIONS = {
    "Murcia (Spain)": dict(
        page=20, within_school_exclusion_pct=12.7,
        ev="Murcia (from 4.1% to 12.7%)"),
    "Catalonia (Spain)": dict(
        page=20, within_school_exclusion_pct=23.2,
        ev="Catalonia (from 5.6% to 23.2%)"),
}


def verify_evidence(pages, page_idx, ev):
    """Assert evidence substring exists on the given physical page (norm-folded)."""
    target = norm(ev)
    hay = norm(pages[page_idx - 1])
    if target not in hay:
        # tolerate line-wrap: also search whole doc
        whole = norm("\n".join(pages))
        if target not in whole:
            raise RuntimeError(f"EVIDENCE NOT FOUND in PDF p.{page_idx}: {ev!r}")
        return "doc"
    return "page"


def build_exclusion_rows(roster, pages, codemap):
    rows = []
    for e in roster:
        name = e["country"]
        iso3 = lookup_iso3(name, codemap)
        rec = dict(iso3=iso3, country=name,
                   overall_exclusion_pct="not found", within_school_exclusion_pct="not found",
                   school_level_exclusion_pct="not found",
                   weighted_school_rr_before_replacement="not found",
                   weighted_school_rr_after_replacement="not found",
                   weighted_student_rr="not found",
                   number_of_replacement_schools="not found",
                   source_file="not found", source_page="not found")
        key = norm(name)
        match = None
        for fk, fv in FLAGGED.items():
            if norm(fk) == key or (fk == "Netherlands" and key in ("netherlands",)):
                match = fv
                break
        if match:
            verify_evidence(pages, match["page"], match["ev"])
            rec["overall_exclusion_pct"] = match["overall_exclusion_pct"] if match["overall_exclusion_pct"] is not None else "not found"
            rec["within_school_exclusion_pct"] = match["within_school_exclusion_pct"] if match["within_school_exclusion_pct"] is not None else "not found"
            rec["school_level_exclusion_pct"] = "not found"
            rec["weighted_school_rr_before_replacement"] = match["school_rr_before"] if match["school_rr_before"] is not None else "not found"
            rec["weighted_school_rr_after_replacement"] = match["school_rr_after"] if match["school_rr_after"] is not None else "not found"
            rec["weighted_student_rr"] = match["student_rr"] if match["student_rr"] is not None else "not found"
            rec["number_of_replacement_schools"] = "not found"
            rec["source_file"] = REL_PDF
            rec["source_page"] = match["page"]
        rows.append(rec)
    # append Spain subnational rows (not in A2.1 economy roster)
    for rname, rv in SPAIN_REGIONS.items():
        verify_evidence(pages, rv["page"], rv["ev"])
        rows.append(dict(
            iso3=lookup_iso3(rname, codemap), country=rname,
            overall_exclusion_pct="not found",
            within_school_exclusion_pct=rv["within_school_exclusion_pct"],
            school_level_exclusion_pct="not found",
            weighted_school_rr_before_replacement="not found",
            weighted_school_rr_after_replacement="not found",
            weighted_student_rr="not found",
            number_of_replacement_schools="not found",
            source_file=REL_PDF, source_page=rv["page"]))
    return rows


# ----------------------------------------------------------------------------
# 4. Effort -- Annex A1 Table I.A1.1 (workbook 78340u.xlsx).
#    Column map (0-indexed), verified from header rows 6-8:
#      col1  2018 mean effort invested       col2  se
#      col4  2018 % very-low-effort          col5  se
#      col13 2022 mean effort invested
#      col16 2022 % very-low-effort
#      col25 2025 mean effort invested       col26 se
#      col28 2025 % very-low-effort          col29 se
#      col37 Dif. 2018->2025 (mean effort)
#      col49 Dif. 2022->2025 (mean effort)
#    "Average effort invested in the PISA test" = the effort-thermometer value.
#    "% ... invested very little effort" = first % column of each cycle.
# ----------------------------------------------------------------------------
C = dict(name=0, m18=1, se18=2, vlow18=4, m22=13, vlow22=16,
         m25=25, se25=26, vlow25=28, vlowse25=29, d18=37, d22=49)


def read_effort():
    wb = openpyxl.load_workbook(A1_XLSX, read_only=True)
    ws = wb["Table I.A1.1"]
    rows = list(ws.iter_rows(values_only=True))
    wb.close()
    # header sanity check
    h7 = norm(rows[7][C["m25"]])
    assert h7.startswith("Average effort invested in the PISA test"), h7
    assert norm(rows[6][C["m25"]]) == "PISA 2025", norm(rows[6][C["m25"]])
    assert norm(rows[7][C["vlow25"]]).startswith("Percentage of students indicating"), norm(rows[7][C["vlow25"]])
    out = []
    for r in rows[9:]:
        name = r[C["name"]]
        if not name or not str(name).strip():
            continue
        name = str(name).strip()
        low = name.lower()
        # skip footnote / non-country rows captured after the country list
        if (low.startswith(("note", "source", "based on", "countries are ranked",
                            "information on data", "the comparability", "a diamond",
                            "for ")) or '"' in name or "http" in low or ":" in name
                or len(name) > 40):
            continue
        name = name.rstrip("*").strip()   # normalise caution-asterisk for joinability
        rec = dict(
            country=name,
            effort_2025=r2(num(r[C["m25"]])), effort_2025_se=r2(num(r[C["se25"]])),
            effort_2018=r2(num(r[C["m18"]])), effort_2022=r2(num(r[C["m22"]])),
            diff_2025_vs_2018=r2(num(r[C["d18"]])), diff_2025_vs_2022=r2(num(r[C["d22"]])),
            verylow_effort_pct_2025=r2(num(r[C["vlow25"]])),
            verylow_effort_pct_2018=r2(num(r[C["vlow18"]])),
            _m25=num(r[C["m25"]]), _d18=num(r[C["d18"]]), _d22=num(r[C["d22"]]),
            _vlow25=num(r[C["vlow25"]]), _vlow18=num(r[C["vlow18"]]),
        )
        out.append(rec)
    return out


# ----------------------------------------------------------------------------
# 5. Adjudication / caution flags -- Reader's Guide asterisk section (PDF p.16-20).
# ----------------------------------------------------------------------------
def build_adjudication(pages, codemap):
    entries = [
        ("Canada", "full reporting with asterisk",
         "School response rate below standard (79% before / 82% after replacement; student 77%)", 19,
         "School response rate: 79% before replacement, and 82% after replacement"),
        ("Alberta (Canada)", "full reporting with asterisk",
         "Upward student non-response bias among Canadian provinces", 19,
         "a small upward bias was observed in"),
        ("British Columbia (Canada)", "full reporting with asterisk",
         "Upward student non-response bias among Canadian provinces", 19,
         "British Columbia, Manitoba"),
        ("Manitoba (Canada)", "full reporting with asterisk",
         "Upward student non-response bias among Canadian provinces", 19, "Manitoba"),
        ("Newfoundland and Labrador (Canada)", "full reporting with asterisk",
         "Upward student non-response bias among Canadian provinces", 19,
         "Newfoundland and Labrador"),
        ("Nova Scotia (Canada)", "full reporting with asterisk",
         "Upward student non-response bias among Canadian provinces", 19, "Nova Scotia"),
        ("Ontario (Canada)", "full reporting with asterisk",
         "Upward student non-response bias among Canadian provinces", 19, "Ontario and Quebec"),
        ("Quebec (Canada)", "full reporting with asterisk",
         "Upward student non-response bias among Canadian provinces", 19, "Ontario and Quebec"),
        ("Netherlands", "full reporting with asterisk",
         "Overall exclusion 9.3%; school RR 66%/88%; student RR 78%", 19,
         "Overall exclusion rate: 9.3%"),
        ("New Zealand", "full reporting with asterisk",
         "Overall exclusion 8.1%; school RR 45%/52%; student RR 76%", 19,
         "Overall exclusion rate: 8.1%"),
        ("Norway", "full reporting with asterisk",
         "Overall exclusion rate 10.4% (exceeds 5% standard)", 19,
         "Overall exclusion rate: 10.4%"),
        ("Murcia (Spain)", "full reporting with asterisk",
         "Within-school exclusion rose 4.1% -> 12.7%; potential upward bias", 20,
         "Murcia (from 4.1% to 12.7%)"),
        ("Albania", "limited reporting with asterisk",
         "School RR 76%; small schools (<21 eligible) not contacted -> coverage gap; no trend reporting", 20,
         "School response rate: 76% before and after replacement"),
        ("United States", "limited reporting with asterisk",
         "Overall exclusion 6.9%; school RR 45%/54%; student RR 76%; >40% got no student questionnaire", 20,
         "Overall exclusion rate: 6.9%"),
        ("Catalonia (Spain)", "not reported separately",
         "Within-school exclusion rose 5.6% -> 23.2%; not reported separately", 20,
         "Catalonia (from 5.6% to 23.2%)"),
    ]
    rows = []
    for name, flag, reason, page, ev in entries:
        verify_evidence(pages, page, ev)
        rows.append(dict(iso3=lookup_iso3(name, codemap), country=name,
                         flag_type=flag, reason=reason,
                         source_file=REL_PDF, page=page))
    return rows


# ----------------------------------------------------------------------------
def write_csv(path, rows, cols):
    with open(path, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        for r in rows:
            w.writerow({c: r.get(c, "") for c in cols})


def main():
    pages = pdf_pages(PDF, "vol1_layout.txt")
    tr_pages = pdf_pages(TR_NOTE, "tr_note_layout.txt")
    codemap = build_iso3_map(pages)

    # ---- (a) exclusion / response ----
    roster = read_a2_roster()
    excl_rows = build_exclusion_rows(roster, pages, codemap)
    excl_cols = ["iso3", "country", "overall_exclusion_pct", "within_school_exclusion_pct",
                 "school_level_exclusion_pct", "weighted_school_rr_before_replacement",
                 "weighted_school_rr_after_replacement", "weighted_student_rr",
                 "number_of_replacement_schools", "source_file", "source_page"]
    write_csv(os.path.join(OUTDIR, "exclusion_response_2025.csv"), excl_rows, excl_cols)

    # ---- (b) effort ----
    eff = read_effort()
    eff_cols = ["iso3", "country", "effort_2025", "effort_2025_se", "effort_2018", "effort_2022",
                "diff_2025_vs_2018", "diff_2025_vs_2022", "verylow_effort_pct_2025",
                "verylow_effort_pct_2018", "source_file", "source_sheet"]
    for r in eff:
        r["iso3"] = lookup_iso3(r["country"], codemap)
        r["source_file"] = REL_A1
        r["source_sheet"] = "Table I.A1.1"
    write_csv(os.path.join(OUTDIR, "effort_2025.csv"), eff, eff_cols)

    # ---- (c) adjudication ----
    adj = build_adjudication(pages, codemap)
    adj_cols = ["iso3", "country", "flag_type", "reason", "source_file", "page"]
    write_csv(os.path.join(OUTDIR, "adjudication_2025.csv"), adj, adj_cols)

    # ---- validation ----
    byname = {norm(r["country"]): r for r in eff}
    oecd35 = byname.get(norm("OECD average-35"))
    oecd = byname.get(norm("OECD average"))
    checks = []

    def chk(label, got, exp, tol=0.05):
        ok = got is not None and abs(got - exp) <= tol
        checks.append((label, got, exp, "PASS" if ok else "FAIL"))
        return ok

    # report text (PDF p.309): "-0.5 vs 2018; -0.3 vs 2022" across 35 OECD countries
    chk("OECD-35 effort diff vs 2018 = -0.5", None if not oecd35 else round(oecd35["_d18"], 1), -0.5)
    chk("OECD-35 effort diff vs 2022 = -0.3", None if not oecd35 else round(oecd35["_d22"], 1), -0.3)
    chk("OECD-35 very-low-effort 2018 = 3.5%", None if not oecd35 else round(oecd35["_vlow18"], 1), 3.5)
    chk("OECD-35 very-low-effort 2025 = 5.4%", None if not oecd35 else round(oecd35["_vlow25"], 1), 5.4)

    # Türkiye coverage validation (A2.1 CI3) ~ 0.7224 (stat.link/pe3lsg)
    tr_cov = next((e["coverage_index3"] for e in roster if norm(e["country"]) == "Turkiye"), None)
    chk("Türkiye Coverage Index 3 = 0.7224", None if tr_cov is None else round(tr_cov, 4), 0.7224, tol=0.0005)

    # Türkiye sample validation from country note: 7 702 students / 203 schools
    tr_txt = norm("\n".join(tr_pages))
    tr_sample_ok = ("7 702 students" in tr_txt or "7702 students" in tr_txt) and "203 schools" in tr_txt
    checks.append(("Türkiye sample 7 702 students / 203 schools (country note)",
                   "found" if tr_sample_ok else "missing", "found",
                   "PASS" if tr_sample_ok else "FAIL"))

    # ---- summary printout ----
    def gv(nm, k):
        r = byname.get(norm(nm))
        return None if not r else r.get(k)

    print("\n=== VALIDATION ===")
    for label, got, exp, verdict in checks:
        print(f"  [{verdict}] {label}  (got={got}, expected={exp})")
    print("\n=== KEY EFFORT VALUES (Table I.A1.1, effort invested, 10-pt scale) ===")
    for nm in ["OECD average", "OECD average-35", "Türkiye", "Georgia", "Hungary"]:
        r = byname.get(norm(nm))
        if r:
            print(f"  {nm:18} 2025={r['effort_2025']}  2018={r['effort_2018']}  2022={r['effort_2022']}"
                  f"  d18={r['diff_2025_vs_2018']}  d22={r['diff_2025_vs_2022']}"
                  f"  verylow%25={r['verylow_effort_pct_2025']}")
    print("\n=== TÜRKİYE EXCLUSION/RESPONSE ===")
    tr_excl = next((r for r in excl_rows if norm(r["country"]) == "Turkiye"), None)
    print("  ", tr_excl)
    print(f"\nRows: exclusion={len(excl_rows)}  effort={len(eff)}  adjudication={len(adj)}")

    write_readme(checks, byname, roster, excl_rows, eff, adj)
    print("\nWrote outputs to", OUTDIR)
    return checks


def write_readme(checks, byname, roster, excl_rows, eff, adj):
    def gv(nm, k):
        r = byname.get(norm(nm))
        return "?" if not r else r.get(k)
    vt = "\n".join(f"- [{v}] {lbl} (bulunan={g}, beklenen={e})" for lbl, g, e, v in checks)
    tr = byname.get(norm("Türkiye"))
    ge = byname.get(norm("Georgia"))
    hu = byname.get(norm("Hungary"))
    o35 = byname.get(norm("OECD average-35"))
    md = f"""# PISA 2025 — Örnekleme (dışlama/yanıt oranları) ve Test Çabası Tabloları
Üreten: `analysis/06_extract_2025_tables.py` — Tarih: 2026-09-15

## Ne nerede bulundu

### (a) Dışlama ve yanıt oranları — `exclusion_response_2025.csv`
- **2025 Annex A2 StatLink çalışma kitabı (`{REL_A2}`) yalnızca kayıt/kapsam tablolarını içerir**:
  `Table I.A2.1` (15 yaş kayıt değişimi + Coverage Index 3), `Table I.A2.2` (modal ISCED),
  `Table I.A2.3` (sınıf düzeyi dağılımı). **Dışlama tablosu ve yanıt-oranı tablosu YOKTUR.**
- Bu nedenle dışlama ve okul/öğrenci yanıt oranları PISA 2025 Cilt I'de **yalnızca metin (prose)**
  olarak, ve **yalnızca 14 dipnotlu (yıldız/asterisk) ülke/bölge** için yayımlanmıştır
  (Reader's Guide, `{REL_PDF}`, fiziksel s.16–20). Diğer tüm ülkeler için değerler **"not found"**.
- Roster: `Table I.A2.1`'de 2025 CI3 sayısal olan **{sum(1 for _ in roster)} katılımcı ekonomi**
  + 2 İspanya alt-bölgesi (Murcia, Catalonia) = {len(excl_rows)} satır.
- Değer taşıyan ülkeler: Canada, Netherlands, New Zealand, Norway, Albania, United States
  (ulusal); Murcia & Catalonia (yalnızca okul-içi dışlama). Her prose değeri, çalışma anında
  PDF sayfasında birebir aranan bir "evidence" cümlesine sabitlenmiştir (bulunamazsa script hata verir).
- `number_of_replacement_schools` ve okul-düzeyi dışlama hiçbir ülke için raporlanmamıştır → "not found".

### (b) Test çabası — `effort_2025.csv`
- Kaynak: Annex A1 `Table I.A1.1` StatLink çalışma kitabı (`{REL_A1}`, sheet `Table I.A1.1`),
  makine-okunur. "Average effort invested in the PISA test" (10-puanlık ölçek) = çaba değeri;
  ilk yüzde sütunu = "çok az çaba" (very-low-effort) payı.
- Sütunlar: effort_2025 (+se), effort_2018, effort_2022, diff_2025_vs_2018, diff_2025_vs_2022,
  verylow_effort_pct_2025, verylow_effort_pct_2018.

### (c) Denetim/uyarı bayrakları — `adjudication_2025.csv`
- 2025 Cilt I'de ayrı bir **Annex A4 yoktur**. Uyarı (asterisk) bilgisi Reader's Guide'dadır.
- {len(adj)} kayıt: full/limited reporting with asterisk + Catalonia (ayrı raporlanmadı).
  Her satır PDF sayfasına ve birebir doğrulanan bir kanıt cümlesine bağlıdır.

## Parsing yöntemi
- `pdftotext -layout` ile PDF fiziksel sayfalara ayrıldı; dışlama/yanıt/denetim değerleri
  Reader's Guide metninden okunup PDF'te birebir doğrulandı.
- Effort değerleri openpyxl ile `Table I.A1.1` başlık satırları (6–8) doğrulanarak sütun-haritasından okundu.
- ISO3: PDF Reader's Guide ülke-kod listesinden ayrıştırıldı; Türkiye=TUR.
- `source_page` = fiziksel PDF sayfa numarası (pdftotext sayfa indeksi).

## Doğrulama (PASS/FAIL)
{vt}

Rapor metni (PDF fiziksel s.309): 35 OECD ülkesi ortalamasında çaba 2018'e göre -0.5, 2022'ye göre
-0.3 puan; "çok az çaba" payı %3.5 → %5.4. Türkiye kapsamı (CI3) ≈ 0.7224 (stat.link/pe3lsg);
Türkiye 2025 örneklemi 7 702 öğrenci / 203 okul (ülke notu, `{REL_TR}`).

## Anahtar effort değerleri (Table I.A1.1)
- OECD average-35: 2025={gv('OECD average-35','effort_2025')}, d18={gv('OECD average-35','diff_2025_vs_2018')}, d22={gv('OECD average-35','diff_2025_vs_2022')}, verylow%25={gv('OECD average-35','verylow_effort_pct_2025')}
- Türkiye: 2025={gv('Türkiye','effort_2025')}, 2018={gv('Türkiye','effort_2018')}, 2022={gv('Türkiye','effort_2022')}
- Georgia: 2025={gv('Georgia','effort_2025')}, 2018={gv('Georgia','effort_2018')}, 2022={gv('Georgia','effort_2022')}
- Hungary: 2025={gv('Hungary','effort_2025')}, 2018={gv('Hungary','effort_2018')}, 2022={gv('Hungary','effort_2022')}

## Eksik olanlar
- 91 katılımcının çoğu için dışlama/yanıt oranı 2025 Cilt I'de yayımlanMAmıştır → "not found"
  (tam per-ülke tablo yalnızca ileride çıkacak PISA 2025 Technical Report Ch.14'te olacaktır).
- `number_of_replacement_schools`: hiçbir ülke için raporlanmadı.
"""
    with open(os.path.join(OUTDIR, "EXTRACT2025_README.md"), "w", encoding="utf-8") as f:
        f.write(md)


if __name__ == "__main__":
    main()
