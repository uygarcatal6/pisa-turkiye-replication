# TASK C — Türkiye PISA örnekleminin okul-türü bileşimi (kompozisyon kanalı)

**Betik:** `analysis/08_composition.py` — tam yeniden üretilebilir.
**Üretilen dosyalar (`data/derived/`):**
`turkiye_school_type_composition.csv`, `turkiye_composition_drift.csv`,
`meb_reported_composition.csv`, bu README.

Hiçbir sayı ezberden değildir: her değer bir kaynak dosyadan okunur ve her çıktı
satırı köken sütunları (source_file + değişken / sayfa) taşır. SPSS öğrenci
dosyaları (döngü başına 1,5–2,2 GB) döngü döngü açılır, yalnızca gereken sütunlar
okunur (`usecols`) ve bir sonraki döngüden önce silinir; tepe bellek ~4 GB altında.

---

## 1. Kullanılan değişkenler ve tabaka çözümlemesi

| Amaç | Değişken | Dosya |
|---|---|---|
| Okul türü (Türkiye) | **STRATUM** (değer etiketi metni) | okul QQQ SPSS |
| Ağırlıklı öğrenci | **W_FSTUWT** (nihai öğrenci ağırlığı) + STRATUM | öğrenci QQQ SPSS |
| Örneklenen okul sayısı | okul dosyasında STRATUM satır sayısı | okul QQQ SPSS |
| Kamu/özel (ikincil) | **SC013Q01TA**, **SCHLTYPE** | okul QQQ SPSS |
| Okul–öğrenci eşleşmesi | **CNTSCHID** | her iki dosya |

Türkiye'de okul türünü **STRATUM** taşır (SUBNATIO'da TUR etiketi yok). Tabaka
etiketleri İngilizce PUF metninden şu Türkçe kategorilere eşlenir
(`classify()` fonksiyonu):

- `anadolu` = Anatolian High School → **Anadolu lisesi**
- `meslek` = Vocational and Technical Anatolian High School → **Mesleki ve teknik**
- `imam_hatip` = (Anatolian) Imam and Preacher High School → **Anadolu imam hatip**
- `fen` = Science High School → **Fen lisesi**
- `sosyal` = Social Sciences High School → **Sosyal bilimler lisesi**
- `cok_programli` = Multi-Programme Anatolian High School → **Çok programlı** (yalnız 2018)
- `spor_guzel` = Anatolian Sport / Fine Arts High School → **Spor/güzel sanatlar**
- `ozel_genel` / `ozel_meslek` = Private General / Vocational High School → **Özel** (yalnız 2025)
- `ortaokul` = Lower-Secondary School / (2015) BASIC EDUCATION → **Ortaokul (temel eğitim)**
- **2015 kaba tabakalar:** GENERAL SECONDARY → `genel_ortaogretim_2015`;
  VOCATIONAL AND TECHNICAL SECONDARY → `meslek_2015`.

---

## 2. Türkiye okul-türü bileşimi (ağırlıklı öğrenci payı)

| Kategori | 2015 | 2018 | 2022 | 2025 |
|---|---:|---:|---:|---:|
| Anadolu lisesi | — | 46,0% | 57,5% | 45,6% |
| Mesleki ve teknik | — | 31,5% | 24,3% | 27,1% |
| Anadolu imam hatip | — | 12,7% | 10,2% | 9,5% |
| Fen lisesi | — | 4,0% | 5,6% | 4,5% |
| Sosyal bilimler | — | 1,4% | 0,9% | 1,1% |
| Çok programlı | — | 3,3% | — | — |
| Spor/güzel sanatlar | — | 0,5% | 1,2% | 1,2% |
| Özel genel lise | — | — | — | 7,9% |
| Özel mesleki lise | — | — | — | 3,2% |
| Ortaokul (temel eğitim) | 3,2% | 0,5% | 0,2% | 0,1% |
| **2015 kaba:** Genel ortaöğretim | 55,4% | | | |
| **2015 kaba:** Mesleki ve teknik | 41,4% | | | |

*Paylar `turkiye_school_type_composition.csv` içinde `share` = ağırlıklı öğrenci
payıdır; `n_schools` = örneklenen okul sayısı. Kamu/özel (SC013) ve sahiplik
(SCHLTYPE) satırları da aynı dosyada ayrı `variable` değerleriyle yer alır
(kamu payı: 2015 %94,8 → 2018 %87,9 → 2022 %86,7 → 2025 %88,5).*

## 3. Bileşim değişimi (2015 → 2025) — >5 puan hareket bayrağı

`turkiye_composition_drift.csv`. Fine kategoriler yalnız 2018→2025 karşılaştırılır.
Aralık (max−min, 2018–2025) > 5 puan olanlar **YES**:

- **Anadolu lisesi — YES** (aralık 11,9 puan): 46,0% → **57,5%** (2022) → 45,6%.
  Net 2018→2025 ≈ 0; hareket tümüyle 2022'deki sıçramadan.
- **Mesleki ve teknik — YES** (aralık 7,1 puan): 31,5% → 24,3% (2022) → 27,1%.
- İmam hatip: 12,7% → 10,2% → 9,5% (istikrarlı düşüş, −3,2 puan; 5 puan altı).
- Ortaokul: 2015 %3,2 → 2018 %0,5 → 2022 %0,2 → 2025 %0,1 (neredeyse sıfırlandı).
- Özel liseler (`ozel_genel`+`ozel_meslek`) yalnız 2025'te ayrı tabaka (%11,1);
  bayrak hesaplanamaz (bkz. §5).

