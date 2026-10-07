# -*- coding: utf-8 -*-
"""
36_a9_three_regressor.py — ek analiz isteği A9: skaler çekirdek yerine matematik, okuma ve fen AYRI regresör.

ÖNCEDEN BELİRLENEN SEÇİMLER (25 Eyl 2026, sonuç görülmeden):
  * Model A9: I = a + b_M·M + b_R·R + b_S·S + e, yalnız DOĞRUSAL (üç regresörlü karesel model n = 28–30'da aşırı parametreli).
  * Karşılaştırma: aynı örneklemde skaler doğrusal model I = a + b·C + e (C = (M+R+S)/3). Örneklemler makaledeki birincil
    spesifikasyonlarla aynı ülke kümeleridir (placebo_conditional_* dosyalarındaki kapsam listeleri).
  * Veri: 2003 ve 2012 alan ortalamaları PUF'tan (31 ve 33 ile aynı önbellek, ağırlık W_FSTUWT, 5 PV ortalaması; 2012'de aynı
    öğrencilerin kâğıt çekirdeği); 2015 ve 2025 panelden (yayımlanmış tablolar), yenilikçi alan 2015'te mikroveri ağırlıklı
    ortalama (placebo_conditional_2015cps.csv), 2025'te panel (Tablo I.B1.2a.4).
  * Rapor: n, katsayılar, RMSE, R², Türkiye (ve HUN, SWE, GEO) artığı puan ve RMSE biriminde, alttan sıra.
Doğrulama: yeniden kurulan skaler çekirdeğin makale dosyalarındaki çekirdekle farkı raporlanır (beklenen < 0,05 puan).
Çıktı: data/derived/mechanisms/three_regressor.csv, three_regressor_summary.json
Kullanım: python analysis/36_a9_three_regressor.py      Yazan: Claude Opus 5.5 (Cowork), 2026-09-25.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import _pisa_puf as P  # noqa: E402

ROOT = HERE.parent
MECH = ROOT / "data" / "derived" / "mechanisms"
FOCUS = ["TUR", "HUN", "SWE", "GEO"]
RENAME_2012 = {"TAP": "TWN"}


def puf_means(cycle, roots, dom_root) -> pd.DataFrame:
    spec = P.parse_datalist(P.ROOT / P.REGISTRY[cycle]["syn"])
    want = ["CNT", "W_FSTUWT", *P.REPW] + [c for r in roots for c in P.pv_cols(spec, r)]
    df = P.read_columns(cycle, want)  # 31/33 ile aynı kolon kümesi → önbellekten
    df["CNT"] = df.CNT.replace(RENAME_2012)
    out = {}
    for r in ["MATH", "READ", "SCIE", dom_root]:
        means = []
        for pv in P.pv_cols(spec, r):
            v = df[pv].to_numpy(float)
            w = df["W_FSTUWT"].to_numpy(float)
            ok = np.isfinite(v) & np.isfinite(w)
            g = pd.DataFrame({"CNT": df.CNT[ok], "wv": w[ok] * v[ok], "w": w[ok]}).groupby("CNT").sum()
            means.append(g.wv / g.w)
        out[r] = pd.concat(means, axis=1).mean(axis=1)
    m = pd.DataFrame(out).rename(columns={"MATH": "M", "READ": "R", "SCIE": "S", dom_root: "I"})
    m.index.name = "iso3"
    return m.reset_index()


def samples() -> dict:
    s = {}
    a = pd.read_csv(MECH / "placebo_conditional_2003ps_puf.csv", encoding="utf-8-sig")
    a = a[(a.core_def == "mat/oku/fen") & (a.spec == "linear")]
    s[2003] = {sc: a[a.scope == sc][["iso3", "core"]] for sc in ["all", "oecd"]}
    b = pd.read_csv(MECH / "placebo_conditional_2012ps_puf.csv", encoding="utf-8-sig")
    b = b[(b.core_def == "PUF mat/oku/fen") & (b.spec == "linear")]
    s[2012] = {sc: b[b.scope == sc][["iso3", "core"]] for sc in ["all", "oecd"]}
    c = pd.read_csv(MECH / "placebo_conditional_2015cps.csv", encoding="utf-8-sig")
    c = c[c.spec == "linear"]
    s[2015] = {sc: c[c.scope == sc][["iso3", "core", "cps2015_mean_weighted"]] for sc in ["all", "oecd"]}
    d = pd.read_csv(MECH / "placebo_conditional_2025.csv", encoding="utf-8-sig")
    d = d[d.spec == "linear"]
    s[2025] = {sc: d[d.scope == sc][["iso3", "core", "cps2025_mean"]] for sc in ["all", "oecd"]}
    return s


def fit(y, X):
    beta, *_ = np.linalg.lstsq(X, y, rcond=None)
    res = y - X @ beta
    n, k = X.shape
    rmse = float(np.sqrt(res @ res / (n - k)))
    r2 = 1 - float(res @ res) / float(((y - y.mean()) ** 2).sum())
    return beta, res, rmse, r2


def main() -> int:
    smp = samples()
    panel = pd.read_csv(ROOT / "data" / "derived" / "analysis_panel.csv")
    dom = {
        2003: puf_means(2003, ["PROB", "MATH", "READ", "SCIE"], "PROB"),
        2012: puf_means("2012cba", ["CPRO", "CMAT", "CREA", "MATH", "READ", "SCIE"], "CPRO"),
    }
    for cy, col in [(2015, "cps2015_mean_weighted"), (2025, "cps2025_mean")]:
        p = panel[panel.cycle == cy][["iso3", "math_mean", "reading_mean", "science_mean"]].rename(
            columns={"math_mean": "M", "reading_mean": "R", "science_mean": "S"})
        dom[cy] = p.merge(smp[cy]["all"][["iso3", col]].rename(columns={col: "I"}), on="iso3", how="inner")
    rows, summ = [], {}
    for cy in [2003, 2012, 2015, 2025]:
        for sc in ["all", "oecd"]:
            s = smp[cy][sc][["iso3", "core"]].merge(dom[cy], on="iso3", how="left")
            miss = s[s[["M", "R", "S", "I"]].isna().any(axis=1)].iso3.tolist()
            s = s.dropna(subset=["M", "R", "S", "I"])
            core_chk = float((s[["M", "R", "S"]].mean(axis=1) - s["core"]).abs().max())
            y = s["I"].to_numpy(float)
            Xs = np.column_stack([np.ones(len(s)), s["core"].to_numpy(float)])
            X3 = np.column_stack([np.ones(len(s)), s[["M", "R", "S"]].to_numpy(float)])
            bs, rs, rms, r2s = fit(y, Xs)
            b3, r3, rm3, r23 = fit(y, X3)
            key = f"{cy}|{sc}"
            summ[key] = {"n": int(len(s)), "dropped_missing": miss, "core_rebuild_max_abs_diff": round(core_chk, 4),
                         "scalar": {"slope": round(float(bs[1]), 3), "rmse": round(rms, 2), "r2": round(r2s, 3)},
                         "three": {"b_math": round(float(b3[1]), 3), "b_read": round(float(b3[2]), 3), "b_scie": round(float(b3[3]), 3),
                                   "rmse": round(rm3, 2), "r2": round(r23, 3)}}
            rk_s = pd.Series(rs).rank(method="min").to_numpy()
            rk_3 = pd.Series(r3).rank(method="min").to_numpy()
            for i, iso in enumerate(s.iso3):
                rec = {"cycle": cy, "scope": sc, "iso3": iso, "n": int(len(s)),
                       "resid_scalar": round(float(rs[i]), 3), "resid_sd_scalar": round(float(rs[i] / rms), 3), "rank_scalar": int(rk_s[i]),
                       "resid_three": round(float(r3[i]), 3), "resid_sd_three": round(float(r3[i] / rm3), 3), "rank_three": int(rk_3[i])}
                rows.append(rec)
                if iso in FOCUS:
                    summ[key][iso] = {k: rec[k] for k in ["resid_scalar", "resid_sd_scalar", "rank_scalar", "resid_three", "resid_sd_three", "rank_three"]}
    tmp = MECH / "three_regressor.csv.tmp"
    pd.DataFrame(rows).to_csv(tmp, index=False, encoding="utf-8")
    os.replace(tmp, MECH / "three_regressor.csv")
    tmp = MECH / "three_regressor_summary.json.tmp"
    tmp.write_text(json.dumps(summ, ensure_ascii=False, indent=1), encoding="utf-8")
    os.replace(tmp, MECH / "three_regressor_summary.json")
    print(f"{'döngü|kapsam':<12}{'n':>4} {'çekirdek fark':>13} {'skaler: TUR':>12} {'sıra':>6} {'RMSE':>6}  {'3 regr: TUR':>12} {'sıra':>6} {'RMSE':>6}  b_M/b_R/b_S")
    for k, v in summ.items():
        t = v.get("TUR", {})
        print(f"{k:<12}{v['n']:>4} {v['core_rebuild_max_abs_diff']:>13} {t.get('resid_scalar'):>12} {str(t.get('rank_scalar'))+'/'+str(v['n']):>6} {v['scalar']['rmse']:>6}  "
              f"{t.get('resid_three'):>12} {str(t.get('rank_three'))+'/'+str(v['n']):>6} {v['three']['rmse']:>6}  {v['three']['b_math']}/{v['three']['b_read']}/{v['three']['b_scie']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
