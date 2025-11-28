#!/usr/bin/env Rscript
###############################################################################
# DEP_plots_cli.R
# A CLI tool to generate individual (or all) DEP diagnostic/result plots
# from LFQ CSV input + design file. Each plot type is exposed as a subcommand.
#
# Subcommands: numbers, coverage, missval, pca, correlation, heatmap, volcano, all
#
# Example:
# Rscript DEP_plots_cli.R numbers \
#   --lfq-csv lfq.csv --design-csv design.csv --output-prefix out/dep \
#   --control Positive
#
# Rscript DEP_plots_cli.R all \
#   --lfq-csv lfq.csv --design-csv design.csv --output-prefix out/dep_all
###############################################################################
suppressPackageStartupMessages({
  library(argparse)
  library(DEP)
  library(dplyr)
  library(ggplot2)
  library(grid)
})

# ---------------------------- Argument Parsing --------------------------------
parser <- ArgumentParser(description = 'Generate DEP analysis plots via subcommands')

# Global shared arguments for building the pipeline objects
parser$add_argument('--lfq-csv', required = TRUE, type = 'character', help = 'Path to LFQ CSV file')
parser$add_argument('--design-csv', required = TRUE, type = 'character', help = 'Path to experimental design CSV (label,condition,replicate)')
parser$add_argument('--skip', type = 'integer', default = 2, help = 'Number of header lines to skip when reading LFQ CSV')
parser$add_argument('--id-col', default = 'Protein', type = 'character', help = 'Column name for protein name (for make_unique)')
parser$add_argument('--acc-col', default = 'Accession', type = 'character', help = 'Column name for accession (for make_unique)')
parser$add_argument('--lfq-regex', default = '^Lane\\.(?!.*_nor)', type = 'character', help = 'Perl regex to select LFQ intensity columns')
parser$add_argument('--impute', choices = c('MinProb','man','knn','QRILC','none'), default = 'MinProb', type = 'character', help = 'Imputation method')
parser$add_argument('--man-shift', type = 'double', default = 1.8, help = 'Shift for manual imputation (man)')
parser$add_argument('--man-scale', type = 'double', default = 0.3, help = 'Scale for manual imputation (man)')
parser$add_argument('--rowmax', type = 'double', default = 0.9, help = 'rowmax for knn imputation')
parser$add_argument('--control', default = 'Positive', type = 'character', help = 'Control condition for test_diff ')
parser$add_argument('--alpha', type = 'double', default = 0.05, help = 'Adjusted p-value cutoff (add_rejections)')
parser$add_argument('--lfc', type = 'double', default = log2(1.5), help = 'Log2 fold change cutoff (add_rejections)')
parser$add_argument('--output-prefix', default = './dep_plots', type = 'character', help = 'Output prefix for generated files')
parser$add_argument('--plots-format', default = 'png', choices = c('png','pdf'), type = 'character', help = 'Output format for plots')
parser$add_argument('--plots-dir', default = NULL, type = 'character', help = 'Directory to save plots (default: <output-prefix>_plots)')
# Volcano contrast moved to volcano subparser specific options

subparsers <- parser$add_subparsers(dest = 'plot', help = 'Select which plot (or all) to generate')
sp_numbers <- subparsers$add_parser('numbers', help = 'Protein numbers per sample (plot_numbers)')
sp_numbers$add_argument('--numbers-stage', choices = c('filtered','raw'), default = 'filtered', type = 'character', help = 'Stage to plot numbers from (filtered after missval filter or raw pre-filter)')

sp_coverage <- subparsers$add_parser('coverage', help = 'Protein coverage per sample (plot_coverage)')

sp_missval <- subparsers$add_parser('missval', help = 'Missing value pattern (plot_missval raw + filtered)')

sp_pca <- subparsers$add_parser('pca', help = 'PCA (plot_pca)')
sp_pca$add_argument('--pca-x', type='integer', default=1, help='Principal component for x-axis')
sp_pca$add_argument('--pca-y', type='integer', default=2, help='Principal component for y-axis')
sp_pca$add_argument('--pca-topN', type='integer', default=500, help='Number of most variable proteins to include (passed to n)')

sp_corr <- subparsers$add_parser('correlation', help = 'Sample correlation matrix (plot_correlation)')
sp_corr$add_argument('--corr-method', choices = c('pearson','spearman'), default='pearson', type='character', help='Correlation method (applied prior to plotting if not pearson)')

sp_heat <- subparsers$add_parser('heatmap', help = 'Clustering heatmap (plot_heatmap)')
sp_heat$add_argument('--heatmap-topN', type='integer', default=0, help='If >0, restrict heatmap to top N most variable proteins (post-imputation)')

sp_volcano <- subparsers$add_parser('volcano', help = 'Volcano plot(s) (plot_volcano)')
sp_volcano$add_argument('--volcano-contrast', default = 'all', type = 'character', help = 'Contrast name to plot or all')

subparsers$add_parser('all', help = 'Generate all available plots')

args <- parser$parse_args()

if (is.null(args$plot)) {
  stop('Please specify a plot subcommand. Use --help for usage.')
}

