# -*- coding: utf-8 -*-
"""
44_e5_coverage_matched_2003.py — editoryal düzeltme E5 (F2): 2003 yanlışlaması kapsam farkından mı geliyor?

Soru (COWORK_AMPIRIK_DUZELTMELER.md E5): 2003 yanlışlaması (−16,4; 1/36 [111]) kohortun %35,6'sını temsil eden bir örneklemde
yapıldı; 2025 örneklemi kohortun %72,2'sini temsil ediyor. Test edilmeyenler test edilenlerin altındaysa kohortun üst %35,6'sı
2025'te test edilen ağırlıklı dağılımın üst ≈ %49'una karşılık gelir. 2025'in bu eşleşik diliminde Türkiye'nin öğrenci düzeyi
artığı, 2025 tüm örneklem artığından farklı mı?

ÖNCEDEN BELİRLENEN SEÇİMLER (RESULTS_EMPIRICAL_FIXES.md §0.3; commit 476fe4e, koşudan önce):
  * Öğrenci modeli (OECD 2014a tipi): yeni alan PV_p ~ tam ikinci derece çekirdek (MATH_p, READ_p, SCIE_p; 3 doğrusal + 3 kare +
    3 etkileşim + sabit); PV başına (2003 M = 5 PROB; 2025 M = 10 CMPS); havuz = ülke düzeyi analizin sistem kümesi (2003: 36,
    2025: 84; OECD ikincil); senato ağırlığı (ülke içinde W_FSTUWT × 1000/ΣW_c). Öğrenci artığı = gözlenen − öngörülen.
  * Türkiye içinde dilimleme ESCS'nin döngü içi ağırlıklı yüzdelik sırasıyla (orta sıra, eşitlik bloklarında); üst q% dilimleri
    q ∈ {30, 40, 49, 60, 70, 80, 90, 100} + ondalıklar; ortalamalar W_FSTUWT ile; SE BRR (Fay 0,5; 80) + Rubin; dilim sınırları
    her replikasyonda o replikasyonun ağırlığıyla yeniden; model katsayıları replikasyonlarda sabit.
  * Gradyan: artığın ESCS yüzdelik sırasına ağırlıklı OLS eğimi (BRR + Rubin).
  * Duyarlılık: öğrenci dışarıda okul ortalaması (aynı okuldaki diğerlerinin p'inci çekirdek PV ortalaması) ile dilimleme.
  * Karar: 2025 eşleşik (q = 49) dilim artığı 2025 tüm örneklem artığının %95 aralığında VE gradyanın %95 aralığı 0'ı içeriyorsa
    → "2003 yanlışlaması kapsamdan kaynaklanan bir yapıt değildir"; aksi hâlde yön ve büyüklük.
  * Kapılar: 2003 MATH/READ/SCIE ülke ortalaması ve SE'si panelle (mutlak fark ≤ 0,001); 2025 CMPS ve çekirdek ağırlıklı
    ortalamaları panelle (≤ 0,003); q* = 0,49 ile 0,36 / CI3_2025 oranı arasındaki fark ≤ 0,01.
  * Alt örneklem yalnız --subsample ile (ülke başına 6000, tohum 20260926); kullanıldıysa özet JSON'da yazılır.
SONRADAN EKLENENLER:
  2026-09-26 (yerel koşu 2, yazar onayı) — 2025 kapısına belgelenmiş BEL istisnası: yalnız BEL 2025 için tavan 0,02
  (dört alan). BEL'in mikroveri − yayımlanmış farkı mat −0,0031, oku +0,0116, fen +0,0032, CPS +0,0027; betik 51 teşhisi
  "neden bulunamadı" (PUF'ta çekirdek PV'si eksik 1 öğrenci, ağırlık payı %0,02). Diğer bütün sistemlerde eşik değişmedi;
  istisna kapı çıktısına `exceptions` olarak yazılır. Betik 45 (E2) ve 50 (E9) bu kapıyı kullanır.
  2026-09-26 (bulut, PR incelemesi; koşulmadı, tanım değişmedi) — (1) panelde karşılığı olmayan kapı (2003 SCIE, n = 0) artık
  "geçti" görünmez: `status: "sınanmadı"` ve `untested` listesine yazılır; dış doğrulama betik 54 (§0.13). (2) Özet JSON'da
  NaN/sonsuz değerler `null` yazılır (katı JSON); önceki koşunun `e5_summary.json`'ı değerleri değişmeden yeniden kaydedildi.
Girdi: 2003 PUF (`_pisa_puf.read_columns`); data/pisa/2025/database/CY09_MS_STU_PUF.zip; data/derived/mechanisms/
       placebo_conditional_{2003ps_puf,2025}.csv (sistem kümeleri); data/derived/analysis_panel.csv (kapılar, CI3_2025);
       data/derived/ontrend/ci3_2003_techreport.json (CI3_2003).
Çıktı: data/derived/empirical_fixes/e5_coverage_matched.csv, e5_summary.json, e5_model_coefs.csv
       (+ önbellek data/derived/cache/e5_2025_students.parquet).
Kullanım (Windows; pyreadstat + pyarrow): python analysis/44_e5_coverage_matched_2003.py [--subsample] [--oecd]
Yazan: Claude Code (bulut oturumu), 2026-09-26. Bu oturumda mikroveri yoktu: betik yalnız sentetik veriyle duman testinden geçti.
"""
from __future__ import annotations

