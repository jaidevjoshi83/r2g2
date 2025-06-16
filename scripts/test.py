
#!/usr/bin/env python
from r_script_to_galaxy_wrapper import FakeArg


def r_script_argument_parsing(parent_locals, FakeArg=FakeArg):
    __description__ = "test"
    
    parser = FakeArg(description=__description__)
    parser.add_argument("""positional_arg""", type=str, help="""A required positional argument""")
    parser_group0 = parser.add_argument_group("""Input Options""")
    parser_group0.add_argument("""--input_file""", type=str, help="""Path to input file""")
    parser_group0.add_argument("""--format""", type=str, choices=("""csv""", """tsv""", """json"""), default="""csv""", help="""Format of input file (default: csv)""")
    parser_group1 = parser.add_argument_group("""Processing Options""")
    parser_group1.add_argument("""--threads""", type=int, default=4, help="""Number of threads to use (default: 4)""")
    parser_group1.add_argument("""--normalize""", action="""store_true""", help="""Enable data normalization""")
    parser_group1.add_argument("""--threshold""", type=float, default=0.5, help="""Threshold value for filtering (default: 0.5)""")
    parser_group1.add_argument("""--categories""", nargs="""+""", type=str, help="""A list of category names (e.g., A B C)""")
    parser_mutually_exclusive_group0 = parser.add_mutually_exclusive_group()
    parser_mutually_exclusive_group0.add_argument("""--enable_feature""", action="""store_true""", help="""Enable a specific feature""")
    parser_mutually_exclusive_group0.add_argument("""--disable_feature""", action="""store_true""", help="""Disable a specific feature""")
    parser_group2 = parser.add_argument_group("""Output Options""")
    parser_group2.add_argument("""--output_file""", type=str, help="""Path to output file""")
    parser_group2.add_argument("""--verbose""", action="""store_true""", help="""Enable verbose mode""")
    parser_group2.add_argument("""--log_level""", type=str, choices=("""DEBUG""", """INFO""", """WARNING""", """ERROR"""), default="""INFO""", help="""Set logging level (default: INFO)""")
    globals().update(parent_locals)

    return parser

blankenberg_parameters = r_script_argument_parsing(dict(locals()))

