# -*- coding: utf-8 -*-
"""
50_e9_distribution_of_gains.py — editoryal düzeltme E9: üst dilim / yurt dışı sınav yönelimi alternatifi (kazanımın dağılımı).

Soru (COWORK_AMPIRIK_DUZELTMELER.md E9): Başarılı öğrencilerin artan bir kısmı PISA'ya biçimce yakın yurt dışı sınavlarına
hazırlanıyorsa yükselişin bir bölümü üst dilimdeki gerçek bir biçim/beceri hizalanmasından gelebilir. PISA'da doğrudan ölçü yok;
bu betik kanalın dağılımsal imzasını sınar: (1) kazanım üst yüzdeliklerde mi yoğun, (2) okul türü ve resmî/özel ayrışması
2015→2018 ve 2018→2022'de ne diyor, (3) plasebo artığındaki açılma üst ESCS diliminde mi yoğun, (4) üst dilimin ek kazancı
ortalamaya en fazla ne katabilir.

ÖNCEDEN BELİRLENEN SEÇİMLER (RESULTS_EMPIRICAL_FIXES.md §0.10; commit cdb5456, betik yazılmadan ve koşulmadan önce):
  * Yüzdelikler P10/P25/P50/P75/P90 ve P90 − P10: ağırlıklı ters birikimli dağılım (tam eşitlikte sonraki değerle ortalama);
    PV başına (M = 10) + Rubin; SE BRR (Fay 0,5; W_FSTURWT1–80; yüzdelik her replikasyonda yeniden).
  * Çiftler 2015→2018 ve 2015→2025 birincil; 2018→2022, 2022→2025 rapor; değişim SE'si √(se_a² + se_b²); bağlantı hatası yok.
  * OECD ortalaması: iki döngüde de kestirimi olan, panelde 2025'te OECD üyesi sistemlerin ağırlıksız ortalaması; donörler alan
    başına `_panel_matrix.build_matrix(alan, "stable_all_oecd")`.
  * Okul türü: şema A (betik 48'in iki kategorisi, tüm çiftler), şema B (betik 08'in ince türleri, 2018→2022 ve 2022→2025);
    DFL tabanı çiftin ilk döngüsü. Sektör: SC013Q01TA etiketi public/private; donörlerde Δμ_resmî − Δμ_özel; en az 3 özel okul ve
    100 özel okul öğrencisi şartı.
  * Artık: betik 44 modeli (2015 CLPS için CFG girdisi çalışma anında eklenir; betik 44 değişmez); ESCS beşte birlikleri,
    üst %20 / alt %80; D = c_2025 − c_2015, c_t = r_t(üst %20) − r_t(alt %80).
  * Büyüklük: q ∈ {0,05; 0,10; 0,20}; E_q = Δμ_üst − Δμ_geri kalan; C_q = q × E_q.
  * Karar: elenir ⇔ altı birincil hücrede Δ(P90 − P10) alt sınırı ≤ 0 VE D'nin aralığı 0'ı içeriyor ya da D ≥ 0.
  * Kapılar: kullanılan her sistem × döngü × alan ağırlıklı PV ortalaması panelle ≤ 0,01; adım 3 için 2015 CLPS ≤ 0,001
    (`cps2015_country_means.csv`) ve 2025 CMPS ≤ 0,003 (betik 44 `gates`).
SONRADAN EKLENENLER: 2026-09-26 (yerel koşu 1'den sonra, E9 henüz koşulmadan) — boş STRATUM etiket önbelleğine güvenilmez (betik 48
  ile aynı koruma; kök neden betik 49'daki ayrıştırıcı hatasıydı). Tanım değişmedi.
  2026-09-26 (yerel koşu 2, yazar onayı) — 2025 kapısına belgelenmiş BEL istisnası: yalnız BEL 2025 için tavan 0,02
  (dört alan). BEL'in mikroveri − yayımlanmış farkı mat −0,0031, oku +0,0116, fen +0,0032, CPS +0,0027; betik 51 teşhisi
  "neden bulunamadı" (PUF'ta çekirdek PV'si eksik 1 öğrenci, ağırlık payı %0,02). Diğer bütün sistemlerde eşik değişmedi;
  istisna kapı çıktısına `exceptions` olarak yazılır. Panel kapısında (≤ 0,01) BEL 2025 için aynı tavan; adım 3 betik 44'ün kapısını kullanır.
Girdi: 2015/2018/2022 öğrenci ve okul QQQ .sav zip'leri (betik 08 yolları), 2015 CPS zip'i, 2025 öğrenci/okul PUF zip'leri;
       data/derived/analysis_panel.csv; data/derived/cps2015_country_means.csv; data/derived/mechanisms/placebo_conditional_{2015cps,2025}.csv.
Çıktı: data/derived/empirical_fixes/e9_quantile_changes.csv, e9_school_type_sector.csv, e9_residual_by_escs.csv,
       e9_magnitude_bound.csv, e9_summary.json (+ önbellek data/derived/cache/e9_*.parquet).
Kullanım (Windows; pyreadstat + pyarrow): python analysis/50_e9_distribution_of_gains.py [--steps 1,2,3,4]
Yazan: Claude Code (bulut oturumu), 2026-09-26. Bu oturumda mikroveri yoktu: betik yalnız sentetik veriyle duman testinden geçti.
"""
from __future__ import annotations

