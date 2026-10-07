# -*- coding: utf-8 -*-
"""
32 — ÖN DÖNEM: 2003–2012 Türkiye ve donör havuzu, mikroveriden (§10(4); §9'un en zayıf noktası).

Üç soru, üçü de mikroveriden:
  (1) Ağırlıklı ülke ortalaması + BRR standart hatası, 2003/2006/2009/2012. Yayımlanmış
      panel değerleriyle karşılaştırılır; uyuşmazsa DURULUR (panel kanoniktir).
  (2) ESCS sabit tutulduğunda 2003–2012 eğimi ne oluyor? Tek ölçeğe getirilmiş trend-ESCS
      (`trend_escs_SPSS.zip`) öğrenci düzeyinde birleştirilir; ülke içi ağırlıklı ESCS
      eğimi b tahmin edilir ve ortalama sabit bir referans ESCS'ye taşınır:
          adj_mean_t = mean_t + b_t * (e_ref - mean_escs_t),   e_ref = ülkenin 2003 ESCS'si
      Belirsizlik BRR + Rubin ile taşınır (81 ağırlık × 5 PV, kapalı form ağırlıklı OLS).
  (3) Spaull/Lee SABİT KOHORT PAYI sınırı: her döngüde kapsanan 15 yaş nüfus payı farklı
      (Türkiye 2006'da %46,7 → 2012'de %68,4). En düşük pay esas alınıp her döngüde
      ağırlıklı dağılımın ÜST s_t = C_min/C_t payı tutulur (dışarıda kalanların alt kuyrukta
      olduğu varsayımı — bu bir SINIR, nokta tahmin değil). Gözlenen eğim ile sabit-kohort
      eğimi arasındaki fark, eğimin kapsam genişlemesinden gelen kısmının sınırıdır.

ÖLÇÜLMÜŞ UYARI — İKİ ESCS DOSYASI AYNI ÖLÇEKTE DEĞİL (bu oturum, 22 Eyl):
`logs/YENI_INDIRMELER_2026-09-22.md` "escs_trend.zip ile birlikte 2000–2022 tek ESCS
ölçeğinde" diyor. Değil. 2012 her iki dosyada da var; 436.947 ortak öğrencide korelasyon
0,9707, |fark| medyanı 0,196 SD, doğrusal uyum R² yalnız 0,942 (saf yeniden ölçekleme
olsaydı ~1 olurdu) ve ülke kesimleri −0,484…+0,085 arasında değişiyor (Türkiye −0,217).
`trend_escs_SPSS.zip` eski, `escs_trend.zip` PISA 2022 ölçeğine ait iki AYRI kalibrasyon.
Bu betik 2003–2012 için YALNIZ `trend_escs_SPSS.zip` kullanır — tek dosya, kendi içinde
tutarlı. İki dosya uç uca eklenmez.

KAPSAM ENDEKSİ KAYNAĞI: panelin `coverage_index3` sütunu 2006/2009/2012 için dolu, 2003
için 37 satırın hepsinde BOŞ. 2003 değerleri **PISA 2003 Technical Report**'tan alındı
(`docs/oecd_technical_reports/2003/9789264010543-en.pdf`, Böl. 12 "Sampling Outcomes",
Table 12.1, pdfplumber sayfa dizini
168–169). O rapor tanımı da veriyor:

    "Index 3: Coverage of the national 15-year-old population, calculated by P/2[a]."
    2[a] = "the entire population of 15-year-olds in each country (enrolled and not enrolled)"
    P    = "the weighted estimate of eligible non-excluded 15-year-olds from the student sample"

yani panelin 2006+ tanımıyla AYNI. (Sonuçlar cildinin Annex A3 Table A3.1'i metin olarak
çıkarıldığında sütunlar kayıyor ve Türkiye için yanlışlıkla 0,54 okunuyor; doğrusu 0,36.)

Değerler kendi ağırlıklarımızla ÇAPRAZ DOĞRULANDI: P = W_FSTUWT toplamı. Türkiye 2003 için
mikroveriden 481.279 çıkıyor, Table 12.1'in P sütunuyla birime kadar aynı;
481.279 / 1.351.492 = 0,356 → basılı 0,36. Sekiz odak ülkenin hepsinde P/2[a] basılı CI3'ü
veriyor. Bu yüzden sınır TAM 2003–2012 penceresinde kurulabiliyor ve Türkiye'nin en düşük
kapsamı 2006 değil **2003 (0,36)**.

Çıktı: data/derived/ontrend/{levels_brr.csv, escs_adjusted.csv, coverage_bound.csv, summary.json}
       V5_ONTREND_SONUC_2026-09-22.md (ayrı adımda). Etiket [E32].
Yazan: Claude Opus 5 (ana oturum), 2026-09-22 — kod Fable 5.1'e gidecekti, Fable kullanım
limiti nedeniyle iki ajan koşumu da düştü. Denetim: Opus 4.8, bekliyor.
"""
from __future__ import annotations

