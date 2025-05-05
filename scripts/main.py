#edit R script to add custom fakearg parser 
#Execute edited R script to extract arguments as python arguments to a json file 
#Build python script based on json string to get the parameter dictionary 
#Generates wrapper 
import argparse
from RScriptSupport import edit_r_script, json_to_python
import subprocess
import tempfile
import os
import shutil
from r_script_to_galaxy_wrapper import DEFAULT_TOOL_TYPE, TOOL_TEMPLATE, FakeArg, format_help, galaxy_tool_citation, Template

def main(r_script, out_dir):
    # Get current working directory
    current_dir = os.getcwd()
    # Create a temp directory inside current working directory
    temp_dir = tempfile.mkdtemp(dir=current_dir)

    if not os.path.exists(os.path.join(current_dir, out_dir)):
        os.makedirs(os.path.join(current_dir, out_dir))
    edited_r_script  = os.path.join(temp_dir, "%s_edited.r"%(r_script.split('/')[len(r_script.split('/'))-1].split('.')[0])) 
    json_out  = os.path.join(temp_dir, "%s.json"%(r_script.split('/')[len(r_script.split('/'))-1].split('.')[0])) 

    edit_r_script(r_script, edited_r_script, json_file_name=json_out )
    # Run the R script
    subprocess.run(['Rscript',  edited_r_script])

    python_code_as_string = json_to_python(json_out)

    __provides__ = [] # Reset provides since it is not always declared
    local_dict={}
    global_dict={}
    local_dict={}

    exec( python_code_as_string, globals(), local_dict)
    extracted_parameters = local_dict.get('blankenberg_parameters')
    tool_type = DEFAULT_TOOL_TYPE

    params = {}

    containers = []
    realtime = None
    profile = ''
    
    filename = 'test_tool'

    template_dict = {
        'id': filename.replace( '-', '_'),
        'tool_type': tool_type,
        'profile': profile,
        'name': filename,
        'version': '',
        'description': extracted_parameters.description,
        #'macros': None,
        'version_command': '%s --version' % filename,
        'requirements': ['<requirement type="package" version="%s">anvio</requirement>' % '' ],
        'containers': containers,
        'realtime': realtime,
        'command': extracted_parameters.blankenberg_to_cmd_line(params, filename),
        'inputs': extracted_parameters.blankenberg_to_inputs(params),
        'outputs': extracted_parameters.blankenberg_to_outputs(params),
        #'tests': None,
        #'tests': { output:'' },
        'help': format_help(extracted_parameters.format_help().replace( os.path.basename(__file__), filename)),
        'doi': ['10.7717/peerj.1319'],
        'bibtex_citations': [galaxy_tool_citation]
        }

    tool_xml = Template(TOOL_TEMPLATE).render( **template_dict )

    print(r_script.split('/')[len(r_script.split('/'))-1].split('.')[0])
    with open(os.path.join(out_dir, "my_first_tool.xml")  , 'w') as out:
        out.write(tool_xml)

    if os.path.exists(temp_dir):
        shutil.rmtree(temp_dir)
 
if __name__=='__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument("--r_script_path","-r", type=str, required=True)
    parser.add_argument("--out_dir", "-o", type=str, required=False, default='out')
    args = parser.parse_args()
    main(args.r_script_path, args.out_dir)



