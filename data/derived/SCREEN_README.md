# Kurumsal Tarama (Institutional Screen) — Donör Havuzu Ön Elemesi

Öneri (`pisa_proposal_v2_TR_EN.md`) §4.1–4.2 kurallarının uygulanmasıdır. Üretici betik:
`analysis/02_institutional_screen.py`. Tüm değerler dosyalardan gelir; her çıktı satırı
kaynak sütunları (`src_vdem`, `src_ert`, `src_cpi`, `src_oecd` veya `source_file`/`source_page`)
taşır. Hiçbir sayı bellekten yazılmamıştır.

## Çıktı dosyaları
- `institutional_screen.csv` — 179 ülke (V-Dem libdem verisi olan tüm ISO3 evreni). Sütunlar:
  iso3, country, oecd_member, libdem_2013(+lo/hi), libdem_latest(+lo/hi), delta_libdem,
  change_outside_ci, ert_aut_episodes, ert_dem_episodes, cpi_mean_2013_2025, class, reason
  (+ cpi_n_years, libdem_latest_year ve kaynak sütunları).
- `paper_based_2015.csv` — 2015'te kâğıt-tabanlı testi uygulayan 15 ülke.
- `asterisk_cycles.csv` — 2015/2018/2022/2025 döngülerinde OECD tarafından uyarı/açıklama
  taşıyan ülke-döngüleri (ülke düzeyi + 2025 için alt-ulusal bölgeler ayrıca kaydedildi).

## Yöntem ve eşikler
**STABLE (stabil) koşulu — ikisi birden:**
1. V-Dem ERT'de 2013–2025 penceresiyle **kesişen hiçbir otokratikleşme (aut) veya
   demokratikleşme (dem) epizodu yok** (epizot [start,end] aralığı [2013,2025] ile kesişiyorsa
   "kesişiyor" sayılır).
