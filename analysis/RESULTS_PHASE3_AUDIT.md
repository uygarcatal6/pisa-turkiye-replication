# Faz 3 Denetimi — RESULTS_PHASE3.md sayı + kod incelemesi

Denetleyen: Claude Opus 4.8 (1M). Tarih: 2026-09-15. Yöntem: yalnızca proje kökü altındaki dosyalar; web ve bellek yok. Donör ortalamaları Python ile yeniden hesaplandı (göz kararı yok); 12b çıktıları öğrenci düzeyi parquet önbelleğinden bağımsız olarak yeniden toplandı; §14 doğrulama regex'i gerçek PDF'e karşı test edildi. Hiçbir betik veya rapor düzenlenmedi.

**Özet karar:** Rapordaki sayıların ezici çoğunluğu (≈210 değer) çıktı dosyalarıyla basılı hassasiyette örtüşüyor. Bir tane orta önemli sayı tutarsızlığı (§0 in-time plasebo çifti, yıl karışması) ve iki düşük önemli yuvarlama notu var. Kod tarafında (a)–(e) kontrolleri temiz; tek gerçek bulgu (f): §14'ün "doğrulama" regex'i **tam sayı** değerler için koruyucu değil — kasıtlı yanlış iki tam sayı (498, 466) testi GEÇİYOR. Bu, hesaplanan hiçbir sonucu değiştirmez ama "43 değer PDF metnine karşı doğrulandı" güvencesini tam sayılar için geçersiz kılar.

---

## Tablo 1 — Sayı denetimi (Part 1)

