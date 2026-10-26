#!/usr/bin/env Rscript
args <- commandArgs(trailingOnly = FALSE)
file_arg <- sub("^--file=", "", args[grep("^--file=", args)])
script <- normalizePath(file_arg, mustWork = TRUE)
root <- normalizePath(file.path(dirname(script), ".."), mustWork = TRUE)
lib <- file.path(root, "data", "bibliometria", "Rlib")
dir.create(lib, recursive = TRUE, showWarnings = FALSE)
.libPaths(c(lib, .libPaths()))
if (!requireNamespace("bibliometrix", quietly = TRUE)) {
  options(repos = c(CRAN = "https://cloud.r-project.org"))
  options(download.file.method = "libcurl")
  install.packages("bibliometrix", lib = lib, Ncpus = 2)
}
stopifnot(requireNamespace("bibliometrix", quietly = TRUE))
cat("bibliometrix ", as.character(packageVersion("bibliometrix")), " instalado em ", lib, "\n", sep = "")
