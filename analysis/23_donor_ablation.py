# -*- coding: utf-8 -*-
"""
23 — Donör kriteri ablasyon merdiveni (spesifikasyon eğrisi) + mod-düzeltilmiş havuz (C3-adj).

Soru (v4 §5.1): "Sonuç dört donör kuralının kendisine mi bağlı?"
Amaç en iyi tahmini bulmak DEĞİL; kuralları teker teker / ikişer / üçer gevşetince tahminin nereye gittiğini haritalamak.
Baseline önceden sabit: C1–C4 açık, C2 = stable_all, ön-dönem ortalamasından arındırılmış SC (Python SC = R Synth; Faz 4 çapraz doğrulaması).

Kriterler (açık = baseline):
  C1 OECD üyeliği · C2 kurumsal istikrar taraması (L0 stable_clean / L1 stable_all / L2 +ambiguous(no ERT episode) / L3 yok)
  C3 2015'te kâğıt kalanların dışlanması (açık / kapalı / adj = tut ve geçiş cezasını düzelt) · C4 uyarı yıldızlı ülke-döngülerinin dışlanması
Koşular: A merdiven 16 hücre × 3 alan; B C2 kademeleri L0–L3 × 3; C C3-adj (diğerleri baseline) × 3 × {donör-düzeltmeli, +Türkiye-düzeltmeli tanı};
         ek: merdivende C3 kapalı olan her hücrenin "adj" ikizi (donör-düzeltmeli) — düzeltme yalnız kâğıt ülkeleri havuza girince iş yapar.
         E düzey eşiği: C2 tarama DEĞİŞİMİ tarar, DÜZEYİ taramaz; kontrol birimi "tedavi görmemiş Türkiye"yi temsil edeceği için
         "libdem_2013 ≥ eşik" koşulu eklenir. Eşik bandı {0,20; 0,25; 0,289 = Türkiye'nin 2013 değeri; 0,35} × libdem değeri
         olmayan ülke {düşer (varsayılan) / kalır (Makao tanısı)}; baseline + C1-kapalı 8 hücre × 3 alan. Eşik gerekçesi
         işaretten bağımsızdır: Katar (0,089) Türkiye'nin 2025'te VARDIĞI düzeyin (≈0,11) altındadır; eşik yalnız C1-kapalı fen
         hücrelerini etkiler (bkz. summary.json → level_floor). Geçiş cezası için %95 GA ve %80 güçte saptanabilir en küçük etki
         (MDE = (z_.975 + z_.80) × SE ≈ 2,80 × SE) de yazılır: n = 17 kademeli geçişle literatürün önerdiği −2…−6 saptanamaz.
Çıkarım: placebo-in-space — p_gap = mean(c(tedavi, plasebolar) ≥ tedavi post-ortalama) [03_synth.R ile aynı]; p_ratio = mean(ratios ≥ tedavi ratio).
Girdi: data/derived/analysis_panel.csv, institutional_screen.csv, paper_based_2015.csv, asterisk_cycles.csv; mod haritası bu betikte (kaynaklar aşağıda).
Çıktı: data/derived/donor_ablation/{ablation_grid.csv, donors_by_cell.csv, mode_map.csv, transition_penalty.csv, summary.json,
        grid_vs_old_donor_rule_grid.csv}; analysis/figures/v4_sekil5_spesifikasyon_egrisi.png
Yazan: Claude Fable 5.1 (kod), 2026-09-20. Denetim: bekliyor (Opus 4.8). Adım 23 (prompt "20" dedi; 20–22 dolu).
"""
from __future__ import annotations

import importlib
import itertools
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from scipy.optimize import minimize
from scipy.stats import norm

MDE_MULT = float(norm.ppf(0.975) + norm.ppf(0.80))  # ≈ 2,80: %5 iki-yönlü, %80 güç
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
m17 = importlib.import_module("17_matrix_completion_conformal")
sc_weights_demeaned = m17.sc_weights_demeaned

ROOT = HERE.parent
D = ROOT / "data" / "derived"
OUT = D / "donor_ablation"
OUT.mkdir(parents=True, exist_ok=True)
FIG = ROOT / "analysis" / "figures"
TREATED = "TUR"
OUTCOMES = ["math", "reading", "science"]
PRE_ALL = [2003, 2006, 2009, 2012]
POST = [2015, 2018, 2022, 2025]
INK, BODY, HAIR, ACCENT = "#1A1A1A", "#6E6C67", "#D7D5CF", "#8A3324"

