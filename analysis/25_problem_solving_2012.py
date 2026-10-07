# -*- coding: utf-8 -*-
"""
25 — Kırılma ÖNCESİ plasebo-alan noktası: PISA 2012 yaratıcı problem çözme (koşullu test, 10/15 ile aynı tasarım).

Neden (20 Eyl 2026): plasebo-alan omurgası tek güçlü noktadan (2025) ibaretti; 2012 tedavi öncesi bir noktadır ve
diziyi "öncesi → sonrası"na çevirir. Türkiye'nin 2012 artığı sıfıra yakınsa paralel-trend kanıtı budur; 2012'de de belirgin
negatifse 2025 artığı şişmenin değil, Türkiye'nin sabit bir özelliğinin (ya da bilgisayar aşinalığının) işareti olabilir.
Sonuç ne çıkarsa yazılır.

Veri: mikroveri klasörde yok; ülke ortalamaları OECD (2014) PISA 2012 Results Volume V, Table V.A "Snapshot of performance
in problem solving" (s. 17; data/pisa/2012/9789264208070-en.pdf, content/dam PDF, indirildi 20 Eyl 2026, logs/manifest.csv)
çalışma anında PDF'ten ayrıştırılır (pdfplumber; yedek pdftotext) — elle yazılmaz. Çekirdek 2012 = panel mat/oku/fen ortalaması.
Katılım tablodan okunur (44 sistem: 28 OECD + 16 partner; Türkiye 454, Macaristan 459; Gürcistan PISA 2012'de yok).

MOD UYARISI (raporda zorunlu): 2012 problem çözme BİLGİSAYARDA, 2012 çekirdek KÂĞITTA uygulandı; 2015 ve 2025'te ikisi de
bilgisayarda. 2012 artığı dolayısıyla bir mod farkını da içerir; Türkiye'nin 2015 mod cezasının atipik ağırlığı (v4 §4.5)
negatif bir 2012 artığını bilgisayar aşinalığıyla da açıklayabilir. İki okuma da yazılır.

Yöntem: PS2012 ~ çekirdek 2012, {tüm, OECD (panel bayrağı = bugünkü üyelik, 10/15 ile aynı)} × {doğrusal, karesel};
artık, artık/RMSE, sıra, yüzdelik, leave-one-out (TUR, HUN). England (Birleşik Krallık) alt-ulusal → regresyon dışı;
Shanghai-China panelde yok → dışı.

Çıktı: data/derived/ps2012_published_means.csv; data/derived/mechanisms/placebo_conditional_2012ps.csv,
       placebo_conditional_2012ps_summary.json; analysis/figures/mech_placebo_conditional_2012ps.png. Etiket [E25].
Yazan: Claude Fable 5.1 (kod), 2026-09-20. Denetim: bekliyor (Opus 4.8).
"""
from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
PDF = ROOT / "data" / "pisa" / "2012" / "9789264208070-en.pdf"
PANEL = ROOT / "data" / "derived" / "analysis_panel.csv"
OUT = ROOT / "data" / "derived"
MECH = OUT / "mechanisms"
FIG = ROOT / "analysis" / "figures"
for d in (OUT, MECH, FIG):
    d.mkdir(parents=True, exist_ok=True)
FOCUS = ["TUR", "HUN", "GEO", "SWE"]
SOURCE = ("OECD (2014), PISA 2012 Results: Creative Problem Solving (Volume V), Table V.A 'Snapshot of performance in problem solving', p. 17; "
          "data/pisa/2012/9789264208070-en.pdf (content/dam, 1 Apr 2014; indirildi 2026-09-20)")