import argparse
import importlib
import json
import os
import sys
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE))
D = ROOT / "data" / "derived"
OUT = D / "empirical_fixes"
CACHE = D / "cache"
Q_MATCHED = 0.49
QS = [0.30, 0.40, Q_MATCHED, 0.60, 0.70, 0.80, 0.90, 1.00]
FAY_MULT = 1.0 / (80 * (1 - 0.5) ** 2)
SEED = 20260926
CFG = {
    2003: dict(M=5, new="PROB", repw=[f"W_FSTR{i}" for i in range(1, 81)], school="SCHOOLID",
               sysfile="placebo_conditional_2003ps_puf.csv", sysfilter={"core_def": "mat/oku/fen"}),
    2025: dict(M=10, new="CMPS", repw=[f"W_FSTURWT{i}" for i in range(1, 81)], school="CNTSCHID",
               sysfile="placebo_conditional_2025.csv", sysfilter={}),
}
CORE = ["MATH", "READ", "SCIE"]


# ----------------------------------------------------------------------------- veri
def systems(cycle: int, scope: str) -> list[str]:
    c = CFG[cycle]
    d = pd.read_csv(D / "mechanisms" / c["sysfile"], encoding="utf-8-sig")
    for k, v in c["sysfilter"].items():
        d = d[d[k] == v]
    return sorted(d[(d.scope == scope) & (d.spec == "linear")].iso3.unique())


def pv(cycle: int, root: str) -> list[str]:
    return [f"PV{i}{root}" for i in range(1, CFG[cycle]["M"] + 1)]


def load(cycle: int) -> pd.DataFrame:
    c = CFG[cycle]
    cols = ["CNT", c["school"], "W_FSTUWT", "ESCS"] + c["repw"] + [x for r in CORE + [c["new"]] for x in pv(cycle, r)]
    if cycle == 2003:
        import _pisa_puf as P
        df = P.read_columns(2003, cols)
    else:
        cache = CACHE / "e5_2025_students.parquet"
        if cache.exists():
            df = pd.read_parquet(cache)
        else:
            m43 = importlib.import_module("43_e1_conditional_change")
            with tempfile.TemporaryDirectory(prefix="e5_", dir=os.environ.get("PISA_TMP")) as td:
                df = m43._sav_from_zip(ROOT / "data/pisa/2025/database/CY09_MS_STU_PUF.zip", ".sav", cols + ["SENWT"], td)
            CACHE.mkdir(parents=True, exist_ok=True)
            df.to_parquet(cache, index=False)
        df["CNT"] = df["CNT"].astype(str).replace({"TAP": "TWN", "KSV": "XKX"})
    df["CNT"] = df["CNT"].astype(str).str.strip()
    for col in df.columns:
        if col != "CNT":
            df[col] = pd.to_numeric(df[col], errors="coerce")
    return df


