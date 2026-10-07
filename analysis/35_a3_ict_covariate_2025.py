# -*- coding: utf-8 -*-
"""
35_a3_ict_covariate_2025.py — ek analiz isteği A3: "müfredat özgüllüğü" alternatifi.

Soru (A3): 2025 hesaplamalı problem çözme (LDW Computational Problem Solving) artığı, bilişim/programlama
maruziyeti düşük bir ülkede şişme olmadan da düşük çıkar mı? 2025 ülke artıklarını bir maruziyet eş değişkeniyle birlikte
uydur; Türkiye'nin −32 puanlık artığının ne kadarı kalıyor?

ÖNCEDEN BELİRLENEN SEÇİMLER (sonuç görülmeden yazıldı, 25 Eyl 2026):
  * BİRİNCİL eş değişken PROG: okul derslerinde bu öğretim yılı "bilgisayar programı, makro ya da uygulama oluşturma"
    (ST436Q07DA; <Scratch>, <Logo>, <VBA>, <Java>) en az "Sometimes" diyen öğrencilerin ağırlıklı payı (geçerli yanıt 1–4).
    Gerekçe: alternatifin mekanizması okulda programlama maruziyetidir; madde ana öğrenci anketinde (opsiyonel değil).
  * İKİNCİL (hepsi raporlanır): ROBOT = ST436Q13DA "program robots" ≥ Sometimes payı; ICTSCH = okulda BİT erişimi (WLE,
    opsiyonel BİT anketi); ICTRES = BİT kaynakları (WLE; PUF'ta 90 sistemin 57'sinde dolu, opsiyon bayraklarıyla örtüşmüyor — koşudan sonra görüldü); CPPK = "Computational Practices Prior Knowledge" PV
    ortalaması (bir BİLGİ ölçüsüdür, maruziyet değil; kendisi de sonuç olabileceği için yalnız duyarlılık); BİRLEŞİK = PROG + ICTRES.
  * Model (ülke düzeyi OLS): CPS = a + b·çekirdek [+ c·çekirdek²] + d·X + e; çekirdek = mat/oku/fen ortalaması (makaledeki
    tanım). Türkiye'nin artığı X'li ve X'siz modelde AYNI örneklemde karşılaştırılır; dört spesifikasyon (tüm/OECD × doğrusal/
    karesel). "Kalan pay" = artık(X'li) / artık(X'siz).
  * Ağırlık W_FSTUWT; eş değişkenler için belirsizlik taşınmaz (regresör); d için klasik OLS standart hatası raporlanır.
Doğrulama: öğrenci dosyasındaki PV1–10CMPS'den ağırlıklı ülke ortalaması, panelin `cps2025_mean` (Tablo I.B1.2a.4) değeriyle
karşılaştırılır; uyuşmazlık > 1 puan olan ülke raporlanır.
SONRADAN DÜZELTME (25 Eyl, ilk koşudan sonra; tanım değişmedi): PUF kodları TAP→TWN, KSV→XKX eşlendi (ilk koşuda 84 sistemin 81'i
eşleşmişti; Kıbrıs 2025 PUF'ta yok → 83). Okuma tek geçişe çevrildi; sandbox'ta PISA_SAV ile önceden açılmış .sav verilebilir.
Not: ICTSCH yalnız opsiyonel BİT anketini uygulayan sistemlerde (44; 24 OECD), ICTRES de beklenenden dar bir kümede (kod
eşlemesinden sonra 51 sistem, 13 OECD) dolu çıktı; ikisi de ikincil olduğundan sonuçları örneklem büyüklüğüyle birlikte raporlanır.
T1 (25 Eyl) notu: OECD alt kümesinde Türkiye ICTSCH'de en altta ve kaldıracı 0,40; Türkiye dışarıda tahmin edilince ICTSCH artığın
%75–77'sini bırakıyor (makale §5.2; RESULTS_PHASE6 §2 eki). Hesap betiğe `loo_turkiye_posthoc` bloğu olarak eklendi (özet JSON'da);
makalede sonradan yapılmış diye geçiyor.
Girdi: data/pisa/2025/database/CY09_MS_STU_PUF.zip (2,17 GB .sav; geçici klasöre açılır, iş bitince geçici klasör kalkar);
       data/derived/analysis_panel.csv (2025 çekirdek ve CPS ortalamaları, OECD üyeliği).
Çıktı: data/derived/cache/ict2025_country.csv (ülke düzeyi eş değişkenler, parmak izli önbellek);
       data/derived/mechanisms/ict_covariate_2025.csv, ict_covariate_2025_summary.json.
Kullanım (Windows, pyreadstat gerekir): python analysis/35_a3_ict_covariate_2025.py      Yazan: Claude Opus 5.5 (Cowork), 2026-09-25.
"""
from __future__ import annotations

