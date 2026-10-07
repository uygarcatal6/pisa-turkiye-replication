# -*- coding: utf-8 -*-
"""
59_e1_studentized.py — E1s: koşullu artık değişiminin dış-studentize sırası (betik 43'ün PRESS sırasına sonradan düzeltme).

ÖN-BELİRLEME: analysis/RESULTS_EMPIRICAL_FIXES.md §0.14 (4 Eki 2026; E1 sonuçları ve güç simülasyonu görüldükten sonra, bu betik
yazılmadan önce). Betik 43 ve çıktıları değişmez.
  * Gerekçe: PRESS hatası e_i = r_i/(1 − h_ii)'nin varyansı σ²/(1 − h_ii); yüksek kaldıraçlı Türkiye'nin e'si daha geniş dağılır
    (güç simülasyonunda değiştirilebilirlik altında Δ = 0 ret oranı 0,12–0,14, nominal 0,085).
  * İstatistik: t_i = r_i / (s₍ᵢ₎ √(1 − h_ii)), s₍ᵢ₎² = [(n − p)s² − r_i²/(1 − h_ii)]/(n − p − 1); normal ve eşit varyanslı hatada
    her t_i ~ t(n − p − 1), kaldıraçtan bağımsız (Belsley, Kuh & Welsch 1980).
  * Sıra #(t < t_TUR) + 1, p = sıra/N, ret ≤ 0,10; 16 hücre (betik 43); birincil d_sd · 2015→2025 · linear.
Kapılar: t iki yoldan (kapalı formül ve açık yeniden uydurma) ≤ 1e-8; PRESS sırası e1_conditional_change.csv ile aynı; t ve e işaretçe
aynı.
Girdi: betik 34 load() (betik 43 pair_frame), data/derived/empirical_fixes/e1_conditional_change.csv.
Çıktı: data/derived/empirical_fixes/e1_studentized.csv, e1_studentized_summary.json
Kullanım: python analysis/59_e1_studentized.py
Yazan: Claude Code (Opus 5.5), 2026-10-04.
"""
from __future__ import annotations

import hashlib
import importlib
import json
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE))
m34 = importlib.import_module("34_a1_residual_change")
m43 = importlib.import_module("43_e1_conditional_change")
OUT = ROOT / "data" / "derived" / "empirical_fixes"
E1CSV = OUT / "e1_conditional_change.csv"