def gates(cycle: int, df: pd.DataFrame) -> dict:
    panel = pd.read_csv(D / "analysis_panel.csv")
    p = panel[panel.cycle == cycle].set_index("iso3")
    out, fails, untested = {}, [], []
    fld = {"MATH": ("math_mean", "math_se"), "READ": ("reading_mean", "reading_se"), "SCIE": ("science_mean", "science_se")}
    if cycle == 2003:
        import _pisa_puf as P
        for r in CORE:
            e = P.brr_pv_stat(df, pv(2003, r), "W_FSTUWT", CFG[2003]["repw"]).set_index("iso3")
            j = e.join(p[list(fld[r])], how="inner").dropna()
            if len(j) == 0:  # SONRADAN: karşılaştırılacak panel değeri yok → sınanmadı (boş kapı "geçti" sayılmaz)
                out[f"2003_{r}"] = {"n": 0, "status": "sınanmadı (panelde değer yok; dış doğrulama betik 54)"}
                untested.append(f"2003 {r}")
                continue
            dm, ds = float((j["mean"] - j[fld[r][0]]).abs().max()), float((j["se"] - j[fld[r][1]]).abs().max())
            out[f"2003_{r}"] = {"n": int(len(j)), "max_mean_diff": round(dm, 5), "max_se_diff": round(ds, 5)}
            if dm > 0.001 or ds > 0.001:
                fails.append(f"2003 {r}")
    else:
        for r, col in list(zip(CORE, ["math_mean", "reading_mean", "science_mean"])) + [("CMPS", "cps2025_mean")]:
            means = {}
            for cn, g in df.groupby("CNT"):
                w = g.W_FSTUWT.to_numpy(float)
                vals = [np.nansum(w * g[x].to_numpy(float)) / np.nansum(w * np.isfinite(g[x].to_numpy(float))) for x in pv(2025, r)]
                means[cn] = float(np.mean(vals))
            j = pd.Series(means).to_frame("m").join(p[[col]], how="inner").dropna()
            dm = float((j.m - j[col]).abs().max())
            m43 = importlib.import_module("43_e1_conditional_change")  # SONRADAN: BEL istisnası (başlık notu)
            mx, exc, ok = m43.gate_2025((j.m - j[col]).abs(), 0.003)
            out[f"2025_{r}"] = {"n": int(len(j)), "max_mean_diff": round(dm, 5), "max_mean_diff_excl_exceptions": round(mx, 5),
                                 "exceptions": exc}
            if not ok:
                fails.append(f"2025 {r}")
    out["failed"] = fails
    out["untested"] = untested
    return out


def m43_ceiling(iso3: str):
    """SONRADAN: 2025 kapı istisnası tavanı (yoksa None); betik 50'nin panel kapısı kullanır."""
    return importlib.import_module("43_e1_conditional_change").GATE_EXCEPTIONS_2025.get(iso3)


def q_gate() -> dict:
    ci3_03 = float(json.loads((D / "ontrend" / "ci3_2003_techreport.json").read_text(encoding="utf-8"))["TUR"])
    panel = pd.read_csv(D / "analysis_panel.csv")
    ci3_25 = float(panel[(panel.cycle == 2025) & (panel.iso3 == "TUR")].coverage_index3.iloc[0])
    ratio = ci3_03 / ci3_25
    return {"q_matched": Q_MATCHED, "ci3_2003_printed": ci3_03, "ci3_2025": ci3_25, "ratio_from_files": round(ratio, 4),
            "abs_diff": round(abs(ratio - Q_MATCHED), 4), "ok": bool(abs(ratio - Q_MATCHED) <= 0.01)}


# ----------------------------------------------------------------------------- model
def design(m: np.ndarray, r: np.ndarray, s: np.ndarray) -> np.ndarray:
    a, b, c = (m - 500) / 100, (r - 500) / 100, (s - 500) / 100  # ölçekleme yalnız sayısal koşulluluk için
    return np.column_stack([np.ones_like(a), a, b, c, a * a, b * b, c * c, a * b, a * c, b * c])


def senate(df: pd.DataFrame) -> np.ndarray:
    tot = df.groupby("CNT").W_FSTUWT.transform("sum").to_numpy(float)
    return df.W_FSTUWT.to_numpy(float) * 1000.0 / tot


