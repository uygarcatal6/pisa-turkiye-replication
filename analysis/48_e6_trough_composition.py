# -*- coding: utf-8 -*-
"""
48_e6_trough_composition.py — editoryal düzeltme E6 (F8; düşük öncelik): 2015 çukuru okul türü bileşiminden mi geliyor?

Soru (COWORK_AMPIRIK_DUZELTMELER.md E6): 2018–25 SDiD etkisinin yarısı 2015 çukurundan geliyor [137]; Bakanlık 2015 düşüşünü
mesleki öğrenci payına bağladı [64]; 2015 aynı zamanda F3'ün baz yılı. 2012→2015 ve 2015→2025 puan değişimleri okul türü
bileşimi ve tür içi değişim olarak nasıl ayrışıyor?

ÖNCEDEN BELİRLENEN SEÇİMLER (RESULTS_EMPIRICAL_FIXES.md §0.7; commit 476fe4e, koşudan önce):
  * Türkiye; döngüler 2012, 2015, 2018, 2022, 2025; alanlar mat/oku/fen.
  * Birincil iki kategori: mesleki (STRATUM etiketi "VOCATIONAL" ya da "TECHNICAL" içeriyor) / diğer (ortaokul ve çok programlı
    dahil). Sağlamlık: üç kategori (ortaokul ayrı: "BASIC EDUCATION", "LOWER-SECONDARY", "LOWER SECONDARY", "PRIMARY").
    Etiketi olmayan ya da "UNDISCLOSED" tabaka çıkarsa DUR ve listele.
  * DiNardo–Fortin–Lemieux: t döngüsü 2012 paylarına çekilir; yeniden ağırlıklı ortalama μ_t^rw = Σ_g pay_2012(g) · μ_t(g)
    (ω_g = pay_2012/pay_t ile ağırlıklandırmanın özdeşi). Ayrıştırma: toplam = μ_b − μ_a; tür içi = μ_b^rw − μ_a^rw
    (μ_2012^rw ≡ μ_2012); bileşim = toplam − tür içi.
  * SE: her döngü bağımsız örneklem; bir büyüklüğün varyansı = Σ_döngü [BRR (Fay 0,5; 80; o döngünün replikasyonu, diğerleri tam
    ağırlıkta; paylar replikasyonda yeniden) + Rubin atama varyansı (o döngünün PV'leri, diğerleri PV ortalamasında)].
    2012 M = 5, sonrası M = 10.
  * Ulusal idari okul türü payları: dış veri gerekli; yapılmaz.
SONRADAN (§0 commit'inden sonra, koşudan ÖNCE, sonuç görülmeden eklendi): doğrulama kapısı — her döngü × alan için Türkiye'nin
  PV ortalaması panelle (analysis_panel.csv) mutlak fark ≤ 0,01; geçmezse DUR. Bağlantı (link) hatası ayrıştırmaya girmez
  (sınırlılık).
SONRADAN (2026-09-26, yerel koşu 1'den sonra): 2012 etiketleri boş geldi; neden betik 49'un `parse_value_labels` hatası (DATA LIST
  satırına takılıyordu; betik 49'da düzeltildi). Boş etiket önbelleğine artık güvenilmez: 2012'de etiketler sözdiziminden yeniden
  okunur, diğer döngülerde veri yeniden okunur. Sınıflama tanımı değişmedi.
Girdi: 2012 PUF (`_pisa_puf.read_columns` + sözdizimi VALUE LABELS); 2015/2018/2022 öğrenci QQQ ve 2025 öğrenci PUF (.sav, betik
       08'deki yollar); data/derived/analysis_panel.csv.
Çıktı: data/derived/empirical_fixes/e6_trough_decomposition.csv, e6_summary.json, e6_strata_map.csv
       (+ önbellek data/derived/cache/e6_tur_<yıl>.parquet).
Kullanım (Windows; pyreadstat + pyarrow): python analysis/48_e6_trough_composition.py
Yazan: Claude Code (bulut oturumu), 2026-09-26. Bu oturumda mikroveri yoktu: betik yalnız sentetik veriyle duman testinden geçti.
"""
from __future__ import annotations