2. `v2x_libdem` değişimi (2013 → latest) **güven bandı içinde**: latest nokta tahmini 2013'ün
   [codelow, codehigh] bandında **ve** 2013 nokta tahmini latest bandında (çift yönlü, "and vice
   versa"). İki koşuldan biri bozulursa `change_outside_ci=1` ve ülke stabil sayılmaz.

**Alt gruplar (yalnız STABLE ülkeler):** ortalama CPI 2013–2025 > 50 → `stable_clean`;
≤ 50 → `stable_corrupt`.

**TREATED (tedavi edilmiş):** pencereyle kesişen epizot(lar) varsa; tür/başlangıç/bitiş kaydedilir.
- Yalnız aut → `treated_autocratization`
- Yalnız dem → `treated_democratization`
- aut **sonra** dem (otokratikleşmeyi demokratikleşme izliyor) → `treated_reversed`
- dem sonra aut (otokratikleşmeyle bitiyor) → `treated_autocratization`

**ambiguous:** epizot yok ama libdem değişimi CI bandı dışında; ya da bir ülkede 2013/latest libdem
verisi veya CPI verisi eksik.

### "latest" yılı seçimi (önemli)
Öneri §4.1 kuralı testi açıkça **"compare libdem_2024 with the 2013 codelow/codehigh band"**
diye yazar; dolayısıyla nokta karşılaştırma yılı olarak **2024** alındı. V-Dem v16 ayrıca 2025'i
de içerir, ancak 2025 kodlamaları en yeni/en oturmamış olanlardır ve kullanıldığında birkaç köklü
demokrasi (Belçika, İspanya, İzlanda, Litvanya, Yeni Zelanda) yalnızca 2025'teki küçük düşüş
nedeniyle `ambiguous`'a düşer. Bu nedenle birincil yıl 2024, 2025 ise **duyarlılık** olarak
raporlanır (aşağıya bakınız). `libdem_latest_year=2024` sütunu bunu belgeler.

## Kaynaklar (dosya + sürüm/sayfa)
- **V-Dem**: `data/governance/vdem/vdem.RData` (V-Dem v16, Mart 2026; `v2x_libdem` +
  `_codelow`/`_codehigh`), pyreadr ile okundu.
- **ERT epizodları**: `data/governance/ert/ert.csv` (ERT v16; `aut_ep*` / `dem_ep_start_year` /
  `dem_ep_end_year`); tanımlar `ERT_codebook_v16.pdf`.
- **CPI**: `data/governance/cpi/CPI2025_Results.xlsx`, sayfa (sheet) *"CPI Timeseries 2012 - 2025"*,
  'CPI score 2013'…'CPI score 2025' sütunları. (Dosya "strict OOXML" olduğundan openpyxl/calamine
  okuyamadı; sheet XML'i doğrudan ayrıştırıldı.) `claim_check/evidence/cpi/CPI2024-Results-and-trends.xlsx`
  2012–2024 için çapraz-doğrulama olarak mevcuttur.
- **OECD üyeliği**: `data/pisa/2025/73451bc5-en.pdf`, **Tablo 1**, basılı s.47 / PDF s.49
  ("OECD Member countries in PISA 2025"), betikte pdftotext ile ayrıştırıldı → **38 üye**.
- **Kâğıt-tabanlı 2015**: Jerrim vd. 2018, dipnot 1, **s.1**
  (`docs/literature/Jerrim_Revised_Main_Body_27_11_2017_Clean.pdf`).
- **Uyarı yıldızı döngüleri**: Volume I PDF'leri (kaynak sayfalar `asterisk_cycles.csv` içinde):
  2015 → PDF s.83 ve dipnot 2, s.108; 2018 → Tablo I.4.1 altındaki '1' dipnotu, s.60 (s.59–64'te
  kullanıldı); 2022 → Reader's Guide s.18–22; 2025 → Reader's Guide s.18–20.

## Sınıf başına sayılar (tüm evren, N=179)
| class | n |
|---|---|
| treated_autocratization | 57 |
| ambiguous | 37 |
| stable_clean | 25 |
| stable_corrupt | 24 |
| treated_reversed | 19 |
| treated_democratization | 17 |

### Yalnız OECD üyeleri (N=38 — önerinin asıl donör evreni)
| class | n | ülkeler |
|---|---|---|
| stable_clean | 16 | AUS, BEL, CAN, DNK, EST, FRA, ISL, IRL, JPN, LVA, LTU, LUX, NZL, NOR, ESP, CHE |
| stable_corrupt | 1 | COL |
| treated_autocratization | 10 | CZE, GRC, HUN, ITA, MEX, SVK, SVN, TUR, GBR, USA |
| treated_reversed | 2 | POL, KOR |
| ambiguous | 9 | AUT, CHL, CRI, FIN, DEU, ISR, NLD, PRT, SWE |

**Uygun donör havuzu (stabil OECD) = 17 ülke** (16 temiz + 1 yozlaşmış: Kolombiya).

## Çapraz kontroller (ledger) — hepsi tuttu
- **TUR**: treated_autocratization; ERT epizodu `TUR_2005_2017` → başlangıç **2005** (yani 2013 veya
  öncesi), 2013–2025 ile kesişiyor. Not: ERT'nin bu çıkarımında epizot 2017'de bitmiş görünür.
- **GEO**: treated_autocratization; aut başlangıcı **2017** (`GEO_2017_2025`); ayrıca dem `2012–2016`
  (dem önce → aut sonra, otokratikleşmeyle bitiyor, "reversed" değil).
- **HUN**: treated_autocratization; aut **2006–2025** (başlangıç 2006).
- **SRB**: treated_autocratization; aut **2010–2025** (başlangıç 2010).
- **POL**: treated_reversed; aut **2016–2021** → dem **2023–2025** (otokratikleşmeyi
  demokratikleşme izliyor).
- **EST**: stable_clean (epizot yok; libdem değişimi CI içinde; ortalama CPI 73.2 > 50).

## Duyarlılık: latest=2024 yerine 2025 kullanılırsa sınıf değişen ülkeler
ALB (stable_corrupt→ambiguous), BEL/ESP/ISL/LTU/NZL (stable_clean→ambiguous),
LBR/SLE/VUT (ambiguous→stable_corrupt). Diğer tüm ülkelerin sınıfı değişmez. Epizotla
"treated" olan hiçbir ülke etkilenmez.

## Uyarılar / sınırlamalar
- **Sıkı çift yönlü CI testi**: libdem'i yüksek ülkelerin V-Dem güven bantları dardır; bu nedenle
  küçük ama bandı aşan düşüşler (ör. AUT −0.045, SWE −0.039, DEU −0.075) epizot olmasa da
  `ambiguous`'a düşer. Analist isterse testi "veya" (bantlardan biri örtüşüyorsa stabil) olarak
  gevşetebilir; `change_outside_ci` ve `reason` sütunları şeffaflığı sağlar.
- **ERT epizot sansürü**: ert.csv'de birçok aut epizodu 2025'te "açık" (bitiş=2025) görünür; bu,
  epizodun 2025'te bittiği değil, veri kesim yılında hâlâ sürdüğü anlamına gelir.
- **Türkiye epizodu 2005–2017**: ERT bu çıkarımında Türkiye epizodunu 2017'de sonlandırır (2018+
  için aut_ep=0). Kural gereği bu epizot 2013–2025 ile kesiştiğinden Türkiye treated_autocratization
  kalır; ERT'nin ne dediği aynen kaydedilmiştir.
- **Kosova ISO3**: V-Dem `XKX`, CPI `KSV` kullanır; CPI birleştirmesinde `KSV→XKX` eşlemesi yapıldı.
- **2025 alt-ulusal yıldızlar**: 7 Kanada eyaleti + Murcia (İspanya) ülke düzeyi PISA birimi
  olmadığından `asterisk_cycles.csv`'de ayrı (iso3 boş) satırlar olarak kaydedildi.
- **2018 İspanya**: Bu ciltteki resmî açıklama '1' dipnotu 4 ülkeyi kapsar (HKG, NLD, PRT, USA);
  İspanya'nın ayrıca belgelenen 2018 okuma-verisi uyarısı bu dipnot kümesinde yer almaz ve bu PDF'de
  ayrı bir yıldız olarak bulunamadı.
- **paper_based / asterisk** listelerinin CPI/V-Dem ISO3'leriyle nihai eşlemesi ve PISA katılımcı
  listesiyle birleştirme sonraki adımda yapılacaktır.
