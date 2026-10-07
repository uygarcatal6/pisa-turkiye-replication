#!/usr/bin/env python3
"""Panel-tamamlama ve konformal çıkarım: sentetik kontrole iki bağımsız tamamlayıcı.

Neden: "Frontier Causal Inference Architectures" memosunun (Gemini, 2026-09-16) panel bölümü,
tek tedavi birimli ülke panelleri için sentetik kontrolün yanına (i) nükleer-norm matris tamamlama
(Athey, Bayati, Doudchenko, Imbens & Khosravi 2021, JASA) ve (ii) konformal/permütasyon çıkarımı
(Chernozhukov, Wüthrich & Zhu 2021, JASA) koymayı öneriyor. İkisi de dengeli ülke×döngü matrisi
ister; bizde var (`_panel_matrix.py`).

(A) Matris tamamlama (MC-NNM, soft-impute): Türkiye'nin tedavi sonrası hücreleri (2015–2025) eksik
    sayılır; düşük-ranklı L + birim etkisi + zaman etkisi modeli, nükleer-norm cezasıyla, yalnız
    gözlenen hücrelerden tahmin edilir; λ, donör hücrelerinin rastgele maskelendiği çapraz doğrulamayla
    seçilir. Karşı-olgusal = tahmin; fark = gözlenen − tahmin. Plasebo: her donör sırayla "tedavi
    edilmiş" sayılır → fark dağılımı → sıra/p.
(B) Konformal çıkarım (CWZ 2021): H0 "tedavi sonrası etki = 0" altında sentetik kontrol tüm döngülerle
    yeniden uydurulur (ortalamadan arındırılmış simpleks ağırlıklar, 03_synth ile aynı model);
    kalıntılar hareketli-blok permütasyonuyla karıştırılır; istatistik = sonrası kalıntıların
    mutlak ortalaması → permütasyon p-değeri. Yalnız 8 (fen 7) döngü olduğu için p-değeri
    ızgarası kaba (1/8 adım); bu bir sınırlılık, sonuç tablosunda yazılır.
Ayrıca (C): sentetik kontrol ağırlıklarının Python NNLS ile yeniden üretimi (R Synth ile
    karşılaştırma için; fark 03_synth path dosyalarıyla raporlanır).

Çıktı: data/derived/mc_conformal/{mc_results.csv, conformal_results.csv, summary.json}
Yazan: Claude Fable 5.1, 2026-09-16. Denetim: Opus 4.8 (sayı + kod).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.optimize import minimize

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _panel_matrix import build_matrix, POST  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "derived" / "mc_conformal"
OUT.mkdir(parents=True, exist_ok=True)
RNG = np.random.default_rng(20260916)

POOLS = ["stable_all_oecd", "stable_plus_ambiguous_oecd", "all_participants"]
OUTCOMES = ["math", "reading", "science"]


# ----------------------------------------------------------------------------- (A) MC-NNM
def soft_impute(Y: np.ndarray, mask: np.ndarray, lam: float, iters: int = 500, tol: float = 1e-7):
    """Y ≈ L + a 1' + 1 b'; gözlenen hücreler (mask=1) üzerinde kareler + λ‖L‖_* (Athey et al. 2021, alg. 1).
    Eksik hücreler her iterasyonda mevcut tahminle doldurulur; L'ye tekil-değer eşikleme uygulanır."""
    n, T = Y.shape
    L = np.zeros((n, T)); a = np.zeros(n); b = np.zeros(T)
    prev = np.inf
    for _ in range(iters):
        fit = L + a[:, None] + b[None, :]
        Z = np.where(mask, Y, fit)
        # sabit etkiler (gözlenen hücreler üzerinden, sırayla)
        R = Z - L
        a = (R - b[None, :]).mean(axis=1)
        b = (R - a[:, None]).mean(axis=0)
        # düşük-ranklı bileşen: tekil değer eşikleme
        U, s, Vt = np.linalg.svd(Z - a[:, None] - b[None, :], full_matrices=False)
        s = np.maximum(s - lam, 0.0)
        L_new = (U * s) @ Vt
        obj = 0.5 * ((mask * (Y - (L_new + a[:, None] + b[None, :])) ** 2).sum()) + lam * s.sum()
        if abs(prev - obj) < tol * max(1.0, abs(prev)):
            L = L_new; break
        L, prev = L_new, obj
    return L + a[:, None] + b[None, :], int(np.sum(s > 0))


