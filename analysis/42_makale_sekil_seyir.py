# -*- coding: utf-8 -*-
"""
42_makale_sekil_seyir.py — makale Şekil 1 (final numarası): Türkiye'nin PISA kaydı 2003–2025.

Neden: makale, açıklamaya çalıştığı olguyu (2015 sonrası yükseliş, 2015 çukuru, 2003–2012 kapsam genişlemesi) yalnız
düz yazıyla veriyordu; okur yükselişi, çukuru ve kimin test edildiğini aynı eksende göremiyordu. Bu şekil yeni analiz
değildir: yalnız doğrulanmış kayıttaki (analysis_panel.csv, ci3_2003_techreport.json) değerleri çizer; hiçbir sayı
elle yazılmaz. Hazırlık kaydı etiketleri §3.4'teki kaynaklı cümlelerin kısaltmasıdır (sayı içermez).
Çizilen: (a) Türkiye'nin matematik/okuma/fen ortalaması, %95 aralık (±1,96 SH), 2025 trend tablolarının verdiği OECD
ortalaması (2012, 2015, 2025); 2012–2015 arası kurumsal kırılma bandı; 2015 bilgisayar geçişi; hazırlık kaydı.
(b) Coverage Index 3 (2003: PISA 2003 Teknik Raporu Tablo 12.1; 2006–2025: sonuç ciltlerinin Ek A2 tabloları) ve genel
dışlama oranı (2006–2022; 2025 taslak değeri OECD'nin kendi bulgusuyla önceki döngülerle karşılaştırılamaz, çizilmez).
Girdi: data/derived/analysis_panel.csv; data/derived/ontrend/ci3_2003_techreport.json
Çıktı: analysis/figures/makale_sekil0_seyir.{png,pdf} (300 dpi); data/derived/placebo_backbone/makale_sekil0_veri.csv
Kullanım: python analysis/42_makale_sekil_seyir.py      Yazan: Claude Opus 5.5 (Cowork), 2026-09-25.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
DER = ROOT / "data" / "derived"
FIG = ROOT / "analysis" / "figures"
OUTD = DER / "placebo_backbone"
INK, BODY, HAIR = "#1A1A1A", "#6E6C67", "#D7D5CF"
DOM = {"math": ("Mathematics", "#2F5D8A", "o"), "reading": ("Reading", "#8A3324", "s"),
       "science": ("Science", "#2E7D5B", "D")}
# §3.4 ve §5.5'teki kaynaklı hazırlık kaydının kısaltması (MEB 2017 s. 10; 2019b s. 23; 2023 s. 33; DÖGM 2025).
PREP = {2015: "administrators\nbriefed", 2018: "administrators\nbriefed", 2022: "+ subject\nteachers",
        2025: "teachers of\nsampled schools"}


def load() -> pd.DataFrame:
    p = pd.read_csv(DER / "analysis_panel.csv", encoding="utf-8-sig")
    tur = p[p.iso3 == "TUR"].sort_values("cycle")
    oecd = p[p.iso3 == "OECD"].set_index("cycle")
    ci3_2003 = json.load(open(DER / "ontrend" / "ci3_2003_techreport.json", encoding="utf-8"))["TUR"]
    rows = []
    for _, r in tur.iterrows():
        cy = int(r.cycle)
        rec = {"cycle": cy}
        for d in DOM:
            rec[f"tur_{d}"] = r[f"{d}_mean"]
            rec[f"tur_{d}_se"] = r[f"{d}_se"]
            rec[f"oecd_{d}"] = oecd.loc[cy, f"{d}_mean"] if cy in oecd.index else np.nan
        rec["coverage_index3"] = ci3_2003 if cy == 2003 else r.coverage_index3
        rec["coverage_source"] = "OECD 2005 Table 12.1" if cy == 2003 else "results volume Annex A2"
        rec["overall_exclusion_pct"] = r.overall_exclusion_pct if cy != 2025 else np.nan  # 2025: karşılaştırılamaz
        rows.append(rec)
    v = pd.DataFrame(rows)
    assert list(v.cycle) == [2003, 2006, 2009, 2012, 2015, 2018, 2022, 2025], v.cycle.tolist()
    assert v.coverage_index3.notna().all()
    return v


def main() -> int:
    v = load()
    OUTD.mkdir(parents=True, exist_ok=True)
    tmp = OUTD / "makale_sekil0_veri.csv.tmp"
    v.to_csv(tmp, index=False, encoding="utf-8")
    os.replace(tmp, OUTD / "makale_sekil0_veri.csv")

    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 9})
    fig, (ax, bx) = plt.subplots(2, 1, figsize=(8.4, 7.0), sharex=True, gridspec_kw={"height_ratios": [2.3, 1]})
    x = v.cycle.values

    # (a) Ortalamalar
    ax.axvspan(2012.35, 2014.65, color=HAIR, alpha=0.55, lw=0, zorder=0)
    ax.text(2013.5, 507, "institutional\nbreak", ha="center", va="top", fontsize=7.4, color=BODY, style="italic")
    for d, (nm, col, mk) in DOM.items():
        y, se = v[f"tur_{d}"].values, v[f"tur_{d}_se"].values
        ok = np.isfinite(y)
        ax.errorbar(x[ok], y[ok], yerr=1.96 * se[ok], fmt="-", color=col, lw=1.6, elinewidth=1.0, capsize=2.5,
                    marker=mk, ms=5.5, label=f"Türkiye, {nm.lower()}", zorder=3)
        o = v[f"oecd_{d}"].values
        ok2 = np.isfinite(o)
        dx = {"math": -0.35, "reading": 0.0, "science": 0.35}[d]   # 2015'te okuma (488,5) ve fen (488,8) üst üste biniyordu
        ax.scatter(x[ok2] + dx, o[ok2], marker=mk, s=34, facecolors="white", edgecolors=col, linewidths=1.3, zorder=4)
    ax.scatter([], [], marker="o", s=34, facecolors="white", edgecolors=BODY, linewidths=1.3,
               label="OECD average (hollow; 2012, 2015, 2025)")
    y15 = np.nanmin([v.loc[v.cycle == 2015, f"tur_{d}"].iloc[0] for d in DOM])
    ax.annotate("2015: move to\ncomputer-based testing", (2015, y15 - 6), xytext=(2016.2, 392),
                fontsize=7.2, color=BODY, ha="left", arrowprops=dict(arrowstyle="-", color=BODY, lw=0.7))
    ax.text(2003.0, 381, "Preparation recorded\nby the ministry:", fontsize=7.2, color=INK, ha="left", va="center",
            fontweight="bold")
    for cy, lab in PREP.items():
        ax.text(cy, 381, lab, fontsize=6.8, color=INK, ha="center", va="center",
                bbox=dict(boxstyle="round,pad=0.25", fc="#F3F1EC", ec=HAIR, lw=0.6))
    ax.set_ylim(368, 510)
    ax.set_ylabel("Mean score (PISA points)")
    ax.spines[["top", "right"]].set_visible(False)
    ax.legend(loc="lower left", bbox_to_anchor=(0.0, 1.01), fontsize=7.2, frameon=False, ncol=4,
              handletextpad=0.4, columnspacing=1.2)
    ax.text(-0.075, 1.0, "(a)", transform=ax.transAxes, fontsize=10, fontweight="bold", va="top")

    # (b) Kapsam ve dışlama
    ex = v.overall_exclusion_pct.values
    bx2 = bx.twinx()
    okx = np.isfinite(ex)
    bx2.bar(x[okx], ex[okx], width=1.1, color=HAIR, edgecolor=BODY, lw=0.6, zorder=1, label="Overall exclusion (%, right axis)")
    for xi, e in zip(x[okx], ex[okx]):
        bx2.text(xi, e + 0.25, f"{e:.1f}", ha="center", va="bottom", fontsize=6.8, color=BODY)
    bx2.text(2025, 0.35, "2025: not\ncomparable", ha="center", va="bottom", fontsize=6.6, color=BODY, style="italic")
    bx2.set_ylim(0, 12)
    bx2.set_ylabel("Exclusion (%)", color=BODY)
    bx2.tick_params(axis="y", colors=BODY)
    bx.set_zorder(bx2.get_zorder() + 1)
    bx.patch.set_visible(False)
    c = v.coverage_index3.values
    bx.plot(x, c, "-o", color=INK, lw=1.5, ms=4.5, label="Coverage Index 3 (left axis)", zorder=3)
    for xi, ci in zip(x, c):
        bx.text(xi, ci + 0.07, f"{ci:.2f}", ha="center", va="bottom", fontsize=6.8, color=INK)
    bx.set_ylim(0, 1.15)
    bx.set_ylabel("Share of 15-year-olds\nrepresented")
    bx.spines[["top"]].set_visible(False)
    bx2.spines[["top"]].set_visible(False)
    h1, l1 = bx.get_legend_handles_labels()
    h2, l2 = bx2.get_legend_handles_labels()
    bx.legend(h1 + h2, l1 + l2, loc="upper left", fontsize=7.2, frameon=False, ncol=2)
    bx.set_xticks(x)
    bx.set_xticklabels([str(c_) for c_ in x])
    bx.set_xlim(2001.8, 2026.4)
    bx.text(-0.075, 1.0, "(b)", transform=bx.transAxes, fontsize=10, fontweight="bold", va="top")

    fig.tight_layout(h_pad=0.8)
    FIG.mkdir(parents=True, exist_ok=True)
    for ext in ("png", "pdf"):
        t = FIG / f"makale_sekil0_seyir.tmp.{ext}"
        fig.savefig(t, dpi=300, bbox_inches="tight")
        os.replace(t, FIG / f"makale_sekil0_seyir.{ext}")
    print(v.round(3).to_string(index=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
