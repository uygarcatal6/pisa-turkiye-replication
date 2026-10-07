# -*- coding: utf-8 -*-
"""
34_a1_residual_change.py — ek analiz isteği A1: yenilikçi-alan koşullu artığının döngüler arası DEĞİŞİMİNİN dağılımı.

Soru (A1): her iki döngüde gözlenen her sistem için artığın değişimi hesaplanır; Türkiye'nin bu
değişim dağılımındaki sırası ve ampirik p-değeri dört spesifikasyonda raporlanır.

ÖNCEDEN BELİRLENEN SEÇİMLER (sonuç görülmeden yazıldı, 25 Eyl 2026):
  * Döngüler: 2003 (problem çözme, PUF; çekirdek = mat/oku/fen), 2012 (yaratıcı PÇ, PUF; çekirdek = PUF mat/oku/fen),
    2015 (işbirlikli PÇ), 2025 (hesaplamalı PÇ). Altı çiftin hepsi raporlanır (seçici çift yok).
  * Birincil ölçü: artığın RMSE birimindeki değişimi (d_sd = r1/RMSE1 − r0/RMSE0). Gerekçe: dört alan farklı yapılardır ve
    kesit dağılımları farklıdır (RMSE 9,3 … 19,4); ölçek bağımsız bir değişim gerekir. İkincil: puan cinsinden değişim
    (d_pts; isteğin lafzı) ve döngü içi yüzdelik sıranın değişimi (d_pct).
  * Sıra alttan sayılır (1 = en olumsuz değişim); ampirik p = sıra / N (tek yönlü, alt kuyruk: şişme artığı düşürür).
  * Kesişim aynı kapsamda (tüm / OECD) iki döngünün regresyon örneklemlerinin kesişimidir; artıklar her döngünün kendi
    tam örneklem uyumundan gelir (yeniden uydurma yok).
SONRADAN EKLENEN SAĞLAMLIK (sonuç görüldükten sonra, açıkça post hoc; 25 Eyl 2026): birincil ölçü tüm-katılımcı kapsamında
  RMSE'nin döngüler arasında neredeyse ikiye katlanmasından etkileniyor (2015 10,7 → 2025 19,4; 2025 örneklemi 84, kesişim 47).
  Bu yüzden her iki döngünün regresyonu YALNIZ ortak sistemler üzerinde yeniden uydurulur (common_refit) ve değişim puan ve
  kesişim-RMSE biriminde yeniden hesaplanır. Bu ölçü birincil değildir; yalnız payda sorununu göstermek içindir.
Girdi: data/derived/mechanisms/placebo_conditional_{2003ps_puf,2012ps_puf,2015cps,2025}.csv
Çıktı: data/derived/placebo_backbone/residual_change.csv (uzun biçim), residual_change_summary.json
Kullanım: python analysis/34_a1_residual_change.py      Yazan: Claude Opus 5.5 (Cowork), 2026-09-25.
"""
from __future__ import annotations

import json
import os
import sys
from itertools import combinations
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
MECH = ROOT / "data" / "derived" / "mechanisms"
OUTDIR = ROOT / "data" / "derived" / "placebo_backbone"
FOCUS = ["TUR", "HUN", "SWE", "GEO"]
SPECS = [("all", "linear"), ("all", "quadratic"), ("oecd", "linear"), ("oecd", "quadratic")]


def load() -> dict[int, pd.DataFrame]:
    d03 = pd.read_csv(MECH / "placebo_conditional_2003ps_puf.csv", encoding="utf-8-sig")
    d03 = d03[d03.core_def == "mat/oku/fen"].rename(columns={"ps2003": "dom"})
    d12 = pd.read_csv(MECH / "placebo_conditional_2012ps_puf.csv", encoding="utf-8-sig")
    d12 = d12[d12.core_def == "PUF mat/oku/fen"].rename(columns={"ps2012_puf": "dom"})
    d15 = pd.read_csv(MECH / "placebo_conditional_2015cps.csv", encoding="utf-8-sig").rename(columns={"cps2015_mean_weighted": "dom"})
    d25 = pd.read_csv(MECH / "placebo_conditional_2025.csv", encoding="utf-8-sig").rename(columns={"cps2025_mean": "dom"})
    out = {}
    for yr, d in [(2003, d03), (2012, d12), (2015, d15), (2025, d25)]:
        d = d[["iso3", "scope", "spec", "residual", "resid_sd", "pctile", "core", "dom"]].copy()
        if d.duplicated(["iso3", "scope", "spec"]).any():
            raise SystemExit(f"{yr}: yinelenen iso3/scope/spec satırı")
        out[yr] = d
    return out