import json
import sys
import tempfile
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _pisa_puf as P  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "derived" / "ontrend"
OUT.mkdir(parents=True, exist_ok=True)
ESCS_ZIP = ROOT / "data" / "pisa_microdata" / "escs_trend" / "trend_escs_SPSS.zip"

CYCLES = [2003, 2006, 2009, 2012]
DONORS = ["BEL", "CHE", "FRA", "ISL", "JPN"]          # donors_by_cell.csv, taban hücre S0
FOCUS = ["TUR"] + DONORS + ["HUN", "SWE"]
DOMAINS = ["MATH", "READ", "SCIE"]
# 2003 Coverage Index 3 — PISA 2003 Technical Report Table 12.1 (9789264010543-en.pdf).
# Her değer P/2[a] ile çapraz doğrulandı; P = bu projenin W_FSTUWT toplamı (docstring).
CI3_2003 = {"TUR": 0.36, "HUN": 0.83, "SWE": 0.98, "BEL": 0.93, "CHE": 1.04,
            "FRA": 0.91, "ISL": 0.94, "JPN": 0.91}
CI3_2003_SOURCE = ("PISA 2003 Technical Report (docs/oecd_technical_reports/2003/9789264010543-en.pdf), "
                   "Bol. 12 Sampling Outcomes, "
                   "Table 12.1; tanim: 'Index 3: Coverage of the national 15-year-old population, "
                   "calculated by P/2[a]'. Her deger P/2[a] ile capraz dogrulandi (P = W_FSTUWT toplami).")


def wmean(w, x):
    return float(w @ x / w.sum())


def wslope(w, x, y):
    """Ağırlıklı tek değişkenli OLS eğimi (kapalı form)."""
    sw = w.sum()
    mx, my = w @ x / sw, w @ y / sw
    vx = w @ (x - mx) ** 2
    return float((w @ ((x - mx) * (y - my))) / vx) if vx > 0 else np.nan


def rubin(theta, v_samp_per_pv):
    """theta: (M,) PV kestirimleri; v_samp_per_pv: (M,) örnekleme varyansları -> (kestirim, SE)."""
    M = len(theta)
    est = float(theta.mean())
    v_s = float(np.mean(v_samp_per_pv))
    v_i = (1.0 + 1.0 / M) * float(((theta - theta.mean()) ** 2).sum()) / (M - 1)
    return est, float(np.sqrt(v_s + v_i))


def brr_over(fn, X, W, R, fay=0.5):
    """fn(weight_vector, pv_column)->skaler; her PV ve her replikasyon için uygular, Rubin'le birleştirir."""
    G, M = R.shape[1], X.shape[1]
    mult = 1.0 / (G * (1.0 - fay) ** 2)
    theta = np.array([fn(W, X[:, p]) for p in range(M)])
    v = np.empty(M)
    for p in range(M):
        rep = np.array([fn(R[:, r], X[:, p]) for r in range(G)])
        v[p] = mult * ((rep - theta[p]) ** 2).sum()
    return rubin(theta, v)


