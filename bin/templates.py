#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Functions for generating XML templates for Galaxy tools."""

from xml.sax.saxutils import quoteattr
from rpy2.rinterface import str_typeint
from utils import simplify_text, to_docstring, unroll_vector_to_text
from r_utils import get_r_help_pages

# XML templates
tool_xml = '''<tool id="%(id)s" name="%(name)s" version="@VERSION@-%(galaxy_tool_version)s">
    <description><![CDATA[%(description)s]]></description>
    <macros>
        <import>%(r_name)s_macros.xml</import>
    </macros>
    <expand macro="requirements" />
    <expand macro="stdio" />
    <expand macro="version_command" />
    <command><![CDATA[
        #if "output_r_script" in str($include_outputs).split(","):
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

# Input templates
input_dataset = '''<param name="%(name)s" type="data" format="rds" label=%(label)s help=%(help)s/>'''
input_text = '''<param name="%(name)s" type="text" value=%(value)s label=%(label)s help=%(help)s/>'''
input_boolean = '''<param name="%(name)s" type="boolean" truevalue="TRUE" falsevalue="FALSE" checked=%(value)s label=%(label)s help=%(help)s/>'''
input_integer = '''<param name="%(name)s" type="integer" value=%(value)s label=%(label)s help=%(help)s/>'''
input_float = '''<param name="%(name)s" type="float" value=%(value)s label=%(label)s help=%(help)s/>'''
input_select = '''<param name="%(name)s" type="text" value=%(value)s label=%(label)s help=%(help)s/><!-- Should be select? -->'''

# Configuration for input types
INPUT_NOT_DETERMINED_PASS_DICT = {}
for select in ['dataset_selected', 'text_selected', 'integer_selected', 'float_selected', 
               'boolean_selected', 'skip_selected', 'NULL_selected', 'NA_selected']:
    INPUT_NOT_DETERMINED_PASS_DICT[select] = "%(" + select + ")s"

# Template for undetermined input type
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

# Default values for input types
INPUT_NOT_DETERMINED_DICT = {}
for select in ['dataset_selected', 'text_selected', 'integer_selected', 'float_selected', 
              'boolean_selected', 'skip_selected', 'NULL_selected', 'NA_selected']:
    INPUT_NOT_DETERMINED_DICT[select] = False

# Template for optional inputs
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

# Optional input templates for different types
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
    ).items())
)

# Template for ellipsis (... in R)
ellipsis_input = '''
    <repeat name="___ellipsis___" title="Additional %(name)s">
        <param name="%(name)s_name" type="text" value="" label="Name for argument" help=""/>
        %(input_not_determined)s
    </repeat>
''' % dict(
    input_not_determined=input_not_determined, 
    name='argument'
) % dict(
    list(INPUT_NOT_DETERMINED_PASS_DICT.items()) + 
    list(dict(
        name='argument', 
        label='"Argument value"', 
        help='""', 
        value='""'
    ).items())
)

# R script templates
CONFIG_SPLIT_DESIRED_OUTPUTS = '''#set $include_files = str($include_outputs).split(",")'''

SAVE_R_OBJECT_TEXT = '''
#if "output_r_dataset" in $include_files:
    saveRDS(rval, file = "${output_r_dataset}", ascii = FALSE, version = 2, compress = TRUE)
#end if
'''

def generate_macro_xml(package_name, package_version, r_name, galaxy_tool_version):
    """Generate the macros.xml file content for a Galaxy tool.
    
    Args:
        package_name: Name of the R package
        package_version: Version of the R package
        r_name: Name of the R library
        galaxy_tool_version: Version string for the Galaxy tool
        
    Returns:
        String containing the XML content
    """
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
#set $int_species_column = int(str($species_column))
#set $fixed_sample_columns = []
#for $sample_col in map(int, str($sample_columns).split(",")):
#assert $sample_col != $int_species_column, "Sample label column and sample count columns must not be the same."
#silent $fixed_sample_columns.append(str($sample_col if $sample_col < $int_species_column else $sample_col-1))
#end for
options(bitmapType='cairo')## No X11, so we'll use cairo
library(%(r_name)s)
input_abundance <- read.table("${input_abundance}", sep="\t", row.names=${species_column}, header=${header})
input_abundance <- t(input_abundance[c(${",".join($fixed_sample_columns)})])
]]>
    </token>

    <token name="@VERSION@">%(package_version)s</token>

