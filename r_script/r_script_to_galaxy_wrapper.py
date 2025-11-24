#!/usr/bin/env python
# -*- coding: utf-8

"""A script to convert anvi'o python scripts to Galaxy Tools."""

import argparse as argparse_original
import sys
import os
from collections import OrderedDict
from xml.sax.saxutils import quoteattr
from jinja2 import Template
import json

#profile="19.01"
TOOL_TEMPLATE = """<tool id="{{id}}" name="{{name}}" version="{{version}}" profile="{{profile}}" >
{%- if description %}
    <description>{{ description }}</description>
{%- endif %}
{%- if macros %}
    <macros>
        <import>macros.xml</import>
    </macros>
    <expand macro="requirements" />
    <expand macro="stdio" />
{%- if version_command %}
    <expand macro="version_command" />
{%- endif %}
{%- else %}
    <requirements>
    {{ requirements }}
    </requirements>
{%- if realtime %}
    <entry_points>
{%- for ep in realtime %}
        <entry_point name="{{ ep['name'] }}" requires_domain="true">
            <port>{{ ep.get('port', DEFAULT_INTERACTIVE_PORT) }}</port>
            {%- if 'url' in ep and ep['url']%}
            <url><![CDATA[{{ ep['url'] }}]]></url>
            {%- endif %}
        </entry_point>
{%- endfor %}
    </entry_points>
{%- endif %}
    <stdio>
        <exit_code range="1:" />
    </stdio>
{%- if version_command %}
    <version_command>{{ version_command }}</version_command>
{%- endif %}
{%- endif %}
    <command><![CDATA[ 
        Rscript '$__tool_directory__/{{file_name}}'
{%- if command %}
    {{ command }}
{%- else %}
        TODO: Fill in command template.
{%- endif %}
    ]]></command>
    <inputs>
{%- for input in inputs %}
       {{ input }}
{%- endfor %}
    </inputs>
    <outputs>
{%- for output in outputs %}
        {{ output }}
{%- endfor %}
    </outputs>
{%- if tests %}
    <tests>
{%- for test in tests %}
        <test>
{%- for param in test.params %}
            <param name="{{ param[0]}}" value="{{ param[1] }}"/>
{%- endfor %}
{%- for output in test.outputs %}
            <output name="{{ output[0] }}" file="{{ output[1] }}"/>
{%- endfor %}
        </test>
{%- endfor %}
    </tests>
{%- endif %}
    <help><![CDATA[
{%- if help %}
{{ help }}
{%- else %}
        TODO: Fill in help.
{%- endif %}
    ]]></help>
{%- if macros %}
    <expand macro="citations" />
{%- else %}
{%- if doi or bibtex_citations %}
    <citations>
{%- for single_doi in doi %}
        <citation type="doi">{{ single_doi }}</citation>
{%- endfor %}
{%- for bibtex_citation in bibtex_citations %}
        <citation type="bibtex">{{ bibtex_citation }}</citation>
{%- endfor %}
    </citations>
{%- endif %}
{%- endif %}
</tool>
"""

MACROS_TEMPLATE = """<macros>
    <xml name="requirements">
        <requirements>
{%- for requirement in requirements %}
        {{ requirement }}
{%- endfor %}
            <yield/>
{%- for container in containers %}
        {{ container }}
{%- endfor %}
        </requirements>
    </xml>
    <xml name="stdio">
        <stdio>
            <exit_code range="1:" />
        </stdio>
    </xml>
    <xml name="citations">
        <citations>
{%- for single_doi in doi %}
            <citation type="doi">{{ single_doi }}</citation>
{%- endfor %}
{%- for bibtex_citation in bibtex_citations %}
            <citation type="bibtex">{{ bibtex_citation }}</citation>
{%- endfor %}
            <yield />
        </citations>
    </xml>
{%- if version_command %}
    <xml name="version_command">
        <version_command>{{ version_command }}</version_command>
    </xml>
{%- endif %}
</macros>
"""

galaxy_tool_citation ='''@ARTICLE{Blankenberg20-anvio,
   author = {Daniel Blankenberg Lab, et al},
   title = {In preparation..},
   }'''


