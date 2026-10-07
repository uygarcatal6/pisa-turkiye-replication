# RESULTS — Faz 6: ek analiz istekleri A1, A3, A9, A10, sabit kohort bandı, makale Şekil 1 (25 Eylül 2026)

Yazan: Claude Opus 5.5 (Cowork), yazarın isteğiyle · Betikler `analysis/34`–`39` · Makale etiketleri [E34]–[E39] · Tablolar çıktı dosyalarından betikle üretildi (elle sayı yok).

| | Bulgu | Kaynak |
| :---: | :--- | :--- |
| 🔴 | **A1:** 2003→2015 Türkiye'nin konumu kötüleşmiyor; 2015→2025 artık 18,4–22,0 puan düşüyor. OECD'de 35 sistemin 1.–3.'sü (RMSE birimi p 0,029–0,086); tüm katılımcılarda puanda 3.–4./47, önceden belirlenen RMSE biriminde 12.–14./47. | §1 |
| 🔴 | **A3:** önceden belirlenen programlama maruziyeti (PROG) artığın hiçbirini açıklamıyor (%100,3–100,8 kalıyor); okul BİT erişimi (ICTSCH, opsiyonel anket) OECD alt kümesinde (24) örneklem içinde yaklaşık yarısını, Türkiye dışarıda tahmin edilince dörtte birini açıklıyor (Türkiye endekste en altta, kaldıraç 0,40). | §2 |
| 🟡 | **A9:** üç ayrı regresörle Türkiye'nin konumu değişmiyor (2003: 2./36; 2025: 3./84, OECD'de 1./38). | §3 |
| 🟡 | **A10:** 2012 ülke artıklarımız OECD Tablo V.2.6 göreli performansıyla r = 0,958 (41 sistem), OECD üyelerinde 0,981; Türkiye bizde 13., OECD'de 15. | §4 |
| 🟡 | **Kohort bandı:** uç sınır (+93,2 / +99,8 / +90,2) dışarıdakilerin kuyruktaki yerine duyarsız (alt %10: +89,2…; alt çeyrek: +81,6…); yalnız seçilim yoksa gözlenenin altına iniyor (+13,4 / +25,6 / +13,9). | §5 |
| 🔴 | **Kaynakça:** önceki `KAYNAKCA_APA6.md`'de 8 kayıt yanlış esere ya da var olmayan DOI'ye gidiyordu; düzeltildi. | §6 |

**Legend:** 🔴 makalenin iddiasını değiştiren · 🟡 doğrulama/sağlamlık.

---

## 1. A1 — koşullu artığın döngüler arası değişimi [E34]

`34_a1_residual_change.py` → `data/derived/placebo_backbone/residual_change{.csv,_summary.json}`. Birincil ölçü Δ RMSE birimi; sıra alttan (1 = en olumsuz değişim); p = sıra/N (tek yönlü). "Ortak yeniden uyum" post hoc'tur (aşağıda Ön kayıt notu).

