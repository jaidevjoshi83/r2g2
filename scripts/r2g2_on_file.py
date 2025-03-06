#!/usr/bin/env python
# -*- coding: utf-8

"""A script to convert R library functions to Galaxy Tools."""

import argparse
import os
import string
import re

import rpy2.robjects.packages as rpackages
from rpy2 import robjects
from rpy2.robjects.functions import DocumentedSTFunction
from rpy2.robjects.help import pages
from rpy2.robjects.vectors import BoolVector, IntVector, FloatVector, StrVector, ListVector
from xml.sax.saxutils import quoteattr
from rpy2.rinterface import str_typeint
from RScriptSupport import returnCleanedParams

package_name = None
package_version = None
r_name = None
galaxy_tool_version = None

def extract_r_script_arguments(r_script):
    pattern = re.compile(r'(parser\$add_argument\(.*?(?:\n\s+.*?)*\))', re.DOTALL)
    # Find all matches
    matches = pattern.findall(r_script)
    # Clean up the matches by removing newline characters and extra spaces
    cleaned_matches = [' '.join(match.split()) for match in matches]

    # # Print the result
    # for match in cleaned_matches:
    #     print(match)

    return cleaned_matches


tool_xml ='''<tool id="%(id)s" name="%(name)s" version="@VERSION@-%(galaxy_tool_version)s">
                <description><![CDATA[%(description)s]]></description>
                <macros>
                    <import>%(r_name)s_macros.xml</import>
                </macros>
                <expand macro="requirements" />
                <expand macro="stdio" />
                <expand macro="version_command" />
                <command><![CDATA[
                    #if "output_r_script" in str( $include_outputs ).split( "," ):
                        cp '${%(id_underscore)s_script}' '${output_r_script}' &&
                    #end if
                    Rscript '${%(id_underscore)s_script}'
                ]]>
                </command>
                <configfiles>
                     <configfile name="%(id_underscore)s_script"><![CDATA[#!/usr/bin/env RScript
            %(rscript_content)s
                ]]>
                     </configfile>
                </configfiles>
                <inputs>
            %(inputs)s
                    <param name="include_outputs" type="select" multiple="True" label="Datasets to create">
                        <option value="output_r_dataset" selected="true">Results in RDS format</option>
                        <option value="output_r_script" selected="false">R script</option>
                    </param>
                </inputs>
                <outputs>
                    <data format="rds" name="output_r_dataset" label="${tool.name} on ${on_string} (RDS)">
                        <filter>"output_r_dataset" in include_outputs</filter>
                    </data>
                    <data format="txt" name="output_r_script" label="${tool.name} on ${on_string} (Rscript)">
                        <filter>"output_r_script" in include_outputs</filter>
                    </data>%(outputs)s
                </outputs>
                <help><![CDATA[
            Automatically Parsed R Help
            ===========================

            %(help_rst)s
                ]]></help>
            <tests>
                <test>
                </test>
            </tests>
            <citations>
            </citations>
            </tool>
            <!-- Created automatically using R2-G2: https://github.com/blankenberg/r2g2 -->
          '''

#input_dataset = '''<param name="input_%(name)s" type="data" format="rds" label=%(label)s help=%(help)s/>'''
input_dataset = '''<param name="%(name)s" type="data" format="rds" label=%(label)s help=%(help)s/>'''
input_text = '''<param name="%(name)s" type="text" value=%(value)s label=%(label)s help=%(help)s/>'''
input_boolean = '''<param name="%(name)s" type="boolean" truevalue="TRUE" falsevalue="FALSE" checked=%(value)s label=%(label)s help=%(help)s/>'''
input_integer = '''<param name="%(name)s" type="integer" value=%(value)s label=%(label)s help=%(help)s/>'''
input_float = '''<param name="%(name)s" type="float" value=%(value)s label=%(label)s help=%(help)s/>'''
input_select = '''<param name="%(name)s" type="text" value=%(value)s label=%(label)s help=%(help)s/><!-- Should be select? -->'''

#NULL
INPUT_NOT_DETERMINED_PASS_DICT = {}
for select in ['dataset_selected', 'text_selected', 'integer_selected', 'float_selected', 'boolean_selected', 'skip_selected', 'NULL_selected', 'NA_selected' ]:
   INPUT_NOT_DETERMINED_PASS_DICT[select] = "%(" + select + ")s" 


