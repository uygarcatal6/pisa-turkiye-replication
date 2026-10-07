# Sağlamlık testleri (proposal §4.1'in donör kuralını sınamak için):
#   R1  leave-one-out: ana havuzdan her donör sırayla çıkarılır
#   R2  in-time placebo: sahte kırılma 2009 (ön 2003–2006, post 2009–2012) — gerçek kırılmadan önce açık çıkmamalı
#   R3  donör kuralı ızgarası: yıldız kuralı, ambiguous, OECD kısıtı, kâğıt-2015 kuralı açık/kapalı
#   R4  ön dönem duyarlılığı: 2003–2012 yerine 2006–2012 / 2009–2012
# Yazan: Claude Fable 5.1 (kod), 2026-09-15. Çekirdek: analysis/_synth_core.R
ROOT <- Sys.getenv("PISA_ROOT", getwd()); setwd(ROOT)  # depo kökünden çalıştırın
source("analysis/_synth_core.R")
suppressPackageStartupMessages({ library(ggplot2); library(jsonlite) })
OUT <- "data/derived/robustness"; FIG <- "analysis/figures"
dir.create(OUT, recursive = TRUE, showWarnings = FALSE); dir.create(FIG, showWarnings = FALSE)
log_lines <- c(); logf <- function(...) { s <- paste0(...); cat(s, "\n"); log_lines <<- c(log_lines, s) }

TREATED <- "TUR"
PRE  <- c(2003, 2006, 2009, 2012)
POST <- c(2015, 2018, 2022, 2025)

# ---------------- R1: leave-one-out ----------------
logf("== R1 leave-one-out (ana havuz: stabil OECD, katı kurallar) ==")
loo_rows <- list()
for (d in DOMS) {
  outcome <- mean_cols[[d]]
  pre <- trim_pre(TREATED, PRE, outcome)
  donors <- build_pool(TREATED, c(pre, POST), "stable_all", TRUE, outcome)
  if (length(donors) < 3) { logf("  ", d, ": donör yetersiz (", length(donors), ")"); next }
  base <- run_one(TREATED, donors, pre, POST, outcome)
  loo_rows[[length(loo_rows) + 1]] <- tibble(domain = d, dropped = "(none)", n_donors = length(donors),
                                             pre_rmspe = base$pre_rmspe, gap_2025 = base$gap_last, post_gap_mean = base$post_gap_mean)
  for (dn in donors) {
    r <- tryCatch(run_one(TREATED, setdiff(donors, dn), pre, POST, outcome), error = function(e) NULL)
    if (is.null(r)) next
    loo_rows[[length(loo_rows) + 1]] <- tibble(domain = d, dropped = dn, n_donors = length(donors) - 1,
                                               pre_rmspe = r$pre_rmspe, gap_2025 = r$gap_last, post_gap_mean = r$post_gap_mean)
  }
  rng <- range(map_dbl(loo_rows[map_chr(loo_rows, ~ .x$domain[1]) == d], ~ .x$gap_2025[1]))
  logf(sprintf("  %-8s temel 2025 açığı %.1f | LOO aralığı %.1f – %.1f", d, base$gap_last, rng[1], rng[2]))
}
loo <- bind_rows(loo_rows); write_csv(loo %>% mutate(across(where(is.numeric), ~ round(.x, 2))), file.path(OUT, "leave_one_out.csv"))

# ---------------- R2: in-time placebo (sahte kırılma 2009) ----------------
logf("\n== R2 in-time placebo: sahte kırılma 2009 (ön 2003–2006, post 2009–2012) ==")
it_rows <- list()
for (d in DOMS) {
  outcome <- mean_cols[[d]]
  pre_f <- trim_pre(TREATED, c(2003, 2006), outcome)
  post_f <- c(2009, 2012)
  if (length(pre_f) < 2) { logf("  ", d, ": sahte ön dönem <2 gözlem, atlandı"); next }
  donors <- build_pool(TREATED, c(pre_f, post_f), "stable_all", TRUE, outcome)
  if (length(donors) < 3) { logf("  ", d, ": donör yetersiz"); next }
  r <- tryCatch(run_one(TREATED, donors, pre_f, post_f, outcome), error = function(e) NULL)
  if (is.null(r)) { logf("  ", d, ": tahmin hatası"); next }
  it_rows[[length(it_rows) + 1]] <- tibble(domain = d, n_donors = length(donors), pre_rmspe = r$pre_rmspe,
                                           gap_2009 = r$gap[r$cycles == 2009], gap_2012 = r$gap[r$cycles == 2012],
                                           post_gap_mean = r$post_gap_mean)
  logf(sprintf("  %-8s donör=%d ön-RMSPE=%.1f | sahte-post açıkları 2009:%+.1f 2012:%+.1f (ort %+.1f)",
               d, length(donors), r$pre_rmspe, r$gap[r$cycles == 2009], r$gap[r$cycles == 2012], r$post_gap_mean))
}
if (length(it_rows)) write_csv(bind_rows(it_rows) %>% mutate(across(where(is.numeric), ~ round(.x, 2))), file.path(OUT, "in_time_placebo.csv"))

