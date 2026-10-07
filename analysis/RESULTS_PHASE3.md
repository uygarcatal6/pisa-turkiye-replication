# Faz 3 — Sağlamlık ve tanımlama testleri (ara rapor)

Tarih: 2026-09-15. Yazan: Claude Fable 5.1. Betikler: `analysis/09_robustness.R`, `10_placebo_domain.py`, `11_coverage_adjusted.R` (+ ortak çekirdek `_synth_core.R`). Çıktılar: `data/derived/robustness/`, `data/derived/coverage_adj/`, `data/derived/mechanisms/`. Mikroveri çaba/bileşim analizleri hâlâ çalışıyor, bu raporda yok.

## 0. Başlık: tasarımın en zayıf yeri bulundu

**Sahte kırılma testi (in-time placebo) kaldı.** Kırılmayı 2013 yerine 2009 varsayınca Türkiye zaten pozitif açık veriyor: sahte post dönemi ortalaması matematik +22,5, okuma +23,7 (2009: +20,1 / +18,6; 2012: +25,0 / +28,7). Yani Türkiye sentetik kontrolünden yalnızca 2013 sonrasında değil, 2009–2012'de de sapıyor. Ham haliyle bu, "2013 kurumsal kırılması" iddiasını zayıflatır.

**Ama iki niteleme testi kurtarıyor (kısmen):**
1. Test güçsüz: sahte ön dönem yalnızca 2 gözlem (2003, 2006) ve 14 donör → ön-RMSPE 0,0, yani sentetik kontrol ön dönemi *tam* eşliyor; böyle bir uyumdan sonra post açığı kısıtlanmamış durumda. İki noktalı ön dönemle bu test neredeyse her ülkede açık üretir.
2. Kırılma öncesi sapmanın bilinen mekanik açıklaması var: **kapsam genişlemesi**. Türkiye'nin Coverage Index 3'ü 2006'da 0,467, 2012'de 0,684 (+21,7 puan); donörlerde aynı dönemde −3,5 puan. Kırılma sonrasında ise Türkiye'nin kapsamı yalnızca +2,4 puan (0,6989 → 0,7224), donörlerde −3,7.

Göreli kazanımı göreli kapsam değişimine bölünce (`data/derived/coverage_adj/gap_per_coverage_point.csv`):

| Pencere | Göreli kapsam değişimi | Göreli kazanım (mat / okuma / fen) | Kapsam puanı başına kazanım |
|---|---|---|---|
| 2006→2012 (kırılma öncesi) | +25,2 pp | +24,3 / +15,2 / +35,2 | 1,0 / 0,6 / 1,4 |
| 2015→2025 (kırılma sonrası) | +6,1 pp | +62,5 / +75,8 / +78,5 | 10,3 / 12,5 / 12,9 |

Kırılma öncesi yükseliş kapsamla birlikte yürüyor; kırılma sonrası yükseliş kapsam değişiminin on katından fazla. Yani iki dönem aynı şey değil — ama "temiz 2013 kırılması" anlatısı artık savunulamaz. **Doğru çerçeve: Türkiye 2006'dan beri sentetik kontrolünden yukarı sapıyor; 2015'te kesintiye uğruyor; 2015 sonrası sapma kapsamla açıklanamayacak büyüklükte.**

## 1. Leave-one-out (R1)

Ana havuzdan (stabil OECD, katı kurallar) her donör sırayla çıkarıldı (`robustness/leave_one_out.csv`):

| Alan | Temel 2025 açığı | LOO aralığı |
|---|---|---|
| matematik | +50,4 | +31,6 … +57,5 |
| okuma | +34,1 | +31,0 … +55,1 |
| fen | +48,8 | +29,6 … +48,8 |

