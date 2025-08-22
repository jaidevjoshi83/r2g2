import json
import os 
import argparse
import rpy2.robjects.packages as rpackages
import xml.etree.ElementTree as ET
# from r_script_to_galaxy_wrapper import FakeArg
from anvio import FakeArg, SKIP_PARAMETER_NAMES 

class CustomFakeArg(FakeArg):
    def __init__(self, *args, **kwargs):

        self.param_cat = {}
        # call parent constructor
        super().__init__(*args, **kwargs)
    
    def generate_conditional_block(self,  params):
        """Generate Galaxy XML <conditional> block based on param definitions and subprocess mapping."""
        # Build lookup: argument -> XML snippet

        sub_process = self.param_cat['subparsers']

        param_lookup = {}
        for d in self.oynaxraoret_get_params( params ):
            if d.name not in SKIP_PARAMETER_NAMES and d.is_input:
                arg = d.name
                if arg:
                    param_lookup[arg] = d.to_xml_param()

        xml_lines = []
        xml_lines.append('<conditional name="sub_process">')
        xml_lines.append('  <param name="process" type="select" label="Select Process">')
        for proc in sub_process:
            xml_lines.append(f'    <option value="{proc}">{proc.capitalize()}</option>')
        xml_lines.append('  </param>')

        for proc, args in sub_process.items():
            xml_lines.append(f'  <when value="{proc}">')
            for arg in args:
                if arg in param_lookup.keys():
                    xml_lines.append(f'    {param_lookup[arg]}')
                else:
                    xml_lines.append(f'    <!-- No param XML found for {arg} -->')
            xml_lines.append('  </when>')

        xml_lines.append('</conditional>')
        return "    \n".join(xml_lines)
    
    def generate_mutual_group_conditionals(self,   params):
        """Generate <conditional> blocks for each mutual exclusion group."""
       
        mut_groups = self.param_cat['mutually_exclusive_groups']

        # Build lookup: argument -> full <param> snippet
        param_lookup = {}
        for d in self.oynaxraoret_get_params( params ):
            if d.name not in SKIP_PARAMETER_NAMES and d.is_input:
                arg = d.name
                if arg:
                    param_lookup[arg] = d.to_xml_param()

        xml_lines = []

        for group_name, args in mut_groups.items():
            xml_lines.append(f'<conditional name="{group_name}">')
            xml_lines.append(f'  <param name="process" type="select" label="Select Option for {group_name}">')
            for arg in args:
                safe_option = arg.lstrip('-').replace('-', '_')
                xml_lines.append(f'    <option value="{safe_option}">{safe_option}</option>')
            xml_lines.append('  </param>')

            for arg in args:
                safe_option = arg.lstrip('-').replace('-', '_')
                xml_lines.append(f'  <when value="{safe_option}">')
                if arg in param_lookup:
                    xml_lines.append(f'    {param_lookup[arg]}')
                else:
                    xml_lines.append(f'    <!-- No param XML found for {arg} -->')
                xml_lines.append('  </when>')

            xml_lines.append('</conditional>')

        return "\n\t".join(xml_lines)
    
    def generate_misc_params(self, params):
        """
        Generate <param> blocks for arguments that are NOT in sub_process or mutual groups.
        Returns a joined string of <param> XML snippets.
        """

        sub_process = self.param_cat['subparsers']
        mut_groups = self.param_cat['mutually_exclusive_groups']

        # Flatten all arguments from sub_process
        sub_args = set(arg for args in sub_process.values() for arg in args)
        # Flatten all arguments from mutual groups
        mut_args = set(arg for args in mut_groups.values() for arg in args)
        # All grouped arguments
        grouped_args = sub_args.union(mut_args)

        misc_lines = []

        for d in self.oynaxraoret_get_params( params ):
            if d.name not in SKIP_PARAMETER_NAMES and d.is_input:
                arg = d.name
                if arg and arg not in grouped_args:
                    misc_lines.append(d.to_xml_param())

        return "\n\t".join(misc_lines)
    
    def generate_command_section_subpro(self, params):
        """Generate Galaxy XML <command> block matching the conditional subprocess options."""
        # Build lookup: argument -> name

        # for d in param_strings:
        #     param = ET.fromstring(d)
        #     arg = param.attrib.get('argument')
        #     name = param.attrib.get('name')
        #     if arg and name:
        #         param_lookup[arg] = name

        sub_process = self.param_cat['subparsers']

        param_lookup = {}

        for d in self.oynaxraoret_get_params( params ):
            if d.name not in SKIP_PARAMETER_NAMES and d.is_input:
                arg = d.name
                name = d.name
                if arg and name:
                     param_lookup[arg] = name

        cmd_lines = []
        first = True
        for proc, args in sub_process.items():
            if first:
                cmd_lines.append(f'    #if $sub_process.process == "{proc}"')
                first = False
            else:
                cmd_lines.append(f'    #elif $sub_process.process == "{proc}"')

            for arg in args:
                if arg in param_lookup:
                    cmd_lines.append(f'        {arg} "${{sub_process.{param_lookup[arg]}}}"')
                else:
                    safe_name = arg.strip("-").replace("-", "_")
                    cmd_lines.append(f'        {arg} "${{sub_process.missing_param_for_{safe_name}}}"')

        cmd_lines.append('    #end if')
        return "\n\t".join(cmd_lines)
    
    def generate_mutual_group_command(self, params):
        """Generate <command> block for mutually exclusive argument groups."""
        # Build lookup: argument -> param name

        mut_groups = self.param_cat['mutually_exclusive_groups']
        param_lookup = {}
        for d in self.oynaxraoret_get_params( params ):
            if d.name not in SKIP_PARAMETER_NAMES and d.is_input:
                arg = d.name
                name = d.name
                if arg and name:
                     param_lookup[arg] = name

        cmd_lines = []
  
        # Loop over groups
        for group_name, args in mut_groups.items():
            first = True
            for arg in args:
                safe_option = arg.lstrip('-').replace('-', '_')
                if first:
                    cmd_lines.append(f'    #if ${group_name}.process == "{safe_option}"')
                    first = False
                else:
                    cmd_lines.append(f'    #elif ${group_name}.process == "{safe_option}"')

                if arg in param_lookup:
                    cmd_lines.append(f'        {arg} "${{{group_name}.{param_lookup[arg]}}}"')
                else:
                    cmd_lines.append(f'        {arg} "${{{group_name}.missing_param_for_{safe_option}}}"')

            cmd_lines.append('    #end if')
        return "\n\t".join(cmd_lines)
    
    def generate_misc_cmd(self, params):
        """
        Generate <param> blocks for arguments that are NOT in sub_process or mutual groups.
        Returns a joined string of <param> XML snippets.
        """
        sub_process = self.param_cat['subparsers']
        mut_groups = self.param_cat['mutually_exclusive_groups']

        # Flatten all arguments from sub_process
        sub_args = set(arg for args in sub_process.values() for arg in args)
        # Flatten all arguments from mutual groups
        mut_args = set(arg for args in mut_groups.values() for arg in args)
        # All grouped arguments
        grouped_args = sub_args.union(mut_args)

        misc_lines = []

        for d in self.oynaxraoret_get_params( params ):
            if d.name not in SKIP_PARAMETER_NAMES and d.is_input:
                arg = d.name
                if arg and arg not in grouped_args:
                    misc_lines.append(d.to_cmd_line())
                    
        return "\n\t".join(misc_lines)

        


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
    for i in data:
        if "add_argument" in i:
            cleaned_json.append("parser.add_argument"+i.split('.add_argument')[1])
    return cleaned_json


