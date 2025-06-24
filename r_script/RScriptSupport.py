import json
import os 
import rpy2.robjects.packages as rpackages


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

def return_dependencies(r_script_path):
    package_list = []
    packages = {'name':None, 'version':None}
    with open(r_script_path,  'r' ) as fh:
        input = fh.read()
        for i in input.split('\n'):
            if "library(" in i:
                package_name = i.split('(')[1].strip(')')
                package_importr = rpackages.importr( package_name)
                packages['name'] =  package_name
                packages['version'] =  package_importr.__version__
                package_list.append((package_name, package_importr.__version__))
    return package_list
   
def json_to_python(json_file):
    # print(json_file)
    with open(json_file) as testread:
        data = json.loads(testread.read())

    parser_name = 'parser'
    arg_groups = []
    inp_list = []
    mutually_ex_groups = []

    for line in data:
        if 'add_argument_group' in line:
            group_name = line.strip().split()[0]
            arg_groups.append( group_name )
            #print 'added group', group_name    
        elif "add_mutually_exclusive_group" in line:
            mutually_ex_name = line.strip().split()[0]
            mutually_ex_groups.append(mutually_ex_name)
        else:
            for group_name in arg_groups:
                if group_name in line:
                    line = line.replace( group_name, parser_name )
                    inp_list.append(line)
            

        args_string = '\n    '.join(inp_list)

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
