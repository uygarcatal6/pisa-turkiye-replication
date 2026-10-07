# Mechanism descriptives from the annex-based panel (no microdata yet):
# (a) coverage / exclusion trajectories: Türkiye vs donors; (b) placebo-domain test 2025: computational problem solving vs core domains, relative to OECD average;
# (c) 2022→2025 and 2015→2025 changes vs OECD average. Author: Claude Fable 5.1, 2026-09-15.
suppressPackageStartupMessages({ library(dplyr); library(readr); library(tidyr); library(ggplot2); library(stringr); library(jsonlite) })
ROOT <- Sys.getenv("PISA_ROOT", getwd()); setwd(ROOT)  # depo kökünden çalıştırın
OUT <- "data/derived/mechanisms"; FIG <- "analysis/figures"; dir.create(OUT, recursive = TRUE, showWarnings = FALSE); dir.create(FIG, showWarnings = FALSE)
panel <- read_csv("data/derived/analysis_panel.csv", show_col_types = FALSE); names(panel) <- tolower(names(panel)); panel$cycle <- as.integer(panel$cycle)
long <- read_csv("data/derived/pisa_scores_long.csv", show_col_types = FALSE); names(long) <- tolower(names(long)); long$cycle <- as.integer(long$cycle)
screen <- read_csv("data/derived/institutional_screen.csv", show_col_types = FALSE); names(screen) <- tolower(names(screen))
class_col <- names(screen)[str_detect(names(screen), regex("^class$|^stability_class$", ignore_case = TRUE))][1]
screen <- screen %>% rename(sclass = all_of(class_col)) %>% distinct(iso3, .keep_all = TRUE)
col_for <- function(df, dom, kind) { cand <- names(df)[str_detect(names(df), regex(paste0("^", dom, ".*", kind), ignore_case = TRUE))]; if (!length(cand)) NA_character_ else cand[1] }
oecd_col <- names(panel)[str_detect(names(panel), "oecd")][1]
is_oecd <- function(df) df[[oecd_col]] %in% c(TRUE, 1, "1", "TRUE", "True", "yes", "Yes")
res <- list()

# (a) coverage index & exclusion: Türkiye vs stable OECD donors, by cycle
cov_col <- col_for(panel, "coverage_index3", ""); exc_col <- names(panel)[str_detect(names(panel), "overall_exclusion")][1]
if (!is.na(cov_col)) {
  pool <- screen %>% filter(sclass %in% c("stable_clean", "stable_corrupt")) %>% pull(iso3)
  cv <- panel %>% filter(iso3 == "TUR" | (iso3 %in% pool & is_oecd(panel))) %>% mutate(grp = ifelse(iso3 == "TUR", "Türkiye", "stable OECD donors")) %>%
    group_by(grp, cycle) %>% summarise(coverage = mean(.data[[cov_col]], na.rm = TRUE), exclusion = if (!is.na(exc_col)) mean(.data[[exc_col]], na.rm = TRUE) else NA, n = n(), .groups = "drop")
  write_csv(cv, file.path(OUT, "coverage_vs_donors.csv"))
  g <- ggplot(cv, aes(cycle, coverage, colour = grp)) + geom_line(linewidth = 1) + geom_point() + labs(title = "Coverage Index 3: Türkiye vs stable OECD donors", y = "Coverage Index 3", x = "PISA cycle") + theme_minimal()
  ggsave(file.path(FIG, "mech_coverage.png"), g, width = 8, height = 5, dpi = 150)
  res$coverage <- cv
}