def fit_model(cycle: int, df: pd.DataFrame, sysset: list[str]):
    """Havuzlanmış senato ağırlıklı WLS, PV başına. Döner: katsayılar (M × 10), artık SS birimi, R² listesi."""
    c = CFG[cycle]
    d = df[df.CNT.isin(sysset)]
    coefs, sds, r2s = [], [], []
    for p in range(c["M"]):
        m, r, s = (d[pv(cycle, x)[p]].to_numpy(float) for x in CORE)
        y = d[pv(cycle, c["new"])[p]].to_numpy(float)
        ok = np.isfinite(m) & np.isfinite(r) & np.isfinite(s) & np.isfinite(y) & np.isfinite(d.W_FSTUWT.to_numpy(float))
        w = senate(d[ok])  # senato ağırlığı geçerli öğrenciler üzerinden: her ülke tam 1000
        X, yy = design(m[ok], r[ok], s[ok]), y[ok]
        Xw = X * w[:, None]
        beta = np.linalg.solve(X.T @ Xw, Xw.T @ yy)
        e = yy - X @ beta
        sds.append(float(np.sqrt(np.average(e ** 2, weights=w) - np.average(e, weights=w) ** 2)))
        r2s.append(float(1 - np.average(e ** 2, weights=w) / np.average((yy - np.average(yy, weights=w)) ** 2, weights=w)))
        coefs.append(beta)
    return np.array(coefs), float(np.mean(sds)), r2s


def residuals(cycle: int, t: pd.DataFrame, coefs: np.ndarray) -> np.ndarray:
    """Türkiye öğrencileri için n × M artık matrisi."""
    c = CFG[cycle]
    out = np.full((len(t), c["M"]), np.nan)
    for p in range(c["M"]):
        m, r, s = (t[pv(cycle, x)[p]].to_numpy(float) for x in CORE)
        out[:, p] = t[pv(cycle, c["new"])[p]].to_numpy(float) - design(m, r, s) @ coefs[p]
    return out


# ----------------------------------------------------------------------------- BRR + Rubin
def wrank(x: np.ndarray, w: np.ndarray) -> np.ndarray:
    """Ağırlıklı orta sıra (0–1); eşitlik bloğu tek sıra alır."""
    order = np.argsort(x, kind="mergesort")
    xs, ws = x[order], w[order]
    uniq, start = np.unique(xs, return_index=True)
    blockw = np.add.reduceat(ws, start)
    below = np.concatenate([[0.0], np.cumsum(blockw)[:-1]])
    mid = (below + blockw / 2) / ws.sum()
    rk_sorted = np.repeat(mid, np.diff(np.append(start, len(xs))))
    out = np.empty_like(rk_sorted)
    out[order] = rk_sorted
    return out


def rubin(theta: np.ndarray, theta_rep: np.ndarray) -> tuple[float, float]:
    """theta: (M,), theta_rep: (G, M). Döner: nokta, SE."""
    M = len(theta)
    v_s = float((FAY_MULT * ((theta_rep - theta[None, :]) ** 2).sum(axis=0)).mean())
    v_i = (1 + 1 / M) * float(theta.var(ddof=1))
    return float(theta.mean()), float(np.sqrt(v_s + v_i))


def slice_stats(e: np.ndarray, key: np.ndarray, W: np.ndarray, spec: tuple) -> tuple[float, float, int]:
    """e: n × M artık; key: sıralama değişkeni (NaN = dışarıda); W: n × (1 + G) ağırlık (0: tam, 1..G: replikasyon).
    spec = ("top", q) | ("decile", d) | ("all", None) | ("gradient", None)."""
    ok = np.isfinite(key)
    kind, par = spec
    G1, M = W.shape[1], e.shape[1]
    th = np.empty((G1, M))
    n = 0
    for g in range(G1):
        w = W[:, g]
        if kind == "all":
            sel = np.ones(len(w), bool)
        else:
            rk = np.full(len(w), np.nan)
            rk[ok] = wrank(key[ok], w[ok])
            if kind == "top":
                sel = ok & (rk > 1 - par)
            elif kind == "decile":
                sel = ok & (rk > (par - 1) / 10) & (rk <= par / 10)
            else:
                sel = ok
        if g == 0:
            n = int(sel.sum())
        for p in range(M):
            ee = e[:, p]
            s2 = sel & np.isfinite(ee)
            if kind == "gradient":
                x, y, ww = rk[s2], ee[s2], w[s2]
                xm = np.average(x, weights=ww)
                th[g, p] = float(np.sum(ww * (x - xm) * (y - np.average(y, weights=ww))) / np.sum(ww * (x - xm) ** 2))
            else:
                th[g, p] = float(np.sum(w[s2] * ee[s2]) / np.sum(w[s2]))
    est, se = rubin(th[0], th[1:])
    return est, se, n


