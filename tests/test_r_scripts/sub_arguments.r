# library(argparse)
library(reticulate)
library(R6)
source("/Users/joshij/Desktop/r2g2/scripts/r-argparse/R/argparse.R")
# Create parser
parser <- ArgumentParser(description = "Example script with all possible argument types")

# Add arguments
parser$add_argument("positional_arg", type="character", help="A required positional argument")
input_group <- parser$add_argument_group("Input Options")
print(input_group)
input_group$add_argument("--input_file", type="character", help="Path to input file")
input_group$add_argument("--format", type="character", choices=c("csv", "tsv", "json"), default="csv")


input_group_1 <- parser$add_argument_group("out Options")
print(input_group_1)
input_group_1$add_argument("--out_file", type="character", help="Path to input file")
input_group_1$add_argument("--format_out", type="character", choices=c("csv", "tsv", "json"), default="csv")

# Access the internal _actions list
# for (action in parser$`_actions`) {
#   # Print argument flags
#   print(paste("args", toString(action$option_strings)))
  
#   # Print keyword arguments
#   cat("  default:", action$default, "\n")
#   cat("  help:", action$help, "\n")
#   cat("  type:", action$type, "\n")
#   cat("  metavar:", action$metavar, "\n")
#   cat("  dest:", action$dest, "\n")
#   cat("  choices:", if (!is.null(action$choices)) toString(action$choices) else "NULL", "\n\n")
# }