class Parameter( object ):
    _output_startswith = ('output', 'export')
    def __init__( self, name, arg_short, arg_long, info_dict ):
        self._name = name
        self.name = name.replace( "-", '_' )
        self.arg_short = arg_short
        self.arg_long = arg_long
        self.info_dict = info_dict
        self.required = info_dict.get( 'required', False )
        self.is_output = name.lower().startswith( self._output_startswith )
        self.is_input = not self.is_output
    def copy(self, name=None, arg_short=None, arg_long=None, info_dict = None):
        orig_dict = self.info_dict.copy()
        if info_dict:
            orig_dict.update( info_dict )
        return self.__class__( name or self.name, arg_short or self.arg_short, arg_long or self.arg_long, orig_dict )
    def get_name( self ):
        return quoteattr( self.name )
    def get_output_cmd_name(self):
        return self.name
    def get_input_cmd_name(self):
        return self.name
    def get_type( self ):
        return 'text'
    def get_label( self ):
        return quoteattr( self.name.replace( '_', " " ).title() )
    def get_default( self ):
        default = self.info_dict.get( 'default', None )
        if default is None:
            default = ''
        return quoteattr( str( default ) )
    def get_argument( self ):
        return quoteattr( self.arg_long )
    def is_positional_arg( self ):
        return not ( self.arg_short or self.arg_long )
    def get_arg_text( self ):
        arg = self.arg_long or self.arg_short or ''
        return arg
    def get_help( self, extra=None ):
        help = self.info_dict.get('help', '')
        #if 'default' not in self.info_dict and '%(default)' in help:
        #    print('MISSING DEFAULT!')
        #    self.info_dict['default'] = None
        #help = help % self.info_dict
        #FIX FOR NOT DEFINED DEFAULT IN HELP TEXT
        #A,B,C,D
        try:
            help = help.format(**self.info_dict)
        except KeyError as e:
            print('FIXME: formatting help failed')
            # print(e)
        if extra:
            help = "%s %s" % (help, extra)
        help = help.replace( '\n', ' ' ).replace( '\r', ' ' ).replace( '\t', ' ' ).strip()
        while '  ' in help:
            help = help.replace( '  ', ' ' )
        return quoteattr( help )
    def get_optional( self ):
        if self.info_dict.get( 'required', False ):
            return 'False'
        return 'True'
    def to_xml_param( self ):
        return """<param name=%s type="%s" label=%s value=%s optional="%s" argument=%s help=%s/>""" % \
            (
                quoteattr( self.get_input_cmd_name() ), 
                self.get_type(),  
                self.get_label(), 
                self.get_default(), 
                self.get_optional(),
                self.get_argument(), 
                self.get_help(),
            )
    def to_xml_output( self ):
        return ''
    def get_pre_cmd_line( self ):
        return ''
    def get_post_cmd_line( self ):
        return ''
    def to_cmd_line( self ):
        text = ''
        cmd_txt =  "%s '${%s}'" % ( self.get_arg_text(), self.get_input_cmd_name() )
        if not self.required:
            text = """
#if $str( $%s ):
    %s
#end if\n""" % ( self.get_input_cmd_name(), cmd_txt )
        else:
            text = "%s\n" % cmd_txt
        return text
    def __str__( self ):
        return "%s\n%s\n" % ( self.to_xml_param(), self.to_cmd_line() )

class ParameterDiscard( Parameter ):
    def get_type(self):
        return "string"
    def to_xml_param( self ):
        return ''
    def to_cmd_line( self ):
        return ''

class ParameterBooleanAlwaysTrue( Parameter ):
    def get_type(self):
        return "boolean"
    def to_xml_param( self ):
        return ''
    def to_cmd_line( self ):
        return self.arg_long

class ParameterAlwaysDefault( Parameter ):
    def get_type(self):
        return "text"
    def to_xml_param( self ):
        return ''
    def to_cmd_line( self ):
        return "%s '%s'" % (self.arg_long, self.get_default())

class ParameterAlwaysValue( Parameter ):
    value = None
    def get_type(self):
        return "text"
    def to_xml_param( self ):
        return ''
    def to_cmd_line( self ):
        return "%s '%s'" % (self.arg_long, self.value)

class ParameterBoolean( Parameter ):
    def get_type(self):
        return "boolean"
    def to_xml_param( self ):
        return """<param name=%s type="%s" label=%s truevalue="%s" falsevalue="" checked=%s optional="%s" argument=%s help=%s/>""" % \
            (
                self.get_name(), 
                self.get_type(),  
                self.get_label(),
                self.arg_long,
                '"true"', 
                self.get_optional(),
                self.get_argument(), 
                self.get_help(),
            )
    
    def to_cmd_line( self ):
        return "${%s}\n" % ( self.name )

class ParameterINT( Parameter ):
    def get_type(self):
        return "integer"

class ParameterFLOAT( Parameter ):
    def get_type(self):
        return "float"

class ParameterNUM_CPUS( ParameterINT ):
    def to_xml_param( self ):
        return ''
    def to_cmd_line( self):
        return '%s "\\${GALAXY_SLOTS:-1}"\n' % ( self.get_arg_text() )

