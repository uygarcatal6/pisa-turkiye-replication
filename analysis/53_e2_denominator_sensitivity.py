# -*- coding: utf-8 -*-
"""
53_e2_denominator_sensitivity.py — E2 açıklanan payının paydası: aynı sistem kümesiyle duyarlılık (SONRADAN).

Soru (PR incelemesi, 2026-09-26): E2'nin (betik 45) açıklanan payı, §0.4 gereği betik 35'in `ict_covariate_2025.csv`
çıktısındaki Türkiye ülke artığına bölünüyor. O artık 44 (OECD 24) sistemle uydurulmuş; E2'nin BİT kümesi ise 43 (OECD 23)
çıktı (fark GBR). Pay aynı kümedeki artığa bölünseydi ne değişirdi?

Bu betik sonradan eklenmiş bir duyarlılıktır; birincil sonuç (§0.4 tanımı) değişmez.
Yöntem: betik 35'in ülke düzeyi modeli (CPS_2025 = a + b·çekirdek + e; çekirdek = mat/oku/fen ortalaması; ağırlıksız OLS;
  paneldeki 2025 ülke ortalamaları), Türkiye'nin artığı.
  Kapı: 44 (OECD 24) sistemde betik 35'in `tur_resid_without` değerini (2 basamağa yuvarlanmış) ≤ 0,005 ile yeniden üretmeli.
  Sonra aynı model 43 (OECD 23) sistemde; E2'nin açıklanan puanı yeni paydaya bölünür.
  Açıklanan puan = γ × ΔX; γ ve ΔX `e2_summary.json`'dan (γ 4, ΔX 4 basamağa yuvarlanmış; aralık `e2_within_ict.csv`
  lo95/hi95 × ΔX). Yuvarlama payın 4. basamağını etkileyebilir; karşılaştırma için betik 35 paydasıyla da aynı yoldan
  yeniden hesaplanır.
Girdi: data/derived/empirical_fixes/e2_summary.json, e2_within_ict.csv; data/derived/analysis_panel.csv;
       data/derived/mechanisms/ict_covariate_2025.csv.
Çıktı: data/derived/empirical_fixes/e2_denominator_sensitivity.csv, e2_denominator_sensitivity.json.
Kullanım: python analysis/53_e2_denominator_sensitivity.py (mikroveri gerekmez).
Yazan: Claude Code (bulut oturumu), 2026-09-26.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
D = ROOT / "data" / "derived"
OUT = D / "empirical_fixes"
SETS = {"ict44": "all", "ict_oecd": "oecd"}
TOL = 0.005


def tur_resid(panel: pd.DataFrame, members: list[str]) -> tuple[int, float]:
    d = panel.loc[members].dropna(subset=["core", "cps2025_mean"])
    X = np.column_stack([np.ones(len(d)), d.core.to_numpy(float)])
    b = np.linalg.lstsq(X, d.cps2025_mean.to_numpy(float), rcond=None)[0]
    e = d.cps2025_mean.to_numpy(float) - X @ b
    return len(d), float(e[list(d.index).index("TUR")])


def main() -> int:
    s = json.loads((OUT / "e2_summary.json").read_text(encoding="utf-8"))
    wi = pd.read_csv(OUT / "e2_within_ict.csv")
    ict35 = pd.read_csv(D / "mechanisms" / "ict_covariate_2025.csv")
    p = pd.read_csv(D / "analysis_panel.csv")
    p = p[p.cycle == 2025].set_index("iso3")
    p["core"] = p[["math_mean", "reading_mean", "science_mean"]].mean(axis=1)
    set43 = sorted(s["ict_set"])
    set44 = sorted(set(set43) | {"GBR"})
    members = {"ict44": (set44, set43), "ict_oecd": ([c for c in set44 if p.loc[c, "oecd_member"]],
                                                     [c for c in set43 if p.loc[c, "oecd_member"]])}
    info = {"note": "SONRADAN duyarlılık (PR incelemesi, 2026-09-26); birincil E2 sonucu (§0.4) değişmez.", "gate": {}, "denominators": {}}
    den = {}
    for sn, (big, small) in members.items():
        r35 = ict35[(ict35.scope == SETS[sn]) & (ict35.spec == "linear") & (ict35.covariate == "ICTSCH")].iloc[0]
        n_big, e_big = tur_resid(p, big)
        n_small, e_small = tur_resid(p, small)
        diff = abs(e_big - float(r35.tur_resid_without))
        info["gate"][sn] = {"n_betik35": int(r35.n), "n_recomputed": n_big, "betik35": float(r35.tur_resid_without),
                            "recomputed": round(e_big, 4), "abs_diff": round(diff, 4), "ok": bool(diff <= TOL and n_big == int(r35.n))}
        if not info["gate"][sn]["ok"]:
            raise SystemExit(f"DUR: betik 35 paydası yeniden üretilemedi: {info['gate'][sn]}")
        den[sn] = (e_big, e_small)
        info["denominators"][sn] = {"n_betik35_set": n_big, "resid_betik35_set": round(e_big, 4),
                                    "n_e2_set": n_small, "resid_e2_set": round(e_small, 4)}
    rows = []
    for key, v in s["shares"].items():
        model, sn, inc = key.split("|")
        w = wi[(wi.model == model) & (wi.set == sn) & (wi.tur_included == (inc == "tur_dahil"))]
        if len(w) != 1:
            raise SystemExit(f"DUR: {key} için e2_within_ict.csv satırı bulunamadı ({len(w)})")
        w = w.iloc[0]
        expl = float(v["gamma"]) * float(v["dx"])
        ci = sorted([float(w.lo95) * float(v["dx"]), float(w.hi95) * float(v["dx"])])
        e_big, e_small = den[sn]
        rows.append({"key": key, "model": model, "set": sn, "tur": inc, "primary": bool(v["primary"]),
                     "explained_pts": round(expl, 4), "share_reported": v["share_of_resid"],
                     "share_betik35_denom": round(expl / e_big, 4), "share_same_set_denom": round(expl / e_small, 4),
                     "share_same_set_lo95": round(min(c / e_small for c in ci), 4),
                     "share_same_set_hi95": round(max(c / e_small for c in ci), 4)})
    t = pd.DataFrame(rows)
    info["max_abs_share_change"] = round(float((t.share_same_set_denom - t.share_betik35_denom).abs().max()), 4)
    info["max_abs_share_same_set_primary"] = round(float(t[t.primary].share_same_set_denom.abs().max()), 4)
    info["max_abs_hi95_same_set_primary"] = round(float(t[t.primary][["share_same_set_lo95", "share_same_set_hi95"]].abs().max().max()), 4)
    OUT.mkdir(parents=True, exist_ok=True)
    tmp = OUT / "e2_denominator_sensitivity.csv.tmp"
    t.to_csv(tmp, index=False, encoding="utf-8")
    os.replace(tmp, OUT / "e2_denominator_sensitivity.csv")
    tmp = OUT / "e2_denominator_sensitivity.json.tmp"
    tmp.write_text(json.dumps(info, ensure_ascii=False, indent=1, allow_nan=False), encoding="utf-8")
    os.replace(tmp, OUT / "e2_denominator_sensitivity.json")
    print(json.dumps(info, ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
