# Kapsam-düzeltilmiş sentetik kontrol.
#
# Sorun (09_robustness.R R2'den): 2009'a konan SAHTE kırılma da +20/+29 puanlık açık veriyor.
# Türkiye'nin 2013 öncesi yükselişi, kapsam endeksinin 0,47'den (2006) 0,68'e (2012) çıkmasıyla
# eş zamanlı; donörlerde kapsam sabit (~0,92). Yani ön dönem trendi mekanik olarak kirli.
# 2015 SONRASI ise kapsam yatay (0,699 → 0,722) ama puanlar yükseliyor.
#
# Bu betik kapsamı dışarı alıp aynı testleri tekrarlar:
#   S1  kapsam eşleştirme: kapsam ön dönem ortalaması ek eşleştirme değişkeni olarak
#   S2  artık (residual) sonuç: y ~ ülke sabit etkisi + b*kapsam, SC artıklar üzerinde
#         b iki türlü: (i) tüm ülkeler, (ii) yalnız tedavi görmemiş ülkeler
#   S3  S2 sonucu üzerinde in-time placebo (sahte kırılma 2009) — asıl sınav:
#         kapsam düzeltmesi sahte açığı yok ediyor ama 2015+ açığı duruyorsa tasarım kurtulur
# Yazan: Claude Fable 5.1 (kod), 2026-09-15.
ROOT <- Sys.getenv("PISA_ROOT", getwd()); setwd(ROOT)  # depo kökünden çalıştırın
source("analysis/_synth_core.R")
suppressPackageStartupMessages({ library(ggplot2); library(jsonlite) })
OUT <- "data/derived/coverage_adj"; FIG <- "analysis/figures"
dir.create(OUT, recursive = TRUE, showWarnings = FALSE); dir.create(FIG, showWarnings = FALSE)
log_lines <- c(); logf <- function(...) { s <- paste0(...); cat(s, "\n"); log_lines <<- c(log_lines, s) }

TREATED <- "TUR"
PRE  <- c(2006, 2009, 2012)          # kapsam 2003'te yok → ön dönem 2006'dan başlar
POST <- c(2015, 2018, 2022, 2025)
COV  <- "coverage_index3"
stopifnot(COV %in% names(panel))

# tedavi görmüş ülkeler (b tahmininden dışlamak için)
treated_iso <- screen %>% filter(str_detect(sclass, "^treated")) %>% pull(iso3)

logf("== Kapsam betimleyici ==")
cv <- panel %>% filter(iso3 %in% c(TREATED, build_pool(TREATED, c(PRE, POST), "stable_all", TRUE, mean_cols[["math"]])),
                       cycle %in% c(PRE, POST)) %>%
  mutate(grp = ifelse(iso3 == TREATED, "TUR", "donör")) %>%
  group_by(grp, cycle) %>% summarise(cov = mean(.data[[COV]], na.rm = TRUE), .groups = "drop") %>%
  pivot_wider(names_from = grp, values_from = cov)
logf(paste(capture.output(print(as.data.frame(round(cv, 3)), row.names = FALSE)), collapse = "\n"))

# ---------------- kapsam katsayısı ----------------
est_b <- function(exclude_treated) {
  d <- panel %>% filter(!is.na(.data[[COV]])) %>% select(iso3, cycle, all_of(COV), all_of(unname(mean_cols)))
  if (exclude_treated) d <- d %>% filter(!iso3 %in% treated_iso)
  out <- list()
  for (dm in DOMS) {
    y <- mean_cols[[dm]]
    dd <- d %>% filter(!is.na(.data[[y]])) %>% group_by(iso3) %>% filter(n() >= 3) %>%
      mutate(y_c = .data[[y]] - mean(.data[[y]]), x_c = .data[[COV]] - mean(.data[[COV]])) %>% ungroup()
    fit <- lm(y_c ~ x_c - 1, data = dd)          # ülke sabit etkili (within) eğim
    out[[dm]] <- list(b = unname(coef(fit)[1]), se = summary(fit)$coefficients[1, 2], n = nrow(dd),
                      n_country = length(unique(dd$iso3)))
  }
  out
}
b_all <- est_b(FALSE); b_ctrl <- est_b(TRUE)
logf("\n== Kapsam katsayısı (within, puan / 1 birim kapsam; 0,1 kapsam artışı = b/10 puan) ==")
for (dm in DOMS) logf(sprintf("  %-8s tüm ülkeler b=%+.1f (s.h. %.1f, n=%d/%d ülke) | tedavisizler b=%+.1f (s.h. %.1f, n=%d/%d)",
                              dm, b_all[[dm]]$b, b_all[[dm]]$se, b_all[[dm]]$n, b_all[[dm]]$n_country,
                              b_ctrl[[dm]]$b, b_ctrl[[dm]]$se, b_ctrl[[dm]]$n, b_ctrl[[dm]]$n_country))

# artık sonuç sütunlarını panele ekle
add_resid <- function(p, bset, suffix) {
  for (dm in DOMS) {
    y <- mean_cols[[dm]]
    p[[paste0(dm, "_resid_", suffix)]] <- p[[y]] - bset[[dm]]$b * p[[COV]]
  }
  p
}
panel <- add_resid(panel, b_all, "all")
panel <- add_resid(panel, b_ctrl, "ctrl")

