# -*- coding: utf-8 -*-
"""
31 — Kırılma ÖNCESİ plasebo-alan noktası, MİKROVERİDEN: PISA 2003 problem çözme (§10(6)).

NEDEN 2012 DEĞİL 2003: Prompt (22 Eyl) 2012 problem çözmenin ağırlıklı yeniden hesabını
istiyordu. 2012 problem çözme PV'leri diskteki HİÇBİR 2012 dosyasında yok; 2012 bilgisayar
tabanlı değerlendirme ayrı bir OECD yayını ve klasörde değil. Kanıt (22 Eyl, bu oturum):
  · PISA2012_SPSS_student.txt tek DATA LIST, 634 değişken, maxpos 2348 = veri satır uzunluğu
    2348 → sözdizimi eksiksiz; PV kökleri MATH READ SCIE + MACC MACQ MACS MACU MAPE MAPF MAPI.
    PROB / CPRO / CMAT / CREA yok.
  · INT_COG12_DEC03 ve INT_COG12_S_DEC03 madde önekleri yalnız PM / PR / PS (kâğıt);
    CP / CM / CR (bilgisayar) maddesi sıfır.
  · 2012 öğrenci dosyasında CBA kitapçık/oturum değişkeni yok (yalnız BOOKID).
Buna karşılık PISA 2003 öğrenci dosyasında PV1PROB…PV5PROB VAR (konum 1055–1099) ve 2003
problem çözme maddeleri (önek X, 19 madde) çekirdek maddelerle AYNI kâğıt kitapçık
rotasyonunda. Yani 2003 noktası hem kırılma öncesi hem MOD EŞLEŞMELİ: §9'un 2012 için
yazdığı "problem çözme bilgisayarda, çekirdek kâğıtta" uyarısı 2003'te tasarımdan düşüyor.

Betik 25 (2012, yayımlanmış tam sayılı Table V.A) DEĞİŞTİRİLMEZ; bu betik onun yerine
geçmez, yanına kırılma öncesi ikinci ve mod-eşleşmeli bir nokta koyar.

YÖNTEM: 10/15/25 ile aynı koşullu tasarım — PS2003 ~ çekirdek 2003, {tüm, OECD} ×
{doğrusal, karesel}; artık, artık/RMSE, sıra, yüzdelik, leave-one-out.
Betik 25'ten FARKI: ülke ortalamaları yayımlanmış tam sayı değil, mikroveriden
W_FSTUWT ağırlıklı; standart hatalar BRR (Fay 0,5, 80 replikasyon) + Rubin kuralıyla
(`_pisa_puf.brr_pv_stat`). Artığın belirsizliği parametrik bootstrap ile taşınır:
her turda her ülkenin PS'i ve çekirdeği kendi BRR standart hatasıyla çekilir, doğru
YENİDEN uydurulur, artık yeniden hesaplanır — yani hem ölçüm hatası hem uyum çizgisinin
oynaması hesaba girer. Betik 25'te bu mümkün değildi (yayımlanmış tam sayı, SE yok).

KAPSAM: 2003 PUF'ta 41 birim. GBR dışarıda — PISA 2003'te yanıt oranı standardını
tutturamadığı için OECD ortalamalarını yayımlamadı (panelde de 2003 satırı yok);
mikroveride duruyor ama karşılaştırılabilir değil. Ana spesifikasyon panelle eşleşen
ülkelerde (betik 25 ile aynı mantık), sağlamlık olarak "tüm PUF birimleri" de yazılır.
GEO PISA 2003'te yok.

Çıktı: data/derived/mechanisms/placebo_conditional_2003ps_puf.csv, *_summary.json;
       analysis/figures/mech_placebo_conditional_2003ps_puf.png. Etiket [E31].
Yazan: Claude Opus 5 (ana oturum), 2026-09-22 — kod Fable 5.1'e gidecekti, Fable kullanım
limiti nedeniyle iki ajan koşumu da düştü. Denetim: Opus 4.8, bekliyor.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _pisa_puf as P  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
PANEL = ROOT / "data" / "derived" / "analysis_panel.csv"
MECH = ROOT / "data" / "derived" / "mechanisms"
FIG = ROOT / "analysis" / "figures"
for d in (MECH, FIG):
    d.mkdir(parents=True, exist_ok=True)

FOCUS = ["TUR", "HUN", "SWE"]
NOT_COMPARABLE = {"GBR": "PISA 2003'te yanit orani standardi tutmadi; OECD ortalama yayimlamadi"}
BOOT = 2000
SEED = 20260922


def ols(x, y, deg=1):
    X = np.vander(x, deg + 1, increasing=True)
    beta, *_ = np.linalg.lstsq(X, y, rcond=None)
    fit = X @ beta
    resid = y - fit
    n, k = len(y), X.shape[1]
    rmse = float(np.sqrt((resid @ resid) / max(n - k, 1)))
    ss = float(((y - y.mean()) ** 2).sum())
    return beta, fit, resid, (1 - float(resid @ resid) / ss if ss > 0 else np.nan), rmse


def main() -> int:
    spec = P.parse_datalist(P.ROOT / P.REGISTRY[2003]["syn"])
    roots = ["PROB", "MATH", "READ", "SCIE"]
    for r in roots:
        if not P.pv_cols(spec, r):
            raise SystemExit(f"2003 sozdiziminde PV kokleri yok: {r} — DUR, tahmin etme")
    want = ["CNT", "W_FSTUWT", *P.REPW] + [c for r in roots for c in P.pv_cols(spec, r)]
    df = P.read_columns(2003, want)
    print(f"[2003 PUF] {len(df):,} satir, {df.CNT.nunique()} birim, TUR {int((df.CNT=='TUR').sum()):,}")

    est = {}
    for r in roots:
        e = P.brr_pv_stat(df, P.pv_cols(spec, r), "W_FSTUWT", P.REPW).set_index("iso3")
        est[r] = e
        print(f"  {r}: {len(e)} birim · TUR {e.loc['TUR','mean']:.1f} (SE {e.loc['TUR','se']:.2f})")

    # PS ile çekirdek AYNI öğrencilerden geliyor → ülke kestirimleri korelasyonlu.
    # Bootstrap'ta bağımsız çekmek aralığı gereksiz genişletir (Opus 4.8 denetimi D2a).
    # PV indeksine göre hizalı çekirdek: p'inci grup = [MATHp, READp, SCIEp]
    core_pv = [[P.pv_cols(spec, r)[i] for r in ("MATH", "READ", "SCIE")] for i in range(5)]
    rho = P.brr_pv_corr(df, P.pv_cols(spec, "PROB"), core_pv, "W_FSTUWT", P.REPW).set_index("iso3")

    d = pd.DataFrame({
        "ps2003": est["PROB"]["mean"], "ps2003_se": est["PROB"]["se"],
        "ps_se_s": est["PROB"]["se_sampling"], "ps_se_i": est["PROB"]["se_imputation"],
        "rho_s": rho["rho_sampling"], "rho_i": rho["rho_imputation"],
        "math": est["MATH"]["mean"], "math_se": est["MATH"]["se"],
        "read": est["READ"]["mean"], "read_se": est["READ"]["se"],
        "scie": est["SCIE"]["mean"], "scie_se": est["SCIE"]["se"],
        "math_se_s": est["MATH"]["se_sampling"], "math_se_i": est["MATH"]["se_imputation"],
        "read_se_s": est["READ"]["se_sampling"], "read_se_i": est["READ"]["se_imputation"],
        "scie_se_s": est["SCIE"]["se_sampling"], "scie_se_i": est["SCIE"]["se_imputation"],
        "n_students": est["PROB"]["n_students"],
    }).reset_index()
    d["core"] = d[["math", "read", "scie"]].mean(axis=1)
    # Çekirdek ortalamasının SE'si: üç alan aynı öğrencilerden geldiği için bağımsız DEĞİL;
    # bağımsızlık varsayımı SE'yi KÜÇÜK gösterir, pozitif korelasyon altında üst sınır
    # ortalama SE'dir. Muhafazakâr olan üst sınır alınır (bootstrap'ta da bu kullanılır).
    d["core_se"] = d[["math_se", "read_se", "scie_se"]].mean(axis=1)
    # çekirdeğin bileşen SE'leri: üst sınır mantığı (docstring) aynen korunur
    d["core_se_s"] = d[["math_se_s", "read_se_s", "scie_se_s"]].mean(axis=1)
    d["core_se_i"] = d[["math_se_i", "read_se_i", "scie_se_i"]].mean(axis=1)
    d["core_mr"] = d[["math", "read"]].mean(axis=1)

    panel = pd.read_csv(PANEL)
    p03 = panel[panel.cycle == 2003][["iso3", "country_name", "math_mean", "reading_mean"]]
    oecd = (panel.sort_values("cycle").groupby("iso3").oecd_member.last())
    d = d.merge(p03, on="iso3", how="left")
    d["oecd"] = pd.to_numeric(d.iso3.map(oecd), errors="coerce").fillna(0) > 0
    d["in_panel_2003"] = d.math_mean.notna()
    d["note"] = d.iso3.map(NOT_COMPARABLE).fillna("")

    chk = d[d.in_panel_2003].copy()
    chk["dm"] = (chk.math - chk.math_mean).abs()
    chk["dr"] = (chk.read - chk.reading_mean).abs()
    print(f"[panel kontrolu] n={len(chk)} · |mat farki| maks {chk.dm.max():.4f} · "
          f"|oku farki| maks {chk.dr.max():.4f}")
    if max(chk.dm.max(), chk.dr.max()) > 0.01:
        raise SystemExit("DUR: PUF cekirdegi yayimlanmis panel degerleriyle uyusmuyor (panel kanoniktir)")

    base = d[~d.iso3.isin(NOT_COMPARABLE)].copy()
    main_set = base[base.in_panel_2003].copy()
    print(f"regresyona giren (ana): {len(main_set)} · OECD bayragi {int(main_set.oecd.sum())} · "
          f"disarida: {sorted(NOT_COMPARABLE)} + panelde 2003 satiri olmayan "
          f"{sorted(base.loc[~base.in_panel_2003,'iso3'])}")

    rng = np.random.default_rng(SEED)
    rows, summary = [], {
        "note": "PISA 2003 problem cozme (KAGIT, cekirdekle ayni kitapcik rotasyonu → mod farki YOK). "
                "Ulke ortalamalari mikroveriden W_FSTUWT agirlikli; SE = BRR (Fay 0,5; 80 replikasyon) + Rubin.",
        "why_not_2012": "2012 problem cozme/CBA PV'leri diskteki hicbir 2012 dosyasinda yok "
                        "(ogrenci sozdizimi eksiksiz: maxpos 2348 = reclen 2348; bilissel dosyalarda yalniz PM/PR/PS onekleri). "
                        "2012 CBA ayri bir OECD yayini, klasorde degil.",
        "source": "data/pisa_microdata/2003/INT_stui_2003_v2.zip (+ PISA2003_SPSS_student.txt sozdizimi)",
        "engine": "analysis/_pisa_puf.py — 587 ulke x dongu x alan hucresinde yayimlanmis ortalama ve SE'yi "
                  "birebir yeniden uretti (maks sapma 0,0005 = yayimlanmis degerin yuvarlamasi)",
        "n_units_puf": int(df.CNT.nunique()), "n_in_main_regression": int(len(main_set)),
        "excluded": {k: v for k, v in NOT_COMPARABLE.items()},
        "not_in_panel_2003": sorted(base.loc[~base.in_panel_2003, "iso3"]),
        "bootstrap_draws": BOOT, "seed": SEED,
        "bootstrap_note": "PS ve cekirdek KORELASYONLU cekilir (brr_pv_corr); bagimsiz cekim Var(y-bx)'i abartip araligi gereksiz genisletiyordu — Opus 4.8 denetimi 22 Eyl, D2a.",
        "focus_status": {i: ("participated" if (d.iso3 == i).any() else "not in PISA 2003")
                         for i in FOCUS + ["GEO"]},
        "mode_note": "2003 problem cozme ve cekirdek AYNI kagit kitapciklarda uygulandi; "
                     "betik 25'in 2012 icin tasidigi mod uyarisi burada gecerli DEGIL.",
    }

    for scope in ["all", "oecd"]:
        s = main_set if scope == "all" else main_set[main_set.oecd]
        for core_col, core_se_col, core_tag in [("core", "core_se", "mat/oku/fen"), ("core_mr", "math_se", "mat/oku")]:
            x = s[core_col].to_numpy(float)
            y = s.ps2003.to_numpy(float)
            xs = s[core_se_col].to_numpy(float)
            ys = s.ps2003_se.to_numpy(float)
            for deg, name in [(1, "linear"), (2, "quadratic")]:
                beta, fit, resid, r2, rmse = ols(x, y, deg)
                tmp = s[["iso3", "country_name", "oecd", "n_students"]].copy()
                tmp["scope"], tmp["spec"], tmp["core_def"] = scope, name, core_tag
                tmp["core"], tmp["core_se"] = x, xs
                tmp["ps2003"], tmp["ps2003_se"] = y, ys
                tmp["ps_pred"], tmp["residual"] = fit, resid
                tmp["resid_sd"] = resid / rmse if rmse else np.nan
                tmp["rank_low"] = tmp.residual.rank(method="min")
                tmp["pctile"] = tmp.residual.rank(pct=True) * 100

                # KORELASYONLU bootstrap: PS ve çekirdek aynı öğrencilerden, bağımsız çekilmez.
                rr = P.combine_rho(s.rho_s.to_numpy(float), s.rho_i.to_numpy(float),
                                   s.ps_se_s.to_numpy(float), s.ps_se_i.to_numpy(float),
                                   s.core_se_s.to_numpy(float), s.core_se_i.to_numpy(float))
                boot = np.empty((BOOT, len(s)))
                for b in range(BOOT):
                    z1, z2 = rng.standard_normal(len(s)), rng.standard_normal(len(s))
                    yb = y + ys * z1
                    xb = x + xs * (rr * z1 + np.sqrt(np.maximum(1 - rr ** 2, 0)) * z2)
                    boot[b] = yb - np.vander(xb, deg + 1, increasing=True) @ ols(xb, yb, deg)[0]
                lo, hi = np.percentile(boot, [2.5, 97.5], axis=0)
                tmp["resid_lo95"], tmp["resid_hi95"] = lo, hi
                tmp["resid_boot_se"] = boot.std(axis=0, ddof=1)
                rows.append(tmp)

                key = f"{scope}_{name}_{core_col}"
                summary[key] = {"n": int(len(s)), "slope": round(float(beta[1]), 4),
                                "r2": round(float(r2), 3), "rmse": round(float(rmse), 2)}
                for iso in FOCUS:
                    r = tmp[tmp.iso3 == iso]
                    if r.empty:
                        continue
                    r = r.iloc[0]
                    m = s.iso3 != iso
                    b_loo, *_ = ols(x[m.to_numpy()], y[m.to_numpy()], deg)
                    pred_loo = float(np.polyval(b_loo[::-1], float(r.core)))
                    summary[key][iso] = {
                        "core_2003": round(float(r.core), 1), "ps2003": round(float(r.ps2003), 1),
                        "ps2003_se": round(float(r.ps2003_se), 2),
                        "ps_predicted": round(float(r.ps_pred), 1),
                        "residual": round(float(r.residual), 1),
                        "residual_ci95": [round(float(r.resid_lo95), 1), round(float(r.resid_hi95), 1)],
                        "residual_in_sd": round(float(r.resid_sd), 2),
                        "residual_leave_one_out": round(float(r.ps2003) - pred_loo, 1),
                        "rank_from_bottom": f"{int(r.rank_low)}/{len(tmp)}",
                        "percentile": round(float(r.pctile), 1),
                    }
                foc = ", ".join(
                    f"{i}: {summary[key][i]['residual']:+.1f} "
                    f"[{summary[key][i]['residual_ci95'][0]:+.1f}, {summary[key][i]['residual_ci95'][1]:+.1f}] "
                    f"({summary[key][i]['rank_from_bottom']})" for i in FOCUS if i in summary[key])
                print(f"[{scope}/{name}/{core_tag}] n={len(s)} egim={beta[1]:.4f} R2={r2:.3f} "
                      f"RMSE={rmse:.2f} | {foc}")

    res = pd.concat(rows, ignore_index=True)
    res.to_csv(MECH / "placebo_conditional_2003ps_puf.csv", index=False, encoding="utf-8-sig")

    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        pl = res[(res.scope == "all") & (res.spec == "linear") & (res.core_def == "mat/oku/fen")].sort_values("core")
        fig, ax = plt.subplots(figsize=(8.5, 6))
        ax.errorbar(pl.core, pl.ps2003, yerr=pl.ps2003_se, xerr=pl.core_se, fmt="o", ms=4,
                    color="grey", alpha=0.55, lw=0.7, label=f"katilimcilar (n={len(pl)}), ±1 SE")
        ax.plot(pl.core, pl.ps_pred, color="black", lw=1.2, label="OLS uyum")
        for iso, col in [("TUR", "firebrick"), ("HUN", "steelblue"), ("SWE", "seagreen")]:
            r = pl[pl.iso3 == iso]
            if r.empty:
                continue
            ax.errorbar(r.core, r.ps2003, yerr=r.ps2003_se, xerr=r.core_se, fmt="o", ms=9,
                        color=col, zorder=5, lw=1.2, label=iso)
            ax.annotate(f"{iso} ({float(r.residual.iloc[0]):+.0f})",
                        (float(r.core.iloc[0]), float(r.ps2003.iloc[0])),
                        textcoords="offset points", xytext=(9, -13), color=col, fontsize=9)
        ax.set_xlabel("cekirdek alanlar 2003 (mat/oku/fen, PUF agirlikli; KAGIT)")
        ax.set_ylabel("problem cozme 2003 (PUF agirlikli; KAGIT — ayni kitapcik)")
        ax.set_title("Kosullu plasebo-alan testi: PS 2003 ~ cekirdek (kirilma oncesi, mod eslesmeli)")
        ax.legend(frameon=False, fontsize=9, loc="lower right")
        ax.grid(alpha=0.3, linestyle="--")
        fig.tight_layout()
        fig.savefig(FIG / "mech_placebo_conditional_2003ps_puf.png", dpi=150)
        plt.close(fig)
    except Exception as exc:  # pragma: no cover
        print(f"sekil cizilemedi: {exc}")

    (MECH / "placebo_conditional_2003ps_puf_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=1), encoding="utf-8")
    print("DONE PS 2003 placebo (PUF)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