input_not_determined = '''
        <conditional name="%(name)s_type">
            <param name="%(name)s_type_selector" type="select" label="%(name)s: type of input">
                <option value="dataset" selected="%(dataset_selected)s">Dataset</option>
                <option value="text" selected="%(text_selected)s">Text</option>
                <option value="integer" selected="%(integer_selected)s">Integer</option>
                <option value="float" selected="%(float_selected)s">Float</option>
                <option value="boolean" selected="%(boolean_selected)s">Boolean</option>
                <option value="skip" selected="%(skip_selected)s">Skip</option>
                <option value="NULL" selected="%(NULL_selected)s">NULL</option>
                <option value="NA" selected="%(NA_selected)s">NA</option>
            </param>
            <when value="dataset">
                %(input_dataset)s
            </when>
            <when value="text">
                %(input_text)s
            </when>
            <when value="integer">
                %(input_integer)s
            </when>
            <when value="float">
                %(input_float)s
            </when>
            <when value="boolean">
                %(input_boolean)s
            </when>
            <when value="skip">
                <!-- Do nothing here -->
            </when>
            <when value="NULL">
                <!-- Do nothing here -->
            </when>
            <when value="NA">
                <!-- Do nothing here -->
            </when>
        </conditional>
''' % dict(
      list(INPUT_NOT_DETERMINED_PASS_DICT.items()) +
      list(dict(
           name = "%(name)s",
           input_dataset = input_dataset,
           input_text = input_text,
           input_boolean = input_boolean,
           input_integer = input_integer,
           input_float = input_float,
           input_select = input_select
           ).items())
      )
INPUT_NOT_DETERMINED_DICT = {}

for select in ['dataset_selected', 'text_selected', 'integer_selected', 'float_selected', 'boolean_selected', 'skip_selected', 'NULL_selected', 'NA_selected' ]:
   INPUT_NOT_DETERMINED_DICT[select] = False 

#need to add select to above?

optional_input = '''
        <conditional name="%(name)s_type">
            <param name="%(name)s_type_selector" type="boolean" truevalue="True" falsevalue="False" checked="True" label="%(name)s: Provide value"/>
            <when value="True">
                %(input_template)s
            </when>
            <when value="False">
                <!-- Do nothing here -->
            </when>
        </conditional>
'''


optional_input_dataset = optional_input % dict(
                                               name = "%(name)s",
                                               input_template = input_dataset
                                               )
optional_input_text = optional_input % dict(
                                               name = "%(name)s",
                                               input_template = input_text
                                               )
optional_input_boolean = optional_input % dict(
                                               name = "%(name)s",
                                               input_template = input_boolean
                                               )
optional_input_integer = optional_input % dict(
                                               name = "%(name)s",
                                               input_template = input_integer
                                               )
optional_input_float = optional_input % dict(
                                               name = "%(name)s",
                                               input_template = input_float
                                               )
optional_input_select = optional_input % dict(
                                               name = "%(name)s",
                                               input_template = input_select
                                               )
optional_input_not_determined = optional_input % dict( 
                                                       list(INPUT_NOT_DETERMINED_PASS_DICT.items()) +
                                                       list(dict(
                                                            name = "%(name)s",
                                                            input_template = input_not_determined
                                                  ).items()) )


ellipsis_input = '''
        <repeat name="___ellipsis___" title="Additional %(name)s">
            <param name="%(name)s_name" type="text" value="" label="Name for argument" help=""/>
            %(input_not_determined)s
        </repeat>
''' % dict( input_not_determined=input_not_determined, name='argument' ) % dict( list(INPUT_NOT_DETERMINED_PASS_DICT.items()) + list(dict( name='argument', label='"Argument value"', help='""', value='""'  ).items()) )

