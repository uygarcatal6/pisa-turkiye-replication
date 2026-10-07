#!/usr/bin/env python3
"""PISA 2025 COG_PROCESS dosyasının yapısını keşfet (yalnızca metaveri + küçük örnek).
Amaç: 2025 madde yanıt sürelerinin hangi değişkenlerde olduğunu, geniş mi uzun format mı
olduğunu ve kod şemasını görmek; hesaplama betiği (12b) buna göre yazılacak.
Çıktı: data/derived/cache/process2025_structure.txt
Yazan: Claude Fable 5.1, 2026-09-15.
"""
from __future__ import annotations

import glob
import os
import re
from collections import Counter
from pathlib import Path

import pyreadstat

ROOT = Path(__file__).resolve().parent.parent
WORK = Path(os.environ.get("PISA_WORK", os.path.join(__import__("tempfile").gettempdir(), "pisa_microdata_work")))
OUTF = ROOT / "data" / "derived" / "cache" / "process2025_structure.txt"
OUTF.parent.mkdir(parents=True, exist_ok=True)

cands = glob.glob(str(WORK / "2025_proc" / "*.sav")) + glob.glob(str(WORK / "2025_proc" / "*.SAV"))
if not cands:
    raise SystemExit("2025 process .sav yok; extraction bitmedi mi?")
sav = Path(max(cands, key=os.path.getsize))
lines = [f"file: {sav} ({sav.stat().st_size/1e9:.2f} GB)"]
_, meta = pyreadstat.read_sav(str(sav), metadataonly=True)
cols = meta.column_names
lab = meta.column_names_to_labels
lines.append(f"rows: {meta.number_rows} | columns: {len(cols)}")

# sütun adı kalıpları
suffix = Counter()
for c in cols:
    m = re.search(r"([A-Za-z]+)$", c)
    suffix[m.group(1) if m else "?"] += 1
lines.append("suffix counts (top 25): " + ", ".join(f"{k}={v}" for k, v in suffix.most_common(25)))
prefix = Counter(c[:2] for c in cols)
lines.append("prefix2 counts (top 15): " + ", ".join(f"{k}={v}" for k, v in prefix.most_common(15)))

kw = Counter()
for c in cols:
    l = (lab.get(c) or "").lower()
    for k in ("timing", "time", "duration", "visit", "action", "response", "score", "click", "event", "position", "order", "sequence", "booklet", "form", "cluster", "number of"):
        if k in l:
            kw[k] += 1
lines.append("label keyword counts: " + ", ".join(f"{k}={v}" for k, v in kw.most_common()))

lines.append("\nfirst 40 columns:")
for c in cols[:40]:
    lines.append(f"  {c:28s} | {lab.get(c)}")
lines.append("\ncolumns whose label mentions timing/time/duration (first 40):")
n = 0
for c in cols:
    l = (lab.get(c) or "").lower()
    if any(k in l for k in ("timing", "time", "duration")):
        lines.append(f"  {c:28s} | {lab.get(c)}")
        n += 1
        if n >= 40:
            break
lines.append("\ncolumns whose label mentions position/order/sequence/cluster/booklet/form (first 30):")
n = 0
for c in cols:
    l = (lab.get(c) or "").lower()
    if any(k in l for k in ("position", "order", "sequence", "cluster", "booklet", "form")):
        lines.append(f"  {c:28s} | {lab.get(c)}")
        n += 1
        if n >= 30:
            break
lines.append("\nvalue labels for up to 8 columns that have them:")
n = 0
for c, vl in meta.variable_value_labels.items():
    lines.append(f"  {c}: {dict(list(vl.items())[:12])}")
    n += 1
    if n >= 8:
        break

# küçük örnek: ilk 3 satır, ilk 25 sütun
df, _ = pyreadstat.read_sav(str(sav), row_limit=3, usecols=cols[:25])
lines.append("\nsample rows (first 3, first 25 cols):")
lines.append(df.to_string())
OUTF.write_text("\n".join(lines), encoding="utf-8")
print("\n".join(lines[:12]))
print(f"... full dump: {OUTF}")