İşaret her durumda pozitif; büyüklük tek bir donöre duyarlı (matematikte en düşük değer temelin %63'ü). 5–8 donörlü havuzda beklenen kırılganlık.

## 2. Donör kuralı ızgarası (R3)

16 kombinasyon (havuz × OECD kısıtı × uyarı-yıldızı kuralı × 2015-kâğıt kuralı), `robustness/donor_rule_grid.csv`:

| Alan | Medyan 2025 açığı | Aralık | Pozitif oran |
|---|---|---|---|
| matematik | +50,4 | +42,9 … +70,8 | %100 |
| okuma | +33,1 | +31,7 … +34,1 | %100 |
| fen | +16,2 | −16,4 … +52,6 | %50 |

Matematik ve okuma kural seçimine **dayanıklı**. Fen değil: OECD kısıtı kalkınca Katar ağırlık 1,0 alıyor ve işaret dönüyor. Fen sonucu yalnızca OECD donörleriyle raporlanmalı, bu kısıt gerekçelendirilerek.

## 3. Ön dönem duyarlılığı (R4)

| Alan | 2003–2012 | 2006–2012 | 2009–2012 |
|---|---|---|---|
| matematik | +50,4 | +23,9 | +31,9 |
| okuma | +34,1 | +29,7 | +29,6 |
| fen | +48,8 | +48,8 | +43,8 |

Matematikte 2003 gözlemi sonucu iki katına çıkarıyor — 2003'te Türkiye'nin kapsamı en düşük (veri yok, 2006'da 0,467) ve puanı en düşük. Muhafazakâr okuma: **matematik açığı ~+24, okuma ~+30, fen ~+44–49.**

## 4. Kapsam-düzeltilmiş spesifikasyon (S2)

Kapsamı ülke-içi (within) regresyonla dışarı alıp SC tekrarlandı (`coverage_adj/coverage_adjusted_specs.csv`):

| Alan | Ham (ön 2006–2012) | Kapsam-düz. (tüm ülkeler) | Kapsam-düz. (yalnız tedavisizler) |
|---|---|---|---|
| matematik | +23,9 | +20,5 | +19,3 |
| okuma | +29,7 | +28,2 | +27,1 |
| fen | +48,8 | +37,7 | +41,0 |

**Uyarı — bu düzeltme geçerli bir seçim düzeltmesi DEĞİL.** Tahmin edilen kapsam katsayısı pozitif çıktı (matematik +17,0, okuma +24,9, fen +35,9 puan / birim kapsam; standart hatalar büyük). Teori tersini söyler: kapsam genişlerse marjinal (daha zayıf) öğrenciler örnekleme girer, ortalama **düşer**. Pozitif katsayı, ülke-içi regresyonun seçim etkisini değil ortak zaman trendini yakaladığını gösteriyor. Dolayısıyla tablo yalnızca bir duyarlılık kaydı.

Yine de yön olarak kullanışlı: katsayı **yanlış işaretliyken bile** açıklar ayakta kalıyor; doğru işaretle (b < 0) düzeltme Türkiye'nin açığını **büyütürdü**, çünkü Türkiye'nin kapsamı donörlerden hızlı arttı. Yani raporlanan açıklar bu kanal açısından muhafazakâr.

Gerçek çözüm mikroveride: sabit kohort payına göre kesme (Spaull / Lee sınırları) — örneğin her döngüde en üst %47'lik dilimle karşılaştırma. Mikroveri ajanı bittiğinde yapılacak.

## 5. Koşullu plasebo-alan testi (yeni)

Ham "çekirdek − CPS" farkı düşük kapasiteli sistemlerde mekanik olarak büyük olduğu için CPS, çekirdek düzeye regresyon edildi; Türkiye'nin artığına bakıldı (`mechanisms/placebo_conditional_2025.csv`).

| Örneklem / model | n | Eğim | R² | Türkiye artığı | Sıra (en negatiften) |
|---|---|---|---|---|---|
| Tüm katılımcılar, doğrusal | 84 | 1,013 | 0,891 | **−31,8** | 5/84 |
| Tüm katılımcılar, karesel | 84 | — | 0,908 | **−35,1** | 3/84 |
| Yalnız OECD, doğrusal | 38 | 0,863 | 0,849 | **−33,5** | **1/38** |
| Yalnız OECD, karesel | 38 | — | 0,850 | −33,0 | **1/38** |

Gürcistan −22,0 (9/84) ve −26,2 (8/84); Macaristan +2,6 / −2,3 (ortalarda). Odak ülke uyuma dahil edildiği için artıklar muhafazakâr; Türkiye uyumdan çıkarılınca (leave-one-out) artık −32,3 / −35,8 (tüm) ve −34,5 / −34,2 (OECD). Yani **Türkiye'nin hesaplamalı problem çözme puanı, kendi çekirdek alan düzeyine koşullu olarak OECD'nin en düşük artığı** — hazırlık yapılabilen alanların şiştiği, yapılamayanın şişmediği öngörüsüyle tutarlı. Ham farkta Türkiye'nin üstünde görünen KEN/QCI/AZE/ARM burada ayrışıyor: koşullu test düzey etkisini temizliyor.

Uyarı: tek döngü, tek yeni alan. İkinci aday alan (PISA 2022 yaratıcı düşünme) Türkiye için kullanılamıyor — bkz. §5b.

## 5b. İkinci plasebo alan denemesi: PISA 2022 yaratıcı düşünme — Türkiye katılmadı

Veri 2026-09-16'da indirildi (Opus 5 tarayıcı ajanı; `data/pisa_microdata/2022/creative_thinking/CRT_SPSS.zip`, kod kitabı, compendia; Volume III PDF + 7 annex çalışma kitabı `data/pisa/2022/volume_iii/`). Betik: `13_creative_thinking_2022.py` (Fable 5.1); çıktılar `data/derived/creative_thinking_2022.csv`, `data/derived/mechanisms/placebo_conditional_2022*.{csv,json}`, `analysis/figures/mech_placebo_conditional_2022.png`.

**Bulgu (iki bağımsız kaynak):** Annex Table III.B1.2.1'de (`opbe7a.xlsx`) 74 ülke/ekonomi satırının 64'ü katılımcı, 10'u 'm' (missing): Avusturya, İrlanda, Norveç, İsviçre, **Türkiye**, Birleşik Krallık (6 OECD üyesi) ve Arjantin, **Gürcistan**, Kosova, Karadağ. Mikroveride (`CY08MSP_CRT_COG.SAV`, 499.843 öğrenci, 63 sistem) CNT listesinde TUR ve GEO yok; 'm' olan hiçbir ülke mikroveride bulunmadı. Sonuç: **yaratıcı düşünme Türkiye için de Gürcistan için de plasebo-alan sonucu olamaz.** İkiz vaka karşılaştırması bu alanda yapılamaz.

Yorum sınırı: "Türkiye hazırlık yapılamayan alandan kaçındı" biçiminde bir tasarım-karşıtlığı argümanı **desteklenmiyor** — aynı alana Norveç, İsviçre, İrlanda, Avusturya ve Birleşik Krallık da katılmadı; katılmama ayırt edici değil.

Veri notları: PV adları `PV1CRTH_NC…PV10CRTH_NC` ("Number Correct" etiketine rağmen 0–60 raporlama ölçeğinde; gözlenen aralık 0,10–59,30); CRT dosyasında W_FSTUWT ve hiçbir W_* yok (ağırlıklı hesap için STU_QQQ ile CNT+CNTSCHID+CNTSTUID birleştirmesi gerekir); dosya CRT sürümü çekirdek PV'ler (`PV1MATC…`, `PV1REAC…`, `PV1SCIC…`) içerir, bunlar STU_QQQ PV'leriyle aynı sayılar değildir. Çapraz-kontrol: mikroveriden ağırlıksız 10-PV ortalaması ile yayımlanmış ağırlıklı ortalama arasındaki fark ortalama +0,20 puan, en büyük |fark| 2,42 (Tayland; n=60 eşleşen sistem) — isim ve ölçek doğru.

**Katılımcılar için koşullu test** (yaratıcı düşünme ~ çekirdek 2022; panelde çekirdek puanı olan 61 sistem, 28 OECD üyesi; OECD ortalaması 32,67):

| Örneklem, spesifikasyon | n | Eğim | R² | RMSE | Macaristan artığı (puan / SD) | Sıra (en negatif = 1) |
|---|---|---|---|---|---|---|
| Tüm katılımcılar, doğrusal | 61 | 0,1135 | 0,852 | 2,57 | −1,03 / −0,40 | 16/61 |
| Tüm katılımcılar, karesel | 61 | — | 0,877 | 2,37 | −1,60 / −0,68 | 12/61 |
| Yalnız OECD, doğrusal | 28 | 0,0915 | 0,771 | 1,61 | −2,12 / −1,32 | 3/28 |
| Yalnız OECD, karesel | 28 | — | 0,800 | 1,53 | −1,73 / −1,13 | 4/28 |

Macaristan (yaratıcı düşünme 30,94, S.E. 0,33; çekirdek 477,2) OECD içinde alt uçta ama tüm katılımcılar arasında ortalarda; leave-one-out artıkları −1,05 / −1,65 / −2,20 / −1,83. Türkiye'nin CPS'teki −32…−35'lik (RMSE'nin 1,5–2 katı) artığıyla karşılaştırılabilir bir sinyal değil; Macaristan'ın çekirdek puanları zaten düz (§RESULTS).

Katılım taraması (yerel mikroveriden, `data/derived/cache/innovative_domain_participation.csv`): PISA 2015 işbirlikli problem çözme — STU_QQQ'daki `Option_CPS` bayrağı Türkiye'de 5.895/5.895, Macaristan'da 5.658/5.658 öğrencide 1, Gürcistan'da 0 (53/73 sistem katıldı); PISA 2018 küresel yetkinlik bilişsel testi — `PV1GLCM` Türkiye, Gürcistan ve Macaristan'da tümüyle boş (29/80 sistem katıldı). Yani kullanılabilir ikinci alan **2015 işbirlikli problem çözme** — §5c. PISA 2012 yaratıcı problem çözme (kırılma öncesi karşılaştırma noktası) henüz kontrol edilmedi (2012 mikroverisi klasörde yok).

## 5c. İkinci plasebo alan (kullanılabilen): PISA 2015 işbirlikli problem çözme — Türkiye katıldı

Veri: `data/pisa_microdata/2015/PUF_SPSS_COMBINED_CMB_STU_CPS.zip` (36.306.694 B, webfs.oecd.org, 2026-09-16'da curl ile indirildi; üye `CY6_MS_CMB_STU_CPS.sav`, 414.498 öğrenci, 53 sistem, `PV1CLPS…PV10CLPS`; dosyada ağırlık yok → `W_FSTUWT` STU_QQQ'dan CNT+CNTSCHID+CNTSTUID ile birleştirildi, eşleşmeyen öğrenci payı 0,0000). Betik: `15_cps2015_placebo.py` (Fable 5.1); çıktılar `data/derived/cps2015_country_means.csv`, `data/derived/mechanisms/placebo_conditional_2015cps*.{csv,json}`, `analysis/figures/mech_placebo_conditional_2015cps.png`. Alt-ulusal birimler (İspanya bölgeleri, Massachusetts, Kuzey Karolina) atıldı → 50 sistem (B-S-J-G Çin dahil); panelde 2015 çekirdek puanı olmayan QCH (B-S-J-G Çin), RUS, TUN regresyon dışında → **n=47** (35 OECD üyesi — bugünkü üyelik, panel bayrağı).

Ülke ortalaması = 10 PV'nin öğrenci-düzeyi ortalamasının W_FSTUWT-ağırlıklı ortalaması (nokta tahmini; BRR standart hatası üretilmedi). Türkiye 422,4 (ağırlıksız 419,7; PV'si tam 5.895 öğrenci), Macaristan 472,2 (ağırlıksız 479,3). OECD üyesi ülke ortalamalarının ortalaması 495,4 (n=35; Volume V'in OECD ortalaması 2015 üyeliğine göre tanımlı olduğu için birebir karşılaştırılamaz). Ağırlıklı−ağırlıksız fark ortalama −0,6 puan, en büyük |fark| 15,5 (Slovenya; Şili −14,1, Danimarka +13,3 — tabakalı aşırı-örnekleme ile uyumlu). Yayımlanmış değerlerle çapraz-kontrol: OECD Volume V annex tablosunun kendisi alınamadı (oecd.org / oecd-ilibrary / doi.org 403), ancak OECD ülke ortalamalarını yeniden basan Birleşik Krallık DfE raporu (*Achievement of 15-Year-Olds in England: PISA 2015 Collaborative Problem Solving National Report*, Kasım 2017, Tablo 5; `docs/secondary_reports/UK_DfE_PISA_2015_CPS_National_Report.pdf`) Türkiye **422**, Macaristan **472** veriyor — bizim 422,4 / 472,2 ile 0,5 puan içinde. Birincil tabloyla karşılaştırma 20 Eylül 2026'da yapıldı (adım 24, `24_placebo_backbone.py`): OECD Volume V Figure V.1.1 (s. 43–44; `data/pisa/2015/9789264285521-en.pdf`) 50/50 ülkede yuvarlama sonrası birebir, maks fark 0,50 (`data/derived/placebo_backbone/cps2015_crosscheck_oecd_volv.csv`); DfE Tablo 3–5 ile 49/49.

**Koşullu test** (CPS 2015 ~ çekirdek 2015):

| Örneklem, spesifikasyon | n | Eğim | R² | RMSE | Türkiye artığı (puan / SD) | Sıra | Macaristan artığı (puan / SD) | Sıra |
|---|---|---|---|---|---|---|---|---|
| Tüm katılımcılar, doğrusal | 47 | 0,980 | 0,934 | 10,7 | **−12,9 / −1,20** | 5/47 | −11,7 / −1,09 | 8/47 |
| Tüm katılımcılar, karesel | 47 | — | 0,942 | 10,2 | **−13,1 / −1,29** | 5/47 | −7,9 / −0,77 | 14/47 |
| Yalnız OECD, doğrusal | 35 | 1,009 | 0,888 | 11,5 | −11,5 / −1,00 | 8/35 | −11,7 / −1,02 | 6/35 |
| Yalnız OECD, karesel | 35 | — | 0,906 | 10,7 | **−14,5 / −1,36** | **2/35** | −6,7 / −0,63 | 10/35 |

Leave-one-out artıklar: Türkiye −13,7 / −13,9 / −13,3 / −17,1; Macaristan −11,9 / −8,3 / −12,1 / −7,2. Çekirdek 2015: Türkiye 424,8 (mat 420,5 / okuma 428,3 / fen 425,5), Macaristan 474,4; ikisinde de 2015 uyarı yıldızı yok.

**Okuma.** 2015'te (kırılmadan iki yıl sonra, Türkiye'nin çekirdek puanlarının düştüğü "kesinti" döngüsü) Türkiye'nin hazırlık yapılamayan alandaki artığı **yön olarak şişmeyle uyumlu ama orta büyüklükte**: ≈ −13 puan, RMSE'nin 1,0–1,4 katı, dağılımın alt %6–23'ü; Macaristan'ınkiyle (düz seyreden bir ülke) hemen hemen aynı büyüklükte, yani 2015'te Türkiye'ye özgü değil. 2025 CPS artığıyla (−32…−35, OECD'de 1/38) yan yana konduğunda tablo, §0'daki "2015 sonrası hızlanma" çerçevesiyle tutarlı: hazırlık-uyumlu alan ayrışması 2015'te zayıf, 2025'te güçlü. Uyarı: iki alan (işbirlikli problem çözme, hesaplamalı problem çözme) farklı yapılar; artıklar doğrudan puan olarak karşılaştırılamaz, yalnızca SD/sıra düzeyinde.

## 6. Bu turun net sonucu

- **Güçlenen**: 2015 sonrası sapma kural seçimine, donör çıkarmaya ve (yanlış işaretli) kapsam düzeltmesine dayanıklı; koşullu plasebo-alan testi şişme yönünde ve OECD'de en uç.
- **Zayıflayan**: "2013'te temiz kırılma" iddiası. Türkiye 2009–2012'de de sapıyor; o sapmanın kapsamla açıklanabilir olması hipotezi kurtarıyor ama tasarımın çapa yılını savunmasız bırakıyor.
- **Öneri**: proposal §4.1 revize edilsin — tek kırılma yılı yerine "2006'dan beri süren yukarı sapma; 2015 kesintisi; 2015 sonrası kapsamla açıklanamayan hızlanma" çerçevesi. Kırılma yılı duyarlılığı (2013 vs 2015 vs sürekli trend) ayrı bir tablo olarak raporlansın.

## 7. Çaba kanalı — mikroveri (madde süreleri, hızlı tahmin, atlama)

Kaynak: `data/derived/effort_microdata.csv` (2015–2022; betik `07_microdata_effort.py`, Opus 4.8 yazdı, Fable 5.1 inceledi) ve `data/derived/effort_2025_process.csv` (2025; betik `12b_effort_2025_process.py`, süreler `CY09_MS_COG_PROCESS` dosyasından). Tanımlar: NT15 = madde süresinin, o maddenin havuz medyanının %15'inin altında olması (Michaelides & Ivanova 2022); "sıfır eylem" = öğrencinin maddeyle hiç etkileşmemesi (yalnız 2025); ağırlık W_FSTUWT. Donör = BEL, CHE, FRA, ISL, JPN ortalaması. Madde kümesi döngüler arası değiştiği için yalnızca **döngü içi Türkiye − donör farkı** yorumlanır.

| Gösterge | 2015 TUR / donör | 2018 | 2022 | 2025 |
|---|---|---|---|---|
| Madde başına medyan süre (s) | 62,2 / 63,8 | 41,2 / 41,0 | 55,2 / 55,2 | **57,8 / 47,4** |
| Hızlı yanıt NT15 (%) | 8,4 / 6,2 | 10,5 / 6,4 | 5,3 / 5,4 | 4,4 / 5,2 |
| Sabit 5 sn (%) | 5,0 / 3,4 | 24,6 / 21,4† | 14,2 / 12,8 | 17,9 / 18,1 |
| Boş bırakma (%) | 2,2 / 2,0 | 1,1 / 1,4 | 1,3 / 2,6 | yok‡ |
| Sona ulaşamama (%) | 0,5 / 0,9 | 2,7 / 3,5 | 1,2 / 3,1 | 0,6 / 1,4 |
| Sıfır eylemli madde (%) | – | – | – | 1,5 / 2,8 |
| Doğru yüzdesi | 41,7 / 57,6 | 65,2 / 71,5 | 58,3 / 64,6 | 58,0 / 59,5 |

† 2018 okuma-akıcılığı maddeleri tasarım gereği 1–3 sn'de yanıtlanır; sabit eşik bu döngüde yapısal olarak şişer (Japonya da %21). ‡ 2025 PUF'ta "no response" kodu yok.

Okuma:
- **Türkiye öğrencilerinin çabası hiçbir döngüde donörlerin altında değil**: boş bırakma ve sona ulaşamama her döngüde daha düşük; hızlı yanıt 2018'de geçici olarak yüksek (+4,1 puan, kısmen madde tipi), 2022'den itibaren donör düzeyinde ya da altında.
- **2025'te zaman-üstünde-kalma açıldı**: 2022'de madde başına süre donörlerle eşitken (55,2 / 55,2) 2025'te Türkiye 57,8 s ile 26 ülkelik havuzun **en yükseği**, donörlerden 10,4 s (%22) fazla. Hızlı yanıt −0,9, sıfır eylem −1,3, sona ulaşamama −0,8 puan. Yani 2025'te Türkiye öğrencileri akranlarına göre daha uzun uğraştı ve daha az bıraktı; bu, hazırlık/motivasyon seferberliğinin uygulama davranışına yansıması olarak **hazırlık hipoteziyle tutarlı**, fakat tek başına şişme kanıtı değil (gerçek beceri artışı da süre kullanımını değiştirebilir).
- **Öz-bildirim ile davranış ayrışıyor**: çaba termometresi (Table I.A1.1) Türkiye'de 8,91 (2018) → 8,57 (2022) → 8,32 (2025) düşerken (hâlâ OECD-35 ortalaması 7,16'nın çok üstünde, "çok az çaba" payı %2 vs OECD %5,5), gözlenen zaman-üstünde-kalma yükseldi. Öz-bildirim bu soruda zayıf ölçüt.
- **Doğru yüzdesi farkı kapanıyor**: −15,9 (2015) → −6,3 → −6,3 → −1,5 (2025); puan yakınsamasının madde düzeyindeki karşılığı.
- **Gürcistan çaba kanalıyla açıklanıyor gibi**: NT15 %15,4 (2022) → %8,1 (2025), madde başına süre 37,5 → 47,1 s, sona ulaşamama %3,2 → %1,5; termometre +0,18. Fen +38'in önemli kısmı uygulama davranışındaki düzelmeyle uyumlu. Macaristan düz (NT15 %5,0; süre 47,8).
- Test-sonu düşüşü hesaplanamadı: madde uygulama sırası kamuya açık dosyalarda yok.