import argparse
import importlib
import json
import os
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE))
m44 = importlib.import_module("44_e5_coverage_matched_2003")
m48 = importlib.import_module("48_e6_trough_composition")
m49 = importlib.import_module("49_e8_frame_bounds")
import _panel_matrix as PM  # noqa: E402

D = ROOT / "data" / "derived"
OUT = D / "empirical_fixes"
CACHE = D / "cache"
CYCLES = [2015, 2018, 2022, 2025]
DOMS = {"math": "MATH", "reading": "READ", "science": "SCIE"}
M = 10
REPW = [f"W_FSTURWT{i}" for i in range(1, 81)]
FAY_MULT = 1.0 / (80 * (1 - 0.5) ** 2)
QS = [0.10, 0.25, 0.50, 0.75, 0.90]
QNAMES = ["P10", "P25", "P50", "P75", "P90"]
PAIRS_PRIMARY = [(2015, 2018), (2015, 2025)]
PAIRS = PAIRS_PRIMARY + [(2018, 2022), (2022, 2025)]
TYPE_PAIRS_B = [(2018, 2022), (2022, 2025)]
TAIL_QS = [0.05, 0.10, 0.20]
CNT_MAP = {"TAP": "TWN", "KSV": "XKX", "QCH": "CHN"}
SCH = {  # betik 08'deki okul dosyaları
    2015: ("data/pisa_microdata/2015/PUF_SPSS_COMBINED_CMB_SCH_QQQ.zip", "_SCH_QQQ.sav"),
    2018: ("data/pisa_microdata/2018/SPSS_SCH_QQQ.zip", "_SCH_QQQ.sav"),
    2022: ("data/pisa_microdata/2022/SCH_QQQ_SPSS.zip", "_SCH_QQQ.sav"),
    2025: ("data/pisa/2025/database/CY09_MS_SCH_PUF.zip", "_SCH_PUF.sav"),
}


# ----------------------------------------------------------------------------- sınıflama
def fine_type(label: str) -> str | None:
    """Betik 08 `classify()` belirteç sırası (08 içe aktarılınca koştuğu için burada aynen yinelendi)."""
    L = label or ""
    rules = [("BASIC EDUCATION", "ortaokul"), ("GENERAL SECONDARY", "genel_ortaogretim_2015"),
             ("VOCATIONAL AND TECHNICAL SECONDARY", "meslek_2015"), ("Lower-Secondary", "ortaokul"), ("Science High", "fen"),
             ("Social Sciences", "sosyal"), ("Imam and Preacher", "imam_hatip"), ("Vocational and Technical", "meslek"),
             ("Multi-Programme", "cok_programli"), ("Sport", "spor_guzel"), ("Fine Arts", "spor_guzel"),
             ("Private General", "ozel_genel"), ("Private Vocational", "ozel_meslek"), ("Anatolian High", "anadolu")]
    for tok, code in rules:
        if tok in L:
            return code
    return None


def sector_of(label: str) -> str | None:
    L = (label or "").lower()
    return "resmi" if "public" in L else ("ozel" if "private" in L else None)


# ----------------------------------------------------------------------------- veri
def _read(zp: Path, suffix: str, cols: list[str], td: str, label_var: str | None):
    import pyreadstat
    with zipfile.ZipFile(zp) as z:
        name = [n for n in z.namelist() if n.lower().endswith(suffix.lower())][0]
        try:
            z.extract(name, td)
        except NotImplementedError:
            r = subprocess.run(["unzip", "-o", "-q", str(zp), name, "-d", td], capture_output=True, text=True)
            if r.returncode != 0:
                raise SystemExit(f"DUR: unzip başarısız: {r.stderr[:300]}")
    sav = str(Path(td) / name)
    _, meta = pyreadstat.read_sav(sav, metadataonly=True)
    have = {c.upper(): c for c in meta.column_names}
    miss = [c for c in cols if c.upper() not in have]
    if miss:
        raise SystemExit(f"DUR: {zp.name} içinde yok: {miss[:8]}")
    df, meta = pyreadstat.read_sav(sav, usecols=[have[c.upper()] for c in cols])
    labels = {m49._norm_code(k): str(v) for k, v in meta.variable_value_labels.get(have[label_var.upper()], {}).items()} if label_var else {}
    df.columns = [c.upper() for c in df.columns]
    os.remove(sav)
    return df, labels


