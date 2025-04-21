import re
import xml.etree.ElementTree as ET
import argparse as argparse_original
import json
import argparse
import fake_argparser

#Deprecated
def return_all_available_options_in_r_argparse():

    '''
    Parameter	Default Value	Description
    name	Required	Argument flag (e.g., --config). Needs to be set manually.
    dest	Same as name	Variable name in the args object. If not provided, it defaults to the argument name.
    type	"character"	If unspecified, values are treated as character strings.
    nargs	1 (single value)	Accepts a single value by default.
    action	"store"	Stores the argument's value.
    default	NULL	If not set, no default value is assigned.
    required	FALSE	Arguments are optional unless explicitly marked as TRUE.
    help	"" (empty string)	No help description unless manually added.
    metavar	NULL	Uses the argument name in help messages if not explicitly set.
    choices	NULL	If not specified, any value is allowed.
    append	FALSE	Does not append values to a list unless explicitly set.
    constant	NULL	Only used when action = "store_const". No default value.
    store_missing_action	"store"	Controls behavior when the argument is missing. Defaults to "store".
    arg_group	NULL	Argument does not belong to a group unless explicitly assigned.
    '''
        
    return {
        "name": "Argument name (e.g., --config)",
        "dest": "Variable name in args object",
        "type": "Expected data type (character, integer, double, logical)",
        "nargs": "Number of values (e.g., +, *, ?, or a specific number)",
        "action": "Defines how the argument behaves (e.g., store, store_true)",
        "default": "Default value if the argument is not provided",
        "required": "Whether the argument is mandatory (True/False)",
        "help": "Description shown in --help output",
        "metavar": "Name displayed in help message",
        "choices": "Restricts valid values to a predefined set",
        "append": "Whether to append values to a list (True/False)",
        "constant": "Value assigned if action=store_const",
        "store_missing_action": "Controls behavior when argument is missing",
        "arg_group": "Adds argument to a specific argument group"
    }

#Deprecated
def readFile(r_script_path):
    with open(r_script_path) as rScript:
        return rScript.read()
#Deprecated
def extract_argument_lines(r_script_text):
    #regex Used to find all argument definitions
    pattern = r'parser\$add_argument\(.*?\)(?=\s*$|\s*parser|\s*#|\s*args)'
    
    # re.DOTALL flag makes the dot match newlines as well
    arguments = re.findall(pattern, r_script_text, re.DOTALL | re.MULTILINE)
    
    # Clean up the matches by removing extra whitespace
    cleaned_arguments = []
    for arg in arguments:
        cleaned_arg = re.sub(r'\s+', ' ', arg.strip())
        cleaned_arguments.append(cleaned_arg)
    
    return cleaned_arguments
#Deprecated
def extract_inner_args(parser_line):
    # Pattern to match content between parser$add_argument( and the closing )
    pattern = r'parser\$add_argument\((.*)\)'
    match = re.search(pattern, parser_line)
    
    if match:
        return match.group(1)
    else:
        return "No arguments found"
#Deprecated
def returnArgLines():

    raw_r = readFile()
    with open('test.r' ) as out:
        raw_r  = out.read()
    # Extract and print the argument lines
        argument_lines = extract_argument_lines(raw_r)

    arg_lines = []

    for i, line in enumerate(argument_lines, 1):
        arg_lines.append(extract_inner_args(line))
#Deprecated
def c(*args):
    return list(args) 
#Deprecated
def clean_formating(text):
    updated_text = re.sub(r'"\%\((.*?)\)s"\]', ']', text)
    return updated_text
#Deprecated
def convert_R_args_to_dictionary(*args, **kwargs):
    return [args, kwargs]
#Deprecated
def returnCleanedParams(r_script_path):

    cleaned_arguments = []
    param_list = []

    raw_lines = readFile(r_script_path)
    raw_arguments = extract_argument_lines(raw_lines)

    for i in raw_arguments:
        cleaned_arguments.append(extract_inner_args(i))

    for n, i in enumerate (cleaned_arguments):
        i = i.replace('TRUE', 'True')
        param_list.append(eval('convert_R_args_to_dictionary('+i+')'))

    # for p in param_list:
    #     print(p)

    return param_list
#Deprecated
def TypeCheck(s):
    if isinstance(s, bool):
        return 'boolean'
    elif isinstance(s, str):
        try:
            if isinstance(eval(s), bool):
                return 'boolean'
            if isinstance(eval(s), int):
                return 'integer'
            if isinstance(eval(s), float):
                return 'float'
        except:
            return 'text'

#Deprecated
def guess_the_type(raw_dict):
    type_dict = {'integer':'integer', 'double':'float', 'character': 'text', 'logical':'boolean'}
    if "type" in raw_dict.keys():
        if raw_dict['type']:
            return str(type_dict[raw_dict['type']])
    elif 'default' in raw_dict.keys():
        return TypeCheck( raw_dict['default'])
        
    else:
        return 'unknown'
