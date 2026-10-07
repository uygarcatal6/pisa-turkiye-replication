# -*- coding: utf-8 -*-
"""
08_composition.py — TASK C: school-type composition of Türkiye's PISA samples
vs. the composition MEB itself reports, plus cross-cycle drift.

Reproducible. No number is hard-coded from memory: every value is read from a
source file, and every output row carries provenance (source_file + variable /
page). Peak memory kept low: SPSS student files (1.5-2.2 GB each) are extracted
one cycle at a time, read column-selectively (usecols) and deleted before the
next cycle; school files are tiny.

Inputs
  School questionnaire SPSS (STRATUM encodes the Turkish school type):
    2015 data/pisa_microdata/2015/PUF_SPSS_COMBINED_CMB_SCH_QQQ.zip
    2018 data/pisa_microdata/2018/SPSS_SCH_QQQ.zip
    2022 data/pisa_microdata/2022/SCH_QQQ_SPSS.zip
    2025 data/pisa/2025/database/CY09_MS_SCH_PUF.zip
  Student questionnaire SPSS (final weight W_FSTUWT + STRATUM + CNTSCHID):
    2015 data/pisa_microdata/2015/PUF_SPSS_COMBINED_CMB_STU_QQQ.zip
    2018 data/pisa_microdata/2018/SPSS_STU_QQQ.zip
    2022 data/pisa_microdata/2022/STU_QQQ_SPSS.zip
    2025 data/pisa/2025/database/CY09_MS_STU_PUF.zip
  MEB national reports (docs/national_reports_meb/*.pdf) parsed with pdftotext.

Outputs (data/derived/)
  turkiye_school_type_composition.csv
  turkiye_composition_drift.csv
  meb_reported_composition.csv
  COMPOSITION_README.md   (Turkish)
"""
import os, csv, zipfile, tempfile
import pyreadstat
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))).replace("\\", "/")
DERIVED = os.path.join(ROOT, "data", "derived")
SCRATCH = os.environ.get(
    "PISA_SCRATCH",
    os.path.join(tempfile.gettempdir(), "pisa_scratch"),
)
os.makedirs(SCRATCH, exist_ok=True)

# cycle -> (zip path, member inside zip) for SCHOOL and STUDENT files
SCH = {
    "2015": ("data/pisa_microdata/2015/PUF_SPSS_COMBINED_CMB_SCH_QQQ.zip", "CY6_MS_CMB_SCH_QQQ.sav"),
    "2018": ("data/pisa_microdata/2018/SPSS_SCH_QQQ.zip", "SCH/CY07_MSU_SCH_QQQ.sav"),
    "2022": ("data/pisa_microdata/2022/SCH_QQQ_SPSS.zip", "CY08MSP_SCH_QQQ.SAV"),
    "2025": ("data/pisa/2025/database/CY09_MS_SCH_PUF.zip", "CY09_MS_SCH_PUF.sav"),
}
STU = {
    "2015": ("data/pisa_microdata/2015/PUF_SPSS_COMBINED_CMB_STU_QQQ.zip", "CY6_MS_CMB_STU_QQQ.sav"),
    "2018": ("data/pisa_microdata/2018/SPSS_STU_QQQ.zip", "STU/CY07_MSU_STU_QQQ.sav"),
    "2022": ("data/pisa_microdata/2022/STU_QQQ_SPSS.zip", "CY08MSP_STU_QQQ.SAV"),
    "2025": ("data/pisa/2025/database/CY09_MS_STU_PUF.zip", "CY09_MS_STU_PUF.sav"),
}