def top_share_mean(w, x, share):
    """Ağırlıklı dağılımın ÜST `share` payının ortalaması (sınırda kesirli ağırlık)."""
    if share >= 1.0:
        return wmean(w, x)
    o = np.argsort(-x)
    ws, xs = w[o], x[o]
    cum = np.cumsum(ws)
    target = share * ws.sum()
    k = int(np.searchsorted(cum, target))
    if k == 0:
        return float(xs[0])
    keep = ws[:k].copy()
    rem = target - cum[k - 1]
    if k < len(ws) and rem > 0:
        keep = np.append(keep, rem)
        return float(keep @ xs[:k + 1] / keep.sum())
    return float(keep @ xs[:k] / keep.sum())


def load_escs_trend():
    """trend_escs_SPSS.zip -> {yıl: DataFrame[cnt, schoolid, stidstd, escs_trend]}."""
    import pyreadstat
    tmp = tempfile.mkdtemp()
    out = {}
    with zipfile.ZipFile(ESCS_ZIP) as z:
        for y in CYCLES:
            name = f"{y}_escs.sav"
            if name not in z.namelist():
                print(f"  [ESCS] {name} zip'te yok — atlandi")
                continue
            d, _ = pyreadstat.read_sav(z.extract(name, tmp))
            d.columns = [c.lower() for c in d.columns]
            out[y] = d[["cnt", "schoolid", "stidstd", "escs_trend"]]
    return out