# ---------------------------------------------------------------- veri
panel = pd.read_csv(D / "analysis_panel.csv")
panel = panel[panel.iso3.notna() & (panel.iso3.str.len() == 3)].copy()
panel["cycle"] = panel.cycle.astype(int)
panel["oecd"] = pd.to_numeric(panel.oecd_member, errors="coerce").fillna(0) > 0
screen = pd.read_csv(D / "institutional_screen.csv")
screen["no_episode"] = screen.ert_aut_episodes.isna() & screen.ert_dem_episodes.isna()
cls_of = dict(zip(screen.iso3, screen["class"]))
noep_of = dict(zip(screen.iso3, screen.no_episode))
libdem13 = dict(zip(screen.iso3, screen.libdem_2013))
TUR_LIBDEM13 = float(libdem13["TUR"])  # 0,289 — düzey eşiği tanısı (E bloğu): tarama değişim tarar, düzey taramaz
paper15 = set(pd.read_csv(D / "paper_based_2015.csv").iso3)
ast = pd.read_csv(D / "asterisk_cycles.csv")
ast_pairs = set(zip(ast.iso3, ast.cycle.astype(int)))
oecd_iso = set(panel[panel.oecd].iso3)
names = dict(zip(panel.iso3, panel.country_name))

# ---------------------------------------------------------------- mod haritası (ülke × döngü)
# Kaynaklar: 2003–2012 tüm katılımcılar kâğıt (PISA 2022 TR: "Cognitive units were administered in paper-based format ... until and
#   including PISA 2012"); 2015 kâğıt: paper_based_2015.csv (Jerrim vd. 2018 dipnot 1); 2018 kâğıt: PISA 2018 TR Ch. 1 Annex Table 1.A.2
#   (ARG JOR LBN MDA MKD ROU SAU UKR VNM); 2022 kâğıt: PISA 2022 TR Ch. 11 PBA/new-PBA grubu (Viet Nam, Cambodia, Guatemala, Paraguay) +
#   PISA 2025 TR Ch. 18 "moved from paper- to computer-based ... Viet Nam ... Guatemala and Paraguay"; 2025 kâğıt: PISA 2025 TR Excel T1.A.2
#   (Cambodia, Dushanbe (Tajikistan), Kurdistan Region (Iraq), Mauritius, Rwanda, Zambia).
PAPER = {2003: "ALL", 2006: "ALL", 2009: "ALL", 2012: "ALL",
         2015: set(paper15),
         2018: {"ARG", "JOR", "LBN", "MDA", "MKD", "ROU", "SAU", "UKR", "QUA", "VNM"},
         2022: {"KHM", "GTM", "PRY", "VNM"},
         2025: {"KHM", "QDT", "QKI", "MUS", "RWA", "ZMB"}}
rows = []
for iso, g in panel.groupby("iso3"):
    cyc = sorted(int(c) for c in g.cycle if not np.isnan(g.loc[g.cycle == c, "math_mean"].iloc[0]) or not np.isnan(g.loc[g.cycle == c, "reading_mean"].iloc[0]))
    first_cbt, first_cycle, had_paper = None, (cyc[0] if cyc else None), False
    for c in cyc:
        mode = "paper" if (c < 2015 or iso in PAPER[c]) else "cba"  # 2000–2012: tüm katılımcılar kâğıt
        if mode == "paper":
            had_paper = True
        elif first_cbt is None:
            first_cbt = c
        rows.append(dict(iso3=iso, cycle=c, mode=mode))
    for r in rows:
        if r["iso3"] == iso:
            r["first_cycle"] = first_cycle
            r["first_cbt_cycle"] = first_cbt
            r["transition"] = int(first_cbt is not None and had_paper and r["cycle"] == first_cbt and first_cbt != first_cycle)
            r["first_participation"] = int(r["cycle"] == first_cycle)
mode_map = pd.DataFrame(rows)
mode_map["country"] = mode_map.iso3.map(names)
mode_map.to_csv(OUT / "mode_map.csv", index=False)

# ---------------------------------------------------------------- geçiş cezası (ülke + döngü sabit etkili panel)
def fe_regression(outcome: str, spec: str = "all_transitions") -> dict:
    """spec='all_transitions': tek geçiş kuklası (2015 dâhil; 2015'te 52 sistem birden geçtiği için döngü sabit etkisiyle
    büyük ölçüde karışır). spec='staggered_2018_2022': geçiş kuklası yalnız 2018/2022/2025 geçişleri (kademeli, kontrol grubu
    büyük); 2015 geçişleri ayrı bir kuklayla absorbe edilir."""
    df = panel.merge(mode_map[["iso3", "cycle", "transition", "first_participation"]], on=["iso3", "cycle"], how="inner")
    df = df[df[f"{outcome}_mean"].notna() & (df.cycle >= 2006)].copy()
    y = df[f"{outcome}_mean"].to_numpy(float)
    X_c = pd.get_dummies(df.iso3, drop_first=True).to_numpy(float)
    X_t = pd.get_dummies(df.cycle, drop_first=True).to_numpy(float)
    if spec == "all_transitions":
        tr = df.transition.to_numpy(float)
        extra = []
    else:
        tr = (df.transition.to_numpy(bool) & df.cycle.isin([2018, 2022, 2025]).to_numpy()).astype(float)
        extra = [(df.transition.to_numpy(bool) & (df.cycle == 2015).to_numpy()).astype(float)]
    X = np.column_stack([np.ones(len(df)), tr, df.first_participation.to_numpy(float)] + extra + [X_c, X_t])
    beta, *_ = np.linalg.lstsq(X, y, rcond=None)
    resid = y - X @ beta
    dof = len(y) - X.shape[1]
    s2 = float(resid @ resid / dof)
    XtX_inv = np.linalg.pinv(X.T @ X)
    se = np.sqrt(np.diag(XtX_inv) * s2)
    b, s = float(beta[1]), float(se[1])
    return dict(spec=spec, outcome=outcome, n_obs=int(len(y)), n_countries=int(df.iso3.nunique()), n_transitions=int(tr.sum()),
                beta_transition=b, se_transition=s, t_transition=(b / s if s > 0 else np.nan),
                ci95_lo=b - 1.96 * s, ci95_hi=b + 1.96 * s, mde_80=MDE_MULT * s,  # güç: bu tasarımın saptayabileceği en küçük |β|
                beta_first_participation=float(beta[2]), se_first_participation=float(se[2]))