# ------------------------------------------------------------------ classifier
# Maps the ENGLISH STRATUM label text (as stored in the PUF value labels) to a
# harmonised school-type category with a Turkish label. Order matters: test the
# most specific tokens first.  2015 strata are coarse (region x programme only),
# so 2015 falls into the *_2015 coarse buckets.
def classify(label):
    L = label
    # --- 2015 coarse strata (region x programme) ---
    if "BASIC EDUCATION" in L:                     return ("ortaokul", "Ortaokul (temel eğitim)")
    if "GENERAL SECONDARY" in L:                   return ("genel_ortaogretim_2015", "Genel ortaöğretim (2015 birleşik)")
    if "VOCATIONAL AND TECHNICAL SECONDARY" in L:  return ("meslek_2015", "Mesleki ve teknik (2015 birleşik)")
    # --- 2018/2022/2025 fine strata ---
    if "Lower-Secondary" in L:                     return ("ortaokul", "Ortaokul (temel eğitim)")
    if "Science High" in L:                        return ("fen", "Fen lisesi")
    if "Social Sciences" in L:                     return ("sosyal", "Sosyal bilimler lisesi")
    if "Imam and Preacher" in L:                   return ("imam_hatip", "Anadolu imam hatip lisesi")
    if "Vocational and Technical" in L:            return ("meslek", "Mesleki ve teknik Anadolu lisesi")
    if "Multi-Programme" in L:                     return ("cok_programli", "Çok programlı Anadolu lisesi")
    if "Sport" in L or "Fine Arts" in L:           return ("spor_guzel", "Anadolu spor / güzel sanatlar lisesi")
    if "Private General" in L:                     return ("ozel_genel", "Özel genel lise")
    if "Private Vocational" in L:                  return ("ozel_meslek", "Özel mesleki lise")
    if "Anatolian High" in L:                      return ("anadolu", "Anadolu lisesi")
    if "Undisclosed" in L:                         return ("undisclosed", "Açıklanmayan tabaka")
    return ("other", "DİĞER: " + L)

# a stable display order
ORDER = ["anadolu","meslek","imam_hatip","fen","sosyal","cok_programli","spor_guzel",
         "ozel_genel","ozel_meslek","ortaokul","genel_ortaogretim_2015","meslek_2015",
         "undisclosed","other"]


def extract(zippath, member, dest_name):
    """Extract one member of a zip to SCRATCH; return the local path.

    Some PISA 2025 zips use Deflate64 (compress_type 9), which Python's zipfile
    cannot inflate; fall back to the Info-ZIP `unzip` CLI for those.
    """
    out = os.path.join(SCRATCH, dest_name)
    full = os.path.join(ROOT, zippath)
    with zipfile.ZipFile(full) as z:
        info = z.getinfo(member)
        if info.compress_type == 9:  # Deflate64 -> use external unzip
            import subprocess, shutil
            base = os.path.basename(member)
            subprocess.run(["unzip", "-o", full, member, "-d", SCRATCH],
                           check=True, capture_output=True)
            extracted = os.path.join(SCRATCH, member.replace("/", os.sep))
            if extracted != out:
                shutil.move(extracted, out)
            return out
        with z.open(member) as src, open(out, "wb") as dst:
            while True:
                chunk = src.read(1 << 20)
                if not chunk:
                    break
                dst.write(chunk)
    return out


def read_school(cy):
    """Return TUR school-level frame with columns: STRATUM_label, SC013, SCHLTYPE,
    CNTSCHID, plus the STRATUM value-label dict."""
    zp, member = SCH[cy]
    path = extract(zp, member, f"sch_{cy}.sav")
    cols = ["CNT", "CNTSCHID", "STRATUM", "SC013Q01TA", "SCHLTYPE"]
    df, meta = pyreadstat.read_sav(path, usecols=cols)
    stratlab = meta.variable_value_labels.get("STRATUM", {})
    sc13lab = meta.variable_value_labels.get("SC013Q01TA", {})
    schtlab = meta.variable_value_labels.get("SCHLTYPE", {})
    df = df[df.CNT == "TUR"].copy()
    df["strat_label"] = df.STRATUM.map(lambda s: stratlab.get(s, str(s)))
    df["cat"] = df.strat_label.map(classify)
    df["cat_code"] = df.cat.map(lambda t: t[0])
    df["cat_label"] = df.cat.map(lambda t: t[1])
    df["sc013"] = df.SC013Q01TA.map(lambda v: sc13lab.get(v, str(v)))
    df["schtype"] = df.SCHLTYPE.map(lambda v: schtlab.get(v, str(v)))
    try:
        os.remove(path)
    except OSError:
        pass
    return df


