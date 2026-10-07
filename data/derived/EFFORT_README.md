# EFFORT_README — Öğrenci çaba göstergeleri (PISA mikroverisi)

**Üretim betiği:** `analysis/07_microdata_effort.py`
**Çıktı:** `data/derived/effort_microdata.csv` (her ülke × döngü için ağırlıklı + ağırlıksız iki satır)
**Ara önbellek:** `data/derived/cache/effort_students_<yıl>.parquet`, `effort_itemmedian_<yıl>.csv`, `effort_vars_<yıl>.txt`
**Tarih:** 2026-09-15 · Model: Opus 4.8 (mekanik/araç-temelli çıkarım; her sayı dosyadan okundu)

Bu not, "score-inflation" hipotezinin **çekirdek mekanizma testidir**: Türkiye öğrencilerinin
sınavdaki çabası (hız, boş bırakma, sona ulaşamama) 2015 sonrası donör ülkelere göre
**bozuldu mu?** Hiçbir değer ezberden gelmez; bulunamayan her göstergeye "not found" yazıldı.

---

## 1. Hangi dosya, hangi değişkenler

> **Kritik olgu (dosyalardan doğrulandı):** Bilişsel test **madde yanıt süreleri** ve
> **puanlanmış yanıtlar** COG dosyalarının içindedir. Ayrı `*_TIM / *_QTM / *_TT` dosyaları
> yalnızca **anket maddesi** süreleridir (ST/IC/EC/WB `_TT`), bilişsel test süresi DEĞİL —
> başlıklarından doğrulandı. Bu yüzden görevdeki dosya tanımının aksine, süre + puan **COG**'dan alındı.

| Döngü | COG dosyası (kaynak) | Süre değişkeni | Puan değişkeni | Ağırlık kaynağı |
|---|---|---|---|---|
| 2015 | `CY6_MS_CMB_STU_COG.sav` | etiket~"Timing", sonek `…Q01T` (n=367) | etiket~"Scored Response", `…Q01S` (n=380) | `CY6_MS_CMB_STU_QQQ.sav` |
| 2018 | `CY07_MSU_STU_COG.sav` | `…Q01T` (n=581) | `…Q01S` (n=734) | `CY07_MSU_STU_QQQ.sav` |
| 2022 | `CY08MSP_STU_COG.SAV` | `…Q01TT` (n=605) | `…Q01S` (n=785) | `CY08MSP_STU_QQQ.SAV` |
| 2025 | `CY09_MS_COG_20260806.sav` | **YOK (n=0)** | `…Q01S` (n=704) | `CY09_MS_STU_PUF.sav` |

- Süre/puan sütunları **etikete göre** seçildi (sonek adlandırması döngüler arası değişiyor:
  2015/2018 `T`, 2022 `TT`); böylece adlandırma farkına karşı sağlam.
- **Ağırlık** `W_FSTUWT` COG dosyalarında YOKTUR; `CNTSTUID` üzerinden anket (QQQ) / öğrenci
  (2025 STU) dosyasından birleştirildi. Betikte her satırda `source_file` sütunu bunu belgeler.
- Tam değişken listeleri ve kod etiketleri: `data/derived/cache/effort_vars_<yıl>.txt`.

### Kod şeması (değer etiketlerinden okundu)
- **Puan (2015/2018/2022, sayısal):** 0/1/2 = kredi · 5 = Valid Skip · 6 = Not Reached ·
  7 = Not Applicable · 8 = Invalid · 9 = No Response (boş bırakma/omit).
- **Puan (2025, METİN kodları):** '0'/'1'/'2' = kredi · '7' = Not Applicable · **'r' = Not Reached** ·
  't' = Technical Issue. → 2025'te **omit (No Response) kodu YOK**: boş bırakma oranı **ayrıştırılamaz**.
- **Süre (ms):** geçerli değer `0 < t < 99999990`. Özel kodlar 99999995–99999999
  (Valid Skip / Not Reached / N/A / Invalid / No Response). Birim **milisaniye** (Türkiye
  madde-medyanı ~60–80 s ile doğrulandı); raporda saniyeye çevrildi.
- `pyreadstat` notu: `row_limit=0` = **tüm satırları oku** (sıfır değil); metaveri için
  `metadataonly=True`, 6/9/'r' kodlarını kurtarmak için `user_missing=True` şart.

---

## 2. Göstergeler ve eşikler

Öğrenci başına hesaplanıp ülke × döngü düzeyinde toplandı; **ağırlıklı** (W_FSTUWT) ve
**ağırlıksız** iki satır. Oranlar madde-yanıtı düzeyinde toplanır:
`pay = Σ_s w_s·n_s / Σ_s w_s·payda_s`. Ağırlıklı medyan için ağırlıklı kuantil kullanıldı.

- **Toplam test süresi** (median/mean, s) = öğrencinin geçerli madde sürelerinin toplamı.
- **Madde başına süre** (median, s) = öğrenci-içi geçerli sürelerin medyanının ülke medyanı.
- **Hızlı yanıt payı (rapid-response):** geçerli süreli madde-yanıtları içinde eşiğin altındakiler.
  - **Sabit 5 sn kuralı:** t < 5000 ms.
  - **Normatif NT15 kuralı (Michaelides & Ivanova 2022):** eşik_i = **0,15 × madde_i medyanı**;
    madde medyanları, yüklenen **hedef ülke havuzu** üzerinden (döngü başına) hesaplandı (normatif proxy).
