#Proteiomics Data Preprocessing with DEP

# Load required libraries
library(argparse)
library(dplyr)
library(readr)
library(tibble)
library(DEP)
library(ggplot2)

# Set up argument parsing
parser <- ArgumentParser(description='Proteomics Data Preprocessing with DEP')

# Add arguments
parser$add_argument('--input_data', '-i', 
                   help='Path to input proteomics data file (CSV/TSV)',
                   required=TRUE)

parser$add_argument('--input_data_exp_design', '-e',
                   help='Path to experimental design file (CSV/TSV). If not provided, will parse from column names',
                   default=NULL)

parser$add_argument('--generate_qc', '-q',
                   help='Generate all QC plots',
                   action='store_true')

parser$add_argument('--imputation_fun', '-f',
                   help='Imputation function to use',
                   choices=c('MinProb', 'man', 'knn', 'QRILC', 'MLE', 'zero'),
                   default='MinProb')

parser$add_argument('--output_dir', '-o',
                   help='Output directory for plots and results',
                   default='./output')

parser$add_argument('--shift', '-s',
                   help='Shift parameter for manual imputation (only used with "man" function)',
                   type='double',
                   default=1.8)

parser$add_argument('--scale', '-c',
                   help='Scale parameter for manual imputation (only used with "man" function)',
                   type='double',
                   default=0.3)

parser$add_argument('--q_value', 
                   help='Q parameter for MinProb imputation',
                   type='double',
                   default=0.01)

parser$add_argument('--gene_names_col',
                   help='Column name for gene names (used as primary identifier)',
                   default='Gene.names')

parser$add_argument('--protein_ids_col',
                   help='Column name for protein IDs (used as secondary identifier)',
                   default='Protein.IDs')

parser$add_argument('--delimiter',
                   help='Delimiter used in the protein/gene identifier columns',
                   default=';')
parser$add_argument('--data_column_prefix', '-p', 
                   help='Prefix for data columns (default: "LFQ.")',
                   default="LFQ.")

parser$add_argument('--output_RDS_data', '-r', 
                   help='output RDS data file',
                   default="processed_data.rds")

# Parse arguments
args <- parser$parse_args()

# Create output directory if it doesn't exist
if (!dir.exists(args$output_dir)) {
  dir.create(args$output_dir, recursive = TRUE)
}

# Load input data
cat("Loading input data from:", args$input_data, "\n")

# Determine file extension and load accordingly
file_ext <- tools::file_ext(args$input_data)
if (file_ext %in% c("csv")) {
  data <- read_csv(args$input_data, show_col_types = FALSE,  na = character(0))
} else {
  stop("Unsupported file format. Please provide CSV or TSV file.")
}

cat("Data loaded successfully. Dimensions:", dim(data), "\n")

# Check if specified columns exist in the data
if (!args$gene_names_col %in% colnames(data)) {
  stop(paste("Column", args$gene_names_col, "not found in data. Available columns:", paste(colnames(data), collapse=", ")))
}
if (!args$protein_ids_col %in% colnames(data)) {
  stop(paste("Column", args$protein_ids_col, "not found in data. Available columns:", paste(colnames(data), collapse=", ")))
}

# Check for duplicated gene names
gene_col <- data[[args$gene_names_col]]
cat("Checking for duplicated gene names in column:", args$gene_names_col, "\n")
has_duplicates <- any(duplicated(gene_col))
cat("Has duplicates:", has_duplicates, "\n")

# Make a table of duplicated gene names
dup_table <- data %>% 
  group_by(!!sym(args$gene_names_col)) %>% 
  summarize(frequency = n()) %>% 
  arrange(desc(frequency)) %>% 
  filter(frequency > 1)

if (nrow(dup_table) > 0) {
  cat("Found", nrow(dup_table), "duplicated gene names\n")
} else {
  cat("No duplicated gene names found\n")
}

# Make unique names using the specified columns
cat("Creating unique names using:", args$gene_names_col, "and", args$protein_ids_col, "with delimiter:", args$delimiter, "\n")
data_unique <- make_unique(data, args$gene_names_col, args$protein_ids_col, delim = args$delimiter)