def generate_macro_xml():
    macro_xml = '''<macros>
    <xml name="requirements">
        <requirements>
            <requirement type="package" version="%(package_version)s">%(package_name)s</requirement>
            <yield />
        </requirements>
    </xml>

    <xml name="version_command">
        <version_command><![CDATA[Rscript -e 'suppressMessages(library(%(r_name)s));cat(toString(packageVersion("%(r_name)s")))' ]]></version_command>
    </xml>

    <xml name="stdio">
        <stdio>
            <exit_code range="1:" />
            <exit_code range=":-1" />
        </stdio>
    </xml>

    <xml name="params_load_tabular_file">
        <param name="input_abundance" type="data" format="tabular" label="File with abundance values for community" help="Rows are samples; columns are species/phyla/community classifier"/>
        <param name="species_column" label="Group name column" type="data_column" data_ref="input_abundance" value="6" help="Species, phylum, etc"/>
        <param name="sample_columns" label="Sample count columns" type="data_column" multiple="True" value="2" data_ref="input_abundance" help="Select each column that contains counts"/>
        <param name="header" type="boolean" truevalue="TRUE" falsevalue="FALSE" checked="False" label="Input has a header line"/>
    </xml>

    <token name="@RSCRIPT_LOAD_TABULAR_FILE@"><![CDATA[
#set $int_species_column = int( str( $species_column ) )
#set $fixed_sample_columns = []
#for $sample_col in map( int, str( $sample_columns ).split( "," ) ):
#assert $sample_col != $int_species_column, "Sample label column and sample count columns must not be the same."
#silent $fixed_sample_columns.append( str( $sample_col if $sample_col < $int_species_column else $sample_col-1 ) )
#end for
options(bitmapType='cairo')## No X11, so we'll use cairo
library(%(r_name)s)
input_abundance <- read.table("${input_abundance}", sep="\t", row.names=${ species_column }, header=${header} )
input_abundance <- t( input_abundance[ c( ${ ",".join( $fixed_sample_columns ) } )] )
]]>
    </token>

    <token name="@VERSION@">%(package_version)s</token>

</macros>''' % dict( package_name=package_name, package_version=package_version, r_name=r_name, galaxy_tool_version=galaxy_tool_version )
    return macro_xml

CONFIG_SPLIT_DESIRED_OUTPUTS = '''#set $include_files = str( $include_outputs ).split( "," )'''

SAVE_R_OBJECT_TEXT = '''
#if "output_r_dataset" in $include_files:
    saveRDS(rval, file = "${output_r_dataset}", ascii = FALSE, version = 2, compress = TRUE )
#end if
'''

def generate_LOAD_MATRIX_TOOL_XML():
    LOAD_MATRIX_TOOL_XML ='''<tool id="r_load_matrix" name="Load Tabular Data into R" version="%(galaxy_tool_version)s">
    <description>
        as a Matrix / Dataframe
    </description>
    <macros>
        <import>%(r_name)s_macros.xml</import>
    </macros>
    <expand macro="requirements" />
    <expand macro="stdio" />
    <expand macro="version_command" />
    <command><![CDATA[
        #if "output_r_script" in str( $include_outputs ).split( "," ):
            cp '${r_load_script}' '${output_r_script}' &&
        #end if
        Rscript '${r_load_script}'
    ]]>
    </command>
    <configfiles>
        <configfile name="r_load_script"><![CDATA[
@RSCRIPT_LOAD_TABULAR_FILE@
saveRDS(input_abundance, file = "${output_r_dataset}", ascii = FALSE, version = 2, compress = TRUE )


    ]]>
        </configfile>
    </configfiles>
    <inputs>
        <expand macro="params_load_tabular_file" />
        <param name="include_outputs" type="select" multiple="True" label="Datasets to create">
            <option value="output_r_script" selected="false">R script</option>
        </param>
    </inputs>
    <outputs>
        <data format="rds" name="output_r_dataset" label="${tool.name} on ${on_string} (RDS)">
        </data>
        <data format="txt" name="output_r_script" label="${tool.name} on ${on_string} (Rscript)">
            <filter>"output_r_script" in include_outputs</filter>
        </data>
    </outputs>
    <tests>
        <test>
            <param name="input_abundance" ftype="tabular" value="%(r_name)s_in.tabular"/>
            <param name="include_outputs" value="output_r_script"/>
            <output name="output_r_dataset" ftype="rds" file="%(r_name)s_output_r_script.txt" />
            <output name="output_r_script" ftype="tabular" file="%(r_name)s_output_r_script.txt" />
        </test>
    </tests>
    <help>
        <![CDATA[
        
        Loads Tabular file into an R object
        ]]>
    </help>
    <citations>
    </citations>
</tool>''' % dict( package_name=package_name, package_version=package_version, r_name=r_name, galaxy_tool_version=galaxy_tool_version )
    return LOAD_MATRIX_TOOL_XML

