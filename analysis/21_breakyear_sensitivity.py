# -*- coding: utf-8 -*-
"""
21 — Kırılma-yılı duyarlılığı: 2015 çukuru tabanı belirlediğinde ne değişir?  (v4 §4.5'in "zorunlu" testi)

Soru: Türkiye'nin 2018–2025 sapması, 2015 çukurundan ölçüldüğü için mi büyük görünüyor?
Dört varyant, aynı donör havuzu ve aynı ön dönem verisiyle:
  A  "2013 kırılması"  : ön 2003–2012, sonrası 2015–2025 (2015 sonrası dönemde; Faz 2–3 manşeti)
  B  "2015 kırılması"  : ön 2003–2015, sonrası 2018–2025 (2015 ön dönemde; SDiD manşeti buna yakın)
  C  "2015 DIŞARIDA"   : ön 2003–2012, sonrası 2018–2025; 2015 sütunu matristen tümüyle atılır
  D  "sürekli trend"   : A'nın açıkları, ön dönem doğrusal trendi sonrasına uzatılıp çıkarılarak (trend-düzeltmeli)
Tahminciler: (1) ortalamadan arındırılmış sentetik kontrol (simpleks ağırlık; 17'deki Python SC = R Synth),
             (2) sentetik DiD (16'daki uygulama; Arkhangelsky vd. 2021),
             (3) 2012-tabanlı basit DiD: (Y_TUR,t − Y_TUR,2012) − donör ortalaması(Y_t − Y_2012).
Çıkarım: placebo-in-space (her donör sırayla tedavi edilmiş sayılır); p = (#{|τ_j| ≥ |τ_TUR|} + 1)/(N0 + 1).
Havuzlar: stable_all_oecd (manşet), stable_plus_ambiguous_oecd, all_participants — `_panel_matrix.build_matrix` ile aynı kurallar.
Çıktılar: data/derived/breakyear/{breakyear_sensitivity.csv, summary.json, breakyear_table.md};
          analysis/figures/v4_sekil3_kirilma_yili.png
Yazan: Claude Fable 5.1 (kod), 2026-09-20. Denetim: bekliyor (Opus 4.8).
"""
from __future__ import annotations

import importlib
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from _panel_matrix import build_matrix  # noqa: E402

m16 = importlib.import_module("16_synthetic_did")
m17 = importlib.import_module("17_matrix_completion_conformal")
sdid, sc_weights_demeaned = m16.sdid, m17.sc_weights_demeaned

ROOT = HERE.parent
OUT = ROOT / "data" / "derived" / "breakyear"
OUT.mkdir(parents=True, exist_ok=True)
FIG = ROOT / "analysis" / "figures"
POOLS = ["stable_all_oecd", "stable_plus_ambiguous_oecd", "all_participants"]
OUTCOMES = ["math", "reading", "science"]
VARIANTS = {
    "A_2013_kirilma_2015_sonrasi": dict(pre_end=2012, post=[2015, 2018, 2022, 2025], drop2015=False),
    "B_2015_kirilma_2015_on_donemde": dict(pre_end=2015, post=[2018, 2022, 2025], drop2015=False),
    "C_2015_disarida": dict(pre_end=2012, post=[2018, 2022, 2025], drop2015=True),
}


def sc_gaps(y1: np.ndarray, Y0: np.ndarray, fit_idx: list[int]) -> tuple[np.ndarray, np.ndarray, float]:
    """Ortalamadan arındırılmış SC: açık serisi (tüm sütunlar), ağırlıklar, ön dönem RMSPE."""
    w = sc_weights_demeaned(y1, Y0, fit_idx)
    y1d = y1 - y1[fit_idx].mean()
    Y0d = Y0 - Y0[:, fit_idx].mean(axis=1, keepdims=True)
    gap = y1d - w @ Y0d
    rmspe = float(np.sqrt((gap[fit_idx] ** 2).mean()))
    return gap, w, rmspe


def placebo_p(stat_tr: float, stats_pl: np.ndarray) -> float:
    return (int((np.abs(stats_pl) >= abs(stat_tr)).sum()) + 1) / (len(stats_pl) + 1)


