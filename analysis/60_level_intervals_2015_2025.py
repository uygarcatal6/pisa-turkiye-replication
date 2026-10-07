# -*- coding: utf-8 -*-
"""
60_level_intervals_2015_2025.py — L1: Tablo 1'in 2015 ve 2025 düzey artıkları için ilişkili bootstrap aralığı.

Ön-belirleme: analysis/RESULTS_EMPIRICAL_FIXES.md §0.15 (7 Eki 2026, betik yazılmadan önce; sha256 f5487a1a02a8…).
SONRADAN eklenen belirsizlik kalemi; nokta kestirimleri ve sıralar değişmez.

Yöntem betik 31'in 2003 bloğu: her çekilişte yenilikçi alan ortalaması y_i ~ y_i + se_y,i·z1 ve çekirdek
x_i ~ x_i + se_x,i·(ρ_i z1 + √(1−ρ_i²) z2); ρ_i = combine_rho(örnekleme, atama); doğru yeniden uydurulur; artık
y_b − f_b(x_b). Nokta kestirimleri Tablo 1'in dosyalarından, SE ve korelasyon betik 43'ün mikroveri önbelleğinden.
Girdi: data/derived/mechanisms/placebo_conditional_{2015cps,2025}.csv, data/derived/cache/e1_boot_inputs_{2015,2025}.csv
Çıktı: data/derived/empirical_fixes/l1_level_intervals.csv, l1_level_intervals_summary.json
Kullanım: python analysis/60_level_intervals_2015_2025.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import _pisa_puf as P  # noqa: E402

D = HERE.parent / "data" / "derived"
OUT = D / "empirical_fixes"
B, SEED = 2000, 20261007
FILES = {2015: ("placebo_conditional_2015cps.csv", "cps2015_mean_weighted"),
         2025: ("placebo_conditional_2025.csv", "cps2025_mean")}
TOL, TOL_EXC = 0.01, {(2025, "BEL"): 0.02}   # §0.15 kapı (ii); BEL istisnası betik 43'teki belgelenmiş sapma


CYP_RHO = None   # §0.15 sapma: None = öteki sistemlerin birleşik ρ medyanı; duyarlılık için komut satırından 0 / 0.95


def add_published(inp, fit, ycol):
    """§0.15 sapma: 2025 kamu mikroverisinde olmayan fit sistemleri (CYP) için yayımlanmış SE'ler (analysis_panel.csv)."""
    eksik = sorted(set(fit.iso3) - set(inp.index))
    if not eksik:
        return inp
    assert eksik == ["CYP"], eksik
    pan = pd.read_csv(D / "analysis_panel.csv")
    r = pan[(pan.iso3 == "CYP") & (pan.cycle == 2025)].iloc[0]
    core_se = float(np.mean([r.math_se, r.reading_se, r.science_se]))          # betik 31 tanımı
    g = inp.loc[sorted(set(fit.iso3) & set(inp.index))]          # yalnız fit sistemleri (UZB fit dışı ve NaN)
    rho_all = P.combine_rho(g.rho_s.to_numpy(float), g.rho_i.to_numpy(float), g.dom_se_s.to_numpy(float),
                            g.dom_se_i.to_numpy(float), g.core_se_s.to_numpy(float), g.core_se_i.to_numpy(float))
    assert np.isfinite(rho_all).all() and len(rho_all) == 83, len(rho_all)
    rho = float(np.median(rho_all)) if CYP_RHO is None else float(CYP_RHO)
    f = fit[(fit.iso3 == "CYP")].iloc[0]
    row = {"dom_mean": float(f[ycol]), "dom_se": float(r.cps2025_se), "dom_se_s": float(r.cps2025_se), "dom_se_i": 0.0,
           "core_mean": float(f.core), "core_se": core_se, "core_se_s": core_se, "core_se_i": 0.0,
           "rho_s": rho, "rho_i": 0.0, "rho": rho}
    print(f"[sapma §0.15] CYP yayımlanmış SE: alan {r.cps2025_se:.4f}, çekirdek {core_se:.4f}; ρ = {rho:.3f}")
    return pd.concat([inp, pd.DataFrame([row], index=["CYP"])])


