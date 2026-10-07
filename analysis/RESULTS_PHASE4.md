# Faz 4 — Yöntem memoları (Gemini) değerlendirmesi ve yeni tahminciler: sentetik DiD, matris tamamlama, konformal çıkarım, makro-bölümleme

Tarih: 2026-09-16. Yazan: Claude Fable 5.1 (kod + sentez); memo çıkarımı ve kaynak doğrulaması Opus 4.8; sayı/kod denetimi Opus 4.8 (§8). Her sayı `data/derived/{sdid,mc_conformal,macro_partition}/` çıktılarından; kaynak referansları `claim_check/B6_METHODS_GEMINI_CHECKED.md` defterine bağlı.

## 0. Özet

Başka bir çalışma için hazırlanmış üç yöntem memosu incelendi. Memoların ana gövdesi (derin temsil öğrenmesi, TMLE, nedensel ormanlar) **mikro-birim düzeyinde tedavi** varsayar; bizim tanımlama sorunumuz **tek tedavi birimli ülke paneli** (Türkiye, 8 döngü) olduğu için doğrudan uygulanamaz. Uygulanabilen üç parça alındı ve hesaplandı:

| Yeni tahminci | Kaynak memo | Türkiye 2025 (veya sonrası) etkisi — ana havuz (stabil OECD donörleri) | Çıkarım |
|---|---|---|---|
| Sentetik DiD (Arkhangelsky vd. 2021), taban 2015 | Frontier §3.2 | mat **+45,6** / oku **+20,5** / fen **+46,0** (2018–2025 ortalaması); R `synthdid` ile fark ≤ 0,30 | plasebo SE 7,6 / 5,6 / 12,9; sıra-p 0,17 / 0,17 / 0,11 (N0 = 5–8) |
| Matris tamamlama MC-NNM (Athey vd. 2021) | Frontier §3.1 | 2025 farkı mat **+49,0** / oku **+40,9** / fen **+47,1** | plasebo sırası 1/6, 1/6, 2/9 |
| Konformal çıkarım (Chernozhukov, Wüthrich & Zhu 2021) | Frontier §3 | yalnız-2025 %80 aralığı mat [4, 62], oku [−10, 80], fen [−6, 82] | T = 8 ile en küçük p 0,125: **bilgi vermiyor** |
| Makro-bölümleme (MOB/CTree, Zeileis vd. 2008; Hothorn vd. 2006) + makro-uzay kNN | Partitioning §3 | 2015→2025 üç-alan ortalama değişimi Türkiye **+51,2**; kendi makro-yaprağında (düşük libdem, n=14) artık +49,1, **1/14**; 8 en yakın makro-komşu ortalaması −13,1 (z = 5,2) | tanımlama değil, donör seçiminin veriye bırakıldığı sağlamlık testi |

