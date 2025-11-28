from r_script_to_galaxy_wrapper import FakeArg
import argparse


__description__ = "test"

parser = argparse.ArgumentParser(description=__description__)
parser.add_argument(r"""--verbose""", action=r"""store_true""", help=r"""Enable verbose output""")
parser_subparsers = parser.add_subparsers(dest=r"""command""", help=r"""Subcommand to run""")
parser_subparsers_subparser0 = parser_subparsers.add_parser(r"""train""", help=r"""Train the model""")
parser_subparsers_subparser0.add_argument(r"""--epochs""", type=int, default=10, help=r"""Number of epochs""")
parser_subparsers_subparser0.add_argument(r"""--lr""", type=float, default=0.001, help=r"""Learning rate""")
parser_subparsers_subparser1 = parser_subparsers.add_parser(r"""predict""", help=r"""Make predictions""")
parser_subparsers_subparser1.add_argument(r"""--input-file""", type=str, help=r"""Input CSV file""")
parser_subparsers_subparser1.add_argument(r"""--output-file""", type=str, help=r"""Output CSV file""")
parser_group0 = parser.add_argument_group(r"""Input Options""")
parser_group0.add_argument(r"""--input_file""", type=str, help=r"""Path to input file""")
parser_group0.add_argument(r"""--format""", type=str, choices=(r"""csv""", r"""tsv""", r"""json"""), default=r"""csv""", help=r"""Format of input file (default: csv)""")
parser_group1 = parser.add_argument_group(r"""Processing Options""")
parser_group1.add_argument(r"""--threads""", type=int, default=4, help=r"""Number of threads to use (default: 4)""")
parser_group1.add_argument(r"""--normalize""", action=r"""store_true""", help=r"""Enable data normalization""")
parser_group1.add_argument(r"""--threshold""", type=float, default=0.5, help=r"""Threshold value for filtering (default: 0.5)""")
parser_group1.add_argument(r"""--categories""", nargs=r"""+""", type=str, help=r"""A list of category names (e.g., A B C)""")
parser_mutually_exclusive_group0 = parser.add_mutually_exclusive_group()
parser_mutually_exclusive_group0.add_argument(r"""--enable_feature""", action=r"""store_true""", help=r"""Enable a specific feature""")
parser_mutually_exclusive_group0.add_argument(r"""--disable_feature""", action=r"""store_true""", help=r"""Disable a specific feature""")
parser_group2 = parser.add_argument_group(r"""Output Options""")
parser_group2.add_argument(r"""--output_file""", type=str, help=r"""Path to output file""")
parser_group2.add_argument(r"""--log_level""", type=str, choices=(r"""DEBUG""", r"""INFO""", r"""WARNING""", r"""ERROR"""), default=r"""INFO""", help=r"""Set logging level (default: INFO)""")
# globals().update(parent_locals)

print( dir(parser))
      



# for i in dir(parser):
#     print(i)
