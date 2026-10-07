# -*- coding: utf-8 -*-
"""
47_e7_sc_inference_table.py — editoryal düzeltme E7 (F8): SC ailesinin p-değerlerini havuz büyüklüğüyle birlikte raporlama.

Soru (COWORK_AMPIRIK_DUZELTMELER.md E7): Makale [137] "hiçbir kestirim p < 0,10'a ulaşmıyor" diyor. Plasebo-yerleşim p'si
≥ 1/(J+1)'dir; J = 5 → 0,167, J = 8 → 0,111. Cümle çıktı dosyalarıyla uzlaşıyor mu, yoksa yazılmamış bir havuz kısıtına mı
dayanıyor? Yeniden kestirim YOK; yalnız mevcut çıktıların derlenmesi.

ÖNCEDEN BELİRLENEN SEÇİMLER (RESULTS_EMPIRICAL_FIXES.md §0.6; commit 476fe4e, koşudan önce):
  * Satır = tahminci × pencere × havuz × alan (× hücre/p türü); yalnız Türkiye (HUN/GEO satırları hariç).
  * Taban: plasebo-yerleşim p'si için 1/(J+1); konformal p için ızgara adımı 1/T (`p_grid_step`). Taban bayrağı: |p − taban| ≤ 0,0015.
  * Havuz türü eşlemesi §0.6'daki gibi (istikrarlı OECD / belirsizler eklenmiş / tüm katılımcılar / otokratikleşenleri içeren).
  * Tutarlılık kapıları (koşu içinde): SDiD sırası = p_rank·(J+1) tam sayıya 0,02 içinde; ablasyonda rank_gap paydası = J+1;
    SC plasebo dosyasındaki satır sayısı = J+1 ve dosyadan hesaplanan p_gap = synth_summary p_gap.
SONRADAN EKLENENLER: yok.
Girdi: data/derived/sdid/sdid_results.csv; data/derived/donor_ablation/ablation_grid.csv; data/derived/mc_conformal/{conformal_results,
       mc_results}.csv; data/derived/robustness/donor_rule_grid.csv; data/derived/synth/synth_summary.csv + synth/TUR*_placebo.csv.
Çıktı: data/derived/empirical_fixes/e7_sc_inference_table.csv, e7_summary.json.
Kullanım: python analysis/47_e7_sc_inference_table.py      Yazan: Claude Code (bulut oturumu), 2026-09-26.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
D = ROOT / "data" / "derived"
OUT = D / "empirical_fixes"
TOL = 0.0015
ALPHA = 0.10

POOL_TYPE = {"stable_all_oecd": "istikrarlı OECD", "stable_all": "istikrarlı OECD", "stable_clean": "istikrarlı OECD",
             "stable_plus_ambiguous_oecd": "belirsizler eklenmiş", "stable_plus_ambiguous": "belirsizler eklenmiş",
             "all_participants": "tüm katılımcılar"}


def ablation_pool_type(c1: bool, c2: str) -> str:
    if c2 == "L3":
        return "otokratikleşenleri içeren"
    if not c1:
        return "tüm katılımcılar"
    return "belirsizler eklenmiş" if c2 == "L2" else "istikrarlı OECD"


def base(estimator, source, window, pool, pool_type, domain, cell, p_kind, J, rank, p, floor, floor_kind, **extra):
    at_floor = (not pd.isna(p)) and abs(float(p) - floor) <= TOL
    return {"estimator": estimator, "source": source, "window": window, "pool": pool, "pool_type": pool_type, "domain": domain,
            "cell": cell, "p_kind": p_kind, "J": int(J), "tur_rank": rank, "p": (None if pd.isna(p) else round(float(p), 4)),
            "floor": round(floor, 4), "floor_kind": floor_kind, "at_floor": bool(at_floor),
            "p_lt_010": (None if pd.isna(p) else bool(float(p) < ALPHA)), "floor_lt_010": bool(floor < ALPHA), **extra}


def rows_sdid():
    s = pd.read_csv(D / "sdid" / "sdid_results.csv", encoding="utf-8-sig")
    out = []
    for r in s.itertuples():
        rk_f = r.p_rank * (r.n_donors + 1)
        if abs(rk_f - round(rk_f)) > 0.02:
            raise SystemExit(f"DUR (kapı): SDiD sırası tam sayı değil: {r.window} {r.outcome} {r.pool} {rk_f}")
        out.append(base("SDiD", "sdid/sdid_results.csv", r.window, r.pool, POOL_TYPE[r.pool], r.outcome, "", "p_rank",
                        r.n_donors, f"{int(round(rk_f))}/{r.n_donors + 1}", r.p_rank, 1 / (r.n_donors + 1), "1/(J+1)",
                        estimate=r.tau_sdid))
    return out


def rows_ablation():
    a = pd.read_csv(D / "donor_ablation" / "ablation_grid.csv", encoding="utf-8-sig")
    out = []
    for r in a.itertuples():
        for kind, rank_s, p in (("p_gap", r.rank_gap, r.p_gap), ("p_ratio", r.rank_ratio, r.p_ratio)):
            num, den = (int(x) for x in str(rank_s).split("/"))
            if den != r.n_donors + 1:
                raise SystemExit(f"DUR (kapı): ablasyon {r.cell_id} {r.outcome}: sıra paydası {den} ≠ J+1 = {r.n_donors + 1}")
            out.append(base("SC ön-dönem arındırılmış (ablasyon)", "donor_ablation/ablation_grid.csv", "2015–2025",
                            f"c1={r.c1};c2={r.c2};c3={r.c3};c4={r.c4}", ablation_pool_type(bool(r.c1), r.c2), r.outcome,
                            f"{r.block}:{r.cell_id}:{r.off_criteria}", kind, r.n_donors, rank_s, p, 1 / (r.n_donors + 1),
                            "1/(J+1)", estimate=r.post_gap_mean))
    return out


def rows_conformal_mc():
    c = pd.read_csv(D / "mc_conformal" / "conformal_results.csv", encoding="utf-8-sig")
    m = pd.read_csv(D / "mc_conformal" / "mc_results.csv", encoding="utf-8-sig")
    out = []
    for r in c.itertuples():
        jm = m[(m.outcome == r.outcome) & (m.pool == r.pool)].n_donors.unique()
        if len(jm) != 1 or int(jm[0]) != int(r.n_donors):
            raise SystemExit(f"DUR (kapı): mc_results J uyuşmuyor {r.outcome} {r.pool}")
        for win, p in (("tüm post (tau0)", r.conformal_p_tau0), ("yalnız 2025", r.conformal_p_2025only),
                       ("2018–2025", r.conformal_p_2018_25)):
            out.append(base("Konformal (SC)", "mc_conformal/conformal_results.csv", win, r.pool, POOL_TYPE[r.pool], r.outcome, "",
                            "conformal_p", r.n_donors, None, p, float(r.p_grid_step), "1/T (ızgara)", T=int(r.T)))
        num, den = (int(x) for x in str(r.mc_rank).split("/"))
        if den != r.n_donors + 1:
            raise SystemExit(f"DUR (kapı): mc_rank paydası {den} ≠ J+1")
        out.append(base("Matris tamamlama (MC)", "mc_conformal/conformal_results.csv", "2015–2025", r.pool, POOL_TYPE[r.pool],
                        r.outcome, "", "mc_p", r.n_donors, r.mc_rank, r.mc_p, 1 / (r.n_donors + 1), "1/(J+1)",
                        estimate=r.mc_post_gap_mean))
    return out


SYNTH_POOL = {"TUR": None, "TUR_robust_ambig": None, "TUR_levels": None, "TUR_keepflagged": "belirsizler eklenmiş (yıldızlılar tutulmuş)",
              "TUR_allparticipants": "tüm katılımcılar"}


def rows_synth():
    s = pd.read_csv(D / "synth" / "synth_summary.csv")
    s = s[s.treated == "TUR"]
    out = []
    for r in s.itertuples():
        short = "levels" if str(r.spec).startswith("levels") else "demeaned"
        f = D / "synth" / f"{r.case}_{r.domain}_{r.pool}_{short}_placebo.csv"
        pl = pd.read_csv(f)
        if len(pl) != r.n_donors + 1:
            raise SystemExit(f"DUR (kapı): {f.name}: {len(pl)} satır ≠ J+1 = {r.n_donors + 1}")
        t = float(pl.loc[pl.unit == "treated", "post_gap_mean"].iloc[0])
        rank_gap = int((pl.post_gap_mean >= t - 1e-9).sum())
        if abs(rank_gap / len(pl) - r.p_gap) > TOL:
            raise SystemExit(f"DUR (kapı): {f.name}: dosyadan p_gap {rank_gap / len(pl):.3f} ≠ özet {r.p_gap}")
        ptype = SYNTH_POOL.get(r.case) or POOL_TYPE[r.pool]
        for kind, rank_s, p in (("p_gap", f"{rank_gap}/{len(pl)}", r.p_gap), ("p_ratio", r.rank, r.p_ratio)):
            out.append(base("SC (Synth, R)", f"synth/synth_summary.csv + {f.name}", "2015–2025", r.pool, ptype, r.domain,
                            f"{r.case}:{short}", kind, r.n_donors, rank_s, p, 1 / (r.n_donors + 1), "1/(J+1)",
                            estimate=r.post_gap_mean))
    return out


def rows_rule_grid():
    g = pd.read_csv(D / "robustness" / "donor_rule_grid.csv")
    out = []
    for r in g.itertuples():
        ptype = "tüm katılımcılar" if not bool(r.oecd_only) else POOL_TYPE[r.pool]
        out.append(base("SC (donör kuralı ızgarası)", "robustness/donor_rule_grid.csv", "2015–2025", r.pool, ptype, r.domain,
                        f"oecd_only={r.oecd_only};drop_asterisk={r.drop_asterisk};drop_paper2015={r.drop_paper2015}",
                        "p yok (yalnız nokta kestirimi)", r.n_donors, None, np.nan, 1 / (r.n_donors + 1), "1/(J+1)",
                        estimate=r.post_gap_mean))
    return out


def summarise(t: pd.DataFrame) -> dict:
    out = {}
    tp = t[t.p.notna()]
    for (est, win, kind), g in tp.groupby(["estimator", "window", "p_kind"], sort=False):
        sig = g[g.p_lt_010.astype(bool)]
        out[f"{est} | {win} | {kind}"] = {
            "n_cells": int(len(g)), "J_range": [int(g.J.min()), int(g.J.max())],
            "n_at_floor": int(g.at_floor.sum()), "n_floor_lt_010": int(g.floor_lt_010.sum()),
            "n_p_lt_010": int(len(sig)), "J_of_p_lt_010": sorted(int(x) for x in sig.J.unique()),
            "p_range_p_lt_010": ([round(float(sig.p.min()), 4), round(float(sig.p.max()), 4)] if len(sig) else None),
            "n_p_lt_010_at_floor": int(sig.at_floor.sum()),
            "by_pool_type": {pt: {"n": int(len(h)), "n_at_floor": int(h.at_floor.sum()), "n_p_lt_010": int(h.p_lt_010.astype(bool).sum()),
                                  "J_range": [int(h.J.min()), int(h.J.max())]}
                             for pt, h in g.groupby("pool_type", sort=False)}}
    return out


def main() -> int:
    t = pd.DataFrame(rows_sdid() + rows_ablation() + rows_conformal_mc() + rows_synth() + rows_rule_grid())
    OUT.mkdir(parents=True, exist_ok=True)
    tmp = OUT / "e7_sc_inference_table.csv.tmp"
    t.to_csv(tmp, index=False, encoding="utf-8")
    os.replace(tmp, OUT / "e7_sc_inference_table.csv")
    summ = {"note": "E7 — SC ailesi çıkarım tablosu; taban = 1/(J+1) (plasebo-yerleşim) ya da 1/T (konformal ızgara); "
                    "taban bayrağı |p − taban| ≤ 0,0015. Yeniden kestirim yok. Ön-belirleme §0.6 (commit 476fe4e).",
            "n_rows": int(len(t)), "n_rows_with_p": int(t.p.notna().sum()),
            "n_rows_p_lt_010": int(t.p_lt_010.fillna(False).astype(bool).sum()),
            "groups": summarise(t)}
    # Cowork ön kontrolünün yeniden üretimi (görev metni E7)
    sd = t[(t.estimator == "SDiD") & (t.window == "post2018")]
    ab = t[(t.source == "donor_ablation/ablation_grid.csv") & (t.p_kind == "p_gap")]
    cf = t[t.p_kind == "conformal_p"]
    summ["precheck_reproduction"] = {
        "sdid_post2018_all_at_floor": f"{int(sd.at_floor.sum())}/{len(sd)}",
        "sdid_post2018_rank1": f"{int(sd.tur_rank.str.startswith('1/').sum())}/{len(sd)}",
        "sdid_post2018_J": [int(sd.J.min()), int(sd.J.max())],
        "sdid_post2018_p_lt_010_J": sorted(int(x) for x in sd[sd.p_lt_010.astype(bool)].J),
        "sdid_post2018_p_lt_010_range": [float(sd[sd.p_lt_010.astype(bool)].p.min()), float(sd[sd.p_lt_010.astype(bool)].p.max())],
        "ablation_cells": int(len(ab)), "ablation_J": [int(ab.J.min()), int(ab.J.max())],
        "ablation_p_gap_at_floor": int(ab.at_floor.sum()), "ablation_p_gap_lt_010": int(ab.p_lt_010.astype(bool).sum()),
        "ablation_p_gap_lt_010_J": sorted(int(x) for x in ab[ab.p_lt_010.astype(bool)].J.unique()),
        "conformal_grid_step": [float(cf.floor.min()), float(cf.floor.max())],
    }
    tmp = OUT / "e7_summary.json.tmp"
    tmp.write_text(json.dumps(summ, ensure_ascii=False, indent=1), encoding="utf-8")
    os.replace(tmp, OUT / "e7_summary.json")
    print(json.dumps(summ["precheck_reproduction"], ensure_ascii=False, indent=1))
    print(f"{'grup':<70}{'n':>5}{'J':>9}{'taban':>7}{'<0,10':>7}{'J(<0,10)':>22}")
    for k, v in summ["groups"].items():
        print(f"{k:<70}{v['n_cells']:>5}{str(v['J_range']):>9}{v['n_at_floor']:>7}{v['n_p_lt_010']:>7}{str(v['J_of_p_lt_010']):>22}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
