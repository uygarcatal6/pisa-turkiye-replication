# -*- coding: utf-8 -*-
"""
52_e9b_escs_benchmark.py — E9b: E9'daki üst ESCS kötüleşmesinin (D) ülkeler arası kıyası.

Soru (RESULTS_EMPIRICAL_FIXES.md §0.12): E9 adım 3'te Türkiye'nin plasebo artığı 2015 CPS → 2025 CMPS arasında ESCS üst %20'de
alt %80'e göre daha çok kötüleşti (D < 0). Bu Türkiye'ye mi özgü, yoksa yeni alanın her ülkede görülen bir özelliği mi?

ÖNCEDEN BELİRLENEN SEÇİMLER (§0.12; commit b0344a7, betik yazılmadan ve koşulmadan önce; birim gerekçesi düzeltmesi §0.12 dipnot ⁴,
yine koşudan önce):
  * Model E9 adım 3 ile birebir: betik 44 öğrenci modeli (2015 CLPS, 2025 CMPS; tam ikinci derece çekirdek; havuzlu, senato ağırlıklı;
    PV başına, M = 10), betik 50 `step3` ile aynı sistem kümeleri (`m44.systems(yıl, "all")`, veride bulunanlar), aynı katsayılar.
  * Birimler: ortak küme = iki model kümesinin (all) kesişimi, 2025 PUF'ta bulunanlar; OECD kümesi = iki dosyanın oecd kapsamlarının
    kesişimi. Bir sistem, iki döngüde de ESCS'si dolu en az 100 öğrencisi varsa girer; girmeyenler nedeniyle listelenir.
  * Ölçü: c_t = r_t(ESCS üst %20) − r_t(ESCS alt %80); ESCS'nin döngü içi ağırlıklı orta sırası (her replikasyonda yeniden);
    BRR (Fay 0,5; W_FSTURWT1–80) + Rubin, betik 50 `slice_theta` ile. D = c_2025 − c_2015; SE √(se₁² + se₂²). Birim puan.
  * İkincil: 2025 gradyanı (bütün 2025 sistemleri), 2015 gradyanı ve gradyan değişimi (ortak küme); `m44.slice_stats` "gradient".
  * Sıra en olumsuzdan: #(D_sistem < D_TUR) + 1; p = sıra/N, tek yönlü.
  * Karar: iki kümede de p ≤ 0,10 → "Türkiye'ye özgü"; yalnız birinde → "kısmen Türkiye'ye özgü" (küme adıyla);
    ikisinde de p > 0,10 → "yeni alanın genel özelliği; E9'un D imzası Türkiye'ye özgü değil". E9'un §0.10 kararı değişmez.
  * Ek raporlar: D'nin sistemler arası medyanı ve çeyrekleri; D < 0 ve %95 aralığı 0'ı dışlayan sistem sayısı; Türkiye'nin c_2015,
    c_2025 ve 2025 gradyan sıraları. SS birimindeki D sırası yalnız ek (dipnot ⁴).
  * Kapılar: E9 adım 3 ile aynı (2015 CLPS ağırlıklı ortalamaları `cps2015_country_means.csv` ile ≤ 0,001; 2025 betik 44 kapısı,
    BEL istisnasıyla, bb2f7eb).
UYGULAMA AYRINTILARI (betik yazılırken, koşudan önce; §0.12'nin açık bırakıp tanımı değiştirmeyenler):
  * "Bütün 2025 sistemleri" = 2025 model kümesi (all, 84 satır), PUF'ta bulunan ve ESCS'si dolu ≥ 100 öğrencisi olanlar.
  * ESCS eşiği ağırlıksız öğrenci sayısıdır (ESCS sonlu). Sıra hesabında ESCS'si eksik öğrenci dışarıda (betik 50 ile aynı).
  * Çeyrekler ve medyan sistemler üzerinden ağırlıksız (`np.percentile`, doğrusal ara değer); Türkiye dahil.
  * Kendi içi tutarlılık kapısı (tanım değil): Türkiye'nin c_2015, c_2025, D ve 2025 gradyanı `e9_residual_by_escs.csv`'deki
    değerlerle mutlak fark ≤ 1e-6 olmalı; tutmazsa model E9 ile birebir değildir → DUR.
Girdi: betik 50'nin 2015 CPS önbelleği/zip'leri (`load_2015_cps`), betik 44'ün 2025 önbelleği/zip'i (`m44.load(2025)`);
       data/derived/cps2015_country_means.csv; data/derived/analysis_panel.csv;
       data/derived/mechanisms/placebo_conditional_{2015cps,2025}.csv; data/derived/empirical_fixes/e9_residual_by_escs.csv.
Çıktı: data/derived/empirical_fixes/e9b_escs_benchmark.csv, e9b_summary.json.
Kullanım (Windows, Git Bash'ten; pyreadstat + pyarrow): python analysis/52_e9b_escs_benchmark.py
Yazan: Claude Code (bulut oturumu), 2026-09-26. Bu oturumda mikroveri yoktu: betik yalnız sentetik veriyle duman testinden geçti.
"""
from __future__ import annotations

