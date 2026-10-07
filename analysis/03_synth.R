# PISA score inflation — synthetic control with placebo-in-space
# Author: Claude Fable 5.1 (2026-09-15). Inputs come only from data/derived/ (built from verified files).
# Cases: TUR (primary, break 2013, post 2015+), GEO (twin, break 2017, post 2018+; descriptive), HUN (negative control, break 2010, post 2012+).
suppressPackageStartupMessages({
  library(dplyr); library(readr); library(tidyr); library(ggplot2); library(Synth)
  library(jsonlite); library(purrr); library(stringr)
})
ROOT <- Sys.getenv("PISA_ROOT", getwd()); setwd(ROOT)  # depo kökünden çalıştırın
OUT <- "data/derived/synth"; FIG <- "analysis/figures"
dir.create(OUT, recursive = TRUE, showWarnings = FALSE); dir.create(FIG, recursive = TRUE, showWarnings = FALSE)
log_lines <- c()
logf <- function(...) { s <- paste0(...); cat(s, "\n"); log_lines <<- c(log_lines, s) }

# ---------- load ----------
panel  <- read_csv("data/derived/analysis_panel.csv", show_col_types = FALSE)
screen <- read_csv("data/derived/institutional_screen.csv", show_col_types = FALSE)
paper15 <- tryCatch(read_csv("data/derived/paper_based_2015.csv", show_col_types = FALSE), error = function(e) tibble(iso3 = character()))
ast     <- tryCatch(read_csv("data/derived/asterisk_cycles.csv", show_col_types = FALSE), error = function(e) tibble(iso3 = character(), cycle = integer()))
names(panel) <- tolower(names(panel)); names(screen) <- tolower(names(screen)); names(paper15) <- tolower(names(paper15)); names(ast) <- tolower(names(ast))
stopifnot(all(c("iso3", "cycle") %in% names(panel)))
panel$cycle <- as.integer(panel$cycle)

col_for <- function(df, dom, kind) {
  cand <- names(df)[str_detect(names(df), regex(paste0("^", dom, ".*", kind, "$"), ignore_case = TRUE))]
  if (!length(cand)) cand <- names(df)[str_detect(names(df), regex(paste0("^", dom, "_?", kind), ignore_case = TRUE))]
  if (!length(cand)) stop("no column for ", dom, " ", kind, " in: ", paste(names(df), collapse = ", "))
  cand[1]
}
DOMS <- c("math", "reading", "science")
mean_cols <- sapply(DOMS, function(d) col_for(panel, d, "mean"))
logf("Outcome columns: ", paste(names(mean_cols), mean_cols, sep = "=", collapse = "; "))
oecd_col <- names(panel)[str_detect(names(panel), regex("oecd", ignore_case = TRUE))][1]
if (is.na(oecd_col) && "oecd_member" %in% names(screen)) { panel <- panel %>% left_join(screen %>% select(iso3, oecd_member) %>% distinct(), by = "iso3"); oecd_col <- "oecd_member" }
logf("OECD flag column: ", ifelse(is.na(oecd_col), "NONE", oecd_col))
cov_col <- names(panel)[str_detect(names(panel), regex("coverage_index3", ignore_case = TRUE))][1]

class_col <- names(screen)[str_detect(names(screen), regex("^class$|^stability_class$", ignore_case = TRUE))][1]
stopifnot(!is.na(class_col))
ep_cols <- names(screen)[str_detect(names(screen), regex("^ert_(aut|dem)_episodes$", ignore_case = TRUE))]
screen <- screen %>% rename(sclass = all_of(class_col)) %>%
  mutate(no_episode = if (length(ep_cols)) rowSums(!is.na(across(all_of(ep_cols))) & across(all_of(ep_cols), ~ nzchar(as.character(.x)))) == 0 else NA) %>%
  select(iso3, sclass, no_episode) %>% distinct(iso3, .keep_all = TRUE)
paper15_iso <- unique(na.omit(paper15$iso3))
ast_pairs <- ast %>% filter(!is.na(iso3)) %>% mutate(cycle = as.integer(cycle)) %>% distinct(iso3, cycle)