run_spec <- function(outcome_col, pre, post, label, extra_cov = FALSE) {
  donors <- build_pool(TREATED, c(pre, post), "stable_all", TRUE, outcome_col)
  if (length(donors) < 3) { logf("  ", label, ": donör yetersiz (", length(donors), ")"); return(NULL) }
  r <- tryCatch(run_one(TREATED, donors, pre, post, outcome_col), error = function(e) { logf("  ", label, " HATA: ", conditionMessage(e)); NULL })
  if (is.null(r)) return(NULL)
  logf(sprintf("  %-34s donör=%2d ön-RMSPE=%5.1f | açıklar: %s | ort post %+.1f",
               label, length(donors), r$pre_rmspe,
               paste(sprintf("%d:%+.1f", r$cycles[r$cycles %in% post], r$gap[r$cycles %in% post]), collapse = " "),
               r$post_gap_mean))
  tibble(spec = label, domain = NA_character_, n_donors = length(donors), pre_rmspe = r$pre_rmspe,
         gap_2025 = r$gap[length(r$gap)], post_gap_mean = r$post_gap_mean,
         gaps = paste(sprintf("%d:%+.1f", r$cycles, r$gap), collapse = " "),
         top_donor = names(which.max(r$weights)), top_w = max(r$weights))
}

rows <- list()
logf("\n== S0 referans: ham puan, ön dönem 2006–2012 (kapsam düzeltmesi YOK) ==")
for (dm in DOMS) {
  pre <- trim_pre(TREATED, PRE, mean_cols[[dm]])
  r <- run_spec(mean_cols[[dm]], pre, POST, paste0("ham | ", dm))
  if (!is.null(r)) rows[[length(rows) + 1]] <- r %>% mutate(domain = dm, adj = "ham")
}
logf("\n== S2 kapsam-düzeltilmiş sonuç (b: tüm ülkeler) ==")
for (dm in DOMS) {
  col <- paste0(dm, "_resid_all"); pre <- trim_pre(TREATED, PRE, col)
  r <- run_spec(col, pre, POST, paste0("kapsam-düz (tüm) | ", dm))
  if (!is.null(r)) rows[[length(rows) + 1]] <- r %>% mutate(domain = dm, adj = "resid_all")
}
logf("\n== S2b kapsam-düzeltilmiş sonuç (b: yalnız tedavisiz ülkeler) ==")
for (dm in DOMS) {
  col <- paste0(dm, "_resid_ctrl"); pre <- trim_pre(TREATED, PRE, col)
  r <- run_spec(col, pre, POST, paste0("kapsam-düz (kontrol) | ", dm))
  if (!is.null(r)) rows[[length(rows) + 1]] <- r %>% mutate(domain = dm, adj = "resid_ctrl")
}

logf("\n== S3 in-time placebo (sahte kırılma 2009; ön 2003–2006 ham / 2006 tek nokta kapsamlı) ==")
# kapsam düzeltmesinde 2003 yok → sahte ön dönem 2006, post 2009–2012 (tek ön nokta: yalnız yön göstergesi)
it_rows <- list()
for (dm in DOMS) {
  for (adj in c("ham", "resid_all")) {
    col <- if (adj == "ham") mean_cols[[dm]] else paste0(dm, "_resid_all")
    pre_f <- trim_pre(TREATED, c(2003, 2006), col)
    if (length(pre_f) < 2) { logf(sprintf("  %-28s ön dönem <2 gözlem (%s) → atlandı", paste0(adj, " | ", dm), paste(pre_f, collapse = ","))); next }
    r <- run_spec(col, pre_f, c(2009, 2012), paste0("PLACEBO ", adj, " | ", dm))
    if (!is.null(r)) it_rows[[length(it_rows) + 1]] <- r %>% mutate(domain = dm, adj = adj)
  }
}

res <- bind_rows(rows); write_csv(res %>% mutate(across(where(is.numeric), ~ round(.x, 2))), file.path(OUT, "coverage_adjusted_specs.csv"))
if (length(it_rows)) write_csv(bind_rows(it_rows) %>% mutate(across(where(is.numeric), ~ round(.x, 2))), file.path(OUT, "coverage_adjusted_placebo.csv"))

logf("\n== Özet: 2025 açığı, ham vs kapsam-düzeltilmiş ==")
cmp <- res %>% select(domain, adj, gap_2025) %>% pivot_wider(names_from = adj, values_from = gap_2025)
logf(paste(capture.output(print(as.data.frame(cmp %>% mutate(across(where(is.numeric), ~ round(.x, 1)))), row.names = FALSE)), collapse = "\n"))

if (nrow(res)) {
  g <- ggplot(res, aes(domain, gap_2025, fill = adj)) + geom_col(position = "dodge") +
    geom_hline(yintercept = 0) +
    labs(title = "Türkiye 2025 açığı: ham vs kapsam-düzeltilmiş sentetik kontrol",
         subtitle = "ön dönem 2006–2012; kapsam endeksi ülke-içi regresyonla dışarı alındı",
         x = NULL, y = "2025 açığı (puan)", fill = "sonuç") + theme_minimal()
  ggsave(file.path(FIG, "coverage_adjusted_gaps.png"), g, width = 8, height = 5, dpi = 150)
}
write_json(list(coverage_table = cv, b_all = b_all, b_ctrl = b_ctrl, specs = res,
                placebo = if (length(it_rows)) bind_rows(it_rows) else NULL),
           file.path(OUT, "coverage_adjusted_summary.json"), auto_unbox = TRUE, pretty = TRUE, digits = 3)
writeLines(log_lines, file.path(OUT, "coverage_adjusted_log.txt"))
cat("\nDONE coverage-adjusted\n")