def loo_school_mean(cycle: int, t: pd.DataFrame) -> np.ndarray:
    """Öğrenci dışarıda okul ortalaması (çekirdek), PV başına ortalama alınarak tek anahtar (duyarlılık)."""
    c = CFG[cycle]
    w = t.W_FSTUWT.to_numpy(float)
    keys = []
    for p in range(c["M"]):
        core = np.column_stack([t[pv(cycle, x)[p]].to_numpy(float) for x in CORE]).mean(axis=1)
        tmp = pd.DataFrame({"s": t[c["school"]].to_numpy(), "wc": w * core, "w": w})
        S = tmp.groupby("s").transform("sum")
        den = S.w.to_numpy() - w
        keys.append(np.where(den > 0, (S.wc.to_numpy() - w * core) / np.where(den > 0, den, 1), np.nan))
    return np.nanmean(np.column_stack(keys), axis=1)


def tur_table(cycle: int, df: pd.DataFrame, coefs: np.ndarray, resid_sd: float, pool: str) -> list[dict]:
    c = CFG[cycle]
    t = df[df.CNT == "TUR"].reset_index(drop=True)
    e = residuals(cycle, t, coefs)
    W = np.column_stack([t.W_FSTUWT.to_numpy(float)] + [t[x].to_numpy(float) for x in c["repw"]])
    escs = t.ESCS.to_numpy(float)
    keys = {"escs": escs, "loo_school": loo_school_mean(cycle, t)}
    rows = []

    def add(slicing, label, spec, key):
        est, se, n = slice_stats(e, key, W, spec)
        rows.append({"cycle": cycle, "pool": pool, "slicing": slicing, "slice": label, "n_students": n,
                     "estimate": round(est, 4), "se": round(se, 4), "lo95": round(est - 1.96 * se, 4), "hi95": round(est + 1.96 * se, 4),
                     "resid_sd_unit": round(resid_sd, 4), "estimate_sd": round(est / resid_sd, 4),
                     "escs_missing_share_w": round(float(W[~np.isfinite(escs), 0].sum() / W[:, 0].sum()), 4)})

    add("tüm örneklem", "all", ("all", None), escs)
    for sl, key in keys.items():
        for q in QS:
            add(sl, f"top{int(round(q * 100))}", ("top", q), key)
        if sl == "escs":
            for dcl in range(1, 11):
                add(sl, f"decile{dcl}", ("decile", dcl), key)
        add(sl, "gradient", ("gradient", None), key)
    return rows


# ----------------------------------------------------------------------------- ana akış
def run_cycle(cycle: int, scopes: list[str], subsample: bool, gate_log: dict):
    df = load(cycle)
    g = gates(cycle, df)
    gate_log[str(cycle)] = g
    print(f"[{cycle}] kapı: {g}")
    if g["failed"]:
        raise SystemExit(f"DUR: {cycle} kapısı geçmedi: {g['failed']}")
    rows, coef_rows, info = [], [], {}
    for scope in scopes:
        sysset = systems(cycle, scope)
        present = sorted(set(sysset) & set(df.CNT))
        d = df[df.CNT.isin(present)]
        if subsample:
            rng = np.random.default_rng(SEED)
            d = d.groupby("CNT", group_keys=False).apply(
                lambda x: x.loc[rng.choice(x.index, size=min(len(x), 6000), replace=False)] if len(x) > 6000 else x)
        coefs, rsd, r2 = fit_model(cycle, d, present)
        info[scope] = {"n_systems_listed": len(sysset), "n_systems_in_puf": len(present),
                       "missing_in_puf": sorted(set(sysset) - set(df.CNT)), "resid_sd_unit": round(rsd, 4),
                       "r2_by_pv": [round(x, 4) for x in r2], "n_students_model": int(len(d))}
        for p, b in enumerate(coefs, start=1):
            coef_rows.append({"cycle": cycle, "pool": scope, "pv": p, **{f"b{j}": float(v) for j, v in enumerate(b)}})
        rows += tur_table(cycle, df, coefs, rsd, scope)
    return rows, coef_rows, info