| Çift | Spes. | N | Δ RMSE birimi (sıra; p) | Δ puan (sıra; p) | Δ yüzdelik (sıra) | Ortak yeniden uyum Δ RMSE (sıra; p) | Macaristan Δ puan (sıra) |
| :--- | :--- | ---: | :--- | :--- | :--- | :--- | :--- |
| 2003->2012 | all/linear | 27 | +1.34 (25/27; 0.926) | +9.50 (18/27; 0.667) | +28.9 (21/27) | +0.70 (19/27; 0.704) | -34.0 (1/27) |
| 2003->2012 | all/quadratic | 27 | +1.36 (24/27; 0.889) | +10.64 (19/27; 0.704) | +36.2 (22/27) | +0.70 (19/27; 0.704) | -32.8 (1/27) |
| 2003->2012 | oecd/linear | 23 | +0.89 (15/23; 0.652) | +4.94 (12/23; 0.522) | +21.7 (16/23) | +0.61 (14/23; 0.609) | -35.8 (1/23) |
| 2003->2012 | oecd/quadratic | 23 | +0.94 (17/23; 0.739) | +6.07 (14/23; 0.609) | +21.9 (17/23) | -0.90 (6/23; 0.261) | -34.2 (1/23) |
| 2003->2015 | all/linear | 32 | +0.56 (21/32; 0.656) | +3.53 (21/32; 0.656) | +7.9 (20/32) | +0.64 (21/32; 0.656) | -19.2 (2/32) |
| 2003->2015 | all/quadratic | 32 | +0.38 (21/32; 0.656) | +2.58 (21/32; 0.656) | +7.9 (20/32) | +0.49 (22/32; 0.688) | -16.2 (2/32) |
| 2003->2015 | oecd/linear | 27 | +0.48 (17/27; 0.630) | +2.22 (17/27; 0.630) | +19.5 (17/27) | +1.15 (24/27; 0.889) | -20.3 (2/27) |
| 2003->2015 | oecd/quadratic | 27 | +0.07 (17/27; 0.630) | -1.04 (14/27; 0.519) | -0.9 (14/27) | +0.65 (20/27; 0.741) | -15.0 (4/27) |
| 2003->2025 | all/linear | 36 | +0.12 (17/36; 0.472) | -15.37 (2/36; 0.056) | +3.2 (16/36) | -1.03 (7/36; 0.194) | -4.9 (10/36) |
| 2003->2025 | all/quadratic | 36 | -0.29 (12/36; 0.333) | -19.39 (2/36; 0.056) | +0.8 (17/36) | -1.04 (5/36; 0.139) | -10.6 (7/36) |
| 2003->2025 | oecd/linear | 30 | -1.66 (3/30; 0.100) | -19.80 (1/30; 0.033) | -0.7 (14/30) | -1.89 (3/30; 0.100) | -9.5 (6/30) |
| 2003->2025 | oecd/quadratic | 30 | -1.62 (3/30; 0.100) | -19.45 (1/30; 0.033) | -4.0 (13/30) | -1.85 (1/30; 0.033) | -8.4 (7/30) |
| 2012->2015 | all/linear | 36 | -0.78 (10/36; 0.278) | -5.97 (15/36; 0.417) | -21.1 (10/36) | -0.51 (11/36; 0.306) | +14.7 (34/36) |
| 2012->2015 | all/quadratic | 36 | -0.98 (9/36; 0.250) | -8.07 (12/36; 0.333) | -28.4 (10/36) | -0.77 (10/36; 0.278) | +16.6 (34/36) |
| 2012->2015 | oecd/linear | 26 | -0.42 (9/26; 0.346) | -2.72 (12/26; 0.462) | -2.1 (13/26) | +0.02 (12/26; 0.462) | +15.5 (26/26) |
| 2012->2015 | oecd/quadratic | 26 | -0.87 (7/26; 0.269) | -7.11 (11/26; 0.423) | -22.9 (8/26) | -0.49 (8/26; 0.308) | +19.1 (26/26) |
| 2012->2025 | all/linear | 40 | -1.22 (6/40; 0.150) | -24.87 (6/40; 0.150) | -25.8 (9/40) | -1.66 (4/40; 0.100) | +29.0 (36/40) |
| 2012->2025 | all/quadratic | 40 | -1.65 (4/40; 0.100) | -30.03 (4/40; 0.100) | -35.5 (7/40) | -1.76 (4/40; 0.100) | +22.2 (36/40) |
| 2012->2025 | oecd/linear | 28 | -2.55 (2/28; 0.071) | -24.74 (3/28; 0.107) | -22.4 (9/28) | -2.53 (2/28; 0.071) | +26.4 (27/28) |
| 2012->2025 | oecd/quadratic | 28 | -2.56 (2/28; 0.071) | -25.52 (2/28; 0.071) | -25.9 (8/28) | -2.53 (2/28; 0.071) | +25.8 (27/28) |
| 2015->2025 | all/linear | 47 | -0.44 (14/47; 0.298) | -18.90 (4/47; 0.085) | -4.7 (20/47) | -1.18 (7/47; 0.149) | +14.3 (38/47) |
| 2015->2025 | all/quadratic | 47 | -0.67 (12/47; 0.255) | -21.96 (3/47; 0.064) | -7.1 (17/47) | -1.09 (10/47; 0.213) | +5.6 (31/47) |
| 2015->2025 | oecd/linear | 35 | -2.13 (1/35; 0.029) | -22.02 (2/35; 0.057) | -20.2 (9/35) | -2.13 (1/35; 0.029) | +10.8 (29/35) |
| 2015->2025 | oecd/quadratic | 35 | -1.69 (3/35; 0.086) | -18.41 (3/35; 0.086) | -3.1 (15/35) | -1.68 (3/35; 0.086) | +6.6 (23/35) |