class ParameterFILE_PATH( Parameter ):
    def __init__( self, *args, **kwd ):
        super( ParameterFILE_PATH, self ).__init__( *args, **kwd )
        self.multiple = False
        if self.info_dict.get( 'nargs', None ) == '+':
            self.multiple = True
    def get_type(self):
        return "data"
    def get_format( self ):
        return "txt"
    def get_multiple( self ):
        return self.multiple
    def get_output_label( self ):
        return quoteattr( '${tool.name} on ${on_string}: %s' % ( self.name.replace( '_', " " ).title() ) )
    def to_xml_param( self ):
        return """<param name=%s type="%s" label=%s format="%s" optional="%s" multiple="%s" argument=%s help=%s/>""" % \
            (
                quoteattr( self.get_input_cmd_name() ), 
                self.get_type(),  
                self.get_label(), 
                self.get_format(), 
                self.get_optional(),
                self.get_multiple(),
                self.get_argument(), 
                self.get_help(),
            )
    def get_format_source(self):
        return 'format_source="input_%s"' % ( self.name )
        if ',' in self.get_format():
            return 'format_source="input_%s"' % ( self.name )
        return ''
    
    def get_metadata_source(self):
        return 'metadata_source="input_%s"' % ( self.name )
        if ',' in self.get_format():
            return 'format_source="input_%s"' % ( self.name )
        return ''
    
    def to_xml_output( self ):
        #print ('toxml putput', self.name, self.get_format() ) 
        return """<data name=%s format="%s" %s %s label=%s/>""" % \
            (
                quoteattr(self.get_output_cmd_name() ), 
                self.get_format().split(',')[0],
                self.get_format_source(),
                self.get_metadata_source(),
                self.get_output_label(),
            )
    
    def to_cmd_line( self ):
        text = ''
        cmd_txt =  "%s '${%s}'" % ( self.get_arg_text(), self.get_input_cmd_name() )
        if not self.required:
            text = """
#if $%s:
    %s
#end if\n""" % ( self.get_input_cmd_name(), cmd_txt )
        else:
            text = "%s\n" % cmd_txt
        return text

class ParameterREPORT_FILE_PATH( ParameterFILE_PATH ):
    def __init__( self, *args, **kwd ):
        super( ParameterREPORT_FILE_PATH, self ).__init__( *args, **kwd )
        self.is_input = False
        self.is_output = True

class ParameterDB( ParameterFILE_PATH ):
    def __init__( self, *args, **kwd ):
        super( ParameterDB, self ).__init__( *args, **kwd )
        self.is_output = True
        self.is_input = not self.name.startswith( self._output_startswith )
    def get_format( self ):
        return "anvio_db"
    def to_cmd_line( self ):
        if self.is_input:
            return  "%s '${%s}'\n" % ( self.get_arg_text(), self.get_output_cmd_name() )
        else:
            return  "%s '%s.db'\n" % ( self.get_arg_text(), self.name )
    def get_output_cmd_name(self):
        if self.is_input:
            return "output_%s" % self.name
        else:
            return self.name
    def get_input_cmd_name(self):
        if self.is_output:
            return "input_%s" % self.name
        else:
            return self.name
        
    def get_pre_cmd_line( self ):
        text = ''
        if self.is_input:
            text = ''
            cmd_text = "cp '${%s}' '${%s}'" % ( self.get_input_cmd_name(), self.get_output_cmd_name() )
            if not self.required:
                text = """
    #if $%s:
        %s
    #else
        echo ''
    #end if""" % ( self.get_input_cmd_name(), cmd_text )
            else:
                text = cmd_text
        #else:
        #    text = "rm '${%s}'" % ( self.get_output_cmd_name() )
        return text

    def get_post_cmd_line( self ):
        if not self.is_input:
            return "mv '%s.db' '${%s}'" % ( self.name, self.get_output_cmd_name()  )
        return ''

class ParameterFASTA( ParameterFILE_PATH ):
    def get_format( self ):
        return "fasta"

class ParameterFASTQ( ParameterFILE_PATH ):
    def get_format( self ):
        return "fastq"

class ParameterGENBANK( ParameterFILE_PATH ):
    def get_format( self ):
        return "genbank"

class ParameterVARIABILITY_TABLE(ParameterFILE_PATH):
    def get_format(self):
        return 'anvio_variability'

class ParameterClassifierFile(ParameterFILE_PATH):
    def get_format(self):
        return 'anvio_classifier'

class ParameterSVG(ParameterFILE_PATH):
    def get_format(self):
        return 'svg'
    
class ParameterPROFILE( ParameterFILE_PATH ):
    def get_format( self ):
        return "anvio_profile_db"
    def to_cmd_line( self ):
        text = ''
        if self.multiple:
            cmd_text = """
            #for $gxy_%s in $%s:
                %s '${gxy_%s.extra_files_path}/PROFILE.db'
            #end for
            """ % ( self.name, self.name, self.get_arg_text(), self.name )
        else:
            cmd_text = "%s '${%s.extra_files_path}/PROFILE.db'" % ( self.get_arg_text(), self.name )
        if not self.multiple:
            text = """
#if $%s:
    %s
#end if\n""" % ( self.name, cmd_text )
        else:
            text = cmd_text
        return text

