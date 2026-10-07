# -*- coding: utf-8 -*-
"""
51_diag_bel_2025_gate.py — teşhis: Belçika 2025 okuma ortalaması neden yayımlanmış değerden sapıyor?

Soru: Yerel koşu 1'de (2026-09-26) 2025 kapısı (mikroveri ağırlıklı PV ortalaması ile panel değeri arasındaki mutlak fark ≤ 0,003)
83 sistemde ≤ 0,0005 ile geçti, Belçika okumada 0,0116 ile geçmedi. Bu kapı E1 bootstrap, E5, E2 ve E9'u durduruyor. Yazarın
kararı: önce teşhis, sonra karar. Bu betik yeni sonuç üretmez; yalnız farkın kaynağını arar.

Panel değerlerinin kaynağı (`pisa_scores_long.csv`): `data/pisa/2025/annex_tables/mrq53f.xlsx`, Table I.B1.2a.36 (fen),
I.B1.2a.37 (okuma), I.B1.2a.38 (matematik), I.B1.2a.4 (CPS). Bunlar döngüler arası tablolar; Belçika için 2025 değeri trend
karşılaştırması amacıyla farklı bir alt örneklemle hesaplanmış olabilir (hipotez, doğrulanmadı).

ÖNCEDEN BELİRLENEN TEŞHİS KURALLARI (koşudan önce yazıldı, 2026-09-26):
  T1 PV düzeyi: 10 okuma PV'sinin ağırlıklı ortalamaları ve eksik PV'li öğrenci sayısı/ağırlık payı yazılır.
  T2 Ağırlık: W_FSTUWT eksik ya da ≤ 0 öğrenci sayısı.
  T3 Alt grup: PUF'ta bulunan bölge/dil/tabaka değişkenlerinin (SUBNATIO, REGION, STRATUM, LANGTEST_COG, LANGTEST_QQQ, ADMINMODE)
     her düzeyi için "o düzey dışarıda" ortalama hesaplanır. Bir düzeyi dışarıda bırakmak DÖRT alanın (mat, oku, fen, CPS) hepsinde
     yayımlanmış değeri mutlak fark ≤ 0,003 ile üretiyorsa → "neden bulundu: yayımlanmış değer o alt grubu dışlıyor".
  T4 SE: okuma BRR (Fay 0,5; 80) + Rubin SE'si yayımlanmış SE (3.0358) ile karşılaştırılır.
  T5 (--scan-annex): `data/pisa/2025/annex_tables/*.xlsx` içinde "Belgium" satırında, mikroveri okuma ortalamasına ya da
     yayımlanmış değere 0,05 içinde yakın her hücre listelenir (sayfa + hücre). Başka bir tablo mikroveriyle ≤ 0,003 uyuşuyorsa
     → "neden bulundu: trend tablosu ile ana tablo farklı".
  Hiçbiri tutmazsa → "neden bulunamadı"; karar yazara yeniden sorulur. Bu betik hiçbir kapıyı değiştirmez.
Girdi: data/pisa/2025/database/CY09_MS_STU_PUF.zip; data/derived/analysis_panel.csv; (--scan-annex) data/pisa/2025/annex_tables/*.xlsx.
Çıktı: data/derived/empirical_fixes/diag_bel_2025.json.
Kullanım (Windows, Git Bash'ten; unzip PATH'te olmalı): python analysis/51_diag_bel_2025_gate.py [--scan-annex]
Yazan: Claude Code (bulut oturumu), 2026-09-26. Bulutta mikroveri yok; betik sentetik veriyle sınandı.
SONRADAN (2026-09-26, PR incelemesi; betik yeniden koşulmadı): T3 ve T5'in ≤ 0,003 kararı 4 basamağa yuvarlanmış farkla
  veriliyordu; yuvarlama 0,003–0,00305 arasındaki bir farkı yanlışlıkla eşleşmiş sayabilirdi. Karar artık tam hassasiyetle,
  yuvarlama yalnız gösterimde. Koşulan sürümün hükmü ("neden bulunamadı") etkilenmedi: en yakın T3 farkı 0,2024, T5'te
  mikroveri okuma ortalamasına 0,0035 içinde hücre yok (`diag_bel_2025.json`).
"""
from __future__ import annotations