Okuma: tüm-katılımcı RMSE 2015'te 10,7, 2025'te 19,4 — RMSE birimindeki değişimi payda sönümlüyor; puan ve OECD kümesi uç kuyruğu veriyor. R2'nin ön taahhüdü ("28–40 sistemde son iki-üç"): OECD kümesinde karşılanıyor, tüm katılımcılarda puanda sınırda, önceden belirlenen RMSE ölçüsünde karşılanmıyor.

## 2. A3 — 2025 artığına bilişim maruziyeti eş değişkeni [E35]

`35_a3_ict_covariate_2025.py` → `data/derived/mechanisms/ict_covariate_2025{.csv,_summary.json}`; ülke düzeyi eş değişkenler `data/derived/cache/ict2025_country.csv` (PUF `CY09_MS_STU_PUF.zip`, 755.721 öğrenci, 90 sistem). Doğrulama: PV1–10CMPS ağırlıklı ortalaması 83 sistemde panelin `cps2025_mean` değeriyle en çok 0,003 puan farklı. Türkiye: PROG 0,391 (alttan 28/83), ROBOT 0,305 (38/83), ICTSCH 0,091 (9/44), ICTRES −1,001 (17/51), CPPK 490,7 (50/83).

| Kapsam/spes. | Eş değişken | n | Katsayı (SE) | TUR artık X'siz | X'li | Kalan pay | Sıra |
| :--- | :--- | ---: | :--- | ---: | ---: | ---: | :--- |
| all/linear | PROG | 83 | -13.345 (20.217) | -31.76 | -32.01 | 1.008 | 5→5 |
| all/linear | ROBOT | 83 | -25.428 (23.867) | -31.76 | -31.29 | 0.985 | 5→5 |
| all/linear | ICTSCH | 44 | 20.484 (10.122) | -30.36 | -27.85 | 0.917 | 3→2 |
| all/linear | ICTRES | 51 | 2.813 (5.851) | -31.21 | -28.73 | 0.921 | 5→5 |
| all/linear | CPPK | 83 | 0.481 (0.164) | -31.76 | -24.78 | 0.780 | 5→6 |
| all/linear | PROG+ICTRES | 51 | -37.692, 3.603 (31.915, 5.865) | -31.21 | -30.16 | 0.967 | 5→5 |
| all/quadratic | PROG | 83 | -12.333 (18.682) | -35.09 | -35.31 | 1.006 | 3→3 |
| all/quadratic | ROBOT | 83 | -14.416 (22.347) | -35.09 | -34.75 | 0.990 | 3→3 |
| all/quadratic | ICTSCH | 44 | 7.54 (12.046) | -34.47 | -32.88 | 0.954 | 1→1 |
| all/quadratic | ICTRES | 51 | -3.673 (5.864) | -34.93 | -38.48 | 1.102 | 3→3 |
| all/quadratic | CPPK | 83 | 0.382 (0.156) | -35.09 | -29.17 | 0.831 | 3→4 |
| all/quadratic | PROG+ICTRES | 51 | -30.078, -2.843 (29.876, 5.92) | -34.93 | -39.32 | 1.126 | 3→3 |
| oecd/linear | PROG | 38 | 3.989 (21.623) | -33.49 | -33.58 | 1.003 | 1→1 |
| oecd/linear | ROBOT | 38 | 2.768 (30.657) | -33.49 | -33.63 | 1.004 | 1→1 |
| oecd/linear | ICTSCH | 24 | 74.491 (28.974) | -31.13 | -14.54 | 0.467 | 1→3 |
| oecd/linear | ICTRES | 13 | 12.948 (8.772) | -30.56 | -15.24 | 0.499 | 1→2 |
| oecd/linear | CPPK | 38 | 0.423 (0.135) | -33.49 | -25.86 | 0.772 | 1→2 |
| oecd/linear | PROG+ICTRES | 13 | -157.297, 13.751 (82.151, 7.806) | -30.56 | -9.79 | 0.320 | 1→3 |
| oecd/quadratic | PROG | 38 | 5.769 (21.997) | -32.95 | -33.05 | 1.003 | 1→1 |
| oecd/quadratic | ROBOT | 38 | 6.28 (31.301) | -32.95 | -33.25 | 1.009 | 1→1 |
| oecd/quadratic | ICTSCH | 24 | 74.633 (29.789) | -29.72 | -14.53 | 0.489 | 1→3 |
| oecd/quadratic | ICTRES | 13 | 18.692 (7.976) | -30.15 | -7.53 | 0.250 | 1→2 |
| oecd/quadratic | CPPK | 38 | 0.439 (0.135) | -32.95 | -24.73 | 0.751 | 1→2 |
| oecd/quadratic | PROG+ICTRES | 13 | -136.996, 18.28 (79.861, 7.241) | -30.15 | -4.28 | 0.142 | 1→3 |