import importlib
import json
import os
import re
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
D = ROOT / "data" / "derived"
OUT = D / "empirical_fixes"
CACHE = D / "cache"
CYCLES = [2012, 2015, 2018, 2022, 2025]
DOMS = {"math": "MATH", "reading": "READ", "science": "SCIE"}
FAY_MULT = 1.0 / (80 * (1 - 0.5) ** 2)
SAV = {  # betik 08'deki öğrenci dosyaları
    2015: ("data/pisa_microdata/2015/PUF_SPSS_COMBINED_CMB_STU_QQQ.zip", "_STU_QQQ.sav"),
    2018: ("data/pisa_microdata/2018/SPSS_STU_QQQ.zip", "_STU_QQQ.sav"),
    2022: ("data/pisa_microdata/2022/STU_QQQ_SPSS.zip", "_STU_QQQ.sav"),
    2025: ("data/pisa/2025/database/CY09_MS_STU_PUF.zip", "_STU_PUF.sav"),
}
PAIRS = [(2012, 2015), (2015, 2025), (2012, 2018), (2012, 2022), (2012, 2025), (2015, 2018)]


def M_of(cyc: int) -> int:
    return 5 if cyc == 2012 else 10


def repw_of(cyc: int) -> list[str]:
    return [f"W_FSTR{i}" for i in range(1, 81)] if cyc == 2012 else [f"W_FSTURWT{i}" for i in range(1, 81)]


def classify(label: str) -> tuple[str | None, str | None]:
    L = (label or "").upper()
    if not L or "UNDISCLOSED" in L or L == "(ETIKET YOK)":
        return None, None
    two = "mesleki" if ("VOCATIONAL" in L or "TECHNICAL" in L) else "diger"
    if two == "diger" and re.search(r"BASIC EDUCATION|LOWER[- ]SECONDARY|PRIMARY", L):
        return two, "ortaokul"
    return two, two


# ----------------------------------------------------------------------------- veri
def _read_sav(zp: Path, suffix: str, cols: list[str], td: str) -> tuple[pd.DataFrame, dict]:
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
    labels = meta.variable_value_labels.get(have["STRATUM"], {})
    df.columns = [c.upper() for c in df.columns]
    os.remove(sav)
    return df, labels


def load(cyc: int) -> tuple[pd.DataFrame, dict]:
    m49 = importlib.import_module("49_e8_frame_bounds")
    cols = ["CNT", "STRATUM", "W_FSTUWT"] + repw_of(cyc) + [f"PV{i}{r}" for i in range(1, M_of(cyc) + 1) for r in DOMS.values()]
    cache = CACHE / f"e6_tur_{cyc}.parquet"
    lab_cache = CACHE / f"e6_tur_{cyc}_labels.json"
    if cache.exists() and lab_cache.exists():
        labels = json.loads(lab_cache.read_text(encoding="utf-8"))
        if labels:
            return pd.read_parquet(cache), labels
        if cyc == 2012:  # SONRADAN: boş etiket önbelleğine güvenilmez; 2012 etiketi yalnız sözdiziminden yeniden okunur
            import _pisa_puf as P
            labels = {m49._norm_code(k): str(v) for k, v in m49.parse_value_labels(ROOT / P.REGISTRY[2012]["syn"], "STRATUM").items()}
            lab_cache.write_text(json.dumps(labels, ensure_ascii=False), encoding="utf-8")
            return pd.read_parquet(cache), labels
    if cyc == 2012:
        import _pisa_puf as P
        df = P.read_columns(2012, cols)
        labels = m49.parse_value_labels(ROOT / P.REGISTRY[2012]["syn"], "STRATUM")
    else:
        zp, suf = SAV[cyc]
        with tempfile.TemporaryDirectory(prefix=f"e6_{cyc}_", dir=os.environ.get("PISA_TMP")) as td:
            df, labels = _read_sav(ROOT / zp, suf, cols, td)
    df["CNT"] = df["CNT"].astype(str).str.strip()
    df = df[df.CNT == "TUR"].reset_index(drop=True)
    labels = {m49._norm_code(k): str(v) for k, v in labels.items()}
    CACHE.mkdir(parents=True, exist_ok=True)
    df.to_parquet(cache, index=False)
    lab_cache.write_text(json.dumps(labels, ensure_ascii=False), encoding="utf-8")
    return df, labels