# class ParameterUnknownDB( ParameterFILE_PATH ):
#     #TODO: should we copy the inputs to to outputs?
#     def __init__( self, *args, **kwd ):
#         super( ParameterUnknownDB, self ).__init__( *args, **kwd )
#         self.is_output = True
#         self.is_input = not self.name.startswith( self._output_startswith )
#         #self.basename='PROFILE'
#     def get_format( self ):
#         return "anvio_db"
#     def get_output_cmd_name(self):
#         if self.is_input:
#             return "output_%s" % self.name
#         else:
#             return self.name
#     def get_input_cmd_name(self):
#         if self.is_output:
#             return "input_%s" % self.name
#         else:
#             return self.name
#     def get_base_filename(self, multiple=False):
#         if multiple:
#             return "${gxy_%s.metadata.anvio_basename}" % self.get_output_cmd_name()
#         return "${%s.metadata.anvio_basename}" % self.get_output_cmd_name()
#     def to_cmd_line( self ):
#         text = ''
#         if self.multiple:
#             cmd_text = """
#             #for $gxy_%s in $%s:
#                 %s "${gxy_%s.extra_files_path}/%s"
#             #end for
#             """ % ( self.get_output_cmd_name(), self.get_output_cmd_name(), self.get_arg_text(), self.get_output_cmd_name(), self.get_base_filename(multiple=True) ) #( self.name, self.name, self.get_arg_text(), self.name, self.name )
#         else:
#             cmd_text = "%s '${%s.extra_files_path}/%s'" % ( self.get_arg_text(), self.get_output_cmd_name(), self.get_base_filename() )
#         if not self.multiple:
#             text = """
# #if $%s:
#     %s
# #end if\n""" % ( self.get_output_cmd_name(), cmd_text )
#         else:
#             text = cmd_text
#         return text

#     def get_pre_cmd_line( self ):
#         text = ''
#         if self.is_input:
#             if self.multiple:
#                 #
#                 cmd_text = """
#                 #for $GXY_I, ($gxy_%s, $gxy_%s) in $enumerate( $zip( $%s, $%s ) ):
#                     #if $GXY_I != 0:
#                         &&
#                     #end if
#                     cp -R '${gxy_%s.extra_files_path}' '${gxy_%s.extra_files_path}'
#                 #end for
#                 """ % ( self.get_input_cmd_name(), self.get_output_cmd_name(), self.get_input_cmd_name(), self.get_output_cmd_name(), self.get_input_cmd_name(), self.get_output_cmd_name() )
#                 #
#             else:
#                 cmd_text = "cp -R '${%s.extra_files_path}' '${%s.extra_files_path}'" % ( self.get_input_cmd_name(), self.get_output_cmd_name() )
#             if not self.required:
#                 text = """
#     #if $%s:
#         %s
#     #else
#         echo ''
#     #end if""" % ( self.get_input_cmd_name(), cmd_text )
#             else:
#                 text = cmd_text
#         else:
#             text = "mkdir '${%s.extra_files_path}'\n" % ( self.get_output_cmd_name() )
#         return text

#     def get_post_cmd_line( self ):
#         return ''

#     def to_xml_param( self ):
#         if self.is_input and self.multiple:
#             return """<param name=%s type="%s" collection_type="%s" label=%s format="%s" optional="%s" multiple="%s" argument=%s help=%s/>%s""" % \
#                         (
#                             quoteattr( self.get_input_cmd_name() ), 
#                             'data_collection',#self.get_type(),
#                             'list',
#                             self.get_label(), 
#                             self.get_format(), 
#                             self.get_optional(),
#                             self.get_multiple(),
#                             self.get_argument(), 
#                             self.get_help(extra=COLLECTION_UX_FAIL_NOTE_USER),
#                             COLLECTION_UX_FAIL_NOTE,
#                         )
#         return super( ParameterUnknownDB, self ).to_xml_param()
#     def to_xml_output( self ):
#         if self.is_input and self.multiple:
#             return """<collection name=%s type="%s" format="%s" %s %s %s inherit_format="True" label=%s />""" % \
#                 (
#                     quoteattr(self.get_output_cmd_name() ),
#                     'list',
#                     self.get_format().split(',')[0],
#                     self.get_format_source(),
#                     self.get_metadata_source(),
#                     self.get_structured_like(),
#                     self.get_output_label(),
#                 )
#         else:
#             return super( ParameterUnknownDB, self ).to_xml_output()
#     def get_structured_like(self):
#         if self.is_input and self.multiple:
#             return 'structured_like="input_%s"' % ( self.name )
#         else:
#             return ''
#             #return super( ParameterUnknownDB, self ).get_structured_like()
# ###
# ###

