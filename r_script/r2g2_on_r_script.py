import argparse
from RScriptSupport import edit_r_script, json_to_python, return_dependencies
import subprocess
import tempfile
import os
import shutil
from r_script_to_galaxy_wrapper import *
from dependency_generator import  return_galax_tag

def main(r_script, out_dir):
    dependency_tag = "\n".join([return_galax_tag(i[0], i[1]) for i in return_dependencies(r_script)])
   
    # dependency_tag = ''
    # print("14", dependency_tag)
    current_dir = os.getcwd()
    temp_dir = tempfile.mkdtemp(dir=current_dir)

    if not os.path.exists(os.path.join(current_dir, out_dir)):
        os.makedirs(os.path.join(current_dir, out_dir))
    edited_r_script  = os.path.join(temp_dir, "%s_edited.r"%(r_script.split('/')[len(r_script.split('/'))-1].split('.')[0])) 
    json_out  = os.path.join(temp_dir, "%s.json"%(r_script.split('/')[len(r_script.split('/'))-1].split('.')[0])) 
    
    edit_r_script(r_script, edited_r_script, json_file_name=json_out )
    subprocess.run(['Rscript',  edited_r_script])
    python_code_as_string = json_to_python(json_out)
    input = python_code_as_string
    params = {}
    __provides__ = [] # Reset provides since it is not always declared
    local_dict={}
    global_dict={}
    local_dict = {}

    exec(input, globals(), local_dict)
    blankenberg_parameters = local_dict.get('blankenberg_parameters')

    DEFAULT_TOOL_TYPE = "test_tools"
    tool_type = DEFAULT_TOOL_TYPE
    profile = '3.10'
    filename = r_script.split('/')[len(r_script.split('/'))-1]

    Reformated_command = blankenberg_parameters.blankenberg_to_cmd_line(params, filename).replace(filename, "Rscript '$__tool_directory__/%s'"%(filename))

    template_dict = {
        'id': filename.replace( '-', '_'),
        'tool_type': tool_type,
        'profile': profile,
        'name': filename,
        'version': '0.1.0',
        'description': blankenberg_parameters.description,
        #'macros': None,
        'version_command': '%s --version' % filename,
        'requirements': dependency_tag,
        #'command': blankenberg_parameters.blankenberg_to_cmd_line(params, filename),
        'command': Reformated_command, 
        'inputs': blankenberg_parameters.blankenberg_to_inputs(params),
        'outputs': blankenberg_parameters.blankenberg_to_outputs(params),
        #'tests': None,
        #'tests': { output:'' },
        'help': format_help(blankenberg_parameters.format_help().replace( os.path.basename(__file__), filename)),
        # 'doi': [''],
        # 'bibtex_citations': [galaxy_tool_citation]
        'bibtex_citations': ''
        }

    tool_xml = Template(TOOL_TEMPLATE).render( **template_dict )

    with open( os.path.join ('./', out_dir, "%s.xml" % filename ), 'w') as out:
        out.write(tool_xml)

    if os.path.exists(temp_dir) and os.path.isdir(temp_dir):
        shutil.rmtree(temp_dir)
        print(f"Deleted directory: {temp_dir}")
    else:
        print(f"Directory does not exist: {temp_dir}")

if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument('-r', '--r_script_name', required=True, help="Provide the path of an R script... ")
    parser.add_argument('-o', '--output_dir', required=False, default='out')
    args = parser.parse_args()
    main(args.r_file_name, args.output_dir)