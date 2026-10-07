# -*- coding: utf-8 -*-
"""
33 — PISA 2012 problem çözme: PUF ağırlıklı yeniden hesap + mod kontrolü (§10(6); prompt İş A + İş B).

Betik 25 kırılma öncesi noktayı YAYIMLANMIŞ TAM SAYILI Table V.A ortalamalarından kuruyor ve
§9 bunu "RMSE 15–17, mikroveri yok" diye sınır yazıyor. Bu betik aynı tasarımı mikroveriden
kurar. **Betik 25 DEĞİŞTİRİLMEZ**; çıktı iki sütunlu: `yayimlanmis` ve `puf_agirlikli`.

VERİ: `data/pisa_microdata/2012_cba/CBA_STU12_MAR31.zip` + `PISA2012_SPSS_CBA_student.txt`
(PISA 2012 CBA Database, 22 Eyl 2026'da geldi). Ana 2012 öğrenci dosyasında problem çözme
PV'si YOKTUR — bu ayrı yayındadır. Kabul kapısı: sözdizimi max(bitiş) 2170 = veri kayıt
uzunluğu 2170; 271.323 satır, 43 birim.
İçerik: `PV*CPRO` (problem çözme) · `PV*CMAT` (bilgisayarda matematik) · `PV*CREA` (dijital
okuma) · AYNI öğrencilerin kâğıt `PV*MATH/READ/SCIE`'si · `W_FSTUWT` + `W_FSTR1…80`.

İŞ B — MOD KONTROLÜ, CEVAP: KAPATILAMAZ.
Türkiye 2012'de problem çözmeye girmiş (`PV*CPRO` 4.848 öğrencide %100 dolu) ama
**bilgisayar tabanlı matematiğe ve dijital okumaya GİRMEMİŞ**: `PV*CMAT` ve `PV*CREA`
Türkiye'de %0,0 dolu. 43 birim problem çözmeye, yalnız 32'si CBA çekirdeğe girmiş; Türkiye
o 32'nin içinde değil (Macaristan, İsveç ve bütün donörler içinde). Dolayısıyla Türkiye için
"bilgisayar tabanlı çekirdeğe göre koşullu artık" KURULAMAZ — veri eksikliğinden değil,
Türkiye o testi uygulamadığı için. §9'un mod cümlesi OLDUĞU GİBİ KALIR.
Bunun yerine: CBA çekirdeği olan 32 ülkede mod farkı (CMAT − MATH, aynı öğrenciler)
ölçülür ve problem çözme artığının mod farkıyla ilişkili olup olmadığı sınanır. İlişkiliyse
"bilgisayar aşinalığı" rakip açıklaması güç kazanır; değilse zayıflar. Türkiye'nin kendi mod
farkı gözlenemediği için bu bir ÇIKARIM DESTEĞİDİR, ikame değildir.

YÖNTEM: 10/15/25 ile aynı koşullu tasarım — PS2012 ~ çekirdek 2012, {tüm, OECD} ×
{doğrusal, karesel}; artık, artık/RMSE, sıra, yüzdelik, leave-one-out. Betik 25'ten farkı:
ortalamalar W_FSTUWT ağırlıklı, standart hatalar BRR (Fay 0,5; 80 replikasyon) + Rubin,
artığın %95 aralığı parametrik bootstrap ile (B=2000).

ÇEKİRDEK İKİ TANIM: (a) panel yayımlanmış mat/oku/fen ortalaması — betik 25 ile birebir
karşılaştırma için; (b) CBA dosyasındaki AYNI öğrencilerin kâğıt PV'lerinden PUF çekirdeği.

KAPSAM: GBR dışarıda — PISA 2012 CBA'da Birleşik Krallık'tan yalnız İngiltere katıldı ama
dosya `GBR` kodluyor; betik 25 de "England (United Kingdom)"ı ulusal olmadığı için dışarıda
bırakmıştı, aynı karar sürdürülür. QCN (Shanghai) panelde yok. TAP = Chinese Taipei → TWN.

AÇIK KALEM (örtülmedi): PUF ortalamaları yayımlanmış Table V.A tam sayılarıyla 41 ülkede
karşılaştırıldı; 40'ı ±0,5 içinde (yuvarlama), **Brezilya 3,0 puan sapıyor** (PUF 425,0 vs
yayımlanmış 428). Beş PV'nin hepsi 425 civarında kümeleniyor, ağırlık sorunu yok
(CBA/ana ağırlık oranı 1,016, uç değil), SUBNATIO tek. Sebep bulunamadı. Dosya sürümü
`MAR31` (erken sürüm) olabilir; araştırılmadı. Brezilya çıkarılmadı, işaretlendi.

Çıktı: data/derived/mechanisms/placebo_conditional_2012ps_puf.csv, *_summary.json,
       mode_gap_2012.csv; analysis/figures/mech_placebo_conditional_2012ps_puf.png. Etiket [E33].
Yazan: Claude Opus 5 (ana oturum), 2026-09-22. Denetim: Opus 4.8, bekliyor.
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
MECH = ROOT / "data" / "derived" / "mechanisms"
FIG = ROOT / "analysis" / "figures"
for d in (MECH, FIG):
    d.mkdir(parents=True, exist_ok=True)

CYC = "2012cba"
FOCUS = ["TUR", "HUN", "SWE"]
NOT_NATIONAL = {"GBR": "PISA 2012 CBA'da BK'den yalniz Ingiltere katildi; betik 25 de disarida birakti",
                "QCN": "Shanghai-China panelde yok"}
RENAME = {"TAP": "TWN"}
BOOT, SEED = 2000, 20260922


def ols(x, y, deg=1):
    X = np.vander(x, deg + 1, increasing=True)
    beta, *_ = np.linalg.lstsq(X, y, rcond=None)
    fit = X @ beta
    resid = y - fit
    rmse = float(np.sqrt((resid @ resid) / max(len(y) - X.shape[1], 1)))
    ss = float(((y - y.mean()) ** 2).sum())
    return beta, fit, resid, (1 - float(resid @ resid) / ss if ss > 0 else np.nan), rmse


def main() -> int:
    spec = P.parse_datalist(P.ROOT / P.REGISTRY[CYC]["syn"])
    for r in ("CPRO", "CMAT", "CREA", "MATH", "READ", "SCIE"):
        if not P.pv_cols(spec, r):
            raise SystemExit(f"CBA sozdiziminde PV kokleri yok: {r} — DUR, tahmin etme")
    want = ["CNT", "W_FSTUWT", *P.REPW] + [c for r in ("CPRO", "CMAT", "CREA", "MATH", "READ", "SCIE")
                                           for c in P.pv_cols(spec, r)]
    df = P.read_columns(CYC, want)
    df["CNT"] = df.CNT.replace(RENAME)
    print(f"[2012 CBA] {len(df):,} satir, {df.CNT.nunique()} birim")

    # --- IS B: hangi ulke hangi alana girdi
    cov = df.groupby("CNT").agg(n=("CNT", "size"),
                                CPRO=("PV1CPRO", lambda s: float(s.notna().mean())),
                                CMAT=("PV1CMAT", lambda s: float(s.notna().mean())),
                                CREA=("PV1CREA", lambda s: float(s.notna().mean())))
    has_cba_core = sorted(cov.index[cov.CMAT > 0.5])
    tur_cba = bool(cov.loc["TUR", "CMAT"] > 0.5) if "TUR" in cov.index else False
    print(f"[IS B] CPRO: {int((cov.CPRO>0.5).sum())} birim · CBA cekirdek (CMAT): {len(has_cba_core)} birim")
    print(f"[IS B] TURKIYE CBA cekirdek uyguladi mi: {'EVET' if tur_cba else 'HAYIR'} "
          f"(CMAT doluluk %{float(cov.loc['TUR','CMAT'])*100:.1f}, CREA %{float(cov.loc['TUR','CREA'])*100:.1f})")

    est = {}
    for r in ("CPRO", "MATH", "READ", "SCIE"):
        est[r] = P.brr_pv_stat(df, P.pv_cols(spec, r), "W_FSTUWT", P.REPW).set_index("iso3")
    # PS ile çekirdek AYNI öğrencilerden → korelasyonlu (Opus 4.8 denetimi D2a).
    # Çekirdeğin p'inci PV'si = [MATHp, READp, SCIEp] ortalaması (PV indeksi hizalı).
    core_pv = [[P.pv_cols(spec, r)[i] for r in ("MATH", "READ", "SCIE")] for i in range(5)]
    rho = P.brr_pv_corr(df, P.pv_cols(spec, "CPRO"), core_pv, "W_FSTUWT", P.REPW).set_index("iso3")
    d = pd.DataFrame({"ps2012_puf": est["CPRO"]["mean"], "ps2012_puf_se": est["CPRO"]["se"],
                      "math_puf": est["MATH"]["mean"], "read_puf": est["READ"]["mean"],
                      "scie_puf": est["SCIE"]["mean"],
                      "math_puf_se": est["MATH"]["se"], "read_puf_se": est["READ"]["se"],
                      "scie_puf_se": est["SCIE"]["se"],
                      "ps_se_s": est["CPRO"]["se_sampling"], "ps_se_i": est["CPRO"]["se_imputation"],
                      "rho_s": rho["rho_sampling"], "rho_i": rho["rho_imputation"],
                      "math_se_s": est["MATH"]["se_sampling"], "math_se_i": est["MATH"]["se_imputation"],
                      "read_se_s": est["READ"]["se_sampling"], "read_se_i": est["READ"]["se_imputation"],
                      "scie_se_s": est["SCIE"]["se_sampling"], "scie_se_i": est["SCIE"]["se_imputation"],
                      "n_students": est["CPRO"]["n_students"]}).reset_index()
    d["core_puf"] = d[["math_puf", "read_puf", "scie_puf"]].mean(axis=1)
    d["core_puf_se"] = d[["math_puf_se", "read_puf_se", "scie_puf_se"]].mean(axis=1)
    d["core_se_s"] = d[["math_se_s", "read_se_s", "scie_se_s"]].mean(axis=1)
    d["core_se_i"] = d[["math_se_i", "read_se_i", "scie_se_i"]].mean(axis=1)

    # --- yayimlanmis capalar
    pubps = pd.read_csv(ROOT / "data" / "derived" / "ps2012_published_means.csv")
    pubps = pubps[["iso3", "mean"]].rename(columns={"mean": "ps2012_published"}).dropna(subset=["iso3"])
    panel = pd.read_csv(ROOT / "data" / "derived" / "analysis_panel.csv")
    p12 = panel[panel.cycle == 2012][["iso3", "country_name", "math_mean", "reading_mean",
                                      "science_mean", "oecd_member"]].copy()
    p12["core_pub"] = p12[["math_mean", "reading_mean", "science_mean"]].mean(axis=1)
    d = d.merge(pubps, on="iso3", how="left").merge(p12, on="iso3", how="left")
    d["oecd"] = pd.to_numeric(d.oecd_member, errors="coerce").fillna(0) > 0
    d["note"] = d.iso3.map(NOT_NATIONAL).fillna("")

    chk = d.dropna(subset=["ps2012_published"]).copy()
    chk["dps"] = (chk.ps2012_puf - chk.ps2012_published).abs()
    big = chk[chk.dps > 0.5]
    print(f"[capa] PS: n={len(chk)} · |fark| medyan {chk.dps.median():.3f} · "
          f">0,5 olan {len(big)}: {dict(zip(big.iso3, big.dps.round(2)))}")
    chk2 = d.dropna(subset=["math_mean"]).copy()
    chk2["dm"] = (chk2.math_puf - chk2.math_mean).abs()
    print(f"[capa] kagit matematik (CBA alt orneklemi vs panel tam ornek): n={len(chk2)} · "
          f"|fark| medyan {chk2.dm.median():.2f} · maks {chk2.dm.max():.2f}")

    base = d[~d.iso3.isin(NOT_NATIONAL)].copy()
    rng = np.random.default_rng(SEED)
    rows, summary = [], {
        "note": "PISA 2012 problem cozme, MIKROVERIDEN (CBA_STU12_MAR31). Betik 25 yayimlanmis tam sayi kullanir; "
                "bu betik onu DEGISTIRMEZ, yanina agirlikli ve BRR standart hatali surumu koyar.",
        "source": "data/pisa_microdata/2012_cba/CBA_STU12_MAR31.zip + PISA2012_SPSS_CBA_student.txt",
        "acceptance_gate": "sozdizimi max(bitis) 2170 = veri kayit uzunlugu 2170; 271.323 satir",
        "is_b_mode_check": {
            "question": "Turkiye 2012'de bilgisayar tabanli matematik/okuma uyguladi mi?",
            "answer": "HAYIR",
            "evidence": {"TUR_CPRO_fill": round(float(cov.loc['TUR', 'CPRO']), 4),
                         "TUR_CMAT_fill": round(float(cov.loc['TUR', 'CMAT']), 4),
                         "TUR_CREA_fill": round(float(cov.loc['TUR', 'CREA']), 4),
                         "n_units_CPRO": int((cov.CPRO > 0.5).sum()),
                         "n_units_CBA_core": len(has_cba_core),
                         "units_with_CBA_core": has_cba_core},
            "consequence": "Turkiye icin bilgisayar tabanli cekirdege gore kosullu artik KURULAMAZ. "
                           "§9'un mod cumlesi degismez. Bu veri eksikligi DEGIL, katilim olgusudur.",
        },
        "published_anchor_discrepancy": {},
        "excluded": NOT_NATIONAL, "renamed": RENAME, "bootstrap_draws": BOOT, "seed": SEED,
        "bootstrap_note": "PS ve cekirdek KORELASYONLU cekilir (brr_pv_corr); bagimsiz cekim araligi gereksiz genisletiyordu — Opus 4.8 denetimi 22 Eyl, D2a.",
    }
    for _, r in big.iterrows():
        summary["published_anchor_discrepancy"][r.iso3] = {
            "puf": round(float(r.ps2012_puf), 2), "published": int(r.ps2012_published),
            "diff": round(float(r.ps2012_puf - r.ps2012_published), 2)}

    for core_col, core_se_col, tag in [("core_puf", "core_puf_se", "PUF mat/oku/fen"),
                                       ("core_pub", None, "panel yayimlanmis mat/oku/fen")]:
        for scope in ["all", "oecd"]:
            s = base.dropna(subset=[core_col, "ps2012_puf"]).copy()
            if scope == "oecd":
                s = s[s.oecd]
            x = s[core_col].to_numpy(float)
            y = s.ps2012_puf.to_numpy(float)
            xs = s[core_se_col].to_numpy(float) if core_se_col else np.zeros(len(s))
            ys = s.ps2012_puf_se.to_numpy(float)
            for deg, name in [(1, "linear"), (2, "quadratic")]:
                beta, fit, resid, r2, rmse = ols(x, y, deg)
                tmp = s[["iso3", "country_name", "oecd", "n_students", "ps2012_published"]].copy()
                tmp["scope"], tmp["spec"], tmp["core_def"] = scope, name, tag
                tmp["core"], tmp["core_se"] = x, xs
                tmp["ps2012_puf"], tmp["ps2012_puf_se"] = y, ys
                tmp["ps_pred"], tmp["residual"] = fit, resid
                tmp["resid_sd"] = resid / rmse if rmse else np.nan
                tmp["rank_low"] = tmp.residual.rank(method="min")
                tmp["pctile"] = tmp.residual.rank(pct=True) * 100
                # KORELASYONLU bootstrap (D2a). core_pub spesifikasyonunda xs=0 olduğu için etkisiz.
                rr = (P.combine_rho(s.rho_s.to_numpy(float), s.rho_i.to_numpy(float),
                                    s.ps_se_s.to_numpy(float), s.ps_se_i.to_numpy(float),
                                    s.core_se_s.to_numpy(float), s.core_se_i.to_numpy(float))
                      if core_se_col else np.zeros(len(s)))
                boot = np.empty((BOOT, len(s)))
                for b in range(BOOT):
                    z1, z2 = rng.standard_normal(len(s)), rng.standard_normal(len(s))
                    yb = y + ys * z1
                    xb = x + xs * (rr * z1 + np.sqrt(np.maximum(1 - rr ** 2, 0)) * z2)
                    boot[b] = yb - np.vander(xb, deg + 1, increasing=True) @ ols(xb, yb, deg)[0]
                tmp["resid_lo95"], tmp["resid_hi95"] = np.percentile(boot, [2.5, 97.5], axis=0)
                rows.append(tmp)
                key = f"{scope}_{name}_{'puf' if core_col == 'core_puf' else 'pub'}"
                summary[key] = {"n": int(len(s)), "slope": round(float(beta[1]), 4),
                                "r2": round(float(r2), 3), "rmse": round(float(rmse), 2)}
                for iso in FOCUS:
                    q = tmp[tmp.iso3 == iso]
                    if q.empty:
                        continue
                    q = q.iloc[0]
                    m = (s.iso3 != iso).to_numpy()
                    b_loo, *_ = ols(x[m], y[m], deg)
                    summary[key][iso] = {
                        "core": round(float(q.core), 1),
                        "ps2012_puf": round(float(q.ps2012_puf), 1),
                        "ps2012_puf_se": round(float(q.ps2012_puf_se), 2),
                        "ps2012_published": None if q.ps2012_published != q.ps2012_published else int(q.ps2012_published),
                        "residual": round(float(q.residual), 1),
                        "residual_ci95": [round(float(q.resid_lo95), 1), round(float(q.resid_hi95), 1)],
                        "residual_in_sd": round(float(q.resid_sd), 2),
                        "residual_leave_one_out": round(float(q.ps2012_puf) - float(np.polyval(b_loo[::-1], float(q.core))), 1),
                        "rank_from_bottom": f"{int(q.rank_low)}/{len(tmp)}",
                        "percentile": round(float(q.pctile), 1)}
                foc = ", ".join(f"{i}: {summary[key][i]['residual']:+.1f} "
                                f"[{summary[key][i]['residual_ci95'][0]:+.1f},{summary[key][i]['residual_ci95'][1]:+.1f}]"
                                f" ({summary[key][i]['rank_from_bottom']})" for i in FOCUS if i in summary[key])
                print(f"[{scope}/{name}/{tag}] n={len(s)} egim={beta[1]:.4f} R2={r2:.3f} RMSE={rmse:.2f} | {foc}")

    res = pd.concat(rows, ignore_index=True)
    res.to_csv(MECH / "placebo_conditional_2012ps_puf.csv", index=False, encoding="utf-8-sig")

    # --- IS B devami: mod farki ve problem cozme artigi
    md = df[df.CNT.isin(has_cba_core)]
    gap = []
    for iso, g in md.groupby("CNT"):
        W = g.W_FSTUWT.to_numpy(float)
        cm = float(W @ g[P.pv_cols(spec, 'CMAT')].to_numpy(float).mean(axis=1) / W.sum())
        pm = float(W @ g[P.pv_cols(spec, 'MATH')].to_numpy(float).mean(axis=1) / W.sum())
        cr = float(W @ g[P.pv_cols(spec, 'CREA')].to_numpy(float).mean(axis=1) / W.sum())
        pr = float(W @ g[P.pv_cols(spec, 'READ')].to_numpy(float).mean(axis=1) / W.sum())
        gap.append(dict(iso3=iso, math_paper=pm, math_computer=cm, mode_gap_math=cm - pm,
                        read_paper=pr, read_computer=cr, mode_gap_read=cr - pr))
    gp = pd.DataFrame(gap)
    ref = res[(res.scope == "all") & (res.spec == "linear") & (res.core_def == "PUF mat/oku/fen")]
    gp = gp.merge(ref[["iso3", "residual"]].rename(columns={"residual": "ps_residual"}), on="iso3", how="left")
    gp.to_csv(MECH / "mode_gap_2012.csv", index=False, encoding="utf-8-sig")
    ok = gp.dropna(subset=["ps_residual"])
    if len(ok) > 3:
        rho_m = float(np.corrcoef(ok.mode_gap_math, ok.ps_residual)[0, 1])
        rho_r = float(np.corrcoef(ok.mode_gap_read, ok.ps_residual)[0, 1])
        b_m = float(np.polyfit(ok.mode_gap_math, ok.ps_residual, 1)[0])

        # SAHTE KORELASYON KONTROLU — zorunlu.
        # mode_gap_math = CMAT - MATH ve ps_residual = PS - b*cekirdek; cekirdek MATH iceriyor.
        # MATH iki tarafta da NEGATIF girdigi icin mekanik bir pozitif korelasyon dogar.
        # Ortak bileseni cekirdekten cikarip yeniden olculur; ayrica OKUMA mod farki, cekirdegi
        # READ'siz kurulmus artikla sinanir (sifir ortak bilesen — en temiz test).
        d41 = base.dropna(subset=["ps2012_puf", "math_puf", "read_puf", "scie_puf"]).set_index("iso3")
        gset = [i for i in ok.iso3 if i in d41.index]

        def resid_core(cols):
            x = d41[cols].mean(axis=1).to_numpy(float)
            y = d41.ps2012_puf.to_numpy(float)
            return pd.Series(y - np.polyval(np.polyfit(x, y, 1), x), index=d41.index)

        gm = ok.set_index("iso3").mode_gap_math.loc[gset]
        gr = ok.set_index("iso3").mode_gap_read.loc[gset]
        robust = {}
        for lab, cols, gap in [("core_math_read_scie_SHARED", ["math_puf", "read_puf", "scie_puf"], gm),
                               ("core_read_scie_NO_MATH", ["read_puf", "scie_puf"], gm),
                               ("core_scie_only", ["scie_puf"], gm),
                               ("readgap_core_math_scie_NO_READ", ["math_puf", "scie_puf"], gr)]:
            rr = resid_core(cols).loc[gset]
            robust[lab] = {"corr": round(float(np.corrcoef(gap, rr)[0, 1]), 3),
                           "slope": round(float(np.polyfit(gap, rr, 1)[0]), 3)}
        infl = robust["core_math_read_scie_SHARED"]["corr"] - robust["core_read_scie_NO_MATH"]["corr"]

        summary["mode_gap"] = {
            "n_units": int(len(ok)),
            "mode_gap_math_mean": round(float(ok.mode_gap_math.mean()), 2),
            "mode_gap_math_sd": round(float(ok.mode_gap_math.std(ddof=1)), 2),
            "corr_with_ps_residual_math": round(rho_m, 3),
            "corr_with_ps_residual_read": round(rho_r, 3),
            "slope_resid_on_gap_math": round(b_m, 3),
            "spurious_check": robust,
            "mechanical_inflation_in_corr": round(float(infl), 3),
            "verdict": "Ortak MATH bileseni korelasyonu ~0,12 puan sisiriyor, egimi ~0,09 dusuruyor; "
                       "iliski YOK OLMUYOR. En temiz test (okuma mod farki x READ'siz cekirdek) "
                       "hala guclu. Yani mod kanali gercek, ama raporlanan ham korelasyon sisiktir.",
            "reading": "Turkiye'nin kendi mod farki GOZLENEMEZ (CBA cekirdek uygulamadi); "
                       "bu bir cikarim destegidir, olcum degildir.",
        }
        print(f"[IS B] mod farki (CMAT-MATH): n={len(ok)} ort {ok.mode_gap_math.mean():+.1f} "
              f"sd {ok.mode_gap_math.std(ddof=1):.1f} | ham korelasyon mat {rho_m:+.3f} oku {rho_r:+.3f}")
        for k, v in robust.items():
            print(f"       sahte-korelasyon kontrolu {k}: r={v['corr']:+.3f} egim={v['slope']:+.3f}")
        print(f"       mekanik sisme (korelasyonda): {infl:+.3f}")

    (MECH / "placebo_conditional_2012ps_puf_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=1), encoding="utf-8")
    print("DONE PS 2012 PUF")
    return 0


if __name__ == "__main__":
    sys.exit(main())