## 8. Bileşim kanalı — örneklem vs evren, resmî vs özel

**Mikroveri (STRATUM etiketleri, ağırlıklı öğrenci payı, %; `turkiye_school_type_composition.csv`):** Anadolu 46,0 / 57,5 / 45,6 (2018/2022/2025); mesleki-teknik 31,5 / 24,3 / 27,1; imam hatip 12,7 / 10,2 / 9,5; fen 4,0 / 5,6 / 4,5; özel okul (yalnız 2025'te ayrı tabaka) 11,1. MEB Ön Raporu'nun 2018 payları (43,7 / 31,1 / 13,7) mikroveriyle ≤2,3 puan farkla, 2022 raporu neredeyse birebir örtüşüyor. 2022'de Anadolu payındaki +11,5 puanlık sıçrama (mesleki −7,1) o döngünün ortalamasını yukarı çekmiş olabilir; 2025'te geri dönüyor, oysa puan daha da yükseliyor.

**MEB PISA 2025 Türkiye Raporu (4 Eyl 2026; `meb2025_report_extracts.csv`, 43 değer ilgili grafik bloğunun pdftotext metninde doğrulandı; doğrulayıcı çalışmadan önce 5 kasıtlı yanlış değeri reddettiğini kendi üstünde sınıyor — Opus 4.8 denetiminin bulduğu gevşek sürüm düzeltildi):**

| Okul türü | Örneklem % | Evren % | Fark |
|---|---|---|---|
| Anadolu lisesi | 46,6 | 47,0 | −0,4 |
| Mesleki ve teknik Anadolu | 32,8 | 28,9 | +3,9 |
| Anadolu imam hatip | 9,5 | 10,3 | −0,8 |
| Fen lisesi | 5,9 | 5,3 | +0,6 |
| Sosyal bilimler | 3,2 | 0,9 | +2,3 |
| Çok programlı Anadolu | 1,0 | 3,6 | −2,6 |
| Güzel sanatlar / spor | 0,9 | 1,1 | −0,2 |

Örneklem evreni izliyor; en büyük sapma mesleki-teknik lehine (+3,9), bu ortalamayı **düşürür**. Okul-türü bileşimi (çerçeve içinde) şişme kanalı olarak **desteklenmiyor**. Not: bu "evren" MEB'in çerçeve nüfusudur; açık öğretim ve MESEM bu türlerin hiçbirinde yok — çerçeve dışı kalıp kalmadıkları hâlâ Teknik Rapor'a bağlı.

**Resmî vs özel (aynı rapor, Grafik 3.13 / 4.11 / 5.11 / 6.4):**

| Alan | Resmî 2022 → 2025 | Özel 2022 → 2025 |
|---|---|---|
| Fen | 479 → 497 (+18) | 465 → 475 (+10) |
| Okuma | 458 → 475 (+17) | 448 → 449 (+1) |
| Matematik | 455 → 464 (+9) | 447 → 444 (−3) |
| CPS 2025 | 475 | 453 |

İki sonuç: (i) özel okul payının 2015 %4,8'den 2018+ %11–13'e çıkması ortalamayı **aşağı** çeker (özel okullar daha düşük puanlı) → "özel okul bileşimi" kanalı şişme yönünde değil; (ii) 2022→2025 kazanımı MEB'in doğrudan yönettiği **resmî okullarda** yoğunlaşıyor (her alanda özelden 8–16 puan fazla). Bu, Ocak 2025 çalıştayı (203 örneklem okulu, 601 öğretmen — MEB'in kendi kaydı) ile aynı yönde bir imza; ama özel sektörün 2014 sonrası dershane-dönüşümüyle bileşiminin değiştiği alternatif açıklaması dışlanamıyor. Test: resmî/özel kazanım farkının donör ülkelerde de olup olmadığı (mikroverideki SC013 ile hesaplanabilir, yapılmadı).

