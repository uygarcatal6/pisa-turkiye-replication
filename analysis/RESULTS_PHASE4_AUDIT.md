# RESULTS_PHASE4 denetimi — Opus 4.8 (2026-09-16)

Workflow `pisa-audit-phase4` (üç bağımsız ajan; yalnız okuma; betikler yeniden çalıştırılıp çıktılar bayt-bayt karşılaştırıldı). Bulunan düzeltmeler RESULTS_PHASE4 §8'de özetlenip aynı gün uygulandı. Ham çıktı: `analysis/_phase4_audit_raw.json`.

## SCOPE A denetimi — Sentetik DiD (`16_synthetic_did.py`, RESULTS_PHASE4.md §2 + §0/§6 SDiD hücreleri)

Denetleyen: Opus 4.8. Kaynaklar açıldı: script (kod gövdesi satır 46–126, md5 `6b2f6613…`, oturum sırasında yalnız docstring/satır 4–5,21 değişti; algoritma değişmedi), `data/derived/sdid/sdid_results.csv` (18 satır, yeniden üretilerek bayt-bayt aynı), `_panel_matrix.py` (yeniden çalıştırıldı), AER makalesi arXiv HTML `1812.09970v4` (Alg. 1 ve dipnot 3 birebir okundu).

### 1) Sayı denetimi (§2 tablosu + metin → CSV)

Tüm §2 tablo hücreleri, satır-40 yıl-bazlı etkileri ve §0/§6 SDiD rakamları CSV'den **aynen** doğrulandı (belirtilen yuvarlamada tam eşleşme). Temsili satırlar:

| Konum | Rapor iddiası | CSV / yeniden hesap | Verdikt |
|---|---|---|---|
| §2 R1 post2018 stabil OECD | mat +45,6 (7,6; 0,17) N0=5 | 45.55 / 7.64 / 0.167 / 5 | ✔ |
| §2 R1 | oku +20,5 (5,6; 0,17); fen +46,0 (12,9; 0,11) N0=8 | 20.50/5.62/0.167; 45.98/12.90/0.111/8 | ✔ |
| §2 R2 stabil+belirsiz | mat +52,8 (9,7;0,11)/oku +42,3 (16,7;0,11)/fen +56,4 (8,8;0,07) | 52.83/9.72/.111; 42.34/16.75/.111; 56.37/8.81/.071 | ✔ |
| §2 R3 tüm katılımcı | +51,8/+53,6/+57,6; p 0,09/0,09/0,05; N0 10/10/18 | 51.77/53.55/57.61; .091/.091/.053 | ✔ |
| §2 R4 post2015 stabil | +12,8 (7,3;0,17)/+7,5 (3,5;0,17)/+3,3 (14,1;0,56) | 12.85/7.32/.167; 7.47/3.50/.167; 3.33/14.08/.556 | ✔ |
| §2 R5 tüm katılımcı | +12,1 (20,0;0,55)/+10,1 (17,6;0,64)/−16,0 (20,8;0,42) | 12.07/19.96/.545; 10.13/17.63/.636; −15.97/20.83/.421 | ✔ |
| §2 s.40 yıl etkileri (post2015 stabil) | 2015 −20,5/−31,8/−37,8 … 2025 +35,7/+38,3/+31,2 | CSV per_year birebir | ✔ |
| Zaman ağırlıkları | R1 2015:1,00/2012:1,00/2015:0,75; R4 2012:1,00/0,98/1,00 | birebir | ✔ |
| §0 s.11 & §6 s.75/77 | +45,6/+20,5/+46,0; 2012-taban +12,8/+7,5/+3,3; en iyi p 0,05 | §2/CSV ile tutarlı | ✔ |

Ayrıca içsel tutarlılık: her satırda τ̂ = yıl-bazlı etkilerin ortalaması (ör. post2018/mat 45.57 = (38.8+40.1+57.8)/3) ✔.

### 2) Algoritma sadakati (makale Alg. 1 & 4 ile karşılaştırma) — DOĞRULANDI