class ParameterINOUTCOMPOSITE_DATA_DIR_PATH( ParameterDB ):
    def __init__( self, *args, **kwd ):
        super( ParameterDB, self ).__init__( *args, **kwd )
        self.is_output = True
        self.is_input = True
    def get_format( self ):
        return "anvio_composite"

    def to_cmd_line( self ):
        if self.is_input:
            return  "%s '${%s.extra_files_path}'\n" % ( self.get_arg_text(), self.get_output_cmd_name() )
        else:
            return  "%s '${%s.extra_files_path}'\n" % ( self.get_arg_text(), self.get_output_cmd_name() )
    def get_pre_cmd_line( self ):
        text = ''
        if self.is_input:
            text = ''
            cmd_text = "cp -R '${%s.extra_files_path}' '${%s.extra_files_path}'" % ( self.get_input_cmd_name(), self.get_output_cmd_name() )
            if not self.required:
                text = """
    #if $%s:
        %s
    #else
        echo ''
    #end if""" % ( self.get_input_cmd_name(), cmd_text )
            else:
                text = cmd_text
        else:
            text = "mkdir '${%s.extra_files_path}'\n" % ( self.get_output_cmd_name() )
        return text

    def get_post_cmd_line( self ):
        return ''

class ParameterCOG_DATA_DIR_PATH( ParameterINOUTCOMPOSITE_DATA_DIR_PATH ):
    def get_format( self ):
        return "anvio_cog_profile"

class ParameterPFAM_DATA_DIR_PATH( ParameterINOUTCOMPOSITE_DATA_DIR_PATH ):
    def get_format( self ):
        return "anvio_pfam_profile"

'''
    def to_cmd_line( self ):
        text = ''
        if self.multiple:
            cmd_text = """
            #for $gxy_%s in $%s:
                %s '${gxy_%s.extra_files_path}'
            #end for
            """ % ( self.name, self.name, self.get_arg_text(), self.name )
        else:
            cmd_text = "%s '${%s.extra_files_path}'" % ( self.get_arg_text(), self.name )
        if not self.multiple:
            text = """
#if $%s:
    %s
#end if\n""" % ( self.name, cmd_text )
        else:
            text = cmd_text
        return text

    def to_cmd_line( self ):
        if self.is_input:
            return  "%s '${%s.extra_files_path}'\n" % ( self.get_arg_text(), self.get_output_cmd_name())
        else:
            return  "%s '${%s.extra_files_path}'\n" % ( self.get_arg_text(), self.get_output_cmd_name())
    def get_pre_cmd_line( self ):
        text = ''
        if self.is_input:
            text = ''
            cmd_text = "cp -R '${%s.extra_files_path}' '${%s.extra_files_path}'" % ( self.get_input_cmd_name(), self.get_output_cmd_name() )
            if not self.required:
                text = """
    #if $%s:
        %s
    #end if""" % ( self.get_input_cmd_name(), cmd_text )
            else:
                text = cmd_text
        else:
            text = "mkdir '${%s.extra_files_path}'\n" % ( self.get_output_cmd_name() )
        return text
'''
#    def get_post_cmd_line( self ):
#        if not ( self.is_contigs or self.is_samples ):
#            return super( ParameterContigsDB, self ).get_post_cmd_line()
#        return ''

####
###

class ParameterFILES( ParameterFILE_PATH ):
    def get_format( self ):
        return "data"

class ParameterTABULAR( ParameterFILE_PATH ):
    def get_format( self ):
        return "tabular"

class ParameterNEWICK( ParameterFILE_PATH ):
    def get_format( self ):
        return "newick"

class ParameterSTATE_FILE( ParameterFILE_PATH ):
    def get_format( self ):
        return "anvio_state"

class ParameterINPUT_BAM( ParameterFILE_PATH):
    def get_format( self ):
        return 'bam'
    def get_pre_cmd_line( self ):
        text = ''
        cmd_text = "ln -s '${%s}' '%s.bam' && ln -s '${%s.metadata.bam_index}' '%s.bam.bai'" % ( self.get_input_cmd_name(), self.name, self.get_input_cmd_name(), self.name )
        if not self.required:
            text = """
    #if $%s:
        %s
    #else
        echo ''
    #end if""" % ( self.get_input_cmd_name(), cmd_text )
        else:
            text = cmd_text
        return text
    def to_cmd_line( self ):
        text = ''
        cmd_txt =  "%s '%s.bam'" % ( self.get_arg_text(), self.name )
        if not self.required:
            text = """
#if $%s:
    %s
#end if\n""" % ( self.get_input_cmd_name(), cmd_txt )
        else:
            text = "%s\n" % cmd_txt
        return text