</macros>''' % dict(
        package_name=package_name,
        package_version=package_version,
        r_name=r_name,
        galaxy_tool_version=galaxy_tool_version
    )
    return macro_xml

def generate_LOAD_MATRIX_TOOL_XML(package_name, package_version, r_name, galaxy_tool_version):
    """Generate the r_load_matrix.xml file content for loading tabular data into R.
    
    Args:
        package_name: Name of the R package
        package_version: Version of the R package
        r_name: Name of the R library
        galaxy_tool_version: Version string for the Galaxy tool
        
    Returns:
        String containing the XML content
    """
    return '''<tool id="r_load_matrix" name="Load Tabular Data into R" version="%(galaxy_tool_version)s">
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
        #if "output_r_script" in str($include_outputs).split(","):
            cp '${r_load_script}' '${output_r_script}' &&
        #end if
        Rscript '${r_load_script}'
    ]]>
    </command>
    <configfiles>
        <configfile name="r_load_script"><![CDATA[
@RSCRIPT_LOAD_TABULAR_FILE@
saveRDS(input_abundance, file = "${output_r_dataset}", ascii = FALSE, version = 2, compress = TRUE)


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
</tool>''' % dict(
        package_name=package_name,
        package_version=package_version,
        r_name=r_name,
        galaxy_tool_version=galaxy_tool_version
    )

def process_function_inputs(package_obj):
    """Process the inputs for an R function.
    
    Args:
        package_obj: The R function object
        
    Returns:
        Tuple containing (inputs, input_names, inputs_xml_string)
    """
    inputs = []
    input_names = []
    
    for formal_name, formal_value in package_obj.formals().items():
        default_value = ''
        input_type = 'text'
        input_dict = INPUT_NOT_DETERMINED_DICT.copy()
        input_dict.update({
            'name': simplify_text(formal_name),
            'label': quoteattr(formal_name),
            'help': quoteattr(str(formal_value).strip()),
            'value': '',
            'multiple': False,
        })
        
        input_template = optional_input_text
        use_quotes = True
        
        try:
            value_name, value_value = list(formal_value.items())[0]
            r_type = str_typeint(value_value.typeof)
            
            if r_type == 'INTSXP':
                input_type = 'integer'
                default_value = str(value_value[0])
                input_template = optional_input_integer
                use_quotes = False
                input_dict['integer_selected'] = True
                input_type = 'not_determined'
            elif r_type == 'LGLSXP':
                input_type = 'boolean'
                default_value = str(value_value[0])
                input_template = optional_input_boolean
                use_quotes = False
                if default_value == 'NULL':
                    input_dict['NULL_selected'] = True
                elif default_value == 'NA':
                    input_dict['NA_selected'] = True
                else:
                    input_dict['boolean_selected'] = True
                input_type = 'not_determined'
            elif r_type == 'REALSXP':
                input_type = 'float'
                default_value = str(value_value[0])
                input_template = optional_input_float
                use_quotes = False
                input_dict['float_selected'] = True
                input_type = 'not_determined'
            elif r_type == 'STRSXP':
                input_type = 'text'
                default_value = str(value_value[0])
                input_template = optional_input_text
                input_dict['text_selected'] = True
                input_type = 'not_determined'
            else:
                input_type = 'not_determined'
                input_template = optional_input_not_determined
                input_dict['dataset_selected'] = True
            
            length = len(list(value_value))
            input_dict['multiple'] = (length > 1)
        except Exception as e:
            print(f'Error getting input param info: {e}')
        
        if input_type == 'dataset':
            input_template = optional_input_dataset
        elif input_type == 'boolean':
            default_value = str((default_value.strip().lower() == 'true'))
        
        input_dict['value'] = quoteattr(default_value)
        input_place_name = input_dict['name']
        
        if formal_name in ['...']:
            inputs.append(ellipsis_input % input_dict)
            input_names.append(('...', '___ellipsis___', 'ellipsis', False))
        else:
            inputs.append(input_template % input_dict)
            input_names.append((formal_name, input_place_name, input_type, use_quotes))
    
    return inputs, input_names, "        %s" % ("\n        ".join(inputs))