Fen kazanımı okul türlerinin hepsinde: fen lisesi +18, sosyal +29, Anadolu +22, çok programlı +78, imam hatip +26, güzel sanatlar/spor +13, mesleki +15 (Grafik 3.12). Tek türde yoğunlaşma yok.

## 9. 2025 dışlama ve yanıt oranları — yayımlanmamış

> **ERRATUM (2026-09-19, gece):** Bu başlık yazıldığında OECD'nin PISA 2025 Teknik Raporu **taslak** bölümleri (Böl. 7, 14, 18; 14 Eyl 2026 sürümü) `docs/oecd_technical_reports/2025/` altında zaten duruyordu. Böl. 14 Ek Tablo 14.A.1 Türkiye satırı: genel dışlama **%2,74** (okul düzeyi %0,63; örneklem içi %2,11), okul yanıtı 98,9 / 100, öğrenci yanıtı 98,6 — **ama Böl. 18 Türkiye notuna göre bu oran 2018/2022 ile karşılaştırılamaz** (açık öğretim + MESEM 2025 çerçevesinde yok; 2018/2022'de listelenip dışlama sayılmıştı). Aşağıdaki §8 son notu ve §9 metni bu bilgiyle okunmalı. Ayrıntı: `V4_CERCEVE_DISLAMA_NOTU_2026-09-19.md`; sayılar `analysis/19_exclusion_frame_2025.py`.

