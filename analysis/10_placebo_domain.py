#!/usr/bin/env python3
"""Koşullu plasebo-alan testi (PISA 2025).

Soru: Türkiye'nin hesaplamalı problem çözme (CPS) puanı, çekirdek alan düzeyine
koşullu olarak beklenenin ne kadar altında? Ham fark (çekirdek − CPS) düşük
kapasiteli sistemlerde mekanik olarak büyük olduğu için, CPS'i çekirdeğe
regresyon edip Türkiye'nin artığına (residual) bakıyoruz.

Şişme hipotezi: hazırlık yapılabilen çekirdek alanlar şişer, hazırlık yapılamayan
yeni alan şişmez → Türkiye'nin artığı negatif ve dağılımın alt ucunda olmalı.

Çıktılar:
  data/derived/mechanisms/placebo_conditional_2025.csv
  data/derived/mechanisms/placebo_conditional_summary.json
  analysis/figures/mech_placebo_conditional.png
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "derived" / "mechanisms"
FIG = ROOT / "analysis" / "figures"
OUT.mkdir(parents=True, exist_ok=True)
FIG.mkdir(parents=True, exist_ok=True)

FOCUS = ["TUR", "GEO", "HUN", "SWE"]


def ols(x: np.ndarray, y: np.ndarray, deg: int = 1):
    """Basit OLS; katsayılar, artıklar, R2 ve katsayı standart hataları."""
    X = np.vander(x, deg + 1, increasing=True)          # [1, x, x^2, ...]
    beta, *_ = np.linalg.lstsq(X, y, rcond=None)
    fit = X @ beta
    resid = y - fit
    n, k = len(y), X.shape[1]
    sigma2 = float(resid @ resid) / max(n - k, 1)
    xtx_inv = np.linalg.pinv(X.T @ X)
    se = np.sqrt(np.diag(xtx_inv) * sigma2)
    ss_tot = float(((y - y.mean()) ** 2).sum())
    r2 = 1 - float(resid @ resid) / ss_tot if ss_tot > 0 else np.nan
    return beta, se, fit, resid, r2, np.sqrt(sigma2)


def main() -> int:
    panel = pd.read_csv(ROOT / "data/derived/analysis_panel.csv")
    p25 = panel[panel.cycle == 2025].copy()
    need = ["math_mean", "reading_mean", "science_mean", "cps2025_mean"]
    p25 = p25.dropna(subset=need)
    p25["core"] = p25[["math_mean", "reading_mean", "science_mean"]].mean(axis=1)
    oecd_raw = p25["oecd_member"]
    if oecd_raw.dtype == object:
        p25["oecd"] = oecd_raw.astype(str).str.strip().str.lower().isin(["1", "1.0", "true", "yes", "evet"])
    else:
        p25["oecd"] = pd.to_numeric(oecd_raw, errors="coerce").fillna(0) > 0
    # ülke-üstü toplamları (OECD ortalaması vb.) ve alt-ulusal birimleri ayıkla
    p25 = p25[~p25["iso3"].isna()]
    p25 = p25[p25["iso3"].str.len() == 3]
    print(f"2025'te dört alanı da olan birim: {len(p25)} (OECD üyesi {int(p25.oecd.sum())})")

    rows, summary = [], {}
    for scope in ["all", "oecd"]:
        d = p25 if scope == "all" else p25[p25.oecd]
        x, y = d["core"].to_numpy(float), d["cps2025_mean"].to_numpy(float)
        for deg, name in [(1, "linear"), (2, "quadratic")]:
            if len(d) <= deg + 2:
                continue
            beta, se, fit, resid, r2, rmse = ols(x, y, deg)
            tmp = d[["iso3", "country_name", "core", "cps2025_mean", "oecd"]].copy()
            tmp["scope"], tmp["spec"] = scope, name
            tmp["cps_pred"] = fit
            tmp["residual"] = resid
            tmp["resid_sd"] = resid / rmse if rmse else np.nan
            tmp["pctile"] = tmp["residual"].rank(pct=True) * 100
            tmp["rank_low"] = tmp["residual"].rank(method="min")   # 1 = en negatif artık
            rows.append(tmp)
            key = f"{scope}_{name}"
            summary[key] = {
                "n": int(len(d)),
                "slope": round(float(beta[1]), 3),
                "slope_se": round(float(se[1]), 3),
                "r2": round(float(r2), 3),
                "rmse": round(float(rmse), 1),
            }
            for iso in FOCUS:
                r = tmp[tmp.iso3 == iso]
                if r.empty:
                    continue
                r = r.iloc[0]
                # leave-one-out: odak ülke uyuma dahil edilmeden tahmin (denetim önerisi — daha az muhafazakâr)
                m_loo = d.iso3 != iso
                b_loo, *_ = ols(d.loc[m_loo, "core"].to_numpy(float), d.loc[m_loo, "cps2025_mean"].to_numpy(float), deg)
                pred_loo = float(np.polyval(b_loo[::-1], float(r.core)))
                summary[key][iso] = {
                    "core": round(float(r.core), 1),
                    "cps": round(float(r.cps2025_mean), 1),
                    "cps_predicted": round(float(r.cps_pred), 1),
                    "residual": round(float(r.residual), 1),
                    "residual_in_sd": round(float(r.resid_sd), 2),
                    "residual_leave_one_out": round(float(r.cps2025_mean) - pred_loo, 1),
                    "rank_from_bottom": f"{int(r.rank_low)}/{len(tmp)}",
                    "percentile": round(float(r.pctile), 1),
                }
            foc = ", ".join(
                f"{iso}: artık {summary[key][iso]['residual']:+.1f} ({summary[key][iso]['rank_from_bottom']})"
                for iso in FOCUS if iso in summary[key]
            )
            print(f"[{scope}/{name}] n={len(d)} eğim={beta[1]:.3f} R2={r2:.3f} RMSE={rmse:.1f} | {foc}")

    res = pd.concat(rows, ignore_index=True)
    res.to_csv(OUT / "placebo_conditional_2025.csv", index=False, encoding="utf-8-sig")

    # ---- şekil: tüm katılımcılar, doğrusal uyum ----
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        d = res[(res.scope == "all") & (res.spec == "linear")].sort_values("core")
        fig, ax = plt.subplots(figsize=(8.5, 6))
        ax.scatter(d.core, d.cps2025_mean, s=22, c="grey", alpha=0.6, label="katılımcılar")
        ax.plot(d.core, d.cps_pred, color="black", lw=1.2, label="OLS uyum")
        for iso, col in zip(FOCUS, ["firebrick", "darkorange", "steelblue", "seagreen"]):  # zip keser: FOCUS uzunluğu kadar renk şart
            r = d[d.iso3 == iso]
            if r.empty:
                continue
            ax.scatter(r.core, r.cps2025_mean, s=70, c=col, zorder=5, label=iso)
            ax.annotate(f"{iso} ({float(r.residual.iloc[0]):+.0f})",
                        (float(r.core.iloc[0]), float(r.cps2025_mean.iloc[0])),
                        textcoords="offset points", xytext=(8, -12), color=col, fontsize=9)
        ax.set_xlabel("çekirdek alanlar 2025 (mat/okuma/fen ortalaması)")
        ax.set_ylabel("hesaplamalı problem çözme 2025")
        ax.set_title("Koşullu plasebo-alan testi: CPS ~ çekirdek (PISA 2025)")
        ax.legend(frameon=False, fontsize=9)
        ax.grid(alpha=0.3, linestyle="--")
        fig.tight_layout()
        fig.savefig(FIG / "mech_placebo_conditional.png", dpi=150)
        plt.close(fig)
        print(f"şekil: {FIG / 'mech_placebo_conditional.png'}")
    except Exception as exc:  # pragma: no cover
        print(f"şekil çizilemedi: {exc}")

    (OUT / "placebo_conditional_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=1), encoding="utf-8")
    print("DONE conditional placebo")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