import argparse
import importlib
import json
import os
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE))
D = ROOT / "data" / "derived"
OUT = D / "empirical_fixes"
ZIP = ROOT / "data" / "pisa" / "2025" / "database" / "CY09_MS_STU_PUF.zip"
ROOTS = {"math": "MATH", "reading": "READ", "science": "SCIE", "cps2025": "CMPS"}
REPW = [f"W_FSTURWT{i}" for i in range(1, 81)]
GROUP_CANDIDATES = ["SUBNATIO", "REGION", "STRATUM", "LANGTEST_COG", "LANGTEST_QQQ", "ADMINMODE"]
TOL = 0.003
FAY_MULT = 1.0 / (80 * (1 - 0.5) ** 2)


def read_bel() -> tuple[pd.DataFrame, list[str]]:
    import pyreadstat
    with tempfile.TemporaryDirectory(prefix="diagbel_", dir=os.environ.get("PISA_TMP")) as td:
        with zipfile.ZipFile(ZIP) as z:
            name = [n for n in z.namelist() if n.lower().endswith(".sav")][0]
            try:
                z.extract(name, td)
            except NotImplementedError:
                r = subprocess.run(["unzip", "-o", "-q", str(ZIP), name, "-d", td], capture_output=True, text=True)
                if r.returncode != 0:
                    raise SystemExit(f"DUR: unzip başarısız: {r.stderr[:300]}")
        sav = str(Path(td) / name)
        _, meta = pyreadstat.read_sav(sav, metadataonly=True)
        have = {c.upper(): c for c in meta.column_names}
        groups = [g for g in GROUP_CANDIDATES if g in have]
        cols = ["CNT", "W_FSTUWT"] + REPW + [f"PV{i}{r}" for i in range(1, 11) for r in ROOTS.values()] + groups
        miss = [c for c in cols if c.upper() not in have]
        if miss:
            raise SystemExit(f"DUR: PUF'ta yok: {miss[:8]}")
        df, _ = pyreadstat.read_sav(sav, usecols=[have[c] for c in cols])
    df.columns = [c.upper() for c in df.columns]
    df = df[df.CNT.astype(str).str.strip() == "BEL"].reset_index(drop=True)
    for c in df.columns:
        if c not in ["CNT"] + groups:
            df[c] = pd.to_numeric(df[c], errors="coerce")
    return df, groups


def pv_means(df: pd.DataFrame, root: str) -> np.ndarray:
    w = df.W_FSTUWT.to_numpy(float)
    out = []
    for i in range(1, 11):
        y = df[f"PV{i}{root}"].to_numpy(float)
        ok = np.isfinite(y) & np.isfinite(w)
        out.append(np.sum(w[ok] * y[ok]) / np.sum(w[ok]))
    return np.array(out)


def brr_se(df: pd.DataFrame, root: str) -> float:
    W = np.column_stack([df.W_FSTUWT.to_numpy(float)] + [df[c].to_numpy(float) for c in REPW])
    th = np.empty((81, 10))
    for i in range(10):
        y = df[f"PV{i + 1}{root}"].to_numpy(float)
        ok = np.isfinite(y)
        th[:, i] = (W[ok].T @ y[ok]) / W[ok].sum(axis=0)
    v_s = float((FAY_MULT * ((th[1:] - th[0][None]) ** 2).sum(axis=0)).mean())
    v_i = 1.1 * float(th[0].var(ddof=1))
    return float(np.sqrt(v_s + v_i))


