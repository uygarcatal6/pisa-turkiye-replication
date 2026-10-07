#!/usr/bin/env Rscript
# Makro-bölümleme sağlamlık testi: donör havuzunu elle kurmak yerine makro göstergelerle
# (V-Dem libdem 2013, Δlibdem, CPI ortalaması, WGI yolsuzluk kontrolü, kapsam) veriye böldürüp
# Türkiye'nin 2015→2025 puan değişiminin KENDİ makro-yaprağı içinde uç olup olmadığına bakar.
# Kaynak fikir: "Macro-Micro Recursive Partitioning Methodology" memosu (Gemini, 2026-09-16) —
# MOB (Zeileis, Hothorn & Hornik 2008) ve CTree (Hothorn, Hornik & Zeileis 2006), partykit paketi.
# Üç kurgu:
#   (1) MOB / lmtree: yaprak modeli  değişim ~ 2015 düzeyi  (ortalamaya dönüş), bölme değişkenleri makro.
#   (2) CTree: değişim ~ makro + düzey (permütasyon testli koşullu çıkarım ağacı).
#   (3) Makro-uzayda en yakın k komşu (Mahalanobis): Türkiye'nin değişimi komşularının dağılımında nerede?
# Uyarı (memonun kendi uyarısı): N≈66 ülke ile ağaçlar kararsızdır; leave-one-out (Türkiye çıkarılınca
# bölünme değişiyor mu) raporlanır. Bu bir sağlamlık/betimleme testidir, nedensel kimlik iddiası değildir.
# Çıktı: data/derived/macro_partition/{country_frame.csv, mob_tree.txt, ctree.txt, results.json}
# Yazan: Claude Fable 5.1, 2026-09-16.
suppressPackageStartupMessages({ library(dplyr); library(readr); library(jsonlite); library(partykit) })
root <- normalizePath(file.path(dirname(sub("--file=", "", grep("--file=", commandArgs(FALSE), value = TRUE))), ".."))
D <- file.path(root, "data", "derived"); OUT <- file.path(D, "macro_partition"); dir.create(OUT, showWarnings = FALSE)

panel  <- read_csv(file.path(D, "analysis_panel.csv"), show_col_types = FALSE) %>% filter(!is.na(iso3), nchar(iso3) == 3)
screen <- read_csv(file.path(D, "institutional_screen.csv"), show_col_types = FALSE)
paper  <- read_csv(file.path(D, "paper_based_2015.csv"), show_col_types = FALSE)

wide <- function(v) panel %>% select(iso3, cycle, all_of(v)) %>% tidyr::pivot_wider(names_from = cycle, values_from = all_of(v), names_prefix = paste0(v, "_"))
fr <- wide("math_mean") %>% inner_join(wide("reading_mean"), by = "iso3") %>% inner_join(wide("science_mean"), by = "iso3") %>%
  inner_join(panel %>% filter(cycle == 2015) %>% select(iso3, coverage_2015 = coverage_index3, cc_2015 = cc_est, oecd = oecd_member), by = "iso3") %>%
  inner_join(screen %>% select(iso3, libdem_2013, delta_libdem, cpi_mean = cpi_mean_2013_2025, class), by = "iso3") %>%
  mutate(paper2015 = as.integer(iso3 %in% paper$iso3),
         level_2015 = (math_mean_2015 + reading_mean_2015 + science_mean_2015) / 3,
         change_math = math_mean_2025 - math_mean_2015, change_reading = reading_mean_2025 - reading_mean_2015,
         change_science = science_mean_2025 - science_mean_2015, change_avg = (change_math + change_reading + change_science) / 3,
         oecd = as.integer(as.numeric(oecd) > 0)) %>%
  filter(!is.na(change_avg), !is.na(libdem_2013), !is.na(cpi_mean), !is.na(level_2015))
n_complete <- sum(complete.cases(fr[, c("libdem_2013", "delta_libdem", "cpi_mean", "cc_2015", "coverage_2015", "oecd", "paper2015")]))
cat("ülke sayısı:", nrow(fr), "| Türkiye var:", "TUR" %in% fr$iso3,
    "| bölme değişkenleri eksiksiz (lmtree/ctree/kNN'nin fiilen kullandığı):", n_complete, "\n")

res <- list(n = nrow(fr), n_complete_partitioning_vars = n_complete,
            note = "lmtree/ctree ve Mahalanobis-kNN yalnız bölme değişkenleri eksiksiz ülkeleri kullanır (listwise); leaf_n = predict atamasıdır")
rank_in <- function(x, who) list(value = round(x[who], 1), rank_from_top = as.integer(rank(-x)[who]), n = length(x))

# ---- (1) MOB
set.seed(20260916)
mob <- lmtree(change_avg ~ level_2015 | libdem_2013 + delta_libdem + cpi_mean + cc_2015 + coverage_2015 + oecd + paper2015,
              data = fr, alpha = 0.10, minsize = 10, bonferroni = TRUE)
