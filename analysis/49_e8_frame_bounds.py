# -*- coding: utf-8 -*-
"""
49_e8_frame_bounds.py — editoryal düzeltme E8 (F1; düşük öncelik): çerçeve kanalının ön-dönemi ve okul içi dışlama sınırı.

Soru (COWORK_AMPIRIK_DUZELTMELER.md E8):
  (1) Açık öğretim okulları ve Mesleki Eğitim Merkezleri 2003–2012'de çerçevede ya da örneklemde miydi? Makale [86] ve [201]
      bu dönemi nitelemeden genelliyor.
  (2) Okul içi dışlama nüfusun %0,58'inden (2015) %2,11'ine (2025) çıktı (Tablo 1 [58]); §4.3 özdeşliğiyle [78] 1 ve 2 SS açık
      için puan etkisi ne?

ÖNCEDEN BELİRLENEN SEÇİMLER (RESULTS_EMPIRICAL_FIXES.md §0.8; commit 476fe4e, koşudan önce):
  * Özdeşlik (betik 19 ile aynı): μ_tutulan − μ_tüm = q × (μ_tutulan − μ_dışlanan); q = okul içi dışlama oranı
    (`turkiye_exclusion_series.csv` within_rate / 100); açık k ∈ {1, 2} SS.
  * Birincil birim SS (q × k; σ gerektirmez). Puan birimi: σ_2025 `exclusion_frame/summary.json` ci3 bloğundan geri türetilir
    (kaydırma / q; kaynağı 2025 TR T14.A.11–13, betik 19). σ_2015 türetilmiş dosyada yok → --microdata ile 2015 PUF'tan;
    yoksa 2015 puanı yalnız "σ_2015 = σ_2025" etiketli duyarlılık.
  * Adım 1: 2003–2012 PUF sözdizimlerindeki STRATUM değer etiketlerinde Türkiye tabakaları; "OPEN", "DISTANCE", "VOCATIONAL
    TRAINING CENT", "APPRENTICE" (+ Türkçe karşılıkları) aranır, tabaka başına Türkiye öğrenci sayısı yazılır; 2003 teknik
    raporunda "Turkey" ile bu dizgilerin aynı sayfada geçtiği sayfalar listelenir. 2006/2009/2012 teknik raporları diskte yok →
    "dış veri gerekli". Girdi yoksa adım koşulmaz, durum dosyaya yazılır.
SONRADAN EKLENENLER: 2026-09-26 (yerel koşu 1'den sonra; E6'da 2012'nin 38 Türkiye tabakası etiketsiz çıktı) — `parse_value_labels`
  hatası düzeltildi: değişken adını dosyanın her yerinde arıyordu, gerçek sözdiziminde önce DATA LIST satırına (`STRATUM 20-26 (A)`)
  takılıp boş dönüyordu; artık yalnız VALUE LABELS komutlarının içinde arar ve tırnaksız harf-rakam kodları da tanır
  (ör. `TUR0101 "etiket"`). Etiket kaynağı ve sınıflama tanımı değişmedi.
Girdi: data/derived/exclusion_frame/{turkiye_exclusion_series.csv, summary.json};
       adım 1: data/pisa_microdata/<yıl>/PISA<yıl>_SPSS_student.txt + PUF zip'leri (`_pisa_puf.REGISTRY`),
               docs/oecd_technical_reports/2003/9789264010543-en.pdf (pdfplumber);
       --microdata: data/pisa_microdata/2015/PUF_SPSS_COMBINED_CMB_STU_QQQ.zip, data/pisa/2025/database/CY09_MS_STU_PUF.zip.
Çıktı: data/derived/empirical_fixes/e8_within_school_bound.csv, e8_frame_status.md, e8_summary.json.
Kullanım: python analysis/49_e8_frame_bounds.py [--microdata]      Yazan: Claude Code (bulut oturumu), 2026-09-26.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE))
D = ROOT / "data" / "derived"
OUT = D / "empirical_fixes"
EXF = D / "exclusion_frame"
TR2003 = ROOT / "docs" / "oecd_technical_reports" / "2003" / "9789264010543-en.pdf"
DOMS = {"math": "MATH", "reading": "READ", "science": "SCIE"}
GAPS = (1.0, 2.0)
PATTERNS = [r"\bOPEN\b", r"DISTANCE", r"VOCATIONAL\s+TRAINING\s+CENT", r"APPRENTICE", r"A[CÇ]IK\s*[OÖ][GĞ]RET", r"MESLEK[İI]?\s+E[GĞ][İI]T[İI]M\s+MERKEZ",
            r"[CÇ]IRAK"]


# ----------------------------------------------------------------------------- adım 2
def sigma_2025_from_summary() -> dict:
    s = json.loads((EXF / "summary.json").read_text(encoding="utf-8"))["mechanical_bound"]["ci3_drop_2022_2025"]
    q = float(s["q_share_of_tested_pop"])
    return {dom: float(s["shift_points"][dom]["gap_1.0SD"]) / q for dom in DOMS}


def sigma_microdata() -> dict:
    """Türkiye öğrenci düzeyi SS: W_FSTUWT ağırlıklı SS, PV başına, PV'ler üzerinden ortalama (M = 10)."""
    import importlib
    import tempfile
    m43 = importlib.import_module("43_e1_conditional_change")
    out = {}
    pv = [f"PV{i}{r}" for i in range(1, 11) for r in DOMS.values()]
    with tempfile.TemporaryDirectory(prefix="e8_", dir=os.environ.get("PISA_TMP")) as td:
        for yr, zp, suf in ((2015, ROOT / "data/pisa_microdata/2015/PUF_SPSS_COMBINED_CMB_STU_QQQ.zip", "_QQQ.sav"),
                            (2025, ROOT / "data/pisa/2025/database/CY09_MS_STU_PUF.zip", ".sav")):
            df = m43._sav_from_zip(zp, suf, ["CNT", "W_FSTUWT"] + pv, td)
            t = df[df.CNT.astype(str) == "TUR"]
            w = pd.to_numeric(t.W_FSTUWT, errors="coerce").to_numpy(float)
            out[yr] = {}
            for dom, root in DOMS.items():
                sds = []
                for i in range(1, 11):
                    x = pd.to_numeric(t[f"PV{i}{root}"], errors="coerce").to_numpy(float)
                    ok = np.isfinite(x) & np.isfinite(w)
                    mu = np.average(x[ok], weights=w[ok])
                    sds.append(float(np.sqrt(np.average((x[ok] - mu) ** 2, weights=w[ok]))))
                out[yr][dom] = float(np.mean(sds))
    return out


