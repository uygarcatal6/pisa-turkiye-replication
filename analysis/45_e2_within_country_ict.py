# -*- coding: utf-8 -*-
"""
45_e2_within_country_ict.py — editoryal düzeltme E2 (F5): BİT/programlama açıklaması ülke İÇİNDE de taşınıyor mu?

Soru (COWORK_AMPIRIK_DUZELTMELER.md E2): Ülkeler arası BİT sonucu OECD-24'te Türkiye'nin kaldıracına (0,40) dayanıyor; Türkiye
dışarıda bırakılınca ICTSCH artığın %75–77'sini bırakıyor [123]. Ülke sabit etkili öğrenci düzeyi modelde BİT/programlama
eğimi (γ_içi) ne kadar ve Türkiye'nin BİT açığı, bu eğimle Türkiye'nin ülke artığının ne kadarını açıklar?

ÖNCEDEN BELİRLENEN SEÇİMLER (RESULTS_EMPIRICAL_FIXES.md §0.4; commit 476fe4e, koşudan önce):
  * Sistem kümesi: Option_ICTQ = 1 olan öğrencilerin ağırlıklı payı ≥ 0,5 (beklenen 44; OECD alt kümesi beklenen 24).
  * Model: CMPS_p = ülke sabit etkisi + tam ikinci derece f(MATH_p, READ_p, SCIE_p) + γ·X; ülke içi (within) dönüşüm, senato
    ağırlığı (her ülke 1000, tahmin örnekleminde); PV başına (M = 10) + Rubin.
  * X (ayrı modeller): PROG = ST436Q07DA ≥ 2 (birincil); ICTSCH öğrenci (geçerli < 95); ICTSCH okul ortalaması (CNTSCHID içinde
    W_FSTUWT ağırlıklı, öğrenci dahil); ROBOT = ST436Q13DA ≥ 2; ayrıca ICTSCH öğrenci + okul ortalaması birlikte.
  * SE: ülke-kümeli JK1 jackknife (G = sistem sayısı), PV başına, PV'ler üzerinden ortalama + Rubin atama varyansı.
  * γ_içi Türkiye dahil ve hariç; ülke başına γ_c (kendi regresyonu, W_FSTUWT, BRR Fay 0,5 + Rubin).
  * Açıklanan pay = γ̂_içi(Türkiye hariç; birincil) × (X̄_TUR − X̄_ref); X̄_ref = kümenin Türkiye dışı ülke ortalamalarının ağırlıksız
    ortalaması; kümeler OECD-24 ve 44; payda = betik 35'in `ict_covariate_2025.csv` ICTSCH/linear satırındaki `tur_resid_without`
    (aynı küme); %95 aralık γ'nın jackknife aralığından.
  * İkincil: PROG ve ROBOT tüm geçerli sistemlerde.
  * Kapı: 2025 CMPS ve çekirdek ağırlıklı ortalamaları panelle (≤ 0,003) — betik 44'ün `gates` işlevi.
SONRADAN EKLENENLER: yok.
Girdi: data/pisa/2025/database/CY09_MS_STU_PUF.zip; data/derived/analysis_panel.csv; data/derived/mechanisms/ict_covariate_2025.csv.
Çıktı: data/derived/empirical_fixes/e2_within_ict.csv, e2_country_slopes.csv, e2_summary.json
       (+ önbellek data/derived/cache/e2_2025_students.parquet).
Kullanım (Windows; pyreadstat + pyarrow): python analysis/45_e2_within_country_ict.py
Yazan: Claude Code (bulut oturumu), 2026-09-26. Bu oturumda mikroveri yoktu: betik yalnız sentetik veriyle duman testinden geçti.
"""
from __future__ import annotations

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
CACHE = D / "cache" / "e2_2025_students.parquet"
M = 10
CORE = ["MATH", "READ", "SCIE"]
REPW = [f"W_FSTURWT{i}" for i in range(1, 81)]
FAY_MULT = 1.0 / (80 * (1 - 0.5) ** 2)
XSETS = {"PROG": ["PROG"], "ICTSCH": ["ICTSCH"], "ICTSCH_school": ["ICTSCH_school"], "ROBOT": ["ROBOT"],
         "ICTSCH+ICTSCH_school": ["ICTSCH", "ICTSCH_school"]}


def pv(root: str) -> list[str]:
    return [f"PV{i}{root}" for i in range(1, M + 1)]