import importlib
import json
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE))
m44 = importlib.import_module("44_e5_coverage_matched_2003")
m50 = importlib.import_module("50_e9_distribution_of_gains")

D = ROOT / "data" / "derived"
OUT = D / "empirical_fixes"
REPW = m50.REPW
M = m50.M
MIN_ESCS = 100
P_CUT = 0.10
E9_TOL = 1e-6


def set_cfg_2015() -> None:
    m44.CFG[2015] = dict(M=10, new="CLPS", repw=REPW, school="CNTSCHID", sysfile="placebo_conditional_2015cps.csv", sysfilter={})


def gate_2015(d15: pd.DataFrame) -> dict:
    """Betik 50 step3 ile aynı: 2015 CLPS ağırlıklı ortalamaları ≤ 0,001."""
    ours = pd.read_csv(D / "cps2015_country_means.csv", encoding="utf-8-sig")
    diffs = []
    for cn, g in d15.groupby("CNT"):
        r = ours[ours.iso3 == cn]
        if len(r):
            w = g.W_FSTUWT.to_numpy(float)
            v = [np.nansum(w * g[f"PV{i}CLPS"].to_numpy(float)) / np.nansum(w * np.isfinite(g[f"PV{i}CLPS"].to_numpy(float)))
                 for i in range(1, M + 1)]
            diffs.append(abs(float(np.mean(v)) - float(r.cps2015_mean_weighted.iloc[0])))
    out = {"n": len(diffs), "max_abs_diff": round(max(diffs), 5) if diffs else None}
    if not diffs or max(diffs) > 0.001:
        raise SystemExit(f"DUR: 2015 CLPS kapısı geçmedi: {out}")
    return out


def system_stats(cyc: int, g: pd.DataFrame, coefs: np.ndarray) -> dict:
    g = g.reset_index(drop=True)
    e = m44.residuals(cyc, g, coefs)
    W = np.column_stack([g.W_FSTUWT.to_numpy(float)] + [g[c].to_numpy(float) for c in REPW])
    key = g.ESCS.to_numpy(float)
    c = m50.slice_theta(e, key, W, lambda r: r > 0.8) - m50.slice_theta(e, key, W, lambda r: r <= 0.8)
    c_est, c_se = m44.rubin(c[0], c[1:])
    gr_est, gr_se, _ = m44.slice_stats(e, key, W, ("gradient", None))
    return {"c": c_est, "c_se": c_se, "grad": gr_est, "grad_se": gr_se}


def rank_p(vals: pd.Series, iso: str = "TUR") -> dict:
    v = vals.dropna()
    if iso not in v.index:
        raise SystemExit(f"DUR: {iso} sıralama kümesinde yok")
    r = int((v < v[iso]).sum()) + 1
    return {"rank_from_most_negative": r, "N": int(len(v)), "p": round(r / len(v), 4), "value": float(v[iso])}


def dist(vals: pd.Series) -> dict:
    v = vals.dropna().to_numpy(float)
    q25, q50, q75 = np.percentile(v, [25, 50, 75])
    return {"N": int(len(v)), "q25": float(q25), "median": float(q50), "q75": float(q75), "min": float(v.min()), "max": float(v.max())}


