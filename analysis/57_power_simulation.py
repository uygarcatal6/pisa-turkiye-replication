# -*- coding: utf-8 -*-
"""
57_power_simulation.py — Makale 1: 2015→2025 koşullu sıra testinin gücü (ülke düzeyi Monte Carlo).

ÖN-BELİRLEME: analysis/RESULTS_GUC_SIMULASYONU.md §0 (sha256 4463bdcd…f1ed61f; koşudan önce proje günlüğüne
yazıldı, 4 Eki 2026). Yazar onayı: "Ülke düzeyi Monte Carlo".
  * Test betik 43 ile aynı: pair_frame (betik 34 load), d_i = α + β₁ΔC_i + β₂C0_i, birini-dışarıda tahmin hatası (PRESS),
    Türkiye'nin sırası #(e < e_TUR) + 1, ret sıra/N ≤ 0,10. Hücre = ölçü (d_sd birincil, d_pts) × örneklem × biçim.
  * DGP (§0.3, IN-ASSUMPTION): diğer sistemlerin d'si Türkiye-dışı uyum + standartlaştırılmış artık havuzundan iadeli çekiliş;
    Türkiye'nin d'si aynı ortalama + havuzdan hata − (τ − λ)·Δ/s; τ = b₂₅ + γ·s, b₂₅ 2025 kesitinin Türkiye çekirdeğindeki yerel
    eğimi, s = RMSE₂₅ (d_sd) ya da 1 (d_pts); ΔC_TUR = 51,21 sabit (Δ'sı şişme).
  * Değişkeler (§0.4, OUT-OF-ASSUMPTION): O1 ΔC'de ölçme hatası s_ν ∈ {3,5; 7} (γ_true = γ̂/ρ); O2 normal hata.
  * Izgara Δ ∈ {0, 5, …, 200}, λ ∈ {0; 0,25; 0,5}, R = 10.000; tohum ön-belirlemede SeedSequence(20261004).spawn, (rejim,
    hücre, λ, Δ) sırası; SONRADAN 4'ten beri SeedSequence(20261004, spawn_key=(rejim, hücre, λ)), Δ'lar arasında ortak çekiliş.
SONRADAN (4 Eki 2026, duman testinden sonra, tam koşudan önce; RESULTS_GUC_SIMULASYONU.md §0.7): A3 (ii) denetimi d_sd'de
  d düzeyindeki kaymanın tam boru hattının 0,36–0,97'si kadar olduğunu gösterdi (Türkiye 2025 kesitinde aykırılaştıkça RMSE₂₅
  büyüyor). Birincil "IN" rejimi artık tam eşlemeyi kullanır: yinelemenin d'si 2025 artıklarına çevrilir, Türkiye'nin yeni-alan
  ortalaması (τ − λ)Δ düşürülür (şapka matrisiyle güncelleme), RMSE₂₅ yeniden hesaplanır, d betik 34'ün tanımıyla yeniden
  kurulur. Ön-belirlenen d düzeyi formülü "IN_dduzey" satırı olarak raporlanır. O1 ve O2 tam eşlemeyle.
SONRADAN 2 (§0.8, ikinci duman testinden sonra): temiz dünya d_sd düzeyinde üretilince ortak sistemlerin 2025 artık standart
  sapması 27 çıktı (gözlenen 14; d_sd'nin 2015 artığıyla ilişkisi bağımsız çekilişte kayboluyor), büyüklük yapay olarak 0,02'ye
  düştü. Temiz dünya artık puanla üretilir: 2025 artığı = r15 + d_pts koşullu modelinin ortalaması (Türkiye dışarıda) + puan
  havuzundan hata; τ yapısal ve tek: τ_p = b₂₅ + γ_pts; analist iki ölçüyü de bu artıklardan hesaplar.
SONRADAN 3 (§0.8, üçüncü duman testinden sonra): φ = 1 üreteci 2015 artığının tamamen kalıcı olduğunu varsayıyor; veride
  r25'in r15'e eğimi 0,24–0,51 (Türkiye dışarıda). Birincil IN rejimi: 2025 artığı = a + φ·r15 + γΔC + βC0 + e (Türkiye
  dışarıda OLS; standartlaştırılmış havuz), τ_r = b₂₅ + γ; O1 ve O2 bunun üzerine. φ = 1 üreteci "O3_phi1" satırı.
SONRADAN 4 (§0.9, taze bağlamlı doğrulamadan sonra; wf_…): (i) analist 2025 kesitini yeniden uydurduğu için
  üretilen artık vektörü M₂₅ ile izdüşürülür (önce yalnız δ kayması şapka matrisinden geçiyordu); (ii) kapılar simülasyondan
  önce; r15/rsd15 betik 34'ün 2015 artıklarıyla, stokastik bir yineleme betik 34/43 yoluyla sınanır; (iii) A3 (ii) öngörüsü
  boru hattıyla aynı τ'yu kullanır; (iv) tohum içerikten (rejim, hücre, λ) türetilir, Δ'lar arasında ortak rastgele sayı;
  (v) çıktıda varsayım (IN/OUT) ve kullanılan τ sütunları; Δ = 0 ret oranı yalnız IN_dduzey'de nominal büyüklükle karşılaştırılır.
SONRADAN 5 (4 Eki 2026; RESULTS_EMPIRICAL_FIXES.md §0.14, betik 59): her yinelemede ikinci test, aynı çekilişlerle: dış-studentize
  artık sırası (t_i = r_i/(s₍ᵢ₎√(1 − h_ii))). Çıktıda `test` ∈ {press, stud}; press satırları önceki koşuyla aynı olmalı.
Doğru değer DGP parametresidir (Δ, λ); güç = ret oranı, MCSE = √(p(1−p)/R).
Kapılar: betik 34 artık değişimiyle çerçeve (betik 43 gate_vs_residual_change); Türkiye'nin gözlenen sıra ve e'si e1_summary.json
ile; 2025 yeniden uydurma artık ve RMSE'si dosyayla; ΔC_TUR = 51,2107.
Girdi: betik 34 load() (data/derived/mechanisms/placebo_conditional_*.csv), data/derived/placebo_backbone/residual_change.csv,
       data/derived/empirical_fixes/e1_summary.json.
Çıktı: data/derived/power_sim/{ps_cells.csv, ps_mde.csv, ps_inversion.csv, ps_pipeline_check.csv, ps_raw_primary.npz,
       ps_summary.json}
Kullanım: python analysis/57_power_simulation.py            (R = 10.000)
          python analysis/57_power_simulation.py --quick    (R = 1.000, çıktı power_sim/quick/)
Yazan: Claude Code (Opus 5.5), 2026-10-04.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib
import json
import os
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE))
m34 = importlib.import_module("34_a1_residual_change")
m43 = importlib.import_module("43_e1_conditional_change")

D = ROOT / "data" / "derived"
E1 = D / "empirical_fixes" / "e1_summary.json"
E1S = D / "empirical_fixes" / "e1_studentized_summary.json"
SEED = 20261004
DELTAS = np.arange(0, 205, 5)                     # 41 değer
LAMS = [0.0, 0.25, 0.5]
SCOPES_SPECS = [("all", "linear"), ("all", "quadratic"), ("oecd", "linear"), ("oecd", "quadratic")]
MEASURES = ["d_sd", "d_pts"]
REGIMES = [("IN", None), ("IN_dduzey", None), ("O1", 3.5), ("O1", 7.0), ("O2", None), ("O3_phi1", None)]
ALPHA = 0.10
DC_TUR = 51.2107
PIPE_DELTAS, PIPE_LAMS = [20, 40, 80], [0.0, 0.5]


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


# ----------------------------------------------------------------------------- 2025 kesiti ve hücre kurulumu
def fit2025(data: dict, scope: str, spec: str) -> dict:
    g = data[2025][(data[2025].scope == scope) & (data[2025].spec == spec)].set_index("iso3")
    res, rmse = m34.refit(g.core, g.dom, spec)
    if float((res - g.residual).abs().max()) > 1e-6:
        raise SystemExit(f"DUR (kapı): 2025 {scope}/{spec} yeniden uydurma artığı dosyadan farklı")
    if abs(rmse - float((g.residual / g.resid_sd).median())) > 1e-4:
        raise SystemExit(f"DUR (kapı): 2025 {scope}/{spec} RMSE dosyadan farklı")
    x = g.core.to_numpy(float)
    X = np.column_stack([np.ones_like(x), x] + ([x ** 2] if spec == "quadratic" else []))
    beta = np.linalg.lstsq(X, g.dom.to_numpy(float), rcond=None)[0]
    c = float(g.core.loc["TUR"])
    b25 = float(beta[1] + (2.0 * beta[2] * c if spec == "quadratic" else 0.0))
    H25 = X @ np.linalg.inv(X.T @ X) @ X.T
    t25 = list(g.index).index("TUR")
    return {"b25": b25, "rmse25": rmse, "iso25": list(g.index), "r25": res.to_numpy(float), "k25": X.shape[1],
            "M25": np.eye(len(g)) - H25, "t25": t25, "fit25": g.dom.to_numpy(float) - res.to_numpy(float)}


def stud_t(X: np.ndarray, y: np.ndarray) -> np.ndarray:
    """Dış-studentize artık (betik 59 ile aynı formül)."""
    n, p = X.shape
    XtXi = np.linalg.inv(X.T @ X)
    r = y - X @ (XtXi @ X.T @ y)
    h = np.einsum("ij,jk,ik->i", X, XtXi, X)
    s2_i = ((r @ r) - r ** 2 / (1.0 - h)) / (n - p - 1)
    return r / np.sqrt(s2_i * (1.0 - h))


def lofit(X: np.ndarray, y: np.ndarray, it: int):
    """Türkiye dışarıda OLS (A1) ve standartlaştırılmış, ortalaması çıkarılmış artık havuzu (A2)."""
    keep = np.arange(len(y)) != it
    beta = np.linalg.lstsq(X[keep], y[keep], rcond=None)[0]
    Xk = X[keep]
    hk = np.einsum("ij,jk,ik->i", Xk, np.linalg.inv(Xk.T @ Xk), Xk)
    pool = (y[keep] - Xk @ beta) / np.sqrt(1.0 - hk)
    return beta, pool - pool.mean()


def cell_setup(frame: pd.DataFrame, measure: str, f25: dict) -> dict:
    b25, rmse25 = f25["b25"], f25["rmse25"]
    iso = list(frame.index)
    it = iso.index("TUR")
    N = len(iso)
    dC, C0 = frame.dC.to_numpy(float), frame.C0.to_numpy(float)
    y = frame[measure].to_numpy(float)
    X = m43.design(dC, C0)
    beta, pool = lofit(X, y, it)                                        # IN_dduzey: ön-belirlenen, ölçünün kendi modeli
    beta_p, pool_p = lofit(X, frame.d_pts.to_numpy(float), it)          # O3: φ = 1 puan üreteci (SONRADAN §0.8)
    r15 = f25["r25"][np.array([f25["iso25"].index(c) for c in iso])] - frame.d_pts.to_numpy(float)
    Xr = np.column_stack([np.ones(N), r15, dC, C0])
    beta_r, pool_r = lofit(Xr, f25["r25"][np.array([f25["iso25"].index(c) for c in iso])], it)  # IN/O1/O2: yapısal
    s = rmse25 if measure == "d_sd" else 1.0
    H = X @ np.linalg.inv(X.T @ X) @ X.T
    e_obs = m43.press(X, y)
    ic = np.array([f25["iso25"].index(c) for c in iso])                # ortak sistemlerin 2025 sırası
    return {"iso": iso, "it": it, "N": N, "dC": dC, "C0": C0, "y": y, "X": X, "M": np.eye(N) - H, "h": np.diag(H).copy(),
            "sd": measure == "d_sd", "s": s, "b25": b25, "rmse25": rmse25,
            "beta": beta, "pool": pool, "tau": float(b25 + beta[1] * s),           # ön-belirlenen τ (ölçüye göre)
            "beta_p": beta_p, "pool_p": pool_p, "tau_p": float(b25 + beta_p[1]),   # φ = 1 üretecinin τ'su
            "Xr": Xr, "beta_r": beta_r, "pool_r": pool_r, "tau_r": float(b25 + beta_r[2]),  # yapısal τ (puan)
            "ic": ic, "r25": f25["r25"], "M25": f25["M25"], "t25": f25["t25"], "k25": f25["k25"], "fit25": f25["fit25"],
            "r15": f25["r25"][ic] - frame.d_pts.to_numpy(float),                  # 2015 artığı (puan)
            "rsd15": f25["r25"][ic] / rmse25 - frame.d_sd.to_numpy(float),        # 2015 artığı (RMSE birimi)
            "e_obs": e_obs, "rank_obs": int((e_obs < e_obs[it]).sum() + 1),
            "rank_obs_stud": int((t_obs := stud_t(X, y)) .__lt__(t_obs[it]).sum() + 1)}


# ----------------------------------------------------------------------------- tek görev (R yineleme)
def draw(pool: np.ndarray, R: int, N: int, rng: np.random.Generator, normal: bool) -> np.ndarray:
    if normal:
        return rng.normal(0.0, float(pool.std(ddof=1)), size=(R, N))
    return pool[rng.integers(0, len(pool), size=(R, N))]


def analyst_d(cs: dict, R25c: np.ndarray, delta_pts: float) -> np.ndarray:
    """SONRADAN §0.7–0.9: ortak sistemlerin üretilen 2025 artıkları (puan, R×N; öbür sistemler gözlenen) → Türkiye'nin
    yeni-alan ortalaması delta_pts düşer → analist 2025 kesitini yeniden uydurur: artık = M₂₅·(uyum + üretilen − δe_T)
    = M₂₅·(üretilen − δe_T) → RMSE₂₅ (ddof = parametre sayısı) → betik 34 tanımıyla analistin d'si."""
    R25 = np.tile(cs["r25"], (R25c.shape[0], 1))
    R25[:, cs["ic"]] = R25c
    if delta_pts:
        R25[:, cs["t25"]] -= delta_pts
    R25 = R25 @ cs["M25"]                                               # M₂₅ simetrik
    if not cs["sd"]:
        return R25[:, cs["ic"]] - cs["r15"][None, :]
    rmse = np.sqrt((R25 ** 2).sum(axis=1) / (R25.shape[1] - cs["k25"]))
    return R25[:, cs["ic"]] / rmse[:, None] - cs["rsd15"][None, :]


