# Faz 5 — Kırılma-yılı duyarlılığı: 2015 çukuru tabanı belirlediğinde ne değişir?

Tarih: 2026-09-20. Yazan: Claude Fable 5.1 (kod + metin). Betik: `analysis/21_breakyear_sensitivity.py` (16'nın SDiD/plasebo ve 17'nin Python SC fonksiyonlarını içe aktarır). Çıktılar: `data/derived/breakyear/breakyear_sensitivity.csv` (108 satır: 3 havuz × 3 alan × 3 varyant × 4 tahminci), `summary.json`, `breakyear_table.md` (manşet havuz), `analysis/figures/v4_sekil3_kirilma_yili.png`. Etiket: **[E21]**. Denetim: **bekliyor (Opus 4.8)**.

Bu test v4 §4.5'in kendi cümlesiyle "zorunlu"ydu: *"2015 anormal derin bir çukursa, ondan ölçülen yükselişin bir kısmı kazanım değil ortalamaya dönüştür."*

## 0. Sonuç — üç cümle

1. **2025 düzey açığı 2015'e bağlı değil.** Ön dönem 2003–2012'ye sabitlendiğinde 2015 sütunu ister sonrası dönemde kalsın (A) ister matristen atılsın (C), 2025 açığı aynıdır: SC **+50,4 / +34,1 / +48,8** (mat / oku / fen), SDiD **+35,7 / +38,3 / +31,2** ≈ **+35,8 / +37,8 / +30,9**, 2012-tabanlı basit DiD **+45,2 / +41,8 / +43,1**. Bu, "2015 sonrası hızlanma"nın 2025 gözlemi için çukurdan bağımsız olduğunu gösterir.
2. **2018–2025 ortalama etki tabana bağlıdır — matematik ve fende yaklaşık yarısı 2015 çukurudur.** SDiD 2015-tabanlı (B, Faz 4 manşeti) **+45,6 / +20,5 / +46,0**; 2015 dışarıda (C) **+24,0 / +20,2 / +16,6**. 2018 ve 2022 açıkları 2012'den ölçülünce matematik +18 / +18, okuma +15 / +8, fen +9 / +10 (SDiD C); 2015'ten ölçülünce +39 / +40, +14 / +9, +39 / +39 (SDiD B). Okuma etkilenmez çünkü SDiD orada 2015'e zaten sıfır zaman ağırlığı vermişti. **Manşet ortalama etki bundan sonra iki tabanla birlikte yazılmalıdır.**
3. **Sürekli-trend karşı-olgusalı tezin sınır durumudur.** 2003–2012 açığının doğrusal eğimi matematik ve fende pozitif ve büyük, okumada küçüktür (döngü başına matematik **+7,9**, okuma **+0,7**, fen **+12,1** puan; `pre_trend_slope_per_cycle` — kapsam genişlemesi dönemi). Bu eğim sonrasına uzatılıp çıkarılınca sonrası ortalaması matematik **+0,4** (p 1,00), okuma **+16,5** (p 0,33), fen **−17,3** (p 0,33) olur. Yani "Türkiye 2006'dan beri sapıyordu ve sapmaya devam etti" okuması matematik ve fende 2015 sonrası ek hızlanma bırakmaz. Bu karşı-olgusal, kapsam genişlemesinin 2015 sonrası durduğu (CI3 0,699 → 0,722; Faz 3 §0) bilgisiyle çelişir ve bu yüzden ana tahminci olamaz; ama hakemin ilk soracağı budur ve rapora sınır durumu olarak girer.

## 1. Manşet havuz (stabil OECD; N0 = 5 / 5 / 8)

Yıl bazlı açıklar (Türkiye − sentetik/karşılaştırma; puan). p = placebo-in-space sıra-p, sonrası ortalaması üzerinde; erişilebilir en küçük p = 1/(N0+1) = 0,17 / 0,17 / 0,11.