| Konum | Rapordaki ifade | Dosya değeri (kaynak) | Durum |
|---|---|---|---|
| §0 kapsam/puan tablosu (6 satır × 3) | 25,2 / 24,3·15,2·35,2 / 1,0·0,6·1,4 ve 6,1 / 62,5·75,8·78,5 / 10,3·12,5·12,9 | Birebir aynı (`gap_per_coverage_point.csv`) | ✓ Eşleşti |
| §0 kapsam düzeyleri TUR 2006/2012/2015/2025 | 0,467 / 0,684 / 0,699 / 0,722 | 0,4675 / 0,6842 / 0,6989 / 0,7224 (`analysis_panel.csv` coverage_index3; `coverage_adjusted_summary.json`) | ✓ Eşleşti |
| §0 donör kapsam değişimi −3,5 (06→12), −3,7 (15→25) | −3,5 / −3,7 | 8 donör (BEL CHE FRA ISL JPN EST LTU LVA) ortalaması: 0,9374→0,9024 = −3,50; 0,9249→0,8876 = −3,73 (panel) | ✓ Eşleşti (donör kümesi = betiğin belirttiği 8'li) |
| §0 TUR kapsam değişimi "+2,4 puan (0,699 → 0,722)" | +2,4 | 0,72244−0,69887 = +2,357 → 2,4 (`gap_per_coverage_point.csv` TUR_kapsam_pp=2.4) | ⚠ Düşük: +2,4 kaynaktan doğru (yuvarlanmamış); ama gösterilen 0,699→0,722 uçları +2,3 verir. Yöntem tutarsızlığı, sayı değil. |
| §0 in-time plasebo "2009 varsayınca +20 (mat) ve +29 (okuma)" | +20 / +29 | `in_time_placebo.csv`: math gap_2009=20,13 · gap_2012=24,96 ; reading gap_2009=18,62 · gap_2012=28,71 | ⚠ **Orta**: +20 = math'ın **2009** açığı; +29 = reading'in **2012** açığı. İki rakam farklı yıllardan. Cümlenin dediği gibi "2009" alınırsa okuma +18,6 (≈+19), +29 değil. Nitel sonuç (2009–2012'de pozitif sapma) ayakta; çift yanlış. |
| §1 LOO temel açıkları | mat +50,4 / oku +34,1 / fen +48,8 | 50,38 / 34,14 / 48,82 (`leave_one_out.csv`) | ✓ Eşleşti |
| §1 LOO aralıkları | mat +31,6…+57,5 / oku +31,0…+55,1 / fen +29,6…+48,8 | min/max: 31,63…57,48 / 30,97…55,06 / 29,64…48,82 | ✓ Eşleşti |
| §1 "en düşük değer temelin %63'ü" | %63 | 31,63/50,38 = %62,8 | ✓ Eşleşti |
| §2 ızgara medyan / aralık / pozitif oran | mat 50,4·[42,9–70,8]·%100 / oku 33,1·[31,7–34,1]·%100 / fen 16,2·[−16,4–52,6]·%50 | 16 kombinasyon üzerinden yeniden hesap (`donor_rule_grid.csv`): mat med 50,385 min 42,94 max 70,81 poz 16/16; oku med 33,06 min 31,68 max 34,14 poz 16/16; fen med 16,22 min −16,38 max 52,58 poz 8/16 | ✓ Eşleşti |
| §2 "Katar ağırlık 1,0" | 1,0 | QAT top_w=1 (OECD kısıtı kalkınca) | ✓ Eşleşti |
| §3 ön dönem duyarlılığı (9 hücre) | mat 50,4·23,9·31,9 / oku 34,1·29,7·29,6 / fen 48,8·48,8·43,8 | 50,38·23,91·31,89 / 34,14·29,65·29,63 / 48,82·48,82·43,83 (`pre_period_sensitivity.csv`; fen 2003 yok, ilk iki sütun aynı) | ✓ Eşleşti |
| §4 kapsam-düz. tablo (9 gap) | mat 23,9·20,5·19,3 / oku 29,7·28,2·27,1 / fen 48,8·37,7·41,0 | 23,91·20,49·19,33 / 29,65·28,16·27,06 / 48,82·37,73·40,98 (`coverage_adjusted_specs.csv`) | ✓ Eşleşti |
| §4 kapsam katsayısı (b_all) | mat +17,0 / oku +24,9 / fen +35,9 | 16,978 / 24,893 / 35,910 (`coverage_adjusted_summary.json` b_all) | ✓ Eşleşti (b_ctrl değerleri raporda anılmıyor; her ikisi de pozitif, iddia geçerli) |
| §5 koşullu plasebo (n·eğim·R²·artık·sıra) | 84·1,013·0,891·−31,8·5/84 ; 84·—·0,908·−35,1·3/84 ; 38·0,863·0,849·−33,5·1/38 ; 38·—·0,850·−33,0·1/38 | JSON + CSV'den sıralar bağımsız yeniden hesaplandı: TUR 5/84, 3/84, 1/38, 1/38 — tümü doğrulandı | ✓ Eşleşti |
| §5 Gürcistan / Macaristan | GEO −22,0 (9/84), −26,2 (8/84); HUN +2,6 / −2,3 | JSON birebir; sıralar CSV'den doğrulandı | ✓ Eşleşti |
| §7 çaba tablosu (7 gösterge × 4 döngü × TUR/donör) | tüm hücreler | `effort_microdata.csv` (2015/18/22) + `effort_2025_process.csv` (2025); donör = BEL CHE FRA ISL JPN basit ort. Python ile yeniden hesap — **tüm hücreler** birebir | ✓ Eşleşti |
| §7 "2025 en yüksek, 26 ülke, +10,4 s (%22)" | 26 ülke, +10,4 s, %22 | 26 ülke; TUR 57,75 (en yüksek); 57,75−47,39=10,36; 10,36/47,39=%21,9 | ✓ Eşleşti |
| §7 2025 farklar (NT15 −0,9; sıfır eylem −1,3; sona ulaşamama −0,8) | −0,9 / −1,3 / −0,8 | 4,35−5,23=−0,88; 1,49−2,76=−1,27; 0,61−1,42=−0,81 | ✓ Eşleşti |
| §7 doğru % farkı yakınsaması | −15,9 / −6,3 / −6,3 / −1,5 | −15,92 / −6,27 / −6,34 / −1,45 | ✓ Eşleşti |
| §7 termometre TUR 8,91/8,57/8,32; OECD-35 7,16; %2 vs OECD %5,5 | 8,91·8,57·8,32; 7,16; 1,97; 5,51 | `effort_2025.csv` birebir | ✓ Eşleşti |
| §7 Gürcistan (NT15 15,4→8,1; süre 37,5→47,1; sona 3,2→1,5; termo +0,18) ve Macaristan (NT15 5,0; süre 47,8) | tümü | 15,44→8,08; 37,51→47,11; 3,22→1,48; 7,74→7,92 (+0,18); HUN 4,98→5,0, 47,82 | ✓ Eşleşti |
| §8 mikroveri payları (Anadolu/meslek/imam hatip/fen 2018·22·25; özel 11,1) | 46,0·57,5·45,6 / 31,5·24,3·27,1 / 12,7·10,2·9,5 / 4,0·5,6·4,5 / 11,1 | `turkiye_school_type_composition.csv` share (ağırlıklı) birebir; özel = ozel_genel 7,86 + ozel_meslek 3,19 = 11,05 → 11,1 | ✓ Eşleşti |
| §8 "2022 Anadolu +11,5 (meslek −7,2)" | +11,5 / −7,2 | Basılı paylardan: 57,5−46,0=+11,5 ✓; 24,3−31,5=−7,2 ✓ (ham paylardan 24,35−31,49=−7,14→−7,1) | ⚠ Düşük: basılı hassasiyette −7,2 doğru; ham veriden −7,1. |
| §8 MEB 2025 örneklem/evren/fark (7 tür × 3) | 46,6·47,0·−0,4 … 0,9·1,1·−0,2 | `meb2025_report_extracts.csv` birebir; farklar örneklem−evren ile tutarlı | ✓ Eşleşti |
| §8 Ön Rapor 2018 (43,7/31,1/13,7), "≤2,3 fark" | 43,7·31,1·13,7; ≤2,3 | `meb_reported_composition.csv`; maks |fark|=2,3 | ✓ Eşleşti |
| §8 resmî/özel (Grafik 3.13/4.11/5.11/6.4) + "8–16 puan fazla" | 479→497·465→475 / 458→475·448→449 / 455→464·447→444 / 475·453 | `meb2025_report_extracts.csv` birebir; kazanım farkı fen 8, oku 16, mat 12 → [8;16] | ✓ Eşleşti |
| §8 Grafik 3.12 fen değişimi (7 tür) | 18·29·22·78·26·13·15 | birebir | ✓ Eşleşti |
| §8 özel okul payı 2015 %4,8 → 2018+ %11–13; "43 değer doğrulandı" | 4,8; 11–13; 43 | SC013 2015=0,0476; 2018=12,1·2022=12,9·2025=11,1; CSV'de 43 satır, hepsi pdf_metninde_bulundu=True | ✓ Eşleşti (ancak "doğrulandı" gücü için bkz. Tablo 2, bulgu f) |
| §9 dışlama/yanıt (Hollanda 9,3; YZ 8,1; Norveç 10,4; ABD 6,9; TUR yok) + kapsam 0,722 | 9,3·8,1·10,4·6,9; 0,722 | `adjudication_2025.csv` / `exclusion_response_2025.csv`; TUR tüm alanlar "not found"; 0,722 | ✓ Eşleşti |

**Not (§4 metodoloji, sayı değil):** kapsam katsayısı b, hem ön hem post dönem verisiyle tahmin ediliyor ve sonra tedavi etkisini hesaplamak için kullanılıyor; ayrıca katsayı yanlış (pozitif) işaretli. Rapor bunu §4'te açıkça "geçerli seçim düzeltmesi DEĞİL, yalnızca duyarlılık kaydı" diye niteliyor — dolayısıyla yanıltıcı değil.

---

## Tablo 2 — Kod incelemesi (Part 2)

| Betik | Kontrol | Bulgu | Önem | Sonuca etkisi |
|---|---|---|---|---|
| `_synth_core.R` | (a) demean yalnız ön dönem; donör dışlamaları | `run_one` sat.60: `y - mean(y[cycle %in% pre])` → yalnız ön dönem ortalaması çıkarılıyor. `build_pool` sat.44–50: sınıf + OECD + kâğıt-2015 + yıldız (pencere döngülerinde) + tam-veri kuralları belgelendiği gibi uygulanıyor. | — | Temiz (doğru) |
| `09_robustness.R` | (b) in-time plasebo ön 2003–2006 / post 2009–2012; LOO aynı temel havuz | R2 sat.45–46: `pre_f=trim_pre(TUR,c(2003,2006))`, `post_f=c(2009,2012)` — belgelenen tasarım. R1 sat.24–33: `donors` bir kez kuruluyor, `setdiff(donors,dn)` ile her donör aynı temel havuzdan teker teker düşürülüyor. Fen, 2003/2006'da <2 gözlem olduğu için plasebodan doğru şekilde dışlanıyor. | — | Temiz (doğru). Not: raporun §0'daki +20/+29 çifti bu doğru çıktının **yanlış yıl eşleştirmesiyle** okunmasıdır (Tablo 1). |
| `11_coverage_adjusted.R` | (c) within regresyon (y_c~x_c−1) doğru sabit-etki eğimi; residualizasyon tüm ülkelerde aynı b | sat.46–48: y ve x ülke-içi ortalamadan arındırılıp orijinden regresyon → within (FE) eğimi doğru; `-1` doğru (ortalaması sıfır iki değişken). sat.64: `p[[y]] - bset$b * p[[COV]]` — tek skaler b tüm ülkelere uygulanıyor. | — | Temiz (doğru) |
| `11_coverage_adjusted.R` | ek gözlem: coverage_table donör tanımı | JSON `coverage_table` donör düzeyleri (0,906…) **math donör havuzu** ortalaması; §0'daki donör kapsam değişimi ise 8'li kümeden (`gap_per_coverage_point.csv`). İki farklı "donör" tanımı var. | Düşük | Yok — raporlanan hiçbir sayı JSON donör düzeylerini kullanmıyor. |
| `10_placebo_domain.py` | (d) OECD bayrağı; rank_low 1 = en negatif | sat.55–59: `oecd_member` obje/sayısal ayrımıyla sağlam okunuyor (n_oecd=38 üretiyor, uçtan uca doğrulandı). sat.79: `rank(method="min")` artan sıra → 1 = en negatif artık; CSV'den sıralar birebir yeniden üretildi (TUR 1/38 vb.). | — | Temiz (doğru). Not: regresyona odak birimler (TUR/GEO/HUN) dahil (leave-in); bu Türkiye'nin artığını **muhafazakâr** yapar — hata değil. |
| `12b_effort_2025_process.py` | (e) sentinel 0<t<99999990; NT15 havuz medyanından; sıfır-eylem; ağırlık birleşimi öğrenci düşürüyor mu | sat.116: `T.where((T>0)&(T<99999990))` doğru. sat.128–132: item medyanı öğrenciler üzerinden (axis=0), NT15=0,15×medyan doğru. sat.133–134: `a_valid & (Am==0)` sıfır-eylem doğru. sat.157: **left** merge → öğrenci düşmüyor; eşleşmeyen ağırlık sat.175'te 0'a çekiliyor ama n_students tüm satırları sayıyor. Parquet önbelleğinden bağımsız yeniden toplama: **TUR n=7702** (beklenen), rapid5=0,1789, NT15=0,0435, sıfır-eylem=0,0149, medyan/madde=57,75 — **hepsi CSV ile birebir**. | — | Temiz (doğru). Öğrenci sessizce düşmüyor. |
| `12b_effort_2025_process.py` | ek gözlem: docstring vs kod sentinel | Docstring sat.7 "sentinel 99999995–99999999 geçersiz" der; kod ve `variables` alanı `>=99999990` kullanır. Belge/eşik uyuşmazlığı. | Düşük | Yok — 99999990 eşiği tüm sentinelleri yakalar; ~27,8 saatten uzun meşru madde süresi yok. |
| `14_meb2025_report_extracts.py` | (f) doğrulama regex'i önemsizce geçemesin (iki kasıtlı yanlış değer FAIL etmeli) | **BULGU.** Regex `(?<![\d,\.])<değer>(?![\d])` ±2 sayfalık pencerede yalnızca **varlık** arıyor. Gerçek PDF testi: kasıtlı yanlış **ondalık** değerler doğru şekilde FAIL ediyor (46,9 ve 44,4 → False). Ancak kasıtlı yanlış **tam sayılar GEÇİYOR**: 498 (gerçek 497) → **True** (s.80'de başka bir sayı olarak var), 466 (gerçek 465) → **True** (s.78/80). Nedeni: (i) ±2 sayfa penceresi + yoğun istatistik metni, herhangi bir makul 2–3 haneli tam sayıyı bir yerlerde bulur; (ii) lookahead `(?![\d])` — lookbehind'ın aksine — virgül/nokta hariç tutmaz (asimetri). | **Orta** | Hesaplanan sonuçları değiştirmez (43 değer elle transkribe edildi ve Tablo 1'de tutarlı bulundu). Ama "43 değer PDF metnine karşı doğrulandı" güvencesi ~30 tam sayı (tüm puanlar 444–497, puan farkları 13–78, sayımlar 203/7702/56) için **geçersiz**: transkripsiyon hatası bir tam sayı puanda fark edilmeden geçebilir. Ondalık paylar (13 değer) gerçekten doğrulanmış. |