SAFE_CHARS = list( x for x in string.ascii_letters + string.digits + '_' )
def simplify_text( text ):
    return ''.join( [ x if x in SAFE_CHARS else '_' for x in text ] )
    

def to_docstring( page, section_names = None):
    """ section_names: list of section names to consider. If None
    all sections are used.
    Returns a string that can be used as a Python docstring. """
    
    if section_names is None:
        section_names = list(page.sections.keys())
        
    def walk( s, tree, depth=0):
        if not isinstance(tree, str):
            for elt in tree:
                walk(s, elt, depth=depth+1)
        else:
            s.append(tree)
            s.append(' ')

    rval = []
    for name in section_names:
        rval.append(name.title())
        rval.append(os.linesep)
        rval.append('-' * len(name))
        rval.append(os.linesep)
        rval.append(os.linesep)
        rval.append( '::' )
        rval.append(os.linesep)
        s = []
        walk(s, page.sections[name], depth=1)
        
        rval.append( '  %s  ' % ( os.linesep ) )
        rval.append( "".join( s ).replace( os.linesep, '%s  ' % ( os.linesep ) ) )
        rval.append(os.linesep)
        rval.append(os.linesep)
    return ''.join(rval).strip()


def unroll_vector_to_text( section ):
        
    def walk( s, tree, depth=0):
        if not isinstance(tree, str):
            for elt in tree:
                walk(s, elt, depth=depth+1)
        else:
            s.append(tree)
            s.append(' ')

    rval = []
    walk(rval, section, depth=1)
    return ''.join(rval).strip()

robjects.r('''

    ctr <- 0
    dlBrowser <- function( url ) {
    print( paste( "Fetching", url) )
    #Sys.sleep(5)
    download.file( url, destfile = paste0( "./html/",ctr,".html"), method="wget" )
    ctr <- ctr + 1
    ctr
        }
options( browser= dlBrowser)
''')

parser = argparse.ArgumentParser()
parser.add_argument("--name", help="Package Name", required=False )
parser.add_argument("--toolName", help="toolName", required=False, default=False )
parser.add_argument("--toolId", help="toolId", required=False )
parser.add_argument("--rScript", help="Rscript", required=False,default=False )
parser.add_argument("--package_name", help="[Conda] Package Name", default=None)
parser.add_argument("--package_version", help="[Conda] Package Version", default=None)
parser.add_argument("--out", help="Output directory", default='out')
parser.add_argument("--create_load_matrix_tool", help="Output a tool that will create an RDS from a tabular matrix", action='store_true')
parser.add_argument("--galaxy_tool_version", help="Additional Galaxy Tool Version", default='0.0.1')

args = parser.parse_args()

r_name = args.name
if r_name:
    package_name = args.package_name or r_name
    #utils = rpackages.importr("utils")
    package_importr = rpackages.importr(r_name)
    package_version = args.package_version or package_importr.__version__
    galaxy_tool_version = args.galaxy_tool_version

package_dict = {}
skipped = 0

try:
    os.makedirs( args.out )
except os.error:
    pass

with open( os.path.join( args.out, "%s_macros.xml" % ( r_name ) ), 'w+' ) as out:
    out.write( generate_macro_xml() )

if args.create_load_matrix_tool:
    with open( os.path.join( args.out, "r_load_matrix.xml" ), 'w+' ) as out:
        out.write( generate_LOAD_MATRIX_TOOL_XML() )

# if  args.rScript:
#     xml_dict = {
#             'package_name': args.name,
#             'id': "%s_%s" % ( args.name, args.name ),
#             'galaxy_tool_version': '0.1.0',
#             'name': "%s" % ( args.name ),
#             'description': '',
#             'inputs': '',
#             'rscript_content': '',
#             'outputs': '',
#             'help_rst': '',
#             'r_name': args.name,
#             }
#     xml_dict['id_underscore'] = simplify_text( xml_dict['id'] )
#     xml_dict['id'] = simplify_text( xml_dict['id'] ) # ToolShed doesn't like e.g. '-'' in ids
#     xml_dict['help_rst'] = "Test Help Page"

#     for i in returnCleanedParams('test.r'):
#         print(i)

# else:
    # for j, name in enumerate(dir(package_importr)):

    # user_input = input("Enter something: ")

# try:

rname = 'test_tool'