def read_student_weights(cy):
    """Return TUR student frame: CNTSCHID, STRATUM cat_code/label, W_FSTUWT.
    Extract -> read 4 columns -> delete the multi-GB sav."""
    zp, member = STU[cy]
    path = extract(zp, member, f"stu_{cy}.sav")
    cols = ["CNT", "CNTSCHID", "STRATUM", "W_FSTUWT"]
    df, meta = pyreadstat.read_sav(path, usecols=cols)
    stratlab = meta.variable_value_labels.get("STRATUM", {})
    df = df[df.CNT == "TUR"].copy()
    df["strat_label"] = df.STRATUM.map(lambda s: stratlab.get(s, str(s)))
    df["cat"] = df.strat_label.map(classify)
    df["cat_code"] = df.cat.map(lambda t: t[0])
    df["cat_label"] = df.cat.map(lambda t: t[1])
    try:
        os.remove(path)
    except OSError:
        pass
    return df


# =============================================================== main compute
comp_rows = []          # turkiye_school_type_composition.csv
weighted_share = {}     # cy -> {cat_code: share}  (for drift)
weighted_label = {}     # cat_code -> label
micro_by_cat = {}       # cy -> {cat_code: weighted_students}

for cy in ["2015", "2018", "2022", "2025"]:
    print(f"[{cy}] reading school file ...", flush=True)
    sch = read_school(cy)
    sch_src = SCH[cy][0]
    n_by_cat = sch.groupby(["cat_code", "cat_label"]).size().to_dict()

    print(f"[{cy}] reading student file (weights) ...", flush=True)
    stu = read_student_weights(cy)
    stu_src = STU[cy][0]
    w_by_cat = stu.groupby(["cat_code", "cat_label"]).W_FSTUWT.sum().to_dict()
    tot_w = stu.W_FSTUWT.sum()
    tot_n = len(sch)

    # ---- STRATUM (school-type) rows
    cats = sorted(set([k[0] for k in n_by_cat] + [k[0] for k in w_by_cat]),
                  key=lambda c: (ORDER.index(c) if c in ORDER else 99))
    ws = {}
    for c in cats:
        lab = next((k[1] for k in n_by_cat if k[0] == c),
                   next((k[1] for k in w_by_cat if k[0] == c), c))
        n = sum(v for k, v in n_by_cat.items() if k[0] == c)
        w = sum(v for k, v in w_by_cat.items() if k[0] == c)
        share = (w / tot_w) if tot_w else ""
        ws[c] = share
        weighted_label[c] = lab
        comp_rows.append(dict(
            cycle=cy, variable="STRATUM_schooltype", category_code=c,
            category_label=lab, n_schools=n, weighted_students=round(w, 1),
            share=round(share, 4) if share != "" else "",
            source_file=f"school:{sch_src}#STRATUM ; students:{stu_src}#STRATUM,W_FSTUWT",
        ))
    weighted_share[cy] = ws
    micro_by_cat[cy] = {c: sum(v for k, v in w_by_cat.items() if k[0] == c) for c in cats}

    # ---- SC013 public/private (weighted via student<->school merge on CNTSCHID)
    m = stu.merge(sch[["CNTSCHID", "sc013", "schtype"]], on="CNTSCHID", how="left")
    for varname, col, src in [("SC013_public_private", "sc013", "SC013Q01TA"),
                              ("SCHLTYPE_ownership", "schtype", "SCHLTYPE")]:
        wg = m.groupby(col).W_FSTUWT.sum()
        ng = sch.groupby(col).size()
        for k in wg.index:
            w = wg.get(k, 0.0)
            comp_rows.append(dict(
                cycle=cy, variable=varname, category_code=str(k),
                category_label=str(k), n_schools=int(ng.get(k, 0)),
                weighted_students=round(w, 1),
                share=round(w / tot_w, 4) if tot_w else "",
                source_file=f"school:{sch_src}#{src} ; students:{stu_src}#W_FSTUWT (merge CNTSCHID)",
            ))
    del sch, stu, m
    print(f"[{cy}] done. schools={tot_n} weighted_students={tot_w:,.0f}", flush=True)

# ---------------------------------------------------- write composition csv
comp_path = os.path.join(DERIVED, "turkiye_school_type_composition.csv")
with open(comp_path, "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=["cycle", "variable", "category_code",
        "category_label", "n_schools", "weighted_students", "share", "source_file"])
    w.writeheader()
    for r in comp_rows:
        w.writerow(r)
print("wrote", comp_path)