# def clean_json(json_file):
#     with open(json_file) as testread:
#         data = json.loads(testread.read())

#     return data

def json_to_python_for_param_info(json_file):

    with open(json_file) as testread:
        data = json.loads(testread.read())

    # print(data)
    parser_name = 'parser'     
    args_string = '\n    '.join(data)
    # print(args_string )
    arg_str_function = f"""
#!/usr/bin/env python
import argparse

def param_info_parsing(parent_locals):
    parser = argparse.ArgumentParser()\n    %s
    globals().update(parent_locals)

    return parser
param_info = param_info_parsing(dict(locals()))

"""%(args_string)    
    return arg_str_function

def json_to_python(json_file):

    data = clean_json(json_file)
    # print(data)
    parser_name = 'parser'     
    args_string = '\n    '.join(data)
    # print(args_string )
    arg_str_function = f"""
#!/usr/bin/env python
# from r_script_to_galaxy_wrapper import FakeArg
from RScriptSupport import CustomFakeArg
import json
import argparse

# def param_info_parsing(parent_locals):
#     parser_1 = argparse.ArgumentParser()\n   
#     globals().update(parent_locals)
#     return parser_1

def r_script_argument_parsing(parent_locals, CustomFakeArg=CustomFakeArg):
    __description__ = "test"
    
    parser = CustomFakeArg(description=__description__)\n    %s
    globals().update(parent_locals)

    param_info  =  param_info_parsing(dict(locals()))
    # parser.param_cat = extract_simple_parser_info(param_info)

    return parser

blankenberg_parameters = r_script_argument_parsing(dict(locals()))

"""%(args_string)
    
    return arg_str_function

def extract_simple_parser_info(parser):
    result = {'subparsers': {}, 'mutually_exclusive_groups': {}, 'groups': {}}

    # 1. Groups
    for group in parser._action_groups:
        # skip default positional/optional groups
        if group.title in ('positional arguments', 'optional arguments'):
            continue
        group_args = [a.option_strings[0].lstrip('-').replace('-', '_') if a.option_strings else a.dest for a in group._group_actions]
        result['groups'][group.title] = group_args

    # 2. Mutually exclusive groups
    for i, mex_group in enumerate(getattr(parser, '_mutually_exclusive_groups', [])):
        mex_args = [a.option_strings[0].lstrip('-').replace('-', '_')  for a in mex_group._group_actions]
        result['mutually_exclusive_groups'][f'group{i}'] = mex_args

    # 3. Subparsers
    for action in parser._actions:
        if isinstance(action, argparse._SubParsersAction):
            for sub_name, sub_parser in action.choices.items():
                sub_args = [a.option_strings[0].lstrip('-').replace('-', '_')  if a.option_strings else a.dest for a in sub_parser._actions if not isinstance(a, argparse._SubParsersAction)]
                result['subparsers'][sub_name] = sub_args

    return result

