# -*- coding: utf-8 -*-
"""
58_oecd2025_relative_performance.py — Makale 1 Bölüm 3.2: 2025 ülke düzeyi artığının OECD'nin öğrenci düzeyi göreli performans
ölçüsüyle karşılaştırılması (betik 34/43'ün 2012 doğrulamasının 2025 karşılığı; MAKALE1.md satır 70).

Kaynak: OECD (2026a), PISA 2025 Results (Volume I), Tablo I.B1.2a.20 "Relative performance in computational problem-solving",
StatLink https://stat.link/mrq53f → data/pisa/2025/annex_tables/mrq53f.xlsx (14 Eyl 2026'da edinildi; sha256 14e95853…).
Tablo Not 1: "Relative scores are the residuals obtained from pooled cubic polynomial regressions, across all participating
countries/economies, of performance in computational problem-solving over performance in science, reading or mathematics."
Makale 1 artığı: data/derived/mechanisms/placebo_conditional_2025.csv (dört spesifikasyon).
Eşleştirme ülke adıyla (OECD'deki '*' işareti atılır); eşleşmeyen sistemler yazdırılır. Sıra en düşükten (1 = en olumsuz).
Çıktı: data/derived/oecd2025_relative/{oecd_table_I_B1_2a_20.csv, m1_vs_oecd.csv, summary.json}
Kapılar: Türkiye satırı B96 = −29,17127 ve OECD ortalaması B10 = 8,64895 (StatLink sürümü 08-Sep-2026); 38 OECD üyesinin
basit ortalaması OECD ortalama satırını 1e-4 içinde verir.
Kullanım: python analysis/58_oecd2025_relative_performance.py
Yazan: Claude Code (Opus 5.5), 2026-10-04 (oturum içi hesabın kalıcılaştırılması; taze bağlamlı doğrulama wf_…).
"""
from __future__ import annotations

import hashlib
import json
import os
import sys
from pathlib import Path

import numpy as np
import openpyxl
import pandas as pd
from scipy.stats import pearsonr, spearmanr

ROOT = Path(__file__).resolve().parent.parent
XLSX = ROOT / "data" / "pisa" / "2025" / "annex_tables" / "mrq53f.xlsx"
M1 = ROOT / "data" / "derived" / "mechanisms" / "placebo_conditional_2025.csv"
OUT = ROOT / "data" / "derived" / "oecd2025_relative"
OECD38 = {"Australia", "Austria", "Belgium", "Canada", "Chile", "Colombia", "Costa Rica", "Czechia", "Denmark", "Estonia",
          "Finland", "France", "Germany", "Greece", "Hungary", "Iceland", "Ireland", "Israel", "Italy", "Japan", "Korea",
          "Latvia", "Lithuania", "Luxembourg", "Mexico", "Netherlands", "New Zealand", "Norway", "Poland", "Portugal",
          "Slovak Republic", "Slovenia", "Spain", "Sweden", "Switzerland", "Türkiye", "United Kingdom", "United States"}


