#!/usr/bin/env python3
"""Sentetik fark-farkı (SDiD) — Arkhangelsky, Athey, Hirshberg, Imbens & Wager (2021, AER) — Python uygulaması.

Neden Python: `synthdid` R paketi CRAN'da değil (yalnız GitHub, synth-inference/synthdid v0.0.9; kurulum
denemesi için bkz. RESULTS_PHASE4 §2); algoritma makalede kapalı biçimde tanımlı, burada birebir uygulanır ve Opus 4.8 denetimi makaleyle
karşılaştırır.

Algoritma (makale, Alg. 1; tek tedavi birimi N1=1):
  1. σ̂² = kontrol birimlerinin ön-dönem birinci farklarının varyansı;  ζ = (N1·T1)^{1/4} · σ̂.
  2. Birim ağırlıkları (ω0, ω): min_{ω0∈R, ω∈simpleks} Σ_{t≤T0} (ω0 + Σ_i ω_i Y_it − Y_{tr,t})² + ζ² T0 ‖ω‖²₂.
  3. Zaman ağırlıkları (λ0, λ): min_{λ0∈R, λ∈simpleks} Σ_{i∈kontrol} (λ0 + Σ_{t≤T0} λ_t Y_it − (1/T1)Σ_{t>T0} Y_it)².
     (Makalede zaman ağırlıkları düzenlileştirilmez; sayısal kararlılık için 1e-8 ridge eklenir.)
  4. τ̂ = (Ȳ_tr,post − Σ_t λ_t Y_tr,t) − Σ_i ω_i (Ȳ_i,post − Σ_t λ_t Y_it)   [ağırlıklı DiD; makale Denk. (1)'in
     tek-tedavi-birimli kapalı biçimi].
  5. Çıkarım: plasebo (makale Alg. 4): her kontrol birimi sırayla tedavi edilmiş sayılır, kalan kontrollerle
     τ̂_b hesaplanır; SE = sd(τ̂_b) (küçük N0'da tüm birimler kullanılır, rastgele örnekleme yok);
     ayrıca sıra-tabanlı p = #{|τ̂_b| ≥ |τ̂|}+1 / (N0+1).
Karşılaştırma: aynı ağırlıklarla "sadece ω" (SC-tipi, λ = post ortalaması ile ön-dönem düz) ve
"sadece λ" (DiD-tipi, ω düz) tahminleri de raporlanır (makale Tablo 1 mantığı).

Pencereler: (a) 'post2015': ön 2003/2006–2012, sonrası 2015–2025; (b) 'post2018' (RAPORDA MANŞET): ön …–2015,
sonrası 2018–2025 (zaman ağırlıkları 2015'i taban seçer). Plasebo SE = sd(ddof=1): makale/synthdid 1/B konvansiyonuna
göre ×1,07–1,12 daha büyük (muhafazakâr); denetim notu 2026-09-16.
Çıktı: data/derived/sdid/{sdid_results.csv, summary.json}
Yazan: Claude Fable 5.1, 2026-09-16.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.optimize import minimize

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _panel_matrix import build_matrix  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "derived" / "sdid"
OUT.mkdir(parents=True, exist_ok=True)
POOLS = ["stable_all_oecd", "stable_plus_ambiguous_oecd", "all_participants"]
OUTCOMES = ["math", "reading", "science"]
WINDOWS = {"post2015": [2015, 2018, 2022, 2025], "post2018": [2018, 2022, 2025]}


def simplex_ls(A: np.ndarray, y: np.ndarray, ridge: float) -> tuple[float, np.ndarray]:
    """min_{c, w∈simpleks} ‖c + A w − y‖² + ridge ‖w‖²; A: (m × k)."""
    k = A.shape[1]

    def obj(z):
        c, w = z[0], z[1:]
        r = c + A @ w - y
        return float(r @ r + ridge * (w @ w))

    z0 = np.concatenate([[0.0], np.full(k, 1.0 / k)])
    cons = ({"type": "eq", "fun": lambda z: z[1:].sum() - 1.0},)
    bounds = [(None, None)] + [(0.0, 1.0)] * k
    res = minimize(obj, z0, bounds=bounds, constraints=cons, method="SLSQP", options={"maxiter": 5000, "ftol": 1e-14})
    return float(res.x[0]), res.x[1:]


def sdid(Y_tr: np.ndarray, Y_co: np.ndarray, T0: int) -> dict:
    """Y_tr: (T,), Y_co: (N0, T). İlk T0 sütun ön dönem."""
    N0, T = Y_co.shape
    T1 = T - T0
    # 1. ζ
    d = np.diff(Y_co[:, :T0], axis=1)
    sigma = float(np.sqrt(((d - d.mean()) ** 2).sum() / (N0 * (T0 - 1))))
    zeta = (1 * T1) ** 0.25 * sigma
    # 2. birim ağırlıkları
    w0, omega = simplex_ls(Y_co[:, :T0].T, Y_tr[:T0], ridge=zeta ** 2 * T0)
    # 3. zaman ağırlıkları
    l0, lam = simplex_ls(Y_co[:, :T0], Y_co[:, T0:].mean(axis=1), ridge=1e-8)
    # 4. τ̂
    tr_post, tr_pre = Y_tr[T0:].mean(), float(lam @ Y_tr[:T0])
    co_post, co_pre = float(omega @ Y_co[:, T0:].mean(axis=1)), float(omega @ (Y_co[:, :T0] @ lam))
    tau = (tr_post - tr_pre) - (co_post - co_pre)
    # karşılaştırma tahmincileri
    lam_flat = np.full(T0, 1.0 / T0); om_flat = np.full(N0, 1.0 / N0)
    tau_sc = (tr_post - float(lam_flat @ Y_tr[:T0])) - (co_post - float(omega @ (Y_co[:, :T0] @ lam_flat)))
    tau_did = (tr_post - float(lam_flat @ Y_tr[:T0])) - (float(om_flat @ Y_co[:, T0:].mean(axis=1)) - float(om_flat @ (Y_co[:, :T0] @ lam_flat)))
    # yıl bazlı etki (aynı ω, λ): her sonrası döngü için
    per_year = [(float(Y_tr[t]) - tr_pre) - (float(omega @ Y_co[:, t]) - co_pre) for t in range(T0, T)]
    return dict(tau=tau, tau_sc_type=tau_sc, tau_did_type=tau_did, omega=omega, lam=lam, zeta=zeta, sigma=sigma,
                per_year=per_year, pre_fit_rmse=float(np.sqrt(((w0 + Y_co[:, :T0].T @ omega - Y_tr[:T0]) ** 2).mean())))


def placebo(Y_co: np.ndarray, T0: int) -> np.ndarray:
    taus = []
    for j in range(Y_co.shape[0]):
        rest = np.delete(Y_co, j, axis=0)
        taus.append(sdid(Y_co[j], rest, T0)["tau"])
    return np.array(taus)


def main() -> int:
    rows, summary = [], {}
    for win, post in WINDOWS.items():
        for pool in POOLS:
            for oc in OUTCOMES:
                mat = build_matrix(oc, pool)
                cycles = list(mat.columns)
                T0 = len([c for c in cycles if c not in post])
                Y = mat.to_numpy(float)
                r = sdid(Y[0], Y[1:], T0)
                pl = placebo(Y[1:], T0)
                se = float(pl.std(ddof=1)) if len(pl) > 1 else np.nan
                p_rank = (int((np.abs(pl) >= abs(r["tau"])).sum()) + 1) / (len(pl) + 1)
                top = sorted(zip(mat.index[1:], r["omega"]), key=lambda t: -t[1])[:4]
                row = dict(window=win, outcome=oc, pool=pool, n_donors=len(mat) - 1, T0=T0, T1=len(cycles) - T0,
                           tau_sdid=round(r["tau"], 2), se_placebo=round(se, 2), t_stat=round(r["tau"] / se, 2) if se else np.nan,
                           p_rank=round(p_rank, 3), tau_sc_type=round(r["tau_sc_type"], 2), tau_did_type=round(r["tau_did_type"], 2),
                           zeta=round(r["zeta"], 2), pre_fit_rmse=round(r["pre_fit_rmse"], 2),
                           per_year=" ".join(f"{c}:{v:+.1f}" for c, v in zip(post, r["per_year"])),
                           time_weights=" ".join(f"{c}:{v:.2f}" for c, v in zip(cycles[:T0], r["lam"])),
                           top_unit_weights=" ".join(f"{k}={v:.2f}" for k, v in top))
                rows.append(row); summary[f"{win}_{oc}_{pool}"] = row
                print(f"[{win} {oc} {pool}] N0={len(mat) - 1} τ̂={r['tau']:+.1f} (SE {se:.1f}, p_rank {p_rank:.2f}) | SC-tipi {r['tau_sc_type']:+.1f} DiD-tipi {r['tau_did_type']:+.1f} | {row['per_year']} | λ {row['time_weights']}")
    pd.DataFrame(rows).to_csv(OUT / "sdid_results.csv", index=False, encoding="utf-8-sig")
    (OUT / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=1, default=float), encoding="utf-8")
    print("DONE sdid")
    return 0


if __name__ == "__main__":
    sys.exit(main())