penalty = pd.DataFrame([fe_regression(o, sp) for sp in ["all_transitions", "staggered_2018_2022"] for o in OUTCOMES])
penalty.to_csv(OUT / "transition_penalty.csv", index=False)
BETA = dict(zip(penalty[penalty.spec == "all_transitions"].outcome, penalty[penalty.spec == "all_transitions"].beta_transition))

# ---------------------------------------------------------------- havuz kurucu (dört bağımsız bayrak)
def wide(outcome: str, cycles: list[int], adjust: str | None = None) -> pd.DataFrame:
    """Geniş matris; adjust ∈ {None, 'donors', 'donors+treated'}: geçiş döngüsündeki puandan β çıkarılır (β<0 → yukarı)."""
    df = panel[["iso3", "cycle", f"{outcome}_mean"]].copy()
    if adjust:
        tr = mode_map[(mode_map.transition == 1)][["iso3", "cycle"]]
        key = set(zip(tr.iso3, tr.cycle))
        adj = np.array([(i, c) in key for i, c in zip(df.iso3, df.cycle)])
        if adjust == "donors":
            adj &= (df.iso3 != TREATED).to_numpy()
        df.loc[adj, f"{outcome}_mean"] = df.loc[adj, f"{outcome}_mean"] - BETA[outcome]
    w = df.pivot_table(index="iso3", columns="cycle", values=f"{outcome}_mean", aggfunc="first").reindex(columns=cycles)
    return w


def libdem_missing(i: str) -> bool:
    v = libdem13.get(i, np.nan)
    return (v is None) or pd.isna(v)


def below_floor(i: str, floor: float, keep_missing: bool = False) -> bool:
    """Eşik testi. Değeri olmayan ülke (V-Dem kapsamı dışı: Makao) testi GEÇEMEZ değil, GİREMEZ — iki durum ayrı raporlanır:
    keep_missing=False → düşer (varsayılan), True → kalır (Makao tanısı)."""
    if libdem_missing(i):
        return not keep_missing
    return float(libdem13[i]) < floor


def build_pool(outcome: str, cycles: list[int], c1_oecd: bool, c2_level: str, c3_paper: str, c4_ast: bool,
               floor: float | None = None, missing_policy: str = "drop") -> tuple[list[str], dict]:
    w = wide(outcome, cycles)
    complete = set(w.dropna(how="any").index) - {TREATED}
    cand = set(complete)
    if c1_oecd:
        cand &= oecd_iso
    if c2_level == "L0":
        cand &= {i for i in cand if cls_of.get(i) == "stable_clean"}
    elif c2_level == "L1":
        cand &= {i for i in cand if cls_of.get(i) in ("stable_clean", "stable_corrupt")}
    elif c2_level == "L2":
        cand &= {i for i in cand if cls_of.get(i) in ("stable_clean", "stable_corrupt") or (cls_of.get(i) == "ambiguous" and noep_of.get(i))}
    elif c2_level == "L3":
        pass
    else:
        raise ValueError(c2_level)
    if floor is not None:  # E bloğu: libdem_2013 ≥ eşik (düzey eşiği); değeri olmayan ülke missing_policy'ye göre düşer/kalır
        cand = {i for i in cand if not below_floor(i, floor, keep_missing=(missing_policy == "keep"))}
    if c3_paper == "on":
        cand -= paper15
    if c4_ast:
        cand -= {i for (i, c) in ast_pairs if c in cycles}
    donors = sorted(cand)
    contamination = dict(treated_classes=sorted(i for i in donors if str(cls_of.get(i, "")).startswith("treated")),
                         ambiguous=sorted(i for i in donors if cls_of.get(i) == "ambiguous"),
                         unscreened=sorted(i for i in donors if i not in cls_of),
                         paper2015=sorted(i for i in donors if i in paper15),
                         asterisk=sorted({f"{i}:{c}" for (i, c) in ast_pairs if i in donors and c in cycles}),
                         non_oecd=sorted(i for i in donors if i not in oecd_iso),
                         below_tur_libdem13=sorted(i for i in donors if (not libdem_missing(i)) and below_floor(i, TUR_LIBDEM13)),
                         libdem_missing=sorted(i for i in donors if libdem_missing(i)))
    return donors, contamination