| Öğe | Makale (1812.09970v4) | Kod | Sonuç |
|---|---|---|---|
| ζ | (N_tr·T_post)^{1/4}·σ̂ | `(1*T1)**0.25*sigma` (N1=1) | ✔ |
| σ̂² | Σ(Δ_it−Δ̄)²/(N_co(T_pre−1)), kontrol **ön-dönem** birinci farkları, global Δ̄ çıkarılır | `np.diff(Y_co[:,:T0])`, `/(N0*(T0−1))`, `d.mean()` | ✔ |
| Birim ağırlığı ridge | ζ²·**T_pre**·‖ω‖² | `ridge=zeta**2*T0` (T0=T_pre) | ✔ |
| Kesişim (ω0, λ0) | her iki problemde var | `simplex_ls` serbest `c` | ✔ |
| Simpleks | ω,λ ≥ 0, toplam 1 | eq-kısıt + [0,1] sınır | ✔ |
| Zaman ağırlığı düzenlileştirme | ana amaçta yok (dipnot 3: (1e-6σ̂)²N_co tekillik için) | 1e-8 (docstring açıkça beyan ediyor) | ✔ (bkz. B2) |
| Kapalı-biçim τ̂ | ağırlıklı iki-yön SE regresyonu; tek tedavi = çift-doğrulu form | `(tr_post−tr_pre)−(co_post−co_pre)` | ✔ |
| Plasebo (Alg. 4) | her kontrol sırayla plasebo-tedavi, **tam** SDiD yeniden çalışır | `placebo()` her j için `sdid()` çağırıyor | ✔ |

**Bağımsız sağlama:** kapalı-biçim τ̂, kanonik çift-doğrusal SDiD formuyla `[−ω;1]ᵀ Y [−λ;1/T1]` **18/18 hücrede |fark| < 1,5e-13** eşleşti. σ̂, ζ, ridge, kesişim, simpleks, kapalı-biçim: makaleyle bire bir.

### 3) Kod/sadakat bulguları

- **[DÜŞÜK]** Plasebo SE `ddof=1` (1/(N0−1)); makale/synthdid konvansiyonu 1/B (ddof=0). Etki: bildirilen SE'ler N0=5'te ×1,118, N0=8'te ×1,069 **daha büyük** (muhafazakâr). Ör. post2018/mat/stabil SE 7,64 vs 6,84; t 5,96 vs 6,66. Niteliksel sonuç değişmiyor (rapor zaten anlamsızlık + sıra-p dili kullanıyor). Rapor (§2 s.30 "SE = sd") kodla iç-tutarlı; sapma yalnız makale konvansiyonuna karşı.
- **[ÖNEMSİZ]** Zaman ağırlığı ridge sabit 1e-8; makale dipnot 3 (1e-6σ̂)²·N_co ≈ 5e-10…4e-9. İkisi de ihmal edilebilir; nokta tahminlere etkisiz.
- **[BİLGİ]** `p_rank` (sıra-tabanlı permütasyon p) makalenin ötesinde ek çıkarım; raporda "sıra-p" olarak açıkça etiketli — sapma değil.
- **[DÜŞÜK/kozmetik]** Script docstring (s.21) 2012-tabanlı pencereyi "ana", 2015-tabanlı pencereyi "duyarlılık" etiketliyor; rapor tam tersine 2015-tabanlını manşet yapıyor. Yalnız adlandırma; sayı etkisi yok.
- **[NOT — olumlu]** Docstring/§2 s.30'daki `synthdid` düzeltmesi ("CRAN'da değil, yalnız GitHub synth-inference/synthdid") doğruluk yönünde bir düzeltme; sürüm "v0,0,9" tarafımca bağımsız doğrulanmadı (kapsam dışı).

### 4) Metin-veri çelişkisi (tek bulgu)

