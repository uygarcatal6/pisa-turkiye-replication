# Staggered DiD (Callaway & Sant'Anna 2021, R package 'did') as a robustness check to the synthetic controls.
# Treated cohorts = countries with an ERT autocratization episode (institutional_screen.csv); first treated cycle = first PISA cycle after the episode start year.
# Controls = never-treated stable countries. Outcome = mean score per domain. Author: Claude Fable 5.1, 2026-09-15.
# 2026-09-28 (Opus 5.5, blind audit C3): the multiplier bootstrap (bstrap = TRUE, biters = 1000) was unseeded, so
# SEs changed run to run (RESULTS.md 6.9/7.9/7.0 vs output 7.02/7.52/6.62; within Monte Carlo error, |z| <= 1.74).
# Fix: fixed seed, reset before each domain so every domain's SE is reproducible regardless of loop order.
# Not re-run here: R is blocked on this machine by Windows Application Control (vctrs.dll), so data/derived/did/
# still holds the last unseeded run. ATTs do not depend on the seed; only SEs/bands do.
suppressPackageStartupMessages({ library(dplyr); library(readr); library(tidyr); library(ggplot2); library(did); library(stringr); library(purrr); library(jsonlite) })
ROOT <- Sys.getenv("PISA_ROOT", getwd()); setwd(ROOT)  # depo kökünden çalıştırın
SEED <- 20260928L
OUT <- "data/derived/did"; FIG <- "analysis/figures"; dir.create(OUT, recursive = TRUE, showWarnings = FALSE); dir.create(FIG, showWarnings = FALSE)
panel  <- read_csv("data/derived/analysis_panel.csv", show_col_types = FALSE); names(panel) <- tolower(names(panel)); panel$cycle <- as.integer(panel$cycle)
screen <- read_csv("data/derived/institutional_screen.csv", show_col_types = FALSE); names(screen) <- tolower(names(screen))
class_col <- names(screen)[str_detect(names(screen), regex("^class$|^stability_class$", ignore_case = TRUE))][1]
ep_col <- names(screen)[str_detect(names(screen), regex("ert_aut", ignore_case = TRUE))][1]
screen <- screen %>% rename(sclass = all_of(class_col), aut_ep = all_of(ep_col)) %>% distinct(iso3, .keep_all = TRUE)
col_for <- function(df, dom, kind) { cand <- names(df)[str_detect(names(df), regex(paste0("^", dom, ".*", kind), ignore_case = TRUE))]; if (!length(cand)) stop("no col ", dom, kind); cand[1] }
DOMS <- c("math", "reading", "science"); mean_cols <- sapply(DOMS, function(d) col_for(panel, d, "mean"))
cycles <- sort(unique(panel$cycle)); cyc_index <- setNames(seq_along(cycles), cycles)

# cohort: first cycle strictly after the first autocratization-episode start year
first_start <- function(s) { y <- as.integer(str_extract_all(as.character(s), "\\d{4}")[[1]]); if (!length(y)) NA_integer_ else min(y) }
coh <- screen %>% mutate(start = map_int(aut_ep, first_start),
                         g_cycle = map_int(start, ~ if (is.na(.x)) NA_integer_ else { cc <- cycles[cycles > .x]; if (length(cc)) min(cc) else NA_integer_ }),
                         treated = str_detect(sclass, "^treated") & !is.na(g_cycle),
                         never = sclass %in% c("stable_clean", "stable_corrupt"))
# Manual overrides where the proposal fixes the break explicitly (ledger-verified): TUR 2013→2015; GEO 2017→2018; HUN 2010→2012
ovr <- c(TUR = 2015L, GEO = 2018L, HUN = 2012L)
coh <- coh %>% mutate(g_cycle = ifelse(iso3 %in% names(ovr), ovr[iso3], g_cycle), treated = treated | iso3 %in% names(ovr))
keep <- coh %>% filter(treated | never) %>% select(iso3, sclass, start, g_cycle, treated, never)
write_csv(keep, file.path(OUT, "cohorts.csv"))
cat("Treated cohorts:\n"); print(keep %>% filter(treated) %>% select(iso3, start, g_cycle) %>% arrange(g_cycle), n = 50)
cat("Never-treated controls:", sum(keep$never), "\n")

dat <- panel %>% inner_join(keep, by = "iso3") %>% mutate(id = as.integer(factor(iso3)), t = cyc_index[as.character(cycle)],
                                                          g = ifelse(treated, cyc_index[as.character(g_cycle)], 0))
