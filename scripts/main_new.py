# from tool_generator_anvio import *
import argparse
from RScriptSupport import edit_r_script, json_to_python
import subprocess
import tempfile
import os
# import shutil
# from r_script_to_galaxy_wrapper import DEFAULT_TOOL_TYPE, TOOL_TEMPLATE, FakeArg, format_help, galaxy_tool_citation, Template
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

    inp_list = input.split( '\n' )
    for i, line in enumerate( inp_list ):
        if '%s.parse_args()' % (parser_name) in line:
            indent = len(line) - len( line.lstrip( ' ' ) )
            inp_list[i] = " " * indent + "return %s" % (parser_name) #"return parser.parse_args()"
        if '%s.parse_known_args()' % (parser_name) in line:
            indent = len(line) - len( line.lstrip( ' ' ) )
            inp_list[i] = " " * indent + "return %s" % (parser_name) #"return parser.parse_args()"
        if 'import ' in line and '"' not in line and line.strip().startswith('import') and '\\' not in line:
            indent = len(line) - len( line.lstrip( ' ' ) )
            line2 = """%stry:
%s    %s
%sexcept Exception as e:
%s    print ('Failed import', e)
""" % ( " " * indent, " " * indent, line.lstrip( ' ' ), " " * indent, " " * indent )
            inp_list[i] = line2
        if 'add_argument_group' in line:
            group_name = line.strip().split()[0]
            arg_groups.append( group_name )
            #print 'added group', group_name
        else:
            for group_name in arg_groups:
                if group_name in line:
                    line = line.replace( group_name, parser_name )
                    inp_list[i] = line

    output = '\n'.join( inp_list )
    output = """%s
blankenberg_parameters = blankenberg_parsing(dict(locals()))""" % output

    __provides__ = [] # Reset provides since it is not always declared
    local_dict={}
    global_dict={}
    local_dict = {}

    # print(output)
    exec( input, globals(), local_dict)
    blankenberg_parameters = local_dict.get('blankenberg_parameters')

    print("###################################################")
    print(blankenberg_parameters)
    print("###################################################")

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

    #test = {'choices': ('normal', 'uniform', 'binomial'), 'default': 'normal', 'help': 'The distribution mode to use. Choices are: normal, uniform, or binomial [default %(default)s]'}

    test_print =  blankenberg_parameters.blankenberg_to_cmd_line(params, filename)

    print ("#$#$#$#$#$#$#$#$#$#$#$#$133" )
    print( test_print)
    print ("#$#$#$#$#$#$#$#$#$#$#$#$137")

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
    # print('template_dict', template_dict)
    tool_xml = Template(TOOL_TEMPLATE).render( **template_dict )
    # print('tool_xml', tool_xml)

    with open( os.path.join ('./test_out', "%s.xml" % filename ), 'w') as out:
        out.write(tool_xml)
        # xml_count += 1
            #sys.exit()
    # else:
    #     print('no parse!')
# else:
#     print('not python')
    print("Created %i anvi'o Galaxy tools." % (1))
    '''
        print filename,
        line = fh.readline()
        if line.startswith( "#!/usr/bin/env python" ):
            print 'python'
            args = []
            while True:
                line = fh.readline()
                if not line:
                    break
                line = line.strip()
                if 'argparse.ArgumentParser' in line:
                    args.append( line )
                    while True:
                        line = fh.readline()
                        if not line:
                            break
                        line = line.strip()
                        if 

                if line.startswith( 'parser' ):
                    args.append( line )
            print 'args', args
            assert 'description' in args[0], args[0]
        else:
            print line
    '''

if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument('--r_file_name', required=False, help="Provide path of a R file... ")
    parser.add_argument('--output_dir', required=True, default='out')
    args = parser.parse_args()
    main(args.r_file_name, args.output_dir)