def puf_inputs(cyc, inn):
    """§0.15 genişletme: betik 31 (2003, PROB) ve 33 (2012 CBA, CPRO) PUF blokları aynen; önbellekten okunur."""
    spec = P.parse_datalist(P.ROOT / P.REGISTRY[cyc]["syn"])
    roots = (inn, "MATH", "READ", "SCIE")
    want = ["CNT", "W_FSTUWT", *P.REPW] + [c for r in roots for c in P.pv_cols(spec, r)]
    df = P.read_columns(cyc, want)
    if cyc == "2012cba":
        df["CNT"] = df.CNT.replace({"TAP": "TWN"})
    est = {r: P.brr_pv_stat(df, P.pv_cols(spec, r), "W_FSTUWT", P.REPW).set_index("iso3") for r in roots}
    core_pv = [[P.pv_cols(spec, r)[i] for r in ("MATH", "READ", "SCIE")] for i in range(5)]
    rho = P.brr_pv_corr(df, P.pv_cols(spec, inn), core_pv, "W_FSTUWT", P.REPW).set_index("iso3")
    g = pd.DataFrame({"dom_mean": est[inn]["mean"], "dom_se": est[inn]["se"],
                      "dom_se_s": est[inn]["se_sampling"], "dom_se_i": est[inn]["se_imputation"],
                      "rho_s": rho["rho_sampling"], "rho_i": rho["rho_imputation"]})
    for k, col in (("se", "se"), ("se_s", "se_sampling"), ("se_i", "se_imputation")):
        g[f"core_{k}"] = pd.concat([est[r][col] for r in ("MATH", "READ", "SCIE")], axis=1).mean(axis=1)
    g["core_mean"] = pd.concat([est[r]["mean"] for r in ("MATH", "READ", "SCIE")], axis=1).mean(axis=1)
    return g


def early_cycles(summ):
    """2003 ve 2012 için sıra aralığı (Tablo 1'in artık aralıkları betik 31/33'ten kalır)."""
    out_rows = []
    for year, cyc, inn, fname, ycol, cdef in [
            (2003, 2003, "PROB", "placebo_conditional_2003ps_puf.csv", "ps2003", "mat/oku/fen"),
            (2012, "2012cba", "CPRO", "placebo_conditional_2012ps_puf.csv", "ps2012_puf", "PUF mat/oku/fen")]:
        rng = np.random.default_rng(SEED + year)
        fit = pd.read_csv(D / "mechanisms" / fname)
        fit = fit[fit.core_def == cdef]
        inp = puf_inputs(cyc, inn)
        for (scope, spec), s in fit.groupby(["scope", "spec"], sort=False):
            s = s.reset_index(drop=True)
            g = inp.loc[s.iso3]
            if max(np.abs(g.core_mean.to_numpy() - s.core.to_numpy()).max(),
                   np.abs(g.dom_mean.to_numpy() - s[ycol].to_numpy()).max()) > 1e-6:
                raise SystemExit(f"DUR (kapı): {year} {scope} {spec} PUF girdileri csv ile uyuşmuyor")
            deg = 1 if spec == "linear" else 2
            x, y = s.core.to_numpy(float), s[ycol].to_numpy(float)
            _, r0 = ols(x, y, deg)
            if np.max(np.abs(r0 - s.residual.to_numpy(float))) > 1e-6:
                raise SystemExit(f"DUR (kapı iii): {year} {scope} {spec} nokta artıkları yeniden üretilmedi")
            xs, ys = g.core_se.to_numpy(float), g.dom_se.to_numpy(float)
            rr = P.combine_rho(g.rho_s.to_numpy(float), g.rho_i.to_numpy(float), g.dom_se_s.to_numpy(float),
                               g.dom_se_i.to_numpy(float), g.core_se_s.to_numpy(float), g.core_se_i.to_numpy(float))
            boot, ranks = np.empty((B, len(s))), np.empty((B, len(s)))
            for k in range(B):
                z1, z2 = rng.standard_normal(len(s)), rng.standard_normal(len(s))
                yb = y + ys * z1
                xb = x + xs * (rr * z1 + np.sqrt(np.maximum(1 - rr ** 2, 0)) * z2)
                _, rb = ols(xb, yb, deg)
                boot[k], ranks[k] = rb, pd.Series(rb).rank(method="min").to_numpy()
            lo, hi = np.percentile(boot, [2.5, 97.5], axis=0)
            rlo, rhi = np.percentile(ranks, [2.5, 97.5], axis=0)
            o = s[["iso3", "scope", "spec", "residual", "rank_low", "resid_lo95", "resid_hi95"]].rename(
                columns={"resid_lo95": "resid_lo95_script31_33", "resid_hi95": "resid_hi95_script31_33"})
            o["year"], o["resid_lo95"], o["resid_hi95"] = year, lo, hi
            o["resid_boot_se"], o["rank_lo95"], o["rank_hi95"], o["rho_used"] = boot.std(axis=0, ddof=1), rlo, rhi, rr
            out_rows.append(o)
            t = o[o.iso3 == "TUR"].iloc[0]
            summ[f"{year}_{scope}_{spec}"] = {
                "n": int(len(s)), "TUR_residual": round(float(t.residual), 1),
                "TUR_ci95_script60": [round(float(t.resid_lo95), 1), round(float(t.resid_hi95), 1)],
                "TUR_ci95_script31_33": [round(float(t.resid_lo95_script31_33), 1), round(float(t.resid_hi95_script31_33), 1)],
                "TUR_rank": int(t.rank_low), "TUR_rank_ci95": [int(t.rank_lo95), int(t.rank_hi95)],
                "n_ci_excluding_zero": int(((o.resid_hi95 < 0) | (o.resid_lo95 > 0)).sum()),
            }
    return out_rows


