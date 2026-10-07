# -*- coding: utf-8 -*-
"""
37_a10_oecd_relative_ps2012.py — ek analiz isteği A10: 2012 ülke düzeyi artıklarımız OECD'nin kendi "göreli performans"
istatistiğiyle uyuşuyor mu?

OECD ölçüsü: PISA 2012 Results Vol. V (Creative Problem Solving), Annex B1, Tablo V.2.6 [Part 1/3], ilk sütun
"Relative performance across all students (actual minus expected score)". Beklenen puan, katılan tüm ülkelerin
öğrencileri üzerinde problem çözmenin matematik, okuma ve fen üzerine ikinci derece polinom (kareler ve etkileşimler dahil)
regresyonundan gelir (tablo dipnotu 2); ülke değeri, öğrenci düzeyi fiili − beklenen farkının ortalamasıdır.
Bizim ölçü: ülke ortalamaları üzerinde I = a + b·C (+ c·C²) + e, C = mat/oku/fen ortalaması (PUF, 2012 kâğıt çekirdeği).

ÖNCEDEN BELİRLENEN SEÇİMLER (25 Eyl 2026; tablo ayrıştırılırken Türkiye satırı −14 görüldü, karşılaştırma sonucu görülmeden):
  * Birincil karşılaştırma: tüm katılımcı / doğrusal artığımız (puan) ↔ OECD sütun 1, ortak sistemler (İngiltere, Kıbrıs,
    Şanghay bizim 2012 örnekleminde yok).
  * Ölçüler: Pearson r, Spearman ρ, Türkiye'nin iki ölçüdeki alttan sırası, ortalama mutlak fark.
  * İkincil: tüm/karesel, OECD/doğrusal, OECD/karesel.
Tablo kaynağı: pdftotext (poppler) ile PDF'den ayrıştırılır ve data/derived/mechanisms/oecd_vol5_table_v2_6_part1.csv olarak
saklanır; pdftotext yoksa saklanan CSV kullanılır (Windows'ta poppler yok).
Girdi: data/pisa/2012/9789264208070-en.pdf; data/derived/mechanisms/placebo_conditional_2012ps_puf.csv (core_def PUF mat/oku/fen)
Çıktı: data/derived/mechanisms/oecd_vol5_table_v2_6_part1.csv, a10_oecd_relative_2012.csv, a10_oecd_relative_2012_summary.json
Kullanım: python analysis/37_a10_oecd_relative_ps2012.py      Yazan: Claude Opus 5.5 (Cowork), 2026-09-25.
"""
from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
PDF = ROOT / "data" / "pisa" / "2012" / "9789264208070-en.pdf"
MECH = ROOT / "data" / "derived" / "mechanisms"
TABLE = MECH / "oecd_vol5_table_v2_6_part1.csv"
FOCUS = ["TUR", "HUN", "SWE", "POL"]

NAME2ISO = {
    "Australia": "AUS", "Austria": "AUT", "Belgium": "BEL", "Canada": "CAN", "Chile": "CHL", "Czech Republic": "CZE",
    "Denmark": "DNK", "Estonia": "EST", "Finland": "FIN", "France": "FRA", "Germany": "DEU", "Hungary": "HUN",
    "Ireland": "IRL", "Israel": "ISR", "Italy": "ITA", "Japan": "JPN", "Korea": "KOR", "Netherlands": "NLD",
    "Norway": "NOR", "Poland": "POL", "Portugal": "PRT", "Slovak Republic": "SVK", "Slovenia": "SVN", "Spain": "ESP",
    "Sweden": "SWE", "Turkey": "TUR", "England (United Kingdom)": "ENG", "United States": "USA",
    "Brazil": "BRA", "Bulgaria": "BGR", "Colombia": "COL", "Croatia": "HRV", "Cyprus*": "CYP", "Hong Kong-China": "HKG",
    "Macao-China": "MAC", "Malaysia": "MYS", "Montenegro": "MNE", "Russian Federation": "RUS", "Serbia": "SRB",
    "Shanghai-China": "QCN", "Singapore": "SGP", "Chinese Taipei": "TWN", "United Arab Emirates": "ARE", "Uruguay": "URY",
}
OECD_2012 = {"AUS", "AUT", "BEL", "CAN", "CHL", "CZE", "DNK", "EST", "FIN", "FRA", "DEU", "HUN", "IRL", "ISR", "ITA", "JPN",
             "KOR", "NLD", "NOR", "POL", "PRT", "SVK", "SVN", "ESP", "SWE", "TUR", "ENG", "USA"}
ROW = re.compile(r"^\s*(?:OECD|Partners)?\s*(?P<name>[A-Z][A-Za-z .()*\-]+?)\s{2,}(?P<v>-?\d+)\s+\((?P<se>\d+\.\d)\)\s+"
                 r"(?P<pct>\d+\.\d)\s+\((?P<pse>\d+\.\d)\)")


