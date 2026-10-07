#!/usr/bin/env python3
"""PISA 2025 madde-süresi çaba göstergeleri — COG_PROCESS süreç dosyasından.

07_microdata_effort.py 2025 için süre üretemedi (COG PUF'ta süre yok). Süreler
CY09_MS_COG_PROCESS_*.sav içinde: her madde için `<item>TT` (Total Timing, ms),
`<item>A` (Number of Actions), `<item>F` (Time to First Action). Bu betik 07 ile aynı
tanımları kullanır (süre >= 99.999.990 ms geçersiz — PISA sentinel kodları 9999999x bu eşiğin
üstünde; NT15 = madde medyanının %15'i,
medyanlar yüklenen hedef havuz üzerinden; sabit 5 sn kuralı) ve ek olarak
sıfır-eylem payını (öğrencinin hiç etkileşmediği madde payı) hesaplar.

Girdi:  %TEMP%/pisa_microdata_work/2025_proc/*.sav (önceden açılmış, 12,3 GB)
        data/pisa/2025/database/CY09_MS_STU_PUF.zip (W_FSTUWT için; unzip CLI ile açılır)
        data/derived/cache/effort_students_2025.parquet (07'nin puan tabanlı göstergeleri; varsa birleştirilir)
Çıktı: data/derived/effort_2025_process.csv (ülke × ağırlıklı/ağırlıksız)
        data/derived/cache/effort2025_students.parquet, effort2025_itemmedian.csv, effort2025_vars.txt
Yazan: Claude Fable 5.1, 2026-09-15.
"""
from __future__ import annotations

import gc
import glob
import os
import subprocess
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
import pyreadstat

ROOT = Path(__file__).resolve().parent.parent
WORK = Path(os.environ.get("PISA_WORK", os.path.join(__import__("tempfile").gettempdir(), "pisa_microdata_work")))
CACHE = ROOT / "data" / "derived" / "cache"
CACHE.mkdir(parents=True, exist_ok=True)
OUT = ROOT / "data" / "derived" / "effort_2025_process.csv"

TARGETS = ["TUR", "GEO", "HUN", "BEL", "CHE", "FRA", "ISL", "JPN", "EST", "LVA", "LTU", "POL",
           "SRB", "MEX", "BRA", "KAZ", "COL", "DEU", "PRT", "AUT", "FIN", "SWE", "NLD", "ESP", "ITA", "GRC"]
CHUNK = 15000
TIME_SENTINEL = 99_999_990
FIXED_MS = 5_000
NT_FRAC = 0.15
T0 = time.time()


def log(*a):
    print(f"[{time.time()-T0:7.0f}s]", *a, flush=True)


def largest(pattern: str) -> Path | None:
    c = glob.glob(pattern)
    return Path(max(c, key=os.path.getsize)) if c else None


def wmedian(v, w):
    v = np.asarray(v, float); w = np.asarray(w, float)
    m = np.isfinite(v) & np.isfinite(w) & (w > 0)
    v, w = v[m], w[m]
    if v.size == 0:
        return np.nan
    o = np.argsort(v); v, w = v[o], w[o]
    cw = np.cumsum(w)
    return float(v[np.searchsorted(cw, 0.5 * cw[-1])])


def ensure_weights() -> Path:
    """2025 öğrenci dosyasından W_FSTUWT; zip Deflate64 olabilir → unzip CLI."""
    d = WORK / "2025_wt"
    d.mkdir(parents=True, exist_ok=True)
    have = largest(str(d / "*.sav")) or largest(str(d / "*.SAV"))
    if have:
        return have
    z = ROOT / "data/pisa/2025/database/CY09_MS_STU_PUF.zip"
    log("2025 STU PUF açılıyor (unzip)…")
    r = subprocess.run(["unzip", "-o", "-q", str(z), "-d", str(d)], capture_output=True, text=True)
    if r.returncode != 0:
        raise SystemExit(f"unzip başarısız: {r.stderr[:300]}")
    have = largest(str(d / "*.sav")) or largest(str(d / "*.SAV"))
    if not have:
        raise SystemExit("2025 STU .sav bulunamadı")
    return have