# ---------------- R3: donör kuralı ızgarası ----------------
logf("\n== R3 donör kuralı ızgarası (2025 açığı) ==")
grid <- expand.grid(pool = c("stable_all", "stable_plus_ambiguous"), oecd = c(TRUE, FALSE),
                    drop_ast = c(TRUE, FALSE), drop_paper = c(TRUE, FALSE), stringsAsFactors = FALSE)
g_rows <- list()
for (i in seq_len(nrow(grid))) {
  for (d in DOMS) {
    outcome <- mean_cols[[d]]
    pre <- trim_pre(TREATED, PRE, outcome)
    donors <- build_pool(TREATED, c(pre, POST), grid$pool[i], grid$oecd[i], outcome, grid$drop_ast[i], grid$drop_paper[i])
    if (length(donors) < 3) next
    r <- tryCatch(run_one(TREATED, donors, pre, POST, outcome), error = function(e) NULL)
    if (is.null(r)) next
    g_rows[[length(g_rows) + 1]] <- tibble(domain = d, pool = grid$pool[i], oecd_only = grid$oecd[i],
                                           drop_asterisk = grid$drop_ast[i], drop_paper2015 = grid$drop_paper[i],
                                           n_donors = length(donors), pre_rmspe = r$pre_rmspe,
                                           gap_2025 = r$gap_last, post_gap_mean = r$post_gap_mean,
                                           top_donor = names(which.max(r$weights)), top_w = max(r$weights))
  }
}
gr <- bind_rows(g_rows); write_csv(gr %>% mutate(across(where(is.numeric), ~ round(.x, 2))), file.path(OUT, "donor_rule_grid.csv"))
for (d in DOMS) {
  sub <- gr %>% filter(domain == d)
  if (!nrow(sub)) next
  logf(sprintf("  %-8s %d spesifikasyon | 2025 açığı medyan %+.1f, aralık %+.1f – %+.1f | pozitif oran %.0f%%",
               d, nrow(sub), median(sub$gap_2025), min(sub$gap_2025), max(sub$gap_2025), 100 * mean(sub$gap_2025 > 0)))
}

# ---------------- R4: ön dönem duyarlılığı ----------------
logf("\n== R4 ön dönem duyarlılığı ==")
p_rows <- list()
for (pre_set in list(c(2003, 2006, 2009, 2012), c(2006, 2009, 2012), c(2009, 2012))) {
  for (d in DOMS) {
    outcome <- mean_cols[[d]]
    pre <- trim_pre(TREATED, pre_set, outcome)
    if (length(pre) < 2) next
    donors <- build_pool(TREATED, c(pre, POST), "stable_all", TRUE, outcome)
    if (length(donors) < 3) next
    r <- tryCatch(run_one(TREATED, donors, pre, POST, outcome), error = function(e) NULL)
    if (is.null(r)) next
    p_rows[[length(p_rows) + 1]] <- tibble(domain = d, pre_period = paste(pre, collapse = "-"), n_donors = length(donors),
                                           pre_rmspe = r$pre_rmspe, gap_2025 = r$gap_last, post_gap_mean = r$post_gap_mean)
  }
}
pr <- bind_rows(p_rows); write_csv(pr %>% mutate(across(where(is.numeric), ~ round(.x, 2))), file.path(OUT, "pre_period_sensitivity.csv"))
for (d in DOMS) {
  sub <- pr %>% filter(domain == d)
  if (nrow(sub)) logf(sprintf("  %-8s 2025 açığı: %s", d, paste(sprintf("%s=%+.1f", sub$pre_period, sub$gap_2025), collapse = "  ")))
}

# ---------------- özet şekil ----------------
if (nrow(gr)) {
  g <- ggplot(gr, aes(x = domain, y = gap_2025)) +
    geom_hline(yintercept = 0, colour = "grey60") +
    geom_jitter(aes(colour = oecd_only, shape = drop_asterisk), width = 0.12, height = 0, size = 2.4, alpha = 0.85) +
    labs(title = "Türkiye 2025 açığı: donör kuralı ızgarası",
         subtitle = "her nokta bir donör-kuralı kombinasyonu (havuz × OECD kısıtı × yıldız × kâğıt-2015)",
         x = NULL, y = "2025 açığı (Türkiye − sentetik, puan)", colour = "yalnız OECD", shape = "yıldızlı ülkeler atıldı") +
    theme_minimal()
  ggsave(file.path(FIG, "robust_donor_grid.png"), g, width = 8, height = 5, dpi = 150)
}
write_json(list(loo = loo, in_time = if (length(it_rows)) bind_rows(it_rows) else NULL, grid = gr, pre_sens = pr),
           file.path(OUT, "robustness_summary.json"), auto_unbox = TRUE, pretty = TRUE, digits = 3)
writeLines(log_lines, file.path(OUT, "robustness_log.txt"))
cat("\nDONE robustness\n")