def within_bound(sig_micro: dict | None):
    ser = pd.read_csv(EXF / "turkiye_exclusion_series.csv").set_index("cycle")
    s25 = sigma_2025_from_summary()
    rows = []
    for cyc in ser.index:
        q = float(ser.loc[cyc, "within_rate"]) / 100
        for dom in DOMS:
            if sig_micro and cyc in sig_micro:
                sig, src = sig_micro[cyc][dom], "mikroveri (W_FSTUWT, M = 10)"
            elif cyc == 2025:
                sig, src = s25[dom], "exclusion_frame/summary.json ci3 bloğu (2025 TR T14.A.11–13)"
            else:
                sig, src = s25[dom], "DUYARLILIK: σ_2025 kullanıldı (bu döngünün σ'sı türetilmiş dosyada yok)"
            for k in GAPS:
                rows.append({"cycle": int(cyc), "domain": dom, "q_within": round(q, 6), "gap_sd": k,
                             "shift_sd_units": round(q * k, 6), "sigma": round(sig, 4), "sigma_source": src,
                             "shift_points": round(q * k * sig, 4)})
    b = pd.DataFrame(rows)
    ch = []
    for dom in DOMS:
        for k in GAPS:
            a = b[(b.cycle == 2015) & (b.domain == dom) & (b.gap_sd == k)].iloc[0]
            z = b[(b.cycle == 2025) & (b.domain == dom) & (b.gap_sd == k)].iloc[0]
            ch.append({"cycle": "2015->2025", "domain": dom, "q_within": round(z.q_within - a.q_within, 6), "gap_sd": k,
                       "shift_sd_units": round(z.shift_sd_units - a.shift_sd_units, 6), "sigma": None,
                       "sigma_source": f"2015: {a.sigma_source} | 2025: {z.sigma_source}",
                       "shift_points": round(z.shift_points - a.shift_points, 4)})
    return pd.concat([b, pd.DataFrame(ch)], ignore_index=True)