### (f) bulgusunun kanıtı (gerçek PDF'e karşı, script'in kendi mantığıyla)

```
DOĞRU değerler (True olmalı):      46,6 → True | 47,0 → True | 479 → True | 497 → True | 18 → True
KASITLI YANLIŞ (False olmalı):     46,9 → False | 44,4 → False  (ondalık: DOĞRU şekilde fail)
                                    498  → True  | 466  → True   (tam sayı: YANLIŞ şekilde geçiyor)
Yer: '498' s.80'de, '466' s.78 ve s.80'de bulunuyor (hedef s.79'un ±2 penceresi).
```

**Öneri (yalnız kayıt için; düzeltme yapılmadı):** tam sayı doğrulaması için (i) pencereyi hedef sayfaya indir, (ii) değeri kategori/etiketiyle birlikte ara ya da sayfadaki tüm sayıları çıkarıp beklenen kümeyle karşılaştır, (iii) lookahead'i `(?![\d,\.])` yaparak asimetriyi gider. Rapor metnindeki "43 değer doğrulandı" ifadesi "13 ondalık değer metinde doğrulandı; 30 tam sayı yalnızca varlık düzeyinde işaretlendi" olarak nitelenmeli.


---

# Ek denetim 2026-09-16 — §5b (yaratıcı düşünme 2022) ve §5c (işbirlikli problem çözme 2015), betik 13 ve 15