# ----------------------------------------------------------------------------- veri
def load() -> pd.DataFrame:
    cols = (["CNT", "CNTSCHID", "W_FSTUWT", "Option_ICTQ", "ST436Q07DA", "ST436Q13DA", "ICTSCH"] + REPW
            + [x for r in CORE + ["CMPS"] for x in pv(r)])
    if CACHE.exists():
        df = pd.read_parquet(CACHE)
    else:
        m43 = importlib.import_module("43_e1_conditional_change")
        with tempfile.TemporaryDirectory(prefix="e2_", dir=os.environ.get("PISA_TMP")) as td:
            df = m43._sav_from_zip(ROOT / "data/pisa/2025/database/CY09_MS_STU_PUF.zip", ".sav", cols, td)
        CACHE.parent.mkdir(parents=True, exist_ok=True)
        df.to_parquet(CACHE, index=False)
    df.columns = [c.upper() for c in df.columns]
    df["CNT"] = df["CNT"].astype(str).str.strip().replace({"TAP": "TWN", "KSV": "XKX"})
    for c in df.columns:
        if c != "CNT":
            df[c] = pd.to_numeric(df[c], errors="coerce")
    return prepare(df)


def prepare(df: pd.DataFrame) -> pd.DataFrame:
    for item, key in (("ST436Q07DA", "PROG"), ("ST436Q13DA", "ROBOT")):
        x = df[item]
        df[key] = np.where(x.isin([1, 2, 3, 4]), (x >= 2).astype(float), np.nan)
    df["ICTSCH"] = df["ICTSCH"].where(df["ICTSCH"] < 95)
    df["OPTION_ICTQ"] = df["OPTION_ICTQ"].where(df["OPTION_ICTQ"].isin([0, 1]))
    v = df["ICTSCH"].notna()
    tmp = pd.DataFrame({"k": df.CNT + "|" + df.CNTSCHID.astype(str), "wx": np.where(v, df.W_FSTUWT * df.ICTSCH.fillna(0), 0.0),
                        "w": np.where(v, df.W_FSTUWT, 0.0)})
    s = tmp.groupby("k")[["wx", "w"]].transform("sum")
    df["ICTSCH_SCHOOL"] = np.where(s.w > 0, s.wx / s.w.where(s.w > 0), np.nan)
    df = df.rename(columns={"ICTSCH_SCHOOL": "ICTSCH_school"})
    return df


def country_means(df: pd.DataFrame, col: str) -> pd.Series:
    ok = df[col].notna()
    g = df[ok].assign(wx=lambda x: x.W_FSTUWT * x[col]).groupby("CNT")[["wx", "W_FSTUWT"]].sum()
    return g.wx / g.W_FSTUWT


def ict_set(df: pd.DataFrame) -> tuple[list[str], list[str]]:
    opt = country_means(df, "OPTION_ICTQ")
    s44 = sorted(opt[opt >= 0.5].index)
    panel = pd.read_csv(D / "analysis_panel.csv")
    p = panel[panel.cycle == 2025]
    oecd = set(p[pd.to_numeric(p.oecd_member, errors="coerce").fillna(0) > 0].iso3)
    return s44, sorted(set(s44) & oecd)


# ----------------------------------------------------------------------------- tahmin
def quad(m, r, s) -> np.ndarray:
    a, b, c = (m - 500) / 100, (r - 500) / 100, (s - 500) / 100
    return np.column_stack([a, b, c, a * a, b * b, c * c, a * b, a * c, b * c])


def country_blocks(df: pd.DataFrame, xs: list[str], p: int) -> dict:
    """Ülke başına within-dönüşümlü normal denklem blokları (A_c, b_c); senato ağırlığı tahmin örnekleminde."""
    cols = [pv(r)[p] for r in CORE] + [pv("CMPS")[p]] + xs
    d = df.dropna(subset=cols + ["W_FSTUWT"])
    out = {}
    for cn, g in d.groupby("CNT"):
        w = g.W_FSTUWT.to_numpy(float)
        w = w * 1000.0 / w.sum()
        X = np.column_stack([quad(*(g[pv(r)[p]].to_numpy(float) for r in CORE))] + [g[x].to_numpy(float) for x in xs])
        y = g[pv("CMPS")[p]].to_numpy(float)
        Xd = X - np.average(X, axis=0, weights=w)
        yd = y - np.average(y, weights=w)
        out[cn] = (Xd.T @ (Xd * w[:, None]), Xd.T @ (yd * w), len(g))
    return out