NAME2ISO = {"Singapore": "SGP", "Korea": "KOR", "Japan": "JPN", "Macao-China": "MAC", "Hong Kong-China": "HKG", "Shanghai-China": "QCN",
            "Chinese Taipei": "TWN", "Canada": "CAN", "Australia": "AUS", "Finland": "FIN", "England (United Kingdom)": "ENG", "Estonia": "EST",
            "France": "FRA", "Netherlands": "NLD", "Italy": "ITA", "Czech Republic": "CZE", "Germany": "DEU", "United States": "USA",
            "Belgium": "BEL", "Austria": "AUT", "Norway": "NOR", "Ireland": "IRL", "Denmark": "DNK", "Portugal": "PRT", "Sweden": "SWE",
            "Russian Federation": "RUS", "Slovak Republic": "SVK", "Poland": "POL", "Spain": "ESP", "Slovenia": "SVN", "Serbia": "SRB",
            "Croatia": "HRV", "Hungary": "HUN", "Turkey": "TUR", "Israel": "ISR", "Chile": "CHL", "Brazil": "BRA", "Malaysia": "MYS",
            "United Arab Emirates": "ARE", "Montenegro": "MNE", "Uruguay": "URY", "Bulgaria": "BGR", "Colombia": "COL", "Cyprus": "CYP"}
NOT_NATIONAL = {"ENG": "England ≠ Birleşik Krallık toplamı (panel çekirdeği UK); regresyon dışı", "QCN": "Shanghai-China panelde yok"}


def ols(x: np.ndarray, y: np.ndarray, deg: int = 1):
    X = np.vander(x, deg + 1, increasing=True)
    beta, *_ = np.linalg.lstsq(X, y, rcond=None)
    fit = X @ beta
    resid = y - fit
    n, k = len(y), X.shape[1]
    rmse = float(np.sqrt((resid @ resid) / max(n - k, 1)))
    ss_tot = float(((y - y.mean()) ** 2).sum())
    r2 = 1 - float(resid @ resid) / ss_tot if ss_tot > 0 else np.nan
    return beta, fit, resid, r2, rmse


def parse_table_va(pdf: Path) -> tuple[pd.DataFrame, int | None, str]:
    """Table V.A satırları: 'Ülke  <ort>  <%düşük>  <%üst>  <cinsiyet farkı>  <göreli performans> ...'; sayfa 16–19 taranır."""
    rx = re.compile(r"^\s*([A-Za-z][A-Za-z .()\-]*?[A-Za-z)])[0-9,]*\s{2,}(\d{3})\s+(\d+\.\d)\s+(\d+\.\d)\s+(-?\d+)\s+(-?\d+)")

    def harvest(text_by_page):
        rows, oecd = {}, None
        for pno, txt in text_by_page:
            for line in txt.splitlines():
                m = rx.match(line)
                if not m:
                    continue
                name = m.group(1).strip()
                if name == "OECD average":
                    oecd = oecd or int(m.group(2))
                    continue
                if name not in rows:
                    rows[name] = dict(name=name, mean=int(m.group(2)), share_low=float(m.group(3)), share_top=float(m.group(4)),
                                      gender_diff=int(m.group(5)), relative_perf=int(m.group(6)), page=pno)
        return rows, oecd

    pages = [16, 17, 18, 19]
    rows, oecd, how = {}, None, ""
    try:
        import pdfplumber
        with pdfplumber.open(str(pdf)) as doc:
            rows, oecd = harvest([(p, doc.pages[p - 1].extract_text(layout=True) or "") for p in pages if p <= len(doc.pages)])
        how = "pdfplumber(layout=True)"
    except Exception as exc:  # pragma: no cover
        how = f"pdfplumber başarısız: {exc}"
    if len(rows) < 40 and shutil.which("pdftotext"):
        texts = []
        for p in pages:
            out = subprocess.run(["pdftotext", "-layout", "-f", str(p), "-l", str(p), str(pdf), "-"], capture_output=True)
            texts.append((p, out.stdout.decode("utf-8", errors="replace")))
        rows, oecd = harvest(texts)
        how += " → pdftotext -layout"
    return pd.DataFrame(rows.values()), oecd, how