- **Boş bırakma (omission) oranı** = No Response(9) / ulaşılan maddeler{0,1,2,9}. (2025: not found.)
- **Sona ulaşamama (not-reached) oranı** = NotReached(6; 2025:'r') / uygulanan maddeler{0,1,2,9,6}.
  PISA'nın 6/'r' kodu zaten "son yanıttan sonraki maddeler" tanımını taşır (konumsal tanım gömülü).
- **Doğru yüzdesi** = {1,2} / {0,1,2} (kredi alan maddeler içinde).
- **Test-sonu düşüşü (ilk vs son üçte bir):** madde **uygulama sırası/konumu** kamuya açık
  dosyalarda **yer almadığından hesaplanamadı** → tüm döngüler için **"not found (item position unavailable)"**.
  (Sütun sırası uygulama sırası değildir; proxy olarak kullanılmadı.)

---

## 3. Uyarılar / karşılaştırılabilirlik (ÖNEMLİ)

1. **Ana alan (major domain) her döngüde değişir:** 2015 Fen, 2018 Okuma, 2022 Matematik,
   2025 Fen. Madde kümesi ve zorluk döngüler arası farklı → **mutlak** değerler (özellikle
   `pct_correct`, `median_total_time`) döngüler arası **doğrudan karşılaştırılamaz**. Doğru
   test **döngü-içi Türkiye − donör farkıdır** (aynı döngüde herkes aynı maddeleri alır).
2. **Sabit 5 sn kuralı güvenilmezdir:** 2018 (Okuma) **okuma akıcılığı** maddelerini içerir;
   bunlar tasarım gereği 1–3 sn'de yanıtlanır ve <5 sn payını yapay olarak şişirir
   (2018'de Türkiye %24,6 AMA Japonya da %21 → ülkeye özgü değil, yapısal). **NT15 tercih edilir**
   (eşik her maddenin kendi medyanına göre ölçeklenir, hızlı-tasarım maddelerden etkilenmez).
3. **NT15 kalibrasyonu (2015 sanity):** havuz NT15 = %4,7 (Michaelides ~%3 komşuluğunda → PASS);
   havuz sabit-5sn = %2,5 (literatür <%1; büyüklük mertebesi tutuyor ama üstünde → FLAG,
   yukarıdaki madde-tipi/"total timing" nedeniyle).
4. **Uygulama modu:** 2015'te bazı ülkeler kağıt-kalem (ör. **Gürcistan 2015 = kağıt** → süre yok,
   NaN). Türkiye tüm döngülerde bilgisayar tabanlı.
5. **2025 sınırları:** COG'da bilişsel süre YOK ve omit kodu YOK → 2025 için süre/hızlı-yanıt/
   boş-bırakma **not found**. Yalnızca not-reached('r'), doğru yüzdesi, öğrenci sayısı hesaplandı.
   (Bilişsel süreler muhtemelen `CY09_MS_COG_PROCESS_PUF.zip` süreç dosyasında; görev kapsamı dışıydı.)
6. **Süre tanımı:** değişken "Total Timing / Timing of last visit" = maddeye tüm ziyaretlerin
   toplam süresi (tek-ziyaret ilk-yanıt değil); RG literatürünün bir kısmıyla tam örtüşmez.
7. **Rapid-response paydası:** geçerli süreli tüm ulaşılan maddeler (yanıtlanmamış ama <eşik
   olanlar dahil); "yalnızca yanıtlanmış madde" tanımı biraz daha düşük değer verirdi.
8. **NT15 normatif havuzu:** uluslararası tam örneklem yerine yüklenen hedef ülkeler; eşikler
   tüm ülkelere aynı uygulandığından ülkeler-arası karşılaştırma tutarlıdır.

---

## 4. Yeniden üretim

```
cd <depo-kökü>
python analysis/07_microdata_effort.py            # tüm döngüler (önbellek varsa hızlı)
python analysis/07_microdata_effort.py 2022       # tek döngü
```
Ağır `.sav` dosyaları proje DIŞINA (`%TEMP%/pisa_microdata_work`) açılır ve her
döngüden sonra **silinir**; per-döngü sonuçlar `cache/…parquet` içinde tutulur
(silinirse yeniden hesaplanır). Bellek < ~4 GB (sütun-seçimli + parça-parça okuma, float32).

## 5. Bulgu (özet)
Türkiye'nin çaba göstergeleri 2015 sonrası donörlere göre **kötüleşmedi**: 2022'de Türkiye
donörlerden daha uzun süre harcar, daha az boş bırakır, daha az "sona ulaşamama" gösterir ve
hızlı-yanıt (NT15) donör ortalamasına yakınsar. Tek yükseklik, kısmen okuma-akıcılığı ağırlıklı
2018 döngüsündeki geçici hızlı-yanıt/not-reached artışıdır. Ayrıntılı tablo: aşağıdaki döndürülen özet.
