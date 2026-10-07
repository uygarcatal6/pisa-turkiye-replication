# -*- coding: utf-8 -*-
"""
61_makale1_figure1.py — Makale 1 Şekil 1: betik 39'un aynısı + 2015 ve 2025 için %95 aralık (betik 60, §0.15).
Betik 39 başka bir şeklin de kaynağı olduğu için değiştirilmedi; bu betik onun kopyasıdır.
Fark: lo95/hi95 2015 ve 2025'te data/derived/empirical_fixes/l1_level_intervals.csv'den (TUR, all · linear); çıktı adları;
TIFF (300 dpi, RGB, LZW; betik 41'in biçimi). 7 Eki 2026, CC (Opus 5.5).
--- betik 39 başlığı ---
39_backbone_figure.py — makale Şekil 1: plasebo-alan omurgası 2003–2025, 2003 noktası ve mod bilgisiyle.

Neden: v4 Şekil 5 (24_placebo_backbone.py) 2003'ü içermiyor ve 2012'yi yayımlanmış tamsayı ortalamalarla çiziyordu; makale
tablosu 2 ise 2003 ve 2012'yi mikroveriden veriyor ve mod eşleşmesini tasarım koşulu sayıyor. Bu betik Tablo 2 ile aynı
dosyalardan çizer; hiçbir sayı elle yazılmaz.
Çizilen: Türkiye'nin tüm-katılımcı doğrusal artığı (puan; birincil), 95% aralık (2003, 2012; ilişkili bootstrap), tüm
spesifikasyonlar boyunca aralık (2003 ve 2012'de 8, 2015 ve 2025'te 4 spesifikasyon), ±1 RMSE bandı (tüm/doğrusal uyum),
Macaristan/İsveç/Gürcistan'ın tüm/doğrusal artıkları; 2018 ve 2022 boşlukları; mod satırı (çekirdek / yenilikçi alan).
Girdi: data/derived/mechanisms/placebo_conditional_{2003ps_puf,2012ps_puf,2015cps,2025}.csv
Çıktı: analysis/figures/makale_sekil1_plasebo_omurgasi.{png,pdf}; data/derived/placebo_backbone/makale_sekil1_veri.csv
Kullanım: python analysis/39_backbone_figure.py      Yazan: Claude Opus 5.5 (Cowork), 2026-09-25.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
MECH = ROOT / "data" / "derived" / "mechanisms"
FIG = ROOT / "analysis" / "figures"
OUTD = ROOT / "data" / "derived" / "placebo_backbone"
INK, BODY, HAIR, ACCENT = "#1A1A1A", "#6E6C67", "#D7D5CF", "#8A3324"
CMP = {"HUN": ("Hungary", "^", "#2F5D8A"), "SWE": ("Sweden", "s", "#2E7D5B"), "GEO": ("Georgia", "D", "#B07D2B")}
MODE = {2003: "paper/paper", 2012: "paper/computer", 2015: "computer/computer",
        2018: "(no Türkiye score)", 2022: "(no Türkiye score)", 2025: "computer/computer"}
DOMAIN = {2003: "problem solving", 2012: "creative PS", 2015: "collaborative PS",
          2018: "global competence", 2022: "creative thinking", 2025: "computational PS"}
POS = {2003: 0, 2012: 1, 2015: 2, 2018: 3, 2022: 4, 2025: 5}  # eşit aralıklı kategorik eksen (yıllar arası boşluk etikette)


def load() -> dict[int, pd.DataFrame]:
    a = pd.read_csv(MECH / "placebo_conditional_2003ps_puf.csv", encoding="utf-8-sig")           # 8 spes. (2 çekirdek tanımı)
    b = pd.read_csv(MECH / "placebo_conditional_2012ps_puf.csv", encoding="utf-8-sig")           # 8 spes. (PUF + yayımlanmış çekirdek)
    c = pd.read_csv(MECH / "placebo_conditional_2015cps.csv", encoding="utf-8-sig")
    d = pd.read_csv(MECH / "placebo_conditional_2025.csv", encoding="utf-8-sig")
    a["primary"] = (a.core_def == "mat/oku/fen") & (a.scope == "all") & (a.spec == "linear")
    b["primary"] = (b.core_def == "PUF mat/oku/fen") & (b.scope == "all") & (b.spec == "linear")
    for x in (c, d):
        x["primary"] = (x.scope == "all") & (x.spec == "linear")
    l1 = pd.read_csv(ROOT / "data" / "derived" / "empirical_fixes" / "l1_level_intervals.csv")
    for cy, x in ((2015, c), (2025, d)):
        q = l1[(l1.year == cy) & (l1.scope == "all") & (l1.spec == "linear")].set_index("iso3")
        m = x.primary
        x.loc[m, "resid_lo95"] = x.loc[m, "iso3"].map(q.resid_lo95)
        x.loc[m, "resid_hi95"] = x.loc[m, "iso3"].map(q.resid_hi95)
        assert np.allclose(x.loc[m, "residual"].to_numpy(), x.loc[m, "iso3"].map(q.residual).to_numpy(), atol=1e-9)
    return {2003: a, 2012: b, 2015: c, 2025: d}


def main() -> int:
    data = load()
    rows = []
    for cy, d in data.items():
        t = d[d.iso3 == "TUR"]
        p = t[t.primary].iloc[0]
        rmse = float(p.residual / p.resid_sd)
        rec = {"cycle": cy, "iso3": "TUR", "residual": float(p.residual), "rmse_all_linear": rmse,
               "lo95": float(p.resid_lo95) if "resid_lo95" in t.columns else np.nan,
               "hi95": float(p.resid_hi95) if "resid_hi95" in t.columns else np.nan,
               "spec_min": float(t.residual.min()), "spec_max": float(t.residual.max()), "n_specs": int(len(t)),
               "rank_low": int(p.rank_low), "n": int(d[d.primary].shape[0])}
        rows.append(rec)
        for iso in CMP:
            q = d[(d.iso3 == iso) & d.primary]
            if len(q):
                rows.append({"cycle": cy, "iso3": iso, "residual": float(q.residual.iloc[0]),
                             "rank_low": int(q.rank_low.iloc[0]), "n": rec["n"]})
    v = pd.DataFrame(rows)
    tmp = OUTD / "makale1_sekil1_veri.csv.tmp"
    v.to_csv(tmp, index=False, encoding="utf-8")
    os.replace(tmp, OUTD / "makale1_sekil1_veri.csv")

    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 9})
    fig, ax = plt.subplots(figsize=(8.4, 4.8))
    xs = list(POS)
    ax.axhline(0, color=BODY, lw=0.8)
    ax.axvspan(POS[2012] - 0.45, POS[2012] + 0.45, color=HAIR, alpha=0.45, lw=0, zorder=0)
    tur = v[v.iso3 == "TUR"].set_index("cycle")
    for cy in tur.index:
        r, x = tur.loc[cy], POS[cy]
        ax.fill_between([x - 0.32, x + 0.32], -r.rmse_all_linear, r.rmse_all_linear, color=HAIR, alpha=0.55, lw=0, zorder=1)
        ax.plot([x, x], [r.spec_min, r.spec_max], color=ACCENT, lw=7, alpha=0.25, solid_capstyle="butt", zorder=2)
        if np.isfinite(r.lo95):
            ax.errorbar(x, r.residual, yerr=[[r.residual - r.lo95], [r.hi95 - r.residual]], fmt="none", ecolor=ACCENT,
                        elinewidth=1.2, capsize=3, zorder=4)
        ax.plot(x, r.residual, "o", color=ACCENT, ms=7, zorder=5)
        ax.annotate(f"{r.residual:.1f}\n{int(r.rank_low)}/{int(r.n)}", (x, r.residual), xytext=(-9, 0),
                    textcoords="offset points", ha="right", va="center", fontsize=7.5, color=ACCENT)
    for k, (iso, (nm, mk, col)) in enumerate(CMP.items()):
        s = v[v.iso3 == iso]
        ax.scatter(s.cycle.map(POS) + 0.14 + 0.09 * k, s.residual, marker=mk, s=24, color=col, zorder=3, label=nm)
    for cy in (2018, 2022):
        ax.text(POS[cy], 1.5, "no observation\nfor Türkiye", ha="center", va="bottom", fontsize=7.2, color=BODY, style="italic")
    ax.set_xlim(-0.6, 5.6)
    ax.set_ylim(-42, 27)
    ax.set_xticks([POS[x] for x in xs])
    ax.set_xticklabels([f"{x}\n{DOMAIN[x]}\n{MODE[x]}" for x in xs], fontsize=7.4)
    ax.set_ylabel("Innovative-domain residual (PISA points)")
    ax.spines[["top", "right"]].set_visible(False)
    ax.plot([], [], "o", color=ACCENT, label="Türkiye (all participants, linear)")
    ax.plot([], [], color=ACCENT, lw=7, alpha=0.25, label="Türkiye, range over specifications")
    ax.fill_between([], [], [], color=HAIR, alpha=0.55, label="±1 RMSE of the cross-country fit")
    ax.legend(loc="upper left", fontsize=7.2, frameon=False, ncol=2)
    # Açıklama (etiketler, bıyıklar, gölgeli sütun, mod satırı) makaledeki şekil altyazısında; şekle gömülmez.
    FIG.mkdir(parents=True, exist_ok=True)
    for ext in ("png", "pdf"):
        tmp = FIG / f"makale1_sekil1.tmp.{ext}"
        fig.savefig(tmp, dpi=300, bbox_inches="tight")
        os.replace(tmp, FIG / f"makale1_sekil1.{ext}")
    from PIL import Image  # betik 41'in TIFF biçimi: RGB, LZW, 300 dpi
    im = Image.open(FIG / "makale1_sekil1.png")
    bg = Image.new("RGB", im.size, "white"); bg.paste(im, mask=im.split()[3] if im.mode == "RGBA" else None)
    tmp = FIG / "makale1_sekil1.tmp.tif"
    bg.save(tmp, format="TIFF", compression="tiff_lzw", dpi=(300, 300))
    os.replace(tmp, FIG / "makale1_sekil1.tif")
    print(v.round(2).to_string(index=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
