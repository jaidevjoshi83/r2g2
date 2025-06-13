import json
import os 


def edit_r_script(r_script_path, edited_r_script_path, fakearg_path=None, json_file_name="out.json"):
    
    if  not fakearg_path :
        fakearg_path  =  os.path.join(os.getcwd(), 'FakeArg.r')
   
    with open(r_script_path,  'r' ) as fh:
        input = fh.read()

    new_input = """source("%s")\ntool_params = function (){\n"""%(fakearg_path) 
    new_input += input.replace('ArgumentParser', "FakeArgumentParser")

    lines_to_append = """
        write_json(args_list, path = "%s", pretty = TRUE, auto_unbox = TRUE)
        }

    tool_params()
    """%(json_file_name)
    new_input += lines_to_append

    with open(edited_r_script_path,  'w' ) as fh:
        fh.write(new_input)


def json_to_python(json_file):
    print(json_file)
    with open(json_file) as testread:
        data = json.loads(testread.read())
        args_string = '\n    '.join(data)

        arg_str_function = f"""
from r_script_to_galaxy_wrapper import FakeArg



def r_script_argument_parsing(parent_locals, FakeArg=FakeArg):
    __description__ = "test"
    
    print_test = "OOOOOOOOO"

    parser = FakeArg(description=__description__)\n    %s

    globals().update(parent_locals)

    return parser

print("OKKsdfsfds")

blankenberg_parameters = r_script_argument_parsing(dict(locals()))

print("SDFSDFSFD")
"""%(args_string)
    
    return arg_str_function