def generate_conditional_block(param_strings, sub_process):
    """Generate Galaxy XML <conditional> block based on param definitions and subprocess mapping."""
    # Build lookup: argument -> XML snippet
    param_lookup = {}
    for d in param_strings:
        param = ET.fromstring(d)
        arg = param.attrib.get('argument')
        if arg:
            param_lookup[arg] = d

    xml_lines = []
    xml_lines.append('<conditional name="sub_process">')
    xml_lines.append('  <param name="process" type="select" label="Select Process">')
    for proc in sub_process:
        xml_lines.append(f'    <option value="{proc}">{proc.capitalize()}</option>')
    xml_lines.append('  </param>')

    for proc, args in sub_process.items():
        xml_lines.append(f'  <when value="{proc}">')
        for arg in args:
            if arg in param_lookup:
                xml_lines.append(f'    {param_lookup[arg]}')
            else:
                xml_lines.append(f'    <!-- No param XML found for {arg} -->')
        xml_lines.append('  </when>')

    xml_lines.append('</conditional>')
    return "\n".join(xml_lines)


def generate_command_section_subpro(param_strings, sub_process):
    """Generate Galaxy XML <command> block matching the conditional subprocess options."""
    # Build lookup: argument -> name
    param_lookup = {}
    for d in param_strings:
        param = ET.fromstring(d)
        arg = param.attrib.get('argument')
        name = param.attrib.get('name')
        if arg and name:
            param_lookup[arg] = name

    cmd_lines = []
    first = True
    for proc, args in sub_process.items():
        if first:
            cmd_lines.append(f'    #if $sub_process.process == "{proc}"')
            first = False
        else:
            cmd_lines.append(f'    #elif $sub_process.process == "{proc}"')

        for arg in args:
            if arg in param_lookup:
                cmd_lines.append(f'        {arg} "${{sub_process.{param_lookup[arg]}}}"')
            else:
                safe_name = arg.strip("-").replace("-", "_")
                cmd_lines.append(f'        {arg} "${{sub_process.missing_param_for_{safe_name}}}"')

    cmd_lines.append('    #end if')
    return "\n".join(cmd_lines)

def generate_mutual_group_conditionals(param_strings, mut_groups):
    """Generate <conditional> blocks for each mutual exclusion group."""
    # Build lookup: argument -> full <param> snippet
    param_lookup = {}
    for d in param_strings:
        param = ET.fromstring(d)
        arg = param.attrib.get('argument')
        if arg:
            param_lookup[arg] = d

    xml_lines = []

    for group_name, args in mut_groups.items():
        xml_lines.append(f'<conditional name="{group_name}">')
        xml_lines.append(f'  <param name="process" type="select" label="Select Option for {group_name}">')
        for arg in args:
            safe_option = arg.lstrip('-').replace('-', '_')
            xml_lines.append(f'    <option value="{safe_option}">{safe_option}</option>')
        xml_lines.append('  </param>')

        for arg in args:
            safe_option = arg.lstrip('-').replace('-', '_')
            xml_lines.append(f'  <when value="{safe_option}">')
            if arg in param_lookup:
                xml_lines.append(f'    {param_lookup[arg]}')
            else:
                xml_lines.append(f'    <!-- No param XML found for {arg} -->')
            xml_lines.append('  </when>')

        xml_lines.append('</conditional>')

    return "\n".join(xml_lines)

def generate_mutual_group_command(param_strings, mut_groups):
    """Generate <command> block for mutually exclusive argument groups."""
    # Build lookup: argument -> param name
    param_lookup = {}
    for d in param_strings:
        param = ET.fromstring(d)
        arg = param.attrib.get('argument')
        name = param.attrib.get('name')
        if arg and name:
            param_lookup[arg] = name

    cmd_lines = []
    cmd_lines.append('<command>')
    cmd_lines.append('    tool_exe')

    # Loop over groups
    for group_name, args in mut_groups.items():
        first = True
        for arg in args:
            safe_option = arg.lstrip('-').replace('-', '_')
            if first:
                cmd_lines.append(f'    #if ${group_name}.process == "{safe_option}"')
                first = False
            else:
                cmd_lines.append(f'    #elif ${group_name}.process == "{safe_option}"')

            if arg in param_lookup:
                cmd_lines.append(f'        {arg} "${{{group_name}.{param_lookup[arg]}}}"')
            else:
                cmd_lines.append(f'        {arg} "${{{group_name}.missing_param_for_{safe_option}}}"')

        cmd_lines.append('    #end if')

    cmd_lines.append('</command>')
    return "\n".join(cmd_lines)

