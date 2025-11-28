#!/usr/bin/env Rscript

# Load required libraries
suppressPackageStartupMessages({
  library(argparse)
  library(dplyr)
})

# Set up argument parser
parser <- ArgumentParser(description = "Filter UbiLength data and save as CSV")

# Add arguments
parser$add_argument("--output", "-o", type = 'character', default = "data_filtered.csv",
                   help = "Output CSV file path [default: data_filtered.csv]")
parser$add_argument("--input-data", type = 'character', default = "UbiLength",
                   help = "Input data object name [default: UbiLength]")
parser$add_argument("--remove-reverse", action = "store_true", default = TRUE,
                   help = "Remove reverse hits (decoy database) [default: TRUE]")
parser$add_argument("--remove-contaminants", action = "store_true", default = TRUE,
                   help = "Remove potential contaminants [default: TRUE]")
parser$add_argument("--include-rownames", action = "store_true", default = FALSE,
                   help = "Include row names in output CSV [default: FALSE]")
parser$add_argument("--verbose", "-v", action = "store_true", default = FALSE,
                   help = "Print verbose output")

# Parse arguments
args <- parser$parse_args()

# Function to load data (assumes UbiLength is available in environment or package)
load_data <- function(data_name) {
  if (data_name == "UbiLength") {
    # Try to load UbiLength data - this might be from DEP package or similar
    if (exists("UbiLength")) {
      return(UbiLength)
    } else {
      # Try to load from common proteomics packages
      tryCatch({
        library(DEP)
        data("UbiLength")
        return(UbiLength)
      }, error = function(e) {
        stop("UbiLength data not found. Please ensure the data is loaded or specify a different input.")
      })
    }
  } else {
    # Try to get the object by name
    if (exists(data_name)) {
      return(get(data_name))
    } else {
      stop(paste("Data object", data_name, "not found in environment."))
    }
  }
}

# Main processing
if (args$verbose) {
  cat("Starting data filtering process...\n")
  cat("Input data:", args$input_data, "\n")
  cat("Output file:", args$output, "\n")
}

# Load the data
data <- load_data(args$input_data)

if (args$verbose) {
  cat("Original data dimensions:", nrow(data), "rows,", ncol(data), "columns\n")
}

# Apply filters
original_rows <- nrow(data)

# Filter for contaminant proteins and decoy database hits
if (args$remove_reverse && "Reverse" %in% colnames(data)) {
  data <- filter(data, Reverse != "+")
  if (args$verbose) {
    cat("After removing reverse hits:", nrow(data), "rows remaining\n")
  }
}

if (args$remove_contaminants && "Potential.contaminant" %in% colnames(data)) {
  data <- filter(data, Potential.contaminant != "+")
  if (args$verbose) {
    cat("After removing contaminants:", nrow(data), "rows remaining\n")
  }
}

filtered_rows <- nrow(data)

# Save the filtered data as a CSV file
write.csv(data, file = args$output, row.names = args$include_rownames)

# Print summary
cat("Filtering complete!\n")
cat("Removed", original_rows - filtered_rows, "rows (", 
    round((original_rows - filtered_rows) / original_rows * 100, 2), "%)\n")
cat("Filtered data saved to:", args$output, "\n")
cat("Final data dimensions:", nrow(data), "rows,", ncol(data), "columns\n")

if (args$verbose) {
  cat("\nColumn names in filtered data:\n")
  print(colnames(data))
}