# ----------------------------------------------------------------------------- adım 1
def parse_value_labels(syn: Path, var: str) -> dict:
    """SPSS sözdiziminin VALUE LABELS komutlarından tek değişkenin etiketleri (tolerant ayrıştırıcı).

    Yalnız `VALUE LABELS` komutlarının içinde arar (komut, satır sonundaki `.` ya da yeni bir SPSS komutu ile biter); böylece
    DATA LIST (`STRATUM 20-26 (A)`) ve VARIABLE LABELS (`STRATUM 'Stratum ID'`) satırları yanlış başlangıç sayılmaz.
    Komut içinde değişken başlığı `STRATUM` ya da `/STRATUM` (aynı satırda ilk çift olabilir); ardından satır başına
    `'kod' 'etiket'`, `sayı 'etiket'` ya da `KOD 'etiket'` (tırnaksız harf-rakam kod). Değişkenin bloğu `/` ile başlayan satırda,
    çift olmayan ilk satırda ya da komut sonunda biter.
    """
    lines = syn.read_text(encoding="latin-1").splitlines()
    pair = re.compile(r"""^\s*(?:(['"])([^'"]*)\1|([A-Za-z0-9_.\-]+))\s+(['"])(.*)\4\s*\.?\s*$""")
    head = re.compile(rf"""(?i)^/?\s*{var}\b\s*(.*)$""")
    vl_start = re.compile(r"(?i)^\s*value\s+labels\b\s*(.*)$")
    new_cmd = re.compile(r"(?i)^\s*(variable\s+labels|missing\s+values|data\s+list|formats|execute|save|value\s+labels|"
                         r"compute|recode|variable\s+level|add\s+value\s+labels)\b")
    commands, cur = [], None
    for ln in lines:
        st = ln.strip()
        if st.startswith("*"):
            continue
        m = vl_start.match(st)
        if m:
            if cur is not None:
                commands.append(cur)
            cur = [m.group(1).strip()] if m.group(1).strip() else []
        elif cur is not None:
            if new_cmd.match(st):
                commands.append(cur)
                cur = None
                continue
            cur.append(st)
        if cur is not None and cur and cur[-1].endswith("."):  # SPSS komut sonu
            commands.append(cur)
            cur = None
    if cur is not None:
        commands.append(cur)
    out: dict = {}
    for cmd in commands:
        on = False
        for st in cmd:
            if not on:
                h = head.match(st)
                if h:
                    on = True
                    rest = h.group(1).strip()
                    m = pair.match(rest) if rest else None
                    if m:
                        out[(m.group(2) if m.group(1) else m.group(3)).strip()] = m.group(5)
                continue
            if st.startswith("/") or not st:
                break
            m = pair.match(st)
            if not m:
                break
            out[(m.group(2) if m.group(1) else m.group(3)).strip()] = m.group(5)
        if out:
            break
    return out


def _norm_code(x) -> str:
    """Tabaka kodu: sayısal ise baştaki sıfırsız tam sayı metni, değilse kırpılmış büyük harf metin."""
    s = str(x).strip().strip("'\"")
    try:
        f = float(s)
        return str(int(f)) if f.is_integer() else s
    except ValueError:
        return s.upper()


def frame_status() -> tuple[list[dict], list[str]]:
    import _pisa_puf as P
    rows, notes = [], []
    for cyc in (2003, 2006, 2009, 2012):
        cfg = P.REGISTRY[cyc]
        syn, zp = ROOT / cfg["syn"], ROOT / cfg["zip"]
        if not syn.exists() or not zp.exists():
            notes.append(f"{cyc}: PUF girdisi yok ({cfg['syn']} / {cfg['zip']}) → bu koşuda incelenmedi")
            continue
        labels = parse_value_labels(syn, "STRATUM")
        if not labels:
            notes.append(f"{cyc}: STRATUM değer etiketi sözdiziminden ayrıştırılamadı → DUR (elle bakılmalı)")
            continue
        labels = {_norm_code(k): v for k, v in labels.items()}
        df = P.read_columns(cyc, ["CNT", "STRATUM", "W_FSTUWT"])
        t = df[df.CNT == "TUR"]
        g = t.groupby("STRATUM").agg(n=("W_FSTUWT", "size"), w=("W_FSTUWT", "sum")).reset_index()
        for r in g.itertuples():
            code = _norm_code(r.STRATUM)
            lab = labels.get(code, "(etiket yok)")
            hits = [p for p in PATTERNS if re.search(p, lab.upper())]
            rows.append({"cycle": cyc, "source": f"{cfg['zip']} + {cfg['syn']}#STRATUM", "stratum": code, "label": lab,
                         "n_students": int(r.n), "weighted": round(float(r.w), 1), "pattern_hits": ";".join(hits)})
        tur_labels = {k: v for k, v in labels.items()
                      if k.upper().startswith("TUR") or k.startswith("792") or "TURK" in v.upper()}  # 792 = ISO sayısal Türkiye
        flagged = [f"{k}: {v}" for k, v in tur_labels.items() if any(re.search(p, v.upper()) for p in PATTERNS)]
        notes.append(f"{cyc}: sözdiziminde Türkiye'ye ait {len(tur_labels)} STRATUM etiketi; desenle eşleşen: "
                     f"{flagged if flagged else 'yok'} (örneklemde gözlenen tabaka sayısı {len(g)})")
    if TR2003.exists():
        try:
            import pdfplumber
            with pdfplumber.open(str(TR2003)) as doc:
                hits = []
                for i, pg in enumerate(doc.pages, start=1):
                    txt = pg.extract_text() or ""
                    if "Turkey" in txt and any(re.search(p, txt.upper()) for p in PATTERNS[:4]):
                        for m in re.finditer(r"Turkey", txt):
                            hits.append(f"s. {i} (pdf): …{' '.join(txt[max(0, m.start() - 150): m.end() + 250].split())}…")
            notes.append(f"2003 teknik raporu ({TR2003.relative_to(ROOT)}): {len(hits)} eşleşme")
            rows += [{"cycle": 2003, "source": str(TR2003.relative_to(ROOT)), "stratum": "", "label": h, "n_students": None,
                      "weighted": None, "pattern_hits": "metin"} for h in hits]
        except ImportError:
            notes.append("2003 teknik raporu var ama pdfplumber yok → incelenmedi")
    else:
        notes.append(f"2003 teknik raporu yok ({TR2003.relative_to(ROOT)}) → bu koşuda incelenmedi")
    notes.append("2006 / 2009 / 2012 teknik raporları diskte yok → dış veri gerekli (görev metni)")
    return rows, notes


