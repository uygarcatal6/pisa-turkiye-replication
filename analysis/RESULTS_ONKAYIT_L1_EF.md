# Ön-kayıt ve sonuç notları: L1 ve EF (7 Eki 2026)

Bu dosya, bu depoda yer almayan çalışma notunun (`RESULTS_EMPIRICAL_FIXES.md`) §0.15 ve §0.16 bölümlerinin anonimleştirilmiş özüdür. Betik 60 ve 62'nin başlıkları bu bölümlere gönderme yapar. Ön-kayıt seçimleri değiştirilmedi; yalnız iç dosya yolları, makaleden alıntılar ve bölüm adları, sohbet ve iç okuma izleri çıkarıldı ya da nötr ifadeyle değiştirildi.

### 0.15 L1 — 2015 ve 2025 düzey artıkları için ilişkili bootstrap aralığı (betik 60) · eklenme: 7 Eki 2026, CC (Opus 5.5), yazar

Zamanlama notu: **sonradan** eklenen bir belirsizlik kalemidir. Tablo 1'in nokta kestirimleri ve sıraları görüldükten sonra, betik 60 yazılmadan ve koşulmadan önce yazıldı. Nokta kestirimleri ve sıralar değişmez; yalnız aralık eklenir.

| Öğe | Seçim |
| :--- | :--- |
| Yöntem | Betik 31'in 2003 bloğu aynen: her çekilişte her sistemin yenilikçi alan ortalaması kendi SE'siyle, çekirdek ortalaması kendi SE'siyle ve yenilikçi alanla **ilişkili** çekilir (`_pisa_puf.combine_rho`; örnekleme ve atama bileşenleri), doğru yeniden uydurulur, artık yeniden hesaplanır |
| Nokta kestirimleri | Tablo 1'in kendi dosyaları: `data/derived/mechanisms/placebo_conditional_2015cps.csv` (2015) ve `placebo_conditional_2025.csv` (2025); dört şartname (all/oecd × linear/quadratic) |
| SE ve korelasyon | `data/derived/cache/e1_boot_inputs_{2015,2025}.csv` (betik 43'ün mikroveri önbelleği: BRR Fay 0,5, W_FSTURWT1–80, Rubin M = 10); çekirdek SE'si betik 31 ile aynı tanım |
| Çekiliş | B = 2000, tohum 20261007 |
| Rapor | Türkiye'nin artığı için %2,5–%97,5 yüzdelik aralığı ve bootstrap SE; sıranın (alttan) %2,5–%97,5 aralığı; dört şartnamede; birincil hücre all · linear (Tablo 1) |
| Kapılar | (i) Fit'teki her sistemin önbellekte satırı olmalı (eksikse DUR); (ii) önbellekteki ortalamalarla fit'in ortalamaları arasındaki mutlak fark ≤ 0,01 (2025'te BEL için betik 43'teki belgelenmiş 0,02 istisnası); (iii) nokta artıkları dosyadakilerle 1e-6 içinde yeniden üretilir |
| Makale | Tablo 1'in "95% interval" satırı (2015, 2025) ve notları; sonradan eklendiği notlarda yazılır |
| Çıktı | `data/derived/empirical_fixes/l1_level_intervals.csv`, `l1_level_intervals_summary.json` |

**Sapma (7 Eki 2026, ilk koşu kapı (i)'de durduktan sonra, ikinci koşudan önce):**

- 2025 fit'indeki 84 sistemden Kıbrıs (CYP) 2025 kamu mikroverisinde yok, bu yüzden betik 43'ün önbelleğinde de yok. Önbellekte fit dışı UZB var.
- CYP için SE'ler yayımlanmış değerlerden alınır (`data/derived/analysis_panel.csv`, OECD annex `mrq53f.xlsx`): yenilikçi alan `cps2025_se`; çekirdek, betik 31 tanımıyla üç alanın SE ortalaması.
- Mikroveri olmadığı için CYP'nin korelasyonu öteki 83 sistemin birleşik ρ'sunun medyanıdır. Bileşen SE'leri örnekleme payına yazılır, atama payı 0.
- Duyarlılık: CYP'nin ρ'su 0 ve 0,95 alınarak koşulur; Türkiye aralığındaki değişim raporlanır.
- Başka bir değişiklik yok.

**Genişletme (7 Eki 2026, 2015/2025 sonuçları görüldükten sonra, 2003/2012 kısmı yazılmadan önce):**

- Gerekçe: 2015 ve 2025'te sistemlerin çoğunun düzey aralığı sıfırı dışlıyor (2015'te 47'de 38, 2025'te 84'te 69). Mevcut 2003 çıktısında da durum aynı (36'da 33). Yani "aralık sıfırı dışlıyor" ölçütü ayırt edici değil; ayırt edici olan sıra.
- Kapsam: betik 60, 2003 ve 2012 için de **sıra** aralığı üretir. Yöntem aynı; aynı B = 2000; tohum 20261007 (2003 ve 2012 için ayrı akış: tohum + yıl).
- Girdiler: betik 31 ve 33'ün PUF blokları aynen (`brr_pv_stat`, `brr_pv_corr`, çekirdek SE'si bileşen ortalaması; önbellekten).
- Nokta kestirimleri: `placebo_conditional_2003ps_puf.csv` ve `placebo_conditional_2012ps_puf.csv` (çekirdek mat/oku/fen).
- Kapılar: girdi ortalamaları csv'yle 1e-6 içinde; nokta artıkları 1e-6 içinde.
- Makale: Tablo 1'deki 2003 ve 2012 artık aralıkları betik 31 ve 33'ten kalır; betik 60'ın artık aralıkları yalnız yeniden üretim kontrolüdür (Monte Carlo farkı beklenir). Tabloya yeni satır olarak her döngü için sıranın %95 aralığı eklenir.

