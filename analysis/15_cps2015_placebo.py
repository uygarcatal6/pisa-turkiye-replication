#!/usr/bin/env python3
"""İkinci plasebo alan (gerçekten kullanılabilen): PISA 2015 işbirlikli problem çözme (CPS 2015).

Neden: 2022 yaratıcı düşünmeye Türkiye katılmadı (bkz. 13). 2015 işbirlikli problem çözme
ise kırılma (2013) sonrası ilk döngüde uygulanan, önceden hazırlık yapılamayan yeni alan;
Türkiye katıldı (STU_QQQ'daki Option_CPS bayrağı 5.895/5.895 öğrencide 1; Macaristan da
katıldı; Gürcistan katılmadı — `data/derived/cache/innovative_domain_participation.csv`).

Yöntem:
  1. `PUF_SPSS_COMBINED_CMB_STU_CPS.zip` → CY6_MS_CMB_STU_CPS.sav: CNT, CNTSCHID, CNTSTUID,
     PV1CLPS…PV10CLPS (dosyada ağırlık yok).
  2. `PUF_SPSS_COMBINED_CMB_STU_QQQ.zip` → CY6_MS_CMB_STU_QQQ.sav: W_FSTUWT (CNT+CNTSCHID+CNTSTUID
     üzerinden birleştirme).
  3. Ülke ortalaması = 10 PV'nin öğrenci-düzeyi ortalamasının W_FSTUWT-ağırlıklı ortalaması
     (nokta tahmini; standart hata için BRR + Rubin gerekir, burada üretilmez).
  4. Koşullu test: CPS2015 ~ çekirdek 2015 (panel mat/okuma/fen ortalaması); artık, sıra,
     leave-one-out; TUR ve HUN raporlanır.

İç tutarlılık kontrolleri: ağırlıklı vs ağırlıksız fark; birleştirmede kayıp öğrenci payı;
OECD üyesi ülke ortalamalarının ortalaması (OECD'nin CPS ölçeğini OECD ortalaması ≈ 500 olacak
şekilde kurduğu Volume V'te doğrulanmalı — betik yalnızca değeri raporlar).
Yayımlanmış değerlerle çapraz-kontrol adım 24'te (`24_placebo_backbone.py`, 2026-09-20): OECD Volume V Figure V.1.1
(s. 43–44; `data/pisa/2015/9789264285521-en.pdf`, birincil) ve UK DfE raporu Tablo 3–5 (ikincil); sonuç
`data/derived/placebo_backbone/summary.json → crosscheck_oecd_volv / crosscheck_dfe`.

Çıktı:
  data/derived/cps2015_country_means.csv
  data/derived/mechanisms/placebo_conditional_2015cps.csv, placebo_conditional_2015cps_summary.json
  analysis/figures/mech_placebo_conditional_2015cps.png
Yazan: Claude Fable 5.1, 2026-09-16.
"""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd
import pyreadstat

ROOT = Path(__file__).resolve().parent.parent
CPS_ZIP = ROOT / "data/pisa_microdata/2015/PUF_SPSS_COMBINED_CMB_STU_CPS.zip"
QQQ_ZIP = ROOT / "data/pisa_microdata/2015/PUF_SPSS_COMBINED_CMB_STU_QQQ.zip"
PANEL = ROOT / "data/derived/analysis_panel.csv"
OUT = ROOT / "data/derived"
MECH = OUT / "mechanisms"
FIG = ROOT / "analysis/figures"
for d in (OUT, MECH, FIG):
    d.mkdir(parents=True, exist_ok=True)
FOCUS = ["TUR", "HUN", "GEO", "SWE"]
IDS = ["CNT", "CNTSCHID", "CNTSTUID"]
# 2015 mikroveri CNT kodu → panel iso3 (yalnız bilinen farklar)
# Kod kitabı (Codebook_CMB, CNT etiketleri): QCH = B-S-J-G (China), QES = Spain (Regions),
# QUC = Massachusetts (USA), QUE = North Carolina (USA), TAP = Chinese Taipei
MICRO_ISO = {"TAP": "TWN", "QCH": "CHN"}
SUBNATIONAL = ["QUC", "QUE", "QES", "QAR"]


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


def extract(zp: Path, work: Path) -> Path:
    zf = zipfile.ZipFile(zp)
    member = max(zf.namelist(), key=lambda n: zf.getinfo(n).file_size)
    subprocess.run(["unzip", "-o", "-q", str(zp), member, "-d", str(work)], check=True)
    return work / member


