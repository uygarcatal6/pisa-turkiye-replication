# analysis/ — analiz hattı

Tek giriş noktası (proje kökünden çalıştır):

```bash
python analysis/run_all.py
```

`Rscript` PATH'te olmadığı için otomatik bulunur (`C:/Program Files/R/R-4.6.1/bin/x64/Rscript.exe`);
istersen `RSCRIPT` ortam değişkeniyle üzerine yazabilirsin. Her adımın çıktısı
`analysis/logs/<adım>.log` dosyasına gider; bir adım hata verirse hat orada durur.
Çalıştırmadan önce `data/derived/` klasörünün yedeği `data/_derived_backup_<tarih>/`
altına alınır (son 3 yedek tutulur).

Seçenekler: `--only 03 04`, `--from 03`, `--dry-run`, `--no-backup`.

## Adımlar

| # | Dil | Betik | İş | Ana çıktı |
|---|---|---|---|---|
| 01 | Python | `01_build_panel.py` | OECD annex tabloları + WGI/CPI/ERT → panel (her satırda köken) | `data/derived/analysis_panel.csv` |
| 02 | Python | `02_institutional_screen.py` | V-Dem/ERT + CPI ile stabil/tedavi sınıflaması, 2015 kâğıt listesi, uyarı-yıldızı döngüleri | `data/derived/institutional_screen.csv` |
| 03 | R | `03_synth.R` | Ortalamadan arındırılmış sentetik kontrol + placebo-in-space (TUR, HUN, GEO) | `data/derived/synth/synth_summary.csv` |
| 04 | R | `04_cs_did.R` | Callaway–Sant'Anna kademeli DiD + olay çalışması | `data/derived/did/csdid_summary.json` |
| 05 | R | `05_mechanisms.R` | Kapsam, plasebo alan (CPS vs çekirdek), OECD'ye göre değişim | `data/derived/mechanisms/mechanisms_summary.json` |

Faz 3 (sağlamlık + mekanizmalar; `run_all.py` hafif adımlar 09/10/11/14, ağır adımlar `--heavy` ile 06/07/08/12b/13/15):

| # | Dil | Betik | İş | Ana çıktı |
|---|---|---|---|---|
| 06 | Python | `06_extract_2025_tables.py` | 2025 dışlama/yanıt/çaba tabloları (Vol I PDF + annex) | `data/derived/effort_2025.csv` |
| 07 | Python | `07_microdata_effort.py` | Çaba göstergeleri 2015–2022 (COG mikroverisi: atlama, yetişilmeyen, hızlı tahmin) | `data/derived/effort_microdata.csv` |
| 08 | Python | `08_composition.py` | Türkiye okul-türü bileşimi (STRATUM, W_FSTUWT) | `data/derived/turkiye_school_type_composition.csv` |
| 09 | R | `09_robustness.R` | Leave-one-out, in-time placebo (2009), donör ızgarası, ön dönem | `data/derived/robustness/robustness_summary.json` |
| 10 | Python | `10_placebo_domain.py` | Koşullu plasebo alan: CPS ~ çekirdek (2025) | `data/derived/mechanisms/placebo_conditional_summary.json` |
| 11 | R | `11_coverage_adjusted.R` | Kapsam-düzeltilmiş sentetik kontrol (geçersiz; bkz. RESULTS_PHASE3 §4) | `data/derived/coverage_adj/coverage_adjusted_summary.json` |
| 12a/12b | Python | `12a_inspect_2025_process.py`, `12b_effort_2025_process.py` | 2025 süreç verisi (12 GB): madde süreleri, hızlı tahmin, sıfır eylem | `data/derived/effort_2025_process.csv` |
| 13 | Python | `13_creative_thinking_2022.py` | 2022 yaratıcı düşünme: yayımlanmış tablo + CRT mikroveri çapraz-kontrolü; **TUR/GEO katılmadı** | `data/derived/mechanisms/placebo_conditional_2022_summary.json` |
| 14 | Python | `14_meb2025_report_extracts.py` | MEB PISA 2025 Türkiye Raporu grafik değerleri (PDF metniyle doğrulamalı) | `data/derived/meb2025_report_extracts.csv` |
| 15 | Python | `15_cps2015_placebo.py` | 2015 işbirlikli problem çözme: mikroveriden ağırlıklı ülke ortalamaları (PV1–10CLPS × W_FSTUWT) + koşullu plasebo testi; **TUR ve HUN katıldı, GEO katılmadı** | `data/derived/mechanisms/placebo_conditional_2015cps_summary.json` |

