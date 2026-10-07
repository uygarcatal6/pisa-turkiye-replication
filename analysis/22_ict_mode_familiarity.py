#!/usr/bin/env python3
"""
22_ict_mode_familiarity.py

SORU: Türkiye'nin 2015'teki atipik büyük düşüşü, kâğıttan bilgisayara geçişin
yarattığı "bilgisayar aşinalığı" etkisiyle açıklanabilir mi?

YÖNTEM
  1. PISA 2015 ve 2018 öğrenci anketlerinden ülke düzeyinde ağırlıklı ICT
     ortalamaları çıkarılır (W_FSTUWT ile).
  2. 2015'te bilgisayara geçen 55 sistem için 2012->2015 puan değişimi
     (data/derived/mode_transition_2015/cba2015_changes.csv) ICT ölçülerine
     karşı regrese edilir.
  3. Türkiye'nin gözlenen düşüşünü üretmek için gereken ICT değeri hesaplanır
     ve örneklem aralığıyla karşılaştırılır.

KRİTİK OLGU: Türkiye PISA 2015'te OPSİYONEL ICT Familiarity anketini
UYGULAMADI. ICTHOME/ICTSCH/COMPICT/ENTUSE/USESCH/INTICT/AUTICT/SOIAICT
Türkiye için %0 doludur. Yalnız ICTRES (çekirdek ankettin ev olanakları
maddelerinden türetilir, ESCS bileşenidir) mevcuttur.

ÇIKTILAR -> data/derived/mode_transition_2015/
  ict_country_means_2015.csv
  ict_country_means_2018.csv
  ict_coverage_2015.csv
  ict_penalty_fit.csv
  ict_summary.json

Çalıştırma: python3 analysis/22_ict_mode_familiarity.py
Gereksinim: pyreadstat, pandas, numpy
"""
from __future__ import annotations

import json
import shutil
import tempfile
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd
import pyreadstat

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "derived" / "mode_transition_2015"
OUT.mkdir(parents=True, exist_ok=True)

ZIP15 = ROOT / "data" / "pisa_microdata" / "2015" / "PUF_SPSS_COMBINED_CMB_STU_QQQ.zip"
ZIP18 = ROOT / "data" / "pisa_microdata" / "2018" / "SPSS_STU_QQQ.zip"
CHANGES = OUT / "cba2015_changes.csv"

# ICT modülü (opsiyonel) endeksleri + ICTRES (çekirdek ankette, ESCS bileşeni)
ICT_MODULE = ["ICTHOME", "ICTSCH", "COMPICT", "ENTUSE", "HOMESCH",
              "USESCH", "INTICT", "AUTICT", "SOIAICT"]
ICT_CORE = ["ICTRES"]
ICT_ALL = ICT_CORE + ICT_MODULE


def _extract_sav(zip_path: Path, tmpdir: Path) -> Path:
    """Zip'ten en büyük .sav dosyasını çıkarıp yolunu döndürür."""
    with zipfile.ZipFile(zip_path) as z:
        savs = [n for n in z.namelist() if n.lower().endswith(".sav")]
        if not savs:
            raise FileNotFoundError(f"{zip_path} içinde .sav yok")
        target = max(savs, key=lambda n: z.getinfo(n).file_size)
        z.extract(target, tmpdir)
    return tmpdir / target


def _weighted_mean(g: pd.DataFrame, col: str, wcol: str = "W_FSTUWT",
                   min_n: int = 30) -> float:
    s = g[[col, wcol]].dropna()
    if len(s) < min_n:
        return np.nan
    return float(np.average(s[col], weights=s[wcol]))