Volume I 2025'in Annex A2'si yalnızca kayıt/kapsam tablolarını (I.A2.1–I.A2.3) içeriyor; dışlama ve yanıt oranlarını "PISA 2025 Technical Report, Chapter 14 (forthcoming)" adresine erteliyor. Yalnızca uyarı bayrağı alan ülkelerin oranları Okuyucu Rehberi'nde (Kanada, Hollanda %9,3, Yeni Zelanda %8,1, Norveç %10,4, ABD %6,9, Arnavutluk; `adjudication_2025.csv`). Türkiye bayrak almadığı için 2025 dışlama/yanıt oranı **kamuya açık değil**; bilinen tek şey kapsam endeksi 0,722. Bu boşluk Teknik Rapor çıkana kadar kapanmaz.


Not (2026-09-16, yazar): MESEM/açık öğretim/program bazlı örnekleme iddiasının tek kaynağı soL Haber'dir; proje kaynak politikasında partizan/"ciddiye alma" bayraklıdır (`claim_check/SOURCE_RELIABILITY_FLAGS.md`). 8 Eylül 2026 tarihli PISA 2025 Vol I (Annex A2 dahil), OECD Türkiye ülke notu, 2025 annex çalışma kitapları ve MEB 2025 raporunda bu iddialar geçmiyor → asılsız/doğrulanmamış; Teknik Rapor Bölüm 14'e kadar yalnızca kontrol edilecek soru.

