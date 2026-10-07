#!/usr/bin/env Rscript
# Çapraz doğrulama: 16_synthetic_did.py (Python SDiD) vs referans uygulama `synthdid` (R, GitHub
# synth-inference/synthdid; CRAN'da yok — B6-012). remotes::install_github ile kurulur (saf R, derleyici
# gerekmez). Aynı dengeli panel matrisleri (`data/derived/panel_matrices/`), aynı pencereler.
# Not: synthdid'in plasebo SE'si rastgele yeniden örnekleme (replications=200) kullanır; Python sürümü
# tüm N0 kontrolü sırayla tedavi sayan deterministik plasebo kullanır — SE'ler bu yüzden birebir değil.
# Çıktı: data/derived/sdid/r_synthdid_crosscheck.csv
# Yazan: Claude Fable 5.1, 2026-09-16.
lib <- Sys.getenv("R_LIBS_USER"); .libPaths(c(lib, .libPaths()))
if (!requireNamespace("synthdid", quietly = TRUE)) {
  if (!requireNamespace("remotes", quietly = TRUE)) install.packages("remotes", repos = "https://cloud.r-project.org", lib = lib, type = "binary", quiet = TRUE)
  remotes::install_github("synth-inference/synthdid", lib = lib, upgrade = "never", quiet = TRUE)
}
suppressPackageStartupMessages(library(synthdid))
root <- normalizePath(file.path(dirname(sub("--file=", "", grep("--file=", commandArgs(FALSE), value = TRUE))), ".."))
py <- read.csv(file.path(root, "data/derived/sdid/sdid_results.csv"), check.names = FALSE)
set.seed(20260916)
rows <- list()
for (pool in c("stable_all_oecd", "stable_plus_ambiguous_oecd", "all_participants")) for (oc in c("math", "reading", "science")) {
  m <- read.csv(file.path(root, "data/derived/panel_matrices", paste0(oc, "_", pool, ".csv")), check.names = FALSE)
  cyc <- as.integer(colnames(m)[-1]); Y <- as.matrix(m[, -1]); rownames(Y) <- m$iso3
  Yr <- rbind(Y[-1, ], Y[1, , drop = FALSE]); N0 <- nrow(Yr) - 1          # synthdid: kontroller önce, tedavi son satır
  for (win in c("post2015", "post2018")) {
    T0 <- if (win == "post2015") sum(cyc < 2015) else sum(cyc < 2018)
    est <- synthdid_estimate(Yr, N0, T0); se <- sqrt(vcov(est, method = "placebo"))
    p <- py[py$window == win & py$outcome == oc & py$pool == pool, ]
    rows[[length(rows) + 1]] <- data.frame(window = win, outcome = oc, pool = pool, n_donors = N0,
      tau_r_synthdid = round(as.numeric(est), 2), se_r_placebo = round(se, 2),
      tau_python = p$tau_sdid, se_python = p$se_placebo, diff_tau = round(p$tau_sdid - as.numeric(est), 2),
      lambda_r = paste(round(attr(est, "weights")$lambda, 2), collapse = " "),
      omega_r_top = paste(names(sort(setNames(attr(est, "weights")$omega, rownames(Yr)[1:N0]), decreasing = TRUE))[1:3],
                          round(sort(attr(est, "weights")$omega, decreasing = TRUE)[1:3], 2), sep = "=", collapse = " "))
  }
}
out <- do.call(rbind, rows)
write.csv(out, file.path(root, "data/derived/sdid/r_synthdid_crosscheck.csv"), row.names = FALSE)
print(out[, c("window", "outcome", "pool", "n_donors", "tau_r_synthdid", "tau_python", "diff_tau", "se_r_placebo", "se_python")], row.names = FALSE)
cat(sprintf("maks |tau farkı| = %.2f (18 vaka)\n", max(abs(out$diff_tau))))
cat("DONE synthdid crosscheck\n")