xml_dict = {
            'package_name': package_name,
            'id': "%s_%s" % ( package_name, rname ),
            'galaxy_tool_version': galaxy_tool_version,
            'name': "%s" % ( rname ),
            'description': '',
            'inputs': '',
            'rscript_content': '',
            'outputs': '',
            'help_rst': '',
            'r_name': r_name,
            }
xml_dict['id_underscore'] = simplify_text( xml_dict['id'] )
xml_dict['id'] = simplify_text( xml_dict['id'] ) # ToolShed doesn't like e.g. '-'' in ids

help = pages( rname )

inputs = []
input_names = []
input_file_name = None

for i in returnCleanedParams('test.r'):
    print(i[0])

for i, (formal_name, formal_value ) in enumerate( package_obj.formals().items() ):

    default_value = ''
    input_type = 'text'
    input_dict = INPUT_NOT_DETERMINED_DICT.copy()
    input_dict.update( {
                    'name': simplify_text( formal_name ),
                    'label': quoteattr( formal_name ),
                    'help':quoteattr( str( formal_value ).strip() ),
                    'value': '',
                    'multiple': False,
                    } )
    
    input_template = optional_input_text
    use_quotes = True
    try:
        value_name, value_value = list( formal_value.items() )[0]
        
        r_type = str_typeint( value_value.typeof )
        if r_type == 'INTSXP':
            input_type = 'integer'
            default_value = str( value_value[0] )
            input_template = optional_input_integer
            use_quotes = False
            input_dict[ 'integer_selected' ] = True
            input_type = 'not_determined'
        elif r_type == 'LGLSXP': #this seems to have caught NA...FIXME
            input_type = 'boolean'
            default_value = str( value_value[0] )
            input_template = optional_input_boolean
            use_quotes = False
            if default_value == 'NULL':
                input_dict[ 'NULL_selected' ] = True
            elif default_value == 'NA':
                input_dict[ 'NA_selected' ] = True
            else:
                input_dict[ 'boolean_selected' ] = True
            input_type = 'not_determined'
        elif r_type == 'REALSXP':
            input_type = 'float'
            default_value = str( value_value[0] )
            input_template = optional_input_float
            use_quotes = False
            input_dict[ 'float_selected' ] = True
            input_type = 'not_determined'
        elif r_type == 'STRSXP':
            input_type = 'text'
            default_value = str( value_value[0] )
            input_template = optional_input_text
            input_dict[ 'text_selected' ] = True
            input_type = 'not_determined'
        else:
            input_type = 'not_determined'
            input_template = optional_input_not_determined
            input_dict[ 'dataset_selected' ] = True
        
        length = len( list( value_value ) )
        input_dict['multiple'] = ( length > 1 )
    except Exception as e:
        print('Error getting input param info:')
        print(e)

    if input_type == 'dataset':
        input_template = optional_input_dataset
    elif input_type == 'boolean':
        default_value = str( ( default_value.strip().lower() == 'true' ) )
    
    input_dict['value'] = quoteattr( default_value )
    input_place_name = input_dict['name']
    
    #FIXME: change ... into repeat with conditional to allow providing any? type of input, with/without names?
    if formal_name in ['...']:
        print('has ... need to replace with a repeat and conditional')
        inputs.append( ellipsis_input % input_dict )
        input_names.append( ( '...', '___ellipsis___', 'ellipsis', False ) )
    else:
    #if formal_name not in ['...']:
        inputs.append( input_template % input_dict )
        input_names.append( ( formal_name, input_place_name, input_type, use_quotes ) )
    
xml_dict['inputs'] = "        %s" % ( "\n        ".join( inputs ) )    