def pooled_gamma(blocks: dict, countries: list[str], k: int) -> tuple[np.ndarray, np.ndarray]:
    """Havuzlanmış γ (son k katsayı) ve JK1 replikaları (G × k)."""
    cs = [c for c in countries if c in blocks]
    A = sum(blocks[c][0] for c in cs)
    b = sum(blocks[c][1] for c in cs)
    full = np.linalg.solve(A, b)[-k:]
    reps = np.array([np.linalg.solve(A - blocks[c][0], b - blocks[c][1])[-k:] for c in cs])
    return full, reps


def jk_rubin(full: np.ndarray, reps: list[np.ndarray]) -> tuple[np.ndarray, np.ndarray]:
    """full: M × k; reps: M adet (G × k). JK1 örnekleme varyansı PV başına, ortalama + Rubin."""
    vs = []
    for p in range(len(reps)):
        G = reps[p].shape[0]
        vs.append((G - 1) / G * ((reps[p] - reps[p].mean(axis=0)) ** 2).sum(axis=0))
    v_s = np.mean(vs, axis=0)
    v_i = (1 + 1 / len(full)) * full.var(axis=0, ddof=1)
    return full.mean(axis=0), np.sqrt(v_s + v_i)


def country_slope(g: pd.DataFrame, xs: list[str]) -> tuple[float, float]:
    """Ülkenin kendi regresyonu, W_FSTUWT; BRR (80) + Rubin; ilk X'in katsayısı."""
    th = np.full((81, M), np.nan)
    for p in range(M):
        cols = [pv(r)[p] for r in CORE] + [pv("CMPS")[p]] + xs
        h = g.dropna(subset=cols)
        if len(h) < 50 or h[xs[0]].nunique() < 2:
            return np.nan, np.nan
        X = np.column_stack([np.ones(len(h)), quad(*(h[pv(r)[p]].to_numpy(float) for r in CORE))] + [h[x].to_numpy(float) for x in xs])
        y = h[pv("CMPS")[p]].to_numpy(float)
        for j, wc in enumerate(["W_FSTUWT"] + REPW):
            w = h[wc].to_numpy(float)
            Xw = X * w[:, None]
            th[j, p] = np.linalg.lstsq(X.T @ Xw, Xw.T @ y, rcond=None)[0][10]
    theta = th[0]
    v_s = float((FAY_MULT * ((th[1:] - theta[None, :]) ** 2).sum(axis=0)).mean())
    v_i = (1 + 1 / M) * float(theta.var(ddof=1))
    return float(theta.mean()), float(np.sqrt(v_s + v_i))