def ols(x, y, deg):
    X = np.vander(x, deg + 1, increasing=True)
    beta, *_ = np.linalg.lstsq(X, y, rcond=None)
    return beta, y - X @ beta


def main() -> int:
    rng = np.random.default_rng(SEED)
    rows, summ = [], {"prespec": "RESULTS_EMPIRICAL_FIXES.md §0.15", "B": B, "seed": SEED}
    for year, (fname, ycol) in FILES.items():
        fit = pd.read_csv(D / "mechanisms" / fname)
        inp = pd.read_csv(D / "cache" / f"e1_boot_inputs_{year}.csv").set_index("iso3")
        if year == 2025:
            inp = add_published(inp, fit, ycol)
        for (scope, spec), s in fit.groupby(["scope", "spec"], sort=False):
            s = s.reset_index(drop=True)
            miss = sorted(set(s.iso3) - set(inp.index))
            if miss:
                raise SystemExit(f"DUR (kapı i): {year} {scope} {spec} önbellekte yok: {miss}")
            g = inp.loc[s.iso3]
            dx = (g.core_mean.to_numpy() - s.core.to_numpy())
            dy = (g.dom_mean.to_numpy() - s[ycol].to_numpy())
            for iso, a, b_ in zip(s.iso3, np.abs(dx), np.abs(dy)):
                tol = TOL_EXC.get((year, iso), TOL)
                if a > tol or b_ > tol:
                    raise SystemExit(f"DUR (kapı ii): {year} {iso} çekirdek farkı {a:.4f}, alan farkı {b_:.4f} > {tol}")
            deg = 1 if spec == "linear" else 2
            x, y = s.core.to_numpy(float), s[ycol].to_numpy(float)
            _, r0 = ols(x, y, deg)
            if np.max(np.abs(r0 - s.residual.to_numpy(float))) > 1e-6:
                raise SystemExit(f"DUR (kapı iii): {year} {scope} {spec} nokta artıkları yeniden üretilmedi")
            xs, ys = g.core_se.to_numpy(float), g.dom_se.to_numpy(float)
            rr = P.combine_rho(g.rho_s.to_numpy(float), g.rho_i.to_numpy(float),
                               g.dom_se_s.to_numpy(float), g.dom_se_i.to_numpy(float),
                               g.core_se_s.to_numpy(float), g.core_se_i.to_numpy(float))
            boot, ranks = np.empty((B, len(s))), np.empty((B, len(s)))
            for k in range(B):
                z1, z2 = rng.standard_normal(len(s)), rng.standard_normal(len(s))
                yb = y + ys * z1
                xb = x + xs * (rr * z1 + np.sqrt(np.maximum(1 - rr ** 2, 0)) * z2)
                _, rb = ols(xb, yb, deg)
                boot[k] = rb
                ranks[k] = pd.Series(rb).rank(method="min").to_numpy()
            lo, hi = np.percentile(boot, [2.5, 97.5], axis=0)
            rlo, rhi = np.percentile(ranks, [2.5, 97.5], axis=0)
            out = s[["iso3", "scope", "spec", "residual", "rank_low"]].copy()
            out["year"] = year
            out["resid_lo95"], out["resid_hi95"] = lo, hi
            out["resid_boot_se"] = boot.std(axis=0, ddof=1)
            out["rank_lo95"], out["rank_hi95"] = rlo, rhi
            out["rho_used"] = rr
            rows.append(out)
            t = out[out.iso3 == "TUR"].iloc[0]
            summ[f"{year}_{scope}_{spec}"] = {
                "n": int(len(s)), "TUR_residual": round(float(t.residual), 1),
                "TUR_ci95": [round(float(t.resid_lo95), 1), round(float(t.resid_hi95), 1)],
                "TUR_boot_se": round(float(t.resid_boot_se), 2),
                "TUR_rank": int(t.rank_low), "TUR_rank_ci95": [int(t.rank_lo95), int(t.rank_hi95)],
                "TUR_rho": round(float(t.rho_used), 3),
                "n_ci_excluding_zero": int(((out.resid_hi95 < 0) | (out.resid_lo95 > 0)).sum()),
            }
    rows += early_cycles(summ)
    OUT.mkdir(parents=True, exist_ok=True)
    pd.concat(rows).to_csv(OUT / "l1_level_intervals.csv", index=False)
    (OUT / "l1_level_intervals_summary.json").write_text(json.dumps(summ, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps(summ, ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    if len(sys.argv) > 1:                       # duyarlılık: python 60_... <cyp_rho> ; çıktı yazılmaz
        CYP_RHO = float(sys.argv[1]); OUT = D / "empirical_fixes" / f"_l1_duyarlilik_cyp_rho_{sys.argv[1]}"
    raise SystemExit(main())