def parse_pdf() -> pd.DataFrame | None:
    exe = shutil.which("pdftotext")
    if exe is None:
        return None
    with tempfile.TemporaryDirectory() as td:
        txt = Path(td) / "v5.txt"
        subprocess.run([exe, "-layout", str(PDF), str(txt)], check=True)
        lines = txt.read_text(encoding="utf-8", errors="replace").splitlines()
    start = None
    for i, ln in enumerate(lines):
        if "[Part 1/3]" in ln and any("Table V.2.6" in x for x in lines[i:i + 4]) \
                and any("across all students2" in x for x in lines[i:i + 20]):
            start = i
            break
    if start is None:
        raise SystemExit("Tablo V.2.6 [Part 1/3] bulunamadı")
    rows = []
    for ln in lines[start + 1:]:
        if "[Part 2/3]" in ln:
            break
        m = ROW.match(ln)
        if m and m.group("name").strip() in NAME2ISO:
            nm = m.group("name").strip()
            rows.append({"country": nm, "iso3": NAME2ISO[nm], "rel_perf": int(m.group("v")), "rel_perf_se": float(m.group("se")),
                         "pct_above_expected": float(m.group("pct")), "pct_se": float(m.group("pse"))})
    t = pd.DataFrame(rows)
    if len(t) != 44 or t.iso3.duplicated().any():
        raise SystemExit(f"ayrıştırma beklenmedik: {len(t)} satır (beklenen 44)")
    return t


def main() -> int:
    t = parse_pdf()
    if t is None:
        t = pd.read_csv(TABLE, encoding="utf-8")
        print(f"pdftotext yok → saklanan tablo kullanıldı ({len(t)} satır)")
    else:
        tmp = TABLE.with_suffix(".csv.tmp")
        t.to_csv(tmp, index=False, encoding="utf-8")
        os.replace(tmp, TABLE)
        print(f"PDF'den ayrıştırıldı: {len(t)} sistem → {TABLE.relative_to(ROOT)}")
    ours = pd.read_csv(MECH / "placebo_conditional_2012ps_puf.csv", encoding="utf-8-sig")
    ours = ours[ours.core_def == "PUF mat/oku/fen"]
    rows, summ = [], {"source": "OECD (2014) PISA 2012 Results Vol. V, Annex B1 Table V.2.6 Part 1/3, col. 1", "specs": {}}
    for scope in ["all", "oecd"]:
        for spec in ["linear", "quadratic"]:
            o = ours[(ours.scope == scope) & (ours.spec == spec)][["iso3", "residual"]]
            m = o.merge(t[["iso3", "rel_perf", "rel_perf_se"]], on="iso3", how="inner")
            n = len(m)
            r = float(np.corrcoef(m.residual, m.rel_perf)[0, 1])
            rho = float(m.residual.rank().corr(m.rel_perf.rank()))
            b = np.polyfit(m.rel_perf, m.residual, 1)
            key = f"{scope}/{spec}"
            summ["specs"][key] = {"n": n, "pearson_r": round(r, 3), "spearman_rho": round(rho, 3),
                                  "mean_abs_diff": round(float((m.residual - m.rel_perf).abs().mean()), 2),
                                  "slope_ours_on_oecd": round(float(b[0]), 3),
                                  "not_in_ours": sorted(set(t.iso3) - set(o.iso3) - ({"ENG"} if scope == "all" else set()))}
            for _, row in m.iterrows():
                rows.append({"scope": scope, "spec": spec, "iso3": row.iso3, "n": n, "our_residual": round(float(row.residual), 2),
                             "oecd_rel_perf": int(row.rel_perf), "oecd_se": row.rel_perf_se,
                             "rank_ours": int((m.residual < row.residual).sum() + 1),
                             "rank_oecd": int((m.rel_perf < row.rel_perf).sum() + 1)})
                if row.iso3 in FOCUS:
                    summ["specs"][key][row.iso3] = {"ours": round(float(row.residual), 2), "oecd": int(row.rel_perf),
                                                    "oecd_se": row.rel_perf_se,
                                                    "rank_ours": int((m.residual < row.residual).sum() + 1),
                                                    "rank_oecd": int((m.rel_perf < row.rel_perf).sum() + 1)}
    tmp = MECH / "a10_oecd_relative_2012.csv.tmp"
    pd.DataFrame(rows).to_csv(tmp, index=False, encoding="utf-8")
    os.replace(tmp, MECH / "a10_oecd_relative_2012.csv")
    tmp = MECH / "a10_oecd_relative_2012_summary.json.tmp"
    tmp.write_text(json.dumps(summ, ensure_ascii=False, indent=1), encoding="utf-8")
    os.replace(tmp, MECH / "a10_oecd_relative_2012_summary.json")
    for k, v in summ["specs"].items():
        tu = v.get("TUR", {})
        print(f"{k:<16} n={v['n']:>2} r={v['pearson_r']:.3f} rho={v['spearman_rho']:.3f} MAD={v['mean_abs_diff']:>5} "
              f"eğim={v['slope_ours_on_oecd']:.2f}  TUR: bizim {tu.get('ours')} (sıra {tu.get('rank_ours')}) / OECD {tu.get('oecd')} "
              f"(sıra {tu.get('rank_oecd')})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
