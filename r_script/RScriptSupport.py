import json
import os 
import rpy2.robjects.packages as rpackages

def clean_r_script(lines):
    new_lines = []

    for i, line in enumerate(lines):
        if "parse_args()" in line:
            new_lines.append(line)
            break  
        else:
            new_lines.append(line)
  
    new_string = '\n'.join(new_lines)
    
    return new_string


def edit_r_script(r_script_path, edited_r_script_path, fakearg_path=None, json_file_name="out.json"):
    
    if  not fakearg_path :
        fakearg_path  =  os.path.join(os.getcwd(), 'FakeArg.r')
   
    with open(r_script_path,  'r' ) as fh:
        input = fh.read()

    cleaned_lines = clean_r_script(input.split('\n'))    


    new_input = """source("%s")\ntool_params = function (){\n"""%(fakearg_path) 
    new_input += cleaned_lines.replace('ArgumentParser', "FakeArgumentParser")

    lines_to_append = """
        write_json(args_list, path = "%s", pretty = TRUE, auto_unbox = TRUE)
        }

    tool_params()
    """%(json_file_name)
    new_input += lines_to_append

    with open(edited_r_script_path,  'w' ) as fh:
        fh.write(new_input)

def return_dependencies(r_script_path):
    package_list = []
    packages = {'name':None, 'version':None}
    with open(r_script_path,  'r' ) as fh:
        input = fh.read()
        for i in input.split('\n'):
            if "library(" in i and "argparse" not in i:
                package_name = i.split('(')[1].strip(')')
                package_importr = rpackages.importr( package_name)
                packages['name'] =  package_name
                packages['version'] =  package_importr.__version__
                package_list.append((package_name, package_importr.__version__))
    return package_list


def clean_json(json_file):
    with open(json_file) as testread:
        data = json.loads(testread.read())
    cleaned_json = []
    for d in data:
        if "add_argument" in d and "add_argument_group" not in d:
            cleaned_json.append('parser.add_argument'+d.split(".add_argument")[1])
    return cleaned_json
   
def json_to_python(json_file):

    data = clean_json(json_file)
    parser_name = 'parser'     
    args_string = '\n    '.join(data)

    arg_str_function = f"""
#!/usr/bin/env python
from r_script_to_galaxy_wrapper import FakeArg

def r_script_argument_parsing(parent_locals, FakeArg=FakeArg):
    __description__ = "test"
    
    parser = FakeArg(description=__description__)\n    %s
    globals().update(parent_locals)

    return parser

blankenberg_parameters = r_script_argument_parsing(dict(locals()))

"""%(args_string)
    
    return arg_str_function