## 4. MEB'in bildirdiği bileşimle karşılaştırma

`meb_reported_composition.csv` — MEB ulusal raporlarından pdftotext ile alıntılı.
ERG'nin bildirdiği 2018 rakamları aslında MEB **PISA 2018 Ön Raporu** (s.24)
rakamlarıdır ve mikroveri bunları yeniden üretir:

| Döngü | MEB | Mikroveri | fark (puan) |
|---|---|---|---|
| 2018 Anadolu | 43,7% | 46,0% | −2,3 |
| 2018 Mesleki-teknik | 31,1% | 31,5% | −0,4 |
| 2018 İmam hatip | 13,7% | 12,7% | +1,0 |
| 2018 Fen+sosyal+ç.prog.+g.sanat | 11,2% | 9,3% | +1,9 |
| 2018 Ortaokul | 0,3% | 0,5% | −0,2 |
| **2022** Anadolu / Mesleki / İmam / Fen / Sosyal / G.sanat / Ortaokul | 56,0 / 23,0 / 10,2 / 5,6 / 0,9 / 1,2 / 0,2 | 57,5 / 24,3 / 10,2 / 5,6 / 0,9 / 1,2 / 0,2 | ≤1,5; çoğu **~0,0** |
| 2025 Anadolu | 46,6% | 45,6% | +1,0 |
| 2025 Mesleki-teknik | 32,8% | 27,1% | **+5,7** |
| 2025 İmam hatip | 9,5% | 9,5% | 0,0 |
| 2025 MIX (fen+sosyal+ç.prog.+g.sanat/spor) | 11,0% | 6,7% | +4,3 |
| 2025 Ortaokul | 0,1% | 0,1% | 0,0 |

**Eşleşen:** 2018 (≤2,3 puan) ve özellikle **2022 (neredeyse tam; imam/fen/sosyal/
güzel sanat/ortaokul birebir)**. **Eşleşmeyen:** 2025'te mesleki-teknik (+5,7) ve
MIX (+4,3). Nedeni §5.

## 5. Uyarılar (caveats)

1. **Tabaka etiketleri döngüler arası değişir.** 2015 tabakaları yalnız
   *bölge × program* (temel eğitim / genel ortaöğretim / mesleki-teknik) ayırır;
   Anadolu / imam hatip / fen ayrı **değildir**. Bu yüzden 2015 fine kategorilerle
   karşılaştırılamaz. Ancak kaba eşleme tutarlıdır: 2015 "genel ortaöğretim"
   %55,4 ≈ 2018 akademik demeti (Anadolu+fen+sosyal+ç.prog.+spor = %55,2);
   2015 "mesleki ve teknik" %41,4 ≈ 2018 mesleki+imam hatip (%44,2) — yani
   **2015'te imam hatip büyük olasılıkla mesleki-teknik tabakası içine katlanmıştır.**
2. **2025 özel-okul tabakaları.** 2025 PUF'unda "Private General/Vocational High
   School" ayrı tabakalardır (ağırlıklı %7,9 + %3,2 = %11,1). MEB raporu özel
   okulları ayrı göstermez; programlarına göre Anadolu/mesleki/MIX içine yerleştirir.
   2025'teki mesleki-teknik (+5,7) ve MIX (+4,3) farkının kaynağı budur: PUF'un
   özel-tabaka şeması MEB'in okul-türü kategorilerini keser. 2018/2022'de böyle bir
   tabaka olmadığı için eşleşme neredeyse tamdır.
3. **Ağırlık seçimi.** Paylar nihai öğrenci ağırlığı W_FSTUWT ile hesaplanır
   (ağırlıklı öğrenci payı). Okul sayısı payları (`n_schools`) biraz farklıdır
   (ör. 2018 Anadolu: okulda %41,9, ağırlıklı %46,0).
4. **Açık öğretim / MESEM.** Bir medya iddiasına göre 2025'te açık öğretim ve
   MESEM örnekleme çerçevesi dışındadır; bu **doğrulanmamıştır** ve mikroveriden
   tabaka etiketleriyle ayrıca teyit edilemez (bu kategoriler için ayrı tabaka yok).
5. **MEB 2015 raporu** okul türüne göre örneklem dağılımı **vermez** (not found).

## 6. Sonuç (kompozisyon kanalı)

Türkiye PISA örnekleminde ağırlıklı öğrenci bileşimi Anadolu liseleri (~%46–58)
ve mesleki-teknik (~%24–32) egemenliğindedir; imam hatip **istikrarlı biçimde
gerilemiştir** (%12,7 → %10,2 → %9,5) ve ortaokul (15 yaş temel eğitim) payı
neredeyse **sıfırlanmıştır** (%3,2 → %0,1). Fine kategorilerde 2018→2025 net kayma
küçüktür; en büyük hareket 2022'deki geçici Anadolu sıçraması (+11,5 puan aralık) ve
buna eşlik eden mesleki-teknik düşüşüdür. Mikroveri, MEB'in bildirdiği bileşimi
2018 ve özellikle 2022'de yeniden üretir; 2025'teki sapma yöntemseldir (özel-okul
tabakalarının ayrılması), gerçek bir örneklem kaymasını değil.
