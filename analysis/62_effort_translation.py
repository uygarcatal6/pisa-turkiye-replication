# -*- coding: utf-8 -*-
"""
62_effort_translation.py — EF: CMPS − çekirdek hızlı tahmin farkının 2025 artığına puan karşılığı (ülkeler arası, OECD).

Ön-belirleme: analysis/RESULTS_EMPIRICAL_FIXES.md §0.16 (7 Eki 2026, betik yazılmadan önce). SONRADAN eklenen çeviri.
Model: r_c = α + γ·g_c (+ e), g_c = 100 × (CMPS hızlı tahmin payı − çekirdek payı), OLS, HC3. Birincil: NT15, OECD · doğrusal,
Türkiye dışarıda uydurulur; Türkiye'nin payı = γ̂ × (g_TUR − ḡ_37). İkinciller: Türkiye dahil, öteki eşikler, karesel artık,
iki regresörlü model (çekirdek ve CMPS payları ayrı).
Girdi: outputs/tables/pisa2025/h7_country.csv, outputs/tables/pisa2025/h7_results.csv,
       data/derived/mechanisms/placebo_conditional_2025.csv
Çıktı: data/derived/empirical_fixes/ef_effort_translation.csv, ef_effort_translation_summary.json
Kullanım: python analysis/62_effort_translation.py
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "derived" / "empirical_fixes"


def hc3(X, y):
    X = np.asarray(X, float); y = np.asarray(y, float)
    XtX_inv = np.linalg.inv(X.T @ X)
    b = XtX_inv @ X.T @ y
    e = y - X @ b
    h = np.einsum("ij,jk,ik->i", X, XtX_inv, X)
    meat = (X * (e / (1 - h))[:, None] ** 2).T @ X
    V = XtX_inv @ meat @ XtX_inv
    return b, np.sqrt(np.diag(V)), e


def main() -> int:
    h = pd.read_csv(ROOT / "outputs" / "tables" / "pisa2025" / "h7_country.csv")
    hr = pd.read_csv(ROOT / "outputs" / "tables" / "pisa2025" / "h7_results.csv").set_index("threshold")
    fit = pd.read_csv(ROOT / "data" / "derived" / "mechanisms" / "placebo_conditional_2025.csv")
    rows, summ = [], {"prespec": "RESULTS_EMPIRICAL_FIXES.md §0.16 (sonradan)"}
    for thr in ["NT15", "NT10", "NT20", "FIX5S"]:
        g = h[h.threshold == thr].set_index("CNT")
        if len(g) != 38:
            raise SystemExit(f"DUR: {thr} {len(g)} sistem")
        # kapılar: Türkiye'nin farkı ve OECD ortalaması H7 özetiyle
        if abs(g.loc["TUR", "diff_share"] - hr.loc[thr, "tur_diff"]) > 1e-9:
            raise SystemExit(f"DUR: {thr} TUR diff uyuşmuyor")
        mean38 = float(g.diff_share.mean())
        summ[f"{thr}_oecd_avg_check"] = {"mean38": mean38, "h7_oecd_avg_diff": float(hr.loc[thr, "oecd_avg_diff"]),
                                         "abs_diff": abs(mean38 - float(hr.loc[thr, "oecd_avg_diff"]))}
        for spec in ["linear", "quadratic"]:
            f = fit[(fit.scope == "oecd") & (fit.spec == spec)].set_index("iso3")
            common = sorted(set(f.index) & set(g.index))
            if len(common) != 38:
                raise SystemExit(f"DUR: {thr} {spec} eşleşen {len(common)}")
            d = pd.DataFrame({"r": f.loc[common, "residual"], "gap": 100 * g.loc[common, "diff_share"],
                              "core": 100 * g.loc[common, "core_share"], "cmps": 100 * g.loc[common, "cmps_share"]})
            for sample in ["excl_TUR", "incl_TUR"]:
                s = d.drop(index="TUR") if sample == "excl_TUR" else d
                X = np.column_stack([np.ones(len(s)), s.gap])
                b, se, e = hc3(X, s.r)
                ref = float(d.drop(index="TUR").gap.mean())
                dg = float(d.loc["TUR", "gap"] - ref)
                contrib = b[1] * dg
                lo, hi = (b[1] - 1.96 * se[1]) * dg, (b[1] + 1.96 * se[1]) * dg
                ss = float(((s.r - s.r.mean()) ** 2).sum())
                r2 = 1 - float(e @ e) / ss
                # iki regresörlü model (ikincil)
                X2 = np.column_stack([np.ones(len(s)), s.core, s.cmps])
                b2, se2, _ = hc3(X2, s.r)
                ref_core = float(d.drop(index="TUR").core.mean()); ref_cmps = float(d.drop(index="TUR").cmps.mean())
                c2 = b2[1] * (d.loc["TUR", "core"] - ref_core) + b2[2] * (d.loc["TUR", "cmps"] - ref_cmps)
                row = {"threshold": thr, "spec": spec, "sample": sample, "n": int(len(s)),
                       "gamma": b[1], "gamma_se_hc3": se[1], "gamma_lo95": b[1] - 1.96 * se[1],
                       "gamma_hi95": b[1] + 1.96 * se[1], "r2": r2,
                       "tur_gap_pp": float(d.loc["TUR", "gap"]), "ref_gap_pp_37": ref, "tur_excess_gap_pp": dg,
                       "tur_residual": float(d.loc["TUR", "r"]), "tur_contrib_pts": contrib,
                       "tur_contrib_lo95": min(lo, hi), "tur_contrib_hi95": max(lo, hi),
                       "share_of_residual": contrib / float(d.loc["TUR", "r"]),
                       "two_reg_core_coef": b2[1], "two_reg_core_se": se2[1], "two_reg_cmps_coef": b2[2],
                       "two_reg_cmps_se": se2[2], "two_reg_tur_contrib_pts": float(c2)}
                rows.append(row)
    res = pd.DataFrame(rows)
    OUT.mkdir(parents=True, exist_ok=True)
    res.to_csv(OUT / "ef_effort_translation.csv", index=False)
    prim = res[(res.threshold == "NT15") & (res.spec == "linear") & (res["sample"] == "excl_TUR")].iloc[0]
    summ["primary"] = {k: (round(float(v), 4) if isinstance(v, (float, np.floating)) else (int(v) if isinstance(v, (np.integer,)) else v)) for k, v in prim.items()}
    summ["range_contrib_all_cells"] = [round(float(res.tur_contrib_pts.min()), 2), round(float(res.tur_contrib_pts.max()), 2)]
    (OUT / "ef_effort_translation_summary.json").write_text(json.dumps(summ, ensure_ascii=False, indent=1), encoding="utf-8")
    print(res[["threshold", "spec", "sample", "n", "gamma", "gamma_lo95", "gamma_hi95", "r2", "tur_excess_gap_pp",
               "tur_residual", "tur_contrib_pts", "tur_contrib_lo95", "tur_contrib_hi95", "two_reg_tur_contrib_pts"]]
          .round(3).to_string(index=False))
    print(json.dumps({k: v for k, v in summ.items() if k.endswith("check")}, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
