#!/usr/bin/env Rscript
# Inspect SDG4 quantitative data and its codebook.
args <- commandArgs(trailingOnly = FALSE)
file_arg <- grep("^--file=", args, value = TRUE)
script_dir <- if (length(file_arg)) dirname(normalizePath(sub("^--file=", "", file_arg[1]))) else getwd()
quant_path <- file.path(script_dir, "SDG4_Quant_Data.csv")
codebook_path <- file.path(script_dir, "SDG4_Codebook.csv")

# Keep text columns as character; do not convert strings to factors.
df <- read.csv(quant_path, stringsAsFactors = FALSE)
cat("Columns:\n")
print(names(df))
cat("Head (first 3 rows):\n")
print(head(df, 3))
cat("Summary statistics:\n")
print(summary(df))

tryCatch({
  codebook <- read.csv(codebook_path, stringsAsFactors = FALSE)
  cat("Codebook:\n")
  print(codebook, row.names = FALSE)
}, error = function(e) {
  message("Could not read codebook (", codebook_path, "): ", conditionMessage(e))
})