§2 son cümle "**üçü de aynı işaret**" iddiası, kaynak gösterilen `sdid_results.csv`'nin **post2015/all_participants/science** satırıyla çelişiyor: SDiD −15,97, SC-tipi −9,38, **DiD-tipi +20,94** → üç tahminci aynı işaretli DEĞİL (18 satırın 1'i, ikincil havuz). Manşet stabil-OECD satırlarında iddia doğru; ancak kayıtsız-şartsız cümlenin 1 karşı-örneği var. Rapor §3 s.54 zaten "fen tüm-katılımcı havuzunda işaret değiştirir" diyerek bu kararsızlığı başka yerde kabul ediyor.

### 5) Reprodüksiyon ve havuz/N0

- `python analysis/16_synthetic_did.py` → CSV/JSON **bayt-bayt aynı** (orijinal yedekle diff temiz). `_panel_matrix.py` → panel matrisleri aynı.
- Havuz donör sayıları: stabil OECD 5/5/8 (BEL CHE FRA ISL JPN; fen +COL EST LTU), stabil+belirsiz 8/8/13, tüm katılımcı 10/10/18 → §2'deki **N0 = 5/5/8, 8/8/13, 10/10/18 sütunlarıyla tam eşleşiyor**. `top_unit_weights`'teki tüm ülkeler ilgili havuzun donör listesinde.
- Not (kod-durum damgası): repo git değil; algoritma gövdesi (s.46–126) md5 `6b2f66139aa9d117f86a5e21f6acc7e3` üzerinden denetlendi.

### Verdikt

**GEÇTİ (küçük düzeltmelerle).** Uygulama Arkhangelsky vd. (2021) Alg. 1'i sadık biçimde hayata geçiriyor; §2/§0/§6'daki tüm SDiD sayıları CSV'yi bire bir yansıtıyor ve script deterministik olarak yeniden üretiliyor; kapalı-biçim tahminci kanonik forma makine hassasiyetinde eşit; havuzlar/N0 uyumlu. İki sapma yalnız makale konvansiyonuna karşı ve ikisi de ihmal edilebilir/muhafazakâr (plasebo SE ddof, zaman-ağırlığı ridge büyüklüğü). Tek gerçek metin-veri çelişkisi: "üçü de aynı işaret" ifadesinin ikincil fen/tüm-katılımcı hücresinde 1 karşı-örneği; cümle "manşet stabil-OECD havuzunda" diye nitelenmeli.

---

## SCOPE B Denetimi — `17_matrix_completion_conformal.py` + RESULTS_PHASE4 §3–§4 (ve §0/§6 MC/konformal hücreleri)

**Denetçi:** Opus 4.8 (sayı + kod). Kaynak/çıktı açılarak doğrulandı; hiçbir proje dosyası değiştirilmedi.

### Reprodüksiyon
Betik sabit tohumla çalışır (`np.random.default_rng(20260916)`). Çıktı klasörü yedeklendikten sonra betik yeniden çalıştırıldı; dört çıktı dosyası da **bit-birebir aynı** (SHA-256 özdeş): `mc_results.csv`, `conformal_results.csv`, `r_vs_python_sc.csv`, `summary.json`. **Tam reprodüksiyon: EVET.**

### §3 — Matris tamamlama (MC-NNM) sayı tablosu
Üç havuz × üç alan için tüm hücreler `summary.json`/`mc_results.csv` ile eşleşiyor (belirtilen yuvarlamayla):

| Alan/Havuz | İddia (2025 farkı) | Çıktı (mc_gap_2025) | ✓ |
|---|---|---|---|
| mat/stabil OECD | +49,0 | 48,982 | ✓ |
| oku/stabil OECD | +40,9 | 40,883 | ✓ |
| fen/stabil OECD | +47,1 | 47,079 | ✓ |
| mat/stabil+belirsiz | +60,1 | 60,074 | ✓ |
| oku/stabil+belirsiz | +47,9 | 47,913 | ✓ |
| fen/stabil+belirsiz | +53,5 | 53,463 | ✓ |
| mat/tüm katılımcı | +50,4 | 50,387 | ✓ |
| oku/tüm katılımcı | +46,1 | 46,146 | ✓ |
| fen/tüm katılımcı | +82,2 | 82,209 | ✓ |