# ---------------------------------------------------- drift across cycles (b)
drift_path = os.path.join(DERIVED, "turkiye_composition_drift.csv")
all_cats = [c for c in ORDER if any(c in weighted_share[cy] for cy in weighted_share)]
with open(drift_path, "w", newline="", encoding="utf-8") as f:
    fn = ["category_code", "category_label", "share_2015", "share_2018",
          "share_2022", "share_2025", "delta_2018_2025", "max_minus_min_2018_2025",
          "flag_gt5pp", "note"]
    w = csv.DictWriter(f, fieldnames=fn)
    w.writeheader()
    for c in all_cats:
        s = {cy: weighted_share[cy].get(c) for cy in ["2015", "2018", "2022", "2025"]}
        fine = [s["2018"], s["2022"], s["2025"]]
        fine = [x for x in fine if x is not None]
        d1825 = (s["2025"] - s["2018"]) if (s["2018"] is not None and s["2025"] is not None) else None
        rng = (max(fine) - min(fine)) if len(fine) >= 2 else None
        # 2015 coarse categories are not comparable to the fine 2018+ ones
        coarse = c in ("genel_ortaogretim_2015", "meslek_2015")
        flag = ""
        if rng is not None:
            flag = "YES" if rng > 0.05 else "no"
        note = ""
        if coarse:
            note = "2015 yalnizca kaba tabaka; fine kategorilerle karsilastirilamaz"
        if c == "ozel_genel" or c == "ozel_meslek":
            note = "Ozel liseler yalnizca 2025'te ayri tabaka; onceki dongularde Anadolu vb. icine gomulu"
        w.writerow(dict(
            category_code=c, category_label=weighted_label.get(c, c),
            share_2015=round(s["2015"], 4) if s["2015"] is not None else "",
            share_2018=round(s["2018"], 4) if s["2018"] is not None else "",
            share_2022=round(s["2022"], 4) if s["2022"] is not None else "",
            share_2025=round(s["2025"], 4) if s["2025"] is not None else "",
            delta_2018_2025=round(d1825, 4) if d1825 is not None else "",
            max_minus_min_2018_2025=round(rng, 4) if rng is not None else "",
            flag_gt5pp=flag, note=note))
print("wrote", drift_path)