# ---------------------------------------------------------------- SC + plasebo
def sc_fit(y1: np.ndarray, Y0: np.ndarray, fit_idx: list[int]):
    w = sc_weights_demeaned(y1, Y0, fit_idx)
    gap = (y1 - y1[fit_idx].mean()) - w @ (Y0 - Y0[:, fit_idx].mean(axis=1, keepdims=True))
    pre_rmspe = float(np.sqrt((gap[fit_idx] ** 2).mean()))
    return w, gap, pre_rmspe


def levels_fit(y1: np.ndarray, Y0: np.ndarray, fit_idx: list[int]) -> tuple[float, bool]:
    """Düzey SC (ortalama çıkarılmadan): ön-RMSPE ve dışbükey örtü gerekli koşulu (her ön döngüde min ≤ TUR ≤ max)."""
    J = Y0.shape[0]
    obj = lambda w: float(((y1[fit_idx] - w @ Y0[:, fit_idx]) ** 2).sum())
    res = minimize(obj, np.full(J, 1.0 / J), bounds=[(0, 1)] * J, constraints=({"type": "eq", "fun": lambda w: w.sum() - 1.0},),
                   method="SLSQP", options={"maxiter": 2000, "ftol": 1e-12})
    rmspe = float(np.sqrt(obj(res.x) / len(fit_idx)))
    ok = bool(all(Y0[:, t].min() <= y1[t] <= Y0[:, t].max() for t in fit_idx))
    return rmspe, ok


def run_cell(outcome: str, donors: list[str], adjust: str | None) -> dict:
    pre = [c for c in PRE_ALL if not np.isnan(panel.loc[(panel.iso3 == TREATED) & (panel.cycle == c), f"{outcome}_mean"].iloc[0])] if outcome == "science" else PRE_ALL
    pre = [c for c in pre if c >= 2006] if outcome == "science" else pre
    cycles = pre + POST
    w = wide(outcome, cycles, adjust)
    mat = w.loc[[TREATED] + donors]
    assert not mat.isna().any().any(), (outcome, donors)
    Y = mat.to_numpy(float)
    y1, Y0 = Y[0], Y[1:]
    fit_idx = list(range(len(pre)))
    post_idx = list(range(len(pre), len(cycles)))
    wts, gap, pre_rmspe = sc_fit(y1, Y0, fit_idx)
    post_gap = gap[post_idx]
    post_rmspe = float(np.sqrt((post_gap ** 2).mean()))
    ratio = post_rmspe / pre_rmspe if pre_rmspe > 0 else np.inf
    post_mean = float(post_gap.mean())
    pl_means, pl_ratios = [], []
    for j in range(len(donors)):
        wj, gj, prj = sc_fit(Y0[j], np.delete(Y0, j, axis=0), fit_idx)
        pj = gj[post_idx]
        pl_means.append(float(pj.mean()))
        pl_ratios.append(float(np.sqrt((pj ** 2).mean()) / prj) if prj > 0 else np.inf)
    all_means = np.array([post_mean] + pl_means)
    all_ratios = np.array([ratio] + pl_ratios)
    p_gap = float((all_means >= post_mean).mean())
    p_ratio = float((all_ratios >= ratio).mean())
    rank_gap = int((all_means >= post_mean).sum())
    rank_ratio = int((all_ratios >= ratio).sum())
    lv_rmspe, hull_ok = levels_fit(y1, Y0, fit_idx)
    # tek-donör kırılganlığı: en ağır donör çıkarılınca 2025 açığı ve yeni en ağır donör
    top_i = int(np.argmax(wts))
    if len(donors) >= 3:
        w2, g2, _ = sc_fit(y1, np.delete(Y0, top_i, axis=0), fit_idx)
        d2 = [d for k, d in enumerate(donors) if k != top_i]
        loo_gap = round(float(g2[cycles.index(2025)]), 1)
        loo_top = f"{d2[int(np.argmax(w2))]}={float(w2.max()):.2f}"
    else:
        loo_gap, loo_top = np.nan, ""
    return dict(n_donors=len(donors), loo_top_gap_2025=loo_gap, loo_top_new_top=loo_top, pre=" ".join(map(str, pre)), pre_rmspe=round(pre_rmspe, 2), post_rmspe=round(post_rmspe, 2),
                ratio=round(ratio, 2), gap_2015=round(float(gap[cycles.index(2015)]), 1), gap_2018=round(float(gap[cycles.index(2018)]), 1),
                gap_2022=round(float(gap[cycles.index(2022)]), 1), gap_2025=round(float(gap[cycles.index(2025)]), 1),
                post_gap_mean=round(post_mean, 1), p_gap=round(p_gap, 3), p_ratio=round(p_ratio, 3),
                rank_gap=f"{rank_gap}/{len(all_means)}", rank_ratio=f"{rank_ratio}/{len(all_ratios)}",
                donors_json=json.dumps({d: round(float(x), 3) for d, x in sorted(zip(donors, wts), key=lambda t: -t[1])}),
                top_donor=donors[int(np.argmax(wts))], top_w=round(float(wts.max()), 3),
                levels_pre_rmspe=round(lv_rmspe, 1), convex_hull_ok=hull_ok)