# ----------------------------------------------------------------------------- hesap
class Cycle:
    """Tek döngü: ağırlık sütunu j (0 = tam, 1..80 replikasyon) × PV p için kategori ortalamaları ve paylar."""

    def __init__(self, cyc: int, df: pd.DataFrame, cat: np.ndarray, dom: str):
        self.cyc, self.M = cyc, M_of(cyc)
        W = np.column_stack([df.W_FSTUWT.to_numpy(float)] + [df[c].to_numpy(float) for c in repw_of(cyc)])
        Y = np.column_stack([pd.to_numeric(df[f"PV{i}{DOMS[dom]}"], errors="coerce").to_numpy(float) for i in range(1, self.M + 1)])
        self.cats = sorted(set(cat))
        G = W.shape[1]
        self.mu = np.empty((G, self.M))
        self.cm = {g: np.empty((G, self.M)) for g in self.cats}
        self.sh = {g: np.empty(G) for g in self.cats}
        for j in range(G):
            w = W[:, j]
            for p in range(self.M):
                ok = np.isfinite(Y[:, p])
                self.mu[j, p] = np.sum(w[ok] * Y[ok, p]) / np.sum(w[ok])
                for g in self.cats:
                    s = ok & (cat == g)
                    self.cm[g][j, p] = np.sum(w[s] * Y[s, p]) / np.sum(w[s])
            for g in self.cats:
                self.sh[g][j] = np.sum(w[cat == g]) / np.sum(w)

    def get(self, arr: np.ndarray, st: tuple) -> float:
        j, p = st
        return float(arr[j].mean()) if p is None else float(arr[j, p])


def evaluate(q, cycles: dict[int, Cycle]) -> tuple[float, float]:
    """q(state) → büyüklük; state = {döngü: (j, p)}. Varyans = Σ_döngü [BRR + Rubin] (bağımsız örneklemler)."""
    base = {c: (0, None) for c in cycles}
    est = q(base)
    v = 0.0
    for c, cy in cycles.items():
        reps = np.array([q({**base, c: (j, None)}) for j in range(1, 81)])
        pvs = np.array([q({**base, c: (0, p)}) for p in range(cy.M)])
        v += FAY_MULT * float(((reps - est) ** 2).sum()) + (1 + 1 / cy.M) * float(pvs.var(ddof=1))
    return est, float(np.sqrt(v))


def quantities(cycles: dict[int, Cycle]) -> list[dict]:
    base = cycles[2012]

    def T(c):
        return lambda st: cycles[c].get(cycles[c].mu, st[c])

    def RW(c):
        def f(st):
            tot = 0.0
            for g in base.cats:
                if g not in cycles[c].cm:
                    return np.nan
                tot += base.sh[g][st[2012][0]] * cycles[c].get(cycles[c].cm[g], st[c])
            return tot
        return f

    rows = []
    for c in CYCLES:
        for kind, fn in (("level", T(c)), ("level_rw2012", RW(c))):
            est, se = evaluate(lambda st, fn=fn: fn(st), {k: cycles[k] for k in {2012, c}})
            rows.append({"quantity": kind, "cycle": str(c), "estimate": est, "se": se})
        for g in cycles[c].cats:
            est, se = evaluate(lambda st, c=c, g=g: float(cycles[c].sh[g][st[c][0]]), {c: cycles[c]})
            rows.append({"quantity": f"share_{g}", "cycle": str(c), "estimate": est, "se": se})
    for a, b in PAIRS:
        used = {k: cycles[k] for k in {2012, a, b}}
        tot = lambda st, a=a, b=b: T(b)(st) - T(a)(st)
        wit = lambda st, a=a, b=b: RW(b)(st) - RW(a)(st)
        cmp_ = lambda st, a=a, b=b: (T(b)(st) - T(a)(st)) - (RW(b)(st) - RW(a)(st))
        for kind, fn in (("total", tot), ("within_type", wit), ("composition", cmp_)):
            est, se = evaluate(fn, used)
            rows.append({"quantity": kind, "cycle": f"{a}->{b}", "estimate": est, "se": se})
    return rows