# ----------------------------------------------------------------------------- ana akış
def main() -> int:
    df = load()
    m44 = importlib.import_module("44_e5_coverage_matched_2003")
    gate = m44.gates(2025, df)
    print("kapı:", gate)
    if gate["failed"]:
        raise SystemExit(f"DUR: 2025 kapısı geçmedi: {gate['failed']}")
    s44, s24 = ict_set(df)
    allsys = m44.systems(2025, "all")  # ikincil küme: ülke düzeyi analizin 84 sistemi (PUF'ta olanlar)
    print(f"BİT anketi kümesi: {len(s44)} sistem ({len(s24)} OECD); TUR içinde: {'TUR' in s44}")
    if "TUR" not in s44:
        raise SystemExit("DUR: Türkiye BİT anketi kümesinde değil")
    rows, summ = [], {"gate": gate, "n_ict_set": len(s44), "n_ict_set_oecd": len(s24), "ict_set": s44, "models": {}, "shares": {}}
    sets = {"ict44": s44, "ict_oecd": s24}
    plan = [(xn, sn, inc) for xn in XSETS for sn in sets for inc in (True, False)]
    plan += [(xn, "all_valid", inc) for xn in ("PROG", "ROBOT") for inc in (True, False)]
    blocks_cache: dict = {}
    for xn, sn, inc in plan:
        xs = XSETS[xn]
        members = sets.get(sn, allsys)
        cs = [c for c in members if inc or c != "TUR"]
        fulls, reps = [], []
        for p in range(M):
            key = (xn, p)
            if key not in blocks_cache:
                blocks_cache[key] = country_blocks(df, xs, p)
            f, r = pooled_gamma(blocks_cache[key], cs, len(xs))
            fulls.append(f)
            reps.append(r)
        est, se = jk_rubin(np.array(fulls), reps)
        n_sys = len([c for c in cs if c in blocks_cache[(xn, 0)]])
        for j, x in enumerate(xs):
            rows.append({"model": xn, "x": x, "set": sn, "tur_included": inc, "n_systems": n_sys,
                         "gamma": round(float(est[j]), 4), "se_jk_rubin": round(float(se[j]), 4),
                         "lo95": round(float(est[j] - 1.96 * se[j]), 4), "hi95": round(float(est[j] + 1.96 * se[j]), 4)})
    t = pd.DataFrame(rows)
    # ülke başına eğimler (tek X modelleri)
    slopes = []
    for xn in ("PROG", "ICTSCH", "ICTSCH_school", "ROBOT"):
        for cn in s44:
            b, se = country_slope(df[df.CNT == cn], XSETS[xn])
            slopes.append({"x": xn, "iso3": cn, "oecd": cn in s24, "gamma_c": b, "se_brr_rubin": se})
    sl = pd.DataFrame(slopes)
    # açıklanan pay
    ict = pd.read_csv(D / "mechanisms" / "ict_covariate_2025.csv")
    den_rows = {sn: ict[(ict.scope == sc) & (ict.spec == "linear") & (ict.covariate == "ICTSCH")].iloc[0]
                for sn, sc in (("ict44", "all"), ("ict_oecd", "oecd"))}
    denom = {sn: float(r.tur_resid_without) for sn, r in den_rows.items()}
    summ["denominator_check"] = {sn: {"n_betik35": int(r.n), "n_this_set": len(sets[sn]), "same_n": int(r.n) == len(sets[sn])}
                                 for sn, r in den_rows.items()}
    for xn in ("PROG", "ICTSCH", "ICTSCH_school", "ROBOT"):
        x = XSETS[xn][0]
        cm = country_means(df, x)
        for sn, members in sets.items():
            for inc in (False, True):
                r = t[(t.model == xn) & (t.x == x) & (t.set == sn) & (t.tur_included == inc)].iloc[0]
                ref = float(cm.reindex([c for c in members if c != "TUR"]).mean())
                dx = float(cm["TUR"]) - ref
                expl = [r.gamma * dx, r.lo95 * dx, r.hi95 * dx]
                summ["shares"][f"{xn}|{sn}|tur_{'dahil' if inc else 'haric'}"] = {
                    "gamma": r.gamma, "x_tur": round(float(cm["TUR"]), 4), "x_ref": round(ref, 4), "dx": round(dx, 4),
                    "explained_pts": round(expl[0], 3), "explained_pts_ci": sorted(round(v, 3) for v in expl[1:]),
                    "tur_country_resid": denom[sn], "share_of_resid": round(expl[0] / denom[sn], 4),
                    "share_ci": sorted(round(v / denom[sn], 4) for v in expl[1:]), "primary": (not inc)}
    for xn in ("PROG", "ICTSCH", "ICTSCH_school", "ROBOT"):
        g = sl[(sl.x == xn) & sl.gamma_c.notna()]
        tur = g[g.iso3 == "TUR"]
        summ["models"][f"country_slopes|{xn}"] = {
            "n": int(len(g)), "median": round(float(g.gamma_c.median()), 4),
            "iqr": [round(float(g.gamma_c.quantile(.25)), 4), round(float(g.gamma_c.quantile(.75)), 4)],
            "tur_gamma": (round(float(tur.gamma_c.iloc[0]), 4) if len(tur) else None),
            "tur_se": (round(float(tur.se_brr_rubin.iloc[0]), 4) if len(tur) else None),
            "tur_rank_from_bottom": (int((g.gamma_c < tur.gamma_c.iloc[0]).sum() + 1) if len(tur) else None)}
    OUT.mkdir(parents=True, exist_ok=True)
    for name, frame in (("e2_within_ict.csv", t), ("e2_country_slopes.csv", sl)):
        tmp = OUT / f"{name}.tmp"
        frame.to_csv(tmp, index=False, encoding="utf-8")
        os.replace(tmp, OUT / name)
    summ["note"] = "E2 — ülke içi BİT/programlama gradyanı; ön-belirleme §0.4 (commit 476fe4e)."
    tmp = OUT / "e2_summary.json.tmp"
    tmp.write_text(json.dumps(summ, ensure_ascii=False, indent=1, default=float), encoding="utf-8")
    os.replace(tmp, OUT / "e2_summary.json")
    print(t.to_string(index=False))
    print(json.dumps(summ["shares"], ensure_ascii=False, indent=1, default=float))
    return 0


if __name__ == "__main__":
    sys.exit(main())