# ---------------------------------------------------------------- hücreler
CRIT = ["C1", "C2", "C3", "C4"]
cells = []
# A. merdiven: 16 hücre (kapalı kombinasyonları), C2 kapalı = L3
for n_off in range(5):
    for off in itertools.combinations(CRIT, n_off):
        cid = "S0" if n_off == 0 else "S" + "".join(c[1] for c in off)
        cells.append(dict(block="A_ladder", cell_id=cid, off_criteria="+".join(off) if off else "none", n_off=n_off,
                          c1=("C1" not in off), c2=("L3" if "C2" in off else "L1"), c3=("off" if "C3" in off else "on"), c4=("C4" not in off), adjust=None))
# B. C2 kademeleri
for lvl in ["L0", "L1", "L2", "L3"]:
    cells.append(dict(block="B_screen_ladder", cell_id=f"B-{lvl}", off_criteria=f"C2={lvl}", n_off=(0 if lvl == "L1" else 1), c1=True, c2=lvl, c3="on", c4=True, adjust=None))
# C. mod-düzeltilmiş havuz — diğerleri baseline
cells.append(dict(block="C_mode_adjusted", cell_id="C3-adj", off_criteria="C3=adj", n_off=1, c1=True, c2="L1", c3="adj", c4=True, adjust="donors"))
cells.append(dict(block="C_mode_adjusted", cell_id="C3-adj+TUR", off_criteria="C3=adj; TUR also adjusted (diagnostic)", n_off=1, c1=True, c2="L1", c3="adj", c4=True, adjust="donors+treated"))
# ek: merdivende C3 kapalı olan hücrelerin adj ikizleri (donör-düzeltmeli); C1 kapalı + C3 adj için TUR-tanı ikizi
for c in [c for c in cells if c["block"] == "A_ladder" and c["c3"] == "off"]:
    cells.append({**c, "block": "A_ladder_adj_twin", "cell_id": c["cell_id"] + "-adj", "off_criteria": c["off_criteria"].replace("C3", "C3=adj"), "c3": "adj", "adjust": "donors"})
cells.append(dict(block="C_mode_adjusted", cell_id="S13-adj+TUR", off_criteria="C1 off; C3=adj; TUR also adjusted (diagnostic)", n_off=2, c1=False, c2="L1", c3="adj", c4=True, adjust="donors+treated"))
# E. düzey eşiği (karar 2): C2'ye "libdem_2013 ≥ eşik" eklenirse ne değişir? Baseline + C1-kapalı 8 hücre; eşik bandı × eksik-değer politikası.
#    Gerekçe (işaretten ÖNCE): tarama değişimi tarar, düzeyi taramaz; kontrol birimi tedavi görmemiş Türkiye'yi temsil etmeli.
#    0,289 = Türkiye'nin kendi 2013 değeri (araştırmacı seçimi) → 0,20 / 0,25 / 0,35 ile bant duyarlılığı. Değeri olmayan ülke (Makao)
#    testi geçemediği için değil, giremediği için düşer → "+nan" ikizinde tutulur; fark ayrı raporlanır.
FLOORS = {"20": 0.20, "25": 0.25, "289": TUR_LIBDEM13, "35": 0.35}
for c in [c for c in cells if c["block"] == "A_ladder" and (c["cell_id"] == "S0" or not c["c1"])]:
    for tag, fl in FLOORS.items():
        for pol in ["drop", "keep"]:
            if tag == "289" and pol == "drop":
                cid, blk = c["cell_id"] + "-lvl", "E_level_floor"  # önceki ad korunur (rapor §9)
            else:
                cid = f"{c['cell_id']}-lvl{tag}" + ("+nan" if pol == "keep" else "")
                blk = "E_level_floor_band" if pol == "drop" else "E_level_floor_missing_kept"
            off = (c["off_criteria"] + f"; +libdem_2013 ≥ {fl:.3f}" + ("; libdem yoksa kalır" if pol == "keep" else "")).replace("none; ", "")
            cells.append({**c, "block": blk, "cell_id": cid, "off_criteria": off, "floor": fl, "missing_policy": pol})

results, donors_rows = [], []
for cell in cells:
    for oc in OUTCOMES:
        pre = [2006, 2009, 2012] if oc == "science" else PRE_ALL
        donors, cont = build_pool(oc, pre + POST, cell["c1"], cell["c2"], cell["c3"], cell["c4"], floor=cell.get("floor"),
                                  missing_policy=cell.get("missing_policy", "drop"))
        if len(donors) < 2:
            results.append({**cell, "outcome": oc, "n_donors": len(donors), "note": "havuz < 2 donör; koşulmadı"})
            continue
        r = run_cell(oc, donors, cell["adjust"])
        note = []
        if cont["treated_classes"]:
            note.append(f"kirlenme: tedavi/otokratikleşen sınıf donörde ({len(cont['treated_classes'])}: {' '.join(cont['treated_classes'])})")
        if cont["unscreened"]:
            note.append(f"taramasız ülke ({len(cont['unscreened'])})")
        if cont["paper2015"]:
            note.append(f"2015 kâğıt ülkeleri havuzda ({' '.join(cont['paper2015'])})" + (" — geçiş döngüsü düzeltildi" if cell["adjust"] else " — mod etkisi kontrol grubuna bulaşır"))
        if cont["asterisk"]:
            note.append(f"yıldızlı ülke-döngü havuzda ({' '.join(cont['asterisk'])})")
        if cont["ambiguous"]:
            note.append(f"ambiguous sınıf ({' '.join(cont['ambiguous'])})")
        results.append({**cell, "outcome": oc, **r, "contamination": cont, "note": "; ".join(note)})
        donors_rows.append(dict(cell_id=cell["cell_id"], block=cell["block"], outcome=oc, donors=" ".join(donors), donors_json=r["donors_json"]))
        print(f"[{cell['cell_id']:12s} {oc:8s}] N0={len(donors):2d} pre-RMSPE {r['pre_rmspe']:5.1f} gap25 {r['gap_2025']:+6.1f} post {r['post_gap_mean']:+6.1f} p_gap {r['p_gap']:.2f} p_ratio {r['p_ratio']:.2f} hull={r['convex_hull_ok']} top {r['top_donor']}={r['top_w']}")

