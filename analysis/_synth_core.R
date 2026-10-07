# Ortak sentetik-kontrol çekirdeği. 03_synth.R ve 09_robustness.R bunu source eder.
# Veri yükleme + donör havuzu kuralları + tek bir SC tahmini. Çıktı yazmaz, şekil çizmez.
suppressPackageStartupMessages({
  library(dplyr); library(readr); library(tidyr); library(Synth); library(purrr); library(stringr)
})

DOMS <- c("math", "reading", "science")

panel  <- read_csv("data/derived/analysis_panel.csv", show_col_types = FALSE)
screen <- read_csv("data/derived/institutional_screen.csv", show_col_types = FALSE)
paper15 <- tryCatch(read_csv("data/derived/paper_based_2015.csv", show_col_types = FALSE), error = function(e) tibble(iso3 = character()))
ast     <- tryCatch(read_csv("data/derived/asterisk_cycles.csv", show_col_types = FALSE), error = function(e) tibble(iso3 = character(), cycle = integer()))
names(panel) <- tolower(names(panel)); names(screen) <- tolower(names(screen))
names(paper15) <- tolower(names(paper15)); names(ast) <- tolower(names(ast))
panel$cycle <- as.integer(panel$cycle)

col_for <- function(df, dom, kind) {
  cand <- names(df)[str_detect(names(df), regex(paste0("^", dom, ".*", kind, "$"), ignore_case = TRUE))]
  if (!length(cand)) cand <- names(df)[str_detect(names(df), regex(paste0("^", dom, "_?", kind), ignore_case = TRUE))]
  if (!length(cand)) stop("no column for ", dom, " ", kind)
  cand[1]
}
mean_cols <- sapply(DOMS, function(d) col_for(panel, d, "mean"))
oecd_col <- names(panel)[str_detect(names(panel), regex("oecd", ignore_case = TRUE))][1]

class_col <- names(screen)[str_detect(names(screen), regex("^class$|^stability_class$", ignore_case = TRUE))][1]
ep_cols <- names(screen)[str_detect(names(screen), regex("^ert_(aut|dem)_episodes$", ignore_case = TRUE))]
screen <- screen %>% rename(sclass = all_of(class_col)) %>%
  mutate(no_episode = if (length(ep_cols)) rowSums(!is.na(across(all_of(ep_cols))) & across(all_of(ep_cols), ~ nzchar(as.character(.x)))) == 0 else NA) %>%
  select(iso3, sclass, no_episode) %>% distinct(iso3, .keep_all = TRUE)
paper15_iso <- unique(na.omit(paper15$iso3))
ast_pairs <- ast %>% filter(!is.na(iso3)) %>% mutate(cycle = as.integer(cycle)) %>% distinct(iso3, cycle)

is_oecd_iso <- function() panel %>%
  filter(.data[[oecd_col]] %in% c(TRUE, 1, "1", "TRUE", "True", "yes", "Yes")) %>% pull(iso3) %>% unique()

# Donör havuzu: sınıf + OECD + 2015 kâğıt + uyarı yıldızı + tam veri kuralları
build_pool <- function(treated, cycles, pool_type = c("stable_clean", "stable_corrupt", "stable_all", "stable_plus_ambiguous"),
                       oecd_only = TRUE, outcome, drop_asterisk = TRUE, drop_paper2015 = TRUE) {
  pool_type <- match.arg(pool_type)
  cls <- switch(pool_type, stable_clean = "stable_clean", stable_corrupt = "stable_corrupt",
                stable_all = c("stable_clean", "stable_corrupt"),
                stable_plus_ambiguous = c("stable_clean", "stable_corrupt", "ambiguous"))
  cand <- screen %>% filter(sclass %in% cls) %>% filter(sclass != "ambiguous" | no_episode %in% TRUE) %>% pull(iso3)
  cand <- setdiff(cand, treated)
  if (oecd_only && !is.na(oecd_col)) cand <- intersect(cand, is_oecd_iso())
  if (drop_paper2015) cand <- setdiff(cand, paper15_iso)
  if (drop_asterisk) cand <- setdiff(cand, unique(ast_pairs %>% filter(cycle %in% cycles) %>% pull(iso3)))
  ok <- panel %>% filter(iso3 %in% cand, cycle %in% cycles) %>% group_by(iso3) %>%
    summarise(n = sum(!is.na(.data[[outcome]])), .groups = "drop") %>% filter(n == length(cycles)) %>% pull(iso3)
  sort(ok)
}

# Tek SC tahmini. demean = TRUE ise her birimin ön dönem ortalaması çıkarılır (intercept serbest).
run_one <- function(treated, donors, pre, post, outcome, demean = TRUE) {
  cyc <- c(pre, post)
  df <- panel %>% filter(iso3 %in% c(treated, donors), cycle %in% cyc) %>%
    select(iso3, cycle, y = all_of(outcome)) %>% arrange(iso3, cycle)
  if (any(is.na(df$y))) stop("NA outcome in ", treated, " pool")
  if (demean) df <- df %>% group_by(iso3) %>% mutate(y = y - mean(y[cycle %in% pre])) %>% ungroup()
  df <- as.data.frame(df)
  df$unit_num <- as.integer(factor(df$iso3, levels = c(treated, donors)))
  special <- lapply(pre, function(t) list("y", t, "mean"))
  dp <- dataprep(foo = df, predictors = NULL, special.predictors = special, dependent = "y",
                 unit.variable = "unit_num", time.variable = "cycle", time.predictors.prior = pre,
                 treatment.identifier = 1, controls.identifier = 2:(length(donors) + 1),
                 time.optimize.ssr = pre, time.plot = cyc, unit.names.variable = "iso3")
  invisible(capture.output(res <- synth(dp, verbose = FALSE)))
  w <- as.numeric(res$solution.w); names(w) <- donors
  y1 <- as.numeric(dp$Y1plot); y0 <- as.numeric(dp$Y0plot %*% res$solution.w)
  gap <- y1 - y0
  pre_rmspe <- sqrt(mean(gap[cyc %in% pre]^2)); post_rmspe <- sqrt(mean(gap[cyc %in% post]^2))
  list(treated = treated, weights = w, cycles = cyc, y_treated = y1, y_synth = y0, gap = gap,
       pre_rmspe = pre_rmspe, post_rmspe = post_rmspe, ratio = post_rmspe / pre_rmspe,
       post_gap_mean = mean(gap[cyc %in% post]), gap_last = gap[length(gap)])
}

# Tedavi biriminin o alanda gözlemi olan ön dönem döngüleri (fen ölçeği 2006'da başlar)
trim_pre <- function(treated, pre, outcome) {
  avail <- panel %>% filter(iso3 == treated, cycle %in% pre, !is.na(.data[[outcome]])) %>% pull(cycle)
  sort(intersect(pre, avail))
}