#Deprecated
def create_galaxy_params(raw_param):
    params_dict = {

        'name' : {'short':None, 'long':None},
        'label' : None,
        'help' : None,
        'value': None,
        'multiple': None,
        'type' : None,
        'optional' : None,
        'choices' : None,
        'select' : False
    }
    
    if isinstance(raw_param[0], tuple):
        for i in raw_param[0]:
            if bool(re.match(r"^--[^-]", i)):
               params_dict['name']['long'] = i.strip('--')
            elif bool(re.match(r"^-[^-]", i)):  # Changed to elif
               params_dict['name']['short'] = i.strip('-')
    
    if isinstance(raw_param[1], dict):
         params_dict['type'] = guess_the_type(raw_param[1])

         if 'help' in raw_param[1].keys():
             params_dict['help'] = raw_param[1]['help']
         else:
             params_dict['help'] = ''

         if 'required' in raw_param[1].keys():
             params_dict['optional'] = str(raw_param[1]['required']).lower()
         else:
             params_dict['optional'] = 'false'

         if 'default' in raw_param[1].keys():
             params_dict['value'] = str(raw_param[1]['default'])
         else:
             params_dict['optional'] = 'false'

         if 'choices' in raw_param[1].keys():
             params_dict['choices'] = raw_param[1]['choices']
             params_dict['select'] = True
         else:
             params_dict['choices'] = None

    return params_dict

import xml.etree.ElementTree as ET

#Deprecated
def generate_select(param_dict):
    
    select = """<param name="%(name)s" type="%(type)s" label="%(label)s" argument="%(label)s" help="%(help)s">
%(options)s
</param>"""
    
    l = ['csv', 'tsv', 'json']
    
    options = '\n'.join('      <option value="%s">%s</option>'%(i, i) for i in param_dict['choices'])
    param_dict['options'] = options
    select_template = select % param_dict
    
    # returns the formatted select string
    return select_template

#Deprecated
def generate_simple_command_line_options(galaxy_inputs, r_script):

    command_line = '''<![CDATA[ 
                    Rscript '$__tool_directory__/%(r_script)s'             %(temp)s 
                ]]>'''

    temp = {
        'temp': None,
        'r_script':r_script 
    }

    string  = '''
                        #if $%s
                            %s '$%s'
                        #end if''' 

    temp['temp'] = "\n".join([string%(data['name']['long'] if data['name']['long'] is not None else data['name']['short'], data['argument'], data['name']['long'] if data['name']['long'] is not None else data['name']['short']) for data in galaxy_inputs])
    return command_line%temp

#Deprecated
def add_repeat_for_action_append():
    '''
    library(argparse)
    parser <- ArgumentParser(description = "Example of append argument")
    parser$add_argument("--items", action = "append", help = "Add multiple items to a list")

    args <- parser$parse_args()

    print(args$items)

    CMD Rscript script.R --items apple --items banana --items cherry
    '''

    temp = ''

    return 

#Deprecated
def add_conditional_templated_for_groups():

    '''
    library(argparse)

    # Create the argument parser
    parser <- ArgumentParser(description = "Example of argument groups")

    # Create an argument group for input arguments
    input_group <- parser$add_argument_group("Input Arguments")
    input_group$add_argument("--input_file", required = TRUE, help = "Path to input file")
    input_group$add_argument("--format", choices = c("csv", "json", "xml"), help = "Input file format")

    # Create an argument group for processing arguments
    processing_group <- parser$add_argument_group("Processing Options")
    processing_group$add_argument("--threads", type = "integer", default = 1, help = "Number of processing threads")
    processing_group$add_argument("--verbose", action = "store_true", help = "Enable verbose logging")

    # Parse the arguments
    args <- parser$parse_args()

    # Print parsed arguments
    print(args)
    '''
    temp = ""

    return 

#Deprecated
def add_condiational_template_fo_mutually_exclusive_groups():

    '''
    library(argparse)
    parser <- ArgumentParser(description = "Mutually Exclusive Group Example")

    # Create mutually exclusive group
    group <- parser$add_mutually_exclusive_group(required = TRUE)
    group$add_argument("--verbose", action = "store_true", help = "Enable verbose output")
    group$add_argument("--quiet", action = "store_true", help = "Suppress all output")

    args <- parser$parse_args()
    print(args)
    --input 
    '''
    temp = ""

    return 

import json