Sonrası ortalamaları (24,5/11,4/18,8 · 30,7/15,0/21,5 · 24,2/13,1/42,9), plasebo sıraları+p (1/6 0,17 · 1/6 0,17 · 2/9 0,22 · 1/9 0,11 · 2/9 0,22 · 2/14 0,14 · 2/11 0,18 · 3/11 0,27 · 6/19 0,32), ön-dönem RMSE (2,1/2,1/3,7 · 2,0/1,2/6,8 · 1,6/3,2/1,3) ve rank(L) (3/3/5 · 5/5/4 · 6/5/6) hücrelerinin **tamamı** eşleşti. §3 SC-karşılaştırma satırı (SC 50,4/34,1/48,8 vs MC 49,0/40,9/47,1) ve fen-ayrışması (SC −16,4 / MC +82,2) da eşleşti.

### §4 — Konformal + Python–R çapraz doğrulama
- "6 vakada 0,00 farkla" — `r_vs_python_sc.csv` mutlak farkları 4e-8…7e-4 (en büyük: oku/stabil 0,00072); R yol dosyalarındaki 2025 gap değerleriyle bağımsızca da eşleşti (50,385 · 34,145 · 48,816 · 70,812 · 33,063 · 48,816). ✓
- "en küçük p = 0,125 (fen 0,143)" = 1/8, 1/7. ✓ Bağımsız yeniden-hesap: mat/stabil için 2015-25 H0 p=0,125 ve yalnız-2025 p=0,125 doğrulandı.
- "okuma/fen yalnız-2025 p = 0,25 / 0,29" ✓ (0,25 · 0,2857).
- Yalnız-2025 %80 aralıkları mat [4,62], oku [−10,80], fen [−6,82] ✓.
- **MISMATCH (metin↔çıktı):** "2018–2025 sabit etki için aralıklar **sınırsız**" — stabil OECD'de çıktı bunu yalancı çıkarıyor: mat [−22,168] ve oku [−38,142] ızgara içinde **SINIRLI**; yalnız fen [−40,200] (tam ızgara) sınırsız. Bağımsız yeniden-hesapla doğrulandı. Muhtemelen asıl sınırsız olan **2015–2025 ana pencere** CI'si (`ci80_lo/hi` = [−40,200], science-all-participants [8,200] hariç) ile karışmış. Genel sonucu ("konformal bu T ile bilgi vermiyor") değiştirmez; etki düşük ama ifade hatalı.