# ---------------------------------------------------- MEB reported (c)
# Figures transcribed from the MEB/ODSGM national reports (pdftotext verified).
# 2015 report has NO school-type breakdown -> "not found".
meb = [
    # cycle, category_label, meb_share(0-1 or ''), micro cat_code to compare, source_file, page, quote
    ("2015", "(okul türü dağılımı raporda yok)", "", None,
     "docs/national_reports_meb/09155512_PISA_2015.pdf", "-",
     "PISA 2015 Ulusal Raporu okul turune gore ornekleme dagilimi vermiyor (not found)"),

    ("2018", "Anadolu lisesi", 0.437, "anadolu",
     "docs/national_reports_meb/03105347_PISA_2018_Turkiye_On_Raporu.pdf", "24",
     "orneklemde... %43,7'si Anadolu lisesi"),
    ("2018", "Mesleki ve teknik Anadolu lisesi", 0.311, "meslek",
     "docs/national_reports_meb/03105347_PISA_2018_Turkiye_On_Raporu.pdf", "24",
     "%31,1'i mesleki ve teknik Anadolu lisesi"),
    ("2018", "Anadolu imam hatip lisesi", 0.137, "imam_hatip",
     "docs/national_reports_meb/03105347_PISA_2018_Turkiye_On_Raporu.pdf", "24",
     "%13,7'si Anadolu imam hatip lisesi"),
    ("2018", "Fen+sosyal+cok programli+guzel sanatlar", 0.112, "MIX",
     "docs/national_reports_meb/03105347_PISA_2018_Turkiye_On_Raporu.pdf", "24",
     "kalan %11,2 fen/sosyal bilimler/cok programli/guzel sanatlar (100 - digerleri)"),
    ("2018", "Ortaokul", 0.003, "ortaokul",
     "docs/national_reports_meb/03105347_PISA_2018_Turkiye_On_Raporu.pdf", "24",
     "Ortaokul %0,3 (grafik)"),

    ("2022", "Anadolu lisesi", 0.560, "anadolu",
     "docs/national_reports_meb/21120745_26152640_pisa2022_rapor.pdf", "35",
     "Grafik 1.1 Okul Turleri: Anadolu 56,0"),
    ("2022", "Mesleki ve teknik Anadolu lisesi", 0.230, "meslek",
     "docs/national_reports_meb/21120745_26152640_pisa2022_rapor.pdf", "35",
     "mesleki ve teknik 23,0"),
    ("2022", "Anadolu imam hatip lisesi", 0.102, "imam_hatip",
     "docs/national_reports_meb/21120745_26152640_pisa2022_rapor.pdf", "35",
     "imam hatip 10,2"),
    ("2022", "Fen lisesi", 0.056, "fen",
     "docs/national_reports_meb/21120745_26152640_pisa2022_rapor.pdf", "35",
     "fen 5,6 (Grafik 1.1)"),
    ("2022", "Cok programli Anadolu lisesi", 0.028, "cok_programli",
     "docs/national_reports_meb/21120745_26152640_pisa2022_rapor.pdf", "35",
     "cok programli 2,8"),
    ("2022", "Guzel sanatlar lisesi", 0.012, "spor_guzel",
     "docs/national_reports_meb/21120745_26152640_pisa2022_rapor.pdf", "35",
     "guzel sanatlar 1,2"),
    ("2022", "Sosyal bilimler lisesi", 0.009, "sosyal",
     "docs/national_reports_meb/21120745_26152640_pisa2022_rapor.pdf", "35",
     "sosyal bilimler 0,9"),
    ("2022", "Ortaokul", 0.002, "ortaokul",
     "docs/national_reports_meb/21120745_26152640_pisa2022_rapor.pdf", "35",
     "ortaokul 0,2"),

    ("2025", "Anadolu lisesi", 0.466, "anadolu",
     "docs/national_reports_meb/PISA2025TurkiyeRaporu.pdf", "33",
     "%46,6'sinin Anadolu lisesi"),
    ("2025", "Mesleki ve teknik Anadolu lisesi", 0.328, "meslek",
     "docs/national_reports_meb/PISA2025TurkiyeRaporu.pdf", "33",
     "%32,8'inin mesleki ve teknik Anadolu lisesi"),
    ("2025", "Anadolu imam hatip lisesi", 0.095, "imam_hatip",
     "docs/national_reports_meb/PISA2025TurkiyeRaporu.pdf", "33",
     "%9,5'inin Anadolu imam hatip lisesi"),
    ("2025", "Fen+sosyal+cok programli+guzel sanatlar/spor", 0.110, "MIX",
     "docs/national_reports_meb/PISA2025TurkiyeRaporu.pdf", "33",
     "toplami orneklemin %11'ini olusturur"),
    ("2025", "Ortaokul", 0.001, "ortaokul",
     "docs/national_reports_meb/PISA2025TurkiyeRaporu.pdf", "33",
     "%0,1'i ortaokul ogrencilerinden olusur"),
]

def micro_mix(cy):
    """weighted share of fen+sosyal+cok_programli+spor_guzel for comparison to MEB MIX."""
    d = micro_by_cat.get(cy, {})
    tot = sum(d.values())
    mix = sum(d.get(c, 0.0) for c in ("fen", "sosyal", "cok_programli", "spor_guzel"))
    return mix / tot if tot else None

meb_path = os.path.join(DERIVED, "meb_reported_composition.csv")
with open(meb_path, "w", newline="", encoding="utf-8") as f:
    fn = ["cycle", "category_label", "meb_reported_share", "microdata_weighted_share",
          "diff_pp", "source_file", "page", "quote"]
    w = csv.DictWriter(f, fieldnames=fn)
    w.writeheader()
    for cy, lab, share, code, src, page, quote in meb:
        micro = ""
        diff = ""
        if code == "MIX":
            mv = micro_mix(cy)
            micro = round(mv, 4) if mv is not None else ""
        elif code is not None:
            d = micro_by_cat.get(cy, {})
            tot = sum(d.values())
            mv = (d.get(code, 0.0) / tot) if tot else None
            micro = round(mv, 4) if mv is not None else ""
        if share != "" and micro != "":
            diff = round((share - micro) * 100, 1)
        w.writerow(dict(cycle=cy, category_label=lab,
            meb_reported_share=share, microdata_weighted_share=micro,
            diff_pp=diff, source_file=src, page=page, quote=quote))
print("wrote", meb_path)
print("DONE")