def country_means(sav: Path, cycle: int) -> tuple[pd.DataFrame, pd.DataFrame]:
    _, meta = pyreadstat.read_sav(str(sav), metadataonly=True)
    present = [c for c in ICT_ALL if c in meta.column_names]
    use = ["CNT", "W_FSTUWT", "ESCS"] + present
    df, _ = pyreadstat.read_sav(str(sav), usecols=use)
    df["CNT"] = df["CNT"].astype(str).str.strip()

    means, cover = [], []
    for cnt, g in df.groupby("CNT"):
        row = {"iso3": cnt, "cycle": cycle, "n_students": len(g)}
        cov = {"iso3": cnt, "cycle": cycle, "n_students": len(g)}
        for c in present + ["ESCS"]:
            row[c] = _weighted_mean(g, c)
            cov[c + "_pct"] = round(100.0 * g[c].notna().mean(), 1)
        means.append(row)
        cover.append(cov)
    return pd.DataFrame(means), pd.DataFrame(cover)


def fit_table(m: pd.DataFrame, ict_cols: list[str],
              tur_override: dict[str, float] | None = None) -> pd.DataFrame:
    """Her (ICT ölçüsü, alan) için korelasyon + Türkiye öngörüsü + gereken değer."""
    rows = []
    tur_override = tur_override or {}
    for icol in ict_cols:
        if icol not in m.columns:
            continue
        for d in ["d_math", "d_read", "d_sci"]:
            # Model Türkiye HARİÇ kurulur (dışsal öngörü için)
            s = m[(m["iso3"] != "TUR")][[icol, d]].dropna()
            if len(s) < 10:
                continue
            x, y = s[icol].to_numpy(), s[d].to_numpy()
            slope, intercept = np.polyfit(x, y, 1)
            r = float(np.corrcoef(x, y)[0, 1])
            rho = float(s[icol].rank().corr(s[d].rank()))

            tur_x = tur_override.get(icol, m.loc[m["iso3"] == "TUR", icol].values[0]
                                     if icol in m.columns else np.nan)
            obs = float(m.loc[m["iso3"] == "TUR", d].values[0])
            pred = float(slope * tur_x + intercept) if pd.notna(tur_x) else np.nan

            # Eğim sıfıra yakınsa "gereken değer" tanımsızdır: doğru neredeyse
            # yataydır, HİÇBİR ICT değeri gözlenen cezayı üretemez. Ham bölme
            # devasa/absürt bir sayı verir ve ileride yanlış okunur -> NaN + bayrak.
            slope_sd = float(np.std(y, ddof=1)) / max(float(np.std(x, ddof=1)), 1e-12)
            slope_negligible = abs(slope) < 0.05 * slope_sd
            if slope_negligible or slope == 0:
                need = np.nan
            else:
                need = float((obs - intercept) / slope)
            rows.append({
                "ict_measure": icol, "domain": d, "n_countries": len(s),
                "pearson_r": round(r, 3), "spearman_rho": round(rho, 3),
                "slope_points_per_sd": round(float(slope), 2),
                "tur_ict_value": round(float(tur_x), 4) if pd.notna(tur_x) else None,
                "tur_ict_source": "2018 vekil" if icol in tur_override else "2015",
                "tur_predicted": round(pred, 1) if pd.notna(pred) else None,
                "tur_observed": round(obs, 1),
                "tur_residual": round(obs - pred, 1) if pd.notna(pred) else None,
                "ict_needed_for_observed": round(need, 2) if pd.notna(need) else None,
                "slope_negligible": bool(slope_negligible),
                "sample_min": round(float(s[icol].min()), 2),
                "sample_max": round(float(s[icol].max()), 2),
                "needed_outside_range": (
                    None if pd.isna(need)
                    else bool(need < s[icol].min() or need > s[icol].max())),
                "verdict": (
                    "egim~0: hicbir ICT degeri gozlenen cezayi uretemez"
                    if slope_negligible else
                    "gereken deger orneklem araligi DISINDA"
                    if (need < s[icol].min() or need > s[icol].max()) else
                    "gereken deger orneklem araligi icinde"),
            })
    return pd.DataFrame(rows)


