#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Functions to generate various Galaxy XML files."""

def generate_macro_xml(package_name, package_version, r_name, galaxy_tool_version):
    """Generate the Galaxy macros XML file."""
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

</macros>''' % dict(package_name=package_name, package_version=package_version, 
                    r_name=r_name, galaxy_tool_version=galaxy_tool_version)
    return macro_xml

def generate_LOAD_MATRIX_TOOL_XML(package_name, package_version, r_name, galaxy_tool_version):
    """Generate the Galaxy XML for the load matrix tool."""
    LOAD_MATRIX_TOOL_XML = '''<tool id="r_load_matrix" name="Load Tabular Data into R" version="%(galaxy_tool_version)s">
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
</tool>''' % dict(package_name=package_name, package_version=package_version, 
                 r_name=r_name, galaxy_tool_version=galaxy_tool_version)
    return LOAD_MATRIX_TOOL_XML