def main() -> int:
    set_cfg_2015()
    d15 = m50.numeric(m50.load_2015_cps())
    info = {"note": "E9b — üst ESCS kötüleşmesinin (D) ülkeler arası kıyası; ön-belirleme §0.12 (commit b0344a7) + dipnot ⁴.",
            "gates": {"2015_clps": gate_2015(d15)}}
    d25 = m44.load(2025)
    g25 = m44.gates(2025, d25)
    info["gates"]["2025"] = g25
    if g25["failed"]:
        raise SystemExit(f"DUR: 2025 kapısı geçmedi: {g25['failed']}")

    data = {2015: d15, 2025: d25}
    present = {cyc: set(df.CNT.unique()) for cyc, df in data.items()}
    model_sys = {cyc: sorted(set(m44.systems(cyc, "all")) & present[cyc]) for cyc in data}
    n_escs = {cyc: df[np.isfinite(df.ESCS.to_numpy(float))].groupby("CNT").size() for cyc, df in data.items()}

    # modeller: E9 adım 3 ile birebir (aynı kümeler, aynı katsayılar)
    coefs, rsd = {}, {}
    for cyc, df in data.items():
        cf, sd, r2 = m44.fit_model(cyc, df[df.CNT.isin(model_sys[cyc])], model_sys[cyc])
        coefs[cyc], rsd[cyc] = cf, sd
        info[f"model_{cyc}"] = {"n_systems": len(model_sys[cyc]), "resid_sd_unit": round(sd, 4), "r2_by_pv": [round(x, 4) for x in r2]}

    # birimler
    all15, all25 = set(m44.systems(2015, "all")), set(m44.systems(2025, "all"))
    oecd15, oecd25 = set(m44.systems(2015, "oecd")), set(m44.systems(2025, "oecd"))
    excluded = []

    def eligible(name: str, cands: set, cycles: tuple) -> list[str]:
        keep = []
        for cn in sorted(cands):
            miss = [c for c in cycles if cn not in present[c]]
            if miss:
                excluded.append({"set": name, "iso3": cn, "reason": f"veride yok: {miss}"})
                continue
            small = {c: int(n_escs[c].get(cn, 0)) for c in cycles if int(n_escs[c].get(cn, 0)) < MIN_ESCS}
            if small:
                excluded.append({"set": name, "iso3": cn, "reason": f"ESCS dolu < {MIN_ESCS}: {small}"})
                continue
            keep.append(cn)
        return keep

    sets = {"common": eligible("common", all15 & all25, (2015, 2025)), "oecd": eligible("oecd", oecd15 & oecd25, (2015, 2025)),
            "all2025": eligible("all2025", all25, (2025,))}
    info["sets"] = {k: {"N": len(v), "members": v} for k, v in sets.items()}
    info["excluded"] = excluded

    # sistem başına ölçüler
    need = {2015: set(sets["common"]) | set(sets["oecd"]), 2025: set(sets["common"]) | set(sets["oecd"]) | set(sets["all2025"])}
    st = {}
    for cyc, df in data.items():
        for cn in sorted(need[cyc]):
            st[(cyc, cn)] = system_stats(cyc, df[df.CNT == cn], coefs[cyc])
        print(f"{cyc}: {len(need[cyc])} sistem", flush=True)

    rows = []
    for cn in sorted(need[2025]):
        a, b = st.get((2015, cn)), st[(2025, cn)]
        r = {"iso3": cn, "in_common": cn in sets["common"], "in_oecd": cn in sets["oecd"], "in_all2025": cn in sets["all2025"],
             "n_escs_2015": int(n_escs[2015].get(cn, 0)), "n_escs_2025": int(n_escs[2025].get(cn, 0)),
             "c2025": b["c"], "c2025_se": b["c_se"], "grad2025": b["grad"], "grad2025_se": b["grad_se"]}
        if a is not None:
            r.update({"c2015": a["c"], "c2015_se": a["c_se"], "grad2015": a["grad"], "grad2015_se": a["grad_se"],
                      "D": b["c"] - a["c"], "D_se": float(np.hypot(a["c_se"], b["c_se"])),
                      "dgrad": b["grad"] - a["grad"], "dgrad_se": float(np.hypot(a["grad_se"], b["grad_se"])),
                      "D_sd": b["c"] / rsd[2025] - a["c"] / rsd[2015]})
        rows.append(r)
    t = pd.DataFrame(rows).set_index("iso3")
    t["D_lo95"], t["D_hi95"] = t.D - 1.96 * t.D_se, t.D + 1.96 * t.D_se

    # kendi içi tutarlılık: Türkiye E9 ile birebir
    e9 = pd.read_csv(OUT / "e9_residual_by_escs.csv")
    ref = {(p, s): v for p, s, v in zip(e9.period, e9.slice, e9.estimate)}
    chk = {"c2015": (t.loc["TUR", "c2015"], ref[("2015", "karsitlik_ust20_alt80")]),
           "c2025": (t.loc["TUR", "c2025"], ref[("2025", "karsitlik_ust20_alt80")]),
           "D": (t.loc["TUR", "D"], ref[("2015->2025", "karsitlik_ust20_alt80")]),
           "grad2025": (t.loc["TUR", "grad2025"], ref[("2025", "gradyan")])}
    info["gates"]["tur_vs_e9"] = {k: round(abs(float(x) - float(y)), 9) for k, (x, y) in chk.items()}
    if max(info["gates"]["tur_vs_e9"].values()) > E9_TOL:
        raise SystemExit(f"DUR: Türkiye değerleri E9 ile uyuşmuyor: {info['gates']['tur_vs_e9']}")

    # sıralar, karar, ek raporlar
    res = {}
    for k in ("common", "oecd"):
        s = t.loc[sets[k]]
        res[k] = {"D": rank_p(s.D), "D_sd_ek": rank_p(s.D_sd), "c2015": rank_p(s.c2015), "c2025": rank_p(s.c2025),
                  "grad2015": rank_p(s.grad2015), "grad2025": rank_p(s.grad2025), "dgrad": rank_p(s.dgrad),
                  "D_distribution": dist(s.D), "n_D_neg_sig": int(((s.D < 0) & (s.D_hi95 < 0)).sum())}
    res["all2025"] = {"grad2025": rank_p(t.loc[sets["all2025"]].grad2025), "c2025": rank_p(t.loc[sets["all2025"]].c2025)}
    info["results"] = res
    hit = {k: res[k]["D"]["p"] <= P_CUT for k in ("common", "oecd")}
    if all(hit.values()):
        verdict = "üst ESCS kötüleşmesi Türkiye'ye özgü"
    elif any(hit.values()):
        verdict = f"kısmen Türkiye'ye özgü (yalnız {'ortak' if hit['common'] else 'OECD'} kümede p ≤ {P_CUT})"
    else:
        verdict = "yeni alanın genel özelliği; E9'un D imzası Türkiye'ye özgü değil"
    info["decision"] = {"p_common": res["common"]["D"]["p"], "p_oecd": res["oecd"]["D"]["p"], "verdict": verdict,
                        "e9_decision_unchanged": True}

    OUT.mkdir(parents=True, exist_ok=True)
    tmp = OUT / "e9b_escs_benchmark.csv.tmp"
    t.reset_index().to_csv(tmp, index=False, encoding="utf-8")
    os.replace(tmp, OUT / "e9b_escs_benchmark.csv")
    tmp = OUT / "e9b_summary.json.tmp"
    tmp.write_text(json.dumps(info, ensure_ascii=False, indent=1, default=float), encoding="utf-8")
    os.replace(tmp, OUT / "e9b_summary.json")
    print(json.dumps({"gates": {k: v for k, v in info["gates"].items() if k != "2025"}, "sets": {k: v["N"] for k, v in info["sets"].items()},
                      "decision": info["decision"]}, ensure_ascii=False, indent=1, default=float))
    return 0


if __name__ == "__main__":
    sys.exit(main())