# ----------------------------- Utility Functions -------------------------------
ensure_design <- function(design) {
  required <- c('label','condition','replicate')
  if (!all(required %in% colnames(design))) {
    stop('Design CSV must contain columns: label, condition, replicate')
  }
  design
}

# Determine which pipeline stage is required
stage_needed_for <- function(plot_keys) {
  # map stages numerically
  stage_map <- list(
    numbers = 3,      # data_filt
    coverage = 2,     # data_se
    missval = 3,      # both raw (2) and filtered (3) -> choose 3
    pca = 5,          # data_imp
    correlation = 5,  # data_imp
    heatmap = 6,      # dep
    volcano = 6       # dep
  )
  max(unlist(stage_map[plot_keys]), na.rm = TRUE)
}

save_plot_obj <- function(p, file, format) {
  ext <- format
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
    warning('Unrecognized plot object class for ', file, ': ', paste(class(p), collapse = '/'))
  }
}

# Core pipeline builder up to a required stage
build_pipeline <- function(args, needed_stage) {
  out <- list()
  cat('Reading LFQ CSV: ', args$lfq_csv, '\n')
  lfq_data <- read.csv(args$lfq_csv, skip = args$skip, header = TRUE, stringsAsFactors = FALSE)
  cat('Selecting LFQ columns with regex: ', args$lfq_regex, '\n')
  lfq_cols <- grep(args$lfq_regex, colnames(lfq_data), perl = TRUE)
  if (length(lfq_cols) == 0) stop('No LFQ columns detected with regex: ', args$lfq_regex)

  cat('Reading design: ', args$design_csv, '\n')
  design <- ensure_design(read.csv(args$design_csv, stringsAsFactors = FALSE))

  cat('make_unique...\n')
  lfq_data <- make_unique(lfq_data, args$id_col, args$acc_col, delim = '_')
  lfq_data$ID <- paste0('IMM_', seq_len(nrow(lfq_data)))
  rownames(lfq_data) <- lfq_data$ID

  out$lfq_data <- lfq_data
  out$lfq_cols <- lfq_cols
  out$design <- design
  if (needed_stage >= 2) {
    cat('Building SummarizedExperiment (make_se)\n')
    out$data_se <- make_se(lfq_data, lfq_cols, design)
  }
  if (needed_stage >= 3) {
    cat('Filtering missing values (thr=0)\n')
    out$data_filt <- filter_missval(out$data_se, thr = 0)
  }
  if (needed_stage >= 4) {
    cat('Normalizing with VSN\n')
    out$data_norm <- normalize_vsn(out$data_filt)
  }
  if (needed_stage >= 5) {
    cat('Imputing (method = ', args$impute, ')\n')
    if (args$impute == 'QRILC') {
      out$data_imp <- impute(out$data_norm, fun = 'QRILC')
    } else if (args$impute == 'MinProb') {
      out$data_imp <- impute(out$data_norm, fun = 'MinProb', q = 0.01)
    } else if (args$impute == 'man') {
      out$data_imp <- impute(out$data_norm, fun = 'man', shift = args$man_shift, scale = args$man_scale)
    } else if (args$impute == 'knn') {
      out$data_imp <- impute(out$data_norm, fun = 'knn', rowmax = args$rowmax)
    } else {
      out$data_imp <- out$data_norm
    }
  }
  if (needed_stage >= 6) {
    cat('Differential expression test + add_rejections\n')
    out$data_diff <- test_diff(out$data_imp, type = 'control', control = args$control)
    out$dep <- add_rejections(out$data_diff, alpha = args$alpha, lfc = args$lfc)
  }
  out
}

# ---------------------------- Plot Generation Logic ---------------------------
requested <- if (args$plot == 'all') c('numbers','coverage','missval','pca','correlation','heatmap','volcano') else args$plot
needed_stage <- stage_needed_for(requested)
if (args$plot == 'numbers' && !is.null(args$numbers_stage) && args$numbers_stage == 'raw') {
  needed_stage <- max(needed_stage, 2)
}

plots_dir <- ifelse(is.null(args$plots_dir) || args$plots_dir == '', paste0(args$output_prefix, '_plots'), args$plots_dir)
if (!dir.exists(plots_dir)) dir.create(plots_dir, recursive = TRUE)

cat('Requested plots: ', paste(requested, collapse = ', '), '\n')
cat('Building pipeline up to stage: ', needed_stage, '\n')
objs <- build_pipeline(args, needed_stage)

fmt <- args$plots_format

# numbers
if ('numbers' %in% requested) {
  cat('Generating plot_numbers...\n')
  numbers_obj <- if (!is.null(args$numbers_stage) && args$numbers_stage == 'raw') objs$data_se else objs$data_filt
  p <- try(plot_numbers(numbers_obj), silent = TRUE)
  if (!inherits(p, 'try-error')) save_plot_obj(p, file.path(plots_dir, paste0('plot_numbers.', fmt)), fmt) else warning('Failed plot_numbers')
}

