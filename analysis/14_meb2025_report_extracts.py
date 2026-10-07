#!/usr/bin/env python3
"""MEB ÖDSGM 'PISA 2025 Türkiye Raporu' (docs/national_reports_meb/PISA2025TurkiyeRaporu.pdf,
216 s., 4 Eyl 2026) — grafiklerden okunan sayıların kayıt altına alınması.

Değerler grafik etiketlerinden transkribe edildi; betik her sayının ilgili GRAFİK BLOĞUNUN
(başlıktan bir sonraki grafik/başlığa kadar) pdftotext metninde geçtiğini doğrular ve çalışmaya
başlamadan önce kasıtlı yanlış değerlerin reddedildiğini kendi üstünde sınar (self_test).
Opus 4.8 denetimi (2026-09-15) önceki sürümdeki ±2 sayfalık geniş pencerenin tam sayılar için
koruyucu olmadığını göstermişti; bu sürüm o bulguya yanıttır.
Çıktı: data/derived/meb2025_report_extracts.csv (+ doğrulama raporu ekrana)
Yazan: Claude Fable 5.1, 2026-09-15.
"""
from __future__ import annotations

import re
import subprocess
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
PDF = ROOT / "docs/national_reports_meb/PISA2025TurkiyeRaporu.pdf"
OUT = ROOT / "data/derived/meb2025_report_extracts.csv"