def panel_gate(data: dict) -> dict:
    panel = pd.read_csv(D / "analysis_panel.csv")
    p = panel[panel.iso3 == "TUR"].set_index("cycle")
    out, fails = {}, []
    for cyc, (df, _) in data.items():
        w = df.W_FSTUWT.to_numpy(float)
        for dom, root in DOMS.items():
            vals = []
            for i in range(1, M_of(cyc) + 1):
                y = pd.to_numeric(df[f"PV{i}{root}"], errors="coerce").to_numpy(float)
                ok = np.isfinite(y)
                vals.append(np.sum(w[ok] * y[ok]) / np.sum(w[ok]))
            diff = abs(float(np.mean(vals)) - float(p.loc[cyc, f"{dom}_mean"]))
            out[f"{cyc}_{dom}"] = round(diff, 5)
            if diff > 0.01:
                fails.append(f"{cyc} {dom}")
    out["failed"] = fails
    return out


def main() -> int:
    m49 = importlib.import_module("49_e8_frame_bounds")
    data = {c: load(c) for c in CYCLES}
    gate = panel_gate(data)
    print("panel kapısı:", gate)
    if gate["failed"]:
        raise SystemExit(f"DUR: panel kapısı geçmedi: {gate['failed']}")
    smap, bad = [], []
    cats = {}
    for c, (df, labels) in data.items():
        codes = df.STRATUM.map(m49._norm_code)
        two, three = [], []
        for code in codes:
            lab = labels.get(code, "(etiket yok)")
            a, b = classify(lab)
            two.append(a)
            three.append(b)
        cats[c] = (np.array(two, dtype=object), np.array(three, dtype=object))
        g = pd.DataFrame({"code": codes, "label": [labels.get(x, "(etiket yok)") for x in codes], "two": two, "three": three,
                          "w": df.W_FSTUWT}).groupby(["code", "label", "two", "three"], dropna=False).agg(n=("w", "size"), w=("w", "sum"))
        for (code, lab, a, b), r in g.iterrows():
            smap.append({"cycle": c, "stratum": code, "label": lab, "cat2": a, "cat3": b, "n_students": int(r.n), "weighted": float(r.w)})
            if a is None or (isinstance(a, float) and np.isnan(a)):
                bad.append(f"{c}: {code} = {lab}")
    OUT.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(smap).to_csv(OUT / "e6_strata_map.csv", index=False, encoding="utf-8")
    if bad:
        raise SystemExit(f"DUR: sınıflanamayan tabaka (e6_strata_map.csv yazıldı): {bad}")
    rows = []
    for scheme, k in (("iki_kategori", 0), ("uc_kategori", 1)):
        for dom in DOMS:
            cyc_objs = {c: Cycle(c, data[c][0], cats[c][k], dom) for c in CYCLES}
            for r in quantities(cyc_objs):
                rows.append({"scheme": scheme, "domain": dom, **r, "estimate": round(r["estimate"], 4), "se": round(r["se"], 4)})
    t = pd.DataFrame(rows)
    tmp = OUT / "e6_trough_decomposition.csv.tmp"
    t.to_csv(tmp, index=False, encoding="utf-8")
    os.replace(tmp, OUT / "e6_trough_decomposition.csv")
    summ = {"note": "E6 — DFL bileşim ayrıştırması (2012 paylarına); ön-belirleme §0.7 (commit 476fe4e). Ulusal idari paylarla "
                    "karşılaştırma: dış veri gerekli.", "panel_gate": gate,
            "primary": t[(t.scheme == "iki_kategori") & t.cycle.isin(["2012->2015", "2015->2025"])].to_dict("records")}
    tmp = OUT / "e6_summary.json.tmp"
    tmp.write_text(json.dumps(summ, ensure_ascii=False, indent=1, default=float), encoding="utf-8")
    os.replace(tmp, OUT / "e6_summary.json")
    print(t[t.scheme == "iki_kategori"].to_string(index=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