def write_status_md(rows: list[dict], notes: list[str]):
    L = ["# E8 ADIM 1 — ÇERÇEVE DURUMU 2003–2012", "",
         "Betik 49 çıktısı; elle düzenlenmez. Kaynak + tabaka/sayfa satır başına.", "",
         "| | Not |", "| :---: | :--- |"]
    for n in notes:
        code = "🔴" if ("yok" in n and "eşleşen: yok" not in n) or "DUR" in n or "dış veri" in n else "🟢"
        L.append(f"| {code} | {n.replace('|', '/')} |")
    L += ["", "**Legend:** 🟢 incelendi · 🔴 girdi yok, ayrıştırılamadı ya da dış veri gerekli.", ""]
    if rows:
        L += ["| Döngü | Kaynak | Tabaka | Etiket | n | Ağırlıklı | Desen |", "| ---: | :--- | :--- | :--- | ---: | ---: | :--- |"]
        for r in rows:
            L.append(f"| {r['cycle']} | {r['source']} | {r['stratum']} | {str(r['label']).replace('|', '/')} | "
                     f"{'' if r['n_students'] is None else r['n_students']} | {'' if r['weighted'] is None else r['weighted']} | {r['pattern_hits']} |")
    tmp = OUT / "e8_frame_status.md.tmp"
    tmp.write_text("\n".join(L) + "\n", encoding="utf-8")
    os.replace(tmp, OUT / "e8_frame_status.md")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--microdata", action="store_true", help="σ_2015 ve σ_2025'i PUF'tan hesapla (Windows)")
    a = ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    sig = sigma_microdata() if a.microdata else None
    b = within_bound(sig)
    tmp = OUT / "e8_within_school_bound.csv.tmp"
    b.to_csv(tmp, index=False, encoding="utf-8")
    os.replace(tmp, OUT / "e8_within_school_bound.csv")
    rows, notes = frame_status()
    write_status_md(rows, notes)
    summ = {"note": "E8 — okul içi dışlama sınırı (özdeşlik μ_tutulan − μ_tüm = q × fark) ve çerçeve durumu; ön-belirleme §0.8 (commit 476fe4e).",
            "sigma_2025_from_summary": {k: round(v, 4) for k, v in sigma_2025_from_summary().items()},
            "sigma_microdata": sig, "frame_notes": notes,
            "bound_2015_2025": b[b.cycle.astype(str).isin(["2015", "2025", "2015->2025"])].to_dict("records")}
    tmp = OUT / "e8_summary.json.tmp"
    tmp.write_text(json.dumps(summ, ensure_ascii=False, indent=1), encoding="utf-8")
    os.replace(tmp, OUT / "e8_summary.json")
    print(b[b.cycle.astype(str).isin(["2015", "2025", "2015->2025"])][["cycle", "domain", "q_within", "gap_sd", "shift_sd_units", "sigma",
                                                                       "shift_points"]].to_string(index=False))
    print("\n".join(notes))
    return 0


if __name__ == "__main__":
    sys.exit(main())