# (grafik, sayfa, gösterge, kategori, ölçüm, değer)
ROWS = [
    # Grafik 1.1 — örneklem vs evren, okul türüne göre öğrenci oranı (%), s.33
    ("Grafik 1.1", 33, "okul türü payı", "Anadolu Lisesi", "örneklem", 46.6),
    ("Grafik 1.1", 33, "okul türü payı", "Anadolu Lisesi", "evren", 47.0),
    ("Grafik 1.1", 33, "okul türü payı", "Mesleki ve Teknik Anadolu Lisesi", "örneklem", 32.8),
    ("Grafik 1.1", 33, "okul türü payı", "Mesleki ve Teknik Anadolu Lisesi", "evren", 28.9),
    ("Grafik 1.1", 33, "okul türü payı", "Anadolu İmam Hatip Lisesi", "örneklem", 9.5),
    ("Grafik 1.1", 33, "okul türü payı", "Anadolu İmam Hatip Lisesi", "evren", 10.3),
    ("Grafik 1.1", 33, "okul türü payı", "Fen Lisesi", "örneklem", 5.9),
    ("Grafik 1.1", 33, "okul türü payı", "Fen Lisesi", "evren", 5.3),
    ("Grafik 1.1", 33, "okul türü payı", "Sosyal Bilimler Lisesi", "örneklem", 3.2),
    ("Grafik 1.1", 33, "okul türü payı", "Sosyal Bilimler Lisesi", "evren", 0.9),
    ("Grafik 1.1", 33, "okul türü payı", "Çok Programlı Anadolu Lisesi", "örneklem", 1.0),
    ("Grafik 1.1", 33, "okul türü payı", "Çok Programlı Anadolu Lisesi", "evren", 3.6),
    ("Grafik 1.1", 33, "okul türü payı", "Anadolu Güzel Sanatlar/Spor Lisesi", "örneklem", 0.9),
    ("Grafik 1.1", 33, "okul türü payı", "Anadolu Güzel Sanatlar/Spor Lisesi", "evren", 1.1),
    ("metin s.33", 33, "okul türü payı", "Ortaokul", "örneklem", 0.1),
    # Grafik 1.2 — sınıf düzeyi (%), s.34
    ("Grafik 1.2", 34, "sınıf düzeyi payı", "10. sınıf", "örneklem", 65.1),
    ("Grafik 1.2", 34, "sınıf düzeyi payı", "9. sınıf", "örneklem", 21.2),
    ("Grafik 1.2", 34, "sınıf düzeyi payı", "11. sınıf", "örneklem", 13.7),
    ("Grafik 1.2", 34, "sınıf düzeyi payı", "8. sınıf", "örneklem", 0.1),
    # Grafik 3.12 — fen puanı değişimi 2022→2025, okul türüne göre (puan), s.78
    ("Grafik 3.12", 78, "fen değişimi 2022→2025", "Fen Lisesi", "puan farkı", 18),
    ("Grafik 3.12", 78, "fen değişimi 2022→2025", "Sosyal Bilimler Lisesi", "puan farkı", 29),
    ("Grafik 3.12", 78, "fen değişimi 2022→2025", "Anadolu Lisesi", "puan farkı", 22),
    ("Grafik 3.12", 78, "fen değişimi 2022→2025", "Çok Programlı Anadolu Lisesi", "puan farkı", 78),
    ("Grafik 3.12", 78, "fen değişimi 2022→2025", "Anadolu İmam Hatip Lisesi", "puan farkı", 26),
    ("Grafik 3.12", 78, "fen değişimi 2022→2025", "Anadolu Güzel Sanatlar/Spor Lisesi", "puan farkı", 13),
    ("Grafik 3.12", 78, "fen değişimi 2022→2025", "Mesleki ve Teknik Anadolu Lisesi", "puan farkı", 15),
    # Grafik 3.13 — resmî/özel fen ortalaması, s.79
    ("Grafik 3.13", 79, "fen ortalaması", "Resmî okul", "PISA 2022", 479),
    ("Grafik 3.13", 79, "fen ortalaması", "Özel okul", "PISA 2022", 465),
    ("Grafik 3.13", 79, "fen ortalaması", "Resmî okul", "PISA 2025", 497),
    ("Grafik 3.13", 79, "fen ortalaması", "Özel okul", "PISA 2025", 475),
    # Grafik 4.11 — okuma, s.119
    ("Grafik 4.11", 119, "okuma ortalaması", "Resmî okul", "PISA 2022", 458),
    ("Grafik 4.11", 119, "okuma ortalaması", "Özel okul", "PISA 2022", 448),
    ("Grafik 4.11", 119, "okuma ortalaması", "Resmî okul", "PISA 2025", 475),
    ("Grafik 4.11", 119, "okuma ortalaması", "Özel okul", "PISA 2025", 449),
    # Grafik 5.11 — matematik, s.139-140
    ("Grafik 5.11", 139, "matematik ortalaması", "Resmî okul", "PISA 2022", 455),
    ("Grafik 5.11", 139, "matematik ortalaması", "Özel okul", "PISA 2022", 447),
    ("Grafik 5.11", 139, "matematik ortalaması", "Resmî okul", "PISA 2025", 464),
    ("Grafik 5.11", 139, "matematik ortalaması", "Özel okul", "PISA 2025", 444),
    # Grafik 6.4 — bilgi işlemsel problem çözme, s.152
    ("Grafik 6.4", 152, "CPS ortalaması", "Resmî okul", "PISA 2025", 475),
    ("Grafik 6.4", 152, "CPS ortalaması", "Özel okul", "PISA 2025", 453),
    # metin s.18 / s.33 — uygulama bilgisi
    ("metin s.33", 33, "uygulama", "okul sayısı", "adet", 203),
    ("metin s.33", 33, "uygulama", "öğrenci sayısı", "adet", 7702),
    ("metin s.33", 33, "uygulama", "il sayısı", "adet", 56),
]


_FULL_TEXT = None


def full_text_lines() -> list[str]:
    """Tüm raporun pdftotext -layout çıktısı (bir kez)."""
    global _FULL_TEXT
    if _FULL_TEXT is None:
        r = subprocess.run(["pdftotext", "-layout", str(PDF), "-"], capture_output=True, text=True,
                           encoding="utf-8", errors="replace")
        _FULL_TEXT = r.stdout.split("\n")
    return _FULL_TEXT