def studentized(X: np.ndarray, y: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Dış-studentize artık (kapalı formül), kaldıraç ve PRESS hatası."""
    n, p = X.shape
    XtXi = np.linalg.inv(X.T @ X)
    r = y - X @ (XtXi @ X.T @ y)
    h = np.einsum("ij,jk,ik->i", X, XtXi, X)
    s2 = (r @ r) / (n - p)
    s2_i = ((n - p) * s2 - r ** 2 / (1.0 - h)) / (n - p - 1)
    return r / np.sqrt(s2_i * (1.0 - h)), h, r / (1.0 - h)


def studentized_refit(X: np.ndarray, y: np.ndarray) -> np.ndarray:
    """Aynı istatistik, her sistem dışarıda açık yeniden uydurmayla: t_i = e_i / √(s₍ᵢ₎² (1 + x_i'(X₍ᵢ₎'X₍ᵢ₎)⁻¹x_i))."""
    n, p = X.shape
    t = np.empty(n)
    for i in range(n):
        k = np.arange(n) != i
        Xi, yi = X[k], y[k]
        XtXi = np.linalg.inv(Xi.T @ Xi)
        b = XtXi @ Xi.T @ yi
        ri = yi - Xi @ b
        s2i = (ri @ ri) / (n - 1 - p)
        e = y[i] - X[i] @ b
        t[i] = e / np.sqrt(s2i * (1.0 + X[i] @ XtXi @ X[i]))
    return t


def main() -> int:
    data = m34.load()
    e1 = pd.read_csv(E1CSV, encoding="utf-8-sig")
    rows, cells = [], []
    worst_closed_vs_refit, worst_press_err = 0.0, 0.0
    for (y0, y1) in m43.PAIRS:
        pair = f"{y0}->{y1}"
        for sc, sp in m43.SPECS:
            f = m43.pair_frame(data, y0, y1, sc, sp)
            X = m43.design(f.dC.to_numpy(float), f.C0.to_numpy(float))
            iso = list(f.index)
            it = iso.index("TUR")
            n = len(iso)
            for meas in m43.MEASURES:
                y = f[meas].to_numpy(float)
                t, h, e = studentized(X, y)
                t2 = studentized_refit(X, y)
                worst_closed_vs_refit = max(worst_closed_vs_refit, float(np.abs(t - t2).max()))
                if not np.all(np.sign(t) == np.sign(e)):
                    raise SystemExit(f"DUR (kapı): t ve e işaretçe farklı ({pair} {sc}/{sp} {meas})")
                ref = e1[(e1.pair == pair) & (e1.scope == sc) & (e1.spec == sp) & (e1.measure == meas)].set_index("iso3").loc[iso]
                rank_press = np.array([int((e < e[j]).sum() + 1) for j in range(n)])
                if not np.array_equal(rank_press, ref.rank_cond.to_numpy(int)):
                    raise SystemExit(f"DUR (kapı): PRESS sırası betik 43'ten farklı ({pair} {sc}/{sp} {meas})")
                worst_press_err = max(worst_press_err, float(np.abs(e - ref.loo_err.to_numpy(float)).max()))
                rank_t = np.array([int((t < t[j]).sum() + 1) for j in range(n)])
                for j, c in enumerate(iso):
                    rows.append({"pair": pair, "scope": sc, "spec": sp, "measure": meas, "iso3": c, "n": n,
                                 "leverage": round(float(h[j]), 4), "press_err": round(float(e[j]), 4),
                                 "t_stud": round(float(t[j]), 4), "rank_press": int(rank_press[j]),
                                 "rank_stud": int(rank_t[j]), "p_stud": round(int(rank_t[j]) / n, 4)})
                cells.append({"pair": pair, "scope": sc, "spec": sp, "measure": meas, "n": n, "df": n - X.shape[1] - 1,
                              "tur_leverage": round(float(h[it]), 4), "tur_t": round(float(t[it]), 4),
                              "tur_rank_press": int(rank_press[it]), "tur_p_press": round(int(rank_press[it]) / n, 4),
                              "tur_rank_stud": int(rank_t[it]), "tur_p_stud": round(int(rank_t[it]) / n, 4),
                              "reject_stud": bool(int(rank_t[it]) / n <= m43.ALPHA)})
    if worst_closed_vs_refit > 1e-8:
        raise SystemExit(f"DUR (kapı): kapalı formül ile yeniden uydurma farkı {worst_closed_vs_refit}")
    if worst_press_err > 1e-3:
        raise SystemExit(f"DUR (kapı): PRESS e betik 43'ten farklı ({worst_press_err})")
    cdf = pd.DataFrame(cells)
    prim = cdf[(cdf.pair == "2015->2025") & (cdf.measure == "d_sd") & (cdf.spec == "linear")].set_index("scope")
    OUT.mkdir(parents=True, exist_ok=True)
    tmp = OUT / "e1_studentized.csv.tmp"
    pd.DataFrame(rows).to_csv(tmp, index=False, encoding="utf-8")
    os.replace(tmp, OUT / "e1_studentized.csv")
    summ = {"note": "E1s — dış-studentize koşullu sıra; SONRADAN eklenen düzeltme (RESULTS_EMPIRICAL_FIXES.md §0.14). Betik 43'ün "
                    "PRESS sonuçları birincil kayıt olarak kalır.",
            "gates": {"closed_vs_refit_max": worst_closed_vs_refit, "press_err_vs_betik43_max": round(worst_press_err, 6),
                      "press_rank_vs_betik43": "aynı (16 hücre)", "sign_t_vs_e": "aynı"},
            "cells": cdf.to_dict("records"),
            "primary": {"p_stud_all": float(prim.loc["all", "tur_p_stud"]), "p_stud_oecd": float(prim.loc["oecd", "tur_p_stud"]),
                        "p_press_all": float(prim.loc["all", "tur_p_press"]), "p_press_oecd": float(prim.loc["oecd", "tur_p_press"])},
            "n_cells_reject_stud": int(cdf.reject_stud.sum()),
            "script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
    tmp = OUT / "e1_studentized_summary.json.tmp"
    tmp.write_text(json.dumps(summ, ensure_ascii=False, indent=1), encoding="utf-8")
    os.replace(tmp, OUT / "e1_studentized_summary.json")
    print("kapılar:", summ["gates"])
    print(cdf[["pair", "scope", "spec", "measure", "n", "tur_leverage", "tur_t", "tur_rank_press", "tur_rank_stud", "tur_p_stud"]].to_string(index=False))
    print("birincil:", summ["primary"], "| p ≤ 0,10 hücre:", summ["n_cells_reject_stud"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