def scan_annex(targets: dict) -> list[dict]:
    import openpyxl
    hits = []
    for fn in sorted((ROOT / "data" / "pisa" / "2025" / "annex_tables").glob("*.xlsx")):
        wb = openpyxl.load_workbook(fn, read_only=True, data_only=True)
        for ws in wb.worksheets:
            for r in ws.iter_rows():
                if not r or not isinstance(r[0].value, str) or "Belgium" not in r[0].value:
                    continue
                for cell in r[1:]:
                    v = cell.value
                    if isinstance(v, (int, float)):
                        for tag, t in targets.items():
                            if abs(float(v) - t) <= 0.05:
                                d = abs(float(v) - t)
                                hits.append({"file": fn.name, "sheet": ws.title, "cell": cell.coordinate, "value": float(v),
                                             "near": tag, "abs_diff": round(d, 4), "match": bool(d <= TOL)})
    return hits


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--scan-annex", action="store_true")
    a = ap.parse_args()
    panel = pd.read_csv(D / "analysis_panel.csv")
    pub = panel[(panel.cycle == 2025) & (panel.iso3 == "BEL")].iloc[0]
    pub_mean = {"math": pub.math_mean, "reading": pub.reading_mean, "science": pub.science_mean, "cps2025": pub.cps2025_mean}
    df, groups = read_bel()
    res = {"n_students": int(len(df)), "groups_found": groups, "published": {k: float(v) for k, v in pub_mean.items()},
           "published_reading_se": float(pub.reading_se)}
    res["T1_pv"] = {}
    for dom, root in ROOTS.items():
        pm = pv_means(df, root)
        miss = df[[f"PV{i}{root}" for i in range(1, 11)]].isna().any(axis=1)
        res["T1_pv"][dom] = {"mean": round(float(pm.mean()), 4), "diff_vs_published": round(float(pm.mean() - pub_mean[dom]), 4),
                             "pv_means": [round(float(x), 4) for x in pm], "n_missing_pv": int(miss.sum()),
                             "w_share_missing_pv": round(float(df.W_FSTUWT[miss].sum() / df.W_FSTUWT.sum()), 6)}
    w = df.W_FSTUWT
    res["T2_weights"] = {"n_nan": int(w.isna().sum()), "n_nonpositive": int((w <= 0).sum()), "sum": round(float(w.sum()), 2)}
    res["T3_leave_one_level_out"] = []
    for g in groups:
        for lev, n in df[g].astype(str).value_counts().items():
            sub = df[df[g].astype(str) != lev]
            if len(sub) == 0:
                continue
            raw = {dom: float(pv_means(sub, root).mean() - pub_mean[dom]) for dom, root in ROOTS.items()}
            res["T3_leave_one_level_out"].append({"var": g, "level_dropped": lev, "n_dropped": int(n),
                                                  "diffs": {k: round(v, 4) for k, v in raw.items()},
                                                  "reproduces_all": bool(all(abs(v) <= TOL for v in raw.values()))})
    res["T4_reading_se"] = {"brr_rubin": round(brr_se(df, "READ"), 4), "published": float(pub.reading_se)}
    if a.scan_annex:
        res["T5_annex_hits"] = scan_annex({"microdata_reading": res["T1_pv"]["reading"]["mean"], "published_reading": float(pub.reading_mean)})
    found = [r for r in res["T3_leave_one_level_out"] if r["reproduces_all"]]
    annex_match = [h for h in res.get("T5_annex_hits", []) if h["near"] == "microdata_reading" and h["match"]]
    if found:
        verdict = f"neden bulundu (T3): yayımlanmış değer {found[0]['var']} = {found[0]['level_dropped']} alt grubunu dışlıyor"
    elif annex_match:
        verdict = f"neden bulundu (T5): başka bir yayımlanmış tablo mikroveriyle uyuşuyor ({annex_match[0]['file']} {annex_match[0]['sheet']} {annex_match[0]['cell']})"
    else:
        verdict = "neden bulunamadı; karar yazara yeniden sorulur"
    res["verdict"] = verdict
    OUT.mkdir(parents=True, exist_ok=True)
    tmp = OUT / "diag_bel_2025.json.tmp"
    tmp.write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
    os.replace(tmp, OUT / "diag_bel_2025.json")
    print(json.dumps({k: res[k] for k in ("T1_pv", "T2_weights", "T4_reading_se", "verdict")}, ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