def selected_units() -> tuple[set, dict]:
    panel = pd.read_csv(D / "analysis_panel.csv")
    p = panel[panel.cycle == 2025]
    oecd = set(p[pd.to_numeric(p.oecd_member, errors="coerce").fillna(0) > 0].iso3)
    donors = {dom: [c for c in PM.build_matrix(dom, "stable_all_oecd").index if c != "TUR"] for dom in DOMS}
    return oecd | {c for v in donors.values() for c in v} | {"TUR"}, {"oecd": sorted(oecd), **donors}


def load_cycle(cyc: int, units: set) -> tuple[pd.DataFrame, dict]:
    """Öğrenci verisi (seçili sistemler) + okul sektörü; STRATUM etiketleri. Parquet önbellekli."""
    stu_c, lab_c = CACHE / f"e9_stu_{cyc}.parquet", CACHE / f"e9_stu_{cyc}_labels.json"
    if stu_c.exists() and lab_c.exists():
        labels = json.loads(lab_c.read_text(encoding="utf-8"))
        if labels:  # SONRADAN: boş etiket önbelleğine güvenilmez, veri yeniden okunur
            return pd.read_parquet(stu_c), labels
    cols = ["CNT", "CNTSCHID", "STRATUM", "W_FSTUWT", "ESCS"] + REPW + [f"PV{i}{r}" for i in range(1, M + 1) for r in DOMS.values()]
    with tempfile.TemporaryDirectory(prefix=f"e9_{cyc}_", dir=os.environ.get("PISA_TMP")) as td:
        zp, suf = m48.SAV[cyc]
        df, labels = _read(ROOT / zp, suf, cols, td, "STRATUM")
        df["CNT"] = df["CNT"].astype(str).str.strip().replace(CNT_MAP)
        df = df[df.CNT.isin(units)].reset_index(drop=True)
        zs, sufs = SCH[cyc]
        sch, sclab = _read(ROOT / zs, sufs, ["CNT", "CNTSCHID", "SC013Q01TA"], td, "SC013Q01TA")
    sch["CNT"] = sch["CNT"].astype(str).str.strip().replace(CNT_MAP)
    sch["SECTOR"] = sch.SC013Q01TA.map(lambda v: sector_of(sclab.get(m49._norm_code(v), "")) if pd.notna(v) else None)
    df = df.merge(sch[["CNT", "CNTSCHID", "SECTOR"]].drop_duplicates(["CNT", "CNTSCHID"]), on=["CNT", "CNTSCHID"], how="left")
    CACHE.mkdir(parents=True, exist_ok=True)
    df.to_parquet(stu_c, index=False)
    lab_c.write_text(json.dumps(labels, ensure_ascii=False), encoding="utf-8")
    return df, labels


def load_2015_cps() -> pd.DataFrame:
    cache = CACHE / "e9_2015_cps.parquet"
    if cache.exists():
        return pd.read_parquet(cache)
    ids = ["CNT", "CNTSCHID", "CNTSTUID"]
    with tempfile.TemporaryDirectory(prefix="e9_cps_", dir=os.environ.get("PISA_TMP")) as td:
        q, _ = _read(ROOT / "data/pisa_microdata/2015/PUF_SPSS_COMBINED_CMB_STU_QQQ.zip", "_QQQ.sav",
                     ids + ["W_FSTUWT", "ESCS"] + REPW + [f"PV{i}{r}" for i in range(1, M + 1) for r in DOMS.values()], td, None)
        c, _ = _read(ROOT / "data/pisa_microdata/2015/PUF_SPSS_COMBINED_CMB_STU_CPS.zip", "_CPS.sav",
                     ids + [f"PV{i}CLPS" for i in range(1, M + 1)], td, None)
    df = c.merge(q, on=ids, how="left", validate="one_to_one")
    df["CNT"] = df["CNT"].astype(str).str.strip().replace(CNT_MAP)
    CACHE.mkdir(parents=True, exist_ok=True)
    df.to_parquet(cache, index=False)
    return df


def numeric(df: pd.DataFrame) -> pd.DataFrame:
    for c in df.columns:
        if c not in ("CNT", "STRATUM", "SECTOR"):
            df[c] = pd.to_numeric(df[c], errors="coerce")
    return df