Not: OECD'de PROG+ICTRES ve ICTRES modelleri 13 gözlemde 4–5 parametre taşıyor; yorum dışı.

**Ek (sonradan, T1 bulgusu üzerine; `loo_turkiye_posthoc` bloğu):** Türkiye'nin kaldıracı ve Türkiye dışarıda tahmin edildiğinde (örneklem dışı) kalan pay.

| Kapsam/spes./X | n | TUR artık X'siz (dışarıda) | X'li (dışarıda) | Kalan pay | TUR kaldıracı (ortalama) |
| :--- | ---: | ---: | ---: | ---: | :--- |
| oecd/linear/ICTSCH | 24 | −32.49 | −24.30 | 0.748 | 0.402 (0.125) |
| oecd/quadratic/ICTSCH | 24 | −31.85 | −24.36 | 0.765 | 0.402 (0.167) |
| oecd/linear/ICTRES | 13 | −34.42 | −45.67 | 1.327 | 0.666 (0.231) |
| oecd/quadratic/ICTRES | 13 | −34.03 | −40.23 | 1.182 | 0.620 (0.308) |
| all/linear/ICTSCH | 44 | −31.15 | −28.74 | 0.923 | 0.031 (0.068) |
| all/quadratic/ICTSCH | 44 | −35.70 | −34.99 | 0.980 | 0.060 (0.091) |
| oecd/linear/PROG | 38 | −34.45 | −34.62 | 1.005 | 0.030 (0.079) |