# ---------- donor pool builder ----------
build_pool <- function(treated, cycles, pool_type = c("stable_clean", "stable_corrupt", "stable_all", "stable_plus_ambiguous"), oecd_only = TRUE, outcome, drop_asterisk = TRUE) {
  pool_type <- match.arg(pool_type)
  cls <- switch(pool_type, stable_clean = "stable_clean", stable_corrupt = "stable_corrupt", stable_all = c("stable_clean", "stable_corrupt"),
                stable_plus_ambiguous = c("stable_clean", "stable_corrupt", "ambiguous"))
  cand <- screen %>% filter(sclass %in% cls) %>% filter(sclass != "ambiguous" | no_episode %in% TRUE) %>% pull(iso3)   # ambiguous only if no ERT episode
  cand <- setdiff(cand, treated)
  if (oecd_only && !is.na(oecd_col)) {
    oecd_iso <- panel %>% filter(.data[[oecd_col]] %in% c(TRUE, 1, "1", "TRUE", "True", "yes", "Yes")) %>% pull(iso3) %>% unique()
    cand <- intersect(cand, oecd_iso)
  }
  cand <- setdiff(cand, paper15_iso)                                  # paper-based 2015 excluded
  if (drop_asterisk) { flagged <- ast_pairs %>% filter(cycle %in% cycles) %>% pull(iso3); cand <- setdiff(cand, unique(flagged)) }   # asterisk in any used cycle -> excluded
  # complete outcome data in all cycles
  ok <- panel %>% filter(iso3 %in% cand, cycle %in% cycles) %>% group_by(iso3) %>%
    summarise(n = sum(!is.na(.data[[outcome]])), .groups = "drop") %>% filter(n == length(cycles)) %>% pull(iso3)
  sort(ok)
}

# ---------- synth core ----------
run_one <- function(treated, donors, pre, post, outcome, demean = TRUE) {
  cyc <- c(pre, post)
  df <- panel %>% filter(iso3 %in% c(treated, donors), cycle %in% cyc) %>% select(iso3, cycle, y = all_of(outcome)) %>% arrange(iso3, cycle)
  if (any(is.na(df$y))) stop("NA outcome in ", treated, " pool")
  if (demean) df <- df %>% group_by(iso3) %>% mutate(y = y - mean(y[cycle %in% pre])) %>% ungroup()   # demeaned SC (intercept allowed): match pre-period trajectory, not level
  df <- as.data.frame(df)
  df$unit_num <- as.integer(factor(df$iso3, levels = c(treated, donors)))
  special <- lapply(pre, function(t) list("y", t, "mean"))
  dp <- dataprep(foo = df, predictors = NULL, special.predictors = special, dependent = "y",
                 unit.variable = "unit_num", time.variable = "cycle", time.predictors.prior = pre, treatment.identifier = 1,
                 controls.identifier = 2:(length(donors) + 1), time.optimize.ssr = pre, time.plot = cyc,
                 unit.names.variable = "iso3")
  so <- suppressWarnings(invisible(capture.output(res <- synth(dp, verbose = FALSE))))
  w <- as.numeric(res$solution.w); names(w) <- donors
  y1 <- as.numeric(dp$Y1plot); y0 <- as.numeric(dp$Y0plot %*% res$solution.w)
  gap <- y1 - y0
  pre_rmspe <- sqrt(mean(gap[cyc %in% pre]^2)); post_rmspe <- sqrt(mean(gap[cyc %in% post]^2))
  list(treated = treated, weights = w, cycles = cyc, y_treated = y1, y_synth = y0, gap = gap,
       pre_rmspe = pre_rmspe, post_rmspe = post_rmspe, ratio = post_rmspe / pre_rmspe)
}