def main() -> int:
    stu_cache = CACHE / "effort2025_students.parquet"
    if stu_cache.exists():
        log("önbellek var:", stu_cache)
        stud = pd.read_parquet(stu_cache)
    else:
        sav = largest(str(WORK / "2025_proc" / "*.sav")) or largest(str(WORK / "2025_proc" / "*.SAV"))
        if not sav:
            raise SystemExit("2025 process .sav yok")
        _, meta = pyreadstat.read_sav(str(sav), metadataonly=True)
        lab = meta.column_names_to_labels
        tt = [c for c in meta.column_names if "total timing" in (lab.get(c) or "").lower()]
        ac = [c for c in meta.column_names if "number of actions" in (lab.get(c) or "").lower()]
        ac_by_item = {c[:-1]: c for c in ac}                   # '<item>A' → '<item>'
        tt_items = [c[:-2] for c in tt]                        # '<item>TT' → '<item>'
        ac_aligned = [ac_by_item.get(i) for i in tt_items]     # TT ile aynı sırada A sütunu (yoksa None)
        log(f"dosya {sav.name}: rows={meta.number_rows} cols={len(meta.column_names)} TT={len(tt)} A={len(ac)} eşleşen A={sum(a is not None for a in ac_aligned)}")
        (CACHE / "effort2025_vars.txt").write_text(
            "PISA 2025 process-file effort variables\n" f"source: {sav.name}\nrows={meta.number_rows}\n\n"
            f"TT (Total Timing, ms) n={len(tt)}:\n{', '.join(tt)}\n\n"
            f"A (Number of Actions) n={len(ac)}:\n{', '.join(ac)}\n\n"
            f"example TT value labels: {meta.variable_value_labels.get(tt[0])}\n"
            f"example A value labels: {meta.variable_value_labels.get(ac[0]) if ac else None}\n", encoding="utf-8")
        use = ["CNT", "CNTSTUID"] + tt + [a for a in ac_aligned if a]
        frames = []
        nrows = 0
        for ch, _ in pyreadstat.read_file_in_chunks(pyreadstat.read_sav, str(sav), usecols=use, chunksize=CHUNK, user_missing=True):
            nrows += len(ch)
            ch = ch[ch["CNT"].isin(TARGETS)]
            if len(ch):
                T = ch[tt].apply(pd.to_numeric, errors="coerce").astype("float32")
                T = T.where((T > 0) & (T < TIME_SENTINEL))
                A = pd.DataFrame({i: (pd.to_numeric(ch[a], errors="coerce") if a else np.nan) for i, a in zip(tt_items, ac_aligned)}).astype("float32")
                A = A.where(A < TIME_SENTINEL)
                T.columns = tt_items; A.columns = [f"A::{i}" for i in tt_items]
                frames.append(pd.concat([ch[["CNT", "CNTSTUID"]].reset_index(drop=True), T.reset_index(drop=True), A.reset_index(drop=True)], axis=1))
            if nrows % (CHUNK * 10) == 0:
                log(f"  okunan satır {nrows} | tutulan {sum(len(f) for f in frames)}")
        all_ = pd.concat(frames, ignore_index=True); del frames; gc.collect()
        log(f"hedef ülkeler: {len(all_)} öğrenci")
        Tm = all_[tt_items].to_numpy(dtype="float32")
        Am = all_[[f"A::{i}" for i in tt_items]].to_numpy(dtype="float32")
        valid = ~np.isnan(Tm)
        item_med = np.nanmedian(np.where(valid, Tm, np.nan), axis=0)
        pd.Series(item_med, index=tt_items, name="item_median_ms").to_csv(CACHE / "effort2025_itemmedian.csv")
        thr = (NT_FRAC * item_med).astype("float32")
        rapid5 = valid & (Tm < FIXED_MS)
        rapidNT = valid & (Tm < thr[None, :])
        a_valid = ~np.isnan(Am) & valid
        zero_act = a_valid & (Am == 0)
        with np.errstate(all="ignore"):
            med_item = np.nanmedian(np.where(valid, Tm, np.nan), axis=1)
        stud = pd.DataFrame({
            "CNT": all_["CNT"].values, "CNTSTUID": all_["CNTSTUID"].values,
            "n_time_valid": valid.sum(1), "total_time_ms": np.nansum(np.where(valid, Tm, 0), axis=1),
            "n_rapid5": rapid5.sum(1), "n_rapidNT15": rapidNT.sum(1),
            "n_act_valid": a_valid.sum(1), "n_zero_actions": zero_act.sum(1),
            "median_item_time_ms": med_item,
        })
        del all_, Tm, Am, valid, rapid5, rapidNT, a_valid, zero_act; gc.collect()
        # ağırlıklar
        wsav = ensure_weights()
        _, wm = pyreadstat.read_sav(str(wsav), metadataonly=True)
        wvar = next((c for c in wm.column_names if c.upper() == "W_FSTUWT"), None)
        if not wvar:
            raise SystemExit("W_FSTUWT yok")
        wf = []
        for ch, _ in pyreadstat.read_file_in_chunks(pyreadstat.read_sav, str(wsav), usecols=["CNT", "CNTSTUID", wvar], chunksize=50000):
            ch = ch[ch["CNT"].isin(TARGETS)]
            if len(ch):
                wf.append(ch[["CNTSTUID", wvar]])
        W = pd.concat(wf, ignore_index=True).drop_duplicates("CNTSTUID").rename(columns={wvar: "W_FSTUWT"})
        stud = stud.merge(W, on="CNTSTUID", how="left")
        log(f"ağırlık eşleşen: {stud.W_FSTUWT.notna().sum()}/{len(stud)} (kaynak {wsav.name})")
        stud["source_file"] = sav.name
        stud.to_parquet(stu_cache, index=False)

    # 07'nin 2025 puan tabanlı göstergeleri (not-reached, doğru %) varsa ekle
    sc = CACHE / "effort_students_2025.parquet"
    if sc.exists():
        s = pd.read_parquet(sc)
        keep = [c for c in ["CNTSTUID", "n_credit", "n_correct", "n_notreached"] if c in s.columns]
        stud = stud.merge(s[keep].drop_duplicates("CNTSTUID"), on="CNTSTUID", how="left")
        log("07 puan göstergeleri birleştirildi")

    # ---- ülke düzeyi toplama ----
    rows = []
    for cnt, g in stud.groupby("CNT"):
        for weighted in (True, False):
            w = g["W_FSTUWT"].to_numpy(float) if weighted else np.ones(len(g))
            w = np.where(np.isfinite(w), w, 0.0)
            nv = g["n_time_valid"].to_numpy(float)
            def share(num):
                return float((w * num).sum() / (w * nv).sum()) if (w * nv).sum() > 0 else np.nan
            rec = dict(country=cnt, cycle=2025, weighted=weighted, n_students=int(len(g)),
                       n_item_responses=int(nv.sum()),
                       median_total_time_s=round(wmedian(g["total_time_ms"], w) / 1000, 1),
                       mean_total_time_s=round(float((w * g["total_time_ms"]).sum() / w.sum() / 1000), 1) if w.sum() else np.nan,
                       median_per_item_time_s=round(wmedian(g["median_item_time_ms"], w) / 1000, 2),
                       rapid5_share=round(share(g["n_rapid5"].to_numpy(float)), 4),
                       rapidNT15_share=round(share(g["n_rapidNT15"].to_numpy(float)), 4),
                       zero_action_share=round(float((w * g["n_zero_actions"]).sum() / (w * g["n_act_valid"]).sum()), 4) if (w * g["n_act_valid"]).sum() > 0 else np.nan)
            if "n_notreached" in g.columns:
                cred = g["n_credit"].to_numpy(float); nr = g["n_notreached"].to_numpy(float); cor = g["n_correct"].to_numpy(float)
                rec["notreached_rate"] = round(float((w * nr).sum() / (w * (cred + nr)).sum()), 4) if (w * (cred + nr)).sum() > 0 else np.nan
                rec["pct_correct"] = round(float((w * cor).sum() / (w * cred).sum()), 4) if (w * cred).sum() > 0 else np.nan
            rec["source_file"] = "CY09_MS_COG_PROCESS_20260806.sav (TT/A) + CY09_MS_STU_PUF (W_FSTUWT)"
            rec["variables"] = "TT=Total Timing(ms, sentinel>=99999990 invalid); A=Number of Actions; NT15=15% of pooled item median; fixed 5s"
            rows.append(rec)
    out = pd.DataFrame(rows).sort_values(["country", "weighted"], ascending=[True, False])
    out.to_csv(OUT, index=False, encoding="utf-8-sig")
    show = out[out.weighted][["country", "n_students", "median_per_item_time_s", "rapid5_share", "rapidNT15_share", "zero_action_share"] + [c for c in ["notreached_rate", "pct_correct"] if c in out.columns]]
    print(show.to_string(index=False))
    # sanity
    tur = out[(out.country == "TUR") & out.weighted]
    log("SANITY TUR n:", int(tur.n_students.iloc[0]) if len(tur) else None, "(beklenen ≈7702)")
    log("DONE 2025 process effort")
    return 0


if __name__ == "__main__":
    sys.exit(main())
