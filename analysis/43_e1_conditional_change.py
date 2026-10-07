# -*- coding: utf-8 -*-
"""
43_e1_conditional_change.py — editoryal düzeltme E1 (F3): 2015→2025 artık derinleşmesi KOŞULLU olarak uçta mı?

Soru (COWORK_AMPIRIK_DUZELTMELER.md E1): Betik 34'ün sıraladığı artık değişimi koşulsuzdur. Çekirdek kazanımı yeni alana tam
aktarılmıyorsa hızlı yükselen sistemlerin artığı mekanik olarak düşer. Türkiye'nin değişimi, çekirdek değişimi (ΔC) ve başlangıç
düzeyi (C0) verildiğinde öngörülenden daha mı olumsuz?

ÖNCEDEN BELİRLENEN SEÇİMLER (RESULTS_EMPIRICAL_FIXES.md §0.2; commit 476fe4e, koşudan önce):
  * Çiftler 2015→2025 (birincil) ve 2003→2025 (ikincil); betik 34'ün dört spesifikasyonu (all/oecd × linear/quadratic);
    ortak sistemler ve d_sd/d_pts betik 34'ün `load()` işleviyle, aynı tanımla.
  * OLS d_i = α + β₁·ΔC_i + β₂·C0_i; HC3 standart hataları.
  * Türkiye'nin koşullu değeri = Türkiye dışarıda uydurulan modelin tahmin hatası; karşılaştırma = her sistemin kendi dışarıda
    tahmin hatası (OLS'de kesin eşitlik: e_i(−i) = r_i / (1 − h_ii); Türkiye için açık yeniden uydurmayla da kontrol edilir).
  * Sıra en olumsuzdan (#(e < e_TUR) + 1), p = sıra/N tek yönlü. Karar kuralı yalnız d_sd · 2015→2025 · linear hücrelerinden.
  * Bootstrap (--bootstrap; yalnız 2015→2025): B = 2000, tohum 20260926, korelasyonlu parametrik çekiliş (betik 31 bloğu);
    SE ve korelasyonlar mikroveriden (BRR Fay 0,5, W_FSTURWT1–80, Rubin M = 10). Kapılar §0.2'de.
SONRADAN EKLENENLER: 2026-09-26 (yerel koşu 1'den sonra) — bootstrap'ın 2015 CLPS yuvarlama kapısı Vol. V'te yayımlanmış ama
  2015 CPS mikroverisinde olmayan sistemi (CYP) paydaya katıyordu (51 satır); ön kayıttaki tanıma (50/50) uygun olarak yalnız
  mikroverisi olan satırlarda sayılır, dışarıda kalanlar `2015_published_without_microdata` olarak yazılır. Tanım değişmedi.
  2026-09-26 (yerel koşu 2, yazar onayı) — 2025 kapısına belgelenmiş BEL istisnası: yalnız BEL 2025 için tavan 0,02
  (dört alan). BEL'in mikroveri − yayımlanmış farkı mat −0,0031, oku +0,0116, fen +0,0032, CPS +0,0027; betik 51 teşhisi
  "neden bulunamadı" (PUF'ta çekirdek PV'si eksik 1 öğrenci, ağırlık payı %0,02). Diğer bütün sistemlerde eşik değişmedi;
  istisna kapı çıktısına `exceptions` olarak yazılır.
Girdi: data/derived/mechanisms/placebo_conditional_{2003ps_puf,2012ps_puf,2015cps,2025}.csv (betik 34 `load()` üzerinden),
       data/derived/placebo_backbone/residual_change.csv (kapı + koşulsuz sıra);
       --bootstrap için ayrıca data/pisa_microdata/2015/PUF_SPSS_COMBINED_CMB_STU_{QQQ,CPS}.zip,
       data/pisa/2025/database/CY09_MS_STU_PUF.zip, data/derived/analysis_panel.csv,
       data/derived/placebo_backbone/cps2015_crosscheck_oecd_volv.csv, data/derived/cps2015_country_means.csv.
Çıktı: data/derived/empirical_fixes/e1_conditional_change.csv, e1_summary.json; --bootstrap ile e1_bootstrap.csv
       (+ önbellek data/derived/cache/e1_boot_inputs_{2015,2025}.csv).
Kullanım: python analysis/43_e1_conditional_change.py              (nokta kestirimi; mikroveri gerekmez)
          python analysis/43_e1_conditional_change.py --bootstrap  (Windows; pyreadstat + mikroveri gerekir)
Yazan: Claude Code (bulut oturumu), 2026-09-26.
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
m34 = importlib.import_module("34_a1_residual_change")

D = ROOT / "data" / "derived"
OUT = D / "empirical_fixes"
CACHE = D / "cache"
RC = D / "placebo_backbone" / "residual_change.csv"
PAIRS = [(2015, 2025), (2003, 2025)]
SPECS = [("all", "linear"), ("all", "quadratic"), ("oecd", "linear"), ("oecd", "quadratic")]
MEASURES = {"d_sd": ("resid_sd", "rank_d_sd"), "d_pts": ("residual", "rank_d_pts")}
PRIMARY = {"pair": "2015->2025", "measure": "d_sd", "spec": "linear"}
ALPHA = 0.10
BOOT, SEED = 2000, 20260926
# SONRADAN (2026-09-26, yerel koşu 2, yazar onayı): 2025 kapısında belgelenmiş istisna (başlık notu). Betik 44 ve 50 bunu kullanır.
GATE_EXCEPTIONS_2025 = {"BEL": 0.02}


def gate_2025(diffs: pd.Series, tol: float) -> tuple[float, dict, bool]:
    """diffs: iso3 → |mikroveri − yayımlanmış|. İstisna dışı en büyük fark, eşiği aşan istisnalar ve geçip geçmediği."""
    d = diffs.dropna()
    exc = {k: round(float(d[k]), 5) for k in GATE_EXCEPTIONS_2025 if k in d.index and d[k] > tol}
    rest = d.drop(index=[k for k in GATE_EXCEPTIONS_2025 if k in d.index])
    mx = float(rest.max()) if len(rest) else 0.0
    return mx, exc, bool(mx <= tol and all(v <= GATE_EXCEPTIONS_2025[k] for k, v in exc.items()))


# ----------------------------------------------------------------------------- OLS araçları
def design(dC: np.ndarray, C0: np.ndarray) -> np.ndarray:
    return np.column_stack([np.ones_like(dC), dC, C0])


def ols_hc3(X: np.ndarray, y: np.ndarray):
    """β, HC3 SE, artık, kaldıraç. HC3: (X'X)⁻¹ X' diag(r²/(1−h)²) X (X'X)⁻¹ (MacKinnon–White 1985)."""
    XtX_inv = np.linalg.inv(X.T @ X)
    beta = XtX_inv @ X.T @ y
    r = y - X @ beta
    h = np.einsum("ij,jk,ik->i", X, XtX_inv, X)
    meat = X.T @ (X * (r ** 2 / (1.0 - h) ** 2)[:, None])
    se = np.sqrt(np.diag(XtX_inv @ meat @ XtX_inv))
    return beta, se, r, h


def press(X: np.ndarray, y: np.ndarray) -> np.ndarray:
    """Birini dışarıda bırakma tahmin hataları e_i = y_i − ŷ_i(−i) = r_i / (1 − h_ii)."""
    XtX_inv = np.linalg.inv(X.T @ X)
    r = y - X @ (XtX_inv @ X.T @ y)
    h = np.einsum("ij,jk,ik->i", X, XtX_inv, X)
    return r / (1.0 - h)


def rank_low(v: np.ndarray, i: int) -> int:
    return int((v < v[i]).sum() + 1)


# ----------------------------------------------------------------------------- nokta kestirimi
def pair_frame(data: dict, y0: int, y1: int, scope: str, spec: str) -> pd.DataFrame:
    a = data[y0][(data[y0].scope == scope) & (data[y0].spec == spec)].set_index("iso3")
    b = data[y1][(data[y1].scope == scope) & (data[y1].spec == spec)].set_index("iso3")
    common = a.index.intersection(b.index)
    if "TUR" not in common:
        raise SystemExit(f"DUR: {y0}->{y1} {scope}/{spec}: TUR ortak kümede yok")
    return pd.DataFrame({
        "d_sd": b.loc[common, "resid_sd"] - a.loc[common, "resid_sd"],
        "d_pts": b.loc[common, "residual"] - a.loc[common, "residual"],
        "dC": b.loc[common, "core"] - a.loc[common, "core"],
        "C0": a.loc[common, "core"],
    }).sort_index()


def gate_vs_residual_change(frames: dict) -> dict:
    rc = pd.read_csv(RC, encoding="utf-8-sig")
    worst = 0.0
    n = 0
    for (pair, scope, spec), f in frames.items():
        r = rc[(rc.pair == pair) & (rc.scope == scope) & (rc.spec == spec)].set_index("iso3")
        if set(r.index) != set(f.index):
            raise SystemExit(f"DUR (kapı): {pair} {scope}/{spec} ortak küme residual_change.csv ile aynı değil")
        for m in ("d_sd", "d_pts"):
            diff = (f[m] - r.loc[f.index, m]).abs().max()
            worst = max(worst, float(diff))
            n += len(f)
    if worst > 1e-4:
        raise SystemExit(f"DUR (kapı): betik 34 ile en büyük fark {worst:.6f} > 0,0001")
    return {"max_abs_diff_vs_residual_change": round(worst, 6), "cells_checked": n}


def point_estimates():
    data = m34.load()
    frames = {(f"{y0}->{y1}", sc, sp): pair_frame(data, y0, y1, sc, sp) for (y0, y1) in PAIRS for sc, sp in SPECS}
    gate = gate_vs_residual_change(frames)
    rc = pd.read_csv(RC, encoding="utf-8-sig")
    rows, cells = [], []
    for (pair, scope, spec), f in frames.items():
        X = design(f.dC.to_numpy(float), f.C0.to_numpy(float))
        iso = list(f.index)
        it = iso.index("TUR")
        n = len(f)
        dC_rank_desc = int((f.dC > f.dC.loc["TUR"]).sum() + 1)
        for meas, (_, rc_rank_col) in MEASURES.items():
            y = f[meas].to_numpy(float)
            beta, se, r, h = ols_hc3(X, y)
            e = press(X, y)
            # açık yeniden uydurma kontrolü (Türkiye)
            keep = np.arange(n) != it
            b_out = np.linalg.lstsq(X[keep], y[keep], rcond=None)[0]
            e_tur_refit = float(y[it] - X[it] @ b_out)
            if abs(e_tur_refit - e[it]) > 1e-8:
                raise SystemExit(f"DUR: PRESS ile yeniden uydurma uyuşmuyor ({pair} {scope}/{spec} {meas})")
            rk = rank_low(e, it)
            rrow = rc[(rc.pair == pair) & (rc.scope == scope) & (rc.spec == spec) & (rc.iso3 == "TUR")].iloc[0]
            for j, c in enumerate(iso):
                rows.append({"pair": pair, "scope": scope, "spec": spec, "measure": meas, "iso3": c, "n": n,
                             "d": round(float(y[j]), 4), "dC": round(float(f.dC.iloc[j]), 4), "C0": round(float(f.C0.iloc[j]), 4),
                             "loo_pred": round(float(y[j] - e[j]), 4), "loo_err": round(float(e[j]), 4),
                             "rank_cond": rank_low(e, j), "p_cond": round(rank_low(e, j) / n, 4), "leverage": round(float(h[j]), 4)})
            cells.append({"pair": pair, "scope": scope, "spec": spec, "measure": meas, "n": n,
                          "alpha": round(float(beta[0]), 4), "b_dC": round(float(beta[1]), 4), "b_dC_se_hc3": round(float(se[1]), 4),
                          "b_C0": round(float(beta[2]), 4), "b_C0_se_hc3": round(float(se[2]), 4),
                          "tur_d": round(float(y[it]), 4), "tur_loo_pred": round(float(y[it] - e[it]), 4),
                          "tur_loo_err": round(float(e[it]), 4), "tur_rank_cond": rk, "tur_p_cond": round(rk / n, 4),
                          "tur_rank_uncond": int(rrow[rc_rank_col]), "tur_p_uncond": round(int(rrow[rc_rank_col]) / n, 4),
                          "tur_dC": round(float(f.dC.loc["TUR"]), 4), "tur_dC_rank_desc": dC_rank_desc,
                          "tur_leverage": round(float(h[it]), 4), "mean_leverage": round(X.shape[1] / n, 4)})
    return pd.DataFrame(rows), pd.DataFrame(cells), gate, frames


def decide(cells: pd.DataFrame) -> dict:
    c = cells[(cells.pair == PRIMARY["pair"]) & (cells.measure == PRIMARY["measure"]) & (cells.spec == PRIMARY["spec"])]
    p_all = float(c[c.scope == "all"].tur_p_cond.iloc[0])
    p_oecd = float(c[c.scope == "oecd"].tur_p_cond.iloc[0])
    if p_all <= ALPHA and p_oecd <= ALPHA:
        verdict = "çekirdek kazancının öngördüğünden fazla genişleme"
    elif p_oecd <= ALPHA:
        verdict = "yalnız OECD kıyasında uçta; tüm katılımcılarda çekirdek yükselişiyle uyumlu"
    elif p_all <= ALPHA:
        verdict = "yalnız tüm katılımcılarda uçta (görev metninin kuralında olmayan durum; kurala eklenmedi)"
    else:
        verdict = "genişleme çekirdek yükselişiyle açıklanıyor; Türkiye'ye özgü değil"
    return {"primary_cell": PRIMARY, "p_cond_all": p_all, "p_cond_oecd": p_oecd, "alpha": ALPHA, "verdict": verdict}


# ----------------------------------------------------------------------------- bootstrap (mikroveri)
def _sav_from_zip(zp: Path, member_suffix: str, usecols: list[str], td: str) -> pd.DataFrame:
    import pyreadstat
    with zipfile.ZipFile(zp) as z:
        name = [n for n in z.namelist() if n.lower().endswith(member_suffix.lower())][0]
        try:
            z.extract(name, td)
        except NotImplementedError:  # Deflate64 (betik 12b/35 ile aynı durum) → Info-ZIP unzip
            r = subprocess.run(["unzip", "-o", "-q", str(zp), name, "-d", td], capture_output=True, text=True)
            if r.returncode != 0:
                raise SystemExit(f"DUR: unzip başarısız: {r.stderr[:300]}")
    sav = str(Path(td) / name)
    _, meta = pyreadstat.read_sav(sav, metadataonly=True)
    have = {c.upper(): c for c in meta.column_names}
    miss = [c for c in usecols if c.upper() not in have]
    if miss:
        raise SystemExit(f"DUR: {zp.name} içinde yok: {miss[:8]}")
    df, _ = pyreadstat.read_sav(sav, usecols=[have[c.upper()] for c in usecols])
    df.columns = [c.upper() for c in df.columns]
    os.remove(sav)
    return df


def _country_stats(df: pd.DataFrame, dom_pvs: list[str], core_roots: list[str], repw: list[str], M: int) -> pd.DataFrame:
    import _pisa_puf as P
    for c in df.columns:
        if c != "CNT":
            df[c] = pd.to_numeric(df[c], errors="coerce")
    est = {"dom": P.brr_pv_stat(df, dom_pvs, "W_FSTUWT", repw).set_index("iso3")}
    for r in core_roots:
        est[r] = P.brr_pv_stat(df, [f"PV{i}{r}" for i in range(1, M + 1)], "W_FSTUWT", repw).set_index("iso3")
    core_pv = [[f"PV{i}{r}" for r in core_roots] for i in range(1, M + 1)]
    rho = P.brr_pv_corr(df, dom_pvs, core_pv, "W_FSTUWT", repw).set_index("iso3")
    out = pd.DataFrame({"dom_mean": est["dom"]["mean"], "dom_se": est["dom"]["se"],
                        "dom_se_s": est["dom"]["se_sampling"], "dom_se_i": est["dom"]["se_imputation"],
                        "rho_s": rho["rho_sampling"], "rho_i": rho["rho_imputation"]})
    for r in core_roots:
        out[f"{r}_mean"] = est[r]["mean"]
        out[f"{r}_se"], out[f"{r}_se_s"], out[f"{r}_se_i"] = est[r]["se"], est[r]["se_sampling"], est[r]["se_imputation"]
    out["core_mean"] = out[[f"{r}_mean" for r in core_roots]].mean(axis=1)
    for s in ("se", "se_s", "se_i"):  # betik 31'in üst sınır kuralı
        out[f"core_{s}"] = out[[f"{r}_{s}" for r in core_roots]].mean(axis=1)
    out["rho"] = P.combine_rho(out.rho_s.to_numpy(float), out.rho_i.to_numpy(float), out.dom_se_s.to_numpy(float),
                               out.dom_se_i.to_numpy(float), out.core_se_s.to_numpy(float), out.core_se_i.to_numpy(float))
    return out.reset_index()


def boot_inputs(year: int) -> pd.DataFrame:
    cache = CACHE / f"e1_boot_inputs_{year}.csv"
    if cache.exists():
        print(f"önbellek: {cache.relative_to(ROOT)}")
        return pd.read_csv(cache)
    M, core = 10, ["MATH", "READ", "SCIE"]
    repw = [f"W_FSTURWT{i}" for i in range(1, 81)]
    core_cols = [f"PV{i}{r}" for i in range(1, M + 1) for r in core]
    with tempfile.TemporaryDirectory(prefix=f"e1_{year}_", dir=os.environ.get("PISA_TMP")) as td:
        if year == 2015:
            ids = ["CNT", "CNTSCHID", "CNTSTUID"]
            q = _sav_from_zip(D.parent / "pisa_microdata/2015/PUF_SPSS_COMBINED_CMB_STU_QQQ.zip", "_QQQ.sav",
                              ids + ["W_FSTUWT"] + repw + core_cols, td)
            c = _sav_from_zip(D.parent / "pisa_microdata/2015/PUF_SPSS_COMBINED_CMB_STU_CPS.zip", "_CPS.sav",
                              ids + [f"PV{i}CLPS" for i in range(1, 11)], td)
            df = c.merge(q, on=ids, how="left", validate="one_to_one")
            m15 = importlib.import_module("15_cps2015_placebo")  # CNT → panel iso3 eşlemesi (TAP→TWN, QCH→CHN) betik 15'ten
            df["CNT"] = df["CNT"].astype(str).map(lambda c: m15.MICRO_ISO.get(c, c))
            dom = [f"PV{i}CLPS" for i in range(1, 11)]
        else:
            df = _sav_from_zip(D.parent / "pisa/2025/database/CY09_MS_STU_PUF.zip", ".sav",
                               ["CNT", "W_FSTUWT"] + repw + core_cols + [f"PV{i}CMPS" for i in range(1, 11)], td)
            df["CNT"] = df["CNT"].astype(str).replace({"TAP": "TWN", "KSV": "XKX"})
            dom = [f"PV{i}CMPS" for i in range(1, 11)]
    df["CNT"] = df["CNT"].astype(str)
    st = _country_stats(df, dom, core, repw, M)
    CACHE.mkdir(parents=True, exist_ok=True)
    st.to_csv(cache, index=False, encoding="utf-8")
    return st


def boot_gates(st15: pd.DataFrame, st25: pd.DataFrame) -> dict:
    panel = pd.read_csv(D / "analysis_panel.csv")
    out = {}
    volv = pd.read_csv(D / "placebo_backbone" / "cps2015_crosscheck_oecd_volv.csv", encoding="utf-8-sig").dropna(subset=["volv_published"])
    j = volv.merge(st15, on="iso3", how="left")
    # SONRADAN DÜZELTME (2026-09-26, yerel koşu 1): Vol. V'te yayımlanmış ama 2015 CPS mikroverisinde olmayan sistem (CYP)
    # karşılaştırılamaz; kapı ön kayıttaki gibi mikroverisi olan satırlarda sayılır (beklenen 50/50), dışarıda kalan listelenir.
    out["2015_published_without_microdata"] = sorted(j.loc[j.dom_mean.isna(), "iso3"])
    j = j[j.dom_mean.notna()]
    ok = (j.dom_mean.round(0) == j.volv_published).sum()
    out["2015_clps_rounding_match"] = f"{int(ok)}/{len(j)}"
    ours = pd.read_csv(D / "cps2015_country_means.csv", encoding="utf-8-sig").merge(st15, on="iso3", how="inner")
    out["2015_clps_vs_cps2015_country_means_max"] = round(float((ours.cps2015_mean_weighted - ours.dom_mean).abs().max()), 5)
    p15 = panel[panel.cycle == 2015].merge(st15, on="iso3", how="inner")
    out["2015_core_vs_panel_max"] = round(float(max((p15.math_mean - p15.MATH_mean).abs().max(), (p15.reading_mean - p15.READ_mean).abs().max(),
                                                    (p15.science_mean - p15.SCIE_mean).abs().max())), 5)
    p25 = panel[panel.cycle == 2025].merge(st25, on="iso3", how="inner")
    out["2025_cmps_vs_panel_max"] = round(float((p25.cps2025_mean - p25.dom_mean).abs().max()), 5)
    out["2025_core_vs_panel_max"] = round(float(max((p25.math_mean - p25.MATH_mean).abs().max(), (p25.reading_mean - p25.READ_mean).abs().max(),
                                                    (p25.science_mean - p25.SCIE_mean).abs().max())), 5)
    q25 = p25.set_index("iso3")
    cm_mx, cm_exc, cm_ok = gate_2025((q25.cps2025_mean - q25.dom_mean).abs(), 0.003)
    co_mx, co_exc, co_ok = gate_2025(pd.concat([(q25.math_mean - q25.MATH_mean).abs(), (q25.reading_mean - q25.READ_mean).abs(),
                                                (q25.science_mean - q25.SCIE_mean).abs()], axis=1).max(axis=1), 0.003)
    out["2025_cmps_excl_exceptions_max"], out["2025_core_excl_exceptions_max"] = round(cm_mx, 5), round(co_mx, 5)
    out["2025_gate_exceptions"] = {"cmps": cm_exc, "core": co_exc, "ceiling": GATE_EXCEPTIONS_2025}
    fails = []
    if ok != len(j):
        fails.append("2015 CLPS yuvarlama")
    if out["2015_clps_vs_cps2015_country_means_max"] > 0.001:
        fails.append("2015 CLPS vs cps2015_country_means")
    if out["2015_core_vs_panel_max"] > 0.01:
        fails.append("2015 çekirdek")
    if not cm_ok:  # SONRADAN: BEL istisnası gate_2025 içinde
        fails.append("2025 CMPS")
    if not co_ok:
        fails.append("2025 çekirdek")
    out["failed"] = fails
    return out


def run_bootstrap(frames: dict) -> tuple[pd.DataFrame, dict]:
    st = {2015: boot_inputs(2015), 2025: boot_inputs(2025)}
    gates = boot_gates(st[2015], st[2025])
    print("bootstrap kapıları:", gates)
    if gates["failed"]:
        raise SystemExit(f"DUR: bootstrap kapısı geçmedi: {gates['failed']}")
    data = m34.load()
    rng = np.random.default_rng(SEED)
    rows, summ = [], {"gates": gates, "draws": BOOT, "seed": SEED}
    for scope, spec in SPECS:
        deg = 2 if spec == "quadratic" else 1
        cyc = {}
        for yr in (2015, 2025):
            s = data[yr][(data[yr].scope == scope) & (data[yr].spec == spec)].set_index("iso3")
            m = s[["core", "dom"]].join(st[yr].set_index("iso3")[["dom_se", "core_se", "rho"]], how="left")
            fixed = sorted(m.index[m.dom_se.isna()])
            m[["dom_se", "core_se", "rho"]] = m[["dom_se", "core_se", "rho"]].fillna(0.0)
            cyc[yr] = (m, fixed)
        f = frames[("2015->2025", scope, spec)]
        common = list(f.index)
        it = common.index("TUR")
        rec = {k: np.empty(BOOT) for k in ("r15", "r25", "d_sd", "d_pts", "cond_sd", "cond_pts", "p_cond_sd", "p_cond_pts")}
        for b in range(BOOT):
            res, cores = {}, {}
            for yr in (2015, 2025):
                m, _ = cyc[yr]
                z1, z2 = rng.standard_normal(len(m)), rng.standard_normal(len(m))
                y = m.dom.to_numpy(float) + m.dom_se.to_numpy(float) * z1
                rr = m.rho.to_numpy(float)
                x = m.core.to_numpy(float) + m.core_se.to_numpy(float) * (rr * z1 + np.sqrt(np.maximum(1 - rr ** 2, 0)) * z2)
                V = np.vander(x, deg + 1, increasing=True)
                beta = np.linalg.lstsq(V, y, rcond=None)[0]
                r = y - V @ beta
                rmse = float(np.sqrt((r @ r) / (len(r) - V.shape[1])))
                res[yr] = pd.DataFrame({"r": r, "rsd": r / rmse}, index=m.index).loc[common]
                cores[yr] = pd.Series(x, index=m.index).loc[common]
            d_sd = (res[2025].rsd - res[2015].rsd).to_numpy()
            d_pts = (res[2025].r - res[2015].r).to_numpy()
            X = design((cores[2025] - cores[2015]).to_numpy(), cores[2015].to_numpy())
            e_sd, e_pts = press(X, d_sd), press(X, d_pts)
            rec["r15"][b], rec["r25"][b] = res[2015].r.iloc[it], res[2025].r.iloc[it]
            rec["d_sd"][b], rec["d_pts"][b] = d_sd[it], d_pts[it]
            rec["cond_sd"][b], rec["cond_pts"][b] = e_sd[it], e_pts[it]
            rec["p_cond_sd"][b] = rank_low(e_sd, it) / len(common)
            rec["p_cond_pts"][b] = rank_low(e_pts, it) / len(common)
        key = f"{scope}/{spec}"
        summ[key] = {"n_common": len(common), "fixed_no_microdata_se": {str(y): cyc[y][1] for y in cyc}}
        for k, v in rec.items():
            lo, hi = np.percentile(v, [2.5, 97.5])
            row = {"scope": scope, "spec": spec, "quantity": k, "median": round(float(np.median(v)), 4),
                   "lo95": round(float(lo), 4), "hi95": round(float(hi), 4)}
            if k.startswith("p_cond"):
                row["share_p_le_010"] = round(float((v <= ALPHA).mean()), 4)
            rows.append(row)
    return pd.DataFrame(rows), summ


# ----------------------------------------------------------------------------- ana akış
def _write(df: pd.DataFrame, name: str):
    OUT.mkdir(parents=True, exist_ok=True)
    tmp = OUT / f"{name}.tmp"
    df.to_csv(tmp, index=False, encoding="utf-8")
    os.replace(tmp, OUT / name)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--bootstrap", action="store_true", help="mikroveriden korelasyonlu parametrik bootstrap (Windows)")
    a = ap.parse_args()
    long, cells, gate, frames = point_estimates()
    _write(long, "e1_conditional_change.csv")
    summary = {"note": "E1 — koşullu artık değişimi; sıra alttan (1 = en olumsuz), p = sıra/N; koşullu değer = birini dışarıda "
                       "bırakma tahmin hatası (PRESS). Ön-belirleme RESULTS_EMPIRICAL_FIXES.md §0.2 (commit 476fe4e).",
               "gate_betik34": gate, "cells": cells.to_dict("records"), "decision": decide(cells),
               "bootstrap": "koşulmadı (mikroveri gerekli; --bootstrap ile Windows'ta)"}
    if a.bootstrap:
        boot, bsum = run_bootstrap(frames)
        _write(boot, "e1_bootstrap.csv")
        summary["bootstrap"] = bsum
    tmp = OUT / "e1_summary.json.tmp"
    tmp.write_text(json.dumps(summary, ensure_ascii=False, indent=1), encoding="utf-8")
    os.replace(tmp, OUT / "e1_summary.json")
    print("kapı:", gate)
    print(f"{'çift':<11}{'spes':<16}{'ölçü':<6}{'N':>4} {'TUR d':>8} {'LOO ŷ':>8} {'e':>8} {'koşullu':>9} {'koşulsuz':>9} "
          f"{'b_dC (HC3)':>16} {'ΔC sıra':>8} {'h':>6}")
    for r in cells.itertuples():
        print(f"{r.pair:<11}{r.scope + '/' + r.spec:<16}{r.measure:<6}{r.n:>4} {r.tur_d:>8.2f} {r.tur_loo_pred:>8.2f} {r.tur_loo_err:>8.2f} "
              f"{str(r.tur_rank_cond) + '/' + str(r.n) + ' ' + format(r.tur_p_cond, '.3f'):>9} "
              f"{str(r.tur_rank_uncond) + '/' + str(r.n):>9} {format(r.b_dC, '.4f') + ' (' + format(r.b_dC_se_hc3, '.4f') + ')':>16} "
              f"{r.tur_dC_rank_desc:>8} {r.tur_leverage:>6.3f}")
    print("karar:", summary["decision"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