run_case <- function(case_id, treated, pre, post, pool_type, oecd_only, min_donors = 5, drop_asterisk = TRUE, demean = TRUE) {
  out <- list()
  for (d in DOMS) {
    outcome <- mean_cols[[d]]
    pre_all <- pre
    avail <- panel %>% filter(iso3 == treated, cycle %in% pre_all, !is.na(.data[[outcome]])) %>% pull(cycle)
    pre <- sort(intersect(pre_all, avail))                                # domain-specific pre-period (science scale starts 2006)
    tag <- paste(case_id, d, pool_type, ifelse(demean, "demeaned", "levels"), sep = "_")
    if (length(pre) < 2) { logf("[", tag, "] SKIPPED: <2 pre-period observations for treated (", paste(pre, collapse = ","), ")"); pre <- pre_all; next }
    if (length(pre) < length(pre_all)) logf("[", tag, "] pre-period trimmed to ", paste(pre, collapse = ","), " (treated outcome missing in ", paste(setdiff(pre_all, pre), collapse = ","), ")")
    donors <- build_pool(treated, c(pre, post), pool_type, oecd_only, outcome, drop_asterisk)
    if (length(donors) < min_donors) { logf("[", tag, "] SKIPPED: only ", length(donors), " donors (", paste(donors, collapse = ","), ")"); next }
    main <- tryCatch(run_one(treated, donors, pre, post, outcome, demean), error = function(e) { logf("[", tag, "] ERROR: ", conditionMessage(e)); NULL })
    if (is.null(main)) next
    # placebo-in-space
    plac <- map(donors, function(dn) tryCatch(run_one(dn, setdiff(donors, dn), pre, post, outcome, demean), error = function(e) NULL)) %>% compact()
    ratios <- c(treated = main$ratio, setNames(map_dbl(plac, "ratio"), map_chr(plac, "treated")))
    p_ratio <- mean(ratios >= main$ratio)                       # share of units with ratio >= treated (incl. treated)
    post_gap_mean <- mean(main$gap[main$cycles %in% post])
    plac_post_means <- map_dbl(plac, ~ mean(.x$gap[.x$cycles %in% post]))
    p_gap <- mean(c(post_gap_mean, plac_post_means) >= post_gap_mean)  # one-sided: how unusual is a gap this positive
    # write outputs
    write_csv(tibble(donor = names(main$weights), weight = round(main$weights, 4)) %>% arrange(desc(weight)), file.path(OUT, paste0(tag, "_weights.csv")))
    write_csv(tibble(cycle = main$cycles, y_treated = main$y_treated, y_synth = main$y_synth, gap = main$gap, period = ifelse(main$cycles %in% pre, "pre", "post")), file.path(OUT, paste0(tag, "_path.csv")))
    write_csv(tibble(unit = names(ratios), ratio = as.numeric(ratios), post_gap_mean = c(post_gap_mean, plac_post_means)) %>% arrange(desc(ratio)), file.path(OUT, paste0(tag, "_placebo.csv")))
    # figures
    pth <- tibble(cycle = main$cycles, Treated = main$y_treated, Synthetic = main$y_synth) %>% pivot_longer(-cycle, names_to = "series", values_to = "score")
    g1 <- ggplot(pth, aes(cycle, score, colour = series)) + geom_line(linewidth = 1) + geom_point() +
      geom_vline(xintercept = mean(c(max(pre), min(post))), linetype = 2) +
      labs(title = paste0(treated, " — ", d, " (", pool_type, ", ", length(donors), " donors)"), subtitle = sprintf("pre-RMSPE %.1f | post-RMSPE %.1f | ratio %.2f | placebo p(ratio) = %.2f", main$pre_rmspe, main$post_rmspe, main$ratio, p_ratio), x = "PISA cycle", y = "mean score") + theme_minimal()
    ggsave(file.path(FIG, paste0(tag, "_path.png")), g1, width = 8, height = 5, dpi = 150)
    gp <- bind_rows(tibble(unit = treated, cycle = main$cycles, gap = main$gap, kind = "treated"),
                    map_dfr(plac, ~ tibble(unit = .x$treated, cycle = .x$cycles, gap = .x$gap, kind = "placebo")))
    g2 <- ggplot(gp, aes(cycle, gap, group = unit, colour = kind, alpha = kind)) + geom_line(linewidth = 0.7) + geom_hline(yintercept = 0) +
      scale_colour_manual(values = c(treated = "firebrick", placebo = "grey50")) + scale_alpha_manual(values = c(treated = 1, placebo = 0.5)) +
      geom_vline(xintercept = mean(c(max(pre), min(post))), linetype = 2) +
      labs(title = paste0("Placebo-in-space gaps — ", treated, " ", d, " (", pool_type, ")"), x = "PISA cycle", y = "treated − synthetic") + theme_minimal()
    ggsave(file.path(FIG, paste0(tag, "_placebo.png")), g2, width = 8, height = 5, dpi = 150)
    out[[tag]] <- list(case = case_id, treated = treated, domain = d, pool = pool_type, spec = ifelse(demean, "demeaned (intercept allowed)", "levels"), asterisk_rule = ifelse(drop_asterisk, "drop flagged countries", "ignore flags"), n_donors = length(donors), donors = donors,
                       pre = pre, post = post, pre_rmspe = main$pre_rmspe, post_rmspe = main$post_rmspe, ratio = main$ratio,
                       rank_ratio = sum(ratios >= main$ratio), n_units = length(ratios), p_ratio = p_ratio,
                       post_gaps = setNames(as.list(round(main$gap[main$cycles %in% post], 1)), post), post_gap_mean = post_gap_mean, p_gap = p_gap,
                       top_weights = head(sort(main$weights, decreasing = TRUE), 5))
    logf(sprintf("[%s] donors=%d | pre-RMSPE=%.1f post-RMSPE=%.1f ratio=%.2f rank=%d/%d p=%.2f | mean post gap=%.1f (p=%.2f) | gaps: %s",
                 tag, length(donors), main$pre_rmspe, main$post_rmspe, main$ratio, sum(ratios >= main$ratio), length(ratios), p_ratio, post_gap_mean, p_gap,
                 paste(post, round(main$gap[main$cycles %in% post], 1), sep = ":", collapse = " ")))
    pre <- pre_all
  }
  out
}