def press_rank(cs: dict, Y: np.ndarray, X=None):
    """(PRESS sırası, dış-studentize sıra); ikisi de Türkiye için, aynı Y'den."""
    it, N = cs["it"], Y.shape[1]
    if X is None:
        r = Y @ cs["M"]                                                  # M simetrik
        h = np.broadcast_to(cs["h"], r.shape)
        k = cs["X"].shape[1]
    else:
        XtXi = np.linalg.inv(np.einsum("rni,rnj->rij", X, X))
        b = np.einsum("rij,rnj,rn->ri", XtXi, X, Y)
        h = np.einsum("rni,rij,rnj->rn", X, XtXi, X)
        r = Y - np.einsum("rni,ri->rn", X, b)
        k = X.shape[2]
    e = r / (1.0 - h)
    s2_i = ((r ** 2).sum(axis=1, keepdims=True) - r ** 2 / (1.0 - h)) / (N - k - 1)
    t = r / np.sqrt(s2_i * (1.0 - h))
    return (((e < e[:, [it]]).sum(axis=1) + 1).astype(np.int16), ((t < t[:, [it]]).sum(axis=1) + 1).astype(np.int16))


def tau_used(cs: dict, regime: str, s_nu) -> float:
    if regime == "IN_dduzey":
        return cs["tau"]
    if regime == "O3_phi1":
        return cs["tau_p"]
    if regime == "O1":
        return float(cs["b25"] + cs["beta_r"][2] / (1.0 - s_nu ** 2 / float(np.var(cs["dC"], ddof=1))))
    return cs["tau_r"]