def choose_lambda(Y: np.ndarray, mask: np.ndarray, grid: np.ndarray, k: int = 5, frac: float = 0.15):
    """Monte Carlo çapraz doğrulama: k tekrar; her tekrarda gözlenen DONÖR hücrelerinin %frac'ı rastgele maskelenir
    (tekrarlar arasında örtüşme olabilir; ayrık k-katlı bölme DEĞİL), λ başına ortalama kare hata."""
    obs = np.argwhere(mask)
    obs = obs[obs[:, 0] != 0]                       # tedavi birimi (satır 0) CV'ye girmez
    errs = np.zeros(len(grid))
    for _ in range(k):
        hold = obs[RNG.choice(len(obs), size=max(1, int(frac * len(obs))), replace=False)]
        m2 = mask.copy(); m2[hold[:, 0], hold[:, 1]] = False
        for j, lam in enumerate(grid):
            fit, _ = soft_impute(Y, m2, lam)
            errs[j] += ((Y[hold[:, 0], hold[:, 1]] - fit[hold[:, 0], hold[:, 1]]) ** 2).mean()
    return float(grid[int(np.argmin(errs))]), errs / k


def mc_one(mat: pd.DataFrame, treated_row: int, post_cols: list[int], lam: float | None = None):
    Y = mat.to_numpy(float)
    mask = np.ones_like(Y, dtype=bool)
    mask[treated_row, post_cols] = False
    if lam is None:
        smax = np.linalg.svd(Y - Y.mean(), compute_uv=False)[0]
        grid = smax * np.logspace(-3, 0, 12)
        lam, _ = choose_lambda(Y, mask, grid)
    fit, rank = soft_impute(Y, mask, lam)
    gap = Y[treated_row, post_cols] - fit[treated_row, post_cols]
    pre_cols = [j for j in range(Y.shape[1]) if j not in post_cols]
    pre_rmse = float(np.sqrt(((Y[treated_row, pre_cols] - fit[treated_row, pre_cols]) ** 2).mean()))
    return dict(lam=lam, rank=rank, gap=gap, pre_rmse=pre_rmse, fit=fit[treated_row])


# ----------------------------------------------------------------------------- (B) SC + konformal
def sc_weights_demeaned(y1: np.ndarray, Y0: np.ndarray, fit_idx: list[int]) -> np.ndarray:
    """Ortalamadan arındırılmış simpleks ağırlıklar: min Σ_{t∈fit}(ỹ1t − Σ_j w_j ỹ0jt)², w≥0, Σw=1."""
    y1d = y1[fit_idx] - y1[fit_idx].mean()
    Y0d = Y0[:, fit_idx] - Y0[:, fit_idx].mean(axis=1, keepdims=True)
    J = Y0.shape[0]
    obj = lambda w: float(((y1d - w @ Y0d) ** 2).sum())
    cons = ({"type": "eq", "fun": lambda w: w.sum() - 1.0},)
    res = minimize(obj, np.full(J, 1.0 / J), bounds=[(0, 1)] * J, constraints=cons, method="SLSQP",
                   options={"maxiter": 2000, "ftol": 1e-12})
    return res.x


def demeaned_gap(y1, Y0, w, fit_idx):
    """Ön-dönem ortalamaları düşülmüş fark (03_synth'in 'demeaned' spesifikasyonu)."""
    y1d = y1 - y1[fit_idx].mean()
    y0d = w @ (Y0 - Y0[:, fit_idx].mean(axis=1, keepdims=True))
    return y1d - y0d, y1d, y0d


