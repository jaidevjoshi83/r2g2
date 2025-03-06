library(argparse)

# Create the main parser
parser <- ArgumentParser(description="Data analysis tool with various options")

# Create a mutually exclusive group
# Only one of these arguments can be used at a time
group <- parser$add_mutually_exclusive_group(required=TRUE)
group$add_argument("--analyze", action="store_true", 
                   help="Run data analysis")
group$add_argument("--visualize", action="store_true", 
                   help="Create visualizations")

# Sub-arguments for analysis
analysis_group <- parser$add_argument_group("Analysis options",
                   "These options are used when --analyze is selected")
analysis_group$add_argument("--method", 
                   choices=c("linear", "polynomial", "logistic"),
                   default="linear",
                   help="Statistical method to use for analysis")
analysis_group$add_argument("--iterations", type="integer", default=100,
                   help="Number of iterations to run")

# Sub-arguments for visualization
viz_group <- parser$add_argument_group("Visualization options",
                   "These options are used when --visualize is selected")
viz_group$add_argument("--plot-type", 
                   choices=c("scatter", "line", "bar", "heatmap"),
                   default="scatter",
                   help="Type of plot to generate")
viz_group$add_argument("--color-scheme",
                   choices=c("default", "viridis", "blues", "reds"),
                   default="default",
                   help="Color scheme for visualization")

# Common arguments for both modes
parser$add_argument("--input", required=TRUE,
                   help="Input file path")
parser$add_argument("--output",
                   help="Output file path (optional)")
parser$add_argument("--verbose", action="store_true",
                   help="Enable verbose output")

# Parse the arguments
args <- parser$parse_args()

# Example usage in code
if (args$analyze) {
  cat("Running analysis with method:", args$method, "\n")
  cat("Number of iterations:", args$iterations, "\n")
  # Analysis code would go here
} else if (args$visualize) {
  cat("Creating", args$plot_type, "plot with", args$color_scheme, "colors\n")
  # Visualization code would go here
}

cat("Using input file:", args$input, "\n")
if (!is.null(args$output)) {
  cat("Writing to output file:", args$output, "\n")
}