**Sonuç (7 Eki 2026; `data/derived/empirical_fixes/l1_level_intervals_summary.json`; Türkiye, all · linear):**

| Döngü | Artık | %95 aralık | Sıra (alttan) | Sıranın %95 aralığı | Aralığı sıfırı dışlayan sistem |
| :--- | ---: | :--- | :--- | :--- | :--- |
| 2003 | −16,4 | −19,9 ile −13,1 (betik 31; betik 60: −20,0 ile −12,9) | 1 / 36 | 1–4 (dört şartname 1–6) | 33 / 36 |
| 2012 | −6,9 | −11,0 ile −2,9 (betik 33) | 13 / 41 | 10–17 | 37 / 41 |
| 2015 | −12,9 | −16,0 ile −10,0 | 5 / 47 | 2–12 | 38 / 47 |
| 2025 | −31,8 | −33,8 ile −29,7 | 5 / 84 | 5–6 (OECD 1 / 38, çekilişlerin ≥ %97,5'i) | 69 / 84 |

- CYP ρ duyarlılığı (0 ve 0,95) Türkiye'nin 2025 aralıklarını değiştirmedi.
- T1 (`wf_…`): bağımsız yeniden uygulama Monte Carlo farkı içinde aynı. Düşük önemli bulgu: sıra sınırları `int()` ile kesiliyor (678 satırın 15'inde kesirli); Türkiye'nin sınırları tam sayı.
- Makaleye işlendi.

### 0.16 EF — hızlı tahmin farkının puan karşılığı (betik 62) · eklenme: 7 Eki 2026, CC (Opus 5.5), yazar

Zamanlama notu: **sonradan** eklenen bir çeviri. H7 sonuçları (Türkiye'nin CMPS − çekirdek hızlı tahmin farkı OECD ortalamasından 1,53 yüzde puanı geniş) ve 2025 artıkları görüldükten sonra, ama aşağıdaki ilişki hiç hesaplanmadan, betik 62 yazılmadan önce yazıldı. Makaledeki bir çekinceye yanıt.

| Öğe | Seçim |
| :--- | :--- |
| Soru | Ülkeler arasında, CMPS ile çekirdek arasındaki hızlı tahmin farkı 2025 artığıyla ne kadar ilişkili; Türkiye'nin OECD ortalamasından fazla farkı kaç puana karşılık gelir? |
| Veri | `outputs/tables/pisa2025/h7_country.csv` (38 OECD üyesi; `diff_share` = CMPS payı − çekirdek payı); `data/derived/mechanisms/placebo_conditional_2025.csv` (OECD kapsamı) |
| Birincil | Eşik NT15 (makaledeki tanım); OECD · doğrusal artık; OLS r_c = α + γ·g_c (g yüzde puanı); HC3 SE; **Türkiye dışarıda** uydurulur (37 sistem), Türkiye'nin payı = γ̂ × (g_TUR − ḡ₃₇), %95 aralık γ̂'nın HC3 aralığından |
| İkincil (hepsi raporlanır) | Türkiye dahil 38 sistem; NT10, NT20, FIX5S eşikleri; OECD · karesel artık; iki regresörlü model (çekirdek payı ve CMPS payı ayrı) |
| Yorum kuralı | γ̂'nın HC3 aralığı sıfırı içeriyorsa "ülkeler arası ilişki Türkiye'nin artığının ancak X puanını açıklayabilir (aralığın üst ucu)" diye yazılır; içermiyorsa nokta ve aralık. Ekolojik bir ilişkidir; öğrenci düzeyinde yeniden ölçekleme değildir |
| Kapılar | 38 sistemin hepsi iki dosyada eşleşmeli; Türkiye'nin g'si ve OECD ortalaması H7 özetindeki `tur_diff` ve `oecd_avg_diff` ile 1e-9 içinde |
| Makale | İlgili bölümün son cümlesinin yerine; sonuç cümlesindeki çekince sayıya göre güncellenir |
| Çıktı | `data/derived/empirical_fixes/ef_effort_translation.csv`, `ef_effort_translation_summary.json` |

**Sapma (kapı; 7 Eki 2026, koşudan sonra, T1 `wf_…` bulgusu F1(d)):**

- OECD ortalaması kapısı tutmadı. Kapı, 38 sistemin `diff_share` ortalamasının H7 özetindeki `oecd_avg_diff` ile 1e-9 içinde olmasını istiyordu. Mutlak farklar: NT15 2,1e-7; NT10 3,9e-7; NT20 7,9e-8; FIX5S 1,3e-7.
- Neden yuvarlama: `outputs/tables/pisa2025/h7_results.csv` değerleri 6 ondalıkla saklıyor (ör. 0,0032057895 yerine 0,003206). `h7_country.csv`'deki `diff_share` de 6 ondalıklı; `cmps_share − core_share` ile farkı 1e-6'ya kadar çıkıyor.
- Sonuca etkisi yok. ḡ₃₇, H7 ortalamasından değil `h7_country.csv`'den hesaplanır. Betik 62 bu kapıda durmaz; farkı yalnız `ef_effort_translation_summary.json`'a yazar. Durduran tek kapı Türkiye'nin farkındadır; iki dosya da 6 ondalık sakladığı için o kapı tutar.
- Kapı, saklama duyarlığında (≤ 1e-6) sağlanmış sayılır; belgelenmiş sapmadır. Betik değişmedi, yeniden koşulmadı.

**Sonuç (7 Eki 2026; `data/derived/empirical_fixes/ef_effort_translation.csv`, `ef_effort_translation_summary.json`):**

- **Birincil hücre** (NT15; OECD · doğrusal artık; Türkiye dışarıda, n = 37):
  - Eğim: γ̂ = −3,56 (HC3 SE 2,27; %95 −8,02 ile 0,90), R² 0,098.
  - Fark (yüzde puanı): Türkiye 1,85; öteki 37 sistemin ortalaması 0,28; Türkiye'nin fazlası 1,57.
  - Türkiye'nin artığı −33,49.
  - Türkiye'nin payı −5,58 puan (%95 −12,57 ile +1,41), artığın %16,7'si.
  - İki regresörlü modelde (çekirdek ve CMPS payları ayrı) pay −5,30.
- **Yorum kuralı:** γ̂'nın HC3 aralığı sıfırı içeriyor. Bu yüzden üst sınır raporlanır (yaklaşık 13 puan; nokta kestirimi yaklaşık 6). İlişki ekolojiktir, öğrenci düzeyinde yeniden ölçekleme değildir.
- **Bütün hücreler** (Türkiye'nin payı, puan; parantezde %95 aralığı; negatif değer artığı küçültür):

| Eşik | Artık | Türkiye dışarıda (37) | Türkiye dahil (38) |
| :--- | :--- | :--- | :--- |
| NT15 (birincil) | doğrusal | −5,58 (−12,57 ile 1,41) | −8,30 (−16,73 ile 0,12) |
| NT15 | karesel | −5,23 (−12,21 ile 1,76) | −7,93 (−16,32 ile 0,46) |
| NT10 | doğrusal | −4,82 (−7,61 ile −2,03) | −5,95 (−9,51 ile −2,39) |
| NT10 | karesel | −4,44 (−7,38 ile −1,50) | −5,56 (−9,22 ile −1,90) |
| NT20 | doğrusal | −5,37 (−12,56 ile 1,82) | −8,26 (−17,26 ile 0,73) |
| NT20 | karesel | −5,13 (−12,25 ile 1,98) | −8,00 (−16,86 ile 0,87) |
| FIX5S | doğrusal | −1,63 (−4,34 ile 1,07) | −2,83 (−6,60 ile 0,94) |
| FIX5S | karesel | −1,41 (−4,09 ile 1,28) | −2,59 (−6,30 ile 1,12) |

- **Hücreler arası aralık:** Türkiye dışarıda 1,4–5,6 puan; dahil 2,6–8,3 puan. NT10'da γ̂'nın aralığı sıfırı dışlıyor (iki örneklemde ve iki şartnamede). Öteki eşiklerde dışlamıyor.
- **Makalede:** ilgili cümleler bu kurala göre yazıldı.
- **T1:**
  - `wf_…`: 16 hücre bağımsız statsmodels HC3 ile 8e-14 içinde yeniden üretildi. Bu turun bulguları makale cümlelerine işlendi.
  - `wf_…`: çaba cümlesi (§5) ve sonuç cümlesi bu kurala uyuyor; bütün sayılar CSV ile tutuyor (taze bağlam claim-verifier). Düşük önemli not: aynı paragrafta 1,53 (Türkiye dahil OECD ortalamasına göre, H7) ile 1,6 (öteki 37 sistemin ortalamasına göre) yan yana; ikisi de doğru, cümle başvuru kümesini adlandırıyor.