def sim_task(cs: dict, regime: str, s_nu, lam: float, delta: float, R: int, rng: np.random.Generator) -> np.ndarray:
    """Türkiye'nin koşullu sırasını (R,) döndürür."""
    N, it = cs["N"], cs["it"]
    if regime == "IN_dduzey":                                           # ön-belirlenen d düzeyi formülü (§0.3)
        Y = (cs["X"] @ cs["beta"])[None, :] + draw(cs["pool"], R, N, rng, False)
        Y[:, it] -= (cs["tau"] - lam) * delta / cs["s"]
        return press_rank(cs, Y)
    if regime == "O3_phi1":                                             # φ = 1: 2025 artığı = r15 + d_pts modeli + e
        mu = cs["r15"] + cs["X"] @ cs["beta_p"]
        Y = analyst_d(cs, mu[None, :] + draw(cs["pool_p"], R, N, rng, False), (cs["tau_p"] - lam) * delta)
        return press_rank(cs, Y)
    br, tau = cs["beta_r"].copy(), cs["tau_r"]
    if regime == "O1":
        br[2] = br[2] / (1.0 - s_nu ** 2 / float(np.var(cs["dC"], ddof=1)))   # γ_true = γ̂/ρ
        tau = cs["b25"] + br[2]
    E = draw(cs["pool_r"], R, N, rng, normal=(regime == "O2"))
    Y = analyst_d(cs, (cs["Xr"] @ br)[None, :] + E, (tau - lam) * delta)   # temiz 2025 artığı = a + φ·r15 + γΔC + βC0 + e
    if regime != "O1":
        return press_rank(cs, Y)
    dCo = cs["dC"][None, :] + rng.normal(0.0, s_nu, size=(R, N))
    return press_rank(cs, Y, np.stack([np.ones((R, N)), dCo, np.broadcast_to(cs["C0"], (R, N))], axis=2))