def json_safe(o):
    """SONRADAN: NaN/sonsuz → None (katı JSON)."""
    if isinstance(o, (float, np.floating)):
        return float(o) if np.isfinite(o) else None
    if isinstance(o, dict):
        return {k: json_safe(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [json_safe(v) for v in o]
    return o


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--subsample", action="store_true", help="bellek yetmezse: ülke başına 6000 öğrenci (tohum 20260926)")
    ap.add_argument("--oecd", action="store_true", help="OECD havuzlu ikincil modeli de uydur")
    a = ap.parse_args()
    qg = q_gate()
    if not qg["ok"]:
        raise SystemExit(f"DUR: q* kapısı geçmedi: {qg}")
    scopes = ["all", "oecd"] if a.oecd else ["all"]
    gate_log, rows, coefs, info = {}, [], [], {}
    for cyc in (2003, 2025):
        r, c, i = run_cycle(cyc, scopes, a.subsample, gate_log)
        rows += r
        coefs += c
        info[str(cyc)] = i
    t = pd.DataFrame(rows)
    OUT.mkdir(parents=True, exist_ok=True)
    for name, frame in (("e5_coverage_matched.csv", t), ("e5_model_coefs.csv", pd.DataFrame(coefs))):
        tmp = OUT / f"{name}.tmp"
        frame.to_csv(tmp, index=False, encoding="utf-8")
        os.replace(tmp, OUT / name)
    summ = {"note": "E5 — kapsam eşleşik 2003/2025 karşılaştırması; ön-belirleme §0.3 (commit 476fe4e).",
            "q_gate": qg, "gates": gate_log, "models": info, "subsample_used": bool(a.subsample), "comparisons": {}}
    for scope in scopes:
        g = lambda cyc, sl, lab: t[(t.cycle == cyc) & (t.pool == scope) & (t.slicing == sl) & (t.slice == lab)].iloc[0]
        a03, all25 = g(2003, "tüm örneklem", "all"), g(2025, "tüm örneklem", "all")
        m25, grad = g(2025, "escs", f"top{int(round(Q_MATCHED * 100))}"), g(2025, "escs", "gradient")
        in_ci = bool(all25.lo95 <= m25.estimate <= all25.hi95)
        grad0 = bool(grad.lo95 <= 0 <= grad.hi95)
        verdict = ("2003 yanlışlaması kapsamdan kaynaklanan bir yapıt değildir" if in_ci and grad0 else
                   f"koşul sağlanmadı: eşleşik dilim − tüm örneklem = {m25.estimate - all25.estimate:+.2f} puan; "
                   f"gradyan {grad.estimate:+.2f} [{grad.lo95:+.2f}; {grad.hi95:+.2f}]")
        summ["comparisons"][scope] = {
            "tur_2003_all": {k: a03[k] for k in ("estimate", "se", "lo95", "hi95", "estimate_sd")},
            "tur_2025_all": {k: all25[k] for k in ("estimate", "se", "lo95", "hi95", "estimate_sd")},
            "tur_2025_matched_top49": {k: m25[k] for k in ("estimate", "se", "lo95", "hi95", "estimate_sd")},
            "tur_2025_gradient": {k: grad[k] for k in ("estimate", "se", "lo95", "hi95")},
            "matched_in_all_ci": in_ci, "gradient_ci_contains_0": grad0, "verdict": verdict}
    tmp = OUT / "e5_summary.json.tmp"
    tmp.write_text(json.dumps(json_safe(summ), ensure_ascii=False, indent=1, default=float, allow_nan=False), encoding="utf-8")
    os.replace(tmp, OUT / "e5_summary.json")
    print(json.dumps(summ["comparisons"], ensure_ascii=False, indent=1, default=float))
    return 0


if __name__ == "__main__":
    sys.exit(main())
