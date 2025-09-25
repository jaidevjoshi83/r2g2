#!/usr/bin/env Rscript
suppressPackageStartupMessages({
  library(argparse)
  library(DEP)
  library(dplyr)
})

parser <- ArgumentParser(description = "DEP CSV pipeline with subcommands")

# Shared/global arguments
parser$add_argument("--output-prefix", default = "./dep_output", help = "Output prefix for results files")
parser$add_argument("--alpha", type = "double", default = 0.05, help = "Adjusted p-value cutoff for add_rejections")
parser$add_argument("--lfc", type = "double", default = log2(1.5), help = "Log2 fold change cutoff for add_rejections (passed as log2 value)")

# Subparsers for workflows
subparsers <- parser$add_subparsers(dest = "workflow", help = "Choose workflow: LFQ or TMT")

# LFQ subparser
parser_lfq <- subparsers$add_parser("LFQ", help = "Run LFQ pipeline (CSV input)")
parser_lfq$add_argument("--lfq-csv", required=TRUE, help = "Path to LFQ CSV file")
parser_lfq$add_argument("--skip", type = "integer", default = 2, help = "Number of header lines to skip when reading CSV")
parser_lfq$add_argument("--id-col", default = "Protein", help = "Column name for protein name (for make_unique)")
parser_lfq$add_argument("--acc-col", default = "Accession", help = "Column name for accession (for make_unique)")
parser_lfq$add_argument("--lfq-regex", default = '^Lane\\.(?!.*_nor)', help = "Perl regex to select LFQ columns")
parser_lfq$add_argument("--design-csv", required=TRUE, help = "Path to experimental design CSV (label,condition,replicate)")
parser_lfq$add_argument("--impute", choices = c('MinProb','man','knn','QRILC','none'), default = 'MinProb', help = "Imputation method to use")
parser_lfq$add_argument("--man-shift", type = "double", default = 1.8, help = "Shift for manual imputation (when --impute man)")
parser_lfq$add_argument("--man-scale", type = "double", default = 0.3, help = "Scale for manual imputation (when --impute man)")
parser_lfq$add_argument("--rowmax", type = "double", default = 0.9, help = "rowmax for KNN imputation")
parser_lfq$add_argument("--control", default = "Positive", help = "Control condition name used by test_diff")

# TMT subparser (placeholder for future)
parser_tmt <- subparsers$add_parser("TMT", help = "Run TMT pipeline (not yet implemented)")
parser_tmt$add_argument("--tmt-csv", required=FALSE, help = "Path to TMT CSV file (placeholder)")

args <- parser$parse_args()

if (is.null(args$workflow)) {
  stop('Please specify a workflow subcommand. Run with "LFQ" for CSV-based LFQ processing.')
}

if (args$workflow == 'LFQ') {
  cat('Reading LFQ CSV:', args$lfq_csv, '\n')
  lfq_data <- read.csv(args$lfq_csv, skip = args$skip, header = TRUE, stringsAsFactors = FALSE)

  cat('Detecting LFQ columns using regex:', args$lfq_regex, '\n')
  lfq_cols <- grep(args$lfq_regex, colnames(lfq_data), perl = TRUE)
  if (length(lfq_cols) == 0) {
    stop('No LFQ columns detected with regex: ', args$lfq_regex)
  }
  cat('Found', length(lfq_cols), 'LFQ columns\n')

  cat('Reading experimental design from:', args$design_csv, '\n')
  design <- read.csv(args$design_csv, stringsAsFactors = FALSE)
  required_cols <- c('label','condition','replicate')
  if (!all(required_cols %in% colnames(design))) {
    stop('Design CSV must contain columns: label, condition, replicate')
  }

  cat('Making unique identifiers for proteins...\n')
  lfq_data <- make_unique(lfq_data, args$id_col, args$acc_col, delim = "_")
  lfq_data$ID <- paste0("IMM_", seq_len(nrow(lfq_data)))
  rownames(lfq_data) <- lfq_data$ID

  cat('Building SummarizedExperiment (make_se)...\n')
  # make_se expects LFQ columns as integer indices
  data_se <- make_se(lfq_data, lfq_cols, design)

  cat('Filtering missing values (default thr = 0 — identified in all replicates of at least one condition)\n')
  data_filt <- filter_missval(data_se, thr = 0)

  cat('Normalizing using VSN...\n')
  data_norm <- normalize_vsn(data_filt)

  cat('Performing imputation:', args$impute, '\n')
  if (args$impute == 'QRILC') {
    data_imp <- impute(data_norm, fun = 'QRILC')
  } else if (args$impute == 'MinProb') {
    data_imp <- impute(data_norm, fun = 'MinProb', q = 0.01)
  } else if (args$impute == 'man') {
    data_imp <- impute(data_norm, fun = 'man', shift = args$man_shift, scale = args$man_scale)
  } else if (args$impute == 'knn') {
    data_imp <- impute(data_norm, fun = 'knn', rowmax = args$rowmax)
  } else {
    data_imp <- data_norm
  }

  cat('Testing differential expression: type = control (control =', args$control, ')\n')
  data_diff <- test_diff(data_imp, type = 'control', control = args$control)

  cat('Adding rejections (alpha =', args$alpha, ', lfc =', args$lfc, ')\n')
  dep <- add_rejections(data_diff, alpha = args$alpha, lfc = args$lfc)

  cat('Saving results...\n')
  results <- get_results(dep)
  out_rds <- paste0(args$output_prefix, '_results.rds')
  saveRDS(dep, file = out_rds)
  write.csv(results, file = paste0(args$output_prefix, '_results_table.csv'), row.names = FALSE)

  cat('Generating data frames (wide/long)...\n')
  df_wide <- get_df_wide(dep)
  df_long <- get_df_long(dep)
  write.csv(df_wide, file = paste0(args$output_prefix, '_df_wide.csv'), row.names = FALSE)
  write.csv(df_long, file = paste0(args$output_prefix, '_df_long.csv'), row.names = FALSE)

  cat('Done. Outputs written with prefix:', args$output_prefix, '\n')

} else if (args$workflow == 'TMT') {
  stop('TMT workflow is not implemented yet — use LFQ subcommand')
} else {
  stop('Unknown workflow: ', args$workflow)
}