PANEL_GATE_EXCEPTIONS: list[str] = []  # SONRADAN: kullanılan BEL istisnaları (özet dosyasına yazılır)


def panel_gate(cyc: int, df: pd.DataFrame) -> list[str]:
    panel = pd.read_csv(D / "analysis_panel.csv")
    p = panel[panel.cycle == cyc].set_index("iso3")
    fails = []
    for cn, g in df.groupby("CNT"):
        if cn not in p.index:
            continue
        w = g.W_FSTUWT.to_numpy(float)
        for dom, root in DOMS.items():
            pub = p.loc[cn, f"{dom}_mean"]
            if pd.isna(pub):
                continue
            vals = []
            for i in range(1, M + 1):
                y = g[f"PV{i}{root}"].to_numpy(float)
                ok = np.isfinite(y)
                vals.append(np.sum(w[ok] * y[ok]) / np.sum(w[ok]))
            diff = abs(float(np.mean(vals)) - float(pub))
            ceil = m44.m43_ceiling(cn) if cyc == 2025 else None
            if ceil is not None and 0.01 < diff <= ceil:
                PANEL_GATE_EXCEPTIONS.append(f"{cyc} {cn} {dom}: {diff:.5f} (tavan {ceil})")
                continue
            if diff > 0.01:
                fails.append(f"{cyc} {cn} {dom}: {np.mean(vals):.3f} vs {pub}")
    return fails


# ----------------------------------------------------------------------------- adım 1: yüzdelikler
def wquant(y: np.ndarray, W: np.ndarray, qs: list[float]) -> np.ndarray:
    """Ağırlıklı ters birikimli dağılım; W: n × G; döner G × len(qs)."""
    order = np.argsort(y, kind="mergesort")
    ys, Ws = y[order], W[order]
    share = np.cumsum(Ws, axis=0) / Ws.sum(axis=0)
    G, n = W.shape[1], len(y)
    out = np.empty((G, len(qs)))
    cols = np.arange(G)
    for k, q in enumerate(qs):
        idx = np.minimum((share < q - 1e-12).sum(axis=0), n - 1)
        val = ys[idx]
        eq = np.abs(share[idx, cols] - q) <= 1e-12
        nxt = ys[np.minimum(idx + 1, n - 1)]
        out[:, k] = np.where(eq, (val + nxt) / 2, val)
    return out