class ParameterINPUT_BAMS( ParameterFILE_PATH):
    def get_format( self ):
        return 'bam'
    def get_pre_cmd_line( self ):
        text = ''
        cmd_text = """
        #for $gxy_i, $input_galaxy_bam in enumerate( $%s ):
        #if $gxy_i != 0:
            &&
        #end if
        ln -s '${input_galaxy_bam}' '${gxy_i}_%s.bam' && ln -s '${input_galaxy_bam.metadata.bam_index}' '${gxy_i}_%s.bam.bai'
        #end for
        """ % ( self.get_input_cmd_name(), self.name, self.name )
        if not self.required:
            text = """
    #if $%s:
        %s
    #else
        echo ''
    #end if""" % ( self.get_input_cmd_name(), cmd_text )
        else:
            text = cmd_text
        return text
    def to_cmd_line( self ):
        text = ''
        cmd_text = """
        #for $gxy_i, $input_galaxy_bam in enumerate( $%s ):
        %s '${gxy_i}_%s.bam'
        #end for
        """ % ( self.get_input_cmd_name(), self.get_arg_text(), self.name )
        if not self.required:
            text = """
#if $%s:
    %s
#end if\n""" % ( self.get_input_cmd_name(), cmd_text )
        else:
            text = "%s\n" % cmd_text
        return text


class ParameterListOrFile( ParameterFILE_PATH ):
    def get_conditional_name( self ):
        return "%s_source" % self.name
    def get_conditional_selector_name( self ):
        return "%s_source_selector" % self.name
    def get_conditional_name_q( self ):
        return quoteattr( self.get_conditional_name() )
    def get_conditional_selector_name_q( self ):
        return quoteattr( self.get_conditional_selector_name() )
    def to_xml_param( self ):
        return """<conditional name=%s>
                      <param name=%s type="select" label="Use a file or list">
                          <option value="file" selected="True">Values from File</option>
                          <option value="list">Values from List</option>
                      </param>
                      <when value="file">
                          <param name=%s type="%s" label=%s format="%s" optional="%s" argument=%s help=%s/>
                      </when>
                      <when value="list">
                          <param name=%s type="text" label=%s value=%s optional="%s" argument=%s help=%s/>
                      </when>
                  </conditional>""" % \
            (
                self.get_conditional_name_q(),
                self.get_conditional_selector_name_q(),
                self.get_name(), 
                self.get_type(),  
                self.get_label(), 
                self.get_format(), 
                self.get_optional(),
                self.get_argument(), 
                self.get_help(),
                self.get_name(), 
                self.get_label(), 
                self.get_default(), 
                self.get_optional(),
                self.get_argument(), 
                self.get_help(),
            )
    def to_cmd_line( self ):
        cmd_txt =  "%s '${%s.%s}'" % ( self.get_arg_text(), self.get_conditional_name(), self.name )
        text = """
#if $str( $%s.%s ) == "file":
    #if $%s.%s:
        %s
    #end if
#else:
    #if $str( $%s.%s ):
        %s
    #end if
#end if
""" % ( self.get_conditional_name(), self.get_conditional_selector_name(),
            self.get_conditional_name(), self.name,
            cmd_txt,
            self.get_conditional_name(), self.name,
            cmd_txt
         )
        return text

DEFAULT_PARAMETER = Parameter

PARAMETER_BY_METAVAR = {
    # 'DB': ParameterUnknownDB,
    'INT': ParameterINT,
    'INTEGER': ParameterINT,
    'FLOAT': ParameterFLOAT,
    'FILE_PATH': ParameterFILE_PATH,
    'FILE': ParameterFILE_PATH,
    'FASTA': ParameterFASTA,
    'LEEWAY_NTs': ParameterINT,
    'WRAP': ParameterINT,
    'NUM_SAMPLES': ParameterINT,
    #'DIR_PATH': ParameterDIR_PATH,#should this be profile, or generic anvio, probably generic anvio
    'PERCENT_IDENTITY': ParameterFLOAT,
    'GENE_CALLER_ID': ParameterINT,
    'SMTP_CONFIG_INI': ParameterFILE_PATH,
    'FILE_NAME': ParameterFILE_PATH,
    'PROFILE': ParameterPROFILE,
    'SAMPLES-ORDER': ParameterTABULAR,
    'E-VALUE': ParameterFLOAT,
    'SAMPLES-INFO': ParameterTABULAR,#ParameterDB,
    'NEWICK': ParameterNEWICK,
    'GENOME_NAMES': ParameterListOrFile,
    'RUNINFO_PATH': ParameterFILE_PATH,
    'ADDITIONAL_LAYERS': ParameterTABULAR,
    'VIEW_DATA': ParameterTABULAR,
    'BINS_INFO': ParameterTABULAR,
    'PATH': ParameterFILE_PATH, #ParameterDIR_PATH, #used in matrix-to-newick
    'NUM_POSITIONS': ParameterINT,
    'CONTIGS_AND_POS': ParameterTABULAR,
    'GENE-CALLS': ParameterTABULAR,
    'ADDITIONAL_VIEW': ParameterTABULAR,
    'NUM_CPUS': ParameterNUM_CPUS,
    'RATIO': ParameterFLOAT,
    'TAB DELIMITED FILE': ParameterTABULAR,
    'INPUT_BAM': ParameterINPUT_BAM,
    'INPUT_BAM(S)': ParameterINPUT_BAMS,
    'FILE(S)': ParameterFILES,
    'SINGLE_PROFILE(S)': ParameterPROFILE,
    'TEXT_FILE': ParameterTABULAR,
    'NUM_THREADS': ParameterNUM_CPUS,
    'VARIABILITY_TABLE': ParameterVARIABILITY_TABLE,
    'VARIABILITY_PROFILE': ParameterVARIABILITY_TABLE,
    'STATE_FILE': ParameterSTATE_FILE,
    # 'DATABASE': ParameterUnknownDB,
    'BAM_FILE': ParameterINPUT_BAM,
    'REPORT_FILE_PATH': ParameterREPORT_FILE_PATH,
    'FLAT_FILE': ParameterFILE_PATH,
    'STATE': ParameterSTATE_FILE,
    'BINS_DATA': ParameterTABULAR,
    'LINKMER_REPORT': ParameterFILE_PATH, #should we add datatype? well output from anvi-report-linkmers is not datatyped due to generic metavar, so can't really
    # 'DB PATH': ParameterUnknownDB,
    'BAM FILE[S]': ParameterINPUT_BAMS,
    'FASTA FILE': ParameterFASTA,
    'REPORT FILE': ParameterREPORT_FILE_PATH,
    'GENBANK': ParameterGENBANK,
    'GENBANK_METADATA': ParameterFILE_PATH,
    'OUTPUT_FASTA_TXT': ParameterFILE_PATH,
    'EMAPPER_ANNOTATION_FILE': ParameterFILE_PATH,
    'MATRIX_FILE': ParameterTABULAR,
    'CLASSIFIER_FILE': ParameterClassifierFile,
    'SAAV_FILE': ParameterTABULAR,
    'SCV_FILE': ParameterTABULAR,
    'OUTPUT_FILE': ParameterFILE_PATH,
    'CHECKM TREE': ParameterFILE_PATH,
    'CONFIG_FILE': ParameterFILE_PATH,
    'FASTA_FILE': ParameterFASTA,
    'FASTQ_FILES': ParameterFASTQ,
    'IP_ADDR': ParameterDiscard,
    # 'DATABASE_PATH': ParameterUnknownDB,
}