class FakeArg( argparse_original.ArgumentParser ):
    def __init__( self, *args, **kwd ):
        print('init')

        self._blankenberg_args = []
        super( FakeArg, self ).__init__( *args, **kwd )

    def add_argument( self, *args, **kwd ):
        # print('add argument')
        print("##############################, 1248")
        print('args', args)
        print('kwd', kwd)
        print("############################## 1251")
        self._blankenberg_args.append( ( args, kwd ) )
        super( FakeArg, self ).add_argument( *args, **kwd )

    #def add_argument_group( self, *args, **kwd ):
    #    #cheat and return self, no groups!
    #    print 'arg group'
    #    print 'args', args
    #    print 'kwd', kwd
    #    return self

    def blankenberg_params_by_name( self, params ):
        rval = {}#odict()
        for args in self._blankenberg_args:
            name = ''
            for arg in args[0]:
                if arg.startswith( '--' ):
                    name = arg[2:]
                elif arg.startswith( '-'):
                    if not name:
                        name = arg[1]
                else:
                    name = arg
            rval[name] = args[1]
            if 'metavar' not in args[1]:
                print('no metavar', name)
        return rval
    def blankenberg_get_params( self, params ):
        rval = []
        # print('blankenberg_get_params params', params)
        for args in self._blankenberg_args:
            name = ''
            arg_short = ''
            arg_long = ''
            for arg in args[0]:
                if arg.startswith( '--' ):
                    name = arg[2:]
                    arg_long = arg
                elif arg.startswith( '-' ):
                    arg_short = arg
                    if not name:
                        name = arg[1:]
                elif not name:
                    name = arg
            param = None
            if name in params:
                print("%s (name) is in params" % (name) )
                param = params[name]
            #if 'metavar' in args[1]:
                #if args[1]['metavar'] in params:
            #        param = params[args[1]['metavar']]
            if param is None:
                if name in PARAMETER_BY_NAME:
                    param = PARAMETER_BY_NAME[name]( name, arg_short, arg_long, args[1] )
            if param is None:
                print("Param is None")
                metavar = args[1].get( 'metavar', None )
                # print("asdf metavar",args[1],metavar)
                if metavar and metavar in PARAMETER_BY_METAVAR:
                    param = PARAMETER_BY_METAVAR[metavar]( name, arg_short, arg_long, args[1] )
            if param is None:
                # print('no meta_var, using default', name, args[1])
                #param = DEFAULT_PARAMETER( name, arg_short, arg_long, args[1] )
                param = get_parameter( name, arg_short, arg_long, args[1] )

            #print 'before copy', param.name, type(param)
            param = param.copy( name=name, arg_short=arg_short, arg_long=arg_long, info_dict=args[1] )
            #print 'after copy', type(param)
            rval.append(param)
        return rval
    def blankenberg_to_cmd_line( self, params, filename=None ):
        pre_cmd = []
        post_cmd = []
        rval = filename or self.prog
        for param in self.blankenberg_get_params( params ):
            if param.name not in SKIP_PARAMETER_NAMES:
                pre = param.get_pre_cmd_line()
                if pre:
                    pre_cmd.append( pre )
                post = param.get_post_cmd_line()
                if post:
                    post_cmd.append( post )
                cmd = param.to_cmd_line()
                if cmd:
                    rval = "%s\n%s" % ( rval, cmd )
        pre_cmd = "\n && \n".join( pre_cmd )
        post_cmd = "\n && \n".join( post_cmd )
        if pre_cmd:
            rval = "%s\n &&\n %s" % ( pre_cmd, rval )
        rval = "%s\n&> '${GALAXY_ANVIO_LOG}'\n" % (rval)
        if post_cmd:
            rval = "%s\n &&\n %s" % ( rval, post_cmd )
        return rval #+ "\n && \nls -lahR" #Debug with showing directory listing in stdout
    def blankenberg_to_inputs( self, params ):
        rval = []
        for param in self.blankenberg_get_params( params ):
            if param.name not in SKIP_PARAMETER_NAMES and param.is_input:
                inp_xml = param.to_xml_param()
                if inp_xml:
                    rval.append( inp_xml )
        return rval
    def blankenberg_to_outputs( self, params ):
        rval = []
        for param in self.blankenberg_get_params( params ):
            if param.name not in SKIP_PARAMETER_NAMES and param.is_output:
                rval.append( param.to_xml_output() )
        rval.append( GALAXY_ANVIO_LOG_XML )
        return rval

def extract_arguments(arg_json):
    # Open and load the JSON file

    file = open('./test_arg_file.py', 'w')

    with open(arg_json, 'r') as f:
        data = json.load(f)

    return """def blankenberg_parsing(parent_locals):
    __description__ = "test"
    globals().update(parent_locals)
    parser = FakeArg(description=__description__)
    %s\n%s     """%("\n    ".join(data),'blankenberg_parameters = blankenberg_parsing(dict(locals()))\nprint(blankenberg_parameters )' )


def main():

    extracted_args_string = extract_arguments('./params_output_out.json')
    local_dict = {}
    exec( extracted_args_string, globals(), local_dict)

    print(local_dict)


    blankenberg_parameters = local_dict.get('blankenberg_parameters')

    print(blankenberg_parameters)


if __name__=='__main__':


    main()
