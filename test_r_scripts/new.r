
library(R6)
library(argparse)
# source("/Users/joshij/Desktop/r2g2/scripts/r-argparse/R/argparse.R")
#Create the main parser
parser <- ArgumentParser()

# specify our desired options 
# by default ArgumentParser will add an help option 
parser$add_argument("-v", "--verbose", action="store_true", default=TRUE, help="Print  extra output [default]")
parser$add_argument("-q", "--quietly", action="store_false", 
    dest="verbose", help="Print little output")
parser$add_argument("-c", "--count", nargs='+', type="integer", default=5, 
    help="Number of random normals to generate [default %(default)s]",
    metavar="number")
parser$add_argument("--generator", default="rnorm", 
    help = "Function to generate random deviates [default \"%(default)s\"]")
parser$add_argument("--mean", default=0, type="double", help="Mean if generator == \"rnorm\" [default %(default)s]")
parser$add_argument("--sd",
        default=1,
        type="double",
        metavar="standard deviation",
    help="Standard deviation if generator == \"rnorm\" [default %(default)s]")
    
parser$add_argument("--mode", 
                    choices=c("normal", "uniform", "binomial"), 
                    default="normal", 
                    help="The distribution mode to use. Choices are: normal, uniform, or binomial [default %(default)s]")


# parser$add_print_python_code_list()