xml_dict['rscript_content'] = '%s\nlibrary(%s)\n#set $___USE_COMMA___ = ""\nrval <- %s(' % ( CONFIG_SPLIT_DESIRED_OUTPUTS, r_name, rname )
for i, (inp_name, input_placeholder, input_type, use_quotes ) in enumerate( input_names ):
    if False: #not optional
    # treating everything as optional atm
        if input_type == 'dataset':
            xml_dict['rscript_content'] = '%s${___USE_COMMA___}\n#set $___USE_COMMA___ = ","\n%s = readRDS("${input_%s}")' % ( xml_dict['rscript_content'], inp_name, input_placeholder )
        elif input_type == 'not_determined':
            xml_dict['rscript_content'] = '''%s${___USE_COMMA___}
                                                #if str( $%s_type.%s_type_selector ) != 'skip':
                                                    #set $___USE_COMMA___ = ","\n
                                                    #if str( $%s_type.%s_type_selector ) == 'dataset':
                                                        %s = readRDS("${%s_type.%s}")
                                                    #elif str( $%s_type.%s_type_selector ) == 'text':
                                                        %s = "${ %s_type.%s }"
                                                    #elif str( $%s_type.%s_type_selector ) == 'integer':
                                                        %s = ${ %s_type.%s }
                                                    #elif str( $%s_type.%s_type_selector ) == 'float':
                                                        %s = ${ %s_type.%s }
                                                    #elif str( $%s_type.%s_type_selector ) == 'boolean':
                                                        %s = ${ %s_type.%s }
                                                    #elif str( $%s_type.%s_type_selector ) == 'select':
                                                        #raise ValueError( 'not implemented' )
                                                        %s = "${ %s_type.%s }"
                                                    #elif str( $%s_type.%s_type_selector ) == 'NULL':
                                                        %s = NULL
                                                    #end if
                                                #end if
                                                ''' % ( xml_dict['rscript_content'], 
                                                    input_placeholder, input_placeholder,
                                                    input_placeholder, input_placeholder,
                                                    inp_name, input_placeholder, input_placeholder,
                                                    input_placeholder, input_placeholder,
                                                    inp_name, input_placeholder, input_placeholder,
                                                    input_placeholder, input_placeholder,
                                                    inp_name, input_placeholder, input_placeholder,
                                                    input_placeholder, input_placeholder,
                                                    inp_name, input_placeholder, input_placeholder,
                                                    input_placeholder, input_placeholder,
                                                    inp_name, input_placeholder, input_placeholder,
                                                    input_placeholder, input_placeholder,
                                                    inp_name, input_placeholder, input_placeholder,
                                                    input_placeholder, input_placeholder,
                                                    inp_name,
                                                    )
        elif use_quotes:
            xml_dict['rscript_content'] = '%s${___USE_COMMA___}\n#set $___USE_COMMA___ = ","\n%s = "${ %s }"' % ( xml_dict['rscript_content'], inp_name, input_placeholder )
        else:
            xml_dict['rscript_content'] = '%s${___USE_COMMA___}\n#set $___USE_COMMA___ = ","\n%s = ${ %s }' % ( xml_dict['rscript_content'], inp_name, input_placeholder )
    else:
        # is optional
        if input_type == 'ellipsis':
            dict( name='argument'  )
            xml_dict['rscript_content'] = '''%s${___USE_COMMA___}
                                        #set $___USE_COMMA___ = ","
                                        #for eli in $___ellipsis___:
                                            #if str( $eli.argument_type.argument_type_selector ) != 'skip':
                                                    #set $___USE_COMMA___ = ","\n
                                                    #if str( $eli.argument_type.argument_type_selector ) == 'dataset':
                                                        ${eli.argument_name} = readRDS("${eli.argument_type.argument}")
                                                    #elif str( $eli.argument_type.argument_type_selector ) == 'text':
                                                        ${eli.argument_name} = "${eli.argument_type.argument}"
                                                    #elif str( $eli.argument_type.argument_type_selector ) == 'integer':
                                                        ${eli.argument_name} = ${eli.argument_type.argument}
                                                    #elif str( $eli.argument_type.argument_type_selector ) == 'float':
                                                        ${eli.argument_name} = ${eli.argument_type.argument}
                                                    #elif str( $eli.argument_type.argument_type_selector ) == 'boolean':
                                                        ${eli.argument_name} = ${eli.argument_type.argument}
                                                    #elif str( $eli.argument_type.argument_type_selector ) == 'select':
                                                        #raise ValueError( 'not implemented' )
                                                        ${eli.argument_name} = "${eli.argument_type.argument}"
                                                    #elif str( $eli.argument_type.argument_type_selector ) == 'NULL':
                                                        ${eli.argument_name} = NULL
                                                    #end if
                                                #end if
                                        #end for
                                        ''' % ( xml_dict['rscript_content'] )
        else:                                                                 
            xml_dict['rscript_content'] = '%s\n#if str( $%s_type.%s_type_selector ) == "True":\n' % ( xml_dict['rscript_content'], input_placeholder, input_placeholder )
            if input_type == 'dataset':
                xml_dict['rscript_content'] = '%s${___USE_COMMA___}\n#set $___USE_COMMA___ = ","\n%s = readRDS("${input_%s}")' % ( xml_dict['rscript_content'], inp_name, input_placeholder )
            elif input_type == 'not_determined':
                xml_dict['rscript_content'] = '''%s${___USE_COMMA___}
                                                    #if str( $%s_type.%s_type.%s_type_selector ) != 'skip':
                                                        #set $___USE_COMMA___ = ","\n
                                                        #if str( $%s_type.%s_type.%s_type_selector ) == 'dataset':
                                                            %s = readRDS("${%s_type.%s_type.%s}")
                                                        #elif str( $%s_type.%s_type.%s_type_selector ) == 'text':
                                                            %s = "${ %s_type.%s_type.%s }"
                                                        #elif str( $%s_type.%s_type.%s_type_selector ) == 'integer':
                                                            %s = ${ %s_type.%s_type.%s }
                                                        #elif str( $%s_type.%s_type.%s_type_selector ) == 'float':
                                                            %s = ${ %s_type.%s_type.%s }
                                                        #elif str( $%s_type.%s_type.%s_type_selector ) == 'boolean':
                                                            %s = ${ %s_type.%s_type.%s }
                                                        #elif str( $%s_type.%s_type.%s_type_selector ) == 'select':
                                                            #raise ValueError( 'not implemented' )
                                                            %s = "${ %s_type.%s_type.%s }"
                                                        #elif str( $%s_type.%s_type.%s_type_selector ) == 'NULL':
                                                            %s = NULL
                                                        #end if
                                                    #end if
                                                    ''' % ( xml_dict['rscript_content'], 
                                                        input_placeholder, input_placeholder, input_placeholder,
                                                        input_placeholder, input_placeholder, input_placeholder,
                                                        inp_name, input_placeholder, input_placeholder, input_placeholder,
                                                        input_placeholder, input_placeholder, input_placeholder,
                                                        inp_name, input_placeholder, input_placeholder, input_placeholder,
                                                        input_placeholder, input_placeholder, input_placeholder,
                                                        inp_name, input_placeholder, input_placeholder, input_placeholder,
                                                        input_placeholder, input_placeholder, input_placeholder,
                                                        inp_name, input_placeholder, input_placeholder, input_placeholder,
                                                        input_placeholder, input_placeholder, input_placeholder,
                                                        inp_name, input_placeholder, input_placeholder, input_placeholder,
                                                        input_placeholder, input_placeholder, input_placeholder,
                                                        inp_name, input_placeholder, input_placeholder, input_placeholder,
                                                        input_placeholder, input_placeholder, input_placeholder,
                                                        inp_name,
                                                        )
            elif use_quotes:
                xml_dict['rscript_content'] = '%s${___USE_COMMA___}\n#set $___USE_COMMA___ = ","\n%s = "${ %s_type.%s }"' % ( xml_dict['rscript_content'], inp_name, input_placeholder, input_placeholder )
            else:
                xml_dict['rscript_content'] = '%s${___USE_COMMA___}\n#set $___USE_COMMA___ = ","\n%s = ${ %s_type.%s }' % ( xml_dict['rscript_content'], inp_name, input_placeholder, input_placeholder )
            xml_dict['rscript_content'] = '%s\n#end if\n' % ( xml_dict['rscript_content'] )
xml_dict['rscript_content'] = '%s\n)%s' % ( xml_dict['rscript_content'], SAVE_R_OBJECT_TEXT )


assert rname not in package_dict, "%s already exists!" % (package_dict)
package_dict[rname] = xml_dict
with open( os.path.join( args.out, "%s.xml" % ( xml_dict['id_underscore'] ) ), 'w+' ) as out:
    out.write( tool_xml % xml_dict )
print("Created: %s" % ( os.path.join( args.out, "%s.xml" % ( xml_dict['id_underscore'] ) ) ))

# except Exception as e:
#     print('uncaught error in: %s\n' % (  e ))
    # skipped += 1
# print('Ending',j,name)
#print package_dict
print('')
print('created', len(package_dict) + int(args.create_load_matrix_tool), 'tool XMLs')
print('skipped', skipped, 'functions')