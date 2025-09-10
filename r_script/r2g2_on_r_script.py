import argparse
import subprocess
import tempfile
import os
import shutil
from r_script_to_galaxy_wrapper import *
from dependency_generator import  return_galax_tag
import xml.etree.ElementTree as ET
from xml.dom import minidom

from RScriptSupport import (
    edit_r_script,
    json_to_python,
    return_dependencies,
    json_to_python_for_param_info,
    extract_simple_parser_info,
    #TBD: R's logical type need be handled correctly while building galaxy input params. 
    logical
)

def generate_galaxy_xml(xml_str):
    
    xml_str = ET.tostring(xml_str, encoding="unicode")
    return minidom.parseString(xml_str).toprettyxml(indent="  ")

def main(r_script, out_dir, profile, dep_info, description, tool_version, citation_doi):

    if not citation_doi:
        citation_doi = ''

    if not description:
        description = r_script.split('/')[len(r_script.split('/'))-1].split('.')[0] + " tool"

    dependency_tag = "\n".join([return_galax_tag(i[0], i[1], dep_info) for i in return_dependencies(r_script)])
    current_dir = os.getcwd()
    temp_dir = tempfile.mkdtemp(dir=current_dir)

    if not os.path.exists(os.path.join(current_dir, out_dir)):
        os.makedirs(os.path.join(current_dir, out_dir))
        
    edited_r_script  = os.path.join(temp_dir, "%s_edited.r"%(r_script.split('/')[len(r_script.split('/'))-1].split('.')[0])) 
    
    print("####################################################################")
    print("R script with argument parsing edited and processed successfully...")
    print("####################################################################")

    json_out  = os.path.join(temp_dir, "%s.json"%(r_script.split('/')[len(r_script.split('/'))-1].split('.')[0]))  

    print("####################################################################")
    print("Extracted arguments have been written to a JSON file successfully...")  
    print("####################################################################")
   
    edit_r_script(r_script, edited_r_script, json_file_name=json_out )

   
    subprocess.run(['Rscript',  edited_r_script])

    python_code_as_string = json_to_python(json_out)
    param_info_dict = {}
    argument_string = json_to_python_for_param_info(json_out)
    argument_string.replace('logical', 'boolean')

    exec(argument_string, globals(), param_info_dict)

    param_info = param_info_dict.get('param_info')
    # param_cat = extract_simple_parser_info(param_info)

    print(param_info)

    print("####################################################################")
    print("Converted R arguments to Python argparse successfully...")
    print("####################################################################")

    input = python_code_as_string
    params = {}
    __provides__ = [] # Reset provides since it is not always declared
    local_dict={}
    global_dict={}
    local_dict = {}

    exec(input, globals(), local_dict)

    blankenberg_parameters = local_dict.get('blankenberg_parameters')
    blankenberg_parameters.param_cat = extract_simple_parser_info(param_info)

    print(blankenberg_parameters.param_cat )

    print("####################################################################")
    print("Tool parameters have been extracted successfully...")
    print("####################################################################")

    DEFAULT_TOOL_TYPE = "test_tools"
    tool_type = DEFAULT_TOOL_TYPE
    filename = r_script.split('/')[len(r_script.split('/'))-1]


    print(generate_galaxy_xml(blankenberg_parameters.dict_to_xml()))

    # Reformated_command = blankenberg_parameters.oynaxraoret_to_cmd_line(params, filename).replace(filename, "Rscript '$__tool_directory__/%s'"%(filename))
    if blankenberg_parameters.param_cat['subparsers'] != {}:
        # cond_params = blankenberg_parameters.generate_conditional_block( {})
        # cond_command = blankenberg_parameters.generate_command_section_subpro( {})
        # print(blankenberg_parameters.generate_conditional_block())
        pass
    else:
        cond_params, cond_command = '', ''

    if blankenberg_parameters.param_cat['mutually_exclusive_groups']:
        mut_cond_params = blankenberg_parameters.generate_mutual_group_conditionals( {}),
        mut_cond_command = blankenberg_parameters.generate_mutual_group_command( {}),
    else:
        mut_cond_params, mut_cond_command = '', ''

    inputs = [    
        # cond_params,  
        blankenberg_parameters.generate_misc_params( {}),
        mut_cond_params
    ]

    command_str = [
        "Rscript '$__tool_directory__/%s'\n"%(filename),
        blankenberg_parameters.generate_misc_cmd({}),
        # cond_command,
        mut_cond_command[0] ,
    ]
    # print(blankenberg_parameters.oynaxraoret_to_outputs(params))
    cleaned_filename = filename.lower().replace( '-', '_').replace('.r', '')

    template_dict = {
        'id': cleaned_filename ,
        'tool_type': tool_type,
        'profile': profile,
        'name': cleaned_filename,
        'version': tool_version,
        'description': description,
        #'macros': None,
        'version_command': '%s --version' % filename,
        'requirements': dependency_tag,
        'command': "\n\n".join(command_str), 
        'inputs': inputs,
        'outputs': blankenberg_parameters.oynaxraoret_to_outputs(params),
        #'tests': None,
        'help': format_help(blankenberg_parameters.format_help().replace(os.path.basename(__file__), filename)),
        'doi': citation_doi.split(','),
        'bibtex_citations': galaxy_tool_citation,
        'bibtex_citations': ''
        }

    tool_xml = Template(TOOL_TEMPLATE).render( **template_dict )

    with open( os.path.join ('./', out_dir, "%s.xml" % cleaned_filename ), 'w') as out:
        out.write(tool_xml)

    if os.path.exists(temp_dir) and os.path.isdir(temp_dir):
        shutil.rmtree(temp_dir)
        # print(f"Deleted directory: {temp_dir}")
    else:
        print(f"Directory does not exist: {temp_dir}")

if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument('-r', '--r_script_name', required=True, help="Provide the path of an R script... ")
    parser.add_argument('-o', '--output_dir', required=False, default='out')
    parser.add_argument('-p', '--profile', required=False, default="22.01")
    parser.add_argument('-d', '--description', required=False, default=None, help="tool based on R script")
    parser.add_argument('-s', '--dependencies', required=False,  default=False, help=" Extract dependency information..")
    parser.add_argument('-v', '--tool_version', required=False,  default='0.0.1', help="Galaxy tool version..")
    parser.add_argument('-c', '--citation_doi', required=False,  default=None, help="Comma separated Citation DOI.")

    args = parser.parse_args()

    main(args.r_script_name, args.output_dir, args.profile, args.dependencies, args.description, args.tool_version, args.citation_doi)