## 10. Bu turun güncellenmiş sonucu

| Kanal | Bulgu | Şişme hipotezi için |
|---|---|---|
| Kapsam (2003–2012 genişleme) | Kırılma öncesi sapmayı açıklıyor; 2015 sonrası kapsam yatay | Kırılma yılı iddiasını zayıflatır, 2015 sonrası sapmayı açıklamaz |
| Okul-türü bileşimi (çerçeve içi) | Örneklem ≈ evren; mesleki fazla temsil | Desteklenmiyor (ters yön) |
| Özel okul payı | Arttı ama özel okullar daha düşük puanlı | Desteklenmiyor (ters yön) |
| Çerçeve (MESEM / açık öğretim) | Doğrulanamıyor; 2025 dışlama oranı yayımlanmadı | Açık |
| Çaba (davranışsal) | Türkiye her döngüde ≥ donör; 2025'te süre farkı açıldı (+10 s/madde) | Hazırlıkla uyumlu, tek başına belirleyici değil |
| Çaba (öz-bildirim) | Düşüyor | Yön belirsiz |
| Plasebo alan (CPS 2025, koşullu) | Türkiye artığı −32…−35, OECD'de 1/38 | **Destekliyor** |
| Plasebo alan (işbirlikli PÇ 2015, koşullu) | Türkiye artığı ≈ −13 (−1,0…−1,4 SD), 5/47; Macaristan benzer | Yön uyumlu, zayıf; 2015→2025 hızlanma ile tutarlı |
| Resmî vs özel kazanım | Kazanım resmî okullarda yoğun | Hazırlıkla uyumlu, alternatif açıklama var |
| Otokratikleşen akranlar | Havuzlanmış etki ≈ +8, anlamsız | Türkiye istisna |

