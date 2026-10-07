# Analiz Paneli — Veri Sözlüğü ve Kaynak Dökümü

PISA puan-şişmesi araştırması (Türkiye, 2013–2025) için analiz panelleri.
Tümü `analysis/01_build_panel.py` ile üretilir (yeniden üretilebilir). Hiçbir değer
hafızadan yazılmamıştır; her değer bir kaynak dosyadan okunur ve her çıktı satırı
köken bilgisi (source_file / sheet / cell_ref) taşır.

Üretim: `python analysis/01_build_panel.py`
Oluşturulma tarihi: 2026-09-15

---

## Dosyalar

| Dosya | Satır | İçerik |
|---|---:|---|
| `pisa_scores_long.csv`   | 1690 | Ülke × döngü × alan; ortalama + S.E. (hücre düzeyinde köken) |
| `pisa_scores_wide.csv`   | 579  | Ülke × döngü; math/reading/science/cps ortalama+S.E. + kapsam/hariç tutma/yanıt oranları |
| `governance_annual.csv`  | 2344 | ISO3 × yıl (1996–2025); WGI cc/rl + CPI |
| `analysis_panel.csv`     | 579  | wide + döngü yılı ve bir önceki yıl yönetişim + cycle_index |

---

## Kaynaklar

- **PISA ortalama puanları (tüm döngüler 2000–2025)** —
  `data/pisa/2025/annex_tables/mrq53f.xlsx`, trend tabloları:
  - `Table I.B1.2a.36` = Fen (science), 2006→2025
  - `Table I.B1.2a.37` = Okuma (reading), 2000→2025
  - `Table I.B1.2a.38` = Matematik (math), 2003→2025
  - `Table I.B1.2a.4`  = Hesaplamalı problem çözme (cps2025), yalnız 2025
  Her tabloda döngü başlıkları "PISA 20xx" (satır 8), altında `Mean score` / `S.E.`
  sütun çiftleri. Ülke satırları "OECD average" satırından sonra alfabetik.
- **Kapsam / hariç tutma / yanıt oranları** — `data/derived/annex_extract.csv`
  (Annex A2; kökeni orada belgeli). `iso3 + cycle` ile birleştirilir.
- **WGI (yönetişim)** — `data/governance/wgi/wgidataset_with_sourcedata-2025.xlsx`,
  sayfa `cc` (yolsuzluğun kontrolü) ve `rl` (hukukun üstünlüğü). Sütunlar:
  estimate = col I (9.), S.E. = col J (10.), pctrank = col M (13., "Governance score (0-100)").
  Yıl aralığı 1996–2024.
- **CPI** — `data/governance/cpi/CPI2025_Results.xlsx`, sayfa `CPI Timeseries 2012 - 2025`.
  Bu sayfa 2012–2025 tam serisini içerdiği için tek yetkili kaynak olarak kullanıldı
  (2013=50, 2024=34, 2025=31 doğrulandı). `claim_check/evidence/cpi/CPI2024-Results-and-trends.xlsx`
  2012–2024 için teyit eder. CPI çalışma kitabı katı-OOXML (purl.oclc.org) ad-alanı
  kullandığından openpyxl/calamine ile açılamaz; script içindeki `read_strict_xlsx_sheet`
  ile ham XML üzerinden okunur.

---

## Sütun sözlüğü

### pisa_scores_long.csv
| Sütun | Anlam |
|---|---|
| `country_name` | Ekonomi adı (kaynak tablodaki hali; sondaki `*` uyarı işareti çıkarılmış) |
| `iso3` | ISO3 kodu (aşağıya bakınız). Toplamlar: `OECD`, `OECD_A23`, `OECD_A35`, `OECD_TOT` |
| `oecd_member` | 1 = güncel OECD üyesi (38), 0 = değil, boş = toplam satırı |
| `cycle` | PISA döngü yılı (2000–2025) |
| `domain` | `math` / `reading` / `science` / `cps2025` |
| `mean` | Ortalama puan (3 ondalık, tam saklanan hassasiyetten yuvarlanmış) |
| `se` | Standart hata |
| `source_file`, `sheet`, `cell_ref` | Köken; `cell_ref` = `<sheet>!<sütun><satır>` (ortalama hücresi) |

Yalnız sayısal ortalaması olan (yani o döngüye katılan) satırlar yazılır; `m`/`c` (veri yok /
çok az gözlem) satırları atlanır. Bu nedenle 2000–2012 için ülke kapsamı seyrektir (bkz. bilinen boşluklar).

### pisa_scores_wide.csv
Bir satır = ülke × döngü. `math_mean/se`, `reading_mean/se`, `science_mean/se`,
`cps2025_mean/se` (yalnız 2025 dolu) + `annex_extract.csv`'den birleştirilen
`coverage_index3`, `overall_exclusion_pct`, `school_rr_before`, `school_rr_after`,
`student_rr`, `asterisk_flag`. Köken: `scores_source_file` (trend kitabı) ve `annex_source`;
hücre düzeyi köken için `pisa_scores_long.csv`'ye bakınız.