| Varyant | Tahminci | Alan | 2015 | 2018 | 2022 | 2025 | Sonrası ort. | p |
|---|---|---|---:|---:|---:|---:|---:|---:|
| A · ön 2003–12, sonrası 2015–25 | SC (arındırılmış) | mat | −8,7 | +30,2 | +32,8 | **+50,4** | +26,2 | 0,17 |
| | | oku | −28,7 | +19,8 | +4,9 | **+34,1** | +7,6 | 0,50 |
| | | fen | −20,8 | +31,3 | +21,4 | **+48,8** | +20,2 | 0,22 |
| | SDiD | mat | −20,5 | +18,3 | +17,9 | +35,7 | +12,8 | 0,17 |
| | | oku | −31,8 | +14,9 | +8,4 | +38,3 | +7,5 | 0,17 |
| | | fen | −37,8 | +9,6 | +10,3 | +31,2 | +3,3 | 0,56 |
| B · ön 2003–15, sonrası 2018–25 | SC (arındırılmış) | mat | – | +34,4 | +41,4 | +58,6 | +44,8 | 0,17 |
| | | oku | – | +28,0 | +13,7 | +43,0 | +28,2 | 0,17 |
| | | fen | – | +33,5 | +34,1 | +53,0 | +40,2 | 0,11 |
| | SDiD (= Faz 4 manşeti) | mat | – | +38,8 | +40,1 | +57,8 | **+45,6** | 0,17 |
| | | oku | – | +13,6 | +9,3 | +38,7 | **+20,5** | 0,17 |
| | | fen | – | +39,2 | +39,2 | +59,6 | **+46,0** | 0,11 |
| **C · 2015 dışarıda** (ön 2003–12, sonrası 2018–25) | SC (arındırılmış) | mat | – | +30,2 | +32,8 | **+50,4** | +37,8 | 0,17 |
| | | oku | – | +19,8 | +4,9 | **+34,1** | +19,6 | 0,17 |
| | | fen | – | +31,3 | +21,4 | **+48,8** | +33,9 | 0,11 |
| | SC, trend-düzeltmeli | mat | – | +2,5 | −5,4 | +4,3 | **+0,4** | 1,00 |
| | | oku | – | +17,5 | +1,7 | +30,2 | **+16,5** | 0,33 |
| | | fen | – | −5,1 | −31,1 | −15,8 | **−17,3** | 0,33 |
| | SDiD | mat | – | +18,3 | +18,0 | +35,8 | **+24,0** | 0,17 |
| | | oku | – | +15,0 | +7,9 | +37,8 | **+20,2** | 0,17 |
| | | fen | – | +9,4 | +9,6 | +30,9 | **+16,6** | 0,33 |
| | DiD, 2012 tabanı | mat | – | +11,3 | +25,9 | +45,2 | +27,5 | 0,17 |
| | | oku | – | +9,4 | +11,8 | +41,8 | +21,0 | 0,17 |
| | | fen | – | +12,8 | +23,1 | +43,1 | +26,3 | 0,22 |

Tam tablo (dört tahminci × üç varyant, üç havuz): `data/derived/breakyear/breakyear_table.md` ve `breakyear_sensitivity.csv`.

## 2. Ne değişir, ne değişmez

| Soru | Cevap | Kaynak hücre |
|---|---|---|
| 2025 açığı 2015 çukurundan mı ölçülüyor? | **Hayır.** Ön dönem 2012'de bitince 2015 içeride/dışarıda fark etmez: SC 2025 birebir aynı (A = C), SDiD 2025 farkı ≤ 0,5 puan. | `summary.json → delta_2015_in_vs_out` |
| 2018–2025 ortalama etki 2015 çukurundan mı? | **Kısmen, matematik ve fende yaklaşık yarısı.** SDiD τ: B +45,6 / +46,0 → C +24,0 / +16,6; okuma +20,5 → +20,2 (değişmez). | aynı |
| 2018 ve 2022 açıkları | 2012'den ölçülünce **küçük** (SDiD C: +18 / +18 mat, +15 / +8 oku, +9 / +10 fen); 2015'ten ölçülünce büyük (+39 / +40, +14 / +9, +39 / +39). Serinin yükü 2025 gözleminde. | tablo |
| Sürekli trend | Ön dönem eğimi uzatılınca mat +0,4, oku +16,5, fen −17,3. Eğim kapsam genişlemesi dönemine ait (döngü başına +7,9 / +0,7 / +12,1; okumada eğim küçük olduğu için düzeltme az). | `pre_trend_slope_per_cycle` |
| Havuz duyarlılığı | Stabil+belirsiz OECD ve tüm katılımcılarda aynı örüntü; fen, OECD kısıtı kalkınca A/C varyantlarında SC ile negatif (Faz 3'teki bilinen fen kararsızlığı). | CSV, `pool` sütunu |

## 3. v4 için dil kararı (öneri — karar yazarın)

- §4.2'deki SDiD manşeti (**+45,6 / +20,5 / +46,0**) tek başına yazılmaz; yanına 2015-dışarıda değeri (**+24,0 / +20,2 / +16,6**) ve 2025 düzey açığının taban-bağımsızlığı eklenir.
- §4.5'in "ortalamaya dönüş" uyarısı **doğrulanmıştır**: matematik ve fende 2018–2025 ortalama etkisinin yaklaşık yarısı 2015 çukurudur; 2025 düzeyi için geçerli değildir.
- Trend-düzeltmeli varyant §9'a sınır durumu olarak girer: "2006–2012 sapması kapsam genişlemesiyle birlikte yürüdüğü için eğim uzatması yanlış karşı-olgusal; ama uzatılırsa matematik ve fende ek hızlanma kalmaz."
- Öngörü (b) (§7) — "kompozisyon-düzeltilmiş 2015→2025 kazanımı ham kazanımın yarısından fazlasını koruyorsa hipotez yanlışlanır" — bu testle ilgisi yok; ama yeni bir öngörü eklenebilir: **(h) 2025 düzey açığı 2012-tabanlı tahmincilerde de korunuyor (+34…+50); 2029 gözlemi 2012-tabanlı SDiD'de 2025'in altına inerse "tek-gözlem" açıklaması güçlenir.**

## 4. Sınırlar

N0 = 5–8; hiçbir p < 0,10 (erişilebilir en küçük 0,11–0,17). Trend uzatması iki–dört ön-dönem noktasına dayanır; fen ön dönemi 2006–2012 (üç nokta). SDiD zaman ağırlıkları C varyantında 2012'ye yüklenir (bkz. CSV `sdid_time_weights`), yani C'nin SDiD'i pratikte 2012-tabanlı bir SC'dir; bu, DiD-2012 ile yakınlığını açıklar.