def refit(core: pd.Series, dom: pd.Series, spec: str) -> tuple[pd.Series, float]:
    """Ortak sistemler üzerinde yeniden uydurma (post hoc sağlamlık): artık ve RMSE (ddof = parametre sayısı)."""
    x = core.to_numpy(float)
    X = np.column_stack([np.ones_like(x), x] + ([x ** 2] if spec == "quadratic" else []))
    beta, *_ = np.linalg.lstsq(X, dom.to_numpy(float), rcond=None)
    res = dom.to_numpy(float) - X @ beta
    rmse = float(np.sqrt((res ** 2).sum() / (len(res) - X.shape[1])))
    return pd.Series(res, index=core.index), rmse


def rank_low(s: pd.Series, iso: str) -> int:
    # 1 = en küçük (en olumsuz) değer; eşitlikte en kötümser (küçük) sıra
    v = s.loc[iso]
    return int((s < v).sum() + 1)


def main() -> int:
    data = load()
    rows, summ = [], {}
    for (y0, y1) in combinations(sorted(data), 2):
        for scope, spec in SPECS:
            a = data[y0][(data[y0].scope == scope) & (data[y0].spec == spec)].set_index("iso3")
            b = data[y1][(data[y1].scope == scope) & (data[y1].spec == spec)].set_index("iso3")
            common = a.index.intersection(b.index)
            if "TUR" not in common:
                raise SystemExit(f"{y0}->{y1} {scope}/{spec}: TUR kesişimde yok")
            ra, rmse_a = refit(a.loc[common, "core"], a.loc[common, "dom"], spec)
            rb, rmse_b = refit(b.loc[common, "core"], b.loc[common, "dom"], spec)
            d = pd.DataFrame({
                "d_pts": b.loc[common, "residual"] - a.loc[common, "residual"],
                "d_sd": b.loc[common, "resid_sd"] - a.loc[common, "resid_sd"],
                "d_pct": b.loc[common, "pctile"] - a.loc[common, "pctile"],
                "d_pts_cr": rb - ra,
                "d_sd_cr": rb / rmse_b - ra / rmse_a,
            })
            n = len(d)
            key = f"{y0}->{y1}|{scope}/{spec}"
            summ[key] = {"n": n, "rmse_common_refit": [round(rmse_a, 2), round(rmse_b, 2)]}
            ms = ["d_sd", "d_pts", "d_pct", "d_pts_cr", "d_sd_cr"]
            for iso in common:
                rec = {"pair": f"{y0}->{y1}", "scope": scope, "spec": spec, "iso3": iso, "n": n}
                for m in ms:
                    rec[m] = round(float(d.loc[iso, m]), 4)
                    rec[f"rank_{m}"] = rank_low(d[m], iso)
                rows.append(rec)
                if iso in FOCUS:
                    summ[key][iso] = {m: {"value": round(float(d.loc[iso, m]), 2), "rank_from_bottom": rank_low(d[m], iso),
                                          "p_lower": round(rank_low(d[m], iso) / n, 3)} for m in ms}
            summ[key]["median"] = {m: round(float(d[m].median()), 2) for m in ms}
    OUTDIR.mkdir(parents=True, exist_ok=True)
    long = pd.DataFrame(rows)
    tmp = OUTDIR / "residual_change.csv.tmp"
    long.to_csv(tmp, index=False, encoding="utf-8")
    os.replace(tmp, OUTDIR / "residual_change.csv")
    meta = {"note": "A1 — koşullu artığın döngüler arası değişimi; birincil ölçü d_sd (RMSE birimi); sıra alttan (1 = en olumsuz); p_lower = sıra/N",
            "inputs": ["placebo_conditional_2003ps_puf.csv (core_def mat/oku/fen)", "placebo_conditional_2012ps_puf.csv (core_def PUF mat/oku/fen)",
                       "placebo_conditional_2015cps.csv", "placebo_conditional_2025.csv"],
            "results": summ}
    tmp = OUTDIR / "residual_change_summary.json.tmp"
    tmp.write_text(json.dumps(meta, ensure_ascii=False, indent=1), encoding="utf-8")
    os.replace(tmp, OUTDIR / "residual_change_summary.json")
    # konsol özeti: Türkiye, birincil ölçü
    print(f"{'çift':<11}{'spec':<16}{'N':>4}  {'TUR d_sd':>8} {'sıra':>6} {'p':>6}  {'d_pts':>7} {'sıra':>6}  {'cr_pts':>7} {'sıra':>6}  {'cr_sd':>6} {'sıra':>6}  RMSE_cr")
    for key, v in summ.items():
        pair, sp = key.split("|")
        t = v["TUR"]
        f = lambda m: f"{t[m]['rank_from_bottom']:>2}/{v['n']:<3}"
        print(f"{pair:<11}{sp:<16}{v['n']:>4}  {t['d_sd']['value']:>8.2f} {f('d_sd')} {t['d_sd']['p_lower']:>6.3f}  {t['d_pts']['value']:>7.1f} {f('d_pts')}  "
              f"{t['d_pts_cr']['value']:>7.1f} {f('d_pts_cr')}  {t['d_sd_cr']['value']:>6.2f} {f('d_sd_cr')}  {v['rmse_common_refit']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
