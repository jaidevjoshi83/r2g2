library(argparse)

#Create the main parser
parser <- ArgumentParser(description = "Example script with all possible argument types")
    
    # specify our desired options 
    # by default ArgumentParser will add an help option 
parser$add_argument("-v", "--verbose", action="store_true", default=TRUE, help="Print  extra output [default]")
parser$add_argument("-q", "--quietly", action="store_false", 
    dest="verbose", help="Print little output")
parser$add_argument("-c", "--count", type="integer", default=5, 
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

input_group <- parser$add_argument_group("Input Options")
input_group$add_argument("--mode_3", 
                    choices=c("normal", "uniform", "binomial"), 
                    default="normal", 
                    help="The distribution mode to use. Choices are: normal, uniform, or binomial [default %(default)s]")

input_group_1 <- parser$add_argument_group("Input Options")
input_group_1$add_argument("--mode_1", 
                    choices=c("normal", "uniform", "binomial"), 
                    default="normal", 
                    help="The distribution mode to use. Choices are: normal, uniform, or binomial [default %(default)s]")
group <- parser$add_mutually_exclusive_group(required=TRUE)
group$add_argument('--sum', action='store_true', help='sum the integers')
group$add_argument('--max', action='store_true', help='find the max of the integers')

# Add other arguments
parser$add_argument('integers', metavar='N', type='integer', nargs='+',
                    help='an integer for the accumulator')

                                        



# #Parse the arguments
args <- parser$parse_args()