Sonuç: donör havuzu elle değil veriyle kurulduğunda da, tahminci değiştiğinde de (sentetik kontrol → SDiD → düşük-ranklı tamamlama) Türkiye'nin 2015 sonrası sapması aynı büyüklükte ve aynı yönde. Bu, Faz 3'teki "2015 sonrası hızlanma" çerçevesini güçlendirir; "2013'te temiz kırılma" iddiasını geri getirmez (SDiD'nin 2012-tabanlı penceresi 2015 çukuru yüzünden küçük kalır: +12,8 / +7,5 / +3,3). Küçük N0 ve T yüzünden hiçbir tahminci geleneksel anlamlılık vermez; kanıt "büyüklük + tutarlılık + plasebo sırası" düzeyindedir — proposal buna göre yazılmalıdır.

## 1. Memoların değerlendirmesi

Çıkarım: `docs/methods_memos/gemini_ideas_extraction_opus48.json` (Opus 4.8, 2026-09-16; iki ajan, memo metnine sadık, ekleme yok).

**1.1 "Frontier Causal Inference Architectures" (150 KB).** 16 yöntem: TARNet, Dragonnet, CEVAE, VCNet/ACFR, TMLE, RieszNet/ForestRiesz/Auto-DML, "TDA", "DeepNetTMLE", matris tamamlama, sentetik DiD, "geodesic synthetic control", DEC, hiyerarşik nedensel modeller, MIP hibritleri. Tezi: makro göstergeleri ağaçla bölmek yerine sürekli gizil temsile gömüp yarı-parametrik çift-sağlam tahminci eklemek. **Bize uygulanabilirlik:** yalnız §3 (panel): matris tamamlama ve SDiD — ikisi de uygulandı (§2–3). Derin temsil / TMLE / Riesz yöntemleri, gözlem birimi başına ikili tedavi ve büyük N ister; bizde tedavi ülke düzeyinde ve tek birimdir; mikroveri (öğrenci) düzeyinde ise "tedavi" yok (Türkiye'deki her öğrenci aynı rejimde). Bunlar mekanizma aşamasında ancak öğrenci-düzeyi ikili bir müdahale bulunursa (ör. örneklem okulu olmak — liste gizli) gündeme gelir. **Kaynak kalitesi:** Opus 4.8 çıkarımı sistematik atıf-numarası uyuşmazlığı, geleceğe tarihli arXiv kimlikleri (2601–2607 serisi), yerleşik yöntem gibi sunulan ama 2024–25 arXiv ön-baskısı olan adlandırmalar ("DeepNetTMLE" = Guo, Shen & Li 2024; "TDA" = Li … van der Laan 2025; "geodesic SC" = Kurisu, Zhou, Otsu & Müller 2025; "ACFR" doğrulanmadı — B6-015…017) ve düşük kaliteli kaynaklar (Pyro dokümantasyonu, Hugging Face "daily papers") saptadı. Memodaki hiçbir uygulamalı sayı alınmadı; yalnız kanonik yöntem makaleleri, bağımsız doğrulamadan geçirilerek (§8, B6 defteri) kullanıldı.

**1.2 "Macro-Micro Recursive Partitioning Methodology" (36 KB).** 14 yöntem: HLM, çok-yönlü sabit etkiler, CART, MOB, PALM/GLMM ağaçları, CTree, nedensel ağaç/orman, GRF, DML, küme-sağlam çıkarım, PCA. Önerilen hat: makro endeksleri yalnız bölme değişkeni olarak kullan → boyut indirgeme → DML ile ortogonalleştir → yapraklarda dürüst (honest) tahmin → küme-sağlam varyans. **Bize uygulanabilirlik:** "makro göstergelerle homojen ülke kümeleri kur, kıyası küme içinde yap" fikri, bizim elle kurduğumuz donör havuzunun (V-Dem ERT + CPI eşiği) veriye bırakılmış hâlidir; §5'te MOB, CTree ve Mahalanobis-kNN ile yapıldı. Nedensel orman (GRF) için N ≈ 61 ülke yetersiz (memonun kendi uyarısı: ağaç kararsızlığı, boyut laneti); uygulanmadı. **Kaynak kalitesi:** uygulamalı örneklerden "Macaristan medya-ele geçirme 2010–2025 nedensel orman çalışması, 8–12 puan etki" yalnızca kendi-yüklemeli bir ResearchGate kaydı (hakemli değil, açılamadı — B6-013); "Dünya Bankası 2030 yoksulluk projeksiyonunda MOB" doğru ama kaynak IMF değil Dünya Bankası tahminleri (Lakner, Mahler, Negre & Prydz 2022, *J. Econ. Inequality* 20(3) — B6-014); geleceğe tarihli dergi/arXiv kayıtları var. Bunlar proposal'a alınmadı.

**1.3 Kısa Türkçe not (5 KB).** HLM, CCA, PLS-SEM, Procrustes ve "makro göstergelerle ağaç kurup yapraklarda mikro kıyas" fikri; MOB/nedensel orman önerisi ve iki uyarı (ağaç kararsızlığı, değişken çöplüğü). Uyarılar §5'te doğrudan uygulandı: az sayıda, hipoteze bağlı makro değişken; leave-one-out kararlılık.

## 2. Sentetik fark-farkı (SDiD) — `16_synthetic_did.py`

`synthdid` R paketi CRAN'da değil (yalnız GitHub, synth-inference/synthdid v0.0.9 — B6-012); algoritma makaleden (Arkhangelsky vd. 2021, Alg. 1 ve 4) Python'da birebir uygulandı: ζ = (N1·T1)^{1/4}·σ̂ (σ̂ = kontrol birimlerinin ön-dönem birinci-fark sd'si), kesişimli simpleks birim ağırlıkları + ζ²T0 ridge, kesişimli simpleks zaman ağırlıkları, ağırlıklı DiD; çıkarım = her kontrolün sırayla tedavi sayıldığı plasebo dağılımı (SE = sd, sıra-p). Panel: `_panel_matrix.py` (dengeli seriler; 03_synth ile aynı havuz kuralları).

| Pencere | Havuz | N0 | Matematik τ̂ (SE; p) | Okuma | Fen | Zaman ağırlığı |
|---|---|---|---|---|---|---|
| Sonrası 2018–2025, ön …–2015 | stabil OECD | 5 / 5 / 8 | **+45,6** (7,6; 0,17) | **+20,5** (5,6; 0,17) | **+46,0** (12,9; 0,11) | 2015: 1,00 / 2012: 1,00 / 2015: 0,75 |
| aynı | stabil + belirsiz OECD | 8 / 8 / 13 | +52,8 (9,7; 0,11) | +42,3 (16,7; 0,11) | +56,4 (8,8; 0,07) | 2015: 1,00 / 2015: 0,68 / 2015: 1,00 |
| aynı | tüm katılımcılar (tedavi sınıfları hariç) | 10 / 10 / 18 | +51,8 (11,4; 0,09) | +53,6 (14,2; 0,09) | +57,6 (10,4; 0,05) | 2015: 1,00 |
| Sonrası 2015–2025, ön …–2012 | stabil OECD | 5 / 5 / 8 | +12,8 (7,3; 0,17) | +7,5 (3,5; 0,17) | +3,3 (14,1; 0,56) | 2012: 1,00 / 0,98 / 1,00 |
| aynı | tüm katılımcılar | 10 / 10 / 18 | +12,1 (20,0; 0,55) | +10,1 (17,6; 0,64) | −16,0 (20,8; 0,42) | 2012: 1,00 / 0,56 / 0,99 |

Yıl bazlı etkiler (stabil OECD, ön …–2012): 2015 −20,5 / −31,8 / −37,8; 2018 +18,3 / +14,9 / +9,6; 2022 +17,9 / +8,4 / +10,3; 2025 **+35,7 / +38,3 / +31,2**. Okuma: SDiD zaman ağırlığı 2015'e sıfır, 2012'ye bir verdi (2015 okuma çukuru donörlerin sonrası ortalamasını öngörmüyor); bu yüzden okumada 2018–2025 etkisi (+20,5) diğer iki alandan küçük.

**Referans uygulamayla çapraz doğrulama (`16b_synthdid_crosscheck.R`):** `synthdid` GitHub'dan (`remotes`, saf R) kuruldu; 18 vakanın (3 havuz × 3 alan × 2 pencere) tümünde τ̂ farkı en fazla 0,30 puan (ör. matematik 2018–2025: R 45,50 / Python 45,55; okuma 20,52 / 20,50; fen 46,09 / 45,98), zaman ve birim ağırlıkları aynı (λ 2015 = 1; ω CHE 0,63 / JPN 0,37). Plasebo SE'ler yakın ama birebir değil (R rastgele yeniden örnekleme, Python deterministik leave-one-out): 6,74 / 6,99 / 12,86 vs 7,32 / 7,64 / 14,08 (2015-taban). `data/derived/sdid/r_synthdid_crosscheck.csv`.

Okuma: SDiD'nin zaman ağırlıkları veriyle 2015'i (fen/mat) taban seçiyor — yani tahminci kendiliğinden "2015 sonrası" karşılaştırmasına gidiyor; bu, Faz 3 §0'daki "2015 kesintisi + sonrası hızlanma" tanısıyla örtüşüyor. 2012-tabanlı pencere 2015 çukurunu sonrası dönemin içine aldığı için ortalama etkiyi küçültüyor. SC-tipi (yalnız ω) ve DiD-tipi (yalnız λ) karşılaştırma tahminleri `sdid_results.csv`'de; ana havuzda (stabil OECD) üçü de aynı işaret; tek istisna ikincil fen / tüm-katılımcılar hücresi (2015–2025 penceresi: SDiD −16,0, SC-tipi −9,4, DiD-tipi +20,9). Plasebo SE `sd(ddof=1)` ile hesaplanır; makale/synthdid'in 1/B konvansiyonuna göre ×1,07 (N0 = 8) … ×1,12 (N0 = 5) daha büyük, yani muhafazakâr.

## 3. Matris tamamlama (MC-NNM) — `17_matrix_completion_conformal.py` (A)

Türkiye'nin 2015–2025 hücreleri eksik sayılır; düşük-ranklı L + birim + zaman etkisi, nükleer-norm cezası (soft-impute), λ donör hücrelerinin %15'inin rastgele maskelendiği 5 tekrarlı Monte Carlo çapraz doğrulamayla; plasebo: her donör sırayla tedavi edilmiş.

| Havuz | N0 | 2025 farkı mat / oku / fen | Sonrası ortalaması | Plasebo sırası (p) | Ön-dönem RMSE | rank(L) |
|---|---|---|---|---|---|---|
| stabil OECD | 5 / 5 / 8 | **+49,0 / +40,9 / +47,1** | +24,5 / +11,4 / +18,8 | 1/6 (0,17) / 1/6 (0,17) / 2/9 (0,22) | 2,1 / 2,1 / 3,7 | 3 / 3 / 5 |
| stabil + belirsiz OECD | 8 / 8 / 13 | +60,1 / +47,9 / +53,5 | +30,7 / +15,0 / +21,5 | 1/9 (0,11) / 2/9 (0,22) / 2/14 (0,14) | 2,0 / 1,2 / 6,8 | 5 / 5 / 4 |
| tüm katılımcılar | 10 / 10 / 18 | +50,4 / +46,1 / +82,2 | +24,2 / +13,1 / +42,9 | 2/11 (0,18) / 3/11 (0,27) / 6/19 (0,32) | 1,6 / 3,2 / 1,3 | 6 / 5 / 6 |

Sentetik kontrolle karşılaştırma (aynı havuz, 2025): SC +50,4 / +34,1 / +48,8 vs MC +49,0 / +40,9 / +47,1 (stabil OECD). Fen "tüm katılımcılar" havuzunda SC (−16,4) ile MC (+82,2) ayrışıyor: SC dışbükey-örtü kısıtıyla OECD dışı düşük-düzeyli birimlere ağırlık veriyor, MC düşük-ranklı yapıyı tüm panelden öğreniyor — Faz 3 §2'deki "fen OECD kısıtı olmadan işaret değiştirir" bulgusunun tahminci-bağımlı olduğunu gösterir; ana spesifikasyon OECD havuzu olarak kalır.

## 4. Konformal çıkarım — `17_…` (B) ve Python–R çapraz doğrulaması (C)

Python'da ortalamadan arındırılmış simpleks SC (SLSQP) R `Synth` çıktısını 6 vakada 0,00 farkla üretti (`r_vs_python_sc.csv`) — Faz 2–3 sentetik kontrolleri bağımsız uygulamayla doğrulanmış oldu.

Konformal test (CWZ 2021): H0 altında tüm döngülerle uydur, kalıntıları hareketli-blok permütasyonuyla karıştır, S = sonrası kalıntıların mutlak ortalaması. T = 8 (fen 7) olduğu için permütasyon dağılımı 8 noktalı; **erişilebilir en küçük p = 0,125** (fen 0,143). Türkiye tam bu en küçük değeri alıyor (2015–2025 sabit etki H0 ve yalnız-2025 matematik için); okuma/fen yalnız-2025 için p = 0,25 / 0,29. %80 aralıkları (yalnız-2025, stabil OECD; ızgara −40…200, 2 puan adım): matematik **[4, 62]**, okuma [−10, 80], fen [−6, 82]; 2018–2025 sabit etki için matematik [−22, 168], okuma [−38, 142], fen ızgaranın tamamı (sınırsız); 2015–2025 sabit etki için üçü de ızgaranın tamamı. Verdikt: konformal çıkarım bu T ile **bilgi vermiyor**; proposal'da "kesin çıkarım yöntemi olarak denendi, tasarımın T sınırı yüzünden ayırt edici değil" diye yazılır. Bu, memonun "SDiD/MC daha güçlü" iddiasını değil, panelin kısa olduğunu gösterir.

## 5. Makro-bölümleme ve makro-komşular — `18_macro_partition.R`

Çerçeve: 2015 ve 2025'te üç alanı olan ve makro değişkenleri eksiksiz 61 ülke; sonuç = 2015→2025 üç-alan ortalama değişimi; bölme/eşleme değişkenleri: V-Dem libdem 2013, Δlibdem 2013→son, CPI ortalaması 2013–2025, WGI yolsuzluk kontrolü 2015, Coverage Index 3 (2015), OECD, 2015 kâğıt-mod bayrağı; yaprak modeli: değişim ~ 2015 düzeyi.

- **MOB (lmtree, α = 0,10, Bonferroni, min yaprak 10):** bölünme yok — makro değişkenler, düzey-koşullu değişimin parametrelerini anlamlı bölmüyor (Türkiye çıkarılınca da tek yaprak). Not: `lmtree` ve Mahalanobis-kNN, bölme değişkenlerinin tamamı eksiksiz olan **40** ülke üzerinde kurulur (21 ülkede Coverage Index 3 (2015) yok); `results.json`'daki leaf_n = 61 tahmin ataması sayısıdır. Tüm 61 ülkede düzey-koşullu artık (yalnız 2015 düzeyi ile, kapsam gerekmez): Türkiye **+59,8, 1/61** (eğim −0,148).
- **CTree (α = 0,10, min 8):** 3 yaprak. İlk bölünme **libdem 2013 ≤ 0,456** (n = 14, ortalama değişim +2,1: ALB ARE DOM GEO HKG LBN MEX MKD MNE QAT SGP THA TUR XKX); üstünde kapsam 2015 ≤ 0,906 (n = 20, −14,6) / > 0,906 (n = 27, −23,0). Türkiye kendi (düşük-demokrasi) yaprağında artık **+49,1, 1/14**; ikinci Katar +13,5, üçüncü BAE +13,1 (ham 2015→2025 değişimleri +15,6 / +15,2); Gürcistan aynı yaprakta 0,0.
- **Makro-uzayda en yakın komşular (Mahalanobis, 5 makro değişken, 40 eksiksiz ülke):** k = 8 → GEO MEX ISR HUN CAN GBR AUT JPN (ikiz vaka ve negatif kontrol veriden çıkıyor). Türkiye +51,2 vs komşu ortalaması −13,1 (sd 12,5), **z = 5,15, 1/9**; alan bazında komşu ortalamaları mat −15,4 / oku −20,5 / fen −3,4. k = 12: z = 5,30, 1/13.
- Odak ülkeler (2015→2025, mat/oku/fen): Türkiye +41,1 / +43,8 / +68,8; Gürcistan +12,5 / −17,1 / +11,0; Macaristan −17,3 / −17,2 / +3,2.

Verdikt: makro benzerlikle kurulan her kıyas grubunda Türkiye tek başına uçta. Bu bir nedensel tanımlama değildir (makro değişkenler tedaviyi de tanımlıyor); elle kurulan donör havuzuna karşı "seçim ustalığı" itirazını kapatır.

## 6. Tasarım ve iddia üzerindeki net etki

1. **Tahminci-bağımsızlık:** SC (+50/+34/+49), SDiD 2015-taban (+46/+21/+46), MC (+49/+41/+47), makro-komşu farkı (+64 üç-alan ortalaması: 51,2 − (−13,1)) — aynı büyüklük sınıfı, aynı işaret.
2. **Zamanlama:** SDiD zaman ağırlıkları 2015'i taban seçiyor; 2012-tabanlı etki küçük. Kanıt "2015 sonrası hızlanma" için; "2013 kırılma anı" için değil. Proposal §4.1 çapa cümlesi buna göre yazılmalı.
3. **Çıkarım gücü:** N0 = 5–18, T = 7–8: hiçbir yöntem p < 0,05 vermiyor (en iyi: SDiD tüm katılımcılar fen 0,05; MC stabil+belirsiz mat 0,11). Konformal test bilgi vermiyor. Proposal'da anlamlılık dili değil, "plasebo dağılımının kuyruğu + tutarlılık" dili kullanılmalı; asıl ayırt edici kanıt mekanizma tarafında (Faz 3 §5, §5c, §7–8).
4. **Memolardan alınmayanlar:** derin temsil/TMLE/GRF (mikro tedavi yok, N küçük), geodesic SC ve adlandırılmış ama doğrulanamayan mimariler, memoların uygulamalı örnekleri (doğrulama §8/B6).

## 7. Sırada

1. Artırılmış SC (Ben-Michael, Feller & Rothstein 2021): `augsynth` derleyici istiyor; ridge-ASCM Python'da yazılabilir (SC ağırlıkları + sonuç modeli sapma düzeltmesi).
2. Öğrenci düzeyinde ikili bir müdahale bulunursa (örneklem okulu listesi, çalıştay katılımı) memonun DML/GRF hattı mekanizma aşamasında uygulanabilir.
3. 2012 yaratıcı problem çözme (kırılma öncesi plasebo alan) — 2012 mikroverisi indirilmedi.
4. Bu raporun Opus 4.8 denetimi → §8.

## 8. Denetim kaydı

Opus 4.8 denetimi (2026-09-16, üç bağımsız ajan; tam metin `analysis/RESULTS_PHASE4_AUDIT.md`): §2/SDiD 85/85 sayı; algoritma Arkhangelsky vd. (2021) Alg. 1 ve 4 ile birebir (kapalı-biçim τ̂ kanonik çift-doğrusal formla 18/18 hücrede |fark| < 1,5e-13); tek metin düzeltmesi "üçü de aynı işaret" → ana havuzla sınırlandı; plasebo SE ddof=1 muhafazakârlığı belgelendi. §3–4/MC-konformal 96/96 sayı; kod Athey vd. 2021 soft-impute ve CWZ 2021 hareketli-blok testine sadık; düzeltme: 2018–2025 aralıkları yalnız fen için sınırsız (mat/oku sınırlı) → yazıldı; λ seçimi "5-katlı" değil 5 tekrarlı Monte Carlo holdout → betik ve metin düzeltildi; glob sıralaması sağlamlaştırıldı. §5/makro-bölümleme 74/76; düzeltme: Katar/BAE için ham değişim yerine artık (+13,5 / +13,1) yazıldı; MOB ve kNN'nin 40 eksiksiz ülke üzerinde kurulduğu (Coverage 2015 eksik 21 ülke) açıkça yazıldı, betik artık kullanılan n'i raporluyor; N = 61 = 62 (2015 & 2025 üç alan) − MAC (kurumsal taramada yok). Kaynak doğrulaması B6: 11/11 kanonik makale VERIFIED. Ek: `synthdid` referans uygulamasıyla çapraz doğrulama 18/18 (maks |Δτ̂| 0,30).