### governance_annual.csv
| Sütun | Anlam |
|---|---|
| `iso3`, `year` | 1996–2025 |
| `cc_est`, `cc_se`, `cc_pctrank` | WGI Control of Corruption: tahmin, S.E., 0–100 skor |
| `rl_est`, `rl_se` | WGI Rule of Law: tahmin, S.E. |
| `cpi` | Transparency Intl. CPI skoru (0–100) |
| `wgi_source_file`, `wgi_cc_ref`, `wgi_rl_ref`, `cpi_source_file`, `cpi_ref` | Köken (hücre) |

Yalnız PISA'da yer alan 91 ekonominin ISO3 kümesi için satır üretilir; en az bir değeri
olan (iso3, yıl) çiftleri yazılır.

### analysis_panel.csv
`pisa_scores_wide.csv` + döngü yılında yönetişim. WGI için etkin yıl = `min(cycle, 2024)`
(WGI 2024'e kadar; **2025 döngüsü için 2024 WGI kullanılır**). `_prev` = bir önceki yıl.
CPI gerçek döngü yılından (2012–2025) alınır, `cpi_prev` = döngü-1.
`cycle_index`: 2000=1, 2003=2, 2006=3, 2009=4, 2012=5, 2015=6, 2018=7, 2022=8, 2025=9.
`gov_year` / `gov_year_prev` = kullanılan WGI yılları.

---

## ISO3 eşleme notları
Egemen ekonomiler standart ISO3 alır. Ulusal yönetişim serisine yanlış eklenmemesi için
alt/üst-ulusal birimlere Q-önekli sözde kod verilmiştir (bunlar için yönetişim satırı yoktur):
- `QCI` = B-S-J-Z (China), `QDT` = Dushanbe (Tajikistan), `QKI` = Kurdistan Region (Iraq),
  `QUA` = Ukrainian regions (17 of 27).
- `HKG` Hong Kong (China), `MAC` Macao (China), `TWN` Chinese Taipei, `XKX` Kosovo,
  `PSE` Palestinian Authority — bunlar WGI/CPI'de eşleşir (CPI'de Kosovo `KSV`→`XKX` çevrildi).

---

## Doğrulama (defter değerleriyle) — 24/24 PASS

Türkiye math/read/sci: 2015=420/428/425 · 2018=454/466/468 · 2022=453/456/476 · 2025=462/472/494 — **PASS**
Türkiye CPS 2025=473, OECD ort. CPS=500 — **PASS**
OECD ort. 2025 reading=461 / math=463 / science=482 — **PASS**
Georgia 2025=416/384/422 · Hungary 2025=459/452/480 — **PASS**
WGI cc Türkiye 2012≈0.1585, 2024≈−0.5632 — **PASS**
CPI Türkiye 2013=50, 2024=34, 2025=31 — **PASS**

(Tam liste script çıktısında; her seferinde otomatik yeniden hesaplanır.)

---

## Bilinen boşluklar / sınırlar
- **2000–2012 ülke kapsamı seyrek.** Trend tablolarında bu döngülerde çok sayıda ekonomi `m`
  taşır; yalnız sayısal ortalaması olanlar panele girer. Döngü başına alan-ortalama satır sayısı
  yaklaşık: math 2003≈37 → 2025≈93; reading 2000≈40 → 2025≈93; science 2006≈55 → 2025≈94.
- **cps2025 yalnız 2025**; yeni alan olduğundan başka döngü yoktur.
- **2025 için hariç tutma/yanıt oranları yok.** 2025 Annex A2 StatLink kitabı
  (`pe3lsg.xlsx`) yalnız kapsama (CI3) yayımlar; `overall_exclusion_pct`, `school_rr_*`,
  `student_rr` 2025 satırlarında boştur (yalnız tam PDF'de vardır — bkz. annex_extract README).
- **WGI 2025 yok** (seri 2024'te biter); 2025 döngüsü için 2024 WGI kullanıldı.
  `governance_annual.csv`'de 2025 satırları yalnız CPI (85 satır) taşır.
- **Sözde-kodlu 4 ekonomi** (QCI, QDT, QKI, QUA) için yönetişim satırı yoktur (kasıtlı;
  ulusal seriyle yanlış eşleşmeyi önlemek için). 91 ekonomiden 87'sinin en az bir yönetişim satırı var.
- **Standart hata boşluğu yok:** long dosyada 0 satırda S.E. boştur (trend tabloları ortalamayla
  birlikte daima S.E. verir).
- **`language_exclusion_pct`, `replacement_schools`** hiçbir kaynakta yok (annex_extract README).
- **V-Dem/ERT epizotları** (`data/governance/ert/ert.csv`) bu panelde kullanılmadı; epizot-temelli
  olup yıllık skaler olmadığından deliverable sütunlarına girmez, ileride ayrı birleştirilebilir.
- **`QUA` (Ukrainian regions 17/27)** için ulusal Ukrayna (UKR) yönetişimi bir vekil olarak
  istenirse eklenebilir; yanıltıcı olmaması için kasıtlı olarak eklenmedi.
