# RESULTS — Makale 2 revizyonu (betik 55)

29 Eyl 2026 · `analysis/55_paper2_revizyon.py` → `data/derived/paper2_revizyon/` (`sd_series.csv`, `timeline_changes.csv`, `frame_normalised.csv`, `restated_2025_defB.csv`, `bounds_by_transition.csv`, `mode_transition_changes.csv`, `mode_transition_levels.csv`, `gender_composition_2025.csv`, `summary.json`) · şekiller `analysis/figures/paper2/{timeline,frame_normalised,mode_transition}.png` · Yazan: Claude (Opus 5.5, Cowork), yazarın revizyon notları üzerine · Makaledeki etiket: **[E42]** · T1: taze bağlamlı ajan, 29 Eyl (≈ 174 kalem; 5 yanlış, 6 ifade, 1 doğrulanamaz → düzeltildi; betikte sayı değiştiren hata yok)

| | Bulgu | Değer | Dosya |
| :-: | :--- | :--- | :--- |
| 🔴 | Genel dışlama, ortak tanım A (açık öğretim + MESEM her döngüde çerçeve dışı)¹ | 2015 1,10 · 2018 2,06–2,17 · 2022 2,34–2,43 · 2025 2,74* (%) | `frame_normalised.csv` |
| 🔴 | Artışın kaynağı | okul içi dışlama 0,58 → 1,50 → 1,83 → 2,11; diğer okul düzeyi 0,52 · 0,57–0,68 · 0,52–0,61 · 0,63 (kayıtlıların %'si) | aynı |
| 🔴 | 2015→2018 basamağı | yayımlanan 4,57 puan; ortak tanımla 0,97–1,07 (0,92'si okul içi); 2015→2025 ortak tanımla +1,64 (okul içi +1,54) | `summary.json` → `exclusion_jumps_pp` |
| 🟡 | 2025, 2018–2022 tanımıyla (tanım B), bu dosyanın X aralığıyla | genel dışlama 5,99–6,08 (E19'un X = 43.932 senaryosu 6,57 verir ama 2025'in 6.796 "diğer" dışlamasını iki kez sayar; T1 29 Eyl) | `restated_2025_defB.csv` |
| 🔴 | Tüm 15 yaşlıların payı (%)² | temsil edilen 69,9 · 72,6 · 73,7 · 72,2; okul içi dışlanan 0,40 · 1,10 · 1,37 · 1,56; açık öğretim + MESEM (listelenip dışlanan) — · 3,09 · 2,97 · —; çerçeve dışı / kayıt dışı / diğer 29,3 · 22,7 · 21,5 · 25,7 | aynı |
| 🔴 | Mekanik sınır, ortak tanım³ | 2015→2018: 1 SD 0,86–1,01, 2 SD 1,71–2,03 puan (gerçek +33,1 / +37,3 / +42,8; 2 SD'de %4–6); 2015→2025: 1 SD 1,58–1,76, 2 SD 3,16–3,52 (gerçek +41,1 / +43,8 / +68,8; 2 SD'de %9 / %7 / %5) | `bounds_by_transition.csv` |
| 🔴 | 2015→2018 sıçramasını tek başına üretmek için gereken fark | 33–36 SD (mat), 37–41 (okuma), 45–50 (fen) | aynı (`required_gap_sd_*`) |
| 🔴 | Mod geçişi 2012→2015⁴ | −27,5 / −47,2 / −37,9; 52 sistemde en olumsuz 2. / 1. / 1.; z −2,42 / −3,25 / −2,45 (E20 ile birebir) | `mode_transition_changes.csv` |
| 🔴 | 2015→2018 | +33,1 / +37,3 / +42,8; 52 sistemde en olumlu 1. / 1. / 1.; z +4,00 / +4,07 / +4,77 | aynı |
| 🔴 | 2012→2018 net | +5,5 / −9,9 / +4,9; 51 sistemde olumlu uçtan 14., olumsuz uçtan 20., olumlu uçtan 9.; z +0,41 / −0,27 / +0,85 → olağan | aynı |
| 🟡 | OECD ortalaması-35'e uzaklık (puan) | 2012 −42,6 / −18,0 / −35,1 · 2015 −66,8 / −61,9 / −65,3 · 2018 −36,2 / −22,0 / −20,9; OECD SD biriminde 2012 −0,46 / −0,19 / −0,38 · 2015 −0,75 / −0,65 / −0,69 · 2018 −0,40 / −0,22 / −0,22 | `mode_transition_levels.csv` |
| 🟡 | Sabit 51 sistemde düzey z'si | mat −0,63 → −1,22 → −0,59 · okuma −0,16 → −1,33 → −0,27 · fen −0,49 → −1,33 → −0,26 (2012 → 2015 → 2018) | aynı |
| 🟡 | Baz seçimine duyarlılık | 2015→2025 +41,1 / +43,8 / +68,8; 2012→2025 +13,6 / −3,4 / +30,9 | `timeline_changes.csv` |
| 🟡 | 2025 cinsiyet farkı (erkek − kız), Türkiye | mat +17,8 (SH 5,1) · okuma −21,8 (4,8) · fen +4,0 (5,0); OECD ort. +13,1 / −29,6 / −1,2 | `gender_composition_2025.csv` |
| 🟡 | Kız payı kayıt payına çekilirse (bileşim etkisi)⁵ | mat +1,00 · okuma −1,23 · fen +0,23 puan | aynı |
| 🟢 | Türkiye öğrenci SD'leri (yayımlanmış) | 2012 91,1 / 85,9 / 79,9 · 2015 81,9 / 82,4 / 79,3 · 2018 88,2 / 87,7 / 83,5 · 2022 89,8 / 86,5 / 89,4 · 2025 97,1 / 90,7 / 94,5 (mat / okuma / fen) | `sd_series.csv` |

**Legend:** 🔴 makaleye giren ana sayı · 🟡 destekleyici · 🟢 girdi. Sıra hep mat / okuma / fen. * 2025 taslak oranı; 2018–2022 ile yayımlandığı tanımla karşılaştırılamaz.

¹ 2018 ve 2022'de listelenip dışlanan kurumların öğrenci sayısı (X) yayımlanmadı. TR18 Böl. 14 (Türkiye): "The increase in exclusions over previous cycles could be attributed to a particular type of non-formal education institutions which were previously not listed in sampling frames, and which were listed, but excluded, in 2018." Varsayım: bu kurumlar dışındaki okul düzeyi dışlamalar 2018/2022'de 2015 (5.746) ile 2025 (6.796) düzeyleri arasında → X 2018'de 37.132–38.182, 2022'de 37.136–38.186. X hem okul düzeyi dışlamadan hem kayıtlı nüfustan düşülür.
² Payda tüm 15 yaşlılar (Coverage Index 3'ün paydası); yalnız "açık öğretim + MESEM / diğer okul dışlaması" bölünmesi ¹ varsayımına bağlı (orta değer).
³ μ_tutulan − μ_tüm = q × (μ_tutulan − μ_dışlanan); fark k·σ, σ her döngünün kendi öğrenci SD'si (E8 kuralı); geçiş katkısı q₂kσ₂ − q₁kσ₁. Yayımlanan tanımla 2015→2018 aynı kural 3,86–4,10 / 7,72–8,19 verir; E19'un 3,8–4,0 / 7,6–8,1'i Δq × σ₂₀₁₈ kuralıyla. Metinde bu dosyanın kuralı (3,9–4,1 / 7,7–8,2), parantez içinde E19'unki (T1 29 Eyl: iki kuralın karışması §3.5 ile tutarsızdı).
⁴ Küme: PISA 2025 Cilt I eğilim tablolarındaki (I.B1.2a.36–38) sistemlerden 2015 ve 2018'de bilgisayarla test eden, karşılaştırılan döngülerde üç alanda puanı olanlar; 2012→2015 ve 2015→2018 kümeleri birer sistemle ayrışır (İspanya yalnız ilkinde, Dominik Cumhuriyeti yalnız ikincisinde; T1). Sabit 51 sistemde sıralar değişmez (2/1/1 ve 1/1/1), z'ler −2,39 / −3,22 / −2,42 ve +3,96 / +4,08 / +4,75 (T1 yeniden hesabı). 2015 kâğıt listesi `data/derived/paper_based_2015.csv` (Jerrim vd. 2018), 2018 kâğıt listesi OECD (2019) Cilt I s. 33 (dokuz ülke). z = (Türkiye − küme ortalaması) / küme SD (ddof 1, Türkiye kümede; E20 ile aynı).
⁵ (s_kayıt − s_PISA) × (kız − erkek); s_PISA 0,5425, s_kayıt 0,4863 (E41). Kız ve erkek ortalamaları sabit tutulur; dışarıda kalan erkeklerin seçilimi ölçülmez.