def rubin(theta0: np.ndarray, reps: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """theta0: M × K; reps: G × M × K. Döner: K nokta, K SE."""
    v_s = (FAY_MULT * ((reps - theta0[None]) ** 2).sum(axis=0)).mean(axis=0)
    v_i = (1 + 1 / theta0.shape[0]) * theta0.var(axis=0, ddof=1)
    return theta0.mean(axis=0), np.sqrt(v_s + v_i)


def country_quantiles(g: pd.DataFrame) -> dict:
    W = np.column_stack([g.W_FSTUWT.to_numpy(float)] + [g[c].to_numpy(float) for c in REPW])
    out = {}
    for dom, root in DOMS.items():
        th = np.empty((W.shape[1], M, len(QS) + 1))
        for p in range(M):
            y = g[f"PV{p + 1}{root}"].to_numpy(float)
            ok = np.isfinite(y)
            q = wquant(y[ok], W[ok], QS)
            th[:, p, :len(QS)] = q
            th[:, p, -1] = q[:, -1] - q[:, 0]
        est, se = rubin(th[0], th[1:])
        out[dom] = (est, se)
    return out


def step1(qstats: dict, groups: dict) -> tuple[pd.DataFrame, dict]:
    stats = QNAMES + ["P90-P10"]
    rows = []
    for (cyc, cn), per in qstats.items():
        for dom, (est, se) in per.items():
            for k, s in enumerate(stats):
                rows.append({"kind": "level", "unit": cn, "domain": dom, "stat": s, "period": str(cyc),
                             "estimate": float(est[k]), "se": float(se[k])})
    lev = pd.DataFrame(rows)
    ch = []
    for a, b in PAIRS:
        la = lev[lev.period == str(a)].set_index(["unit", "domain", "stat"])
        lb = lev[lev.period == str(b)].set_index(["unit", "domain", "stat"])
        common = la.index.intersection(lb.index)
        d = pd.DataFrame({"estimate": lb.loc[common, "estimate"] - la.loc[common, "estimate"],
                          "se": np.sqrt(lb.loc[common, "se"] ** 2 + la.loc[common, "se"] ** 2)}).reset_index()
        d["kind"], d["period"] = "change", f"{a}->{b}"
        ch.append(d)
        for dom in DOMS:
            for s in stats:
                x = d[(d.domain == dom) & (d.stat == s)].set_index("unit")
                for tag, members in (("OECD_ORT", groups["oecd"]), ("DONOR_ORT", groups[dom])):
                    mm = [c for c in members if c in x.index]
                    if not mm:
                        continue
                    K = len(mm)
                    ch.append(pd.DataFrame([{"unit": tag, "domain": dom, "stat": s, "kind": "change", "period": f"{a}->{b}",
                                             "estimate": float(x.loc[mm, "estimate"].mean()),
                                             "se": float(np.sqrt((x.loc[mm, "se"] ** 2).sum()) / K), "n_units": K}]))
                om = [c for c in groups["oecd"] if c in x.index]
                if "TUR" in om:
                    K = len(om)
                    rest = [c for c in om if c != "TUR"]
                    est = float(x.loc["TUR", "estimate"] - x.loc[om, "estimate"].mean())
                    se = float(np.sqrt((x.loc["TUR", "se"] * (1 - 1 / K)) ** 2 + (x.loc[rest, "se"] ** 2).sum() / K ** 2))
                    ch.append(pd.DataFrame([{"unit": "TUR-OECD_ORT", "domain": dom, "stat": s, "kind": "change",
                                             "period": f"{a}->{b}", "estimate": est, "se": se, "n_units": K}]))
    t = pd.concat([lev] + ch, ignore_index=True)
    t["lo95"], t["hi95"] = t.estimate - 1.96 * t.se, t.estimate + 1.96 * t.se
    prim = t[(t.unit == "TUR") & (t.stat == "P90-P10") & (t.kind == "change") &
             t.period.isin([f"{a}->{b}" for a, b in PAIRS_PRIMARY])]
    cond1 = bool(len(prim) == 6 and (prim.lo95 <= 0).all())
    return t, {"cond1_all_lo95_le_0": cond1, "n_primary_cells": int(len(prim)),
               "breaking_cells": prim[prim.lo95 > 0][["period", "domain", "estimate", "lo95", "hi95"]].to_dict("records")}


# ----------------------------------------------------------------------------- adım 2: okul türü ve sektör
def decompose(cyc_objs: dict, a: int, b: int) -> list[dict]:
    A, B = cyc_objs[a], cyc_objs[b]

    def T(c):
        return lambda st: cyc_objs[c].get(cyc_objs[c].mu, st[c])

    def RW(st):
        tot = 0.0
        for g in A.cats:
            if g not in B.cm:
                return np.nan
            tot += A.sh[g][st[a][0]] * B.get(B.cm[g], st[b])
        return tot

    used = {a: A, b: B}
    rows = []
    for kind, fn in (("total", lambda st: T(b)(st) - T(a)(st)), ("within_type", lambda st: RW(st) - T(a)(st)),
                     ("composition", lambda st: T(b)(st) - RW(st))):
        est, se = m48.evaluate(fn, used)
        rows.append({"quantity": kind, "category": "", "estimate": est, "se": se})
    for g in sorted(set(A.cats) & set(B.cats)):
        est, se = m48.evaluate(lambda st, g=g: B.get(B.cm[g], st[b]) - A.get(A.cm[g], st[a]), used)
        rows.append({"quantity": "within_gain", "category": g, "estimate": est, "se": se})
        est, se = m48.evaluate(lambda st, g=g: float(B.sh[g][st[b][0]] - A.sh[g][st[a][0]]), used)
        rows.append({"quantity": "share_change", "category": g, "estimate": est, "se": se})
    return rows


def sector_ok(g: pd.DataFrame) -> bool:
    pr = g[g.SECTOR == "ozel"]
    return pr.CNTSCHID.nunique() >= 3 and len(pr) >= 100


# ----------------------------------------------------------------------------- adım 3: artığın ESCS dağılımı
def slice_theta(e: np.ndarray, key: np.ndarray, W: np.ndarray, sel) -> np.ndarray:
    ok = np.isfinite(key)
    th = np.empty((W.shape[1], e.shape[1]))
    for j in range(W.shape[1]):
        w = W[:, j]
        rk = np.full(len(w), np.nan)
        rk[ok] = m44.wrank(key[ok], w[ok])
        s = ok & sel(rk)
        for p in range(e.shape[1]):
            s2 = s & np.isfinite(e[:, p])
            th[j, p] = np.sum(w[s2] * e[s2, p]) / np.sum(w[s2])
    return th


def step3() -> tuple[pd.DataFrame, dict]:
    m44.CFG[2015] = dict(M=10, new="CLPS", repw=REPW, school="CNTSCHID", sysfile="placebo_conditional_2015cps.csv", sysfilter={})
    d15 = numeric(load_2015_cps())
    ours = pd.read_csv(D / "cps2015_country_means.csv", encoding="utf-8-sig")
    diffs = []
    for cn, g in d15.groupby("CNT"):
        r = ours[ours.iso3 == cn]
        if len(r):
            w = g.W_FSTUWT.to_numpy(float)
            v = [np.nansum(w * g[f"PV{i}CLPS"].to_numpy(float)) / np.nansum(w * np.isfinite(g[f"PV{i}CLPS"].to_numpy(float)))
                 for i in range(1, M + 1)]
            diffs.append(abs(float(np.mean(v)) - float(r.cps2015_mean_weighted.iloc[0])))
    gate15 = {"n": len(diffs), "max_abs_diff": round(max(diffs), 5) if diffs else None}
    if not diffs or max(diffs) > 0.001:
        raise SystemExit(f"DUR: 2015 CLPS kapısı geçmedi: {gate15}")
    d25 = m44.load(2025)
    g25 = m44.gates(2025, d25)
    if g25["failed"]:
        raise SystemExit(f"DUR: 2025 kapısı geçmedi: {g25['failed']}")
    sels = {"Q1": lambda r: r <= 0.2, "Q2": lambda r: (r > 0.2) & (r <= 0.4), "Q3": lambda r: (r > 0.4) & (r <= 0.6),
            "Q4": lambda r: (r > 0.6) & (r <= 0.8), "Q5": lambda r: r > 0.8, "ust20": lambda r: r > 0.8, "alt80": lambda r: r <= 0.8,
            "all": lambda r: np.isfinite(r)}
    rows, th_store, info = [], {}, {"gate_2015_clps": gate15, "gate_2025": g25}
    for cyc, df in ((2015, d15), (2025, d25)):
        sysset = m44.systems(cyc, "all")
        present = sorted(set(sysset) & set(df.CNT))
        coefs, rsd, r2 = m44.fit_model(cyc, df[df.CNT.isin(present)], present)
        info[str(cyc)] = {"n_systems": len(present), "resid_sd_unit": round(rsd, 4), "r2_by_pv": [round(x, 4) for x in r2]}
        t = df[df.CNT == "TUR"].reset_index(drop=True)
        e = m44.residuals(cyc, t, coefs)
        W = np.column_stack([t.W_FSTUWT.to_numpy(float)] + [t[c].to_numpy(float) for c in REPW])
        key = t.ESCS.to_numpy(float)
        for name, sel in sels.items():
            th = slice_theta(e, key, W, sel)
            th_store[(cyc, name)] = th
            est, se = m44.rubin(th[0], th[1:])
            rows.append({"period": str(cyc), "slice": name, "estimate": est, "se": se, "resid_sd_unit": rsd, "estimate_sd": est / rsd})
        c = th_store[(cyc, "ust20")] - th_store[(cyc, "alt80")]
        est, se = m44.rubin(c[0], c[1:])
        rows.append({"period": str(cyc), "slice": "karsitlik_ust20_alt80", "estimate": est, "se": se, "resid_sd_unit": rsd,
                     "estimate_sd": est / rsd})
        est, se, _ = m44.slice_stats(e, key, W, ("gradient", None))
        rows.append({"period": str(cyc), "slice": "gradyan", "estimate": est, "se": se, "resid_sd_unit": rsd, "estimate_sd": est / rsd})
    t = pd.DataFrame(rows)
    ch = []
    for sl in list(sels) + ["karsitlik_ust20_alt80", "gradyan"]:
        a = t[(t.period == "2015") & (t.slice == sl)].iloc[0]
        b = t[(t.period == "2025") & (t.slice == sl)].iloc[0]
        ch.append({"period": "2015->2025", "slice": sl, "estimate": b.estimate - a.estimate, "se": float(np.hypot(a.se, b.se)),
                   "resid_sd_unit": None, "estimate_sd": b.estimate_sd - a.estimate_sd})
    t = pd.concat([t, pd.DataFrame(ch)], ignore_index=True)
    t["lo95"], t["hi95"] = t.estimate - 1.96 * t.se, t.estimate + 1.96 * t.se
    Drow = t[(t.period == "2015->2025") & (t.slice == "karsitlik_ust20_alt80")].iloc[0]
    top_specific = bool(Drow.estimate < 0 and Drow.hi95 < 0)
    info["D"] = {"estimate": float(Drow.estimate), "lo95": float(Drow.lo95), "hi95": float(Drow.hi95), "top_specific": top_specific}
    return t, info


# ----------------------------------------------------------------------------- adım 4: büyüklük sınırı
def tail_theta(g: pd.DataFrame, root: str, q: float) -> np.ndarray:
    """Döngü içi: G × M × 3 (üst q ortalaması, geri kalan ortalaması, tüm ortalama); üst = ağırlıklı orta sıra > 1 − q."""
    W = np.column_stack([g.W_FSTUWT.to_numpy(float)] + [g[c].to_numpy(float) for c in REPW])
    th = np.empty((W.shape[1], M, 3))
    for p in range(M):
        y = g[f"PV{p + 1}{root}"].to_numpy(float)
        ok = np.isfinite(y)
        yy = y[ok]
        for j in range(W.shape[1]):
            w = W[ok, j]
            top = m44.wrank(yy, w) > 1 - q
            th[j, p] = [np.average(yy[top], weights=w[top]), np.average(yy[~top], weights=w[~top]), np.average(yy, weights=w)]
    return th


def step4(tur: dict) -> pd.DataFrame:
    rows = []
    for dom, root in DOMS.items():
        for q in TAIL_QS:
            th = {c: tail_theta(tur[c], root, q) for c in {x for pr in PAIRS_PRIMARY for x in pr}}
            for a, b in PAIRS_PRIMARY:
                ka = th[a][..., 0] - th[a][..., 1]
                kb = th[b][..., 0] - th[b][..., 1]
                ea, sa = m44.rubin(ka[0], ka[1:])
                eb, sb = m44.rubin(kb[0], kb[1:])
                ma, _ = m44.rubin(th[a][0, :, 2], th[a][1:, :, 2])
                mb, _ = m44.rubin(th[b][0, :, 2], th[b][1:, :, 2])
                E, seE = eb - ea, float(np.hypot(sa, sb))
                rows.append({"period": f"{a}->{b}", "domain": dom, "q": q, "E_q": E, "E_q_se": seE, "C_q": q * E,
                             "C_q_lo95": q * (E - 1.96 * seE), "C_q_hi95": q * (E + 1.96 * seE), "delta_mean_all": mb - ma,
                             "C_q_share_of_delta": (q * E) / (mb - ma) if (mb - ma) != 0 else np.nan})
    return pd.DataFrame(rows)


# ----------------------------------------------------------------------------- ana akış
def _write(df: pd.DataFrame, name: str):
    OUT.mkdir(parents=True, exist_ok=True)
    tmp = OUT / f"{name}.tmp"
    df.to_csv(tmp, index=False, encoding="utf-8")
    os.replace(tmp, OUT / name)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--steps", default="1,2,3,4")
    steps = {int(s) for s in ap.parse_args().steps.split(",")}
    units, groups = selected_units()
    summ = {"note": "E9 — kazanımın dağılımı / üst dilim alternatifi; ön-belirleme §0.10 (commit cdb5456).",
            "groups": groups, "gates": {}}
    qstats, tur, strata, sect_objs, type_objs = {}, {}, [], {}, {"A": {}, "B": {}}
    if steps & {1, 2, 4}:
        for cyc in CYCLES:
            df, labels = load_cycle(cyc, units)
            df = numeric(df)
            fails = panel_gate(cyc, df)
            summ["gates"][str(cyc)] = fails or "geçti"
            summ["gate_exceptions_2025"] = list(PANEL_GATE_EXCEPTIONS)
            if fails:
                raise SystemExit(f"DUR: panel kapısı geçmedi: {fails[:5]}")
            for cn, g in df.groupby("CNT"):
                if 1 in steps:
                    qstats[(cyc, cn)] = country_quantiles(g)
                if 2 in steps and g.SECTOR.notna().any():
                    h = g[g.SECTOR.notna()].reset_index(drop=True)
                    sect_objs[(cyc, cn)] = ({dom: m48.Cycle(cyc, h, h.SECTOR.to_numpy(object), dom) for dom in DOMS}, sector_ok(h))
            t = df[df.CNT == "TUR"].reset_index(drop=True)
            tur[cyc] = t
            codes = t.STRATUM.map(m49._norm_code)
            labs = [labels.get(c, "(etiket yok)") for c in codes]
            catA = [m48.classify(x)[0] for x in labs]
            catB = [fine_type(x) for x in labs]
            for c, lab, a_, b_ in set(zip(codes, labs, catA, catB)):
                strata.append({"cycle": cyc, "stratum": c, "label": lab, "schemeA": a_, "schemeB": b_})
            if 2 in steps:
                if any(x is None for x in catA) or (cyc >= 2018 and any(x is None for x in catB)):
                    _write(pd.DataFrame(strata), "e9_strata_map.csv")
                    raise SystemExit(f"DUR: {cyc} sınıflanamayan Türkiye tabakası (e9_strata_map.csv)")
                type_objs["A"][cyc] = {dom: m48.Cycle(cyc, t, np.array(catA, dtype=object), dom) for dom in DOMS}
                if cyc >= 2018:
                    type_objs["B"][cyc] = {dom: m48.Cycle(cyc, t, np.array(catB, dtype=object), dom) for dom in DOMS}
            del df
    if 1 in steps:
        q, c1 = step1(qstats, groups)
        _write(q, "e9_quantile_changes.csv")
        summ["step1"] = c1
    if 2 in steps:
        rows = []
        for a, b in [(2015, 2018), (2018, 2022), (2022, 2025)]:
            for dom in DOMS:
                objs = {c: type_objs["A"][c][dom] for c in (a, b)}
                rows += [{"analysis": "tur_schemeA", "period": f"{a}->{b}", "domain": dom, "unit": "TUR", **r} for r in decompose(objs, a, b)]
                if (a, b) in TYPE_PAIRS_B:
                    objs = {c: type_objs["B"][c][dom] for c in (a, b)}
                    rows += [{"analysis": "tur_schemeB", "period": f"{a}->{b}", "domain": dom, "unit": "TUR", **r} for r in decompose(objs, a, b)]
                gaps = {}
                for cn in sorted({k[1] for k in sect_objs}):
                    if (a, cn) not in sect_objs or (b, cn) not in sect_objs:
                        continue
                    (oa, ok_a), (ob, ok_b) = sect_objs[(a, cn)], sect_objs[(b, cn)]
                    A, B = oa[dom], ob[dom]
                    if not {"resmi", "ozel"} <= set(A.cats) or not {"resmi", "ozel"} <= set(B.cats):
                        continue
                    used = {a: A, b: B}
                    est, se = m48.evaluate(lambda st: (B.get(B.cm["resmi"], st[b]) - A.get(A.cm["resmi"], st[a]))
                                           - (B.get(B.cm["ozel"], st[b]) - A.get(A.cm["ozel"], st[a])), used)
                    eligible = bool(ok_a and ok_b)
                    gaps[cn] = (est, se, eligible)
                    rows.append({"analysis": "sector_gap", "period": f"{a}->{b}", "domain": dom, "unit": cn,
                                 "quantity": "gain_resmi_minus_ozel", "category": "" if eligible else "özel okul şartı sağlanmadı",
                                 "estimate": est, "se": se})
                    if cn == "TUR":
                        rows += [{"analysis": "tur_sector", "period": f"{a}->{b}", "domain": dom, "unit": "TUR", **r}
                                 for r in decompose({a: A, b: B}, a, b)]
                for tag, members in (("OECD_ORT", groups["oecd"]), ("DONOR_ORT", groups[dom])):
                    mm = [c for c in members if c in gaps and gaps[c][2]]
                    if mm:
                        rows.append({"analysis": "sector_gap", "period": f"{a}->{b}", "domain": dom, "unit": tag,
                                     "quantity": "gain_resmi_minus_ozel", "category": f"n={len(mm)}",
                                     "estimate": float(np.mean([gaps[c][0] for c in mm])),
                                     "se": float(np.sqrt(sum(gaps[c][1] ** 2 for c in mm)) / len(mm))})
        s2 = pd.DataFrame(rows)
        s2["lo95"], s2["hi95"] = s2.estimate - 1.96 * s2.se, s2.estimate + 1.96 * s2.se
        _write(s2, "e9_school_type_sector.csv")
        _write(pd.DataFrame(strata).drop_duplicates(), "e9_strata_map.csv")
    if 4 in steps:
        _write(step4(tur), "e9_magnitude_bound.csv")
    if 3 in steps:
        r3, info3 = step3()
        _write(r3, "e9_residual_by_escs.csv")
        summ["step3"] = info3
    if {1, 3} <= steps:
        cond1, cond2 = summ["step1"]["cond1_all_lo95_le_0"], not summ["step3"]["D"]["top_specific"]
        summ["decision"] = {"cond1_p90p10_not_positive": cond1, "cond2_widening_not_top_specific": cond2,
                            "verdict": ("yurt dışı sınav yönelimi yükselişin ve genişlemenin açıklaması olarak elenir" if cond1 and cond2
                                        else "ek alternatif olarak raporlanır (koşulu bozan hücreler step1.breaking_cells / step3.D)")}
    tmp = OUT / "e9_summary.json.tmp"
    OUT.mkdir(parents=True, exist_ok=True)
    tmp.write_text(json.dumps(summ, ensure_ascii=False, indent=1, default=float), encoding="utf-8")
    os.replace(tmp, OUT / "e9_summary.json")
    print(json.dumps({k: v for k, v in summ.items() if k in ("gates", "step1", "decision")}, ensure_ascii=False, indent=1, default=float))
    return 0


if __name__ == "__main__":
    sys.exit(main())