# Are there any duplicated names?
data$name %>% duplicated() %>% any()


# Load experimental design if provided
if (!is.null(args$input_data_exp_design)) {
  cat("Loading experimental design from:", args$input_data_exp_design, "\n")
  
  # Determine file extension and load accordingly
  exp_file_ext <- tools::file_ext(args$input_data_exp_design)
  if (exp_file_ext %in% c("csv")) {
    experimental_design <- read_csv(args$input_data_exp_design, show_col_types = FALSE)
  } else {
    stop("Unsupported experimental design file format. Please provide CSV or TSV file.")
  }
  
  # Generate a SummarizedExperiment object using experimental design
  LFQ_columns <- grep(args$data_column_prefix, colnames(data_unique)) # get LFQ column numbers
  data_se <- make_se(data_unique, LFQ_columns, experimental_design)
  cat("SummarizedExperiment object created with experimental design\n")
} else {
  cat("No experimental design provided. Parsing condition information from column names\n")
  # Generate a SummarizedExperiment object by parsing condition information from the column names
  LFQ_columns <- grep(args$data_column_prefix, colnames(data_unique)) # get LFQ column numbers
  data_se <- make_se_parse(data_unique, LFQ_columns)
  cat("SummarizedExperiment object created by parsing column names\n")
}


# Generate QC plots if requested
if (args$generate_qc) {
  cat("Generating QC plots...\n")
  
  # Create a list to store all plots
  plot_list <- list()
  
  # Plot frequency
  tryCatch({
    p1 <- plot_frequency(data_se)
    plot_list[["frequency"]] <- p1
    cat("Frequency plot generated\n")
  }, error = function(e) {
    cat("Error generating frequency plot:", e$message, "\n")
  })
  
  # Filter for proteins that are identified in all replicates of at least one condition
  data_filt <- filter_missval(data_se, thr = 0)
  
  # Less stringent filtering:
  # Filter for proteins that are identified in 2 out of 3 replicates of at least one condition
  data_filt2 <- filter_missval(data_se, thr = 1)
  
  # Plot a barplot of the protein identification overlap between samples
  tryCatch({
    p2 <- plot_coverage(data_filt)
    plot_list[["coverage"]] <- p2
    cat("Coverage plot generated\n")
  }, error = function(e) {
    cat("Error generating coverage plot:", e$message, "\n")
  })
  
  tryCatch({
    p3 <- plot_numbers(data_filt)
    plot_list[["numbers"]] <- p3
    cat("Numbers plot generated\n")
  }, error = function(e) {
    cat("Error generating numbers plot:", e$message, "\n")
  })
  
  # Normalize the data
  data_norm <- normalize_vsn(data_filt)
  
  # Visualize normalization by boxplots for all samples before and after normalization
  tryCatch({
    p4 <- plot_normalization(data_filt, data_norm)
    plot_list[["normalization"]] <- p4
    cat("Normalization plot generated\n")
  }, error = function(e) {
    cat("Error generating normalization plot:", e$message, "\n")
  })
  
  # Plot a heatmap of proteins with missing values
  tryCatch({
    p5 <- plot_missval(data_filt)
    plot_list[["missval"]] <- p5
    cat("Missing values plot generated\n")
  }, error = function(e) {
    cat("Error generating missing values plot:", e$message, "\n")
  })
  
  # Plot intensity distributions and cumulative fraction of proteins with and without missing values
  tryCatch({
    p6 <- plot_detect(data_filt)
    plot_list[["detect"]] <- p6
    cat("Detection plot generated\n")
  }, error = function(e) {
    cat("Error generating detection plot:", e$message, "\n")
  })
  
  # Save all plots to a single multi-page PDF
  if (length(plot_list) > 0) {
    combined_pdf_path <- file.path(args$output_dir, "QC_plots_combined.pdf")
    
    # Open PDF device
    pdf(combined_pdf_path, width = 12, height = 8)
    
    # Print each plot to a separate page
    for (plot_name in names(plot_list)) {
      tryCatch({
        print(plot_list[[plot_name]])
        cat("Added", plot_name, "plot to combined PDF\n")
      }, error = function(e) {
        cat("Error adding", plot_name, "plot to PDF:", e$message, "\n")
      })
    }
    
    # Add imputation plot if available (will be added after imputation is performed)
    # This placeholder will be replaced with actual imputation plot later
    
    # Close PDF device (will be reopened later for imputation plot)
    dev.off()
    
    cat("Initial QC plots saved to:", combined_pdf_path, "\n")
    cat("Plots in PDF so far:", length(plot_list), "\n")
  } else {
    cat("No plots were successfully generated\n")
  }
  
  cat("QC plots processing completed.\n")
} else {
  cat("Skipping QC plot generation (use --generate_qc to enable)\n")
  
  # Still need to perform filtering and normalization for imputation
  data_filt <- filter_missval(data_se, thr = 0)
  data_norm <- normalize_vsn(data_filt)
}