# (b) placebo domain 2025: CPS vs core, deviation from OECD average
cps <- long %>% filter(cycle == 2025, str_detect(tolower(domain), "cps|computational")) %>% select(iso3, cps = mean)
core <- long %>% filter(cycle == 2025, tolower(domain) %in% c("math", "reading", "science")) %>% select(iso3, domain, mean) %>% pivot_wider(names_from = domain, values_from = mean)
if (nrow(cps) > 0) {
  oecd_iso <- panel %>% filter(is_oecd(panel)) %>% pull(iso3) %>% unique()
  pd <- core %>% inner_join(cps, by = "iso3") %>% mutate(oecd = iso3 %in% oecd_iso)
  avg <- pd %>% filter(oecd) %>% summarise(across(c(math, reading, science, cps), ~ mean(.x, na.rm = TRUE)))
  pd <- pd %>% mutate(d_math = math - avg$math, d_reading = reading - avg$reading, d_science = science - avg$science, d_cps = cps - avg$cps,
                      core_minus_cps = (d_math + d_reading + d_science) / 3 - d_cps)
  write_csv(pd %>% arrange(desc(core_minus_cps)), file.path(OUT, "placebo_domain_2025.csv"))
  tur <- pd %>% filter(iso3 == "TUR"); geo <- pd %>% filter(iso3 == "GEO")
  rank_tur <- sum(pd$core_minus_cps >= tur$core_minus_cps, na.rm = TRUE); n_cmp <- sum(!is.na(pd$core_minus_cps))
  rank_geo <- if (nrow(geo)) sum(pd$core_minus_cps >= geo$core_minus_cps, na.rm = TRUE) else NA
  res$placebo_domain <- list(oecd_avg = as.list(round(avg, 1)), turkiye = as.list(round(tur %>% select(math, reading, science, cps, d_math, d_reading, d_science, d_cps, core_minus_cps), 1)),
                             georgia = if (nrow(geo)) as.list(round(geo %>% select(math, reading, science, cps, d_math, d_reading, d_science, d_cps, core_minus_cps), 1)) else NULL,
                             turkiye_rank_core_minus_cps = paste0(rank_tur, "/", n_cmp), georgia_rank_core_minus_cps = paste0(rank_geo, "/", n_cmp),
                             oecd_rank_turkiye = paste0(sum(pd$core_minus_cps[pd$oecd] >= tur$core_minus_cps, na.rm = TRUE), "/", sum(pd$oecd & !is.na(pd$core_minus_cps))))
  g <- ggplot(pd, aes(d_cps, (d_math + d_reading + d_science) / 3, label = iso3)) + geom_abline(slope = 1, intercept = 0, linetype = 2) + geom_hline(yintercept = 0, colour = "grey70") + geom_vline(xintercept = 0, colour = "grey70") +
    geom_point(aes(colour = iso3 %in% c("TUR", "GEO", "HUN")), size = 2) + geom_text(data = pd %>% filter(iso3 %in% c("TUR", "GEO", "HUN") | abs(core_minus_cps) > 25), vjust = -0.7, size = 3) +
    scale_colour_manual(values = c(`TRUE` = "firebrick", `FALSE` = "grey40"), guide = "none") +
    labs(title = "Placebo domain 2025: core domains vs computational problem solving (deviation from OECD average)", x = "CPS − OECD avg", y = "mean(core) − OECD avg") + theme_minimal()
  ggsave(file.path(FIG, "mech_placebo_domain_2025.png"), g, width = 8, height = 6, dpi = 150)
}

# (c) changes vs OECD average
wide <- long %>% filter(tolower(domain) %in% c("math", "reading", "science")) %>% select(iso3, cycle, domain, mean)
oecd_iso <- panel %>% filter(is_oecd(panel)) %>% pull(iso3) %>% unique()
chg <- function(c0, c1) wide %>% filter(cycle %in% c(c0, c1)) %>% pivot_wider(names_from = cycle, values_from = mean, names_prefix = "y") %>%
  mutate(change = .data[[paste0("y", c1)]] - .data[[paste0("y", c0)]], window = paste0(c0, "→", c1))
ch <- bind_rows(chg(2015, 2025), chg(2022, 2025), chg(2018, 2025)) %>% filter(!is.na(change))
oecd_ch <- ch %>% filter(iso3 %in% oecd_iso) %>% group_by(window, domain) %>% summarise(oecd_avg_change = mean(change), n = n(), .groups = "drop")
tur_ch <- ch %>% filter(iso3 %in% c("TUR", "GEO", "HUN")) %>% select(iso3, window, domain, change) %>% left_join(oecd_ch, by = c("window", "domain")) %>% mutate(rel = change - oecd_avg_change)
rk <- ch %>% filter(iso3 %in% oecd_iso) %>% group_by(window, domain) %>% mutate(rank_among_oecd = rank(-change), n_oecd = n()) %>% ungroup() %>% select(iso3, window, domain, rank_among_oecd, n_oecd)
rk_all <- ch %>% group_by(window, domain) %>% mutate(rank_among_all = rank(-change), n_all = n()) %>% ungroup() %>% select(iso3, window, domain, rank_among_all, n_all)
tur_ch <- tur_ch %>% left_join(rk, by = c("iso3", "window", "domain")) %>% left_join(rk_all, by = c("iso3", "window", "domain"))
write_csv(tur_ch, file.path(OUT, "changes_vs_oecd.csv"))
res$changes <- tur_ch
write_json(res, file.path(OUT, "mechanisms_summary.json"), auto_unbox = TRUE, pretty = TRUE, digits = 4)
cat("DONE mechanisms\n")
