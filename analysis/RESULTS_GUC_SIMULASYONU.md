# MAKALE 1 — KOŞULLU SIRA TESTİNİN GÜCÜ (ÜLKE DÜZEYİ MONTE CARLO)

4 Eki 2026 · CC (Opus 5.5) · yazar onayı: "Ülke düzeyi Monte Carlo" (sohbet, 4 Eki 2026). Sonuç Makale 1'in dipnot 3'üne ve satır 126'sına girdi (yazar kabulü, 4 Eki 2026); ayrıntı burada. Betik: `analysis/57_power_simulation.py`; çıktı: `data/derived/power_sim/`. Öncül: kaba normal yaklaşım (simülasyon değil).

---

## 0. Ön-belirleme (koşudan önce yazıldı; dosyanın bu hâlinin SHA256'sı koşudan önce proje günlüğüne yazılır)

### 0.1 Soru ve tahmin edilen nicelik

Makalenin 2015→2025 koşullu sıra testi (betik 43; `MAKALE1.md` dipnot 3), Türkiye'nin çekirdeğine eklenen Δ puanlık şişmeyi hangi olasılıkla yakalar? Tahmin edilen: **güç(Δ, λ, hücre)** = P(Türkiye'nin koşullu sırası/N ≤ 0,10 | DGP). Doğru değer DGP parametrelerinden gelir (Δ, λ), tahminden değil. Türetilen: %80 güçle yakalanabilen en küçük şişme (**MDE80**) ve Türkiye'nin gözlenen sırasıyla uyumlu Δ üst sınırı.

### 0.2 Test (betik 43 ile aynı)

Hücre = ölçü (d_sd birincil, d_pts) × örneklem (all N = 47, oecd N = 35) × biçim (linear, quadratic). OLS d_i = α + β₁ΔC_i + β₂C0_i; her sistemin birini-dışarıda tahmin hatası e_i = r_i/(1 − h_ii); Türkiye'nin sırası #(e < e_TUR) + 1; ret: sıra/N ≤ 0,10. Girdi betik 43'ün `pair_frame()`'i (betik 34 `load()`).

### 0.3 DGP — IN-ASSUMPTION rejimi

| | Varsayım | Doğrulama |
| :---: | :--- | :--- |
| A1 | Koşullu model bütün sistemler için doğru: d_i = α + γΔC_i + βC0_i + e_i; katsayılar Türkiye dışarıda OLS (betik 43 çerçevesi) | Betik 43'ün Türkiye sıraları (ör. d_sd linear: 36/47, 9/35) yeniden üretilir; kesin eşitlik kapısı |
| A2 | Hatalar değiştirilebilir ve bağımsız: Türkiye-dışı uyumun standartlaştırılmış artıkları r_i/√(1 − h_i), ortalaması çıkarılmış havuzdan iadeli çekiliş; Türkiye'nin "temiz" hatası da aynı havuzdan | Havuz boyutu ve ortalaması (0) yazdırılır |
| A3 | Şişme yalnız Türkiye'de. Türkiye'nin gözlenen çekirdek artışı ΔC_TUR = 51,21 sabit; bunun Δ'sı şişme, 51,21 − Δ'sı gerçek. Şişmenin λ'sı, gerçek kazancın τ'su yeni alana geçer; τ = b₂₅ + γ·s, b₂₅ 2025 kesit uyumunun Türkiye çekirdeğindeki yerel eğimi (all-linear 1,0129; all-quad 0,8520; oecd-linear 0,8634; oecd-quad 0,8931), s = RMSE₂₅ (d_sd: 19,3815; 17,9128; 10,6992; 10,8047) ya da 1 (d_pts). Sonuç: d_TUR = α + γ·51,21 + β·C0_TUR + e_TUR − (τ − λ)·Δ/s | (i) Türetme: §3 dipnot 2 · (ii) d düzeyindeki kayma, tam boru hattıyla karşılaştırılır: gözlenen veride Türkiye'nin 2025 yeni-alan ortalaması (τ − λ)Δ düşürülür, 2025 kesiti yeniden uydurulur, bütün d yeniden hesaplanır, Türkiye'nin e'si yeniden bulunur (Δ ∈ {20, 40, 80}, λ ∈ {0, 0,5}); göreli fark yazılır |
| A4 | ΔC ve C0 hatasız gözlenir | — (O1 bunu gevşetir) |

