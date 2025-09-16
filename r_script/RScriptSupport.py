import json
import os 
import argparse
import rpy2.robjects.packages as rpackages
from rpy2.robjects.packages import PackageNotInstalledError
import xml.etree.ElementTree as ET
from xml.dom import minidom
# from r_script_to_galaxy_wrapper import FakeArg
from anvio import FakeArg, SKIP_PARAMETER_NAMES 
from pathlib import Path
import re

# Absolute path to the script file
script_path = Path(__file__).resolve().parent


def pretty_xml(element):
    rough_str = ET.tostring(element, encoding="unicode")
    reparsed = minidom.parseString(rough_str)
    return reparsed.toprettyxml(indent="  ")

class CustomFakeArg(FakeArg):
    def __init__(self, *args, **kwargs):

        self.param_cat = {}
        # call parent constructor
        super().__init__(*args, **kwargs)    

    def format_block(self, condition, inner, level):
        """Helper to wrap inner block in a properly indented ##if block."""
        indent = "    " * level
        return (
            f"{indent}#if {condition}\n"
            f"{inner}\n"
            f"{indent}#end if"
        )

        
    def dict_to_xml_and_command(self, spec, parent=None, subparser_name=None,
                                first=True, full_name=None, level=0):
        """
        Convert argparse-like dict into:
        1. Galaxy XML <param>/<conditional> structure
        2. Command template with proper indentation
        Returns (xml_element, command_str).
        """
        cmd_parts = []

        if first:
            # if not spec.get('subparsers'):
            #     return None, None
            # Top-level subparser selector
            cond = ET.Element("conditional", name="top_subparser")
            param = ET.SubElement(cond, "param", name="subparser_selector",
                                type="select", label="Select analysis type")
            for sp in spec.get("subparsers", {}):
                ET.SubElement(param, "option", value=sp).text = sp

            for sp, sp_spec in spec.get("subparsers", {}).items():
                when = ET.SubElement(cond, "when", value=sp)

                # Recurse
                xml_child, cmd_child = self.dict_to_xml_and_command(
                    sp_spec, parent=when, subparser_name=sp,
                    first=False, full_name="top_subparser",
                    level=1
                )

                if xml_child is not None:
                    when.append(xml_child)

                cmd_parts.append(
                    self.format_block(f"'${'top_subparser.subparser_selector'}' == '{sp}'",
                                cmd_child, 0)
                )

            return cond, "\n".join(cmd_parts)

        # -------- Recursive case --------

        # Add mutually exclusive groups
        for group_name, opts in spec.get("mutually_exclusive_groups", {}).items():
            cond2 = ET.Element("conditional",
                            name=f"{subparser_name}__mut_{group_name}")
            
            param2 = ET.SubElement(cond2, "param",
                                name=f"{group_name}_selector",
                                type="select",
                                label=f"Choose {group_name}")
            
            inner_lavels = level*"    "
            
            mut_cond_command = f"\n{inner_lavels}#if '${full_name}.{subparser_name}__mut_{group_name}.{group_name}_selector' == '%s'\n%s\n{inner_lavels}#end if\n"

            for o in opts:
                ET.SubElement(param2, "option", value=o).text = o
            
            mut_cond_list = []
            for o in opts:
                when2 = ET.SubElement(cond2, "when", value=o)

                mut_cond_list.append(mut_cond_command%(self.clean_arg_name(o), f"{inner_lavels}    '${full_name}.{subparser_name}__mut_{group_name}.{self.clean_arg_name(o)}'"))

                when2.append(self.generate_param( o))
            parent.append(cond2)    
            cmd_parts.append("    " * level + f"{ "\n    ".join(mut_cond_list)}\n\n")
            
        # Normal params
        for opt in spec.get("groups", {}).get("options", []):
            if opt != "--help" and "output"  not in opt:
                parent.append(self.generate_param( opt))
                cmd_parts.append("    " * level + f"'${full_name}.{self.clean_arg_name(opt)}'\n")

        # Nested subparsers
        if spec.get("subparsers"):
            cond_nested = ET.Element("conditional",
                                    name=f"{subparser_name}_subparser")
            param_nested = ET.SubElement(cond_nested, "param",
                name=f"{subparser_name}_subparser",
                type="select",
                label=f"Choose {subparser_name} option"
            )
            for sp in spec["subparsers"]:
                ET.SubElement(param_nested, "option", value=sp).text = sp

            inner_cmds = []
            for sp, sp_spec in spec["subparsers"].items():
                when_nested = ET.SubElement(cond_nested, "when", value=sp)
                xml_child, cmd_child = self.dict_to_xml_and_command(
                    sp_spec, parent=when_nested, subparser_name=sp,
                    first=False,
                    full_name=f"{full_name}.{subparser_name}_subparser",
                    level=level+1
                )

                if xml_child is not None:
                    when_nested.append(xml_child)
                inner_cmds.append(
                    self.format_block(
                        f"'${{{full_name}.{subparser_name}_subparser.{subparser_name}_subparser_selector}}' == '{sp}'",
                        cmd_child, level+1
                    )
                )

            parent.append(cond_nested)
            cmd_parts.append("\n".join(inner_cmds))

        return None, "\n".join(cmd_parts)

    def generate_galaxy_xml(self, root):
        # root = self.dict_to_xml(first=True)
        if root:
            xml_str = ET.tostring(root, encoding="unicode")
            return minidom.parseString(xml_str).toprettyxml(indent="  ")
        else:
            return ''

    def mutual_conditional(self,  spec):

        mut_list = []
        mut_command= []

        for group_name, opts in spec.get("mutually_exclusive_groups", {}).items():
            cond2 = ET.Element("conditional",
                            name=f"mut_{group_name}")
            
            param2 = ET.SubElement(cond2, "param",
                                name=f"{group_name}_selector",
                                type="select",
                                label=f"Choose {group_name}")
            for o in opts:
                # print(mut_cond_command%(clean_arg_name(o)))
                ET.SubElement(param2, "option", value=o).text = o
            
            for o in opts:
                when2 = ET.SubElement(cond2, "when", value=o)
                mut_cond_command = f"\n#if '$mut_{group_name}.{group_name}_selector' == '%s'\n%s\n#end if\n"%(self.clean_arg_name(o), f"    '${group_name}.{self.clean_arg_name(o)}'")
                mut_command.append(mut_cond_command)
                when2.append(self.generate_param(o))
            mut_list.append("\n".join(pretty_xml(cond2).split("\n")[1:]))
                
        return "\n".join(mut_list), "\n".join(mut_command)

    def flat_param_groups(self, spec):
        param_list = []
        command_list = []
        for group in spec['groups'].keys():
            for item in spec['groups'][group]:
                if item != "--help" and "output"  not in item:
                    param, command = self.generate_param( item, flat=True)
                    param_list.append("\n".join(pretty_xml(param).split("\n")[1:]))
                    command_list.append(command)
        return "\n".join(param_list),  "\n".join(command_list)
                
    def groups_params(self):
        """Return a list of <param> elements for normal group options."""
        spec = self.param_cat
        params = []
        for k in spec["groups"].keys():
            for opt in spec["groups"][k]:  
                if opt != "--help":
                    if "out" not in opt:
                        # print(ET.fromstring(self.generate_param(opt)))
                        params.append(ET.fromstring(self.generate_param(opt, flat=True)))
        # for i in params:
        #     xml_str = ET.tostring(i, encoding="unicode")
        #     # print(minidom.parseString(xml_str).toprettyxml(indent="  "))

        return params
    
    def clean_arg_name(self, arg: str) -> str:
        """Remove only leading '-' or '--' but preserve internal dashes/underscores."""
        return re.sub(r"^[-]+", "", arg).replace("-", "_")
                
    def generate_param(self, opt, flat=False):
        for d in self.oynaxraoret_get_params( {} ):
            if d.name not in SKIP_PARAMETER_NAMES and d.is_input:
                if self.clean_arg_name(opt) == d.name:
                    xml_str = d.to_xml_param()
                    if flat:
                        return ET.fromstring(xml_str), d.to_cmd_line()
                    else:
                        return ET.fromstring(xml_str)


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
    

    def generate_command_section_subpro(self, spec, tool_id="example_tool"):
        cmd_parts = []  # Galaxy allows CDATA for cleaner commands
        cmd_parts.append(tool_id)   # base executable

        # conditional for subparser
        cmd_parts.append("## Subparser")
        cmd_parts.append("$subparser_selector.subparser")

        for sub_name, sub_info in spec.get("subparsers", {}).items():
            cmd_parts.append(f"#if $subparser_selector.subparser == '{sub_name}'")

            # add normal params
            for opt in sub_info["groups"].get("options", []):
                if opt == "--help" or any(opt in v for v in sub_info["mutually_exclusive_groups"].values()):
                    continue
                arg_name = opt.lstrip("-").replace("-", "_")
                cmd_parts.append(f"    #if str($subparser_selector['{arg_name}']) != ''")
                cmd_parts.append(f"        {opt} '${{subparser_selector.{arg_name}}}'")
                cmd_parts.append("    #end if")

            # handle mutually exclusive groups
            for gname, gopts in sub_info["mutually_exclusive_groups"].items():
                cmd_parts.append(f"    #if $subparser_selector.{sub_name}_{gname}.selector")
                cmd_parts.append(f"        $subparser_selector.{sub_name}_{gname}.selector")
                cmd_parts.append("    #end if")

            cmd_parts.append("#end if")

        # cmd_parts.append("]]>")
        return "\n".join(cmd_parts)

    
    def generate_command_section_subpro_old(self, params):
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
        if "parse_args()" in line :
            new_lines.append(line)
            break  
        elif "library"  in line:
            pass
        else:
            new_lines.append(line)

    new_lines.insert(1, 'library(argparse)')
    new_string = '\n'.join(new_lines)
    return new_string

