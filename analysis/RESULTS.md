# PISA puan şişmesi — Faz 2 analiz sonuçları (ilk tur)

Tarih: 2026-09-15. Yazan: Claude Fable 5.1. Veri: `data/derived/analysis_panel.csv` (579 ülke×döngü satırı; OECD Volume I annex tablolarından, WGI/CPI/ERT dosyalarından; 24/24 doğrulama testi geçti — `data/derived/PANEL_README.md`). Betikler: `analysis/01_build_panel.py`, `02_institutional_screen.py`, `03_synth.R`, `04_cs_did.R`, `05_mechanisms.R`. Çıktılar: `data/derived/synth/`, `data/derived/did/`, `data/derived/mechanisms/`, şekiller `analysis/figures/`. Bu rapordaki her sayı bu çıktı dosyalarından alınmıştır; bağımsız denetim notu en altta.

## 0. Bir cümlelik sonuç

Türkiye'nin 2018–2025 PISA yörüngesi, hem ortalamadan arındırılmış sentetik kontrolün hem de hiç kırılma yaşamamış ülkelerin ima ettiği yolun üzerinde (2025'te üç alanda +34 ile +67 puan arası); otokratikleşen diğer ülkelerde böyle bir yükseliş yok (havuzlanmış etki ≈ +8, anlamsız), Macaristan (negatif kontrol) düz; ama donör havuzu çok ince olduğu için (5–8 OECD ülkesi) plasebo çıkarımı zayıf ve bu ilk tur "mekanizma" değil, yalnızca "olağandışı yörünge" kanıtıdır.

## 1. Donör havuzu ve tasarım kısıtları (proposal §4.1'in veriyle karşılaşması)

Kurumsal tarama (`institutional_screen.csv`, 179 ülke; `SCREEN_README.md`): OECD üyesi 38 ülkeden **stable_clean 16, stable_corrupt 1 (Kolombiya), ambiguous 9 (AUT, CHL, CRI, DEU, FIN, ISR, NLD, PRT, SWE: ERT epizodu yok ama libdem düşüşü güven bandı dışında), treated_autocratization 10 (CZE, GBR, GRC, HUN, ITA, MEX, SVK, SVN, TUR, USA), treated_reversed 2 (KOR, POL)**.

Proposal'ın katı kuralları (stabil + 2015 kâğıt-tabanlı değil + kullanılan döngülerde uyarı yıldızı yok + 2003–2025 tam veri) uygulanınca matematik/okuma için **yalnızca 5 OECD donörü kalıyor: BEL, CHE, FRA, ISL, JPN** (fen için 7–8: + EST, LTU, COL). Sebep: 2022 (AUS, CAN, DNK, IRL, LVA, NLD, NZL, GBR, USA…) ve 2025 (CAN, NLD, NOR, NZL, USA) yanıt-oranı uyarıları OECD'nin yarısını eliyor; ESP/EST/LTU 2003'te yok. **"Yozlaşmış-stabil" alt grubu OECD içinde yok** (tek üye Kolombiya) → proposal'ın iki alt gruplu tasarımı OECD içinde yürütülemez; OECD dışı stabil-yozlaşmış ülkelerde de 2003–2025 tam serisi olan yalnızca BGR ve COL var.