# ----------------------------------------------------------------------------- tam boru hattı denetimi (A3 ii)
def pipeline_check(data: dict, scope: str, spec: str, measure: str, cs: dict, delta: float, lam: float) -> dict:
    """Gözlenen veride Türkiye'nin 2025 yeni-alan ortalaması yapısal (τ_r − λ)Δ puan düşürülür, betik 34 yolundan yeniden
    hesaplanır. Oran: tam kayma / aynı τ_r ile d düzeyi doğrusal öngörü −(τ_r − λ)Δ/s. Ön-belirlenen formül (ölçünün τ'su,
    −(τ − λ)Δ/s) ayrı sütun. _exact_raw yuvarlanmamış değerdir (kapı için; CSV'ye yazılmaz)."""
    d25 = data[2025]
    mask = (d25.scope == scope) & (d25.spec == spec)
    g = d25[mask].set_index("iso3").copy()
    g.loc["TUR", "dom"] -= (cs["tau_r"] - lam) * delta
    res, rm = m34.refit(g.core, g.dom, spec)
    g["residual"], g["resid_sd"] = res, res / rm
    data2 = dict(data)
    data2[2025] = pd.concat([d25[~mask], g.reset_index()[d25.columns]], ignore_index=True)
    f2 = m43.pair_frame(data2, 2015, 2025, scope, spec)
    if list(f2.index) != cs["iso"]:
        raise SystemExit("DUR: boru hattı denetiminde sistem kümesi değişti")
    e2 = m43.press(m43.design(f2.dC.to_numpy(float), f2.C0.to_numpy(float)), f2[measure].to_numpy(float))
    it = cs["it"]
    exact = float(e2[it] - cs["e_obs"][it])
    pred = float(-(cs["tau_r"] - lam) * delta / cs["s"])                # aynı τ (τ_r), d düzeyi doğrusal öngörü
    form = float(-(cs["tau"] - lam) * delta / cs["s"])                  # ön-belirlenen formül (ölçünün τ'su)
    return {"scope": scope, "spec": spec, "measure": measure, "lam": lam, "delta": delta, "tau_r": round(cs["tau_r"], 4),
            "tau_meas": round(cs["tau"], 4), "shift_pred_tau_r": round(pred, 5), "shift_exact": round(exact, 5),
            "ratio_exact_to_pred": round(exact / pred, 4) if pred else None, "shift_dduzey_formula": round(form, 5),
            "rank_exact": int((e2 < e2[it]).sum() + 1), "_exact_raw": exact}