Net: "çerçeve içi bileşim" ve "düşük çaba" kanalları elendi; ayakta kalanlar **hazırlık/teaching-to-test** (plasebo alan + resmî-okul yoğunlaşması + 2025 zaman-üstünde-kalma) ve **çerçeve dışı bileşim** (doğrulanamıyor). Gerçek öğrenme kazanımı hâlâ dışlanamıyor; ayırt edici test, hazırlık yapılamayan alanlarda (2025 CPS artığı −32…−35, 1/38; 2015 işbirlikli problem çözme artığı ≈ −13, 5/47 — §5c; 2022 yaratıcı düşünme ve 2018 küresel yetkinlik Türkiye için yok — §5b) ve bağımsız kohort çıktılarında.

## 11. Sırada

1. ~~PISA 2022 yaratıcı düşünme veri seti indirilip koşullu plasebo testi ikinci alanla tekrarlanacak~~ → indirildi (2026-09-16); **Türkiye ve Gürcistan katılmamış**, test yalnız katılımcılar için raporlandı (§5b). 2015 işbirlikli problem çözme indirildi ve test edildi (§5c: Türkiye artığı ≈ −13, 5/47); 2018 küresel yetkinliğe Türkiye katılmamış. Ülke ortalamaları DfE raporundaki yayımlanmış değerlerle 0,5 puan içinde örtüştü; Volume V birincil tablosuyla karşılaştırma 20 Eylül'de kapandı (adım 24: 50/50 birebir); kalan: 2012 yaratıcı problem çözme (kırılma öncesi karşılaştırma) — yayımlanmış PISA 2012 Volume V tablosundan kurulabilir, mikroveri şart değil.
2. Resmî/özel 2022→2025 kazanım farkının donör ülkelerdeki karşılığı (SC013 ile).
3. Sabit kohort payıyla kapsam sınırlaması (Spaull/Lee) — mikroveri hazır.
4. Zaman-üstünde-kalma ile puan ilişkisi: 2025'te Türkiye'nin süre farkı puan farkının ne kadarını "açıklar" (ülke-içi, kontrol değişkenli).
5. Teknik Rapor çıkınca 2025 dışlama/yanıt oranları ve çerçeve kararı.
6. ~~Bu rapor Opus 4.8 denetiminden geçecek~~ → yapıldı, bkz. §12.