import hashlib
import json
import os
import sys
import tempfile
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
ZIP = ROOT / "data" / "pisa" / "2025" / "database" / "CY09_MS_STU_PUF.zip"
PANEL = ROOT / "data" / "derived" / "analysis_panel.csv"
CACHE = ROOT / "data" / "derived" / "cache" / "ict2025_country.csv"
OUT = ROOT / "data" / "derived" / "mechanisms"
PV_CMPS = [f"PV{i}CMPS" for i in range(1, 11)]
PV_CPPK = [f"PV{i}CPPK" for i in range(1, 11)]
VARS = ["CNT", "W_FSTUWT", "Option_ICTQ", "Option_LDW", "ST436Q07DA", "ST436Q13DA", "ICTSCH", "ICTRES"] + PV_CMPS + PV_CPPK
COVS = ["PROG", "ROBOT", "ICTSCH", "ICTRES", "CPPK"]


def fingerprint() -> str:
    st = ZIP.stat()
    return hashlib.sha256(f"{ZIP.name}|{st.st_size}|{int(st.st_mtime)}|{','.join(VARS)}|v1".encode()).hexdigest()[:16]


def extract() -> pd.DataFrame:
    import pyreadstat
    fp = fingerprint()
    if CACHE.exists():
        c = pd.read_csv(CACHE)
        if "fingerprint" in c.columns and (c["fingerprint"] == fp).all():
            print(f"önbellek kullanıldı: {CACHE.relative_to(ROOT)} ({len(c)} ülke)")
            return c
    acc: dict[str, dict[str, float]] = {}
    pre = os.environ.get("PISA_SAV")  # önceden açılmış .sav (sandbox: arka plan süreci çağrı sonunda ölüyor → açma ve okuma ayrı adım)
    with tempfile.TemporaryDirectory(prefix="pisa25stu_", dir=os.environ.get("PISA_TMP")) as td:
        if pre and Path(pre).exists():
            sav = pre
        else:
            with zipfile.ZipFile(ZIP) as z:
                name = [n for n in z.namelist() if n.lower().endswith(".sav")][0]
                try:
                    z.extract(name, td)
                except NotImplementedError:
                    # zip Deflate64 ile sıkıştırılmış (12b ile aynı durum) → Info-ZIP unzip CLI
                    import subprocess
                    r = subprocess.run(["unzip", "-o", "-q", str(ZIP), name, "-d", td], capture_output=True, text=True)
                    if r.returncode != 0:
                        raise SystemExit(f"unzip başarısız: {r.stderr[:300]}")
            sav = str(Path(td) / name)
        print(f"okunacak: {Path(sav).name} ({Path(sav).stat().st_size / 1e9:.2f} GB)", flush=True)
        n_rows = 0
        # tek geçiş (usecols): sıkıştırılmış .sav'da parça okuma her parçada dosyayı baştan çözüyor; bellek ~0,2 GB
        frames = [pyreadstat.read_sav(sav, usecols=VARS)]
        for ch, _ in frames:
            n_rows += len(ch)
            w = pd.to_numeric(ch["W_FSTUWT"], errors="coerce").fillna(0.0).to_numpy()
            cnt = ch["CNT"].astype(str).to_numpy()
            cols: dict[str, tuple[np.ndarray, np.ndarray]] = {}
            for item, key in [("ST436Q07DA", "PROG"), ("ST436Q13DA", "ROBOT")]:
                x = pd.to_numeric(ch[item], errors="coerce").to_numpy()
                valid = np.isin(x, [1, 2, 3, 4])
                cols[key] = (valid, np.where(valid & (x >= 2), 1.0, 0.0))
            for v in ["ICTSCH", "ICTRES"]:
                x = pd.to_numeric(ch[v], errors="coerce").to_numpy()
                valid = np.isfinite(x) & (x < 95)
                cols[v] = (valid, np.where(valid, x, 0.0))
            for v in ["Option_ICTQ", "Option_LDW"]:
                x = pd.to_numeric(ch[v], errors="coerce").to_numpy()
                valid = np.isin(x, [0, 1])
                cols[v] = (valid, np.where(valid, x, 0.0))
            for grp, pvs in [("CMPS", PV_CMPS), ("CPPK", PV_CPPK)]:
                for i, pv in enumerate(pvs, start=1):
                    x = pd.to_numeric(ch[pv], errors="coerce").to_numpy()
                    valid = np.isfinite(x) & (x < 9990)
                    cols[f"{grp}_{i}"] = (valid, np.where(valid, x, 0.0))
            df = pd.DataFrame({"CNT": cnt})
            for k, (valid, val) in cols.items():
                df[f"w_{k}"] = w * valid
                df[f"wx_{k}"] = w * val * valid
            g = df.groupby("CNT").sum()
            for cn, row in g.iterrows():
                a = acc.setdefault(cn, {})
                for col, val in row.items():
                    a[col] = a.get(col, 0.0) + float(val)
        print(f"okunan satır: {n_rows:,}")
    recs = []
    for cn, a in acc.items():
        r = {"iso3": cn}
        for k in ["PROG", "ROBOT", "ICTSCH", "ICTRES", "Option_ICTQ", "Option_LDW"]:
            r[k] = a[f"wx_{k}"] / a[f"w_{k}"] if a.get(f"w_{k}", 0) > 0 else np.nan
            r[f"{k}_wshare"] = a.get(f"w_{k}", 0.0)
        for grp in ["CMPS", "CPPK"]:
            means = [a[f"wx_{grp}_{i}"] / a[f"w_{grp}_{i}"] for i in range(1, 11) if a.get(f"w_{grp}_{i}", 0) > 0]
            r[grp] = float(np.mean(means)) if len(means) == 10 else np.nan
        recs.append(r)
    c = pd.DataFrame(recs).sort_values("iso3")
    c["fingerprint"] = fp
    CACHE.parent.mkdir(parents=True, exist_ok=True)
    tmp = CACHE.with_suffix(".csv.tmp")
    c.to_csv(tmp, index=False, encoding="utf-8")
    os.replace(tmp, CACHE)
    print(f"önbellek yazıldı: {CACHE.relative_to(ROOT)} ({len(c)} ülke)")
    return c


