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

parser$add_argument('--column_prefix', '-p',
                   help='Prefix for experimental design columns. If not provided, will parse from column names (Ex. LFQ.)',
                   default="LFQ.")

parser$add_argument('--input_data_exp_design', '-e', 
                   help='Path to input experimental design file (CSV/TSV)',
                   required=TRUE)

parser$add_argument('--gene_name_column_name', '-g',
                   help='Column name for gene names in the proteomics data',
                   default="Gene.names")
                   
parser$add_argument('--protein_id_column_name', '-r',
                   help='Column name for protein IDs in the proteomics data',
                   default="Protein.IDs")   

parser$add_argument('--filter_missing_values', '-f',
                   help='Threshold for filtering missing values (e.g., 0.5 for 50%)',
                   type="double",
                   default=FALSE)        

parser$add_argument('--normalization_method', '-n',
                   help='Normalization method (options: "vsn", "quantiles", "none")',
                   default="vsn")  

parser$add_argument('--imputation_method', '-m',
                   help='Imputation method (options: "MinProb", "QRILC", "none")',
                   default="MinProb")   

parser$add_argument('--control_name', '-c',
                   help='Name of the control condition in the experimental design',
                   required=TRUE)       

parser$add_argument('--alpha', '-a',
                   help='Significance level for differential expression (default: 0.05)',
                   type="double",
                   default=0.05)   

parser$add_argument('--lfc_threshold', '-l',
                   help='Log2 fold change threshold for differential expression (default: 1)',
                   type="double",
                   default=1.0)

parser$add_argument('--output_csv', '-o',
                   help='Path to output CSV file for differential expression results',
                   default='differential_expression_results.csv')       


# Parse arguments
args <- parser$parse_args()

# Determine file extension and load accordingly
file_ext <- tools::file_ext(args$input_data)
if (file_ext %in% c("csv")) {
  data <- read_csv(args$input_data, show_col_types = FALSE,  na = character(0))
} else {
  stop("Unsupported file format. Please provide CSV or TSV file.")
}
# Identify LFQ columns based on prefix
LFQ_columns <- grep(args$column_prefix, colnames(data))

# Load experimental design
file_ext <- tools::file_ext(args$input_data_exp_design)
if (file_ext %in% c("csv")) {
  experimental_design <- read_csv(args$input_data_exp_design, show_col_types = FALSE,  na = character(0))
} else {
  stop("Unsupported file format. Please provide CSV or TSV file.")
}

# Data preprocessing
data_unique <- make_unique(data, args$gene_name_column_name, args$protein_id_column_name, delim = ";")
data_se <- make_se(data_unique, LFQ_columns, experimental_design)

# Filter, normalize, and impute data
if (args$filter_missing_values) {
  data_filt <- filter_missval(data_se, thr = args$filter_missing_values)
} else {
  data_filt <- data_se
}

if (args$normalization_method == "vsn") {
  data_norm <- normalize_vsn(data_filt)
} else if (args$normalization_method == "quantiles") {
  data_norm <- normalize_quantiles(data_filt)
} else {
  data_norm <- data_filt
}   

if (args$imputation_method == "MinProb") {
  data_imp <- impute(data_norm, fun = "MinProb")
} else if (args$imputation_method == "QRILC") {
  data_imp <- impute(data_norm, fun = "QRILC")
} else {
  data_imp <- data_norm
}       

# Test every sample versus control
data_diff <- test_diff(data_imp, type = "control", control = args$control_name)
dep <- add_rejections(data_diff, alpha = args$alpha, lfc = log2(args$lfc_threshold))

#save dep to csv file 
write.csv(get_results(dep), args$output_csv, row.names = FALSE)