def conformal_p(y1: np.ndarray, Y0: np.ndarray, post_idx: list[int], tau0: float = 0.0):
    """CWZ (2021) hareketli-blok permütasyon testi. H0: post etki = tau0 (sabit).
    Tüm döngülerle uydur (sonrası çıktıdan tau0 düşülerek), kalıntı vektörünü blok-kaydır, istatistik
    S = ortalama |û_post|. p = #{S_perm ≥ S_obs}/T."""
    T = len(y1)
    y_adj = y1.astype(float).copy(); y_adj[post_idx] -= tau0
    all_idx = list(range(T))
    w = sc_weights_demeaned(y_adj, Y0, all_idx)
    u, _, _ = demeaned_gap(y_adj, Y0, w, all_idx)
    q = len(post_idx)
    S = lambda vec: float(np.abs(vec).mean())
    s_obs = S(u[post_idx])
    stats = []
    for shift in range(T):
        u_perm = np.roll(u, shift)
        stats.append(S(u_perm[-q:]))         # sonrası konumdaki q blok (post en sonda)
    p = float(np.mean([s >= s_obs - 1e-12 for s in stats]))
    return p, s_obs, w


def main() -> int:
    mc_rows, cf_rows, summary = [], [], {}
    for pool in POOLS:
        for oc in OUTCOMES:
            mat = build_matrix(oc, pool)
            cycles = list(mat.columns)
            post_cols = [cycles.index(c) for c in POST if c in cycles]
            pre_idx = [j for j in range(len(cycles)) if j not in post_cols]
            key = f"{oc}_{pool}"
            n_don = len(mat) - 1
            # --- (A) MC-NNM, tedavi = TUR; plasebo: her donör
            r = mc_one(mat, 0, post_cols)
            plac = []
            for j in range(1, len(mat)):
                rj = mc_one(mat, j, post_cols, lam=r["lam"])
                plac.append(rj["gap"].mean())
            plac = np.array(plac)
            gap_mean = float(r["gap"].mean())
            rank_mc = int((plac >= gap_mean).sum()) + 1
            p_mc = rank_mc / (n_don + 1)
            for c, g, f in zip([cycles[j] for j in post_cols], r["gap"], r["fit"][post_cols]):
                mc_rows.append(dict(outcome=oc, pool=pool, n_donors=n_don, cycle=c, observed=float(mat.iloc[0][c]),
                                    mc_counterfactual=float(f), gap=float(g), lam=r["lam"], rank=r["rank"], pre_rmse=r["pre_rmse"]))
            # --- (B) SC (Python NNLS, demeaned) + konformal p; (C) R Synth karşılaştırması
            y1 = mat.iloc[0].to_numpy(float); Y0 = mat.iloc[1:].to_numpy(float)
            w_pre = sc_weights_demeaned(y1, Y0, pre_idx)
            gap_sc, _, _ = demeaned_gap(y1, Y0, w_pre, pre_idx)
            p_cf, s_obs, _ = conformal_p(y1, Y0, post_cols, 0.0)
            # konformal güven aralığı: tau0 ızgarasında H0 reddedilmeyen aralık (p ≥ 0.2 → %80).
            # Üç sonrası-pencere: (i) 2015–2025 sabit etki, (ii) yalnız 2025 (q=1), (iii) 2018–2025 sabit etki.
            grid = np.arange(-40, 201, 2.0)
            def ci80_for(post_idx):
                pv = np.array([conformal_p(y1, Y0, post_idx, t)[0] for t in grid])
                ok = pv >= 0.20
                return (float(grid[ok].min()), float(grid[ok].max())) if ok.any() else (np.nan, np.nan)
            ci80 = ci80_for(post_cols)
            ci80_2025 = ci80_for(post_cols[-1:])
            ci80_18_25 = ci80_for(post_cols[-3:])
            p_2025 = conformal_p(y1, Y0, post_cols[-1:], 0.0)[0]
            p_18_25 = conformal_p(y1, Y0, post_cols[-3:], 0.0)[0]
            top = sorted(zip(mat.index[1:], w_pre), key=lambda t: -t[1])[:4]
            cf_rows.append(dict(outcome=oc, pool=pool, n_donors=n_don, T=len(cycles),
                                sc_post_gap_mean=float(gap_sc[post_cols].mean()),
                                sc_gap_2025=float(gap_sc[post_cols[-1]]),
                                sc_pre_rmspe=float(np.sqrt((gap_sc[pre_idx] ** 2).mean())),
                                conformal_p_tau0=p_cf, conformal_stat=s_obs,
                                conformal_p_2025only=p_2025, conformal_p_2018_25=p_18_25,
                                ci80_lo=ci80[0], ci80_hi=ci80[1],
                                ci80_2025only_lo=ci80_2025[0], ci80_2025only_hi=ci80_2025[1],
                                ci80_2018_25_lo=ci80_18_25[0], ci80_2018_25_hi=ci80_18_25[1],
                                p_grid_step=round(1 / len(cycles), 3),
                                mc_post_gap_mean=gap_mean, mc_gap_2025=float(r["gap"][-1]), mc_rank=f"{rank_mc}/{n_don + 1}", mc_p=round(p_mc, 3),
                                mc_lambda=round(r["lam"], 2), mc_rank_L=r["rank"], mc_pre_rmse=round(r["pre_rmse"], 2),
                                top_weights=" ".join(f"{k}={v:.2f}" for k, v in top)))
            print(f"[{key}] donör={n_don} | SC post-ort {gap_sc[post_cols].mean():+.1f} (2025 {gap_sc[post_cols[-1]]:+.1f}) "
                  f"konformal p={p_cf:.3f} CI80={ci80} 2025:{ci80_2025} 18-25:{ci80_18_25} | MC post-ort {gap_mean:+.1f} (2025 {r['gap'][-1]:+.1f}) "
                  f"sıra {rank_mc}/{n_don + 1} λ={r['lam']:.1f} rank={r['rank']} pre-RMSE={r['pre_rmse']:.1f}")
            summary[key] = cf_rows[-1]
    pd.DataFrame(mc_rows).to_csv(OUT / "mc_results.csv", index=False, encoding="utf-8-sig")
    pd.DataFrame(cf_rows).to_csv(OUT / "conformal_results.csv", index=False, encoding="utf-8-sig")
    (OUT / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=1, default=float), encoding="utf-8")

    # (C) R Synth (03_synth) ile karşılaştırma: aynı havuz/aynı spesifikasyon → 2025 farkı
    comp = []
    for oc in OUTCOMES:
        for case, pool in [("TUR", "stable_all_oecd"), ("TUR_robust_ambig", "stable_plus_ambiguous_oecd")]:
            cands = sorted((ROOT / "data/derived/synth").glob(f"{case}_{oc}_*_demeaned_path.csv"))  # 'stable_all' < 'stable_clean' (alfabetik)
            if not cands:
                continue
            path = pd.read_csv(cands[0])
            r_gap = float(path.loc[path.cycle == 2025, "gap"].iloc[0])
            py_gap = summary[f"{oc}_{pool}"]["sc_gap_2025"]
            comp.append(dict(outcome=oc, pool=pool, r_synth_gap_2025=r_gap, python_sc_gap_2025=py_gap, diff=py_gap - r_gap))
    pd.DataFrame(comp).to_csv(OUT / "r_vs_python_sc.csv", index=False, encoding="utf-8-sig")
    print(pd.DataFrame(comp).round(2).to_string(index=False))
    print("DONE mc_conformal")
    return 0


if __name__ == "__main__":
    sys.exit(main())