def edit_r_script(r_script_path, edited_r_script_path, fakearg_path=None, json_file_name="out.json"):
    
    if  not fakearg_path :
        fakearg_path  =  os.path.join(script_path, 'FakeArg.r')
   
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
                package_name = i.split('library(')[1].replace(')', '')
                # print("262", package_name.replace(')', ''))
                try:
                    package_importr = rpackages.importr( package_name)
                    packages['name'] =  package_name
                    packages['version'] =  package_importr.__version__
                    package_list.append((package_name, package_importr.__version__))

                except PackageNotInstalledError:
                    print(f"❌ The R package {package_name} is not installed.")
                    package_list.append((package_name, ' '))
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
    parser_name = 'parser'     
    args_string = '\n    '.join(data)
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
    def extract_from_parser(p):
        info = {'subparsers': {}, 'mutually_exclusive_groups': {}, 'groups': {}}

        # collect all actions in mutually exclusive groups so we can skip them in normal groups
        mex_actions = set()
        for mex_group in getattr(p, '_mutually_exclusive_groups', []):
            for a in mex_group._group_actions:
                mex_actions.add(a)

        # helper to get the preferred argument string (long option if available)
        def get_arg_name(a):
            if not a.option_strings:
                return a.dest
            # prefer the longest option (e.g. --something over -s)
            return max(a.option_strings, key=len)

        # 1. Groups (exclude actions already in mutually exclusive groups)
        for group in p._action_groups:
            if group.title in ('positional arguments', 'optional arguments'):
                continue
            group_args = [
                get_arg_name(a)
                for a in group._group_actions if a not in mex_actions
            ]
            if group_args:
                info['groups'][group.title] = group_args

        # 2. Mutually exclusive groups
        for i, mex_group in enumerate(getattr(p, '_mutually_exclusive_groups', [])):
            mex_args = [get_arg_name(a) for a in mex_group._group_actions]
            if mex_args:
                info['mutually_exclusive_groups'][f'group{i}'] = mex_args

        # 3. Subparsers (recursive!)
        for action in p._actions:
            if isinstance(action, argparse._SubParsersAction):
                for sub_name, sub_parser in action.choices.items():
                    info['subparsers'][sub_name] = extract_from_parser(sub_parser)

        return info

    return extract_from_parser(parser)


def extract_simple_parser_info_old(parser):
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

def logical(value):
    val = value.lower()
    if val == "true":
        return True
    elif val == "false":
        return False
    else:
        raise argparse.ArgumentTypeError(f"Invalid logical value: {value}. Only TRUE or FALSE allowed.")
