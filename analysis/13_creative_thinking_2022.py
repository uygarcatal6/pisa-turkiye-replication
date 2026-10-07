#!/usr/bin/env python3
"""İkinci plasebo alan: PISA 2022 yaratıcı düşünme (creative thinking).

Sonuç önden: Türkiye ve Gürcistan PISA 2022 yaratıcı düşünme alanına KATILMADI
(Annex Table III.B1.2.1'de satırları 'm'; mikroveride CNT listesinde yoklar). Bu yüzden
yaratıcı düşünme Türkiye için ikinci plasebo-alan sonucu OLAMAZ. Betik yine de:
  1. Yayımlanmış ağırlıklı ülke ortalamalarını (Table III.B1.2.1, opbe7a.xlsx) okur,
  2. Mikroveriden (CY08MSP_CRT_COG.SAV, PV1CRTH_NC…PV10CRTH_NC) ağırlıksız ortalamaları
     hesaplayıp yayımlanmış değerlerle çapraz-kontrol eder (isim/ölçek doğrulaması),
  3. Katılımcı sistemler için koşullu testi (CT ~ çekirdek 2022) çalıştırır; Macaristan
     (üçüncü odak ülke) raporlanır, TUR/GEO "katılmadı" olarak işaretlenir.

Veri notları (Opus 5 indirme ajanı, 2026-09-16, doğrulandı):
  - PV adları PV1CRTH_NC…PV10CRTH_NC ('Number Correct' etiketine rağmen 0–60 Volume III
    raporlama ölçeğinde; gözlenen aralık 0,10–59,30).
  - CRT dosyasında W_FSTUWT YOK; ağırlıklı hesap için STU_QQQ ile CNT+CNTSCHID+CNTSTUID
    üzerinden birleştirme gerekir. Burada ağırlıklı değer yayımlanmış tablodan alınır,
    mikroveri yalnızca çapraz-kontrol içindir.
  - Tabloda '*' örnekleme-standardı uyarısı, '**' zayıf ölçek bağlantısı uyarısıdır.

Girdi:
  data/pisa/2022/volume_iii/opbe7a.xlsx            (Table III.B1.2.1)
  data/pisa_microdata/2022/creative_thinking/CRT_SPSS.zip  (çapraz-kontrol; --no-microdata ile atlanır)
  data/derived/analysis_panel.csv                   (2022 çekirdek puanlar, OECD bayrağı)
Çıktı:
  data/derived/creative_thinking_2022.csv
  data/derived/mechanisms/placebo_conditional_2022.csv
  data/derived/mechanisms/placebo_conditional_2022_summary.json
  analysis/figures/mech_placebo_conditional_2022.png
Yazan: Claude Fable 5.1, 2026-09-16 (önceki sürüm 2026-09-15 STU_QQQ'da PV arıyordu — yanlış dosya).
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
TABLE_XLSX = ROOT / "data/pisa/2022/volume_iii/opbe7a.xlsx"
TABLE_SHEET = "Table III.B1.2.1"
CRT_ZIP = ROOT / "data/pisa_microdata/2022/creative_thinking/CRT_SPSS.zip"
CRT_MEMBER = "CY08MSP_CRT_COG.SAV"
PANEL = ROOT / "data/derived/analysis_panel.csv"
OUT = ROOT / "data/derived"
MECH = OUT / "mechanisms"
FIG = ROOT / "analysis/figures"
for d in (OUT, MECH, FIG):
    d.mkdir(parents=True, exist_ok=True)

FOCUS = ["TUR", "GEO", "HUN", "SWE"]
# Tablo adı → panel adı (panel 2022 satırında bu adlar farklı/eksik)
ALIASES = {
    "Ukrainian regions (18 of 27)": "Ukrainian regions (17 of 27)",  # panel adı (Volume I etiketi)
    "Baku (Azerbaijan)": "Baku (Azerbaijan)",
}
NON_COUNTRY = {"OECD", "Partners", "OECD average"}
# Mikroveri CNT kodu → panel iso3 (PISA'nın kendi kodları; yalnız çapraz-kontrol birleştirmesi için)
MICRO_ISO = {"TAP": "TWN", "QUR": "QUA", "QCY": "CYP"}


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


def read_published_table() -> pd.DataFrame:
    """Table III.B1.2.1 → ülke, ortalama, S.E., bayraklar, katılım durumu."""
    import openpyxl

    warnings.filterwarnings("ignore")
    wb = openpyxl.load_workbook(TABLE_XLSX, read_only=True, data_only=True)
    if TABLE_SHEET not in wb.sheetnames:
        raise SystemExit(f"{TABLE_SHEET} sayfası {TABLE_XLSX.name} içinde yok: {wb.sheetnames[:10]}")
    ws = wb[TABLE_SHEET]
    rows = [r for r in ws.iter_rows(values_only=True) if r and r[0] is not None]
    # Başlık satırlarını atla: veri, 'OECD' bölüm başlığından sonra başlar
    start = next(i for i, r in enumerate(rows) if str(r[0]).strip() == "OECD")
    recs = []
    for r in rows[start:]:
        raw = str(r[0]).strip()
        if raw in NON_COUNTRY or raw.startswith(("Information on", "Note", "* ", "** ")):
            continue
        name = raw.rstrip("*").strip()
        flag_sampling = raw.endswith("*") and not raw.endswith("**")
        flag_linkage = raw.endswith("**")
        mean, se = r[1], r[2]
        if mean == "m":
            status = "did_not_participate"
            mean = se = np.nan
        elif mean == "c":
            status = "suppressed_small_sample"
            mean = se = np.nan
        else:
            status = "participated"
            mean, se = float(mean), float(se)
        recs.append(dict(country_name_table=raw, country_name=name, ct_mean=mean, ct_se=se,
                         flag_sampling_caution=flag_sampling, flag_weak_linkage=flag_linkage,
                         participation=status))
    df = pd.DataFrame(recs)
    if df.empty or df.participation.eq("participated").sum() < 40:
        raise SystemExit("Tablo okunamadı ya da beklenenden az katılımcı; sayfa yapısı değişmiş olabilir")
    return df


def microdata_unweighted_means(zip_path: Path, member: str, chunk: int = 50_000) -> pd.DataFrame:
    """CRT_COG.SAV'dan ülke bazında ağırlıksız 10-PV ortalaması ve katılımcı listesi."""
    import pyreadstat

    work = Path(tempfile.mkdtemp(prefix="crt2022_"))
    try:
        # unzip CLI: Deflate64 üyeleri de açar (python zipfile açamaz)
        subprocess.run(["unzip", "-o", "-q", str(zip_path), member, "-d", str(work)], check=True)
        sav = work / member
        _, meta = pyreadstat.read_sav(str(sav), metadataonly=True)
        cols = meta.column_names
        pv = [c for c in cols if c.upper().startswith("PV") and c.upper().endswith("CRTH_NC")]
        if len(pv) != 10:
            raise SystemExit(f"PV1CRTH_NC…PV10CRTH_NC bekleniyordu, bulunan: {pv}")
        wcols = [c for c in cols if c.upper().startswith("W_")]
        print(f"mikroveri: {member} | satır {meta.number_rows} | PV {pv[0]}…{pv[-1]} | ağırlık sütunu: {wcols or 'YOK'}")
        sums, counts = {}, {}
        for ch, _ in pyreadstat.read_file_in_chunks(pyreadstat.read_sav, str(sav),
                                                    usecols=["CNT"] + pv, chunksize=chunk):
            ch = ch[ch[pv].notna().all(axis=1)]
            ch["pvmean"] = ch[pv].mean(axis=1)
            g = ch.groupby("CNT")["pvmean"].agg(["sum", "count"])
            for cnt, row in g.iterrows():
                sums[cnt] = sums.get(cnt, 0.0) + float(row["sum"])
                counts[cnt] = counts.get(cnt, 0) + int(row["count"])
        out = pd.DataFrame({"cnt_microdata": list(sums), "ct_mean_unweighted_microdata": [sums[k] / counts[k] for k in sums],
                            "n_students_microdata": [counts[k] for k in sums]})
        out["iso3"] = out["cnt_microdata"].map(lambda c: MICRO_ISO.get(c, c))
        return out.sort_values("iso3").reset_index(drop=True)
    finally:
        try:
            (work / member).unlink(missing_ok=True)
            work.rmdir()
        except OSError:
            pass


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-microdata", action="store_true", help="CRT_SPSS.zip çapraz-kontrolünü atla")
    args = ap.parse_args()

    pub = read_published_table()
    panel = pd.read_csv(PANEL)
    p22 = panel[panel.cycle == 2022][["iso3", "country_name", "math_mean", "reading_mean", "science_mean", "oecd_member"]].copy()
    p22["core"] = p22[["math_mean", "reading_mean", "science_mean"]].mean(axis=1)
    p22["oecd"] = pd.to_numeric(p22["oecd_member"], errors="coerce").fillna(0) > 0

    pub["country_name_panel"] = pub["country_name"].map(lambda n: ALIASES.get(n, n))
    ct = pub.merge(p22[["iso3", "country_name", "core", "oecd"]].rename(columns={"country_name": "country_name_panel"}),
                   on="country_name_panel", how="left")
    unmatched = ct[ct.iso3.isna()]["country_name"].tolist()
    print(f"tablo satırı: {len(ct)} | katıldı: {int(ct.participation.eq('participated').sum())} | "
          f"katılmadı ('m'): {int(ct.participation.eq('did_not_participate').sum())} | panelde eşleşmeyen: {unmatched}")

    # ---- mikroveri çapraz-kontrolü ----
    micro_note = "atlandı (--no-microdata)"
    micro_only: list[str] | None = None
    if not args.no_microdata:
        if not CRT_ZIP.exists():
            raise SystemExit(f"{CRT_ZIP} yok")
        micro = microdata_unweighted_means(CRT_ZIP, CRT_MEMBER)
        ct = ct.merge(micro, on="iso3", how="left")
        both = ct.dropna(subset=["ct_mean", "ct_mean_unweighted_microdata"])
        diff = (both.ct_mean_unweighted_microdata - both.ct_mean)
        # Tabloda 'm' olan ülke mikroveride de olmamalı; mikroverideki her ülke tabloda olmalı
        m_in_micro = ct[(ct.participation == "did_not_participate") & ct.n_students_microdata.notna()]["iso3"].tolist()
        micro_only = sorted(set(micro.iso3) - set(ct.iso3.dropna()))  # tabloda olmayan ama mikroveride olan sistemler
        micro_note = (f"{len(micro)} sistem; yayımlanmış−ağırlıksız fark: ort {diff.mean():+.2f}, "
                      f"maks |fark| {diff.abs().max():.2f} (n={len(both)}); 'm' olup mikroveride bulunan: {m_in_micro or 'yok'}; "
                      f"yalnız mikroveride: {micro_only or 'yok'}")
        print("çapraz-kontrol:", micro_note)
        if m_in_micro:
            raise SystemExit("Tutarsızlık: tabloda 'm' olan ülke mikroveride var — katılım sınıflaması güvenilmez")
        if diff.abs().max() > 3.0:
            raise SystemExit("Tutarsızlık: yayımlanmış ile mikroveri ortalaması 3 puandan fazla ayrışıyor — ölçek/isim hatası?")
    ct.to_csv(OUT / "creative_thinking_2022.csv", index=False, encoding="utf-8-sig")

    # ---- koşullu plasebo testi (yalnız katılımcılar) ----
    d_all = ct[(ct.participation == "participated") & ct.core.notna()].copy()
    rows, summary = [], {
        "note": "Türkiye ve Gürcistan PISA 2022 yaratıcı düşünmeye katılmadı (Table III.B1.2.1 'm'; mikroveride yok). "
                "Yaratıcı düşünme Türkiye için plasebo-alan sonucu olamaz; test yalnız katılımcılar için raporlanır.",
        "microdata_crosscheck": micro_note,
        "focus_status": {},
    }
    for iso in FOCUS:
        r = ct[ct.iso3 == iso]
        if not r.empty:
            summary["focus_status"][iso] = r.participation.iloc[0]
        elif micro_only is not None and iso in micro_only:
            summary["focus_status"][iso] = "not_in_table (but in CRT microdata)"
        else:
            summary["focus_status"][iso] = "not_in_table"  # Table III.B1.2.1'de satırı yok; mikroveride de yok (İsveç)
    for scope in ["all", "oecd"]:
        d = d_all if scope == "all" else d_all[d_all.oecd]
        x, y = d["core"].to_numpy(float), d["ct_mean"].to_numpy(float)
        for deg, name in [(1, "linear"), (2, "quadratic")]:
            if len(d) <= deg + 2:
                continue
            beta, fit, resid, r2, rmse = ols(x, y, deg)
            tmp = d[["iso3", "country_name", "core", "ct_mean", "ct_se", "oecd", "flag_sampling_caution", "flag_weak_linkage"]].copy()
            tmp["scope"], tmp["spec"] = scope, name
            tmp["ct_pred"] = fit
            tmp["residual"] = resid
            tmp["resid_sd"] = resid / rmse if rmse else np.nan
            tmp["rank_low"] = tmp["residual"].rank(method="min")
            tmp["pctile"] = tmp["residual"].rank(pct=True) * 100
            rows.append(tmp)
            key = f"{scope}_{name}"
            summary[key] = {"n": int(len(d)), "slope": round(float(beta[1]), 4), "r2": round(float(r2), 3), "rmse": round(float(rmse), 2)}
            for iso in FOCUS:
                r = tmp[tmp.iso3 == iso]
                if r.empty:
                    continue
                r = r.iloc[0]
                m_loo = d.iso3 != iso
                b_loo, *_ = ols(d.loc[m_loo, "core"].to_numpy(float), d.loc[m_loo, "ct_mean"].to_numpy(float), deg)
                pred_loo = float(np.polyval(b_loo[::-1], float(r.core)))
                summary[key][iso] = {
                    "core_2022": round(float(r.core), 1), "ct": round(float(r.ct_mean), 2),
                    "ct_predicted": round(float(r.ct_pred), 2), "residual": round(float(r.residual), 2),
                    "residual_in_sd": round(float(r.resid_sd), 2),
                    "residual_leave_one_out": round(float(r.ct_mean) - pred_loo, 2),
                    "rank_from_bottom": f"{int(r.rank_low)}/{len(tmp)}", "percentile": round(float(r.pctile), 1),
                }
            foc = ", ".join(f"{iso}: artık {summary[key][iso]['residual']:+.2f} ({summary[key][iso]['rank_from_bottom']})"
                            for iso in FOCUS if iso in summary[key]) or "odak ülke yok"
            print(f"[{scope}/{name}] n={len(d)} eğim={beta[1]:.4f} R2={r2:.3f} RMSE={rmse:.2f} | {foc}")
    res = pd.concat(rows, ignore_index=True)
    res.to_csv(MECH / "placebo_conditional_2022.csv", index=False, encoding="utf-8-sig")

    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        d = res[(res.scope == "all") & (res.spec == "linear")].sort_values("core")
        fig, ax = plt.subplots(figsize=(8.5, 6))
        ax.scatter(d.core, d.ct_mean, s=22, c="grey", alpha=0.6, label="katılımcılar (n=%d)" % len(d))
        ax.plot(d.core, d.ct_pred, color="black", lw=1.2, label="OLS uyum")
        r = d[d.iso3 == "HUN"]
        if not r.empty:
            ax.scatter(r.core, r.ct_mean, s=70, c="steelblue", zorder=5, label="HUN")
            ax.annotate(f"HUN ({float(r.residual.iloc[0]):+.1f})", (float(r.core.iloc[0]), float(r.ct_mean.iloc[0])),
                        textcoords="offset points", xytext=(8, -12), color="steelblue", fontsize=9)
        ax.text(0.02, 0.97, "TUR ve GEO: 2022 yaratıcı düşünmeye katılmadı", transform=ax.transAxes,
                va="top", fontsize=9, color="firebrick")
        ax.set_xlabel("çekirdek alanlar 2022 (mat/okuma/fen ortalaması)")
        ax.set_ylabel("yaratıcı düşünme 2022 (0–60 ölçeği)")
        ax.set_title("Koşullu plasebo-alan testi: yaratıcı düşünme ~ çekirdek (PISA 2022)")
        ax.legend(frameon=False, fontsize=9, loc="lower right")
        ax.grid(alpha=0.3, linestyle="--")
        fig.tight_layout()
        fig.savefig(FIG / "mech_placebo_conditional_2022.png", dpi=150)
        plt.close(fig)
    except Exception as exc:  # pragma: no cover
        print(f"şekil çizilemedi: {exc}")

    (MECH / "placebo_conditional_2022_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=1), encoding="utf-8")
    print("DONE creative thinking 2022 —", summary["note"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
