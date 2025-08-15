library(R6)
library(argparse)
library(jsonlite)

args_list = list()

FakeArgs <- R6Class("FakeArgs",
  public = list(
    my_list = NULL,  
    my_dict = NULL,

    initialize = function(name) {
      self$my_list <- list()  # Initialize the list
      private$name <- name
    },
    parse_args = function() {
          print("argument parsed")
        },
    add_argument = function(...) {
      arg_str <- sprintf(
        "%s.add_argument(%s)",
        private$name,
        argparse:::convert_..._to_arguments("add_argument", ...)
      )
      # Append to list (use length+1 for next index)
      self$my_list[[length(self$my_list) + 1]] <- arg_str
      args_list[[length(args_list) + 1]] <<- arg_str
    },

    add_argument_group = function(...) {
            group_name <- paste0(private$name, "_group", private$n_groups)
            private$n_groups <- private$n_groups + 1
            arg_str <- sprintf("%s = %s.add_argument_group(%s)",group_name, private$name,  argparse:::convert_..._to_arguments("add_argument", ...))
            self$my_dict[[group_name]] = group_name
            self$my_list[[length(self$my_list) + 1]] <- arg_str
            args_list[[length(args_list) + 1]] <<- arg_str
            FakeGroup$new(self$my_list, group_name)
    },

    add_mutually_exclusive_group = function(required = FALSE) {
            group_name <- paste0(private$name, "_mutually_exclusive_group",
                                 private$n_mutually_exclusive_groups)
            private$n_mutually_exclusive_groups <- private$n_mutually_exclusive_groups + 1
            arg_str <- sprintf("%s = %s.add_mutually_exclusive_group(%s)",
                           group_name, private$name,
                           ifelse(required, "required=True", ""))

            args_list[[length(args_list) + 1]] <<- arg_str

            FakeGroup$new(self$my_list, group_name)
            # Group$new(private$python_code, group_name)
        },

    add_subparsers = function(...) {

            subparsers_name <- paste0(private$name, "_subparsers")
            arg_str <- sprintf("%s = %s.add_subparsers(%s)",
                            subparsers_name, private$name,
                            argparse:::convert_..._to_arguments("add_argument", ...))

            args_list[[length(args_list) + 1]] <<- arg_str
            FakeSubparsers$new(self$my_list, subparsers_name)
        },

    add_item = function(name, value) {
      self$my_list[[name]] <- value
    },

    get_item = function(name) {
      return(self$my_list[[name]])
    },

    show_all = function() {
      print(self$my_list)
    }
  ),
    private = list( python_code_list=NULL, name = NULL, n_mutually_exclusive_groups = 0, n_groups = 0)
)

FakeArgumentParser = function (description=NULL) {
  FakeArgs$new(name="parser")
}

FakeGroup <- R6Class("FakeGroup", # nolint
    public = list(
        initialize = function(python_code_list, name) {
            private$python_code_list <- python_code_list
            private$name <- name
        },
        parse_args = function() {
          print("argument parsed")
        },
        add_argument = function(...) {
            arg_str <- sprintf("%s.add_argument(%s)",
                private$name, argparse:::convert_..._to_arguments("add_argument", ...))
             private$python_code_list[[length(private$python_code_list) + 1]] <- arg_str
             args_list[[length(args_list) + 1]] <<- arg_str
        }
    ),
    private = list(python_code_list = NULL, name = NULL)
)

FakeSubparsers <- R6Class("FakeSubparsers", # nolint
    public = list(
        initialize = function(python_code_list, name) {
            private$python_code_list <- python_code_list
            private$name <- name
        },
        add_parser = function(...) {
            parser_name <- paste0(private$name, "_subparser", private$n_subparsers)
            private$n_subparsers <- private$n_subparsers + 1

            arg_str = sprintf("%s = %s.add_parser(%s)",
                            parser_name, private$name,
                            argparse:::convert_..._to_arguments("ArgumentParser", ...))
            private$python_code_list[[length(private$python_code_list) + 1]] <- arg_str
            args_list[[length(args_list) + 1]] <<- arg_str
            FakeArgs$new(name=parser_name)
        }
    ),
    private = list(python_code_list = NULL, name = NULL, n_subparsers = 0)
)


# tool_params = function (){
#     parser <- FakeArgumentParser()
    
#     # specify our desired options 
#     # by default ArgumentParser will add an help option 
#     parser$add_argument("-v", "--verbose", action="store_true", default=TRUE, help="Print  extra output [default]")
#     parser$add_argument("-q", "--quietly", action="store_false", 
#         dest="verbose", help="Print little output")
#     parser$add_argument("-c", "--count", type="integer", default=5, 
#         help="Number of random normals to generate [default %(default)s]",
#         metavar="number")
#     parser$add_argument("--generator", default="rnorm", 
#         help = "Function to generate random deviates [default \"%(default)s\"]")
#     parser$add_argument("--mean", default=0, type="double", help="Mean if generator == \"rnorm\" [default %(default)s]")
#     parser$add_argument("--sd",
#             default=1,
#             type="double",
#             metavar="standard deviation",
#         help="Standard deviation if generator == \"rnorm\" [default %(default)s]")
        
#     parser$add_argument("--mode", 
#                         choices=c("normal", "uniform", "binomial"), 
#                         default="normal", 
#                         help="The distribution mode to use. Choices are: normal, uniform, or binomial [default %(default)s]")

#     input_group <- parser$add_argument_group("Input Options")
#     input_group$add_argument("--mode_3", 
#                         choices=c("normal", "uniform", "binomial"), 
#                         default="normal", 
#                         help="The distribution mode to use. Choices are: normal, uniform, or binomial [default %(default)s]")
    
#     input_group_1 <- parser$add_argument_group("Input Options")
#     input_group_1$add_argument("--mode_1", 
#                         choices=c("normal", "uniform", "binomial"), 
#                         default="normal", 
#                         help="The distribution mode to use. Choices are: normal, uniform, or binomial [default %(default)s]")
#     group <- parser$add_mutually_exclusive_group(required=TRUE)
#     group$add_argument('--sum', action='store_true', help='sum the integers')
#     group$add_argument('--max', action='store_true', help='find the max of the integers')

#     # Add other arguments
#     parser$add_argument('integers', metavar='N', type='integer', nargs='+',
#                         help='an integer for the accumulator')

#     write_json(args_list, path = "./params_output_out_1.json", pretty = TRUE, auto_unbox = TRUE)

#     }

# tool_params()