Okuma: OECD alt kümesinde ICTSCH'nin "yarısını açıklıyor" sonucu büyük ölçüde Türkiye'nin kendi noktasından geliyor (endekste 24'ün en altı: 0,091, sonraki 0,184); Türkiye dışarıda tahmin edilince %75–77 kalıyor. ICTRES'in etkisi Türkiye dışarıdayken tamamen kayboluyor.

## 3. A9 — üç çekirdek alanı ayrı regresör (doğrusal) [E36]

`36_a9_three_regressor.py` → `data/derived/mechanisms/three_regressor{.csv,_summary.json}`. Skaler çekirdeğin yeniden kurulumu makale dosyalarıyla birebir (maks. fark 0,0).

| Döngü/kapsam | n | Skaler: TUR artık (sıra), RMSE | Üç regresör: TUR artık (sıra), RMSE | b_M / b_O / b_F |
| :--- | ---: | :--- | :--- | :--- |
| 2003/all | 36 | -16.4 (1/36), 9.31 | -15.1 (2/36), 7.38 | 0.8 / -0.018 / 0.265 |
| 2003/oecd | 30 | -13.7 (1/30), 9.29 | -11.5 (2/30), 6.92 | 0.848 / -0.039 / 0.278 |
| 2012/all | 41 | -6.9 (13/41), 16.52 | -6.3 (15/41), 16.2 | 0.672 / 0.452 / -0.16 |
| 2012/oecd | 28 | -8.8 (7/28), 15.02 | -7.8 (8/28), 14.94 | 0.714 / 0.356 / -0.149 |
| 2015/all | 47 | -12.9 (5/47), 10.7 | -10.9 (6/47), 9.6 | -0.102 / 0.181 / 0.931 |
| 2015/oecd | 35 | -11.5 (8/35), 11.49 | -10.1 (5/35), 10.11 | -0.181 / 0.235 / 0.974 |
| 2025/all | 84 | -31.8 (5/84), 19.38 | -37.2 (3/84), 19.23 | 0.059 / 0.344 / 0.616 |
| 2025/oecd | 38 | -33.5 (1/38), 10.7 | -32.1 (1/38), 10.35 | 0.375 / -0.05 / 0.494 |

## 4. A10 — 2012 artıkları ↔ OECD Cilt V Tablo V.2.6 [E37]

`37_a10_oecd_relative_ps2012.py` → `oecd_vol5_table_v2_6_part1.csv` (44 sistem, PDF'den `pdftotext -layout` ile ayrıştırıldı), `a10_oecd_relative_2012{.csv,_summary.json}`. OECD ölçüsü: öğrenci düzeyi, katılımcı ülkelerin havuzlanmış örnekleminde matematik, okuma, fen ve kareleri ile etkileşimleri üzerine regresyon (tablo dipnotu 2; Cilt V s. 68–70); ülke değeri fiili − beklenen farkın ortalaması. Bizim 2012 örneklemimizde İngiltere, Kıbrıs, Şanghay yok (ortak 41). "oecd" kapsamı güncel üyeliktir (Kolombiya dahil).

| Spes. | n | Pearson r | Spearman ρ | Ort. mutlak fark | Eğim | TUR bizim (sıra) | TUR OECD (SE; sıra) |
| :--- | ---: | ---: | ---: | ---: | ---: | :--- | :--- |
| all/linear | 41 | 0.958 | 0.947 | 10.0 | 0.95 | -6.88 (13) | -14 (1.9; 15) |
| all/quadratic | 41 | 0.949 | 0.937 | 10.04 | 0.934 | -5.02 (16) | -14 (1.9; 15) |
| oecd/linear | 28 | 0.981 | 0.974 | 8.04 | 0.991 | -8.75 (7) | -14 (1.9; 9) |
| oecd/quadratic | 28 | 0.967 | 0.95 | 8.04 | 0.969 | -7.43 (8) | -14 (1.9; 9) |

Düzeltme: makale taslağı OECD ölçüsünü "ülke içinde öğrenci düzeyinde" diye anlatıyordu; tablo notu ve s. 68 havuzlanmış uluslararası örneklemi söylüyor — metin düzeltildi.

## 5. Sabit kohort bandı, Türkiye 2003→2012 [E38]

`38_cohort_band.py` → `data/derived/ontrend/cohort_band{.csv,_summary.json}`. E1 = kohortun üst 0,36 payının ortalaması; S(q): kapsam dışındakiler aynı döngüde kapsanan dağılımın q-yüzdeliği altındaki kısmı gibi dağılır (q = 0 [E32]'yi birebir yeniden üretiyor: maks. fark 0,00000). E2 = tüm kohortun ortalaması, dışarıdakilere kapsanan dağılımın p-yüzdeliği atanarak. Değişim (SE), BRR + Rubin.

| Alan | Gözlenen | E1 q=0 (uç) | q=0,10 | q=0,25 | q=0,50 | q=1 (seçilim yok) | E2 p=0,10 | E2 p=0,25 |
| :--- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| MATH | +24.6 (8.3) | +93.2 (9.7) | +89.2 (9.7) | +81.6 (9.8) | +63.7 (10.0) | +13.4 (14.0) | +68.9 (6.5) | +50.2 (6.9) |
| READ | +34.5 (7.2) | +99.8 (7.8) | +95.7 (7.9) | +87.7 (8.0) | +70.4 (8.1) | +25.6 (10.6) | +74.7 (6.4) | +56.8 (6.8) |
| SCIE | +29.2 (7.1) | +90.2 (7.8) | +86.7 (7.8) | +79.7 (7.9) | +63.3 (8.2) | +13.9 (11.4) | +70.2 (5.8) | +54.1 (6.1) |

Neden 2012 değeri q ≤ 0,474'te sabit: 2012'de tutulan pay 0,526; dışarıdakiler kapsanan dağılımın yarısının altındaysa kohortun üst %36'sına giremez. Ara senaryolar yalnız 2003 tarafını (kapsanan dağılımın altıyla örtüşmeyi) değiştiriyor.

## Ön kayıt notu (neyin önceden, neyin sonradan belirlendiği)

| Analiz | Önceden | Sonradan (açıkça) |
| :--- | :--- | :--- |
| A1 | Birincil Δ RMSE birimi, ikincil puan ve yüzdelik; altı çiftin hepsi; sıra alttan | Ortak sistemlerde yeniden uyum (payda sorununu göstermek için) |
| A3 | Birincil PROG (ST436Q07DA ≥ "Sometimes"); ikinciller ROBOT, ICTSCH, ICTRES, CPPK, PROG+ICTRES | PUF kod eşlemesi (TAP→TWN, KSV→XKX; ilk koşuda 81 → 83 sistem); ICTRES'in dar kapsamı koşudan sonra görüldü |
| A9 | Doğrusal, aynı örneklemler | — |
| A10 | Birincil tüm/doğrusal ↔ OECD sütun 1 | Tablo ayrıştırılırken Türkiye satırı (−14) görüldü, karşılaştırma sonucu görülmeden |
| Kohort | E1/S(q) ve E2 tanımları; q ≤ 0,474'te 2012 değerinin sabit kalacağı hesaptan önce türetildi | — |