def ols(y: np.ndarray, X: np.ndarray):
    beta, *_ = np.linalg.lstsq(X, y, rcond=None)
    res = y - X @ beta
    n, k = X.shape
    s2 = float(res @ res) / (n - k)
    se = np.sqrt(np.diag(np.linalg.pinv(X.T @ X)) * s2)
    return beta, se, res, float(np.sqrt(s2))


def main() -> int:
    c = extract()
    # PUF ülke kodları panelle birebir değil (ilk koşuda yakalandı, 25 Eyl): TAP = Çin Taipei, KSV = Kosova.
    # Kıbrıs (CYP) 2025 PUF'ta yok; QTJ'nin CMPS verisi yok (panelde de yok).
    c["iso3"] = c["iso3"].replace({"TAP": "TWN", "KSV": "XKX"})
    p = pd.read_csv(PANEL)
    p = p[(p.cycle == 2025)].dropna(subset=["math_mean", "reading_mean", "science_mean", "cps2025_mean"]).copy()
    p = p[p["iso3"].astype(str).str.len() == 3]
    p["core"] = p[["math_mean", "reading_mean", "science_mean"]].mean(axis=1)
    om = p["oecd_member"]
    p["oecd"] = (om.astype(str).str.strip().str.lower().isin(["1", "1.0", "true", "yes", "evet"])) if om.dtype == object else (pd.to_numeric(om, errors="coerce").fillna(0) > 0)
    d = p[["iso3", "core", "cps2025_mean", "oecd"]].merge(c, on="iso3", how="left")
    # doğrulama: mikroveri CMPS ortalaması vs panel
    chk = d.dropna(subset=["CMPS"])
    diff = (chk["CMPS"] - chk["cps2025_mean"]).abs()
    validation = {"n_matched": int(len(chk)), "max_abs_diff": round(float(diff.max()), 3), "n_over_1pt": int((diff > 1).sum()),
                  "over_1pt": chk.loc[diff > 1, ["iso3", "CMPS", "cps2025_mean"]].round(2).to_dict("records")}
    print("CMPS doğrulama:", validation)
    rows, summ = [], {"validation_cmps_vs_panel": validation, "models": {}}
    tur_cov = {k: (round(float(d.loc[d.iso3 == "TUR", k].iloc[0]), 4) if k in d and d.loc[d.iso3 == "TUR", k].notna().any() else None) for k in COVS}
    summ["turkiye_covariates"] = tur_cov
    for scope in ["all", "oecd"]:
        base = d if scope == "all" else d[d.oecd]
        for spec in ["linear", "quadratic"]:
            for label, xs in [(k, [k]) for k in COVS] + [("PROG+ICTRES", ["PROG", "ICTRES"])]:
                s = base.dropna(subset=["core", "cps2025_mean"] + xs)
                if "TUR" not in set(s.iso3) or len(s) < 10:
                    summ["models"][f"{scope}/{spec}/{label}"] = {"n": int(len(s)), "note": "TUR yok ya da örneklem küçük"}
                    continue
                y = s["cps2025_mean"].to_numpy(float)
                x = s["core"].to_numpy(float)
                X0 = np.column_stack([np.ones_like(x), x] + ([x ** 2] if spec == "quadratic" else []))
                X1 = np.column_stack([X0] + [s[v].to_numpy(float) for v in xs])
                b0, _, r0, rm0 = ols(y, X0)
                b1, se1, r1, rm1 = ols(y, X1)
                it = list(s.iso3).index("TUR")
                ranks1 = pd.Series(r1).rank(method="min")
                rec = {"scope": scope, "spec": spec, "covariate": label, "n": int(len(s)),
                       "coef": [round(float(b1[X0.shape[1] + j]), 3) for j in range(len(xs))],
                       "coef_se": [round(float(se1[X0.shape[1] + j]), 3) for j in range(len(xs))],
                       "rmse_without": round(rm0, 2), "rmse_with": round(rm1, 2),
                       "tur_resid_without": round(float(r0[it]), 2), "tur_resid_with": round(float(r1[it]), 2),
                       "tur_share_remaining": round(float(r1[it] / r0[it]), 3) if r0[it] != 0 else None,
                       "tur_rank_without": int(pd.Series(r0).rank(method="min").iloc[it]), "tur_rank_with": int(ranks1.iloc[it])}
                rows.append(rec)
                summ["models"][f"{scope}/{spec}/{label}"] = rec
    OUT.mkdir(parents=True, exist_ok=True)
    tmp = OUT / "ict_covariate_2025.csv.tmp"
    pd.DataFrame(rows).to_csv(tmp, index=False, encoding="utf-8")
    os.replace(tmp, OUT / "ict_covariate_2025.csv")
    # Türkiye'nin eş değişken sırası (tüm örneklem, alttan)
    ranks = {}
    for k in COVS:
        s = d.dropna(subset=[k])
        if "TUR" in set(s.iso3):
            ranks[k] = f"{int(s[k].rank(method='min')[s.iso3 == 'TUR'].iloc[0])}/{len(s)}"
    summ["turkiye_covariate_rank_from_bottom"] = ranks
    # SONRADAN (T1, 25 Eyl): Türkiye'nin kaldıracı ve Türkiye dışarıda tahmin edildiğinde (örneklem dışı) kalan pay
    loo = {}
    for scope in ["all", "oecd"]:
        base = d if scope == "all" else d[d.oecd]
        for spec in ["linear", "quadratic"]:
            for cov in COVS:
                s = base.dropna(subset=["core", "cps2025_mean", cov])
                if "TUR" not in set(s.iso3) or len(s) < 10:
                    continue
                def design(f, with_cov):
                    x = f["core"].to_numpy(float)
                    cols = [np.ones_like(x), x] + ([x ** 2] if spec == "quadratic" else []) + ([f[cov].to_numpy(float)] if with_cov else [])
                    return np.column_stack(cols)
                t, o = s[s.iso3 == "TUR"], s[s.iso3 != "TUR"]
                out = {}
                for wc in (False, True):
                    b, *_ = np.linalg.lstsq(design(o, wc), o["cps2025_mean"].to_numpy(float), rcond=None)
                    out[wc] = float(t["cps2025_mean"].iloc[0] - (design(t, wc) @ b)[0])
                Xa = design(s, True)
                i = list(s.iso3).index("TUR")
                lev = float((Xa @ np.linalg.pinv(Xa.T @ Xa) @ Xa.T)[i, i])
                loo[f"{scope}/{spec}/{cov}"] = {"n": int(len(s)), "tur_loo_resid_without": round(out[False], 2),
                                                "tur_loo_resid_with": round(out[True], 2),
                                                "tur_loo_share_remaining": round(out[True] / out[False], 3),
                                                "tur_leverage": round(lev, 3), "mean_leverage": round(Xa.shape[1] / len(s), 3)}
    summ["loo_turkiye_posthoc"] = loo
    tmp = OUT / "ict_covariate_2025_summary.json.tmp"
    tmp.write_text(json.dumps(summ, ensure_ascii=False, indent=1), encoding="utf-8")
    os.replace(tmp, OUT / "ict_covariate_2025_summary.json")
    print("TUR eş değişkenleri:", tur_cov, "sıra:", ranks)
    print(f"{'kapsam/spec/X':<28}{'n':>4} {'katsayı':>14} {'TUR artık X-siz':>16} {'X-li':>7} {'kalan':>6} {'sıra':>9}")
    for r in rows:
        print(f"{r['scope']+'/'+r['spec']+'/'+r['covariate']:<28}{r['n']:>4} {str(r['coef']):>14} {r['tur_resid_without']:>16} "
              f"{r['tur_resid_with']:>7} {r['tur_share_remaining']:>6} {str(r['tur_rank_without'])+'→'+str(r['tur_rank_with']):>9}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
