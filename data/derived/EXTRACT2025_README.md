# PISA 2025 — Örnekleme (dışlama/yanıt oranları) ve Test Çabası Tabloları
Üreten: `analysis/06_extract_2025_tables.py` — Tarih: 2026-09-15

## Ne nerede bulundu

### (a) Dışlama ve yanıt oranları — `exclusion_response_2025.csv`
- **2025 Annex A2 StatLink çalışma kitabı (`data/pisa/2025/annex_tables/pe3lsg.xlsx`) yalnızca kayıt/kapsam tablolarını içerir**:
  `Table I.A2.1` (15 yaş kayıt değişimi + Coverage Index 3), `Table I.A2.2` (modal ISCED),
  `Table I.A2.3` (sınıf düzeyi dağılımı). **Dışlama tablosu ve yanıt-oranı tablosu YOKTUR.**
- Bu nedenle dışlama ve okul/öğrenci yanıt oranları PISA 2025 Cilt I'de **yalnızca metin (prose)**
  olarak, ve **yalnızca 14 dipnotlu (yıldız/asterisk) ülke/bölge** için yayımlanmıştır
  (Reader's Guide, `data/pisa/2025/73451bc5-en.pdf`, fiziksel s.16–20). Diğer tüm ülkeler için değerler **"not found"**.
- Roster: `Table I.A2.1`'de 2025 CI3 sayısal olan **91 katılımcı ekonomi**
  + 2 İspanya alt-bölgesi (Murcia, Catalonia) = 93 satır.
- Değer taşıyan ülkeler: Canada, Netherlands, New Zealand, Norway, Albania, United States
  (ulusal); Murcia & Catalonia (yalnızca okul-içi dışlama). Her prose değeri, çalışma anında
  PDF sayfasında birebir aranan bir "evidence" cümlesine sabitlenmiştir (bulunamazsa script hata verir).
- `number_of_replacement_schools` ve okul-düzeyi dışlama hiçbir ülke için raporlanmamıştır → "not found".

### (b) Test çabası — `effort_2025.csv`
- Kaynak: Annex A1 `Table I.A1.1` StatLink çalışma kitabı (`data/pisa/2025/annex_tables/78340u.xlsx`, sheet `Table I.A1.1`),
  makine-okunur. "Average effort invested in the PISA test" (10-puanlık ölçek) = çaba değeri;
  ilk yüzde sütunu = "çok az çaba" (very-low-effort) payı.
- Sütunlar: effort_2025 (+se), effort_2018, effort_2022, diff_2025_vs_2018, diff_2025_vs_2022,
  verylow_effort_pct_2025, verylow_effort_pct_2018.

### (c) Denetim/uyarı bayrakları — `adjudication_2025.csv`
- 2025 Cilt I'de ayrı bir **Annex A4 yoktur**. Uyarı (asterisk) bilgisi Reader's Guide'dadır.
- 15 kayıt: full/limited reporting with asterisk + Catalonia (ayrı raporlanmadı).
  Her satır PDF sayfasına ve birebir doğrulanan bir kanıt cümlesine bağlıdır.

## Parsing yöntemi
- `pdftotext -layout` ile PDF fiziksel sayfalara ayrıldı; dışlama/yanıt/denetim değerleri
  Reader's Guide metninden okunup PDF'te birebir doğrulandı.
- Effort değerleri openpyxl ile `Table I.A1.1` başlık satırları (6–8) doğrulanarak sütun-haritasından okundu.
- ISO3: PDF Reader's Guide ülke-kod listesinden ayrıştırıldı; Türkiye=TUR.
- `source_page` = fiziksel PDF sayfa numarası (pdftotext sayfa indeksi).

## Doğrulama (PASS/FAIL)
- [PASS] OECD-35 effort diff vs 2018 = -0.5 (bulunan=-0.5, beklenen=-0.5)
- [PASS] OECD-35 effort diff vs 2022 = -0.3 (bulunan=-0.3, beklenen=-0.3)
- [PASS] OECD-35 very-low-effort 2018 = 3.5% (bulunan=3.5, beklenen=3.5)
- [PASS] OECD-35 very-low-effort 2025 = 5.4% (bulunan=5.4, beklenen=5.4)
- [PASS] Türkiye Coverage Index 3 = 0.7224 (bulunan=0.7224, beklenen=0.7224)
- [PASS] Türkiye sample 7 702 students / 203 schools (country note) (bulunan=found, beklenen=found)

Rapor metni (PDF fiziksel s.309): 35 OECD ülkesi ortalamasında çaba 2018'e göre -0.5, 2022'ye göre
-0.3 puan; "çok az çaba" payı %3.5 → %5.4. Türkiye kapsamı (CI3) ≈ 0.7224 (stat.link/pe3lsg);
Türkiye 2025 örneklemi 7 702 öğrenci / 203 okul (ülke notu, `data/pisa/2025/country_notes/3f140b0d-en.pdf`).

## Anahtar effort değerleri (Table I.A1.1)
- OECD average-35: 2025=7.16, d18=-0.52, d22=-0.31, verylow%25=5.42
- Türkiye: 2025=8.32, 2018=8.91, 2022=8.57
- Georgia: 2025=7.92, 2018=7.74, 2022=7.74
- Hungary: 2025=7.09, 2018=7.7, 2022=7.3

## Eksik olanlar
- 91 katılımcının çoğu için dışlama/yanıt oranı 2025 Cilt I'de yayımlanMAmıştır → "not found"
  (tam per-ülke tablo yalnızca ileride çıkacak PISA 2025 Technical Report Ch.14'te olacaktır).
- `number_of_replacement_schools`: hiçbir ülke için raporlanmadı.