def read_cps(sav: Path) -> pd.DataFrame:
    _, meta = pyreadstat.read_sav(str(sav), metadataonly=True)
    cols = meta.column_names
    pv = [f"PV{i}CLPS" for i in range(1, 11)]
    missing = [c for c in pv + IDS if c not in cols]
    if missing:
        raise SystemExit(f"CPS dosyasında eksik sütun: {missing}")
    if any(c.upper().startswith("W_") for c in cols):
        print("uyarı: CPS dosyasında W_* sütunu var; yine de STU_QQQ ağırlığı kullanılacak")
    parts = []
    for ch, _ in pyreadstat.read_file_in_chunks(pyreadstat.read_sav, str(sav), usecols=IDS + pv, chunksize=100_000):
        ch = ch[ch[pv].notna().all(axis=1)].copy()
        ch["pvmean"] = ch[pv].mean(axis=1)
        parts.append(ch[IDS + ["pvmean"]])
    df = pd.concat(parts, ignore_index=True)
    print(f"CPS: {meta.number_rows} satır, PV'si tam olan {len(df)}; sistem sayısı {df.CNT.nunique()}")
    return df


def read_weights(sav: Path, keep_cnt: set[str]) -> pd.DataFrame:
    _, meta = pyreadstat.read_sav(str(sav), metadataonly=True)
    if "W_FSTUWT" not in meta.column_names:
        raise SystemExit("STU_QQQ'da W_FSTUWT yok")
    parts = []
    for ch, _ in pyreadstat.read_file_in_chunks(pyreadstat.read_sav, str(sav), usecols=IDS + ["W_FSTUWT"], chunksize=100_000):
        parts.append(ch[ch.CNT.isin(keep_cnt)])
    w = pd.concat(parts, ignore_index=True)
    print(f"ağırlık: {len(w)} öğrenci ({len(keep_cnt)} CPS sistemi)")
    return w