# ---------- cases ----------
results <- list()
# Levels check (documents the convex-hull failure: Türkiye sits far below every stable OECD donor before 2015)
results <- c(results, run_case("TUR_levels", "TUR", c(2003, 2006, 2009, 2012), c(2015, 2018, 2022, 2025), "stable_plus_ambiguous", oecd_only = TRUE, demean = FALSE))
# Türkiye main: demeaned SC, pre 2003–2012, post 2015–2025 (proposal §4.1). Two donor subgroups + combined.
for (pt in c("stable_clean", "stable_corrupt", "stable_all")) results <- c(results, run_case("TUR", "TUR", c(2003, 2006, 2009, 2012), c(2015, 2018, 2022, 2025), pt, oecd_only = TRUE))
# Robustness A: OECD stable + ambiguous-without-episode donors (looser stability test)
results <- c(results, run_case("TUR_robust_ambig", "TUR", c(2003, 2006, 2009, 2012), c(2015, 2018, 2022, 2025), "stable_plus_ambiguous", oecd_only = TRUE))
# Robustness B: corrupt-stable subgroup drawn from ALL participants (only Colombia is corrupt-stable inside the OECD)
results <- c(results, run_case("TUR_corrupt_allpart", "TUR", c(2003, 2006, 2009, 2012), c(2015, 2018, 2022, 2025), "stable_corrupt", oecd_only = FALSE))
# Robustness C: Türkiye with all stable participants (non-OECD included)
results <- c(results, run_case("TUR_allparticipants", "TUR", c(2003, 2006, 2009, 2012), c(2015, 2018, 2022, 2025), "stable_all", oecd_only = FALSE))
# Robustness D: keep OECD countries that carry a 2022/2025 response-rate caution flag (the strict rule leaves very few donors)
results <- c(results, run_case("TUR_keepflagged", "TUR", c(2003, 2006, 2009, 2012), c(2015, 2018, 2022, 2025), "stable_plus_ambiguous", oecd_only = TRUE, drop_asterisk = FALSE))
# Hungary negative control: break 2010 → pre 2000–2009, post 2012–2025
results <- c(results, run_case("HUN", "HUN", c(2000, 2003, 2006, 2009), c(2012, 2015, 2018, 2022, 2025), "stable_all", oecd_only = TRUE))
# Georgia twin case (descriptive: thin pre-period; PISA 2009+ recorded as cycle 2009 in trend tables if present; 2015 paper-based)
geo_pre <- intersect(c(2009, 2015), panel %>% filter(iso3 == "GEO", !is.na(.data[[mean_cols[["math"]]]])) %>% pull(cycle))
if (length(geo_pre) >= 2) results <- c(results, run_case("GEO", "GEO", geo_pre, c(2018, 2022, 2025), "stable_all", oecd_only = FALSE, min_donors = 8)) else logf("GEO skipped: pre-period cycles available: ", paste(geo_pre, collapse = ","))

write_json(results, file.path(OUT, "synth_summary.json"), auto_unbox = TRUE, pretty = TRUE, digits = 4)
summ <- map_dfr(results, ~ tibble(case = .x$case, treated = .x$treated, domain = .x$domain, pool = .x$pool, spec = .x$spec, asterisk_rule = .x$asterisk_rule, n_donors = .x$n_donors,
                                  pre_rmspe = round(.x$pre_rmspe, 2), post_rmspe = round(.x$post_rmspe, 2), ratio = round(.x$ratio, 2),
                                  rank = paste0(.x$rank_ratio, "/", .x$n_units), p_ratio = round(.x$p_ratio, 3),
                                  post_gap_mean = round(.x$post_gap_mean, 1), p_gap = round(.x$p_gap, 3),
                                  gaps = paste(names(.x$post_gaps), unlist(.x$post_gaps), sep = ":", collapse = " "),
                                  top_weights = paste(names(.x$top_weights), round(.x$top_weights, 2), sep = "=", collapse = " ")))
write_csv(summ, file.path(OUT, "synth_summary.csv"))
writeLines(log_lines, file.path(OUT, "synth_log.txt"))
cat("\nDONE:", nrow(summ), "specifications written to", OUT, "\n")
