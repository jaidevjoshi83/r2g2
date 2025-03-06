import rpy2.robjects as robjects

#!/usr/bin/env python3

def test_funct(*args, **kwargs):
    print("Positional arguments:", args)
    print("Keyword arguments:", kwargs)
    return args, kwargs

# Example usage
test_funct("-n", "--name", type="character", default="User", help="Name of the person [default: %(default)s]")
