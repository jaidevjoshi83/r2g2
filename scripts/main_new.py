import argparse
from RScriptSupport import edit_r_script, json_to_python
import subprocess
import tempfile
import os
from r_script_to_galaxy_wrapper import *

def main(r_script, out_dir):

    current_dir = os.getcwd()
    temp_dir = tempfile.mkdtemp(dir=current_dir)

    if not os.path.exists(os.path.join(current_dir, out_dir)):
        os.makedirs(os.path.join(current_dir, out_dir))
    edited_r_script  = os.path.join(temp_dir, "%s_edited.r"%(r_script.split('/')[len(r_script.split('/'))-1].split('.')[0])) 
    json_out  = os.path.join(temp_dir, "%s.json"%(r_script.split('/')[len(r_script.split('/'))-1].split('.')[0])) 

    edit_r_script(r_script, edited_r_script, json_file_name=json_out )
    subprocess.run(['Rscript',  edited_r_script])
    python_code_as_string = json_to_python(json_out)
    # test = open("./test.py", "w")
    input = python_code_as_string

    params = {}
    param_name = 'parser'
    arg_groups = []
    parser_name = 'parent_parser'


    __provides__ = [] # Reset provides since it is not always declared
    local_dict={}
    global_dict={}
    local_dict = {}

    exec( input, globals(), local_dict)
    blankenberg_parameters = local_dict.get('blankenberg_parameters')


    tool_type = DEFAULT_TOOL_TYPE
    for provides, ttype in PROVIDES_TO_TOOL_TYPE.items():
        if provides in __provides__:
            tool_type = ttype
            break
    if tool_type == 'interactive':
        containers = DEFAULT_CONTAINERS
        # TODO: grab port from args, right now setting all to 8080
        #ports = ['<port name="%s server" type="tcp">%s</port>' % (filename, DEFAULT_INTERACTIVE_PORT)]
        realtime = [dict(
                    name="%s server" % (filename),
                    port=DEFAULT_INTERACTIVE_PORT,
                    url=None
                    )]
        profile = INTERACTIVE_PROFILE_VERSION
        print("%s is an InteractiveTool." % (filename))
    else:
        containers = []
        realtime = None
        profile = ''

    filename = 'test-file'

    test_print =  blankenberg_parameters.blankenberg_to_cmd_line(params, filename)

    ANVIO_VERSION = '0.1'
    template_dict = {
        'id': filename.replace( '-', '_'),
        'tool_type': tool_type,
        'profile': profile,
        'name': filename,
        'version': ANVIO_VERSION,
        'description': blankenberg_parameters.description,
        #'macros': None,
        'version_command': '%s --version' % filename,
        'requirements': ['<requirement type="package" version="%s">anvio</requirement>' % ANVIO_VERSION ],
        'containers': containers,
        'realtime': realtime,
        'command': blankenberg_parameters.blankenberg_to_cmd_line(params, filename),
        'inputs': blankenberg_parameters.blankenberg_to_inputs(params),
        'outputs': blankenberg_parameters.blankenberg_to_outputs(params),
        #'tests': None,
        #'tests': { output:'' },
        'help': format_help(blankenberg_parameters.format_help().replace( os.path.basename(__file__), filename)),
        'doi': ['10.7717/peerj.1319'],
        'bibtex_citations': [galaxy_tool_citation]
        }

    tool_xml = Template(TOOL_TEMPLATE).render( **template_dict )

    with open( os.path.join ('./test_out', "%s.xml" % filename ), 'w') as out:
        out.write(tool_xml)


if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument('-r', '--r_file_name', required=True, help="Provide path of a R file... ")
    parser.add_argument('-o', '--output_dir', required=False, default='out')
    args = parser.parse_args()
    main(args.r_file_name, args.output_dir)