**Seviye eşleştirmesi çöküyor:** Türkiye 2003–2012'de her stabil OECD donörünün 50–100 puan altında (dışbükey zarfın dışında); seviye-Synth'te ön dönem RMSPE'si matematikte 65 puan (`TUR_levels_*`). Bu yüzden ana spesifikasyon **ortalamadan arındırılmış (intercept'li) sentetik kontrol**: her ülkenin puanından kendi ön dönem ortalaması çıkarılır, yörünge eşleştirilir (Doudchenko–Imbens / Ferman–Pinotti mantığı). Ön dönem: mat/okuma 2003–2012 (4 gözlem), fen 2006–2012 (3 gözlem; fen ölçeği 2006'da kuruldu).

## 2. Sentetik kontrol — Türkiye (`data/derived/synth/synth_summary.csv`)

Açık (gap) = Türkiye − sentetik Türkiye, puan. Ön dönem uyumu iyi (pre-RMSPE 2–11). Plasebo p-değerleri: p(ratio) = post/pre RMSPE oranı Türkiye'ninkinden ≥ olan birim payı; p(gap) = ortalama post açığı Türkiye'ninkinden ≥ olan birim payı (birim sayısı = donör + 1; **5 donörle ulaşılabilir en küçük p = 0,17**).

| Spesifikasyon | Donör | Ön-RMSPE | 2015 | 2018 | 2022 | 2025 | Ort. post açığı | p(gap) | p(ratio) |
|---|---|---|---|---|---|---|---|---|---|
| **Ana, mat** (stabil OECD, katı) | 5 | 9,4 | −8,7 | +30,2 | +32,8 | **+50,4** | +26,2 | 0,17 | 0,33 |
| **Ana, okuma** | 5 | 2,6 | −28,7 | +19,8 | +4,9 | **+34,1** | +7,6 | 0,33 | 0,17 |
| **Ana, fen** | 7 | 10,9 | −20,8 | +31,3 | +21,4 | **+48,8** | +20,2 | 0,12 | 0,88 |
| Sağlamlık A: + ambiguous OECD, mat | 8 | 6,7 | −12,4 | +26,5 | +51,4 | +70,8 | +34,1 | 0,11 | 0,67 |
| Sağlamlık A, okuma | 8 | 2,4 | −29,2 | +19,4 | +3,5 | +33,1 | +6,7 | 0,33 | 0,44 |
| Sağlamlık A, fen | 13 | 10,9 | −20,8 | +31,3 | +21,4 | +48,8 | +20,2 | 0,14 | 1,00 |
| Sağlamlık D: yıldızlı ülkeler dahil, mat | 17 | 1,4 | −29,8 | +2,4 | +22,6 | +42,9 | +9,5 | 0,22 | 0,56 |
| Sağlamlık D, okuma | 17 | 2,4 | −29,2 | +19,4 | +3,5 | +33,1 | +6,7 | 0,33 | 0,67 |
| Sağlamlık D, fen | 22 | 10,0 | −36,2 | +15,5 | +29,3 | +52,6 | +15,3 | 0,13 | 1,00 |
| Sağlamlık C: tüm stabil katılımcılar, fen | 11 | 2,5 | −68,4 | −27,1 | −32,7 | −16,4 | −36,1 | 1,00 | 0,67 |

Ana ağırlıklar: mat CHE 0,73 / JPN 0,27; okuma JPN 0,79 / ISL 0,11 / CHE 0,10; fen JPN 1,0. Sağlamlık D'de mat PRT 1,0; fen PRT 0,89 / ISR 0,11.

Okuma:
- **2025 açığı bütün arındırılmış OECD spesifikasyonlarında pozitif ve büyük**: matematik +43 ile +71, okuma +33 ile +34, fen +49 ile +53 puan (seviye spesifikasyonunda fen +37,9). 2018'den itibaren açık pozitif; **2015 her spesifikasyonda negatif**: arındırılmış OECD spesifikasyonlarında −9 ile −36, seviye ve tüm-katılımcı spesifikasyonlarında daha da düşük (−34 ile −74). 2015 çukuru sentetik yolun da altında (mod geçişi / gerçek düşüş ile tutarlı), sonrası sentetik yolu aşıyor.
- **Çıkarım gücü zayıf**: p(gap) matematik ve fende 0,11–0,17 (Türkiye dağılımın tepesinde ama 5–8 birimle "anlamlılık" tanım gereği ulaşılamaz); okumada 0,33. p(ratio) fende yüksek çünkü Türkiye'nin fen ön dönemi (2006–2012, +40 puan, kapsam genişleme dönemi) plasebolardan kötü uyuyor; oran-testi bu yüzden Türkiye'yi cezalandırıyor.
- **Kırılganlık**: OECD dışı donörler eklenince fen sonucu tersine dönüyor (QAT ağırlık 1,0: Katar'ın 2006–2012 dik yükselişi Türkiye'nin arındırılmış ön yörüngesine "uyuyor", sonra Katar yükselmeye devam ediyor). Bu, 3–4 ön dönem gözlemiyle arındırılmış eşleştirmenin tek bir sıra dışı donöre ne kadar duyarlı olduğunu gösterir; ana spesifikasyonda OECD kısıtı bu yüzden korunuyor.

## 3. Negatif kontrol ve ikiz vaka

**Macaristan** (kırılma 2010; ön 2003–2009, post 2012–2025; 5–8 donör): ortalama post açığı matematik +0,4, okuma −5,5, fen −11,7; 2025 açıkları +3,7 / −8,4 / −8,8. Yükseliş yok, hafif düşüş: negatif kontrol beklendiği gibi davranıyor.

**Gürcistan**: sentetik kontrol **tanımlanamıyor** — ön dönemde yalnızca 2 gözlem (2009+, 2015; 2015 kâğıt tabanlı) → ön-RMSPE sıfır, 13 donörle her yörünge mükemmel "uyuyor", oran testi anlamsız; ağırlık yine Katar'a (0,69–1,0) gidiyor ve ortalama post açıkları negatif çıkıyor (mat −9,0, okuma −32,0, fen −25,7; 2025 tek yıl: mat +6,9, okuma −28,8, fen −5,6). **Bu sonuç kanıt değil; Gürcistan için SC bu veriyle yapılamaz**, aşağıdaki DiD tarzı karşılaştırma kullanılmalı.

## 4. Callaway–Sant'Anna DiD (`data/derived/did/`)

Tedavi: ERT otokratikleşme epizodu olan ülkeler (ilk tedavi döngüsü = epizot başlangıcından sonraki ilk döngü; TUR 2015, GEO 2018, HUN 2012 proposal'a göre sabitlendi), kontrol: hiç epizot yaşamamış stabil ülkeler; ≥2 ön ve ≥1 post gözlem şartı. Sonuç (`csdid_summary.json`): **havuzlanmış ATT matematik +7,8 (s.h. 6,9), okuma −3,0 (7,9), fen +7,5 (7,0)**; tedavi 24 (mat/okuma) ve 23 (fen), kontrol 28 ülke. Yani otokratikleşen ülkelerin ortalaması yükselmiyor (Brief 3'ün "yalnızca Türkiye ve Gürcistan yükseldi" gözlemiyle tutarlı).

Ülke bazında açıklar (kontrol grubunun aynı döngüdeki ortalamasına göre, ön dönem farkı arındırılmış; `country_did_gaps_*.csv`):

| | 2015 | 2018 | 2022 | 2025 |
|---|---|---|---|---|
| Türkiye mat / okuma / fen | −8 / −26 / −21 | +38 / +27 / +41 | +49 / +27 / +48 | **+63 / +56 / +67** |
| Gürcistan mat / okuma / fen | – | +19 / +5 / +9 | +22 / +8 / +10 | **+54 / +32 / +49** |
| Macaristan mat / okuma / fen | −5 / −12 / −26 | +13 / +10 / −4 | +15 / +16 / +2 | +8 / +9 / −4 |

Sentetik kontrol ile aynı örüntü: Türkiye 2018'den itibaren, Gürcistan 2025'te sıçrıyor; Macaristan düz.

## 5. Mekanizma betimleyicileri (`data/derived/mechanisms/`)

- **OECD'ye göre değişim**: Türkiye 2015→2025 matematik +41,1 (OECD ort. −21,9), okuma +43,8 (−27,6), fen +68,8 (−6,8) → **üç alanda ve üç pencerede (2015→, 2018→, 2022→2025) 37–38 OECD ülkesi içinde 1. sıra** (2015→2025 penceresinde 38, diğerlerinde 37 ülke); tüm katılımcılar içinde 2015→2025'te 1/65–66, 2022→2025'te 5–10/78–79.
- **Plasebo alan (2025)**: OECD ortalamasına göre Türkiye çekirdek alanlar +7,4 (mat −1,5, okuma +11,2, fen +12,4), hesaplamalı problem çözme **−27,1**; "çekirdek − CPS" farkı **+34,5: OECD içinde 1/38, 85 ekonomi içinde 5.** Gürcistan +25,6 (10/85). Ama üstteki dört birim KEN, QCI, AZE, ARM: üçü çok düşük kapasiteli sistem (CPS'te genel zayıflık), biri (QCI) yüksek performanslı alt-ulusal birim → bu örüntü şişmeyle tutarlı ama tek başına ayırt edici değil; puan düzeyine koşullu karşılaştırma gerekir (yapılacak).
- **Kapsam**: Türkiye Coverage Index 3 2025'te 0,72; stabil OECD donörleri 0,86–0,91 (2009'da 0,86, son döngülerde 0,88–0,91). Genel dışlama 2015 %1,1 → 2018 %5,7 → 2022 %5,6.

## 6. Ne gösterilmedi / sınırlar

- Bu tur **mekanizma testi değildir**: mikroveri (yanıt süreleri, atlama, okul-türü bileşimi), hazırlık primi ve 2025 dışlama/yanıt oranları henüz analiz edilmedi. Sonuç "Türkiye'nin yörüngesi olağandışı" düzeyindedir; "şişme" iddiası için §4.3'teki kanallar gerekir.
- Donör havuzu 5–8 ülke: p-değerleri yapısal olarak ≥0,11–0,17. Gevşetilmiş spesifikasyonlar (17–22 donör) işareti koruyor ama büyüklüğü düşürüyor (mat 2025: +71 → +43).
- Ön dönem 3–4 gözlem ve kapsam genişlemesiyle kirli; arındırılmış SC bunu tam çözmez (fen için oran testi Türkiye aleyhine).
- Proposal §4.1'in "yozlaşmış-stabil OECD" alt grubu veride yok; tasarım revize edilmeli (ya OECD dışı donörler kabul, ya kurum ölçütü CPI yerine WGI/V-Dem eşiği).
- Gürcistan SC tanımlanamıyor; DiD tarzı açıklar kullanılmalı.
- Kurumsal sınıflamada "latest" yılı 2024 (2025 alınırsa BEL, ESP, ISL, LTU, NZL ambiguous'a düşer — `SCREEN_README.md`).

## 7. Sonraki adımlar (öncelik sırasıyla)

1. Plasebo alan testini puan düzeyine koşullu yap (CPS açığı ~ çekirdek düzeyi regresyonu; Türkiye'nin artığı).
2. 2025 dışlama/yanıt oranlarını Volume I PDF'inden çek; MESEM/açık öğretim çerçeve kararını Teknik Rapor çıkınca doğrula.
3. Mikroveri: 2015/2018/2022/2025 yanıt-süresi ve atlama göstergeleri (Türkiye vs donörler), okul-türü bileşimi vs MEB kayıtları.
4. Donör kuralını gevşet/gerekçelendir (yıldız kuralı, "ambiguous" tanımı) ve leave-one-out + in-time placebo (sahte kırılma 2009) ekle.
5. Gelbach ayrıştırması ancak 1–3 tamamlanınca.

## 8. Denetim

Opus 4.8 denetimi (2026-09-15): 255 sayı çıktı dosyalarına karşı kontrol edildi, 248 uyuştu; 5 tutarsızlık (fen 2025 bandı, plasebo-alan üst-4 listesi, DiD fen tedavi sayısı, OECD paydası 37/38, donör kapsam alt sınırı) ve 3 yorum uyarısı (QCI nitelemesi, Gürcistan "negatif" ifadesi, 2015 bandının kapsamı) bu sürümde düzeltildi. Hiçbiri ana sonucu değiştirmedi. Tam liste: `analysis/RESULTS_AUDIT.md`.

## 9. Düzeltme notu (2026-09-28, kör denetim; üstteki metin değiştirilmedi)

Kayıt: `04_calisma/kor_denetim_2026-09-28/`. Bu raporun sayıları 2026-09-15 01:07'de yazıldı; `data/derived/synth` ve `did` çıktıları aynı gece 01:33'te yeniden üretildi.

| | Bu rapordaki ifade | Güncel durum |
| :---: | :--- | :--- |
| 🔴 | §4: CS-DiD s.h. 6,9 / 7,9 / 7,0 | `csdid_summary.json`: 7,02 / 7,52 / 6,62 (ATT aynı: +7,8 / −3,0 / +7,5). Fark tohumsuz bootstrap'tan (B = 1000; MC sd 0,16–0,28; \|z\| ≤ 1,74 — analitik hesap, Wolfram; `04_calisma/kor_denetim_2026-09-28/CROSSCHECK_STAGE2.md` §2 T7). `04_cs_did.R`'ye `set.seed(20260928)` eklendi. **29 Eyl: tohumlu koşu Google Colab'da** (Ubuntu 24.04, R 4.6.1, `did` 2.5.1 — yerel ortamla aynı sürümler; `data/derived/did/sessionInfo_colab.txt`): ATT birebir aynı, s.h. **7,31 / 7,91 / 6,63**; t 1,07 / −0,38 / 1,13 → anlamlılık değişmez. Kohort ve ülke açıkları dosyaları eskisiyle aynı; ham koşu `04_calisma/colab_csdid_2026-09-29/` |
| 🔴 | §2 "Ana" satırı = `stable_clean` (fen 7 donör, p .125 / .875) | Makale `stable_all` satırını kullanıyor (5 / 5 / 8 donör; p(gap) .17 / .33 / .22; p(ratio) .33 / .17 / .89). İki satırın 2025 açığı ve ağırlıkları aynı; fark yalnız fen donör sayısı ve p |
| 🟡 | §2 sağlamlık aralığı "mat +43 ile +71" | Makaledeki "dört donör kuralının 16 bileşimi" `23_donor_ablation.py` A merdiveni (`ablation_grid.csv`): mat +30,1…+50,4, okuma +25,2…+34,1, 16/16 pozitif; fen 8/16 negatif. +70,8 ayrı B tarama merdiveninde (4 hücre) ve bu raporun eski `stable_plus_ambiguous` spesifikasyonunda |
| 🟡 | §3 Macaristan fen negatif kontrolü | Ön-RMSPE = 0 (2 ön dönem gözlemi, 8 donör) → oran 314.087, oran testi tanımsız; yalnız açıklar yorumlanabilir |
| 🟡 | §4 ülke bazlı DiD açıkları (TUR +63 / +56 / +67) | Kontrol ortalaması dengesiz kümeden (bileşim döngüden döngüye değişiyor) → bileşime duyarlı; makalede kullanılmıyor |
| 🟢 | §1 "Ferman–Pinotti" | Doğrusu Ferman & Pinto (2021) |

## 10. Dışlama kanalı ve plasebo artığı, 2025 (betik 56; 2026-09-29, ön-kayıtsız)

Kaynak: `data/derived/exclusion_frame/placebo_association_2025.{csv,json}` ← `rankings_2025.csv` (betik 19, TASLAK Teknik Rapor T14.A.1) × `mechanisms/placebo_conditional_2025.csv` (betik 10); uyarı yıldızı: `03_dogrulama/…/OECD_PISA2025_asterisk-caution-notu.pdf` (veri dosyasındaki ad sonu "*" ülke dipnotu, uyarı değil). Neden: Makale 1 v3 T1'i (Cowork, bulgu #22), "plasebo dışlama kanalına kör" bulgusunun yalnız İsveç ve Lüksemburg'a dayandığını gösterdi. **Ön-kayıtsız**; tüm hücreler raporlanır, p-değerleri çoklu karşılaştırma için düzeltilmemiştir.

| | Sonuç |
| :-: | :--- |
| 🟡 | **Tutarlı ilişki yok; işaret örnekleme göre değişiyor.** Spearman ρ (genel dışlama %, artık): tüm katılımcılar (n = 84) doğrusal −0,106 (p 0,335), ikinci derece −0,224 (p 0,040); OECD (n = 38) doğrusal +0,264 (p 0,109), ikinci derece +0,261 (p 0,113). Dört birincil hücreden yalnız biri nominal olarak anlamlı ve o hücre kaygı yönünde (daha çok dışlama, daha düşük artık). Pearson r −0,136 ile +0,275 arası, en küçük p 0,095. Okul içi dışlama oranıyla ρ −0,222 (tüm katılımcılar, ikinci derece; p 0,042) ile +0,087 arası |
| 🟡 | %5 dışlama standardını aşan 25 sistemin 5'i OECD uyarı yıldızlı (Kanada, Hollanda, Yeni Zelanda, Norveç, ABD; Arnavutluk da yıldızlı ama %3,11). **Yıldızsız 20**; 19'unun artığı var (Kürdistan Bölgesi'nin yok). Alttan sıraları (84'te) doğrusal biçimde 6–79, ikinci derecede 5–77. Alt ondalık dilimde (sıra ≤ 8) en az bir biçimde: Lübnan 6/10, İsrail 11/7, Hırvatistan 8/5; iki biçimde de yalnız Hırvatistan. Lübnan'ın %8,78'inin tamamı okul düzeyinde (okul içi 0): OECD notuna göre çatışmadan etkilenen iki il kapsam dışı; bu olağan öğrenci dışlaması değil, bir kapsam kararı. İsveç 43/37, Lüksemburg 76/66 |
| 🟢 | %5 üstü ve altı sistemlerin artık ortancası (üst grup yıldızlıları da içerir): tüm katılımcılar +1,5 / +1,8 (doğrusal, n 24 / 60; MW p 0,894), −0,4 / −0,4 (ikinci derece; p 0,824); OECD +2,9 / −0,8 (doğrusal, n 18 / 20; p 0,048), +1,9 / −0,2 (ikinci derece; p 0,068). OECD'de yüksek dışlamalı sistemlerin artığı nominal olarak daha yüksek (düzeltmesiz, dört grup testinden biri; tüm katılımcılarda fark yok) |
| 🟢 | Türkiye'nin 2025 dışlaması %2,74 (TASLAK; standardın altında); artığı alttan 5./3. (84) |

**Okuma:** Plasebo artığı 2025'te dışlama oranını tutarlı biçimde izlemiyor: ilişki zayıf, işareti örnekleme göre değişiyor, tek nominal anlamlı hücre kaygı yönünde. Bu, "aynı öğrenciler iki alanı da aldığı için dışlama artıkta sönmeli" beklentisiyle tutarlı, ama onu kanıtlamıyor. "İki olgu" anlatımı seçiciydi: yıldızsız %5 üstü sistemlerin bir kısmı en az bir biçimde alt ondalıkta (iki biçimde yalnız Hırvatistan). Onların alt kuyruk konumunun dışlamadan kaynaklandığını bu veri göstermez. Kesitsel ilişki, tek bir sistemin dışlama değişiminin artığını ne kadar oynattığını tanımlamaz.

**T1 (taze bağlam, 29 Eyl 2026, HEAD `e217a5a`, betik kayıtsız):** tüm sayılar bağımsız kodla girdilerden yeniden hesaplandı, 0 uyuşmazlık; T14.A.1 xlsx'e karşı 5 satır birebir; ad eşleşmesi 84/84. Kod notları (uyarı listesinin "Israel" dizgisinde kesilmesi, sessiz yineleme silme ve ortalama alma) giderildi; çıktılar bayt olarak aynı. Dil notları (5) ve Lübnan notu bu bölüme işlendi.