Diğer sistemlerin d'si her yinelemede A1–A2'den yeniden üretilir; Türkiye'nin ΔC ve C0'ı gözlenen değerlerdir.

### 0.4 OUT-OF-ASSUMPTION değişkeleri (ayrı satır, etiketli; IN-ASSUMPTION iddiasına dayanak olmaz)

| | Gevşetilen | Tasarım |
| :---: | :--- | :--- |
| O1 | A4: ΔC'de ölçme hatası | Analist ΔC + ν görür, ν ~ N(0, s_ν²), s_ν ∈ {3,5; 7} puan (bütün sistemler). DGP'de gerçek eğim γ_true = γ̂/ρ, ρ = 1 − s_ν²/Var(ΔC); τ = b₂₅ + γ_true·s. Ortak bağlama hatası bütün ülkeleri aynı kaydırdığı için kesişime gider, s_ν'ye girmez |
| O2 | A2: ampirik havuz | Hatalar N(0, σ²), σ = havuzun standart sapması |

### 0.5 Izgara, yineleme, tohum

Δ ∈ {0, 5, …, 200} (41 değer); λ ∈ {0; 0,25; 0,5}; 8 hücre; R = 10.000 (güç 0,80'de MCSE ≈ 0,004). Tohum: `numpy.random.SeedSequence(20261004)`, (rejim, hücre, λ, Δ) sırasıyla `spawn` — tohum işe bağlı, işçiye değil.

### 0.6 Çıktılar ve okuma

- Güç tablosu (+ MCSE), her hücre × λ için MDE80 (gücün 0,80'i ilk geçtiği ızgara Δ'sı ve iki komşu arasında doğrusal ara değer), Δ = 0'da büyüklük (değiştirilebilirlik altında beklenen ⌊0,1N⌋/N: 4/47 = 0,085; 3/35 = 0,086).
- Uyumlu Δ üst sınırı (λ = 0, d_sd ve d_pts, linear): P_Δ(sıra_sim ≥ sıra_gözlenen) ≥ 0,10 olan en büyük ızgara Δ'sı.
- Karar kuralı yok; betimsel. MDE80 Türkiye'nin 51,21 puanlık artışıyla karşılaştırılır.
- Ham sonuç: her (rejim, hücre, λ, Δ) için ret sayısı ve Türkiye sıralarının dağılımı (`ps_cells.csv`); birincil hücrelerde yineleme düzeyinde sıra (`ps_raw_primary.npz`); parmak izi (`ps_summary.json`: betik ve girdi SHA256'ları, parametreler).
- Doğrulama: taze bağlamlı kod incelemesi + yalnız bu ön-belirlemeden bağımsız yeniden uygulama (birincil hücreler); fark > 3·MCSE ise durulur.

### 0.7 SONRADAN (4 Eki 2026; duman testinden sonra, tam koşudan önce)

Duman testi (R = 1.000, `data/derived/power_sim/quick/`) A3 (ii) denetiminde şunu gösterdi: d_pts'de d düzeyindeki kayma tam boru hattıyla aynı (doğrusal 1,0000; ikinci derece 0,95–0,99), ama d_sd'de yalnız 0,36–0,97'si kadar. Türkiye 2025 kesitinde aykırılaştıkça RMSE₂₅ büyüyor ve kendi sapmasını sönümlüyor. Bu yüzden birincil **IN** rejimi tam eşlemeyi kullanır: yinelemenin d'si 2025 artıklarına çevrilir (ortak sistemler yinelemeden, öbürleri gözlenen), Türkiye'nin yeni-alan ortalaması (τ − λ)Δ düşürülür (şapka matrisiyle güncelleme), RMSE₂₅ yeniden hesaplanır, d betik 34'ün tanımıyla yeniden kurulur. Eşleme, gözlenen veride betik 34'ün yeniden uydurma yoluyla aynı sonucu vermek zorundadır (kapı). Varsayımlar A1–A4 değişmedi; değişen, A3'ün uygulanışı. Ön-belirlenen d düzeyi formülü **IN_dduzey** satırı olarak raporlanır. O1 ve O2 tam eşlemeyle. Duman testinin güç değerleri bu karardan önce görülmüştü.

### 0.8 SONRADAN 2 ve 3 (4 Eki 2026; ikinci ve üçüncü duman testlerinden sonra, tam koşudan önce)

| | Duman testinde görülen | Tanı | Değişiklik |
| :---: | :--- | :--- | :--- |
| 2 | §0.7'deki eşleme temiz dünyayı d_sd düzeyinde üretince Δ = 0'da d_sd büyüklüğü 0,02 | Ortak sistemlerin yinelemedeki 2025 artık standart sapması 27, gözlenen 14: gözlenen d_sd 2015 artığıyla negatif ilişkili, bağımsız hata çekilişi bu ilişkiyi siliyor ve RMSE₂₅'i yapay olarak şişiriyor | Temiz dünya puanla üretilir; τ yapısal ve tek (puan); analist iki ölçüyü de bu 2025 artıklarından betik 34'ün tanımıyla hesaplar |
| 3 | Puan üreteci (2025 artığı = r15 + d_pts modeli + e) d_sd'de büyüklüğü 0,002'ye düşürdü | Bu üreteç 2015 artığının tamamen kalıcı olduğunu (φ = 1) varsayıyor. Veride r25'in r15'e eğimi (Türkiye dışarıda, ΔC ve C0 sabit): all-linear 0,464 (S.H. 0,180), all-quad 0,511 (0,194), oecd-linear 0,239 (0,151), oecd-quad 0,278 (0,167). Yeni alanlar her döngüde başka yapı; ortalamaya dönüş var | Birincil **IN**: 2025 artığı = a + φ·r15 + γΔC + βC0 + e (Türkiye dışarıda OLS, standartlaştırılmış havuz); τ_r = b₂₅ + γ. O1 ve O2 bunun üzerine. φ = 1 üreteci **O3_phi1** satırı |

**Rejimlerin okunuşu.** IN_dduzey testin kendi değiştirilebilirlik varsayımı altında gücü verir (Türkiye, 2015 konumu bakımından ortalama bir sistem gibi). IN, Türkiye'nin gerçek 2015 artığını ve ortalamaya dönüşü taşır. O3, φ = 1 sınırıdır. İkisi de raporlanır; hiçbiri öbürünün yerine geçmez. Üç değişikliğin hiçbiri güç sonucunu hedef almadı, üçü de DGP'nin gözlenen veriyle tutarlılığını düzeltti; yine de duman testlerinin güç değerleri her değişiklikten önce görülmüştü.

### 0.9 SONRADAN 4 (4 Eki 2026; taze bağlamlı doğrulamadan sonra, `wf_…`)

İlk tam koşu (`data/derived/power_sim/_arsiv_v4_izdusumsuz_2026-10-04/`) ile birlikte koşan kod incelemesi bir yüksek, iki orta önemde bulgu verdi; düzeltmeler tam koşu yinelenmeden önce uygulandı:

| | Bulgu | Düzeltme |
| :---: | :--- | :--- |
| Yüksek | Üretilen temiz 2025 artıkları 2025 tasarımının artık uzayına izdüşürülmüyordu; analist kesiti yeniden uydurduğunda bu vektörü göremez. Etki d_pts doğrusalda sıfır, d_sd ve ikinci derecede bazı hücrelerde > 3·MCSE (OECD, Δ = 50: +0,027) | Artık = M₂₅·(üretilen − δe_T); stokastik kapı: rastgele bir yineleme betik 34 `refit` ve betik 43 `pair_frame` yolundan geçer, fark ≤ 1e-8 |
| Orta | A3 (ii) öngörüsü boru hattından farklı τ kullanıyordu | Öngörü τ_r ile; ön-belirlenen formül ayrı sütun |
| Orta | Kapılar simülasyondan sonra koşuyordu; Δ = 0 özdeşlik kapısı totolojikti | Kapılar önce; r15 ve rsd15 betik 34'ün 2015 artıklarıyla karşılaştırılır |
| Düşük | O1'in τ sütunu kullanılan τ'yu göstermiyordu; IN/OUT etiketi yoktu; Δ = 0 ret oranı her rejimde nominal büyüklükle yan yana yazılıyordu | Kullanılan τ ve tanımı yazılır; `assumption` sütunu; nominal büyüklük yalnız IN_dduzey satırlarında |
| Düşük | Tohum görev sırasına bağlıydı; Δ'lar arasında ortak çekiliş yoktu | Tohum içerikten: `SeedSequence(20261004, spawn_key=(rejim, hücre, λ))`; aynı çekilişler bütün Δ'larda (ortak rastgele sayı: güç eğrisi yineleme düzeyinde monoton, sahte erken 0,80 geçişi yok; düzey hatası aynı, komşu Δ'lar ilişkili). İkinci tur incelemeden (`wf_…`) sonra: eşleme kapısı yuvarlamasız ve 1e-8; stokastik kapı O3 üretecini, 3 yinelemeyi, δ = 200τ'yu ve O1 PRESS yolunu kapsar; MDE80 MCSE'si yeniden örneklemeyle; `monotone` sütunu kaldırıldı (ortak çekilişte tanım gereği doğru). Sonuç dosyası `ps_cells.csv` bu değişikliklerden sonra bayt bayt aynı |

### 0.10 SONRADAN 5 (4 Eki 2026; tam koşudan sonra; `RESULTS_EMPIRICAL_FIXES.md` §0.14, betik 59)

§1.1'deki bulgu (değiştirilebilirlik altında Δ = 0'da PRESS ret oranı 0,12–0,14, nominal 0,085; Türkiye'nin kaldıracı 0,30 ve 0,45) üzerine yazarın onayıyla ("yap") ikinci bir test eklendi. **Bu test ön-belirlenmedi; güç sonuçları görüldükten sonra eklendi. Ön-belirlenen PRESS sırası birincil kayıt olarak kalır.**

| Öğe | Seçim |
| :--- | :--- |
| İstatistik | Dış-studentize artık t_i = r_i / (s₍ᵢ₎ √(1 − h_ii)), s₍ᵢ₎² = (Σr² − r_i²/(1 − h_ii)) / (N − k − 1); tasarım ve OLS PRESS'le aynı (betik 59 ile aynı formül) |
| Sıra ve ret | #(t < t_TUR) + 1; ret sıra/N ≤ 0,10 (§0.2 ile aynı kural) |
| Uygulama | Betik 57 v7: her yinelemede iki test aynı Y'den (`press_rank`, aynı çekilişler); çıktılarda `test` ∈ {press, stud}. DGP, ızgara, tohum ve rejimler değişmedi |
| Kapılar | Gözlenen studentize sıra, betik 59'un `e1_studentized_summary.json`'uyla 8 hücrede aynı; `press` satırları önceki koşuyla aynı (§1) |

---

## 1. Sonuçlar

Koşu: betik 57 v6, R = 10.000, 6 rejim × 8 hücre × 3 λ × 41 Δ; `data/derived/power_sim/` (`ps_cells.csv` sha256 e180c758…, v5 ile bayt bayt aynı: belirlenimci yeniden üretim). Önceki sürümler `_arsiv_v4_izdusumsuz_2026-10-04/` ve `_arsiv_v5_2026-10-04/` altında.

**v7 (SONRADAN 5, §0.10):** 4 Eki 2026 16:16'da başlatıldı (proje günlüğü); 332 sn, `exit=0`, bütün kapılar geçti (`kosu.log`). `ps_cells.csv` sha256 1434046b…, 11.808 satır (iki test). `test == "press"` satırları, `test` sütunu dışında, v5 = v6 dosyasıyla (`_arsiv_v5_2026-10-04/ps_cells.csv`) birebir aynı (pandas `equals` = True; koşuyu başlatan oturum, devralan oturum ve taze bağlamlı doğrulama `wf_…` ayrı ayrı denetledi). Bu yüzden §1.1–1.6'daki PRESS sayıları değişmedi. Tek istisna MCSE'ler: yeniden örnekleme akışı iki testi sırayla dolaştığı için `press` satırlarında da yeniden çekildi. §1.2'nin gösterdiği hassasiyette yalnız IN d_sd OECD λ = 0 MDE80 MCSE'si değişiyor (v6 0,4; v7 0,34). Studentize sonuçlar §1.7'de.

### 1.1 Hüküm tablosu

| | Soru | Bulgu |
| :---: | :--- | :--- |
| 🔴 | Birincil ölçü (d_sd, doğrusal) Türkiye'nin 51 puanlık çekirdek artışının tamamı şişme olsa yakalar mıydı? | **Yapısal DGP'de büyük olasılıkla hayır:** tüm katılımcılarda güç 0,08, OECD'de 0,49 (λ = 0). %80 güç için gereken şişme 100 ve 72 puan; ikisi de artışın tamamından büyük ya da ona yakın |
| 🟡 | Testin kendi değiştirilebilirlik varsayımı altında (ön-belirlenen IN_dduzey) | MDE80 d_sd 79 / 47, d_pts 47 / 50 puan (tüm / OECD); 51 puanda güç 0,56 / 0,85 ve 0,84 / 0,81. Ama Δ = 0'da ret oranı 0,12–0,14 (nominal 0,085): Türkiye'nin kaldıracı (0,30 ve 0,45) PRESS hatasının varyansını büyütüyor |
| 🔴 | Δ = 0'da yapısal DGP | Ret oranı 0–0,02: test Türkiye için çok tutucu. Türkiye'nin 2015 artığı düşük (−12,85; 47'de 5.) ve artıklar ortalamaya dönüyor (φ = 0,46 tüm, 0,24 OECD); test r15'i içermediği için Türkiye'nin beklenen değişimi yukarı kayıyor |
| 🔴 | d_sd'nin öz-normalleşmesi | Türkiye 2025 kesitinde aykırılaştıkça RMSE₂₅ büyüyor: OECD'de d_sd kayması doğrusal öngörünün yalnız %31–55'i, tüm katılımcılarda %85–95'i (`ps_pipeline_check.csv`). d_pts doğrusalda kayma birebir |
| 🟡 | Gözlenen sıralar hangi şişmeyle uyumlu? | λ = 0'da Türkiye'nin gözlenen sırası 0 ile **40–60 puan** arasındaki şişmeyle uyumlu (d_sd 45 / 60, d_pts 40 / 50; tüm / OECD). Yani test, artışın büyük kısmının şişme olmasını dışlayamıyor |
| 🟢 | Ölçme hatası (O1), normal hata (O2) | MDE80 en çok ±10 puan oynuyor; sonuç değişmiyor |
| 🟡 | φ = 1 sınırı (O3) | d_pts'de tablo değiştirilebilir duruma döner (MDE80 47 / 50, Δ = 0'da ret 0,13–0,14); d_sd'de yine 94 / 98 |
| 🟢 | Doğrulama | Bağımsız yeniden uygulama (kod görülmeden, tanımdan): 40 noktada \|z\| > 3 yok, en büyük 2,44 (`ps_bagimsiz_karsilastirma.csv`); iki tur kod incelemesi; kapılar §1.5 |

**Legend:** 🟢 sonuç sağlam ya da doğrulandı · 🟡 varsayıma bağlı ya da yalnız betimsel · 🔴 makalenin okunuşu için önemli kısıt.

### 1.2 Doğrusal hücreler, λ'ya göre (IN = yapısal, birincil; IN_dduzey = ön-belirlenen)

| Rejim | Ölçü | Örneklem | Δ = 0 ret | 51 puanda güç (λ = 0) | MDE80, λ = 0 | MDE80, λ = 0,25 | MDE80, λ = 0,5 |
| :--- | :--- | :--- | ---: | ---: | ---: | ---: | ---: |
| IN | d_sd | tüm (47) | 0,000 | 0,082 (0,003) | **100,0** (0,3) | 147,0 (0,4) | > 200 |
| IN | d_sd | OECD (35) | 0,005 | 0,490 (0,005) | **72,2** (0,4) | 101,9 (0,5) | 175,2 (0,9) |
| IN | d_pts | tüm | 0,020 | 0,671 (0,004) | 59,1 (0,3) | 87,1 (0,4) | 167,8 (0,8) |
| IN | d_pts | OECD | 0,002 | 0,556 (0,005) | 61,2 (0,2) | 87,1 (0,3) | 148,8 (0,5) |
| IN_dduzey | d_sd | tüm | 0,134 | 0,561 | 79,2 | 138,3 | > 200 |
| IN_dduzey | d_sd | OECD | 0,138 | 0,846 | 46,8 | 76,1 | 196,6 |
| IN_dduzey | d_pts | tüm | 0,128 | 0,843 | 47,1 | 73,3 | 166,8 |
| IN_dduzey | d_pts | OECD | 0,139 | 0,810 | 50,2 | 82,7 | > 200 |

Parantez içi MCSE (güç: √(p(1−p)/R); MDE80 ve 51 puanda güç: yinelemeleri 500 kez yeniden örnekleme; yalnız IN doğrusal hücrelerde ham sıra saklandı). MDE80 = gücün 0,80'i ilk geçtiği ızgara noktasıyla bir öncekinin doğrusal ara değeri. τ (yapısal, puan): tüm 0,771, OECD 0,854; ön-belirlenen ölçü τ'su: d_sd 0,580 / 0,653, d_pts 0,695 / 0,633. İkinci derece hücreler, O1–O3 ve bütün Δ'lar `ps_mde.csv` ve `ps_cells.csv`'de.

### 1.3 Gözlenen sıralarla uyumlu şişme (IN, test tersine çevirme)

| Ölçü | Örneklem | Gözlenen sıra | P(sıra ≥ gözlenen \| Δ = 0) | Uyumlu Δ üst sınırı: λ = 0 / 0,25 / 0,5 |
| :--- | :--- | :---: | ---: | :--- |
| d_sd | tüm | 36/47 | 0,859 | 45 / 65 / 130 |
| d_pts | tüm | 20/47 | 0,840 | 40 / 60 / 120 |
| d_sd | OECD | 9/35 | 0,985 | 60 / 85 / 150 |
| d_pts | OECD | 13/35 | 0,982 | 50 / 70 / 125 |

Üst sınır: P_Δ(sıra ≥ gözlenen) ≥ 0,10 olan en büyük ızgara Δ'sı (5 puanlık ızgara). Δ = 0'daki olasılıklar 0,84–0,99: yapısal sıfır altında Türkiye'nin tipik sırası gözlenenden yüksek; gözlenen sıra şişmesiz dünyanın alt %14'ünde (tüm) ve alt %2'sinde (OECD). Bu bir test değil (karar kuralı ön-belirlenmedi), yalnız betimsel.

### 1.4 Okuma

- Makalenin koşullu testi (dipnot 3: p = 0,77 ve 0,26) şişme olmadığını göstermiyor. Birincil ölçüyle, Türkiye'nin 2015 konumu taşındığında, artışın tamamına yakın bir şişmeyi bile büyük olasılıkla kaçırıyor; şişme yeni alana biraz sızıyorsa (λ = 0,25) eşik 100–150 puana çıkıyor.
- Makalenin "the residual … does not measure inflation" ve "cannot separate" ifadeleri bu sonuçla tutarlı. Koretz, McCaffrey ve Hamilton'un (2001) "egregious inflation" uyarısının sayısal karşılığı burada 50–100 puan.
- Tutuculuğun iki kaynağı makalenin kendi tasarım seçimlerinde: (i) d_sd her döngüyü kendi RMSE'siyle ölçekliyor (RMSE₁₅ 10,7, RMSE₂₅ 19,4), bu yüzden düşük 2015 artığı Türkiye'nin d_sd'sini yukarı itiyor ve aykırı 2025 artığı kendi RMSE'sini büyütüyor; (ii) koşullu model r15'i içermiyor, artıklar ise ortalamaya dönüyor.
- Ön-belirlemedeki kaba hesap (öncelik taraması §3: MDE80 43 / 39, λ = 0) gücü olduğundan iyi gösteriyordu. OECD satırında 2025 eğimi yanlış alınmıştı (1,013 yerine 0,863). Değiştirilebilirlik altında bile simülasyon 47–79 veriyor.

### 1.5 Kapılar

| Kapı | Sonuç |
| :--- | :--- |
| Çerçeve = betik 34 artık değişimi (328 hücre) | en büyük fark 5e-05 |
| Türkiye sırası ve e = betik 43 (`e1_summary.json`; gerileme kapısı) | 8 hücre aynı |
| 2025 yeniden uydurma = dosya (artık, RMSE) | geçti |
| r15, rsd15 = betik 34'ün 2015 artıkları | 1,3e-12 |
| Tam eşleme = betik 34 yeniden uydurma yolu (gözlenen veri, 48 denetim, yuvarlamasız) | 6,2e-11 |
| Stokastik: IN ve O3 üreteçleri, hücre başına 3 yineleme, δ = 40τ ve 200τ, betik 34 `refit` + betik 43 `pair_frame` | 3,6e-10 |
| O1 yineleme başına PRESS = betik 43 `press` (sıra) | fark 0 |

### 1.6 Sınırlar

- DGP ülke düzeyinde. Öğrenci düzeyindeki ölçekleme (Pokropek vd., 2022 tarzı) ve çekirdekle yeni alanın ortak ölçekleme modeli simüle edilmedi.
- φ, γ ve τ Türkiye dışarıda tahmin edildi ve sabit tutuldu; belirsizlikleri (φ'nin S.H.'si 0,15–0,19) yalnız O3 sınırıyla yansıtıldı.
- Şişme yalnız Türkiye'de varsayıldı. 2015 artığı "temiz" sayıldı; şişme 2015'ten önce başladıysa durum daha da kötüleşir.
- O1'de ρ marjinal Var(ΔC) ile hesaplandı; kısmi varyansla düzeltme biraz daha büyük olurdu.
- Ortak rastgele sayı güç eğrisini yineleme düzeyinde monoton yapıyor (sahte erken 0,80 geçişi yok); düzey hatası aynı kalıyor, komşu Δ'lar ilişkili.
- Üç DGP değişikliği (§0.7–0.8) ve doğrulama düzeltmeleri (§0.9) duman testlerinden ve ilk tam koşudan sonra yapıldı. Ön-belirlenen sürüm IN_dduzey olarak eksiksiz raporlandı.

### 1.7 Dış-studentize test (SONRADAN 5, §0.10; ön-belirlenmedi)

Koşu v7; tablolar `ps_mde.csv` ve `ps_inversion.csv`'den betikle üretildi (`test` sütunu). PRESS satırları §1.2–1.3 ile aynı, karşılaştırma için yan yana.

| Rejim | Ölçü | Örneklem | Test | Δ = 0 ret | 51 puanda güç (λ = 0) | MDE80, λ = 0 | MDE80, λ = 0,25 | MDE80, λ = 0,5 |
| :--- | :--- | :--- | :--- | ---: | ---: | ---: | ---: | ---: |
| IN | d_sd | tüm (47) | press | 0,000 | 0,082 (0,003) | 100,0 (0,3) | 147,0 | > 200 |
| IN | d_sd | tüm (47) | stud | 0,000 | 0,049 (0,002) | **107,5** (0,3) | 157,9 | > 200 |
| IN | d_sd | OECD (35) | press | 0,005 | 0,490 (0,005) | 72,2 (0,3) | 101,9 | 175,2 |
| IN | d_sd | OECD (35) | stud | 0,003 | 0,325 (0,004) | **86,6** (0,5) | 122,5 | > 200 |
| IN | d_pts | tüm (47) | press | 0,020 | 0,671 (0,004) | 59,1 (0,3) | 87,1 | 167,8 |
| IN | d_pts | tüm (47) | stud | 0,011 | 0,582 (0,005) | 63,4 (0,2) | 93,6 | 180,1 |
| IN | d_pts | OECD (35) | press | 0,002 | 0,556 (0,005) | 61,2 (0,2) | 87,1 | 148,8 |
| IN | d_pts | OECD (35) | stud | 0,001 | 0,398 (0,005) | 67,6 (0,2) | 95,9 | 164,1 |
| IN_dduzey | d_sd | tüm (47) | press | 0,134 (0,085) | 0,561 | 79,2 | 138,3 | > 200 |
| IN_dduzey | d_sd | tüm (47) | stud | 0,097 (0,085) | 0,498 | **86,2** | 150,9 | > 200 |
| IN_dduzey | d_sd | OECD (35) | press | 0,138 (0,086) | 0,846 | 46,8 | 76,1 | 196,6 |
| IN_dduzey | d_sd | OECD (35) | stud | 0,079 (0,086) | 0,756 | **54,8** | 89,1 | > 200 |
| IN_dduzey | d_pts | tüm (47) | press | 0,128 (0,085) | 0,843 | 47,1 | 73,3 | 166,8 |
| IN_dduzey | d_pts | tüm (47) | stud | 0,092 (0,085) | 0,798 | 51,4 | 80,0 | 182,3 |
| IN_dduzey | d_pts | OECD (35) | press | 0,139 (0,086) | 0,810 | 50,2 | 82,7 | > 200 |
| IN_dduzey | d_pts | OECD (35) | stud | 0,077 (0,086) | 0,711 | 59,0 | 97,0 | > 200 |

Parantez içi: Δ = 0 sütununda (IN_dduzey) nominal büyüklük ⌊0,1N⌋/N; güç ve MDE80 sütunlarında MCSE (yalnız IN, λ = 0; yeniden örnekleme, v7). Öbür MCSE'ler, ikinci derece hücreler ve O1–O3 `ps_mde.csv`'de.

| Ölçü | Örneklem | Test | Gözlenen sıra | P(sıra ≥ gözlenen \| Δ = 0) | Uyumlu Δ üst sınırı: λ = 0 / 0,25 / 0,5 |
| :--- | :--- | :--- | :---: | ---: | :--- |
| d_sd | tüm | press | 36/47 | 0,859 | 45 / 65 / 130 |
| d_sd | tüm | stud | 31/47 | 0,918 | 50 / 75 / 150 |
| d_pts | tüm | press | 20/47 | 0,840 | 40 / 60 / 120 |
| d_pts | tüm | stud | 21/47 | 0,834 | 40 / 60 / 120 |
| d_sd | OECD | press | 9/35 | 0,985 | 60 / 85 / 150 |
| d_sd | OECD | stud | 11/35 | 0,985 | 60 / 85 / 150 |
| d_pts | OECD | press | 13/35 | 0,982 | 50 / 70 / 125 |
| d_pts | OECD | stud | 14/35 | 0,983 | 50 / 75 / 125 |

IN rejimi, doğrusal; üst sınırın tanımı §1.3'teki gibi (betimsel, test değil).

- **Büyüklük.** Değiştirilebilirlik altında (IN_dduzey, doğrusal, λ = 0) studentize testin Δ = 0 ret oranı 0,077–0,097 (MCSE ≤ 0,003); PRESS'inki 0,128–0,139; nominal 0,085 / 0,086. PRESS'in fazla reddi büyük ölçüde Türkiye'nin kaldıracından geliyordu. Studentize test tüm katılımcılarda nominalin biraz üstünde (d_sd 0,097, d_pts 0,092), OECD'de biraz altında (0,079, 0,077).
- **Güç bedeli.** Fazla ret kalkınca eşik yükseliyor: doğrusal, λ = 0 MDE80 studentize testte IN_dduzey'de 4–9 puan, IN'de 4–14 puan daha yüksek. Birincil ölçüde (d_sd) MDE80 IN_dduzey 86,2 / 54,8, IN 107,5 / 86,6 (tüm / OECD); 51 puanda güç 0,50 / 0,76 ve 0,05 / 0,32.
- **Yapısal DGP (IN).** Studentize test de çok tutucu: Δ = 0 ret oranı 0–0,011 (doğrusal, λ = 0; bütün λ'larda en çok 0,013). Tutuculuğun kaynağı kaldıraç değil (r15'in modelde olmaması ve d_sd'nin öz-normalleşmesi, §1.4); bu yüzden studentize düzeltme onu gidermiyor.
- **Gözlenen sıralar.** Studentize sıralar (d_sd 31/47 ve 11/35) yapısal sıfır altında da sıradan: P(sıra ≥ gözlenen | Δ = 0) 0,92 ve 0,98. λ = 0'da uyumlu Δ üst sınırı d_sd'de 50 / 60 puan (PRESS 45 / 60); d_pts'de değişmiyor (40 / 50).
- **Okuma.** Studentize test de 16 hücrenin hiçbirinde p ≤ 0,10 vermiyor (betik 59). Birincil ölçüde, yapısal DGP'de, artışın tamamı kadar (51 puan) bir şişmeyi büyük olasılıkla kaçırıyor (güç 0,05 / 0,32); §1.4'ün okunuşu değişmiyor.
- **Doğrulama.** Taze bağlamlı üç doğrulayıcı (`wf_…`), birbirini görmeden şunları buldu. İki tablo CSV'lerden bağımsız olarak yeniden üretildi ve hücre hücre tuttu. Gözlenen studentize sıralar 16 hücrede bağımsız yeniden uydurmayla (açık birini-dışarıda ve statsmodels) aynı. `ps_raw_primary.npz`'den yeniden hesaplanan Δ = 0 ret oranı, 51 puanda güç ve MDE80, `ps_mde.csv`'den en çok 5,6e-17 farklı. `stud_t` ve `press_rank` incelemesinde hata yok.
