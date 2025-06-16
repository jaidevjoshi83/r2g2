from tool_generator_anvio import *
import argparse
from RScriptSupport import edit_r_script, json_to_python
import subprocess
import tempfile
import os
import shutil
from r_script_to_galaxy_wrapper import DEFAULT_TOOL_TYPE, TOOL_TEMPLATE, FakeArg, format_help, galaxy_tool_citation, Template



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

    test = open("./test.py", "w")

    input = python_code_as_string

    test.write(input)

    test.close()
    print(input)


    #unknown_metavar = []
    params = {}
    for param_name, param_tup in []:#list(anvio.D.items()):
        arguments, param_dict = param_tup
        arg_long = ''
        arg_short = ''
        for arg in arguments:
            if arg.startswith( '--' ):
                arg_long = arg
            else:
                arg_short = arg

        param = get_parameter( param_name, arg_short, arg_long, param_dict )

    
    # with open('../test_r_scripts/new.r') as fh:
    # input = fh.read()
    # print(filename, end=' ')
    param_name = 'parser'

    arg_groups = []

    # print(input)

    # if 'parent_parser' in input:
    #     #print('FIXME: skipping parent_parser')
    #     #continue
    #     # print("OKOKOKOKO")
    parser_name = 'parent_parser'

    # if input.startswith( "#!/usr/bin/env python" ):
        
    if "if __name__ == '__main__':" in input:
        input = input.replace( "if __name__ == '__main__':", "def blankenberg_parsing(parent_locals):\n    globals().update(parent_locals)", 1)
    elif 'if __name__ == "__main__":' in input:
        input = input.replace('if __name__ == "__main__":', "def blankenberg_parsing(parent_locals):\n    globals().update(parent_locals)", 1)
    if True:
        input = input.replace( "argparse.ArgumentParser", "FakeArg")

        inp_list = input.split( '\n' )
        for i, line in enumerate( inp_list ):
            if '%s.parse_args()' % (parser_name) in line:
                indent = len(line) - len( line.lstrip( ' ' ) )
                inp_list[i] = " " * indent + "return %s" % (parser_name) #"return parser.parse_args()"
            if 'anvio.get_args(%s)' % (parser_name) in line:
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
        print(output)

        __provides__ = [] # Reset provides since it is not always declared
        local_dict={}
        global_dict={}
        #global blankenberg_parameters
        #blankenberg_parameters = [None]
        #blankenberg_parameters = None
        local_dict = {}

        print(output)
        exec( output, globals(), local_dict)
        blankenberg_parameters = local_dict.get('blankenberg_parameters')

        print('blankenberg_parameters', blankenberg_parameters)
        print(dir( blankenberg_parameters ))
        print('desc', blankenberg_parameters.description)
                    
        #for a in dir( blankenberg_parameters ):
        #    print '~', a, getattr( blankenberg_parameters, a )
        #usage = blankenberg_parameters.format_help()
        #print 'usage', usage
        print('_blankenberg_args', blankenberg_parameters._blankenberg_args)
        #print 'by name', blankenberg_parameters.blankenberg_params_by_name( params )
        print('blankenberg_get_params', blankenberg_parameters.blankenberg_get_params( params ))

        print( '__provides__ %s' % __provides__)
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

        #print '__version__', __version__
        #print '__name__', __name__
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
        print('template_dict', template_dict)
        tool_xml = Template(TOOL_TEMPLATE).render( **template_dict )
        print('tool_xml', tool_xml)
        with open( os.path.join (write_dir, "%s.xml" % filename ), 'w') as out:
            out.write(tool_xml)
            xml_count += 1

                #sys.exit()
    else:
        print('no parse!')
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

#print 'unknown_metavar', unknown_metavar
#print 'anvio.D len', len(anvio.D)
#print 'metavar len', len(unknown_metavar)
    
if __name__ == '__main__':
    #parser = argparse_original.ArgumentParser(description='Create Galaxy Anvio tools.')
    #parser.add_argument('--plink-version', dest='plink_version', default='v1.90b4',
    #                    help='Version for folder input')

    #args = parser.parse_args()
    #main(args.plink_version)
    main('../test_r_scripts/fake_arg_subgroup.r','out')





    #     params[param_name] = param
    #     print (params)
    # outpath = os.path.join( os.curdir, 'output' )
    # if not os.path.exists( outpath ):
    #     os.mkdir( outpath )


# if __name__=='__main__':
#     main()