grid = pd.DataFrame(results)
base = {oc: grid[(grid.cell_id == "S0") & (grid.outcome == oc)].iloc[0] for oc in OUTCOMES}
grid["baseline_gap_2025"] = grid.outcome.map({oc: base[oc].gap_2025 for oc in OUTCOMES})
grid["flip_sign"] = np.sign(grid.gap_2025) != np.sign(grid.baseline_gap_2025)
grid["delta_vs_baseline"] = (grid.gap_2025 - grid.baseline_gap_2025).round(1)
grid["contamination"] = grid.contamination.apply(lambda d: json.dumps(d, ensure_ascii=False) if isinstance(d, dict) else "")
grid.to_csv(OUT / "ablation_grid.csv", index=False, encoding="utf-8-sig")
pd.DataFrame(donors_rows).to_csv(OUT / "donors_by_cell.csv", index=False, encoding="utf-8-sig")

# ---------------------------------------------------------------- eski ızgarayla karşılaştırma
old = pd.read_csv(D / "robustness" / "donor_rule_grid.csv")
cmp_rows = []
for _, o in old.iterrows():
    c2 = "L1" if o.pool == "stable_all" else "L2"
    m = grid[(grid.outcome == o.domain) & (grid.c1 == bool(o.oecd_only)) & (grid.c2 == c2) & (grid.c3 == ("on" if bool(o.drop_paper2015) else "off")) & (grid.c4 == bool(o.drop_asterisk)) & (grid.adjust.isna())]
    if len(m):
        n = m.iloc[0]
        cmp_rows.append(dict(domain=o.domain, pool=o.pool, oecd_only=o.oecd_only, drop_asterisk=o.drop_asterisk, drop_paper2015=o.drop_paper2015,
                             old_n=o.n_donors, new_n=n.n_donors, old_gap_2025=o.gap_2025, new_gap_2025=n.gap_2025, old_pre_rmspe=o.pre_rmspe, new_pre_rmspe=n.pre_rmspe,
                             new_cell=n.cell_id, diff_gap=round(n.gap_2025 - o.gap_2025, 2)))
cmp = pd.DataFrame(cmp_rows)
cmp.to_csv(OUT / "grid_vs_old_donor_rule_grid.csv", index=False)

# ---------------------------------------------------------------- özet
A = grid[grid.block == "A_ladder"]
E = grid[grid.block.str.startswith("E_level_floor") & grid.gap_2025.notna()].copy()


def removed_by_floor(r) -> list[str]:
    """Eşikli hücrenin eşiksiz ikizine göre havuzdan düşen donörler."""
    base_id = r.cell_id.split("-lvl")[0]
    base_row = grid[(grid.cell_id == base_id) & (grid.outcome == r.outcome)].iloc[0]
    return sorted(set(json.loads(base_row.donors_json)) - set(json.loads(r.donors_json)))


band_rows = {f"{r.cell_id}|{r.outcome}": dict(base=r.cell_id.split("-lvl")[0], floor=float(r.floor), missing_policy=r.missing_policy, n_donors=int(r.n_donors),
                                             gap_2025=float(r.gap_2025), post_gap_mean=float(r.post_gap_mean), p_gap=float(r.p_gap), p_ratio=float(r.p_ratio),
                                             top=r.top_donor, top_w=float(r.top_w), pre_rmspe=float(r.pre_rmspe), removed=removed_by_floor(r))
             for r in E.itertuples()}
# bant boyunca işaret: taban hücre × alan → {eşik: işaret} (eksik-değer düşürülmüş politika)
band_sign = {}
for r in E[E.missing_policy == "drop"].itertuples():
    band_sign.setdefault(f"{r.cell_id.split('-lvl')[0]}|{r.outcome}", {})[f"{float(r.floor):.3f}"] = int(np.sign(r.gap_2025))