def did_2012(y1: np.ndarray, Y0: np.ndarray, cycles: list[int], post: list[int]) -> dict:
    i12 = cycles.index(2012)
    return {t: float((y1[cycles.index(t)] - y1[i12]) - (Y0[:, cycles.index(t)] - Y0[:, i12]).mean()) for t in post}


rows = []
for pool in POOLS:
    for oc in OUTCOMES:
        mat_full = build_matrix(oc, pool)
        for vname, v in VARIANTS.items():
            mat = mat_full.drop(columns=[2015]) if v["drop2015"] else mat_full
            cycles = list(mat.columns)
            pre = [c for c in cycles if c <= v["pre_end"] and c not in v["post"]]
            post = v["post"]
            fit_idx = [cycles.index(c) for c in pre]
            post_idx = [cycles.index(c) for c in post]
            Y = mat.to_numpy(float)
            y1, Y0 = Y[0], Y[1:]
            N0 = Y0.shape[0]
            # (1) SC
            gap, w, rmspe = sc_gaps(y1, Y0, fit_idx)
            sc_post = {c: float(gap[cycles.index(c)]) for c in post}
            sc_mean = float(np.mean(list(sc_post.values())))
            pl = []
            for j in range(N0):
                g_j, _, _ = sc_gaps(Y0[j], np.delete(Y0, j, axis=0), fit_idx)
                pl.append(float(g_j[post_idx].mean()))
            sc_p = placebo_p(sc_mean, np.array(pl))
            # (D) trend-düzeltmeli SC (yalnız A ve C anlamlı: ön dönem trendi sonrasına uzatılır)
            X = np.array(pre, float)
            b1, b0 = np.polyfit(X, gap[fit_idx], 1)
            trend_post = {c: float(gap[cycles.index(c)] - (b0 + b1 * c)) for c in post}
            trend_mean = float(np.mean(list(trend_post.values())))
            pl_tr = []
            for j in range(N0):
                g_j, _, _ = sc_gaps(Y0[j], np.delete(Y0, j, axis=0), fit_idx)
                bb1, bb0 = np.polyfit(X, g_j[fit_idx], 1)
                pl_tr.append(float(np.mean([g_j[cycles.index(c)] - (bb0 + bb1 * c) for c in post])))
            trend_p = placebo_p(trend_mean, np.array(pl_tr))
            # (2) SDiD
            T0 = len(pre)
            assert T0 == cycles.index(post[0]), (vname, cycles, pre, post)
            r = sdid(y1, Y0, T0)
            pl_sdid = m16.placebo(Y0, T0)
            sdid_p = placebo_p(r["tau"], pl_sdid)
            sdid_post = {c: float(g) for c, g in zip(post, r["per_year"])}
            # (3) 2012-tabanlı DiD
            d12 = did_2012(y1, Y0, cycles, post)
            pl_d = []
            for j in range(N0):
                dd = did_2012(Y0[j], np.delete(Y0, j, axis=0), cycles, post)
                pl_d.append(float(np.mean(list(dd.values()))))
            d12_mean = float(np.mean(list(d12.values())))
            d12_p = placebo_p(d12_mean, np.array(pl_d))
            top = sorted(zip(mat.index[1:], w), key=lambda t: -t[1])[:3]
            base = dict(variant=vname, outcome=oc, pool=pool, n_donors=N0, pre=" ".join(map(str, pre)), post=" ".join(map(str, post)),
                        sc_pre_rmspe=round(rmspe, 2), sc_top_weights=" ".join(f"{k}={x:.2f}" for k, x in top))
            for est, gp, mean, p in [("SC_demeaned", sc_post, sc_mean, sc_p), ("SC_trend_adjusted", trend_post, trend_mean, trend_p),
                                     ("SDiD", sdid_post, float(r["tau"]), sdid_p), ("DiD_2012base", d12, d12_mean, d12_p)]:
                rows.append({**base, "estimator": est, "gap_2015": round(gp.get(2015, np.nan), 1), "gap_2018": round(gp.get(2018, np.nan), 1),
                             "gap_2022": round(gp.get(2022, np.nan), 1), "gap_2025": round(gp.get(2025, np.nan), 1),
                             "post_mean": round(mean, 1), "p_placebo": round(p, 3),
                             "sdid_time_weights": " ".join(f"{c}:{x:.2f}" for c, x in zip(cycles[:T0], r["lam"])) if est == "SDiD" else "",
                             "pre_trend_slope_per_cycle": round(b1 * 3, 2) if est == "SC_trend_adjusted" else ""})
            print(f"[{pool} {oc} {vname}] N0={N0} SC post-mean {sc_mean:+.1f} (p {sc_p:.2f}) | trend-adj {trend_mean:+.1f} (p {trend_p:.2f}) | SDiD {r['tau']:+.1f} (p {sdid_p:.2f}) | DiD2012 {d12_mean:+.1f} (p {d12_p:.2f}) | 2025: SC {sc_post[2025]:+.1f} SDiD {sdid_post[2025]:+.1f} DiD {d12[2025]:+.1f}")