## 12. Denetim kaydı

Opus 4.8 denetimi (2026-09-15, `analysis/RESULTS_PHASE3_AUDIT.md`): 210 sayı çıktı dosyalarına karşı kontrol edildi, 207 birebir. Bulunan ve bu sürümde düzeltilenler: (1) §0 sahte-kırılma çifti "+20/+29" farklı yıllardan okunmuştu → sahte-post ortalamaları (+22,5 / +23,7) ve yıl bazlı değerler yazıldı; (2) kapsam +2,4 için uçlar dört haneli gösterildi; (3) mesleki payı değişimi ham veriden −7,1. Kod incelemesi (Fable 5.1'in yazdığı `_synth_core.R`, `09`, `10`, `11`, `12b`, `14`): mantık hataları yok; tek gerçek bulgu `14_meb2025_report_extracts.py`'nin doğrulama regex'inin tam sayılar için koruyucu olmaması (±2 sayfa penceresinde kasıtlı yanlış 498 ve 466 geçiyordu) → doğrulama grafik bloğuna daraltıldı, simetrik lookaround, kasıtlı yanlış değerlerle öz-test eklendi; 43/43 yeniden doğrulandı, 5 yanlış değer reddediliyor. Düşük notlar: `12b` docstring sentinel eşiği kodla uyumlu hale getirildi; `11`'in coverage_table'ı ile §0'ın donör kümesi farklı (5'li vs 8'li) — §0 yalnızca 8'li kümenin değişimlerini kullanıyor, JSON'daki düzeyler alıntılanmıyor. Denetim önerisiyle §5'e leave-one-out artıklar eklendi. Fable 5.1 ayrıca Opus 4.8'in yazdığı `07` ve `08` betiklerini inceledi (tabaka sınıflandırma sırası, ağırlıklandırma, kod şeması): mantık hatası bulunmadı.

Ek denetim (2026-09-16, `RESULTS_PHASE3_AUDIT.md` sonundaki bölüm; iki bağımsız Opus 4.8 ajanı): §5b — 50/50 sayı birebir, sıfır uyuşmazlık; Türkiye/Gürcistan'ın 2022 yaratıcı düşünmeye katılmadığı Excel + mikroveri ile doğrulandı; betik 13'te mantık hatası yok (LOW: 'm' etiketi "katılmadı" olarak yorumlanıyor, ölü eşlemeler, temp dizini). §5c — 89/90 sayı; tek küçük uyuşmazlık Türkiye SD aralığı "−1,2…−1,4" (gerçek −1,00…−1,36) → bu sürümde "−1,0…−1,4" yapıldı; betik 15 parquet'ten bağımsız yeniden hesaplamayla birebir; mikroveri ortalamaları DfE raporunun yeniden bastığı OECD değerleriyle (422/472) örtüştü; kozmetik: `focus_asterisk_2015` alanında "nan" string'i → null yapıldı, README giriş cümlesine adım 15 eklendi, "50 ulusal sistem" ifadesi düzeltildi.