res_all <- list()
for (d in DOMS) {
  y <- mean_cols[[d]]
  dd <- dat %>% filter(!is.na(.data[[y]])) %>% select(id, iso3, t, g, y = all_of(y)) %>% as.data.frame()
  # keep cohorts with at least 2 pre-treatment cycles and 1 post cycle observed
  ok_g <- dd %>% filter(g > 0) %>% group_by(iso3, g) %>% summarise(npre = sum(t < g), npost = sum(t >= g), .groups = "drop") %>% filter(npre >= 2, npost >= 1) %>% pull(iso3)
  dd <- dd %>% filter(g == 0 | iso3 %in% ok_g)
  set.seed(SEED)                                                # bootstrap reproducibility (blind audit C3)
  mp <- tryCatch(att_gt(yname = "y", tname = "t", idname = "id", gname = "g", data = dd, control_group = "nevertreated",
                        base_period = "universal", est_method = "reg", panel = TRUE, allow_unbalanced_panel = TRUE, bstrap = TRUE, cband = TRUE, biters = 1000),
                 error = function(e) { cat("att_gt error (", d, "):", conditionMessage(e), "\n"); NULL })
  if (is.null(mp)) next
  es <- tryCatch(aggte(mp, type = "dynamic", na.rm = TRUE), error = function(e) NULL)
  gr <- tryCatch(aggte(mp, type = "group", na.rm = TRUE), error = function(e) NULL)
  gt <- tibble(group_cycle = cycles[mp$group], t_cycle = cycles[mp$t], att_gt = mp$att, se_gt = mp$se)
  write_csv(gt, file.path(OUT, paste0("att_gt_", d, ".csv")))
  if (!is.null(es)) { est <- tibble(event_time = es$egt, att_e = es$att.egt, se_e = es$se.egt); write_csv(est, file.path(OUT, paste0("event_study_", d, ".csv")))
    g <- ggplot(est, aes(event_time, att_e)) + geom_hline(yintercept = 0) + geom_vline(xintercept = -0.5, linetype = 2) +
      geom_errorbar(aes(ymin = att_e - 1.96 * se_e, ymax = att_e + 1.96 * se_e), width = 0.2) + geom_point(size = 2) +
      labs(title = paste0("CS-DiD event study — ", d), subtitle = sprintf("overall ATT %.1f (se %.1f); controls = never-treated stable countries", es$overall.att, es$overall.se), x = "cycles relative to first post-break cycle", y = "ATT (points)") + theme_minimal()
    ggsave(file.path(FIG, paste0("csdid_event_", d, ".png")), g, width = 8, height = 5, dpi = 150) }
  if (!is.null(gr)) write_csv(tibble(group_cycle = cycles[gr$egt], att_g = gr$att.egt, se_g = gr$se.egt), file.path(OUT, paste0("group_att_", d, ".csv")))
  # per-country post-treatment gaps vs never-treated mean change (descriptive, for TUR/GEO/HUN)
  ctrl <- dd %>% filter(g == 0) %>% group_by(t) %>% summarise(ybar_c = mean(y), .groups = "drop")
  pc <- dd %>% filter(iso3 %in% c("TUR", "GEO", "HUN")) %>% left_join(ctrl, by = "t") %>% group_by(iso3) %>%
    mutate(pre_diff = mean((y - ybar_c)[t < g]), did_gap = (y - ybar_c) - pre_diff, period = ifelse(t < g, "pre", "post")) %>% ungroup() %>%
    transmute(iso3, cycle = cycles[t], period, y, ybar_control = round(ybar_c, 1), did_gap = round(did_gap, 1))
  write_csv(pc, file.path(OUT, paste0("country_did_gaps_", d, ".csv")))
  res_all[[d]] <- list(domain = d, seed = SEED, n_treated = length(unique(dd$iso3[dd$g > 0])), n_controls = length(unique(dd$iso3[dd$g == 0])),
                       overall_att = if (!is.null(es)) es$overall.att else NA, overall_se = if (!is.null(es)) es$overall.se else NA,
                       group_att = if (!is.null(gr)) setNames(as.list(round(gr$att.egt, 1)), cycles[gr$egt]) else NULL)
  cat(sprintf("[%s] treated=%d controls=%d overall ATT=%.1f (se %.1f)\n", d, res_all[[d]]$n_treated, res_all[[d]]$n_controls, res_all[[d]]$overall_att, res_all[[d]]$overall_se))
  print(pc %>% filter(period == "post"), n = 30)
}
write_json(res_all, file.path(OUT, "csdid_summary.json"), auto_unbox = TRUE, pretty = TRUE, digits = 4)
cat("DONE\n")