def chart_block(graf: str) -> str:
    """'Grafik X.Y' başlığının GÖVDEDEKİ (içindekiler tablosu değil) geçişinden sonraki blok:
    bir sonraki Grafik/Şekil/Tablo başlığına ya da 45 satıra kadar. Değer araması bu dar blokta yapılır;
    böylece sayfa genelindeki başka istatistikler yanlış pozitif üretemez."""
    lines = full_text_lines()
    key = graf.replace("metin s.", "").strip()
    if graf.startswith("metin s."):
        # ilgili sayfanın gövde bloğu = Grafik 1.1 bloğundan önceki 12 satır + bloğun kendisi
        idx = [i for i, l in enumerate(lines) if re.search(r"\bGrafik 1\.1\b", l) and i > 600]
        i = idx[0] if idx else 0
        return "\n".join(lines[max(0, i - 12): i + 45])
    pat = re.compile(r"\b" + re.escape(key) + r"\b")
    # önce grafik BAŞLIK satırı (satır başında 'Grafik X.Y ...'), yoksa gövdedeki ilk anılma
    title = [i for i, l in enumerate(lines) if re.match(r"\s*" + re.escape(key) + r"\s+[A-ZÇĞİÖŞÜa-z]", l) and i > 600 and not re.search(r"\.{5,}", l)]
    idx = title or [i for i, l in enumerate(lines) if pat.search(l) and i > 600 and not re.search(r"\.{5,}", l)]
    if not idx:
        return ""
    i = idx[0]
    end = i + 45
    for j in range(i + 2, min(len(lines), i + 45)):
        if re.match(r"\s*(Grafik|Şekil|ekil|Tablo)\s+\d", lines[j]) or re.match(r"\s*\d+\.\d+(\.\d+)?\s+[A-ZÇĞİÖŞÜ]", lines[j]):
            end = j
            break
    return "\n".join(lines[i:end])


def fmt(v):
    return (f"{v:.1f}".replace(".", ",") if isinstance(v, float) else str(v))


def found_in(block: str, val) -> bool:
    s = fmt(val)
    pats = [re.escape(s)] + ([re.escape(f"{val:,}".replace(",", "."))] if isinstance(val, int) and val >= 1000 else [])
    return any(re.search(r"(?<![\d,\.])" + p + r"(?![\d,\.])", block) for p in pats)


def self_test() -> None:
    """Doğrulayıcının koruyucu olduğunu kanıtla: kasıtlı yanlış değerler FAIL etmeli."""
    wrong = [("Grafik 3.13", 498), ("Grafik 3.13", 466), ("Grafik 1.1", 46.9), ("Grafik 5.11", 445), ("Grafik 1.1", 44.4)]
    for graf, v in wrong:
        if found_in(chart_block(graf), v):
            raise SystemExit(f"SELF-TEST FAIL: yanlış değer {v} {graf} bloğunda 'bulundu' — doğrulayıcı koruyucu değil")
    print("self-test: 5 kasıtlı yanlış değerin hepsi reddedildi (OK)")


def main() -> int:
    if not PDF.exists():
        raise SystemExit(f"PDF yok: {PDF}")
    self_test()
    blocks = {}
    recs, fails = [], []
    for graf, page, ind, cat, meas, val in ROWS:
        if graf not in blocks:
            blocks[graf] = chart_block(graf)
        ok = found_in(blocks[graf], val)
        recs.append(dict(grafik=graf, sayfa=page, gosterge=ind, kategori=cat, olcum=meas, deger=val,
                         grafik_blogunda_bulundu=ok, source_file=str(PDF.relative_to(ROOT))))
        if not ok:
            fails.append((graf, page, cat, meas, val))
    df = pd.DataFrame(recs)
    df.to_csv(OUT, index=False, encoding="utf-8-sig")
    print(f"{len(df)} satır yazıldı → {OUT}")
    print(f"Grafik bloğunda bulunan: {int(df.grafik_blogunda_bulundu.sum())}/{len(df)}")
    for f in fails:
        print("  BULUNAMADI:", f)
    # türetilmiş özet: örneklem − evren farkı
    g11 = df[df.grafik == "Grafik 1.1"].pivot_table(index="kategori", columns="olcum", values="deger")
    g11["fark_pp"] = (g11["örneklem"] - g11["evren"]).round(1)
    print("\nÖrneklem − evren (puan):")
    print(g11.to_string())
    pub = df[df.kategori.isin(["Resmî okul", "Özel okul"]) & df.olcum.isin(["PISA 2022", "PISA 2025"])]
    pv = pub.pivot_table(index=["gosterge", "kategori"], columns="olcum", values="deger")
    pv["değişim"] = pv["PISA 2025"] - pv["PISA 2022"]
    print("\nResmî vs özel:")
    print(pv.to_string())
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