Faz 4 (Gemini yöntem memolarından alınan tahminciler; hafif adımlar, `run_all.py` içinde; ortak panel matrisi `_panel_matrix.py`; bulgular `RESULTS_PHASE4.md`):

| # | Dil | Betik | İş | Ana çıktı |
|---|---|---|---|---|
| 16 | Python | `16_synthetic_did.py` | Sentetik DiD (Arkhangelsky vd. 2021, Alg. 1/4 birebir; `synthdid` CRAN'da değil, yalnız GitHub) — iki pencere, üç havuz, plasebo SE | `data/derived/sdid/sdid_results.csv` |
| 16b | R | `16b_synthdid_crosscheck.R` | Referans `synthdid` (GitHub, remotes ile) ile 18 vakada çapraz doğrulama; maks τ̂ farkı 0,30 | `data/derived/sdid/r_synthdid_crosscheck.csv` |
| 17 | Python | `17_matrix_completion_conformal.py` | MC-NNM matris tamamlama (Athey vd. 2021) + konformal çıkarım (Chernozhukov, Wüthrich & Zhu 2021) + Python SC = R Synth çapraz doğrulaması | `data/derived/mc_conformal/{mc_results,conformal_results,r_vs_python_sc}.csv` |
| 18 | R | `18_macro_partition.R` | Makro-bölümleme sağlamlığı: MOB/CTree (`partykit`) + Mahalanobis kNN; Türkiye kendi makro-yaprağında 1/14 | `data/derived/macro_partition/results.json` |

Şekiller: `analysis/figures/`. Bulgular: `analysis/RESULTS.md` (Opus 4.8 denetimi: `RESULTS_AUDIT.md`), `analysis/RESULTS_PHASE3.md` (denetim: `RESULTS_PHASE3_AUDIT.md`), `analysis/RESULTS_PHASE4.md` (denetim: `RESULTS_PHASE4_AUDIT.md`).

## Neden hibrit (Python + R)

- **R**: `Synth` (Abadie) ve `did` (Callaway & Sant'Anna) bu iki tahmincinin kanonik
  uygulamaları; hakem bu paketleri bekler. Python karşılıkları (`pysyncon`, `SparseSC`,
  `differences`, `pyfixest`) daha az test edilmiş ve plasebo/olay-çalışması altyapısını
  elle kurmayı gerektirir.
- **Python**: Excel/PDF/RData ayrıştırma, köken (provenance) sütunları ve sıradaki
  mikroveri işi (SPSS dosyaları, yanıt süreleri, plausible values — `pyreadstat`/`pandas`)
  burada çok daha rahat.

R paketleri kullanıcı kütüphanesinde kurulu (`dplyr`, `readr`, `tidyr`, `ggplot2`,
`readxl`, `purrr`, `stringr`, `Synth`, `did`, `kernlab`, `optimx`, `rgenoud`, `jsonlite`).
Yeniden kurulum: `analysis/logs/r_install.log` içindeki komut.

## reference/

`analysis/reference/` — Stanford `Auto-Empirical-Research-Skills` reposundan alınan
DiD/Synth referans şablonları (CC-BY-SA 4.0, atıf `analysis/reference/NOTICE.md`).
Çalıştırılmaz, yalnızca örnek olarak okunur.

| 19 | Python | `19_exclusion_frame_2025.py` | Çerçeve/dışlama serisi 2015–2025 (Vol I Annex A2 + 2025 TR taslak T14.A.1/T14.A.20) + ülkeler arası Δdışlama×Δpuan korelasyonu + mekanik sınır; bulgular `V4_CERCEVE_DISLAMA_NOTU_2026-09-19.md` | `data/derived/exclusion_frame/summary.json` |
| 20 | Python | `20_mode_transition_2015.py` | 2015'te bilgisayar tabanlı uygulamaya geçen sistemler içinde Türkiye'nin 2012→2015 değişimi (v4 §4.5, Şekil 2; 52 sistem — OECD ortalama satırları dışarıda, 20 Eyl gece düzeltmesi), G4 okul-düzeyi dışlama istikrar sıralaması (Ek E), Şekil 1; etiket [E20] | `data/derived/mode_transition_2015/summary.json` |
| 21 | Python | `21_breakyear_sensitivity.py` | Kırılma-yılı duyarlılığı (v4 §4.5'in zorunlu testi): 2015 sonrası dönemde / ön dönemde / matristen atılmış; SC, trend-düzeltmeli SC, SDiD (16'nın fonksiyonları), 2012-tabanlı DiD; placebo-in-space; Şekil 3; etiket [E21] | `data/derived/breakyear/summary.json`, `breakyear_table.md` |
| 22 | Python (ağır) | `22_ict_mode_familiarity.py` | 2015 çukuru bilgisayar aşinalığıyla açıklanıyor mu? 2015/2018 öğrenci anketi ICT ortalamaları, 52 sistemde (ICT ölçüsü olan 49) geçiş cezası ~ ICT regresyonu, Türkiye için gereken değer; bulgu `V4_ICT_MOD_BULGUSU_2026-09-20.md` (diğer oturum, 20 Eyl; 21→22 yeniden numaralandı) | `data/derived/mode_transition_2015/ict_summary.json` |
| 23 | Python | `23_donor_ablation.py` | Donör kriteri ablasyonu (spesifikasyon eğrisi): C1 OECD / C2 tarama (L0–L3) / C3 kâğıt-2015 (açık-kapalı-adj) / C4 yıldız; 16 hücre × 3 alan + C2 kademeleri + mod-düzeltilmiş havuz; **E bloğu: düzey eşiği** (libdem_2013 ≥ {0,20; 0,25; 0,289; 0,35} × libdem'i olmayan ülke düşer/kalır — Makao tanısı); geçiş cezası %95 GA + MDE(%80); placebo-in-space p_gap/p_ratio, dışbükey örtü, en-ağır-donör LOO; mod haritası ülke×döngü; Şekil 4; etiket [E23]; rapor `V4_DONOR_ABLASYON_SONUC_2026-09-20.md` | `data/derived/donor_ablation/summary.json`, `ablation_grid.csv` (309 satır), `transition_penalty.csv` |
| 25 | Python | `25_problem_solving_2012.py` | **Kırılma öncesi plasebo noktası:** PISA 2012 yaratıcı problem çözme ülke ortalamaları (OECD 2012 Volume V, Table V.A, s. 17; `data/pisa/2012/9789264208070-en.pdf`, PDF'ten ayrıştırılır; mikroveri yok) ~ çekirdek 2012; dört spesifikasyon; TUR/HUN artık, sıra, LOO; mod uyarısı (PS bilgisayarda, çekirdek kâğıtta); etiket [E25] | `data/derived/mechanisms/placebo_conditional_2012ps.csv`, `_summary.json`, `data/derived/ps2012_published_means.csv` |
| 24 | Python | `24_placebo_backbone.py` | Plasebo-alan omurgası 2012–2025: 25/10/13/15 çıktıları (2012 yaratıcı PS, 2015 işbirlikli PS, 2018 küresel yetkinlik = yok, 2022 yaratıcı düşünme = TUR yok, 2025 hesaplamalı PS) yan yana; Türkiye–Macaristan ayrımı her spesifikasyonda; **CPS 2015 ülke ortalamalarının çapraz-kontrolü**: OECD Volume V Figure V.1.1 (s. 43–44, PDF'ten ayrıştırılır; birincil) + UK DfE Tablo 3–5 (ikincil); Şekil 5; etiket [E24]; rapor `V4_PLASEBO_OMURGA_SONUC_2026-09-20.md` | `data/derived/placebo_backbone/summary.json`, `backbone_residuals.csv`, `tur_hun_separation.csv`, `cps2015_crosscheck_oecd_volv.csv`, `cps2015_crosscheck_dfe.csv` |