# Makao tanısı: aynı eşikte "düşer" vs "kalır" farkı (yalnız Makao'nun havuza girdiği hücrelerde sıfırdan farklı olabilir)
mac_delta = {}
for r in E[E.missing_policy == "keep"].itertuples():
    twin_id = r.cell_id.replace("+nan", "") if "+nan" in r.cell_id else r.cell_id
    twin_id = twin_id.replace("-lvl289", "-lvl")
    tw = E[(E.cell_id == twin_id) & (E.outcome == r.outcome)]
    if len(tw):
        t = tw.iloc[0]
        kept = sorted(set(json.loads(r.donors_json)) - set(json.loads(t.donors_json)))
        mac_delta[f"{r.cell_id}|{r.outcome}"] = dict(floor=float(r.floor), kept_missing=kept, gap_2025_drop=float(t.gap_2025), gap_2025_keep=float(r.gap_2025),
                                                   delta=round(float(r.gap_2025 - t.gap_2025), 1), top_keep=r.top_donor, top_w_keep=float(r.top_w),
                                                   w_kept_missing={k: json.loads(r.donors_json).get(k) for k in kept})
summary = dict(baseline={oc: dict(gap_2025=float(base[oc].gap_2025), post_gap_mean=float(base[oc].post_gap_mean), pre_rmspe=float(base[oc].pre_rmspe),
                                  n_donors=int(base[oc].n_donors), p_gap=float(base[oc].p_gap), p_ratio=float(base[oc].p_ratio), donors=base[oc].donors_json) for oc in OUTCOMES},
               transition_penalty=penalty.to_dict("records"),
               single_ablation={oc: {r.cell_id: dict(off=r.off_criteria, gap_2025=float(r.gap_2025), delta=float(r.delta_vs_baseline), n_donors=int(r.n_donors), pre_rmspe=float(r.pre_rmspe), p_gap=float(r.p_gap))
                                     for r in A[(A.outcome == oc) & (A.n_off == 1)].itertuples()} for oc in OUTCOMES},
               most_sensitive_single={oc: (lambda s: dict(cell=s.cell_id, off=s.off_criteria, delta=float(s.delta_vs_baseline)))(A[(A.outcome == oc) & (A.n_off == 1)].iloc[A[(A.outcome == oc) & (A.n_off == 1)].delta_vs_baseline.abs().argmax()]) for oc in OUTCOMES},
               flip_cells={oc: [dict(cell=r.cell_id, off=r.off_criteria, gap_2025=float(r.gap_2025), top=r.top_donor, top_w=float(r.top_w), pre_rmspe=float(r.pre_rmspe), loo_top_gap_2025=float(r.loo_top_gap_2025), loo_top_new_top=r.loo_top_new_top) for r in grid[(grid.outcome == oc) & (grid.flip_sign == True)].itertuples()] for oc in OUTCOMES},
               range_ladder={oc: dict(min=float(A[A.outcome == oc].gap_2025.min()), max=float(A[A.outcome == oc].gap_2025.max()), median=float(A[A.outcome == oc].gap_2025.median()),
                                      n_positive=int((A[A.outcome == oc].gap_2025 > 0).sum()), n_cells=int((A.outcome == oc).sum())) for oc in OUTCOMES},
               n_vs_gap_corr={oc: float(np.corrcoef(A[A.outcome == oc].n_donors, A[A.outcome == oc].gap_2025)[0, 1]) for oc in OUTCOMES},
               mode_map=dict(n_transitions_2015=int(((mode_map.transition == 1) & (mode_map.cycle == 2015)).sum()), n_transitions_2018=int(((mode_map.transition == 1) & (mode_map.cycle == 2018)).sum()),
                             n_transitions_2022=int(((mode_map.transition == 1) & (mode_map.cycle == 2022)).sum()), n_transitions_2025=int(((mode_map.transition == 1) & (mode_map.cycle == 2025)).sum()),
                             paper_2025_in_panel=sorted(i for i in PAPER[2025] if i in set(panel.iso3)), paper_2022_in_panel=sorted(i for i in PAPER[2022] if i in set(panel.iso3))),
               old_grid_comparison=dict(n_matched=int(len(cmp)), max_abs_diff_gap=float(cmp.diff_gap.abs().max()) if len(cmp) else None),
               level_floor=dict(tur_libdem_2013=TUR_LIBDEM13, floors=FLOORS, mde_multiplier=MDE_MULT,
                                cells={f"{r.cell_id}|{r.outcome}": dict(n_donors=int(r.n_donors), gap_2025=float(r.gap_2025), post_gap_mean=float(r.post_gap_mean), p_gap=float(r.p_gap),
                                                                        top=r.top_donor, top_w=float(r.top_w), pre_rmspe=float(r.pre_rmspe))
                                       for r in grid[grid.block == "E_level_floor"].itertuples()},
                                removed_vs_unfloored={f"{r.cell_id}|{r.outcome}": removed_by_floor(r) for r in grid[grid.block == "E_level_floor"].itertuples()},
                                band=band_rows, band_sign_by_floor=band_sign, missing_kept_delta=mac_delta),
               notes=["Baseline = S0: C1–C4 açık, C2 = L1 (stable_all), arındırılmış SC, ön 2003–2012 (fen 2006–2012), sonrası 2015–2025.",
                      "p_gap/p_ratio: 03_synth.R tanımı (tedavi dâhil pay). Küçük N0'da erişilebilir en küçük p = 1/(N0+1).",
                      "C3=adj: kâğıt ülkeleri havuzda tutulur, geçiş döngüsündeki puandan β (transition_penalty.csv) çıkarılır; Türkiye düzeltilmez (V4_ICT_MOD_BULGUSU).",
                      "Hiçbir hücre tercih edilen sonuç değildir; rapor tüm dağılımı verir."])