capture.output(print(mob), file = file.path(OUT, "mob_tree.txt"))
fr$mob_node <- predict(mob, newdata = fr, type = "node"); fr$mob_resid <- fr$change_avg - predict(mob, newdata = fr)
tn <- fr$mob_node[fr$iso3 == "TUR"]; leaf <- fr %>% filter(mob_node == tn)
res$mob <- list(n_leaves = width(mob), depth = depth(mob), turkey_node = tn, leaf_n = nrow(leaf), leaf_members = leaf$iso3,
                turkey_resid = rank_in(setNames(leaf$mob_resid, leaf$iso3), "TUR"),
                turkey_change = rank_in(setNames(leaf$change_avg, leaf$iso3), "TUR"),
                split_vars = if (width(mob) > 1) unique(unlist(nodeapply(mob, ids = nodeids(mob, terminal = FALSE), FUN = function(n) names(fr)[split_node(n)$varid]))) else character(0))
cat("MOB: yaprak", width(mob), "| Türkiye yaprağı", tn, "n=", nrow(leaf), "| artık", res$mob$turkey_resid$value, "sıra", res$mob$turkey_resid$rank_from_top, "/", nrow(leaf), "\n")
# leave-one-out kararlılık
mob_loo <- lmtree(change_avg ~ level_2015 | libdem_2013 + delta_libdem + cpi_mean + cc_2015 + coverage_2015 + oecd + paper2015,
                  data = fr %>% filter(iso3 != "TUR"), alpha = 0.10, minsize = 10, bonferroni = TRUE)
res$mob$loo_without_turkey_leaves <- width(mob_loo)
# tek-yaprak ise (bölünme yok): tüm örneklemde düzey-koşullu artık
if (width(mob) == 1) {
  cat("MOB bölünmedi (alpha 0.10): makro değişkenler değişimin eğimini/ortalamasını anlamlı bölmüyor; tüm örneklem tek yaprak.\n")
}

# ---- (2) CTree
ct <- ctree(change_avg ~ libdem_2013 + delta_libdem + cpi_mean + cc_2015 + coverage_2015 + level_2015 + oecd + paper2015,
            data = fr, control = ctree_control(alpha = 0.10, minbucket = 8))
capture.output(print(ct), file = file.path(OUT, "ctree.txt"))
fr$ct_node <- predict(ct, newdata = fr, type = "node"); fr$ct_resid <- fr$change_avg - predict(ct, newdata = fr)
tn2 <- fr$ct_node[fr$iso3 == "TUR"]; leaf2 <- fr %>% filter(ct_node == tn2)
res$ctree <- list(n_leaves = width(ct), turkey_node = tn2, leaf_n = nrow(leaf2), leaf_members = leaf2$iso3,
                  turkey_resid = rank_in(setNames(leaf2$ct_resid, leaf2$iso3), "TUR"))
cat("CTree: yaprak", width(ct), "| Türkiye yaprağı n=", nrow(leaf2), "| artık", res$ctree$turkey_resid$value, "sıra", res$ctree$turkey_resid$rank_from_top, "\n")

# ---- (3) Makro-uzayda en yakın komşular (Mahalanobis; düzey dahil ve hariç)
X <- fr %>% select(libdem_2013, delta_libdem, cpi_mean, cc_2015, coverage_2015) %>% as.matrix(); rownames(X) <- fr$iso3
X <- X[complete.cases(X), ]; S <- cov(X)
dm <- mahalanobis(X, X["TUR", ], S)
for (k in c(8, 12)) {
  nb <- names(sort(dm))[2:(k + 1)]
  ch <- setNames(fr$change_avg, fr$iso3)[c("TUR", nb)]
  res[[paste0("knn", k)]] <- list(neighbours = nb, turkey_change = round(ch["TUR"], 1), neighbours_mean = round(mean(ch[nb]), 1),
                                  neighbours_sd = round(sd(ch[nb]), 1), rank_from_top = as.integer(rank(-ch)["TUR"]),
                                  z = round((ch["TUR"] - mean(ch[nb])) / sd(ch[nb]), 2),
                                  per_domain = list(math = round(setNames(fr$change_math, fr$iso3)[nb] %>% mean(), 1),
                                                    reading = round(setNames(fr$change_reading, fr$iso3)[nb] %>% mean(), 1),
                                                    science = round(setNames(fr$change_science, fr$iso3)[nb] %>% mean(), 1)))
  cat(sprintf("kNN k=%d: komşular %s | Türkiye %+.1f vs komşu ort %+.1f (sd %.1f) z=%.2f sıra %d/%d\n", k, paste(nb, collapse = " "),
              ch["TUR"], mean(ch[nb]), sd(ch[nb]), res[[paste0("knn", k)]]$z, res[[paste0("knn", k)]]$rank_from_top, k + 1))
}
# tüm örneklemde düzey-koşullu artık (referans)
lmfit <- lm(change_avg ~ level_2015, data = fr); fr$lm_resid <- resid(lmfit)
res$level_conditional_all <- list(slope = round(coef(lmfit)[2], 3), turkey_resid = rank_in(setNames(fr$lm_resid, fr$iso3), "TUR"))
cat("Düzey-koşullu artık (tüm ülkeler): Türkiye", res$level_conditional_all$turkey_resid$value, "sıra", res$level_conditional_all$turkey_resid$rank_from_top, "/", nrow(fr), "\n")
write_csv(fr, file.path(OUT, "country_frame.csv"))
write_json(res, file.path(OUT, "results.json"), auto_unbox = TRUE, pretty = TRUE)
cat("DONE macro_partition\n")