def write_atomic(df: pd.DataFrame, path: Path):
    tmp = path.with_suffix(path.suffix + ".tmp")
    df.to_csv(tmp, index=False, encoding="utf-8")
    os.replace(tmp, path)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--quick", action="store_true")
    a = ap.parse_args()
    R = 1000 if a.quick else 10000
    out = D / "power_sim" / ("quick" if a.quick else "")
    out.mkdir(parents=True, exist_ok=True)
    t0 = time.time()

    data = m34.load()
    frames = {("2015->2025", sc, sp): m43.pair_frame(data, 2015, 2025, sc, sp) for sc, sp in SCOPES_SPECS}
    gate = m43.gate_vs_residual_change(frames)
    e1 = {(c["scope"], c["spec"], c["measure"]): c for c in json.loads(E1.read_text(encoding="utf-8"))["cells"]
          if c["pair"] == "2015->2025"}
    cells, fit = {}, {}
    for sc, sp in SCOPES_SPECS:
        fit[(sc, sp)] = fit2025(data, sc, sp)
        f = frames[("2015->2025", sc, sp)]
        if abs(float(f.dC.loc["TUR"]) - DC_TUR) > 1e-3:
            raise SystemExit("DUR (kapı): ΔC_TUR 51,2107 değil")
        for ms in MEASURES:
            cs = cell_setup(f, ms, fit[(sc, sp)])
            ref = e1[(sc, sp, ms)]
            if cs["rank_obs"] != ref["tur_rank_cond"] or abs(cs["e_obs"][cs["it"]] - ref["tur_loo_err"]) > 1e-3:
                raise SystemExit(f"DUR (kapı): {sc}/{sp}/{ms} Türkiye sırası/e betik 43'ten farklı")
            cells[(sc, sp, ms)] = cs
    e1s = {(c["scope"], c["spec"], c["measure"]): c for c in json.loads(E1S.read_text(encoding="utf-8"))["cells"]
           if c["pair"] == "2015->2025"}
    for key, cs in cells.items():
        if cs["rank_obs_stud"] != e1s[key]["tur_rank_stud"]:
            raise SystemExit(f"DUR (kapı): {key} gözlenen studentize sıra betik 59'dan farklı")
    print("ön kapılar geçti:", gate, "| hücre:", len(cells), "| studentize sıra = betik 59")

    # Kapılar (SONRADAN §0.9: simülasyondan önce)
    g15 = {}
    for (sc, sp, ms), cs in cells.items():                             # dış kaynak: betik 34'ün 2015 artıkları
        d15 = data[2015][(data[2015].scope == sc) & (data[2015].spec == sp)].set_index("iso3").loc[cs["iso"]]
        g15[f"{sc}/{sp}/{ms}"] = max(float(np.abs(cs["r15"] - d15.residual.to_numpy(float)).max()),
                                     float(np.abs(cs["rsd15"] - d15.resid_sd.to_numpy(float)).max()))
    if max(g15.values()) > 1e-8:
        raise SystemExit(f"DUR (kapı): r15/rsd15 betik 34'ün 2015 artıklarından farklı {g15}")
    pc = [pipeline_check(data, sc, sp, ms, cells[(sc, sp, ms)], dl, lam)
          for (sc, sp, ms) in cells for dl in PIPE_DELTAS for lam in PIPE_LAMS]
    pcdf = pd.DataFrame(pc)
    gmap = 0.0
    for r in pc:                                                        # gözlenen veride eşleme = betik 34 yeniden uydurma yolu
        cs = cells[(r["scope"], r["spec"], r["measure"])]
        dm = analyst_d(cs, cs["r25"][cs["ic"]][None, :], (cs["tau_r"] - r["lam"]) * r["delta"])[0]
        em = m43.press(cs["X"], dm)
        gmap = max(gmap, abs((em[cs["it"]] - cs["e_obs"][cs["it"]]) - r["_exact_raw"]))
    pcdf = pcdf.drop(columns="_exact_raw")
    if gmap > 1e-8:
        raise SystemExit(f"DUR (kapı): tam eşleme betik 34 yolundan farklı ({gmap})")
    gsto, gpress = 0.0, 0.0
    for k, ((sc, sp, ms), cs) in enumerate(cells.items()):            # stokastik: rastgele yinelemeler, betik 34/43 yolu
        rng0 = np.random.default_rng(np.random.SeedSequence(SEED, spawn_key=(99, k)))
        d25 = data[2025]
        mask = (d25.scope == sc) & (d25.spec == sp)
        for gen in ("IN", "O3_phi1"):
            if gen == "IN":
                R25s, tau = (cs["Xr"] @ cs["beta_r"])[None, :] + draw(cs["pool_r"], 3, cs["N"], rng0, False), cs["tau_r"]
            else:
                R25s, tau = (cs["r15"] + cs["X"] @ cs["beta_p"])[None, :] + draw(cs["pool_p"], 3, cs["N"], rng0, False), cs["tau_p"]
            for R25c in R25s:
                for mult in (40.0, 200.0):
                    dl = tau * mult
                    g = d25[mask].set_index("iso3").copy()
                    raw25 = cs["r25"].copy(); raw25[cs["ic"]] = R25c; raw25[cs["t25"]] -= dl
                    g["dom"] = cs["fit25"] + raw25
                    res, rm = m34.refit(g.core, g.dom, sp)
                    g["residual"], g["resid_sd"] = res, res / rm
                    data2 = dict(data)
                    data2[2025] = pd.concat([d25[~mask], g.reset_index()[d25.columns]], ignore_index=True)
                    f2 = m43.pair_frame(data2, 2015, 2025, sc, sp)
                    gsto = max(gsto, float(np.abs(f2[ms].to_numpy(float) - analyst_d(cs, R25c[None, :], dl)[0]).max()))
        # O1 yolu: yineleme başına X'li PRESS = betik 43 press
        Y = cs["y"][None, :] + draw(cs["pool"], 2, cs["N"], rng0, False)
        dCo = cs["dC"][None, :] + rng0.normal(0.0, 7.0, size=(2, cs["N"]))
        Xs = np.stack([np.ones((2, cs["N"])), dCo, np.broadcast_to(cs["C0"], (2, cs["N"]))], axis=2)
        rk, rks = press_rank(cs, Y, Xs)
        for j in range(2):
            Xj = m43.design(dCo[j], cs["C0"])
            e43 = m43.press(Xj, Y[j])
            tj = stud_t(Xj, Y[j])
            gpress = max(gpress, abs(int((e43 < e43[cs["it"]]).sum() + 1) - int(rk[j])),
                         abs(int((tj < tj[cs["it"]]).sum() + 1) - int(rks[j])))
    if gpress != 0:
        raise SystemExit("DUR (kapı): O1 PRESS yolu betik 43 press ile aynı sırayı vermiyor")
    if gsto > 1e-8:
        raise SystemExit(f"DUR (kapı): stokastik yineleme betik 34/43 yolundan farklı ({gsto})")
    print(f"kapılar: r15/rsd15 {max(g15.values()):.1e} · eşleme {gmap:.1e} · stokastik {gsto:.1e} · O1 PRESS sıra farkı {gpress}")

    cell_keys = [(sc, sp, ms) for sc, sp in SCOPES_SPECS for ms in MEASURES]
    tasks = [(ri, rg, nu, ci, sc, sp, ms, li, lam, float(dl)) for ri, (rg, nu) in enumerate(REGIMES)
             for ci, (sc, sp, ms) in enumerate(cell_keys) for li, lam in enumerate(LAMS) for dl in DELTAS]
    rows, raw = [], {}
    for (ri, rg, nu, ci, sc, sp, ms, li, lam, dl) in tasks:
        cs = cells[(sc, sp, ms)]
        ss = np.random.SeedSequence(SEED, spawn_key=(ri, ci, li))      # içerikten tohum; Δ'lar arasında ortak çekiliş
        rk2 = sim_task(cs, rg, nu, lam, dl, R, np.random.default_rng(ss))
        for test, rk in zip(("press", "stud"), rk2):
          rej = int((rk / cs["N"] <= ALPHA).sum())
          p = rej / R
          hist = np.bincount(rk, minlength=cs["N"] + 1)[1:]
          rows.append({"regime": rg if nu is None else f"O1_snu{nu}", "assumption": "IN" if rg.startswith("IN") else "OUT",
                     "test": test, "measure": ms, "scope": sc, "spec": sp, "lam": lam,
                     "delta": dl, "N": cs["N"], "R": R, "rejections": rej, "power": round(p, 5),
                     "mcse": round(float(np.sqrt(p * (1 - p) / R)), 5), "tau": round(tau_used(cs, rg, nu), 4),
                     "tau_def": {"IN_dduzey": "b25+gamma_meas*s", "O3_phi1": "b25+gamma_pts"}.get(rg,
                                 "b25+gamma_r/rho" if rg == "O1" else "b25+gamma_r"),
                     "rank_hist": " ".join(map(str, hist.tolist()))})
          if rg == "IN" and sp == "linear":
            raw[(test, ms, sc, lam, dl)] = rk
    cdf = pd.DataFrame(rows)
    write_atomic(cdf, out / "ps_cells.csv")

    # MDE80 ve büyüklük
    mde = []
    for key, g in cdf.groupby(["regime", "assumption", "test", "measure", "scope", "spec", "lam"], sort=False):
        g = g.sort_values("delta")
        pw, dl = g.power.to_numpy(), g.delta.to_numpy()
        idx = np.flatnonzero(pw >= 0.80)
        if len(idx):
            j = int(idx[0])
            interp = float(dl[j]) if j == 0 else float(dl[j - 1] + (0.80 - pw[j - 1]) * (dl[j] - dl[j - 1]) / (pw[j] - pw[j - 1]))
            grid = float(dl[j])
        else:
            interp = grid = np.nan
        N = int(g.N.iloc[0])
        mde.append(dict(zip(["regime", "assumption", "test", "measure", "scope", "spec", "lam"], key)) |
                   {"N": N, "p_rej_delta0": float(g.power.iloc[0]), "p_rej_delta0_mcse": float(g.mcse.iloc[0]),
                    "size_nominal_exchangeable": (round(int(np.floor(ALPHA * N + 1e-9)) / N, 4)
                                                  if key[0] == "IN_dduzey" else np.nan),
                    "power_at_51": float(np.interp(DC_TUR, dl, pw)), "mde80_grid": grid, "mde80_interp": round(interp, 2)})
    mdf = pd.DataFrame(mde)

    def mde_of(pw: np.ndarray) -> float:
        idx = np.flatnonzero(pw >= 0.80)
        if not len(idx):
            return np.nan
        j = int(idx[0])
        return float(DELTAS[j]) if j == 0 else float(DELTAS[j - 1] + (0.80 - pw[j - 1]) * 5.0 / (pw[j] - pw[j - 1]))
    mc = []
    brng = np.random.default_rng(np.random.SeedSequence(SEED, spawn_key=(77,)))
    for (test, ms, sc, lam, _), _v in [(k, None) for k in raw if k[4] == 0.0]:
        N = cells[(sc, "linear", ms)]["N"]
        rej = np.array([raw[(test, ms, sc, lam, float(dl))] / N <= ALPHA for dl in DELTAS])   # (Δ, R)
        bm, bp = [], []
        for _b in range(500):
            ii = brng.integers(0, R, R)
            pw = rej[:, ii].mean(axis=1)
            bm.append(mde_of(pw)); bp.append(float(np.interp(DC_TUR, DELTAS, pw)))
        bm = np.array(bm)
        mc.append({"regime": "IN", "test": test, "measure": ms, "scope": sc, "spec": "linear", "lam": lam,
                   "mde80_mcse": round(float(np.nanstd(bm, ddof=1)), 2) if np.isfinite(bm).sum() > 1 else np.nan,
                   "mde80_boot_na_share": round(float(np.isnan(bm).mean()), 3),
                   "power_at_51_mcse": round(float(np.std(bp, ddof=1)), 4)})
    mdf = mdf.merge(pd.DataFrame(mc), on=["regime", "test", "measure", "scope", "spec", "lam"], how="left")
    write_atomic(mdf, out / "ps_mde.csv")

    # Uyumlu Δ üst sınırı: P_Δ(sıra_sim ≥ sıra_gözlenen) ≥ 0,10 olan en büyük ızgara Δ'sı (IN rejimi)
    inv = []
    for (sc, sp, ms), cs in cells.items():
        for lam, test in [(l_, t_) for l_ in LAMS for t_ in ("press", "stud")]:
            g = cdf[(cdf.regime == "IN") & (cdf.test == test) & (cdf.scope == sc) & (cdf.spec == sp) & (cdf.measure == ms)
                    & (cdf.lam == lam)]
            g = g.sort_values("delta")
            ro = cs["rank_obs"] if test == "press" else cs["rank_obs_stud"]
            pr = [sum(map(int, h.split()[ro - 1:])) / R for h in g.rank_hist]
            ok = [d for d, q in zip(g.delta, pr) if q >= 0.10]
            inv.append({"regime": "IN", "test": test, "measure": ms, "scope": sc, "spec": sp, "lam": lam, "rank_obs": ro, "N": cs["N"],
                        "p_obs_at_delta0": round(pr[0], 4), "delta_upper90": max(ok) if ok else np.nan})
    write_atomic(pd.DataFrame(inv), out / "ps_inversion.csv")

    write_atomic(pcdf, out / "ps_pipeline_check.csv")

    tmp = out / "ps_raw_primary.npz.tmp"
    with open(tmp, "wb") as fh:
        np.savez_compressed(fh, ranks=np.array([[[[[raw[(test, ms, sc, lam, float(dl))] for dl in DELTAS] for lam in LAMS]
                                                   for sc in ("all", "oecd")] for ms in MEASURES] for test in ("press", "stud")]),
                            tests=np.array(["press", "stud"]), measures=np.array(MEASURES), scopes=np.array(["all", "oecd"]), lams=np.array(LAMS), deltas=DELTAS,
                            N=np.array([cells[("all", "linear", "d_sd")]["N"], cells[("oecd", "linear", "d_sd")]["N"]]),
                            regime=np.array("IN"), spec=np.array("linear"))
    os.replace(tmp, out / "ps_raw_primary.npz")

    inputs = [ROOT / "data/derived/mechanisms" / f for f in ("placebo_conditional_2003ps_puf.csv", "placebo_conditional_2012ps_puf.csv",
                                                              "placebo_conditional_2015cps.csv", "placebo_conditional_2025.csv")]
    inputs += [D / "placebo_backbone" / "residual_change.csv", E1]
    summ = {"note": "Makale 1 koşullu sıra testinin gücü; ön-belirleme analysis/RESULTS_GUC_SIMULASYONU.md §0",
            "fingerprint": {"script": sha(Path(__file__)), "betik34": sha(HERE / "34_a1_residual_change.py"),
                            "betik43": sha(HERE / "43_e1_conditional_change.py"),
                            "inputs": {str(p.relative_to(ROOT)).replace("\\", "/"): sha(p) for p in inputs},
                            "numpy": np.__version__, "pandas": pd.__version__},
            "params": {"seed": SEED, "R": R, "deltas": [float(x) for x in DELTAS], "lams": LAMS, "alpha": ALPHA,
                       "regimes": [f"{r}{'' if n is None else '_snu' + str(n)}" for r, n in REGIMES], "dC_TUR": DC_TUR},
            "gates": {"betik34_artik_degisimi": gate, "e1_sira_ve_e (gerileme kapısı)": "geçti", "fit2025": "geçti",
                      "r15_rsd15_vs_2015_max": max(g15.values()), "esleme_vs_betik34_max": gmap,
                      "stokastik_yineleme_max (IN+O3, 3 yineleme, δ = 40τ ve 200τ)": gsto, "O1_press_sira_farki": gpress},
            "cell_inputs": [{"scope": sc, "spec": sp, "measure": ms, "N": cs["N"], "b25": round(cs["b25"], 4),
                             "s": round(cs["s"], 4), "gamma": round(float(cs["beta"][1]), 5), "tau_meas": round(cs["tau"], 4),
                             "gamma_p": round(float(cs["beta_p"][1]), 5), "tau_p": round(cs["tau_p"], 4),
                             "pool_n": int(len(cs["pool"])), "pool_sd": round(float(cs["pool"].std(ddof=1)), 5),
                             "pool_p_sd": round(float(cs["pool_p"].std(ddof=1)), 5),
                             "phi": round(float(cs["beta_r"][1]), 4), "gamma_r": round(float(cs["beta_r"][2]), 4),
                             "tau_r": round(cs["tau_r"], 4), "pool_r_sd": round(float(cs["pool_r"].std(ddof=1)), 4),
                             "rank_obs": cs["rank_obs"], "rank_obs_stud": cs["rank_obs_stud"],
                             "tur_leverage": round(float(cs["h"][cs["it"]]), 4)}
                            for (sc, sp, ms), cs in cells.items()],
            "pipeline_ratio_range": [float(pcdf.ratio_exact_to_pred.min()), float(pcdf.ratio_exact_to_pred.max())],
            "seed_scheme": "SeedSequence(20261004, spawn_key=(rejim, hücre, λ)); Δ'lar arasında ortak rastgele sayı",
            "seconds": round(time.time() - t0, 1)}
    tmpj = out / "ps_summary.json.tmp"
    tmpj.write_text(json.dumps(summ, ensure_ascii=False, indent=1), encoding="utf-8")
    os.replace(tmpj, out / "ps_summary.json")
    prim = mdf[(mdf.regime.isin(["IN", "IN_dduzey"])) & (mdf.measure == "d_sd") & (mdf.spec == "linear") & (mdf.lam == 0.0)]
    print(prim[["regime", "test", "scope", "p_rej_delta0", "power_at_51", "mde80_interp"]].to_string(index=False))
    print("boru hattı oranı:", summ["pipeline_ratio_range"], "| süre:", summ["seconds"], "sn")
    return 0


if __name__ == "__main__":
    sys.exit(main())