# Perform imputation based on selected method
cat("Performing imputation using method:", args$imputation_fun, "\n")

if (args$imputation_fun == "MinProb") {
  # Impute missing data using random draws from a Gaussian distribution centered around a minimal value (for MNAR)
  data_imp <- impute(data_norm, fun = "MinProb", q = args$q_value)
  cat("MinProb imputation completed with q =", args$q_value, "\n")
  
} else if (args$imputation_fun == "man") {
  # Impute missing data using random draws from a manually defined left-shifted Gaussian distribution (for MNAR)
  data_imp <- impute(data_norm, fun = "man", shift = args$shift, scale = args$scale)
  cat("Manual imputation completed with shift =", args$shift, "and scale =", args$scale, "\n")
  
} else if (args$imputation_fun == "knn") {
  # Impute missing data using the k-nearest neighbour approach (for MAR)
  data_imp <- impute(data_norm, fun = "knn", rowmax = 0.9)
  cat("KNN imputation completed\n")
  
} else if (args$imputation_fun == "QRILC") {
  # Impute missing data using QRILC (Quantile Regression Imputation of Left-Censored data)
  data_imp <- impute(data_norm, fun = "QRILC")
  cat("QRILC imputation completed\n")
  
} else if (args$imputation_fun == "MLE") {
  # Impute missing data using Maximum Likelihood Estimation
  data_imp <- impute(data_norm, fun = "MLE")
  cat("MLE imputation completed\n")
  
} else if (args$imputation_fun == "zero") {
  # Impute missing data with zeros
  data_imp <- impute(data_norm, fun = "zero")
  cat("Zero imputation completed\n")
}

# Generate imputation plot and add to combined PDF if QC plots are requested
if (args$generate_qc) {
  tryCatch({
    p_imp <- plot_imputation(data_norm, data_imp)
    
    # Add imputation plot to the existing combined PDF
    combined_pdf_path <- file.path(args$output_dir, "QC_plots_combined.pdf")
    
    # Open PDF for appending
    pdf(combined_pdf_path, width = 12, height = 8, onefile = TRUE)
    
    # Re-print all previous plots first
    for (plot_name in names(plot_list)) {
      tryCatch({
        print(plot_list[[plot_name]])
      }, error = function(e) {
        cat("Error re-adding", plot_name, "plot:", e$message, "\n")
      })
    }
    
    # Add imputation plot as the last page
    print(p_imp)
    dev.off()
    
    cat("Combined PDF updated with imputation plot\n")
    cat("Final combined PDF saved to:", combined_pdf_path, "\n")
    cat("Total plots in PDF:", length(plot_list) + 1, "\n")
  }, error = function(e) {
    cat("Error adding imputation plot to combined PDF:", e$message, "\n")
  })
}

# Save the processed data
output_file <- file.path(args$output_dir, "processed_data.rds")
saveRDS(data_imp, output_file)
cat("Processed data saved to:", output_file, "\n")

cat("Data preprocessing completed successfully!\n")
cat("Summary:\n")
cat("- Input data:", args$input_data, "\n")
cat("- Experimental design:", ifelse(is.null(args$input_data_exp_design), "Parsed from column names", args$input_data_exp_design), "\n")
cat("- Imputation method:", args$imputation_fun, "\n")
cat("- QC plots generated:", args$generate_qc, "\n")
cat("- Output directory:", args$output_dir, "\n")#Proteiomics Data Preprocessing with DEP