Workflow `pisa-audit-5b-5c` (iki bağımsız Opus 4.8 ajanı; ilk deneme `pisa-audit-5b-crt` 25 araç çağrısından sonra API SSL hatasıyla düştü, transkriptinde §5b'yi tümüyle doğrulamıştı). Ajanlar yalnızca okudu; bölümler aşağıya Fable 5.1 tarafından eklendi.

## §5b Denetimi — PISA 2022 Yaratıcı Düşünme (Opus 4.8, 2026-09-16)

**Kapsam:** `analysis/RESULTS_PHASE3.md` §5b + `analysis/13_creative_thinking_2022.py`. Kaynaklar açılarak doğrulandı: `opbe7a.xlsx` (openpyxl, read_only/data_only), `CY08MSP_CRT_COG.SAV` (pyreadstat, metadata + tek chunk'lı geçiş, sonra silindi), `creative_thinking_2022.csv`, `placebo_conditional_2022.csv`, `placebo_conditional_2022_summary.json`, `innovative_domain_participation.csv`. Proje dosyaları değiştirilmedi (4 çıktı dosyası md5 ile yedeklenip `--no-microdata` çalıştırması sonrası birebir geri yüklendi).

### 1. Excel — Table III.B1.2.1 (`opbe7a.xlsx`)
| İddia (§5b) | Bulunan (dosyadan) | Verdikt |
|---|---|---|
| 74 ülke/ekonomi satırı | 74 | ✅ |
| 64 katılımcı | 64 | ✅ |
| 10 'm' (missing) | 10 ('c' = 0) | ✅ |
| 'm' listesi: Avusturya, İrlanda, Norveç, İsviçre, Türkiye, B.Krallık, Arjantin, Gürcistan, Kosova, Karadağ | tam aynı 10 ülke | ✅ |
| bunların 6'sı OECD üyesi | AUT, IRL, NOR, CHE, TUR, GBR = 6 | ✅ |
| OECD ortalaması 32,67 | 32,6704 → 32,67 | ✅ |
| Macaristan CT 30,94 | 30,9442 → 30,94 | ✅ |
| Macaristan S.E. 0,33 | 0,3281 → 0,33 | ✅ |
| Macaristan çekirdek 477,2 | panel 477,213 → 477,2 | ✅ |
| 'm'/'c' açıklaması (TOC/notlar) | TOC sayfasında: **m** = "Data are not available… not collected by the country… or removed for technical reasons"; **c** = "fewer than 30 students or fewer than 5 schools" | ✅ bulundu |

### 2. Mikroveri — `CY08MSP_CRT_COG.SAV`
| İddia | Bulunan | Verdikt |
|---|---|---|
| 499.843 öğrenci | 499.843 satır (chunk'lı geçiş; meta ile aynı) | ✅ |
| 63 sistem (CNT) | 63 farklı CNT | ✅ |
| TUR yok | yok | ✅ |
| GEO yok | yok | ✅ |
| W_FSTUWT ve hiçbir W_* yok | 301 sütun, sıfır W_* / sıfır ağırlık sütunu | ✅ |
| PV1CRTH_NC…PV10CRTH_NC var | 10/10 var | ✅ |
| PV1MATC/PV1REAC/PV1SCIC var | üçü de var (her biri PV1..PV10) | ✅ |
| gözlenen aralık 0,10–59,30 | min 0,1000 / maks 59,3000 | ✅ |
| 'm' olan hiçbir ülke mikroveride yok | 10 'm' ISO kodunun hiçbiri 63 CNT'de değil | ✅ |

### 3. Çapraz-kontrol ve koşullu test (CSV + JSON, `--no-microdata` ile yeniden üretildi)
| İddia | Bulunan | Verdikt |
|---|---|---|
| yayımlanmış−ağırlıksız fark ort +0,20 | +0,196 → +0,20 | ✅ |
| en büyük |fark| 2,42 (Tayland) | THA 2,416 → 2,42, gerçekten maks | ✅ |
| n=60 eşleşen sistem | 60 | ✅ |
| panelde çekirdek olan 61 sistem, 28 OECD | 61 / 28 | ✅ |
| Tüm/doğrusal: n61 eğim0,1135 R²0,852 RMSE2,57 artık −1,03/−0,40 sıra16/61 | betik çıktısı birebir aynı | ✅ |
| Tüm/karesel: n61 R²0,877 RMSE2,37 artık −1,60/−0,68 sıra12/61 | birebir | ✅ |
| Yalnız OECD/doğrusal: n28 eğim0,0915 R²0,771 RMSE1,61 artık −2,12/−1,32 sıra3/28 | birebir | ✅ |
| Yalnız OECD/karesel: n28 R²0,800 RMSE1,53 artık −1,73/−1,13 sıra4/28 | birebir | ✅ |
| LOO artıkları −1,05 / −1,65 / −2,20 / −1,83 | JSON birebir | ✅ |

### 4. Katılım taraması (`innovative_domain_participation.csv` — kapsam dışı dosya, yine de doğrulandı)
| İddia | Bulunan | Verdikt |
|---|---|---|
| 2015 CPS: TUR 5.895/5.895 | 5895/5895 | ✅ |
| 2015 CPS: HUN 5.658/5.658 | 5658/5658 | ✅ |
| 2015 CPS: GEO 0; 53/73 sistem | GEO flagged=0; 53/73 | ✅ |
| 2018 GLCM: TUR/GEO/HUN boş; 29/80 | üçü de flagged=0; 29/80 | ✅ |

### 5. README / run_all (madde 5)
`analysis/README.md` "Faz 3" satır 13 ve `run_all.py` HEAVY_STEPS "13" kaydı doğru betiği (`13_creative_thinking_2022.py`) ve doğru çıktıyı (`data/derived/mechanisms/placebo_conditional_2022_summary.json`) adlandırıyor; her ikisi de "TUR/GEO katılmadı" notunu içeriyor. Adlanan tüm çıktı dosyaları diskte mevcut. (Küçük doküman notu, kapsam dışı: README giriş cümlesi ağır adımları "06/07/08/12b/13" diye sayarken 15'i atlıyor; Faz-3 tablosu ve run_all doğru olarak 15'i de içeriyor — satır 13 kendisi doğru.)

### Kod bulguları (13_creative_thinking_2022.py) — gerçek hata yok
- **PASS — Tablo ayrıştırma:** 'OECD' başlangıç işaretçisi ilk bölüm başlığını (filtrelenmiş idx 2) buluyor; NON_COUNTRY + startswith("Information on"/"Note"/"* "/"** ") tam olarak 6 ülke-dışı satırı atıyor; '*'/'**' bayrak mantığı doğru (`endswith('*') and not endswith('**')` → örnekleme; `endswith('**')` → bağlantı); 'm'→did_not_participate, 'c'→suppressed_small_sample TOC açıklamasıyla tutarlı.
- **PASS — LOO:** OLS'i odak ülkeyi çıkararak yeniden kuruyor, `np.polyval(b_loo[::-1], core)` ile tahmin (artan-sıra katsayıları doğru şekilde ters çeviriyor); üretilen değerler JSON ile birebir.
- **PASS — İki bütünlük guard'ı:** (a) tabloda 'm' olan ülke mikroveride görülürse SystemExit (m_in_micro boş doğrulandı); (b) |yayımlanmış−ağırlıksız| maks fark > 3,0 ise SystemExit (2,42 < 3,0). Ayrıca <40 katılımcı ve PV sayısı ≠ 10 guard'ları sağlam.
- **PASS — OECD bayrağı ve yeniden üretilebilirlik:** katılımcı&çekirdek&OECD = 28; 'm'&OECD = 6; `--no-microdata` çalıştırması §5b regresyon tablosunu birebir üretti; `placebo_conditional_2022.csv` ve PNG committed sürümle byte-aynı (md5); committed `creative_thinking_2022.csv` mikroveriyle üretilmiş (mikroveri atlanınca md5 değişiyor) — raporla tutarlı.
- **LOW — Etiket gücü:** 'm' → "did_not_participate" açıklamayı hafifçe güçlendiriyor (yasal olarak 'm' "veri yok"un birkaç nedenini kapsar); TUR/GEO için mikroverideki yokluğla desteklendiği için özde doğru; §5b iddiasını etkilemiyor.
- **LOW — Ölü/no-op eşlemeler:** ALIASES'te `"Baku (Azerbaijan)":"Baku (Azerbaijan)"` no-op; MICRO_ISO'da `"QCY":"CYP"` kullanılmıyor (QCY 63 CNT'de yok). Zararsız.
- **LOW — Temp temizliği:** finally bloğu büyük .sav'ı siliyor sonra rmdir (yalnızca boşsa; OSError yutlur). Büyük dosya her zaman siliniyor; boş olmayan temp dizini sessizce ama zararsızca kalabilir. mkdtemp sistem %TEMP%'ine yazıyor (betiğin kendi tercihi).
- **NOT — Ukraine ALIAS gerekli ve doğru:** Volume III tablosu "Ukrainian regions (18 of 27)", panel (Volume I) "(17 of 27)"; ALIAS bunu uzlaştırıp Ukrayna'yı (QUA, çekirdek 438,7) 61'e dahil ediyor. Doğru.

### Verdikt
§5b'nin her sayısı birincil kaynaklara karşı doğrulandı; **50/50 birebir, sıfır uyuşmazlık**. Başlık iddiası — Türkiye ve Gürcistan PISA 2022 yaratıcı düşünmeye katılmadı (Table III.B1.2.1'de 'm'; 63-sistemlik CRT mikroverisi CNT listesinde yok), dolayısıyla bu alan Türkiye için plasebo-alan olamaz; ve katılmama ayırt edici değil (Norveç/İsviçre/İrlanda/Avusturya/B.Krallık da 'm') — iki bağımsız kaynak (Excel + mikroveri) tarafından **doğrulanıyor**. Kod sağlam; gerçek mantık hatası yok, yalnızca LOW düzeyde etiket/ölü-eşleme/temp notları. Betik `--no-microdata` ile raporun regresyon tablosunu birebir yeniden üretiyor. Denetim yalnızca okuma; hiçbir proje dosyası değiştirilmedi (md5 ile teyit), çıkarılan .sav silindi.

## SCOPE B denetimi — §5c "PISA 2015 işbirlikli problem çözme" (Opus 4.8 olgu/kod denetimi)

**Genel karar: DOĞRULANDI.** §5c, öncesindeki "Katılım taraması" paragrafı, §10 tablosundaki yeni satır ve §11 madde 1'deki her sayı birincil kaynaklarla eşleşiyor. `15_cps2015_placebo.py` betiği tam olarak yeniden üretilebilir: önbellekten yeniden çalıştırıldığında taahhüt edilmiş CSV ve JSON çıktılarını değer-bazında birebir üretti. Parquet önbelleğinden bağımsız yeniden hesaplama (413.888 satır, 53 CNT) TUR ve HUN ağırlıklı ortalamalarını CSV ile aynı üretti. Yayımlanmış çapraz-kontrol elde edildi (aşağıya bakın).

### Kontrol edilen sayılar (claim → bulunan)

| Alan / iddia | Raporda | Kaynakta bulunan | Karar |
|---|---|---|---|
| Option_CPS TUR bayrak | 5.895/5.895 | 5895/5895 (`innovative_domain_participation.csv`) | ✓ |
| Option_CPS HUN bayrak | 5.658/5.658 | 5658/5658 | ✓ |
| Option_CPS GEO | 0 | GEO 5316 öğr., 0 bayrak | ✓ |
| CPS 2015 katılan sistem | 53/73 | participated=53, satır=73 | ✓ |
| PV1GLCM 2018 TUR/GEO/HUN | tümü boş | üçü de n_flagged=0 | ✓ |
| GLCM 2018 katılan sistem | 29/80 | participated=29, satır=80 | ✓ |
| Zip boyutu | 36.306.694 B | 36306694 B (ls + manifest) | ✓ |
| Zip sha256 | 14ae3bff… | 14ae3bfff0372c1ade47906a54721872697e626fc044b28de0069f1099a39854 | ✓ |
| Üye sav boyutu | 169.129.616 B | unzip -l = 169129616 B | ✓ |
| Sav satır sayısı | 414.498 öğrenci | meta.number_rows = 414498 | ✓ |
| Sav sistem sayısı | 53 sistem | CNT nunique = 53 | ✓ |
| PV değişkenleri | PV1CLPS…PV10CLPS | 10'u da mevcut | ✓ |
| Ağırlık değişkeni | dosyada yok | W_* değişkeni yok (metadata + kod kitabı) | ✓ |
| Birleştirme kaybı | 0,0000 | merge_loss = 0.0 (parquet) | ✓ |
| Alt-ulusal atma | QES/QUC/QUE → 50 | dropped=['QES','QUC','QUE'], 50 satır | ✓ |
| Regresyon n | 47 (QCH/RUS/TUN çıktı) | with-core = 47, çekirdeksiz=[QCH,RUS,TUN] | ✓ |
| OECD üye sayısı | 35 | oecd=True = 35 | ✓ |
| TUR ağırlıklı ortalama | 422,4 | 422.362 (CSV = parquet recompute) | ✓ |
| TUR ağırlıksız / n | 419,7 / 5.895 | 419.731 / 5895 | ✓ |
| HUN ağırlıklı / ağırlıksız | 472,2 / 479,3 | 472.155 / 479.322 | ✓ |
| OECD ort-of-ortalamalar | 495,4 (n=35) | 495.368 | ✓ |
| Ağırlıklı−ağırlıksız ort | −0,6 | −0.586 | ✓ |
| En büyük \|fark\| | 15,5 (Slovenya) | 15.50 @ SVN | ✓ |
| Şili / Danimarka farkı | −14,1 / +13,3 | −14.08 / +13.29 | ✓ |
| Koşullu tablo (4 satır) | eğim/R²/RMSE/artık/SD/sıra | JSON + betik çıktısı ile tam eşleşme | ✓ |
| Leave-one-out (TUR 4, HUN 4) | −13,7/−13,9/−13,3/−17,1; −11,9/−8,3/−12,1/−7,2 | JSON'la birebir | ✓ |
| Çekirdek 2015 TUR | 424,8 (420,5/428,3/425,5) | 424.760 (420.454/428.335/425.490) | ✓ |
| Çekirdek 2015 HUN | 474,4 | 474.367 | ✓ |
| 2015 uyarı yıldızı | ikisinde de yok | asterisk_flag = nan (ikisi) | ✓ |
| Kod kitabı CNT etiketleri | QCH=B-S-J-G, QES=Spain(Regions), QUC=Massachusetts, QUE=North Carolina, TAP=Chinese Taipei | Codebook_CMB.xlsx sayfasında birebir doğrulandı | ✓ |
| §10 satırı: TUR artığı SD aralığı | −1,2…−1,4 SD | dört spesin gerçek aralığı −1,00…−1,36 (OECD-doğrusal −1,00 aralık dışında) | ⚠ küçük |

### Yayımlanmış çapraz-kontrol (madde 5)
OECD Volume V annex tablosunun **kendisi elde EDİLEMEDİ**: oecd.org, oecd-ilibrary.org ve doi.org (10.1787/9789264285521) hepsi HTTP 403 döndürdü (tarayıcı UA + Referer ile curl ve WebFetch denendi). Ancak resmi OECD CPS ülke ortalamalarını yeniden basan yayımlanmış ikincil bir kaynak elde edildi — **UK DfE "PISA 2015 CPS National Report" (Tablo 5)**: Türkiye **422**, Macaristan **472** (ayrıca Rusya 473, İspanya 496, Portekiz 498 — hepsi bizim mikroveri ortalamalarımızla <0,5 puan uyumlu). Bizim değerlerimiz: TUR 422,4 (Δ≈+0,4), HUN 472,2 (Δ≈+0,2). OECD ortalaması yayımda tasarım gereği 500'e sabit; bizim 495,4 "üye ülke ortalamalarının ortalaması" (bugünkü 35 üyelik) farklı bir kurgu — rapor bu karşılaştırılamazlığı açıkça not ediyor. Not: bu, OECD'nin Volume V annex xlsx'inin birebir kendisi değil; onu yeniden basan bağımsız bir devlet raporu.

### Kod bulguları
1. **Betik doğru ve yeniden üretilebilir.** Birleştirme `validate="one_to_one"` + %1 kayıp koruması; ağırlıklı ortalama `np.average(pvmean, weights=W_FSTUWT)`; nokta-tahmin yayımlanmış OECD ortalamalarıyla <0,5 puan örtüşüyor (mean lineer olduğundan öğrenci-PV-ortalaması ağırlıklandırması OECD'nin PV-başı yöntemine eşdeğer). OLS + leave-one-out (`polyval(b[::-1], core)`) doğru; önbellek/merge_loss mantığı doğru; temp temizliği `finally` içinde. İşlevsel kusur yok.
2. **Küçük belge tutarsızlığı (denetlenen betikte DEĞİL):** `analysis/README.md` satır 27 ağır adımları "06/07/08/12b/13" diye sayıyor ama `run_all.py` HEAVY_STEPS listesi adım **15**'i de içeriyor; prose numaralandırması 15'i atlıyor. README tablo satırı 15 ve run_all.py girdisi 15 doğru (betik + çıktı yolu mevcut).
3. **Kozmetik:** summary JSON'daki `focus_asterisk_2015` TUR/HUN için JSON null yerine `"nan"` string'i (str(np.nan)) tutuyor; rapor bunu doğru şekilde "2015 yıldızı yok" olarak okuyor. Sonuca etkisi yok.
4. **Not (kusur değil):** SUBNATIONAL listesi CPS sav'ında bulunmayan "QAR"ı içeriyor (zararsız); QCH (B-S-J-G Çin, bölgesel) çekirdek puanı olmadığından regresyondan çıkmadan önce "50 ulusal sistem" içinde sayılıyor — "ulusal" ifadesi gevşek ama n=47 regresyon kümesi doğru.

### Tek uyuşmazlık (küçük)
§10 tablo satırı ve §5c "Okuma" paragrafı Türkiye SD'sini "−1,2…−1,4 SD" / "RMSE'nin 1,2–1,4 katı" olarak veriyor; oysa OECD-doğrusal spesifikasyonunun `residual_in_sd` değeri −1,00 (1,2'nin altında). Dört spesin gerçek min–maks aralığı 1,00–1,36. §5c tablosu −1,00'i açıkça gösterdiği için okuyucu tam tabloyu görüyor; yalnızca özet aralık alt uçta biraz dar. Kozmetik; olgusal başlık iddiasını (Türkiye artığı ≈ −13, 5/47, Macaristan'a benzer, 2015'te zayıf/2025'te güçlü) değiştirmiyor.

**Okuma:** §5c'nin başlık iddiası — Türkiye'nin 2015 CPS koşullu artığının ≈ −13 puan (≈ −1,2…−1,4 SD, 5/47), Macaristan'la benzer büyüklükte, yani 2015'te yalnızca orta düzeyde şişme sinyali — birincil kaynaklarla doğrulandı: mikroveri ortalamaları yayımlanmış OECD değerleriyle örtüşüyor, tüm regresyon çıktıları parquet'ten ve betiğin yeniden çalıştırılmasından birebir üretiliyor. Hiçbir proje dosyası değiştirilmedi (çıktıların mtime'ı korundu); çıkarılan .sav silindi.