# coverage
if ('coverage' %in% requested) {
  cat('Generating plot_coverage...\n')
  p <- try(plot_coverage(objs$data_se), silent = TRUE)
  if (!inherits(p, 'try-error')) save_plot_obj(p, file.path(plots_dir, paste0('plot_coverage.', fmt)), fmt) else warning('Failed plot_coverage')
}

# missval
if ('missval' %in% requested) {
  cat('Generating plot_missval (raw + filtered)...\n')
  p_raw <- try(plot_missval(objs$data_se), silent = TRUE)
  if (!inherits(p_raw, 'try-error')) save_plot_obj(p_raw, file.path(plots_dir, paste0('plot_missval_raw.', fmt)), fmt)
  p_filt <- try(plot_missval(objs$data_filt), silent = TRUE)
  if (!inherits(p_filt, 'try-error')) save_plot_obj(p_filt, file.path(plots_dir, paste0('plot_missval_filtered.', fmt)), fmt)
}

# PCA
if ('pca' %in% requested) {
  cat('Generating plot_pca...\n')
  x_pc <- if (!is.null(args$pca_x)) args$pca_x else 1
  y_pc <- if (!is.null(args$pca_y)) args$pca_y else 2
  topN <- if (!is.null(args$pca_topN)) args$pca_topN else 500
  p <- try(plot_pca(objs$data_imp, x = x_pc, y = y_pc, n = topN), silent = TRUE)
  if (!inherits(p, 'try-error')) save_plot_obj(p, file.path(plots_dir, paste0('plot_pca_PC',x_pc,'_PC',y_pc,'.', fmt)), fmt) else warning('Failed plot_pca')
}

# correlation
if ('correlation' %in% requested) {
  cat('Generating plot_correlation...\n')
  # If spearman requested, transform assay values to cor matrix manually and plot via DEP fallback
  if (!is.null(args$corr_method) && args$corr_method == 'spearman') {
    cat('  Using spearman correlation matrix (custom)...\n')
    mat <- SummarizedExperiment::assay(objs$data_imp)
    cm <- suppressWarnings(cor(mat, method='spearman', use='pairwise.complete.obs'))
    # Simple ggplot heatmap alternative
    dfc <- reshape2::melt(cm, varnames = c('Var1','Var2'), value.name='cor')
    p <- try(ggplot(dfc, aes(Var1, Var2, fill = cor)) + geom_tile() +
              scale_fill_gradient2(limits=c(-1,1)) + theme_bw() +
              theme(axis.text.x=element_text(angle=45,hjust=1)) +
              ggtitle('Spearman correlation'), silent=TRUE)
  } else {
    p <- try(plot_correlation(objs$data_imp), silent = TRUE)
  }
  if (!inherits(p, 'try-error')) save_plot_obj(p, file.path(plots_dir, paste0('plot_correlation.', fmt)), fmt) else warning('Failed plot_correlation')
}

# heatmap
if ('heatmap' %in% requested) {
  cat('Generating plot_heatmap...\n')
  dep_obj <- objs$dep
  if (!is.null(args$heatmap_topN) && args$heatmap_topN > 0) {
    cat('  Selecting top', args$heatmap_topN, 'most variable proteins for heatmap.\n')
    mat <- SummarizedExperiment::assay(dep_obj)
    vars <- matrixStats::rowVars(mat, na.rm=TRUE)
    ord <- order(vars, decreasing=TRUE)
    keep <- head(ord, args$heatmap_topN)
    dep_obj <- dep_obj[keep,]
  }
  p <- try(plot_heatmap(dep_obj), silent = TRUE)
  if (!inherits(p, 'try-error')) save_plot_obj(p, file.path(plots_dir, paste0('plot_heatmap.', fmt)), fmt) else warning('Failed plot_heatmap')
}

# volcano
if ('volcano' %in% requested) {
  cat('Generating volcano plot(s)...\n')
  results_df <- try(get_results(objs$dep), silent = TRUE)
  contrasts <- character(0)
  if (!inherits(results_df, 'try-error') && 'contrast' %in% colnames(results_df)) {
    contrasts <- unique(results_df$contrast)
  }
  if (length(contrasts) == 0) {
    warning('No contrasts detected for volcano plot')
  } else {
    vol_contrast <- if (!is.null(args$volcano_contrast)) args$volcano_contrast else 'all'
    if (vol_contrast != 'all') {
      if (vol_contrast %in% contrasts) {
        contrasts <- vol_contrast
      } else {
        warning('Requested volcano contrast not found: ', vol_contrast, '; using all detected.')
      }
    }
    for (ct in contrasts) {
      cat('  Volcano for contrast: ', ct, '\n')
      p <- try(plot_volcano(objs$dep, contrast = ct), silent = TRUE)
      if (!inherits(p, 'try-error')) save_plot_obj(p, file.path(plots_dir, paste0('plot_volcano_', gsub('[^A-Za-z0-9._-]+','_', ct), '.', fmt)), fmt) else warning('Failed volcano for contrast ', ct)
    }
  }
}

cat('Completed plot generation. Output in: ', plots_dir, '\n')