def main() -> int:
    if not PDF.exists():
        raise SystemExit(f"PDF yok: {PDF}")
    pub, oecd_avg, how = parse_table_va(PDF)
    pub["iso3"] = pub.name.map(NAME2ISO)
    unmapped = sorted(pub[pub.iso3.isna()].name)
    print(f"[Table V.A] {how}; {len(pub)} sistem ayrıştırıldı; OECD ortalaması {oecd_avg}; eşlenemeyen ad: {unmapped}")
    pub["note"] = pub.iso3.map(lambda i: NOT_NATIONAL.get(i, ""))
    pub.to_csv(OUT / "ps2012_published_means.csv", index=False, encoding="utf-8-sig")

    panel = pd.read_csv(PANEL)
    p12 = panel[panel.cycle == 2012][["iso3", "country_name", "math_mean", "reading_mean", "science_mean", "oecd_member", "asterisk_flag"]].copy()
    p12["core"] = p12[["math_mean", "reading_mean", "science_mean"]].mean(axis=1)
    p12["oecd"] = pd.to_numeric(p12.oecd_member, errors="coerce").fillna(0) > 0
    ct = pub[~pub.iso3.isin(NOT_NATIONAL)].merge(p12, on="iso3", how="left")
    unmatched = sorted(ct[ct.core.isna()].iso3.astype(str))
    ct["oecd"] = ct.oecd.fillna(False).astype(bool)
    d_all = ct.dropna(subset=["core"]).copy().rename(columns={"mean": "ps2012_mean_published"})
    print(f"regresyona giren: {len(d_all)} (panelde 2012 çekirdeği olmayan: {unmatched}); OECD bayrağı (bugünkü üyelik): {int(d_all.oecd.sum())}")

    def status12(iso: str) -> str:
        """Table V.A'da varsa katıldı; PISA 2012 panelinde hiç yoksa 'not in PISA 2012' (Gürcistan); panelde var ama tabloda yoksa 'absent'."""
        if (pub.iso3 == iso).any():
            return "participated"
        return "not in PISA 2012" if not (p12.iso3 == iso).any() else "absent"

    rows, summary = [], {
        "note": "PISA 2012 yaratıcı problem çözme (bilgisayarda; çekirdek 2012 kâğıtta). Ülke ortalamaları yayımlanmış Table V.A'dan (tam sayı); "
                "mikroveri yok. Türkiye ve Macaristan katıldı; Gürcistan PISA 2012'de yok. England ve Shanghai regresyon dışı.",
        "source": SOURCE, "parser": how, "n_parsed": int(len(pub)), "unmapped_names": unmapped, "oecd_average_published": oecd_avg,
        "n_in_regression": int(len(d_all)), "n_oecd_flag_current_membership": int(d_all.oecd.sum()), "not_in_panel_2012": unmatched,
        "focus_status": {iso: status12(iso) for iso in FOCUS},
        "published_focus": {i: int(pub.loc[pub.iso3 == i, "mean"].iloc[0]) for i in FOCUS if (pub.iso3 == i).any()},
        "mode_caveat": "2012 problem çözme bilgisayar tabanlı, 2012 çekirdek kâğıt tabanlı; 2015/2025'te ikisi de bilgisayarda. 2012 artığı mod farkını da içerir.",
    }
    for scope in ["all", "oecd"]:
        d = d_all if scope == "all" else d_all[d_all.oecd]
        x, y = d.core.to_numpy(float), d.ps2012_mean_published.to_numpy(float)
        for deg, name in [(1, "linear"), (2, "quadratic")]:
            beta, fit, resid, r2, rmse = ols(x, y, deg)
            tmp = d[["iso3", "country_name", "core", "ps2012_mean_published", "oecd", "asterisk_flag"]].copy()
            tmp["scope"], tmp["spec"] = scope, name
            tmp["ps_pred"], tmp["residual"] = fit, resid
            tmp["resid_sd"] = resid / rmse if rmse else np.nan
            tmp["rank_low"] = tmp.residual.rank(method="min")
            tmp["pctile"] = tmp.residual.rank(pct=True) * 100
            rows.append(tmp)
            key = f"{scope}_{name}"
            summary[key] = {"n": int(len(d)), "slope": round(float(beta[1]), 4), "r2": round(float(r2), 3), "rmse": round(float(rmse), 2)}
            for iso in FOCUS:
                r = tmp[tmp.iso3 == iso]
                if r.empty:
                    continue
                r = r.iloc[0]
                m_loo = d.iso3 != iso
                b_loo, *_ = ols(d.loc[m_loo, "core"].to_numpy(float), d.loc[m_loo, "ps2012_mean_published"].to_numpy(float), deg)
                pred_loo = float(np.polyval(b_loo[::-1], float(r.core)))
                summary[key][iso] = {"core_2012": round(float(r.core), 1), "ps2012": int(r.ps2012_mean_published),
                                     "ps_predicted": round(float(r.ps_pred), 1), "residual": round(float(r.residual), 1),
                                     "residual_in_sd": round(float(r.resid_sd), 2), "residual_leave_one_out": round(float(r.ps2012_mean_published) - pred_loo, 1),
                                     "rank_from_bottom": f"{int(r.rank_low)}/{len(tmp)}", "percentile": round(float(r.pctile), 1)}
            foc = ", ".join(f"{iso}: artık {summary[key][iso]['residual']:+.1f} ({summary[key][iso]['rank_from_bottom']})" for iso in FOCUS if iso in summary[key])
            print(f"[{scope}/{name}] n={len(d)} eğim={beta[1]:.4f} R2={r2:.3f} RMSE={rmse:.2f} | {foc}")
    res = pd.concat(rows, ignore_index=True)
    res.to_csv(MECH / "placebo_conditional_2012ps.csv", index=False, encoding="utf-8-sig")

    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        d = res[(res.scope == "all") & (res.spec == "linear")].sort_values("core")
        fig, ax = plt.subplots(figsize=(8.5, 6))
        ax.scatter(d.core, d.ps2012_mean_published, s=22, c="grey", alpha=0.6, label="katılımcılar (n=%d)" % len(d))
        ax.plot(d.core, d.ps_pred, color="black", lw=1.2, label="OLS uyum")
        for iso, col in [("TUR", "firebrick"), ("HUN", "steelblue")]:
            r = d[d.iso3 == iso]
            if r.empty:
                continue
            ax.scatter(r.core, r.ps2012_mean_published, s=70, c=col, zorder=5, label=iso)
            ax.annotate(f"{iso} ({float(r.residual.iloc[0]):+.0f})", (float(r.core.iloc[0]), float(r.ps2012_mean_published.iloc[0])),
                        textcoords="offset points", xytext=(8, -12), color=col, fontsize=9)
        ax.set_xlabel("çekirdek alanlar 2012 (mat/okuma/fen ortalaması; kâğıt)")
        ax.set_ylabel("yaratıcı problem çözme 2012 (yayımlanmış; bilgisayar)")
        ax.set_title("Koşullu plasebo-alan testi: PS 2012 ~ çekirdek (kırılma öncesi)")
        ax.legend(frameon=False, fontsize=9, loc="lower right")
        ax.grid(alpha=0.3, linestyle="--")
        fig.tight_layout()
        fig.savefig(FIG / "mech_placebo_conditional_2012ps.png", dpi=150)
        plt.close(fig)
    except Exception as exc:  # pragma: no cover
        print(f"şekil çizilemedi: {exc}")

    (MECH / "placebo_conditional_2012ps_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=1), encoding="utf-8")
    print("DONE PS 2012 placebo")
    return 0


if __name__ == "__main__":
    sys.exit(main())