PARAMETER_BY_NAME = {
    'cog-data-dir': ParameterCOG_DATA_DIR_PATH,
    'pfam-data-dir': ParameterPFAM_DATA_DIR_PATH,
    'just-do-it': ParameterBooleanAlwaysTrue,
    'temporary-dir-path': ParameterDiscard,
    'full-report': ParameterREPORT_FILE_PATH,
    'browser-path': ParameterDiscard,
    'server-only': ParameterBooleanAlwaysTrue,
    'password-protected': ParameterDiscard,
    'user-server-shutdown': ParameterBooleanAlwaysTrue,
    'dry-run': ParameterDiscard,
    'genes-to-add-file': ParameterFILE_PATH,
    'genes-to-remove-file': ParameterFILE_PATH,
    #'export-svg': ParameterSVG, #Config Error: You want to export SVGs? Well, you need the Python library 'selenium' to be able               to do that but you don't have it. If you are lucky, you probably can install it                by typing 'pip install selenium' or something :/   
    'export-svg': ParameterDiscard,
}

#FIXME. make skip just reuse ParameterDiscard
SKIP_PARAMETER_NAMES = ['help', 'temporary-dir-path', 'modeller-executable', 'program', 'log-file', 'gzip-output']
#modeller-executable would allow commandline injection
#program may do same
#help is shown on screen
#temp dirs are handled by system
#log-file, is redundant with output redirect always to log
#gzip will force-add a .gz suffix
SKIP_PARAMETER_NAMES = list(map( lambda x: x.replace( "-", '_' ), SKIP_PARAMETER_NAMES ))

'''
<param name="ip_address" type="text" label="Ip Address" value="0.0.0.0" optional="True" argument="--ip-address" help="IP address for the HTTP server. The default ip address (%(default)s) should work just fine for most."/>
    <param name="port_number" type="integer" label="Port Number" value="" optional="True" argument="--port-number" help="Port number to use for anvi'o services. If nothing is declared, anvi'o will try to find a suitable port number, starting from the default port number, 8080."/>
    <param name="browser_path" type="data" label="Browser Path" format="txt" optional="True" multiple="False" argument="--browser-path" help="By default, anvi'o will use your default browser to launch the interactive interface. If you would like to use something else than your system default, you can provide a full path for an alternative browser using this parameter, and hope for the best. For instance we are using this parameter to call Google's experimental browser, Canary, which performs better with demanding visualizations."/>
    <param name="read_only" type="boolean" label="Read Only" truevalue="--read-only" falsevalue="" checked="False" optional="True" argument="--read-only" help="When the interactive interface is started with this flag, all 'database write' operations will be disabled."/>
    <param name="server_only" type="boolean" label="Server Only" truevalue="--server-only" falsevalue="" checked="False" optional="True" argument="--server-only" help="The default behavior is to start the local server, and fire up a browser that connects to the server. If you have other plans, and want to start the server without calling the browser, this is the flag you need."/>
    <param name="password_protected" type="boolean" label="Password Protected" truevalue="--password-protected" falsevalue="" checked="False" optional="True" argument="--password-protected" help="If this flag is set, command line tool will ask you to enter a password and interactive interface will be only accessible after entering same password. This option is recommended for shared machines like clusters or shared networks where computers are not isolated."/>
'''

