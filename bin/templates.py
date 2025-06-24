#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Templates for Galaxy tool XML generation."""

# Main tool XML template
tool_xml = '''<tool id="%(id)s" name="%(name)s" version="@VERSION@-%(galaxy_tool_version)s">
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

# Input parameter templates
input_dataset = '''<param name="%(name)s" type="data" format="rds" label=%(label)s help=%(help)s/>'''
input_text = '''<param name="%(name)s" type="text" value=%(value)s label=%(label)s help=%(help)s/>'''
input_boolean = '''<param name="%(name)s" type="boolean" truevalue="TRUE" falsevalue="FALSE" checked=%(value)s label=%(label)s help=%(help)s/>'''
input_integer = '''<param name="%(name)s" type="integer" value=%(value)s label=%(label)s help=%(help)s/>'''
input_float = '''<param name="%(name)s" type="float" value=%(value)s label=%(label)s help=%(help)s/>'''
input_select = '''<param name="%(name)s" type="text" value=%(value)s label=%(label)s help=%(help)s/><!-- Should be select? -->'''

# Dictionary for not determined inputs
INPUT_NOT_DETERMINED_PASS_DICT = {}
for select in ['dataset_selected', 'text_selected', 'integer_selected', 'float_selected', 
               'boolean_selected', 'skip_selected', 'NULL_selected', 'NA_selected']:
    INPUT_NOT_DETERMINED_PASS_DICT[select] = "%(" + select + ")s"

# Template for when input type is not determined
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
        name="%(name)s",
        input_dataset=input_dataset,
        input_text=input_text,
        input_boolean=input_boolean,
        input_integer=input_integer,
        input_float=input_float,
        input_select=input_select
    ).items())
)

# Default settings for not determined inputs
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

# Define various optional input templates
optional_input_dataset = optional_input % dict(
    name="%(name)s",
    input_template=input_dataset
)
optional_input_text = optional_input % dict(
    name="%(name)s",
    input_template=input_text
)
optional_input_boolean = optional_input % dict(
    name="%(name)s",
    input_template=input_boolean
)
optional_input_integer = optional_input % dict(
    name="%(name)s",
    input_template=input_integer
)
optional_input_float = optional_input % dict(
    name="%(name)s",
    input_template=input_float
)
optional_input_select = optional_input % dict(
    name="%(name)s",
    input_template=input_select
)
optional_input_not_determined = optional_input % dict(
    list(INPUT_NOT_DETERMINED_PASS_DICT.items()) +
    list(dict(
        name="%(name)s",
        input_template=input_not_determined
    ).items())
)

# Template for ellipsis input (variable arguments)
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