def main() -> int:
    panel = pd.read_csv(ROOT / "data" / "derived" / "analysis_panel.csv")
    escs = load_escs_trend()
    print(f"[ESCS trend] donguler: {sorted(escs)} (kaynak: trend_escs_SPSS.zip, tek kalibrasyon)")

    levels, adjusted, bounds = [], [], []
    ref_escs: dict[str, float] = {}

    for cycle in CYCLES:
        spec = P.parse_datalist(P.ROOT / P.REGISTRY[cycle]["syn"])
        roots = [r for r in DOMAINS if P.pv_cols(spec, r)]
        want = ["CNT", "SCHOOLID", "STIDSTD", "W_FSTUWT", *P.REPW] + [c for r in roots for c in P.pv_cols(spec, r)]
        df = P.read_columns(cycle, want)
        df = df[df.CNT.isin(FOCUS)].copy()
        print(f"[{cycle}] odak {df.CNT.nunique()} ulke, {len(df):,} ogrenci")

        et = escs.get(cycle)
        if et is not None:
            df = df.merge(et.rename(columns={"cnt": "CNT", "schoolid": "SCHOOLID", "stidstd": "STIDSTD"}),
                          on=["CNT", "SCHOOLID", "STIDSTD"], how="left")
            hit = df.groupby("CNT").escs_trend.apply(lambda s: float(s.notna().mean()))
            print(f"   ESCS eslesme orani: {', '.join(f'{k} {v:.1%}' for k, v in hit.items())}")
        else:
            df["escs_trend"] = np.nan

        pub = panel[panel.cycle == cycle].set_index("iso3")
        cov = pub.coverage_index3

        for iso, g in df.groupby("CNT"):
            W = g.W_FSTUWT.to_numpy(float)
            R = g[P.REPW].to_numpy(float)
            for r in roots:
                cols = P.pv_cols(spec, r)
                X = g[cols].to_numpy(float)
                est, se = brr_over(wmean, X, W, R)
                pm = float(pub.loc[iso, P.PANEL_FIELD[r][0]]) if iso in pub.index else np.nan
                ps = float(pub.loc[iso, P.PANEL_FIELD[r][1]]) if iso in pub.index else np.nan
                levels.append(dict(cycle=cycle, iso3=iso, domain=r, puf_mean=est, puf_se=se,
                                   pub_mean=pm, pub_se=ps, fark=est - pm if pm == pm else np.nan,
                                   n_students=len(g), coverage_index3=float(cov.get(iso, np.nan))))

                # --- (2) ESCS sabitlenmiş ortalama
                m = g.escs_trend.notna().to_numpy()
                if m.sum() >= 100:
                    E = g.escs_trend.to_numpy(float)[m]
                    Wm, Rm, Xm = W[m], R[m], X[m]
                    b_est, b_se = brr_over(lambda w, y: wslope(w, E, y), Xm, Wm, Rm)
                    # ESCS ortalaması artırılmış değer DEĞİL: atama varyansı yok, yalnız BRR.
                    e_mean = wmean(Wm, E)
                    e_se = float(np.sqrt(sum((wmean(Rm[:, r], E) - e_mean) ** 2
                                             for r in range(Rm.shape[1])) / (Rm.shape[1] * 0.25)))
                    if cycle == 2003:
                        ref_escs.setdefault(iso, e_mean)
                    e_ref = ref_escs.get(iso, np.nan)
                    adj = (lambda w, y: wmean(w, y) + wslope(w, E, y) * (e_ref - wmean(w, E))) \
                        if e_ref == e_ref else None
                    if adj is not None:
                        a_est, a_se = brr_over(adj, Xm, Wm, Rm)
                    else:
                        a_est, a_se = np.nan, np.nan
                    adjusted.append(dict(cycle=cycle, iso3=iso, domain=r, escs_mean=e_mean, escs_se=e_se,
                                         escs_slope=b_est, escs_slope_se=b_se, escs_ref=e_ref,
                                         obs_mean=est, adj_mean=a_est, adj_se=a_se,
                                         n_matched=int(m.sum()), match_rate=float(m.mean())))

                # --- (3) Sabit kohort payı sınırı (kapsam endeksi olan döngüler)
                c_t = CI3_2003.get(iso, np.nan) if cycle == 2003 else float(cov.get(iso, np.nan))
                if c_t == c_t:
                    bounds.append(dict(cycle=cycle, iso3=iso, domain=r, coverage_index3=c_t,
                                       obs_mean=est, __store=(X, W, R)))
        del df

    lv = pd.DataFrame(levels)
    bad = lv.dropna(subset=["fark"])
    bad = bad[bad.fark.abs() > 0.01]
    if len(bad):
        print(bad.to_string(index=False))
        raise SystemExit("DUR: PUF ortalamalari panelle uyusmuyor (panel kanoniktir)")
    print(f"[panel kontrolu] {int(lv.fark.notna().sum())} hucre karsilastirildi, "
          f"maks |fark| {lv.fark.abs().max():.4f} — gecti")
    lv.to_csv(OUT / "levels_brr.csv", index=False, encoding="utf-8-sig")

    # sabit kohort: ülke başına C_min (kapsam endeksi olan döngülerde)
    bd = pd.DataFrame([{k: v for k, v in b.items() if k != "__store"} for b in bounds])
    store = {(b["cycle"], b["iso3"], b["domain"]): b["__store"] for b in bounds}
    cmin = bd.groupby("iso3").coverage_index3.min()
    rows = []
    for _, r in bd.iterrows():
        X, W, R = store[(r.cycle, r.iso3, r.domain)]
        share = float(cmin[r.iso3]) / float(r.coverage_index3)
        est, se = brr_over(lambda w, y: top_share_mean(w, y, share), X, W, R)
        rows.append(dict(cycle=int(r.cycle), iso3=r.iso3, domain=r.domain,
                         coverage_index3=r.coverage_index3, c_min=float(cmin[r.iso3]),
                         retained_share=share, obs_mean=r.obs_mean,
                         const_cohort_mean=est, const_cohort_se=se,
                         gap=est - r.obs_mean))
    cb = pd.DataFrame(rows)
    cb.to_csv(OUT / "coverage_bound.csv", index=False, encoding="utf-8-sig")
    ad = pd.DataFrame(adjusted)
    ad.to_csv(OUT / "escs_adjusted.csv", index=False, encoding="utf-8-sig")

    def slope(frame, col, iso, dom, cycles):
        d = frame[(frame.iso3 == iso) & (frame.domain == dom) & (frame.cycle.isin(cycles))]
        d = d.dropna(subset=[col]).sort_values("cycle")
        if len(d) < 2:
            return np.nan, np.nan
        x, y = d.cycle.to_numpy(float), d[col].to_numpy(float)
        b = np.polyfit(x, y, 1)[0]
        return float(b), float(y[-1] - y[0])

    summary = {
        "engine": "analysis/_pisa_puf.py — BRR (Fay 0,5; 80 replikasyon) + Rubin; 587 hucrede "
                  "yayimlanmis ortalama ve SE birebir yeniden uretildi (maks sapma 0,0005)",
        "escs_source": "trend_escs_SPSS.zip (2000-2012, TEK kalibrasyon). escs_trend.zip ile "
                       "BIRLESTIRILMEDI: 2012 ortusmesinde R2=0,942, |fark| medyani 0,196 SD, "
                       "ulke kesimleri -0,484..+0,085 (TUR -0,217) — iki ayri olcek.",
        "coverage_source": "panel coverage_index3 (2006/2009/2012) + 2003 icin PISA 2003 Technical Report Table 12.1.",
        "ci3_2003_source": CI3_2003_SOURCE,
        "ci3_2003_values": CI3_2003,
        "donor_pool": DONORS, "donor_source": "data/derived/donor_ablation/donors_by_cell.csv, S0",
        "bound_assumption": "Kapsam disinda kalanlar dagilimin ALT kuyrugunda varsayilir "
                            "(Spaull/Lee). Bu bir SINIR, nokta tahmin degil.",
        "trends": {},
    }
    for iso in FOCUS:
        for dom in DOMAINS:
            o_b, o_d = slope(lv, "puf_mean", iso, dom, CYCLES)
            a_b, a_d = slope(ad, "adj_mean", iso, dom, CYCLES)
            c_b, c_d = slope(cb, "const_cohort_mean", iso, dom, CYCLES)
            r_b, r_d = slope(cb, "obs_mean", iso, dom, CYCLES)
            summary["trends"][f"{iso}_{dom}"] = {
                "obs_2003_2012_delta": None if o_d != o_d else round(o_d, 1),
                "escs_fixed_2003_2012_delta": None if a_d != a_d else round(a_d, 1),
                "obs_bound_window_delta": None if r_d != r_d else round(r_d, 1),
                "const_cohort_2003_2012_delta": None if c_d != c_d else round(c_d, 1),
                "coverage_contribution_2003_2012": None if (c_d != c_d or r_d != r_d) else round(r_d - c_d, 1),
            }
    (OUT / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=1), encoding="utf-8")

    print("\n=== TURKIYE: 2003->2012 gozlenen vs ESCS sabit ===")
    for dom in DOMAINS:
        t = summary["trends"].get(f"TUR_{dom}", {})
        print(f"  {dom}: gozlenen {t.get('obs_2003_2012_delta')} · ESCS sabit {t.get('escs_fixed_2003_2012_delta')}")
    print("=== TURKIYE: 2003->2012 gozlenen vs sabit kohort payi ===")
    for dom in DOMAINS:
        t = summary["trends"].get(f"TUR_{dom}", {})
        print(f"  {dom}: gozlenen {t.get('obs_bound_window_delta')} · sabit kohort {t.get('const_cohort_2003_2012_delta')} "
              f"· kapsam katkisi {t.get('coverage_contribution_2003_2012')}")
    print("\nDONE on trend 2003-2012")
    return 0


if __name__ == "__main__":
    sys.exit(main())
