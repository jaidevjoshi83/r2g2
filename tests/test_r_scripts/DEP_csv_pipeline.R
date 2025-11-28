#!/usr/bin/env Rscript
suppressPackageStartupMessages({
  library(argparse)
  library(DEP)
  library(dplyr)
  library(ggplot2)
  library(grid)
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
parser_lfq$add_argument("--lfq-csv", required=TRUE, type = 'character', help = "Path to LFQ CSV file")
parser_lfq$add_argument("--skip", type = "integer", default = 2, help = "Number of header lines to skip when reading CSV")
parser_lfq$add_argument("--id-col", default = "Protein", type = 'character', help = "Column name for protein name (for make_unique)")
parser_lfq$add_argument("--acc-col", default = "Accession", type = 'character', help = "Column name for accession (for make_unique)")
parser_lfq$add_argument("--lfq-regex", default = '^Lane\\.(?!.*_nor)', type = 'character', help = "Perl regex to select LFQ columns")
parser_lfq$add_argument("--design-csv", required=TRUE, type = 'character', help = "Path to experimental design CSV (label,condition,replicate)")
parser_lfq$add_argument("--impute", choices = c('MinProb','man','knn','QRILC','none'), default = 'MinProb', type = 'character', help = "Imputation method to use")
parser_lfq$add_argument("--man-shift", type = "double", default = 1.8, help = "Shift for manual imputation (when --impute man)")
parser_lfq$add_argument("--man-scale", type = "double", default = 0.3, help = "Scale for manual imputation (when --impute man)")
parser_lfq$add_argument("--rowmax", type = "double", default = 0.9, help = "rowmax for KNN imputation")
parser_lfq$add_argument("--control", default = "Positive", type = 'character', help = "Control condition name used by test_diff")
parser_lfq$add_argument("--plots", default = "", type = 'character', help = "Comma-separated list of plots to generate (numbers,coverage,missval,pca,correlation,heatmap,volcano,all)")
parser_lfq$add_argument("--plots-format", default = "png", choices = c("png","pdf"), type = 'character', help = "Output format for plots (png or pdf)")
parser_lfq$add_argument("--plots-dir", default = NULL, type = 'character', help = "Directory to save plots (default: <output-prefix>_plots)")
parser_lfq$add_argument("--volcano-contrast", default = "all", type = 'character', help = "Contrast for volcano plot (name or 'all')")

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

  # Plot generation section -------------------------------------------------
  if (nzchar(args$plots)) {
    cat('Plot generation requested for:', args$plots, '\n')
    plots_dir <- ifelse(is.null(args$plots_dir) || args$plots_dir == '', paste0(args$output_prefix, '_plots'), args$plots_dir)
    if (!dir.exists(plots_dir)) dir.create(plots_dir, recursive = TRUE)

    # Helper to parse list
    raw_plots <- tolower(trimws(unlist(strsplit(args$plots, ','))))
    if (length(raw_plots) == 0) raw_plots <- character(0)
    all_plot_keys <- c('numbers','coverage','missval','pca','correlation','heatmap','volcano')
    if ('all' %in% raw_plots) {
      selected_plots <- all_plot_keys
    } else {
      unknown <- setdiff(raw_plots, all_plot_keys)
      if (length(unknown) > 0) {
        warning('Unknown plot keys ignored: ', paste(unknown, collapse = ', '))
      }
      selected_plots <- intersect(raw_plots, all_plot_keys)
    }

    if (length(selected_plots) == 0) {
      cat('No valid plots selected, skipping plot generation.\n')
    } else {
      cat('Generating plots:', paste(selected_plots, collapse = ', '), '\n')

      # Re-use intermediate objects: data_se, data_filt, data_norm, data_imp, dep
      # Convenience saver
      save_plot_obj <- function(p, filename_root) {
        file <- file.path(plots_dir, paste0(filename_root, '.', args$plots_format))
        ext <- args$plots_format
        if (inherits(p, 'gg') || inherits(p, 'ggplot')) {
          ggsave(filename = file, plot = p, device = ext)
        } else if (inherits(p, 'gtable') || 'gtable' %in% class(p)) {
          if (ext == 'pdf') {
            pdf(file)
            grid::grid.draw(p)
            dev.off()
          } else {
            png(file)
            grid::grid.draw(p)
            dev.off()
          }
        } else if (is.list(p) && !is.null(p$gtable)) { # pheatmap style object
          gt <- p$gtable
          if (ext == 'pdf') {
            pdf(file)
            grid::grid.draw(gt)
            dev.off()
          } else {
            png(file)
            grid::grid.draw(gt)
            dev.off()
          }
        } else {
          warning('Unrecognized plot object class: ', paste(class(p), collapse = '/'))
        }
      }

      # numbers (proteins per sample)
      if ('numbers' %in% selected_plots) {
        cat('Generating plot_numbers...\n')
        p <- try(plot_numbers(data_filt), silent = TRUE)
        if (!inherits(p, 'try-error')) save_plot_obj(p, 'plot_numbers') else warning('Failed to generate plot_numbers')
      }
      # coverage
      if ('coverage' %in% selected_plots) {
        cat('Generating plot_coverage...\n')
        p <- try(plot_coverage(data_se), silent = TRUE)
        if (!inherits(p, 'try-error')) save_plot_obj(p, 'plot_coverage') else warning('Failed to generate plot_coverage')
      }
      # missing value pattern
      if ('missval' %in% selected_plots) {
        cat('Generating plot_missval...\n')
        p <- try(plot_missval(data_se), silent = TRUE)
        if (!inherits(p, 'try-error')) save_plot_obj(p, 'plot_missval_raw') else warning('Failed (raw) plot_missval')
        p2 <- try(plot_missval(data_filt), silent = TRUE)
        if (!inherits(p2, 'try-error')) save_plot_obj(p2, 'plot_missval_filtered')
      }
      # PCA
      if ('pca' %in% selected_plots) {
        cat('Generating plot_pca...\n')
        p <- try(plot_pca(data_imp, x = 1, y = 2, n = 500), silent = TRUE)
        if (!inherits(p, 'try-error')) save_plot_obj(p, 'plot_pca') else warning('Failed to generate plot_pca')
      }
      # correlation matrix
      if ('correlation' %in% selected_plots) {
        cat('Generating plot_correlation...\n')
        p <- try(plot_correlation(data_imp), silent = TRUE)
        if (!inherits(p, 'try-error')) save_plot_obj(p, 'plot_correlation') else warning('Failed to generate plot_correlation')
      }
      # heatmap clustering
      if ('heatmap' %in% selected_plots) {
        cat('Generating plot_heatmap...\n')
        p <- try(plot_heatmap(dep), silent = TRUE)
        if (!inherits(p, 'try-error')) save_plot_obj(p, 'plot_heatmap') else warning('Failed to generate plot_heatmap')
      }
      # volcano plots (may be multiple contrasts)
      if ('volcano' %in% selected_plots) {
        cat('Generating plot_volcano...\n')
        # Attempt to detect contrasts
        results_cols <- try(get_results(dep), silent = TRUE)
        contrasts <- character(0)
        if (!inherits(results_cols, 'try-error') && 'contrast' %in% colnames(results_cols)) {
          contrasts <- unique(results_cols$contrast)
        }
        if (length(contrasts) == 0 && !is.null(dep@results) && 'contrast' %in% names(dep@results)) {
          # fallback (likely not needed)
          contrasts <- unique(dep@results$contrast)
        }
        if (args$volcano_contrast != 'all') {
          if (args$volcano_contrast %in% contrasts) {
            contrasts <- args$volcano_contrast
          } else {
            warning('Requested volcano contrast not found: ', args$volcano_contrast, '; using all detected.')
          }
        }
        if (length(contrasts) == 0) {
          warning('No contrasts detected for volcano plotting')
        } else {
          for (ct in contrasts) {
            cat('  Volcano for contrast:', ct, '\n')
            p <- try(plot_volcano(dep, contrast = ct), silent = TRUE)
            if (!inherits(p, 'try-error')) save_plot_obj(p, paste0('plot_volcano_', gsub('[^A-Za-z0-9._-]+','_', ct))) else warning('Failed volcano plot for contrast ', ct)
          }
        }
      }

      cat('Plot generation completed. Files in: ', plots_dir, '\n')
    }
  }

} else if (args$workflow == 'TMT') {
  stop('TMT workflow is not implemented yet — use LFQ subcommand')
} else {
  stop('Unknown workflow: ', args$workflow)
}