with open(OUT / "summary.json", "w", encoding="utf-8") as fh:
    json.dump(summary, fh, ensure_ascii=False, indent=1, default=float)

# ---------------------------------------------------------------- Şekil 5: spesifikasyon eğrisi (merdiven, 16 hücre × 3 alan)
plt.rcParams.update({"font.family": "sans-serif", "font.sans-serif": ["Liberation Sans", "Arial", "DejaVu Sans"], "font.size": 10})
fig = plt.figure(figsize=(16, 8.5))
gs = fig.add_gridspec(2, 3, height_ratios=[3, 1.35], hspace=0.08, wspace=0.16)
lab = {"math": "Matematik", "reading": "Okuma", "science": "Fen"}
for k, oc in enumerate(OUTCOMES):
    sub = A[A.outcome == oc].sort_values("gap_2025").reset_index(drop=True)
    ax = fig.add_subplot(gs[0, k]); ax2 = fig.add_subplot(gs[1, k], sharex=ax)
    x = np.arange(len(sub))
    ax.axhline(0, color=INK, lw=1.2)
    ax.vlines(x, 0, sub.gap_2025, color=HAIR, lw=1)
    cols = [ACCENT if c == "S0" else (BODY if not f else INK) for c, f in zip(sub.cell_id, sub.flip_sign)]
    sizes = [90 if c == "S0" else 42 for c in sub.cell_id]
    ax.scatter(x, sub.gap_2025, c=cols, s=sizes, zorder=3, edgecolor="white", lw=0.6)
    for xi, (g, n0, pr) in enumerate(zip(sub.gap_2025, sub.n_donors, sub.pre_rmspe)):
        ax.text(xi, g + (2.2 if g >= 0 else -2.2), f"{n0}", ha="center", va="bottom" if g >= 0 else "top", fontsize=7.5, color=BODY)
    ax.set_title(f"{lab[oc]} — baseline {base[oc].gap_2025:+.1f} (N0 = {base[oc].n_donors})", loc="left", fontsize=11.5, color=INK, family="DejaVu Serif")
    ax.set_ylabel("2025 açığı: Türkiye − sentetik (puan)" if k == 0 else "", color=BODY)
    ax.spines[["top", "right"]].set_visible(False); ax.spines[["left", "bottom"]].set_color(HAIR)
    ax.tick_params(colors=BODY, labelbottom=False)
    ax.grid(axis="y", color=HAIR, lw=0.6)
    for j, c in enumerate(CRIT):
        on = sub.off_criteria.apply(lambda s: c not in s.split("+"))
        ax2.scatter(x[on.values], [3 - j] * int(on.sum()), s=34, color=INK, zorder=3)
        ax2.scatter(x[~on.values], [3 - j] * int((~on).sum()), s=34, facecolors="white", edgecolors=BODY, zorder=3)
    ax2.set_yticks([3, 2, 1, 0])
    if k == 0:
        ax2.set_yticklabels(["C1 OECD", "C2 tarama", "C3 kâğıt-2015", "C4 yıldız"], fontsize=8.5, color=BODY)
    else:
        ax2.set_yticklabels([])
    ax2.set_xticks(x); ax2.set_xticklabels(sub.cell_id, rotation=90, fontsize=7.5, color=BODY)
    ax2.set_ylim(-0.7, 3.7); ax2.spines[["top", "right", "left", "bottom"]].set_color(HAIR); ax2.tick_params(colors=BODY)
    ax2.grid(axis="x", color=HAIR, lw=0.5)
fig.suptitle("Şekil 4 · Spesifikasyon eğrisi: dört donör kuralının 16 kombinasyonunda Türkiye'nin 2025 açığı", x=0.01, ha="left",
             fontsize=14, color=INK, family="DejaVu Serif")
fig.text(0.01, 0.005, "Dolu nokta = kriter açık, boş = kapalı. Kırmızı = baseline S0 (C1–C4 açık). Siyah = işaret baseline'a göre dönmüş. Nokta üstündeki sayı = donör sayısı. "
         "Ön dönem 2003–2012 (fen 2006–2012); arındırılmış SC; hiçbir hücre tercih edilen sonuç değildir. Betik: analysis/23_donor_ablation.py [E23].",
         fontsize=8.2, color=BODY)
fig.savefig(FIG / "v4_sekil4_spesifikasyon_egrisi.png", dpi=130, bbox_inches="tight")  # 20 Eyl gece: 5 → 4 (v4'te Şekil 4 yoktu)
plt.close(fig)
print("\nTransition penalty:\n", penalty.round(2).to_string(index=False))
print("\nDONE donor ablation:", len(grid), "rows")
