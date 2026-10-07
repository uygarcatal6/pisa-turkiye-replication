# -*- coding: utf-8 -*-
"""
38_cohort_band.py — sabit kohort sınırını banda çevirme (V5_ONTREND_SONUC_2026-09-22.md §6 Ö4; makale §5.3).

[E32]'nin uç sınırı: her döngüde kapsanan dağılımın üst s_t = C_min / C_t payı tutulur (Türkiye: C_min = 0,36 = 2003,
2012'de s = 0,526). Bu, kapsam dışındaki 15 yaşlıların HEPSİNİN kapsanan en düşük öğrencinin altında olduğunu varsayar;
2003–2012 kazancı +93,2 / +99,8 / +90,2 çıkar. Ö4 ara senaryoları istiyor: "dışarıdakiler dağılımın alt %10'unda /
alt çeyreğinde".

ÖNCEDEN BELİRLENEN SEÇİMLER (25 Eyl 2026, sonuç görülmeden):
  * TAHMİN NESNESİ E1 (birincil, [E32] ile aynı): Türkiye'nin 15 yaş kohortunun ÜST 0,36 payının ortalaması; 2003→2012
    değişimi, alan başına.
  * SENARYO AİLESİ S(q): kapsam dışındakiler (kohortun 1 − C_t payı), aynı döngüde kapsanan dağılımın q-yüzdeliğinin
    ALTINDAKİ kısmı gibi dağılır. q ∈ {0 (limit = [E32]), 0,10 ("alt %10"), 0,25 ("alt çeyrek"), 0,50, 1,00 (seçilim yok)}.
    Kohort = kapsanan (kütle C_t) + kapsam dışı (kütle 1 − C_t) karışımı; üst 0,36 kütlenin ağırlıklı ortalaması alınır.
    Not (hesaptan önce türetildi): 2012'de tutulan pay 0,526 olduğundan q ≤ 0,474 için 2012 değeri uç sınırla AYNI kalır;
    ara senaryolar yalnız 2003 tarafını (kapsanan dağılımın altıyla örtüşmeyi) değiştirir. Bu bir kodlama hatası değil,
    tahmin nesnesinin özelliğidir: sınır, dışarıdakilerin kuyrukta TAM NEREDE olduğuna değil, kohortun üst dilimine girip
    girmediklerine duyarlıdır.
  * TAHMİN NESNESİ E2 (ikincil; Andersson & Sandgren Massih 2023'ün İsveç dışlamaları için kullandığı araç): TÜM kohortun
    ortalaması, kapsam dışındakilere aynı döngüde kapsanan dağılımın p-yüzdelik değeri atanarak; p ∈ {0,10, 0,25}.
  * Belirsizlik: BRR (80 replikasyon, Fay 0,5) + Rubin (5 PV), [E32] ile aynı motor; yüzdelikler her replikasyonda yeniden
    hesaplanır. Döngüler arası değişimin SE'si bağımsız örneklemlerden: √(se₁² + se₂²).
  * Kapsam: 2003 CI3 = 0,36 (PISA 2003 Technical Report Table 12.1; 32 ile aynı), 2006–2012 panel `coverage_index3`.
Doğrulama: S(0) [E32]'nin coverage_bound.csv `const_cohort_mean` değerlerini yeniden üretmeli (maks |fark| < 0,01).
Girdi: PUF önbelleği (32 ile aynı kolon kümesi), data/derived/analysis_panel.csv, data/derived/ontrend/coverage_bound.csv
Çıktı: data/derived/ontrend/cohort_band.csv, cohort_band_summary.json
Kullanım: python analysis/38_cohort_band.py      Yazan: Claude Opus 5.5 (Cowork), 2026-09-25.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import _pisa_puf as P  # noqa: E402

ROOT = HERE.parent
OUT = ROOT / "data" / "derived" / "ontrend"
CYCLES = [2003, 2006, 2009, 2012]
DOMAINS = ["MATH", "READ", "SCIE"]
ISO = "TUR"
CI3_2003_TUR = 0.36
Q_SCEN = [0.0, 0.10, 0.25, 0.50, 1.00]
P_IMPUTE = [0.10, 0.25]
FAY = 0.5


def wquantile(w, x, q):
    o = np.argsort(x)
    xs, cw = x[o], np.cumsum(w[o])
    return float(xs[min(int(np.searchsorted(cw, q * cw[-1])), len(xs) - 1)])


def bottom_part(w, x, q):
    """Ağırlıklı dağılımın ALT q kütlesi (sınırda kesirli ağırlık) → (x_alt, w_alt)."""
    o = np.argsort(x)
    xs, ws = x[o], w[o]
    cum = np.cumsum(ws)
    target = q * cum[-1]
    k = int(np.searchsorted(cum, target))
    keep_w = ws[:k].copy()
    rem = target - (cum[k - 1] if k > 0 else 0.0)
    if k < len(ws) and rem > 0:
        return xs[:k + 1], np.append(keep_w, rem)
    return xs[:k], keep_w


def top_mass_mean(w, x, mass):
    """Toplam kütlesi 1 olan (x, w) karışımında üst `mass` kütlenin ortalaması (32'deki top_share_mean ile aynı mantık)."""
    return P_top(w, x, mass / w.sum())


def P_top(w, x, share):
    if share >= 1.0:
        return float(w @ x / w.sum())
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


def e1(w, x, cov, cmin, q):
    """Üst cmin kohort payının ortalaması, S(q) altında."""
    if q == 0.0:
        return P_top(w, x, cmin / cov)
    a = cov * w / w.sum()
    xb, wb = bottom_part(w, x, q)
    b = (1.0 - cov) * wb / wb.sum()
    return top_mass_mean(np.concatenate([a, b]), np.concatenate([x, xb]), cmin)


def e2(w, x, cov, p):
    return cov * float(w @ x / w.sum()) + (1.0 - cov) * wquantile(w, x, p)


def brr(fn, X, W, R):
    G, M = R.shape[1], X.shape[1]
    mult = 1.0 / (G * (1.0 - FAY) ** 2)
    theta = np.array([fn(W, X[:, m]) for m in range(M)])
    v = np.array([mult * sum((fn(R[:, g], X[:, m]) - theta[m]) ** 2 for g in range(G)) for m in range(M)])
    est = float(theta.mean())
    vi = (1 + 1 / M) * float(((theta - est) ** 2).sum()) / (M - 1)
    return est, float(np.sqrt(v.mean() + vi))


def main() -> int:
    panel = pd.read_csv(ROOT / "data" / "derived" / "analysis_panel.csv")
    ref = pd.read_csv(OUT / "coverage_bound.csv", encoding="utf-8-sig")
    ref = ref[ref.iso3 == ISO].set_index(["cycle", "domain"])
    rows = []
    for cycle in CYCLES:
        spec = P.parse_datalist(P.ROOT / P.REGISTRY[cycle]["syn"])
        roots = [r for r in DOMAINS if P.pv_cols(spec, r)]
        want = ["CNT", "SCHOOLID", "STIDSTD", "W_FSTUWT", *P.REPW] + [c for r in roots for c in P.pv_cols(spec, r)]
        df = P.read_columns(cycle, want)  # 32 ile aynı kolon kümesi → önbellek
        g = df[df.CNT == ISO]
        cov = CI3_2003_TUR if cycle == 2003 else float(panel[(panel.cycle == cycle) & (panel.iso3 == ISO)].coverage_index3.iloc[0])
        W = g.W_FSTUWT.to_numpy(float)
        R = g[P.REPW].to_numpy(float)
        for dom in roots:
            X = g[P.pv_cols(spec, dom)].to_numpy(float)
            obs, obs_se = brr(lambda w, x: float(w @ x / w.sum()), X, W, R)
            rec = {"cycle": cycle, "domain": dom, "coverage_index3": cov, "n_students": len(g), "obs_mean": obs, "obs_se": obs_se}
            for q in Q_SCEN:
                est, se = brr(lambda w, x, q=q: e1(w, x, cov, CI3_2003_TUR, q), X, W, R)
                rec[f"E1_q{int(q * 100):03d}"], rec[f"E1_q{int(q * 100):03d}_se"] = est, se
            for p in P_IMPUTE:
                est, se = brr(lambda w, x, p=p: e2(w, x, cov, p), X, W, R)
                rec[f"E2_p{int(p * 100):02d}"], rec[f"E2_p{int(p * 100):02d}_se"] = est, se
            rec["check_vs_E32"] = rec["E1_q000"] - float(ref.loc[(cycle, dom), "const_cohort_mean"])
            rows.append(rec)
            print(f"{cycle} {dom}: gözlenen {obs:.1f} · E1 q0 {rec['E1_q000']:.1f} (E32 farkı {rec['check_vs_E32']:+.4f}) · "
                  f"q10 {rec['E1_q010']:.1f} · q25 {rec['E1_q025']:.1f} · q50 {rec['E1_q050']:.1f} · q100 {rec['E1_q100']:.1f} · "
                  f"E2 p10 {rec['E2_p10']:.1f} · p25 {rec['E2_p25']:.1f}", flush=True)
    t = pd.DataFrame(rows)
    maxdiff = float(t.check_vs_E32.abs().max())
    if maxdiff > 0.01:
        raise SystemExit(f"DUR: S(0) [E32]'yi yeniden üretmiyor (maks |fark| {maxdiff:.4f})")
    tmp = OUT / "cohort_band.csv.tmp"
    t.to_csv(tmp, index=False, encoding="utf-8")
    os.replace(tmp, OUT / "cohort_band.csv")
    cols = ["obs_mean"] + [f"E1_q{int(q * 100):03d}" for q in Q_SCEN] + [f"E2_p{int(p * 100):02d}" for p in P_IMPUTE]
    summ = {"estimands": {"E1": "üst 0,36 kohort payının ortalaması (S(q): dışarıdakiler kapsanan dağılımın q-yüzdeliği altı gibi)",
                          "E2": "tüm kohortun ortalaması (dışarıdakilere kapsanan dağılımın p-yüzdeliği atanır)"},
            "validation_max_abs_diff_vs_E32": round(maxdiff, 5), "delta_2003_2012": {}}
    for dom in DOMAINS:
        a = t[(t.cycle == 2003) & (t.domain == dom)].iloc[0]
        b = t[(t.cycle == 2012) & (t.domain == dom)].iloc[0]
        se_col = lambda c: "obs_se" if c == "obs_mean" else f"{c}_se"
        summ["delta_2003_2012"][dom] = {c: {"delta": round(float(b[c] - a[c]), 1),
                                            "se": round(float(np.hypot(a[se_col(c)], b[se_col(c)])), 1),
                                            "level_2003": round(float(a[c]), 1), "level_2012": round(float(b[c]), 1)} for c in cols}
    tmp = OUT / "cohort_band_summary.json.tmp"
    tmp.write_text(json.dumps(summ, ensure_ascii=False, indent=1), encoding="utf-8")
    os.replace(tmp, OUT / "cohort_band_summary.json")
    print(f"\nDoğrulama: S(0) vs [E32] maks |fark| = {maxdiff:.5f}")
    print(f"{'alan':<5} " + " ".join(f"{c:>9}" for c in cols))
    for dom in DOMAINS:
        print(f"{dom:<5} " + " ".join(f"{summ['delta_2003_2012'][dom][c]['delta']:>+9.1f}" for c in cols))
    return 0


if __name__ == "__main__":
    sys.exit(main())