def main() -> int:
    ws = openpyxl.load_workbook(XLSX, read_only=True, data_only=True)["Table I.B1.2a.20"]
    rows = list(ws.iter_rows(min_row=1, max_row=115, max_col=13, values_only=True))
    if rows[0][0] != "Table I.B1.2a.20" or "Relative performance in computational problem-solving" not in str(rows[1][0]):
        raise SystemExit("DUR: sayfa kimliği beklenen tablo değil")
    recs = []
    for r in rows[9:106]:
        if not r[0]:
            continue
        name = str(r[0]).strip()
        num = lambda v: float(v) if isinstance(v, (int, float)) else np.nan
        recs.append({"name": name.rstrip("*"), "sci": num(r[1]), "sci_se": num(r[2]), "sci_pct_higher": num(r[3]),
                     "rea": num(r[5]), "rea_se": num(r[6]), "mat": num(r[9]), "mat_se": num(r[10])})
    o = pd.DataFrame(recs)
    avg = o[o.name == "OECD average"].iloc[0]
    o = o[o.name != "OECD average"].copy()
    tur = o[o.name == "Türkiye"].iloc[0]
    if abs(tur.sci - (-29.17127)) > 1e-4 or abs(avg.sci - 8.64895) > 1e-4:
        raise SystemExit("DUR: Türkiye ya da OECD ortalaması StatLink sürümünden farklı")
    o["oecd"] = o.name.isin(OECD38)
    if int(o.oecd.sum()) != 38:
        raise SystemExit(f"DUR: OECD üyesi sayısı {int(o.oecd.sum())}")
    for c in ("sci", "rea", "mat"):
        if abs(o.loc[o.oecd, c].mean() - avg[c]) > 1e-4:
            raise SystemExit(f"DUR: OECD üyelerinin ortalaması {c} için tablo satırından farklı")
    for c in ("sci", "rea", "mat"):
        v = o[c]
        o[f"rank_low_all_{c}"] = v.rank(method="min").where(v.notna())
        o[f"rank_low_oecd_{c}"] = v.where(o.oecd).rank(method="min")

    m = pd.read_csv(M1, encoding="utf-8-sig")
    mp = dict(zip(m.country_name, m.iso3))
    o["iso3"] = o.name.map(mp)
    unmatched = sorted(o[o.iso3.isna() & o.sci.notna()].name)
    out = []
    for (sc, sp), g in m.groupby(["scope", "spec"]):
        j = g.merge(o.dropna(subset=["iso3"]), on="iso3")
        for c in ("sci", "rea", "mat"):
            jj = j.dropna(subset=[c])
            t = jj[jj.iso3 == "TUR"].iloc[0]
            out.append({"scope": sc, "spec": sp, "oecd_measure": c, "n": len(jj),
                        "pearson": round(float(pearsonr(jj.residual, jj[c])[0]), 3),
                        "spearman": round(float(spearmanr(jj.residual, jj[c])[0]), 3),
                        "tur_oecd": round(float(t[c]), 2), "tur_rank_oecd_measure": int((jj[c] < t[c]).sum() + 1),
                        "tur_m1": round(float(t.residual), 2), "tur_rank_m1": int((jj.residual < t.residual).sum() + 1)})
    res = pd.DataFrame(out)
    OUT.mkdir(parents=True, exist_ok=True)
    for df, name in ((o, "oecd_table_I_B1_2a_20.csv"), (res, "m1_vs_oecd.csv")):
        tmp = OUT / (name + ".tmp")
        df.to_csv(tmp, index=False, encoding="utf-8")
        os.replace(tmp, OUT / name)
    summ = {"xlsx_sha256": hashlib.sha256(XLSX.read_bytes()).hexdigest(), "m1_sha256": hashlib.sha256(M1.read_bytes()).hexdigest(),
            "script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            "n_with_sci": int(o.sci.notna().sum()), "unmatched_with_sci": unmatched,
            "turkiye": {c: {"value": round(float(tur[c]), 5), "se": round(float(tur[c + "_se"]), 5),
                            "rank_low_all": int(o.loc[o.name == "Türkiye", f"rank_low_all_{c}"].iloc[0]),
                            "rank_low_oecd": int(o.loc[o.name == "Türkiye", f"rank_low_oecd_{c}"].iloc[0])} for c in ("sci", "rea", "mat")},
            "turkiye_sci_pct_higher": round(float(tur.sci_pct_higher), 4),
            "oecd_average": {c: round(float(avg[c]), 5) for c in ("sci", "rea", "mat")}}
    tmp = OUT / "summary.json.tmp"
    tmp.write_text(json.dumps(summ, ensure_ascii=False, indent=1), encoding="utf-8")
    os.replace(tmp, OUT / "summary.json")
    print(res[(res.spec == "linear")].to_string(index=False))
    print("Türkiye:", summ["turkiye"], "| eşleşmeyen:", unmatched)
    return 0


if __name__ == "__main__":
    sys.exit(main())