df = pd.DataFrame(rows)
df.to_csv(OUT / "breakyear_sensitivity.csv", index=False, encoding="utf-8-sig")

# ---- özet: manşet havuz, 2025 açığı ve sonrası ortalaması, varyant × tahminci ----
head = df[df.pool == "stable_all_oecd"]
summary = {}
for oc in OUTCOMES:
    summary[oc] = {}
    for vname in VARIANTS:
        sub = head[(head.outcome == oc) & (head.variant == vname)]
        summary[oc][vname] = {r_.estimator: dict(gap_2025=r_.gap_2025, gap_2018=r_.gap_2018, gap_2022=r_.gap_2022, post_mean=r_.post_mean,
                                                  p=r_.p_placebo, n_donors=int(r_.n_donors)) for r_ in sub.itertuples()}
# 2015-in vs 2015-out farkı (SC, 2025 açığı)
delta = {oc: dict(A_sc_2025=summary[oc]["A_2013_kirilma_2015_sonrasi"]["SC_demeaned"]["gap_2025"],
                  C_sc_2025=summary[oc]["C_2015_disarida"]["SC_demeaned"]["gap_2025"],
                  A_sdid_2025=summary[oc]["A_2013_kirilma_2015_sonrasi"]["SDiD"]["gap_2025"],
                  C_sdid_2025=summary[oc]["C_2015_disarida"]["SDiD"]["gap_2025"],
                  B_sdid_tau=summary[oc]["B_2015_kirilma_2015_on_donemde"]["SDiD"]["post_mean"],
                  C_sdid_tau=summary[oc]["C_2015_disarida"]["SDiD"]["post_mean"]) for oc in OUTCOMES}