def main() -> int:
    cache = OUT / "cache" / "cps2015_students.parquet"
    if cache.exists():
        m = pd.read_parquet(cache)
        lost = np.nan
        print(f"önbellekten: {cache.name} ({len(m)} öğrenci)")
    else:
        work = Path(tempfile.mkdtemp(prefix="cps2015_"))
        try:
            cps = read_cps(extract(CPS_ZIP, work))
            w = read_weights(extract(QQQ_ZIP, work), set(cps.CNT))
        finally:
            shutil.rmtree(work, ignore_errors=True)
        m = cps.merge(w, on=IDS, how="left", validate="one_to_one")
        lost = float(m.W_FSTUWT.isna().mean())
        print(f"ağırlık birleştirmesi: eşleşmeyen öğrenci payı {lost:.4f}")
        if lost > 0.01:
            raise SystemExit("Birleştirme kaybı %1'i aşıyor — kimlik sütunları farklı olabilir")
        m = m.dropna(subset=["W_FSTUWT"])
        m["merge_loss"] = lost
        cache.parent.mkdir(parents=True, exist_ok=True)
        m.to_parquet(cache, index=False)
    lost = float(m["merge_loss"].iloc[0]) if "merge_loss" in m.columns else lost
    g = m.groupby("CNT")
    means = pd.DataFrame({
        "cps2015_mean_weighted": g.apply(lambda d: float(np.average(d.pvmean, weights=d.W_FSTUWT))),
        "cps2015_mean_unweighted": g.pvmean.mean(),
        "n_students": g.size(),
        "sum_weights": g.W_FSTUWT.sum(),
    }).reset_index().rename(columns={"CNT": "cnt_microdata"})
    means["iso3"] = means.cnt_microdata.map(lambda c: MICRO_ISO.get(c, c))
    # Alt-ulusal birimleri (ABD eyaletleri, İspanya bölgeleri, Buenos Aires) atla; ulusal kodlar kalır
    dropped = sorted(set(means.cnt_microdata) & set(SUBNATIONAL))
    means = means[~means.cnt_microdata.isin(SUBNATIONAL)]
    print(f"alt-ulusal birimler atlandı: {dropped} → {len(means)} ulusal sistem")

    panel = pd.read_csv(PANEL)
    p15 = panel[panel.cycle == 2015][["iso3", "country_name", "math_mean", "reading_mean", "science_mean",
                                      "oecd_member", "asterisk_flag"]].copy()
    p15["core"] = p15[["math_mean", "reading_mean", "science_mean"]].mean(axis=1)
    p15["oecd"] = pd.to_numeric(p15.oecd_member, errors="coerce").fillna(0) > 0
    ct = means.merge(p15, on="iso3", how="left")
    ct["oecd"] = ct.oecd.fillna(False).astype(bool)   # panelde olmayan sistemler → OECD değil
    unmatched = ct[ct.core.isna()].cnt_microdata.tolist()
    ct.to_csv(OUT / "cps2015_country_means.csv", index=False, encoding="utf-8-sig")
    oecd_avg = float(ct[ct.oecd].cps2015_mean_weighted.mean())
    diff = ct.cps2015_mean_weighted - ct.cps2015_mean_unweighted
    print(f"panelde çekirdeği olmayan: {unmatched} | OECD üyesi ülke ortalamalarının ortalaması {oecd_avg:.1f} "
          f"(n={int(ct.oecd.sum())}) | ağırlıklı−ağırlıksız: ort {diff.mean():+.2f}, maks |{diff.abs().max():.2f}|")

    d_all = ct.dropna(subset=["core"]).copy()
    rows, summary = [], {
        "note": "2015 işbirlikli problem çözme: Türkiye ve Macaristan katıldı, Gürcistan katılmadı. Ülke ortalamaları "
                "mikroveriden (PV1–10CLPS, W_FSTUWT STU_QQQ'dan). Yayımlanmış değerlerle çapraz-kontrol: adım 24 "
                "(OECD Volume V Figure V.1.1 birincil + UK DfE Tablo 3–5 ikincil; data/derived/placebo_backbone/summary.json).",
        "oecd_member_mean_of_country_means": round(oecd_avg, 2),
        "weight_merge_loss_share": round(float(lost), 5),
        "focus_status": {iso: ("participated" if iso in set(ct.iso3) else "did_not_participate") for iso in FOCUS},
        "focus_asterisk_2015": {iso: (None if iso not in set(ct.iso3) or pd.isna(ct.loc[ct.iso3 == iso, "asterisk_flag"].iloc[0])
                                      else str(ct.loc[ct.iso3 == iso, "asterisk_flag"].iloc[0])) for iso in FOCUS},
    }
    for scope in ["all", "oecd"]:
        d = d_all if scope == "all" else d_all[d_all.oecd]
        x, y = d.core.to_numpy(float), d.cps2015_mean_weighted.to_numpy(float)
        for deg, name in [(1, "linear"), (2, "quadratic")]:
            if len(d) <= deg + 2:
                continue
            beta, fit, resid, r2, rmse = ols(x, y, deg)
            tmp = d[["iso3", "country_name", "core", "cps2015_mean_weighted", "oecd", "asterisk_flag"]].copy()
            tmp["scope"], tmp["spec"] = scope, name
            tmp["cps_pred"], tmp["residual"] = fit, resid
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
                b_loo, *_ = ols(d.loc[m_loo, "core"].to_numpy(float), d.loc[m_loo, "cps2015_mean_weighted"].to_numpy(float), deg)
                pred_loo = float(np.polyval(b_loo[::-1], float(r.core)))
                summary[key][iso] = {
                    "core_2015": round(float(r.core), 1), "cps2015": round(float(r.cps2015_mean_weighted), 1),
                    "cps_predicted": round(float(r.cps_pred), 1), "residual": round(float(r.residual), 1),
                    "residual_in_sd": round(float(r.resid_sd), 2),
                    "residual_leave_one_out": round(float(r.cps2015_mean_weighted) - pred_loo, 1),
                    "rank_from_bottom": f"{int(r.rank_low)}/{len(tmp)}", "percentile": round(float(r.pctile), 1),
                }
            foc = ", ".join(f"{iso}: artık {summary[key][iso]['residual']:+.1f} ({summary[key][iso]['rank_from_bottom']})"
                            for iso in FOCUS if iso in summary[key])
            print(f"[{scope}/{name}] n={len(d)} eğim={beta[1]:.4f} R2={r2:.3f} RMSE={rmse:.2f} | {foc}")
    res = pd.concat(rows, ignore_index=True)
    res.to_csv(MECH / "placebo_conditional_2015cps.csv", index=False, encoding="utf-8-sig")

    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        d = res[(res.scope == "all") & (res.spec == "linear")].sort_values("core")
        fig, ax = plt.subplots(figsize=(8.5, 6))
        ax.scatter(d.core, d.cps2015_mean_weighted, s=22, c="grey", alpha=0.6, label="katılımcılar (n=%d)" % len(d))
        ax.plot(d.core, d.cps_pred, color="black", lw=1.2, label="OLS uyum")
        for iso, col in [("TUR", "firebrick"), ("HUN", "steelblue")]:
            r = d[d.iso3 == iso]
            if r.empty:
                continue
            ax.scatter(r.core, r.cps2015_mean_weighted, s=70, c=col, zorder=5, label=iso)
            ax.annotate(f"{iso} ({float(r.residual.iloc[0]):+.0f})", (float(r.core.iloc[0]), float(r.cps2015_mean_weighted.iloc[0])),
                        textcoords="offset points", xytext=(8, -12), color=col, fontsize=9)
        ax.set_xlabel("çekirdek alanlar 2015 (mat/okuma/fen ortalaması)")
        ax.set_ylabel("işbirlikli problem çözme 2015 (mikroveriden, ağırlıklı)")
        ax.set_title("Koşullu plasebo-alan testi: CPS 2015 ~ çekirdek")
        ax.legend(frameon=False, fontsize=9, loc="lower right")
        ax.grid(alpha=0.3, linestyle="--")
        fig.tight_layout()
        fig.savefig(FIG / "mech_placebo_conditional_2015cps.png", dpi=150)
        plt.close(fig)
    except Exception as exc:  # pragma: no cover
        print(f"şekil çizilemedi: {exc}")

    (MECH / "placebo_conditional_2015cps_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=1), encoding="utf-8")
    print("DONE CPS 2015 placebo")
    return 0


if __name__ == "__main__":
    sys.exit(main())