def get_parameter( param_name, arg_short, arg_long, info_dict ):

    if param_name in PARAMETER_BY_NAME:
        param = PARAMETER_BY_NAME[param_name]
    elif 'action' in info_dict and info_dict['action'] not in [ 'help', 'store' ]:
        # assert info_dict['action'] == 'store_true' # fix the error with new  code
        param = ParameterBoolean
    else:
        metavar = info_dict.get( 'metavar' )
        #pass
        #print("metavar is dan: %s, %s, %s" % ( param_name, metavar, info_dict ) )
        if metavar is None:
           pass
            # print("metavar is None: %s, %s" % ( param_name, metavar ) )
        elif metavar not in PARAMETER_BY_METAVAR:
            #print("metavar not defined for: %s, %s" % ( param_name, metavar ) )
            pass
        param = PARAMETER_BY_METAVAR.get( metavar, DEFAULT_PARAMETER )
    return param( param_name, arg_short, arg_long, info_dict )

class FakeArg( argparse_original.ArgumentParser ):
    def __init__( self, *args, **kwd ):
        self._blankenberg_args = []
        super( FakeArg, self ).__init__( *args, **kwd )

    def add_argument( self, *args, **kwd ):
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
        # print(self._blankenberg_args)
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
                #print('no metavar', name)
                pass
        return rval
    
    def blankenberg_get_params( self, params ):
        rval = []

        # for i in self._blankenberg_args:
        #     print(i)

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
                # pass
                param = params[name]
            #if 'metavar' in args[1]:
                #if args[1]['metavar'] in params:
            #        param = params[args[1]['metavar']]
            if param is None:
                if name in PARAMETER_BY_NAME:
                    param = PARAMETER_BY_NAME[name]( name, arg_short, arg_long, args[1] )
            if param is None:
                # print("Param is None")
                pass
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
        rval = "%s\n" % (rval)
        if post_cmd:
            rval = "%s\n &&\n %s" % ( rval, post_cmd )
        return rval #+ "\n && \nls -lahR" #Debug with showing directory listing in stdout
    
    def blankenberg_to_inputs( self, params ):
        rval = []
        # print(self.blankenberg_get_params( params ))
        for param in self.blankenberg_get_params( params ):
            # print(param)
            if param.name not in SKIP_PARAMETER_NAMES and param.is_input:
                # print(param.name)
                inp_xml = param.to_xml_param()
                # print(inp_xml)
                if inp_xml:
                    rval.append( inp_xml )
        # print("1061", rval)
        return rval
    
    def blankenberg_to_outputs( self, params ):
        rval = []
        for param in self.blankenberg_get_params( params ):
            if param.name not in SKIP_PARAMETER_NAMES and param.is_output:
                if param.to_xml_output() != '':
                    rval.append( param.to_xml_output() )
        # rval.append( GALAXY_ANVIO_LOG_XML )
        if len(rval) == 0:
            rval.append("<data name='output'  format='tabular' label='${tool.name} on $on_string (tabular)' from_work_dir='out.tsv'/>")
        return rval
    
def format_help(help_text):
    # Just cheat and make it a huge block quote
    #rval = "::\n" #FixMe
    rval = "\n"
    for line in help_text.split('\n'):
        rval = "%s\n  %s" % (rval, line.rstrip())
    return "%s\n\n" % (rval)

def build_tool00000(plink_text_version):
    tool_type = 'default'
    description = ''
    
    script_path = os.path.dirname(os.path.realpath(sys.argv[0]))
    asset_path = os.path.join(script_path, 'assets')
    versioned_asset_path = os.path.join(asset_path, 'versions', plink_text_version)

    with open(os.path.join(versioned_asset_path, 'info.json')) as fh:
        info = json.load(fh)
    tool_id = info.get('tool_id')
    plink_cmd = info.get('plink_cmd')
    tool_name = info.get('tool_name')
    plink_help_input_start = info.get('plink_help_input_start')
    plink_help_input_stop = info.get('plink_help_input_stop')

    with open(os.path.join(versioned_asset_path, 'help.txt')) as fh:
        plink_help = fh.read()

    # Copy&Pasted From https://www.cog-genomics.org/plink/1.9/output
    with open(os.path.join(versioned_asset_path, 'outputs.txt')) as fh:
        PLINK_OUTPUTS_TXT = fh.read()

    with open(os.path.join(asset_path, 'tool_template.txt')) as fh:
        TOOL_TEMPLATE = fh.read()