json.dump(dict(headline_pool="stable_all_oecd", summary=summary, delta_2015_in_vs_out=delta,
               notes=["p = placebo-in-space sıra-p, post-mean istatistiği üzerinde; N0 küçük (5–8) → erişilebilir en küçük p 1/(N0+1).",
                      "C varyantında 2015 sütunu matristen atıldı; donör kümesi A ile aynı (tam seri şartı 2015 dahil uygulandı)."]),
          open(OUT / "summary.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1, default=float)

# ---- markdown tablo (manşet havuz) ----
lab = {"A_2013_kirilma_2015_sonrasi": "A · 2013 kırılması (2015 sonrasında)", "B_2015_kirilma_2015_on_donemde": "B · 2015 kırılması (2015 ön dönemde)",
       "C_2015_disarida": "C · 2015 dışarıda"}
est_lab = {"SC_demeaned": "SC (arındırılmış)", "SC_trend_adjusted": "SC, trend-düzeltmeli", "SDiD": "SDiD", "DiD_2012base": "DiD, 2012 tabanı"}
md = ["| Varyant | Tahminci | Alan | N0 | 2015 | 2018 | 2022 | 2025 | Sonrası ort. | p (plasebo) |", "|---|---|---|---:|---:|---:|---:|---:|---:|---:|"]
for vname in VARIANTS:
    for est in est_lab:
        for oc in OUTCOMES:
            r_ = head[(head.variant == vname) & (head.estimator == est) & (head.outcome == oc)].iloc[0]
            f = lambda x: "–" if pd.isna(x) else f"{x:+.1f}".replace(".", ",").replace("-", "−")
            md.append(f"| {lab[vname]} | {est_lab[est]} | {oc} | {r_.n_donors} | {f(r_.gap_2015)} | {f(r_.gap_2018)} | {f(r_.gap_2022)} | {f(r_.gap_2025)} | {f(r_.post_mean)} | {r_.p_placebo:.2f} |".replace("0.", "0,") if False else
                      f"| {lab[vname]} | {est_lab[est]} | {oc} | {r_.n_donors} | {f(r_.gap_2015)} | {f(r_.gap_2018)} | {f(r_.gap_2022)} | {f(r_.gap_2025)} | {f(r_.post_mean)} | {str(round(r_.p_placebo, 2)).replace('.', ',')} |")
(OUT / "breakyear_table.md").write_text("\n".join(md) + "\n", encoding="utf-8")

# ---- Şekil 3: manşet havuz, SC yıl bazlı açıklar, varyant A vs C vs trend-düzeltmeli ----
fig, axes = plt.subplots(1, 3, figsize=(15, 5), sharey=True)
names = {"math": "Matematik", "reading": "Okuma", "science": "Fen"}
styles = [("A_2013_kirilma_2015_sonrasi", "SC_demeaned", "#8b2c1e", "o", "A · SC, 2015 sonrası dönemde (2018–25'te C ile çakışır)", "--", 2.6),
          ("C_2015_disarida", "SC_demeaned", "#1a1a1a", "s", "C · SC, 2015 dışarıda", "-", 1.8),
          ("C_2015_disarida", "SC_trend_adjusted", "#6b6b6b", "^", "C · SC, trend-düzeltmeli", "-", 1.8),
          ("C_2015_disarida", "SDiD", "#2f6f9f", "D", "C · SDiD", "-", 1.8)]
for ax, oc in zip(axes, OUTCOMES):
    for vname, est, col, mk, label, ls, lw in styles:
        r_ = head[(head.variant == vname) & (head.estimator == est) & (head.outcome == oc)].iloc[0]
        ys = [r_.gap_2015, r_.gap_2018, r_.gap_2022, r_.gap_2025]
        xs = [2015, 2018, 2022, 2025]
        pts = [(x, y) for x, y in zip(xs, ys) if not pd.isna(y)]
        ax.plot([p[0] for p in pts], [p[1] for p in pts], color=col, marker=mk, lw=lw, ms=7, label=label, ls=ls, alpha=0.9 if ls == "-" else 0.7)
    ax.axhline(0, color="#bbb", lw=1)
    ax.set_title(names[oc], fontsize=13)
    ax.set_xticks([2015, 2018, 2022, 2025])
    ax.grid(axis="y", color="#e5e5e5")
    ax.spines[["top", "right"]].set_visible(False)
axes[0].set_ylabel("Türkiye − sentetik kontrol (puan)")
axes[0].legend(fontsize=9, loc="upper left", frameon=False)
fig.suptitle("Şekil 3 · Kırılma yılı duyarlılığı: 2015 çukuru tabanı belirlediğinde açık ne kadar değişir? (stabil OECD havuzu)",
             x=0.01, ha="left", fontsize=14, family="DejaVu Serif")
fig.text(0.01, 0.012, "Ön dönem 2003–2012 (fen 2006–2012). A: 2015 sonrası dönemde. C: 2015 sütunu atılmış; trend-düzeltmeli = ön dönem doğrusal trendi sonrasına uzatılıp çıkarılmış. "
         "Betik: analysis/21_breakyear_sensitivity.py [E21].", fontsize=9, color="#555")
fig.tight_layout(rect=(0, 0.05, 1, 0.94))
fig.savefig(FIG / "v4_sekil3_kirilma_yili.png", dpi=120)
plt.close(fig)
print("DONE breakyear")