### §0 / §6 (MC-konformal hücreleri)
§0 tablosu (MC 49,0/40,9/47,1; plasebo 1/6,1/6,2/9; konformal aralıklar; en küçük p 0,125) ve §6.1 (SC 50/34/49, MC 49/41/47), §6.3 (MC stabil+belirsiz mat 0,11 = en küçük MC p; N0 5–18; T 7–8) — hepsi eşleşti. (§6.1/§6.3'teki SDiD sayıları Scope A; denetlenmedi.)

### §3 fen-ayrışması iddiası (görev madde 3) — DOĞRULANDI, açıklama destekleniyor
`build_matrix("science","all_participants")` ile 18 donörlü matris kuruldu ve SC ağırlıkları yeniden üretildi:
- SC ön-dönem (2006–2012) simpleks ağırlığı **tamamı QAT=1,00** (Katar). Katar **OECD dışı** ve pool'un en düşük düzeyli birimlerinden (fen 349→434). "SC dışbükey-örtü kısıtıyla OECD dışı düşük-düzeyli birimlere ağırlık veriyor" ifadesi çıktıyla **destekleniyor**.
- SC 2025 gap = −16,38 (ön-RMSPE 2,49, iyi ön-uyum) → Türkiye'nin 2015 çukuru + tek-donör demeaned uyum negatif sonrası gap üretiyor. MC: rank-6 L + iki-yön FE tüm panelden öğreniyor (ön-RMSE 1,3), 2025 karşı-olgu 412 → gap +82,2. Ayrışma gerçek; "Faz 3 §2 fen işaret-değişimi tahminci-bağımlı" çıkarımı çıktılarla tutarlı.
- Nüans: gerçek sürücü yalnız dışbükey-örtü değil, **Katar'ın demeaned ön-dönem şekil-uyumu + Türkiye'nin 2015 düşüşü**; ifade doğru ama biraz basitleştirilmiş.

### Kod incelemesi (papers'a karşı)
- **soft_impute vs Athey vd. 2021 (MC-NNM):** SADIK. Amaç fonksiyonu doğru — gözlenen hücrelerde kareler + λ‖L‖_* (eşiklenmiş tekil değerlerin toplamı); iki-yön FE **cezasız** (doğru); eksik hücreler cari tahminle doldurulup SVT uygulanıyor (soft-impute/EM şeması, Mazumder–Hastie–Tibshirani; Athey vd. Alg.1 ile aynı iskelet). Fitted L+a+b gap için kullanılıyor; a/b ayrışımının tekil olmayışı sonucu etkilemez.
- **CV tasarımı:** DOĞRU — `obs[obs[:,0]!=0]` tedavi satırını (satır 0) tümüyle dışlıyor; yalnız donör hücrelerinin %15'i maskeleniyor; MSE holdout üzerinde. "Tedavi satırı hariç, yalnız donör maskeli" karşılanıyor.
- **plasebo:** DOĞRU — tek-taraflı sıra = 1+#{donör gap≥TUR}, p=rank/(N0+1); plasebolar TUR'un seçtiği λ ile (sabit) — standart, savunulabilir.
- **demeaned simpleks SC (SLSQP):** DOĞRU; R `Synth`'i ~0 farkla üretiyor.
- **CWZ 2021 hareketli-blok:** SADIK — `np.roll(u,shift)`, T kaydırma; istatistik son q konumda (`u_perm[-q:]`); post gerçekten son q döngü; p = pay{S≥S_gözlenen}; shift=0 dahil → min p=1/T garanti. §4'te "min p=0,125/0,143" **doğru** yazılmış.

### Verdikt
Scope B **büyük ölçüde temiz ve tam-reprodüklenebilir**: §3/§4/§0/§6'daki her açık sayı çıktılarla eşleşiyor, kod her iki makaleye sadık, fen-ayrışması iddiası doğrulandı. Tek somut düzeltme gereken nokta §4'teki "2018–2025 … sınırsız" ifadesi (stabil OECD mat/oku aralıkları aslında sınırlı). Kalanlar düşük-önemli terminoloji/kırılganlık notları.

---

## SCOPE C Denetimi — `18_macro_partition.R`, RESULTS_PHASE4.md §5 + §0 tablosu + §1 memo değerlendirmesi

**Yeniden üretim:** `18_macro_partition.R` yeniden çalıştırıldı; dört çıktı (`results.json`, `ctree.txt`, `mob_tree.txt`, `country_frame.csv`) bayt-bayt aynı (md5 eşleşti). Proje dosyaları değişmedi; deterministik. R 4.6.1, partykit yüklü.

### §5 — Makro-bölümleme (her sayı çıktı dosyasından)

| İddia (§5) | Kaynak değer | Sonuç |
|---|---|---|
| N = 61 | results.json n=61 | ✓ |
| MOB bölünme yok (LOO dahil tek yaprak) | mob n_leaves=1, loo=1 | ✓ |
| Düzey-koşullu artık +59,8, 1/61, eğim −0,148 | lm slope=-0.148, TUR lm_resid=59.75, rank 1/61 | ✓ |
| CTree 3 yaprak | ctree n_leaves=3 | ✓ |
| İlk bölünme libdem 2013 ≤ 0,456 | ctree.txt `libdem_2013 <= 0.456` | ✓ |
| Yaprak-2 n=14, ort +2,1 | node[2]=2.105, n=14 | ✓ |
| Kapsam 2015 ≤ 0,906 → n=20 (−14,6) / n=27 (−23,0) | node[4]=-14.596 n=20; node[5]=-22.997 n=27; eşik 0.90612 | ✓ |
| Yaprak-2 üyeleri (14 ülke) | ctree leaf_members ile birebir | ✓ |
| Türkiye artık +49,1, 1/14 | ct_resid(TUR)=49.105, rank 1/14 | ✓ |
| **İkinci Katar +15,6** | ct_resid(QAT)=**+13,5**; change_avg(QAT)=15,6 | ✗ tutarsız |
| **Üçüncü BAE +15,2** | ct_resid(ARE)=**+13,1**; change_avg(ARE)=15,2 | ✗ tutarsız |
| Gürcistan aynı yaprakta 0,0 | ct_resid(GEO)=0.03 | ✓ (artık) |
| kNN k=8 komşular GEO MEX ISR HUN CAN GBR AUT JPN | knn8.neighbours | ✓ |
| TUR +51,2 vs ort −13,1 (sd 12,5), z=5,15, 1/9 | knn8 tümü | ✓ |
| Alan bazında komşu ort −15,4 / −20,5 / −3,4 | bağımsız hesaplandı: −15,4 / −20,5 / −3,4 | ✓ |
| k=12: z=5,30, 1/13 | knn12.z=5.3, rank 1 (13) | ✓ |
| Odak TUR +41,1 / +43,8 / +68,8 | change_math/reading/science | ✓ |
| Odak GEO +12,5 / −17,1 / +11,0 | ✓ | ✓ |
| Odak HUN −17,3 / −17,2 / +3,2 | ✓ | ✓ |

**Tek tutarsızlık:** §5 CTree yaprağında Türkiye (+49,1) ve Gürcistan (0,0) **artık** olarak verilirken, "ikinci Katar +15,6 / üçüncü BAE +15,2" değerleri **ham değişim (change_avg)** olarak verilmiş; artık olarak +13,5 / +13,1 olmalıydı. Sıralama (2. Katar, 3. BAE) doğru — sadece rapor edilen metrik karışık. Düşük-orta önem.

### §0 — Özet tablosu (sdid_results.csv / conformal_results.csv / mc_results.csv / macro_partition results.json)

| Hücre | Kaynak | Sonuç |
|---|---|---|
| SDiD stabil OECD mat +45,6 / oku +20,5 / fen +46,0 | post2018 tau_sdid=45.55/20.5/45.98 | ✓ |
| SDiD SE 7,6 / 5,6 / 12,9; p 0,17 / 0,17 / 0,11; N0=5–8 | se_placebo, p_rank, n_donors | ✓ |
| MC-NNM 2025 mat +49,0 / oku +40,9 / fen +47,1; sıra 1/6, 1/6, 2/9 | mc_gap_2025, mc_rank | ✓ |
| Konformal %80 CI mat [4,62], oku [−10,80], fen [−6,82]; en küçük p 0,125 | ci80_2025only_*, conformal_p | ✓ |
| Makro TUR +51,2; yaprak artık +49,1 1/14; komşu ort −13,1 (z=5,2) | results.json | ✓ (z 5,15→5,2) |
| Dipnot 2012-taban SDiD +12,8 / +7,5 / +3,3 | post2015 tau_sdid=12.85/7.47/3.33 | ✓ |

### §1 — Memo değerlendirmesi (`gemini_ideas_extraction_opus48.json`)

- Frontier "16 yöntem": JSON `frontier.methods` = **16** ✓
- Partitioning "14 yöntem": JSON `partitioning.methods` = **14** ✓
- §1.1 şüpheli maddeler (atıf-numarası uyuşmazlığı; geleceğe tarihli arXiv 2601–2607; DeepNetTMLE/TDA/geodesic SC/ACFR; Pyro + HuggingFace daily papers) — hepsi `frontier.suspicious_or_unverifiable` (10 madde) içinde birebir mevcut ✓
- §1.2 şüpheli maddeler (Macaristan medya-ele geçirme 8–12 puan nedensel orman, ResearchGate; Dünya Bankası 2030 yoksulluk MOB; geleceğe tarihli dergi/arXiv) — hepsi `partitioning.suspicious_or_unverifiable` (18 madde) içinde ✓
- Not: §1.3'teki "kısa Türkçe not" (HLM/CCA/PLS-SEM/Procrustes) bu JSON'da yok (JSON yalnız iki memo içeriyor); bu kaynaktan doğrulanamaz. Memo dosya boyutları (150/36/5 KB) proje dışı yollara ait, doğrulanamadı — kusur değil.

### Kod incelemesi bulguları

1. **[ORTA] `lmtree` sessiz listwise silme:** MOB, bölme değişkeni `coverage_2015` eksik olan 21 ülkeyi düşürür → model **n=40** üzerinde kurulur (`mob_tree.txt`: root n=40, eğim −0,232). Ancak `results.json` `leaf_n=61` ve 61 üyenin tamamını raporlar (`predict` atamasından). "Bölünme yok" sonucu geçerli ve TUR korunuyor; fakat rapor edilen yaprak bileşimi (61) tahmin örneklemini (40) abartıyor. §5'te alıntılanan MOB sayısı (+59,8 / −0,148) doğru şekilde **ayrı tam-örneklem lm**'den geliyor, MOB'un −0,232 eğiminden değil — yani §5 sayısı etkilenmiyor. kNN ve Mahalanobis de 40 tam-vaka ülke üzerinde çalışıyor (61 değil).
2. **[BİLGİ] N=61 tam açıklandı:** 2015 ve 2025'te üç-alanı eksiksiz **62** ülke var; tek ek düşen **MAC (Makao)** — V-Dem/CPI ekranında (institutional_screen) olmadığı için libdem/cpi eksik. Denetim sorusundaki "66" doğru payda değil; doğru referans 62, 61 = 62 − MAC. Inner-join'lar doğru.
3. **[BİLGİ] Sonuç sızıntısı yok:** Mahalanobis mesafeleri yalnız 5 makro değişkenden; sonuç (change_avg) X'te değil. Kovaryans S, merkez TUR dahil 40 vakadan (standart, ihmal edilebilir). `level_2015` mekanik olarak change_avg ile ilişkili (change = level2025 − level2015) ama bu tasarım gereği (MOB ortalamaya-dönüş modeli; CTree'de aday bölücü, üzerinde bölmedi). Bölücüler arasında tedaviyle korele makro değişkenler (delta_libdem, cpi) var — §5 verdikti bunu "nedensel tanımlama değil" diye açıkça saklı tutuyor. Kusur değil.
4. **[DÜŞÜK] `country_frame.csv` iki kez yazılıyor** (satır 34 ve 90); ilk yazım düğüm/artık sütunları eklenmeden. Zararsız; nihai dosya tam sürüm.
5. **[BİLGİ] `rank_in`** `as.integer(rank(-x)[who])` — TUR'da bağ yok, ondalık sıra riski gerçekleşmiyor. `predict(type='node')` doğru kullanılmış.

### Verdikt
§5, §0 ve §1'deki sayıların ve iddiaların ezici çoğunluğu (76 kontrolün 74'ü) çıktı dosyalarıyla ve JSON ile tam eşleşiyor; script bayt-bayt yeniden üretilebilir. Tek gerçek uyumsuzluk: §5'te CTree yaprağının 2./3. sıradaki değerleri (Katar +15,6 / BAE +15,2) artık yerine ham değişim olarak verilmiş (artık: +13,5 / +13,1) — sıralamayı ve ana sonucu değiştirmiyor. Bir orta-önem kod notu: MOB tam-örneklemin 40'ı üzerinde kuruluyor ama leaf_n=61 raporlanıyor (raporun §5 sayısını etkilemiyor).