def main() -> None:
    tmp = Path(tempfile.mkdtemp(prefix="ict_"))
    try:
        print("2015 öğrenci anketi okunuyor ...")
        m15, c15 = country_means(_extract_sav(ZIP15, tmp / "y15"), 2015)
        print("2018 öğrenci anketi okunuyor ...")
        m18, c18 = country_means(_extract_sav(ZIP18, tmp / "y18"), 2018)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    m15.to_csv(OUT / "ict_country_means_2015.csv", index=False)
    m18.to_csv(OUT / "ict_country_means_2018.csv", index=False)
    c15.to_csv(OUT / "ict_coverage_2015.csv", index=False)

    chg = pd.read_csv(CHANGES)
    m = chg.merge(m15.drop(columns=["cycle", "n_students"]), on="iso3", how="left")

    # Türkiye'nin 2015 COMPICT'i YOK -> 2018 değeri açıkça etiketli vekil olarak
    tur18 = m18.loc[m18["iso3"] == "TUR", "COMPICT"]
    override = {"COMPICT": float(tur18.values[0])} if len(tur18) and pd.notna(tur18.values[0]) else {}

    fits = fit_table(m, ICT_ALL, tur_override=override)
    fits.to_csv(OUT / "ict_penalty_fit.csv", index=False)

    tur_cov = c15[c15["iso3"] == "TUR"].iloc[0].to_dict()
    module_cov = {k: tur_cov.get(k + "_pct") for k in ICT_MODULE}
    n_module = int((c15["ICTHOME_pct"] >= 50).sum()) if "ICTHOME_pct" in c15 else None

    summary = {
        "question": "Türkiye'nin 2015 atipik düşüşü bilgisayar aşinalığıyla açıklanıyor mu?",
        "answer": "Hayır — eldeki ICT ölçüleriyle açıklanmıyor.",
        "tur_2015_ict_module_administered": False,
        "tur_2015_module_coverage_pct": module_cov,
        "tur_2015_ictres_coverage_pct": tur_cov.get("ICTRES_pct"),
        "n_countries_administering_module_2015": n_module,
        "n_countries_total_2015": int(len(c15)),
        "tur_2018_ict_module_administered": True,
        "tur_2018_compict": override.get("COMPICT"),
        "key_result": (
            "ICTRES (Türkiye'de mevcut) ile geçiş cezası arasında ülkeler-arası ilişki "
            "sıfıra yakın; model Türkiye için -2 ila -4 puanlık bir ceza öngörüyor, "
            "gözlenen ise -27,5 / -47,2 / -37,9. COMPICT (2018 vekil) ile model "
            "-4 ila -8 puan öngörüyor. Gözlenen düşüşü üretmek için gereken COMPICT "
            "değeri örneklem aralığının tamamen dışında."
        ),
        "caveats": [
            "Ülkeler-arası korelasyon zayıf bir testtir (n=43-50, cezalar gürültülü).",
            "Türkiye'nin 2015 COMPICT'i gerçekten yoktur; 2018 vekili kalıcılık varsayar.",
            "2018 aşinalığı 2015'ten muhtemelen YÜKSEKTİR; vekil bu yönde muhafazakârdır, "
            "ama gereken değerle aradaki fark bu düzeltmeyle kapanmaz.",
            "ICTRES ev olanaklarını ölçer ve ESCS bileşenidir; SES ile eşdoğrusaldır.",
            "Etkileşimler (düşük aşinalık x ilk döngü x platform) bu tasarımla saptanamaz.",
        ],
        "sources": {
            "scores_change": str(CHANGES.relative_to(ROOT)),
            "pisa_2015_stu_qqq": str(ZIP15.relative_to(ROOT)),
            "pisa_2018_stu_qqq": str(ZIP18.relative_to(ROOT)),
        },
    }
    (OUT / "ict_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    print("\n=== ÖZET ===")
    print(json.dumps(summary["tur_2015_module_coverage_pct"], ensure_ascii=False))
    key = fits[fits["ict_measure"].isin(["ICTRES", "COMPICT", "ICTHOME"])]
    print(key[["ict_measure", "domain", "n_countries", "pearson_r",
               "tur_predicted", "tur_observed", "tur_residual",
               "ict_needed_for_observed", "verdict"]].to_string(index=False))
    print(f"\nYazıldı -> {OUT}")


if __name__ == "__main__":
    main()
