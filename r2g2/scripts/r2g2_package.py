#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""A script to convert R library functions to Galaxy Tools."""

import argparse
import os
from r2g2.config import CONFIG_SPLIT_DESIRED_OUTPUTS, SAVE_R_OBJECT_TEXT
from r2g2.templates import (tool_xml, input_dataset, input_text, input_boolean, 
                     input_integer, input_float, input_select, 
                     input_not_determined, optional_input_dataset,
                     optional_input_text, optional_input_boolean,
                     optional_input_integer, optional_input_float,
                     optional_input_select, optional_input_not_determined,
                     ellipsis_input, INPUT_NOT_DETERMINED_DICT)
from r2g2.utils import simplify_text, to_docstring, unroll_vector_to_text, str_typeint
from r2g2.xml_generators import generate_macro_xml, generate_LOAD_MATRIX_TOOL_XML
import rpy2.robjects.packages as rpackages
from rpy2 import robjects
from rpy2.robjects.help import pages
from xml.sax.saxutils import quoteattr

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--name", help="Package Name", required=True)
    parser.add_argument("--package_name", help="[Conda] Package Name", default=None)
    parser.add_argument("--package_version", help="[Conda] Package Version", default=None)
    parser.add_argument("--out", help="Output directory", default='out')
    parser.add_argument("--create_load_matrix_tool", help="Output a tool that will create an RDS from a tabular matrix", 
                        action='store_true')
    parser.add_argument("--galaxy_tool_version", help="Additional Galaxy Tool Version", default='0.0.1')

    args = parser.parse_args()

    r_name = args.name
    package_name = args.package_name or r_name
    
    # Import the R package
    package_importr = rpackages.importr(r_name)
    package_version = args.package_version or package_importr.__version__
    galaxy_tool_version = args.galaxy_tool_version

    package_dict = {}
    skipped = 0

    # Create output directory if it doesn't exist
    try:
        os.makedirs(args.out)
    except os.error:
        pass

    # Generate macro XML file
    with open(os.path.join(args.out, f"{r_name}_macros.xml"), 'w+') as out:
        out.write(generate_macro_xml(package_name, package_version, r_name, galaxy_tool_version))

    # Generate load matrix tool if requested
    if args.create_load_matrix_tool:
        with open(os.path.join(args.out, "r_load_matrix.xml"), 'w+') as out:
            out.write(generate_LOAD_MATRIX_TOOL_XML(package_name, package_version, r_name, galaxy_tool_version))

    # Setup R browser function for downloading
    robjects.r('''
        ctr <- 0
        dlBrowser <- function(url) {
            print(paste("Fetching", url))
            download.file(url, destfile = paste0("./html/", ctr, ".html"), method="wget")
            ctr <- ctr + 1
            ctr
        }
        options(browser=dlBrowser)
    ''')

    # Process each function in the package
    for j, name in enumerate(dir(package_importr)):
        try:
            package_obj = getattr(package_importr, name)
            rname = package_obj.__rname__
            
            # Skip functions with dots in their names if needed
            if '.' in rname and False:  # Currently disabled with False
                print(f"Skipping: {rname}")
                skipped += 1
                continue
                
            # Create the XML dictionary
            xml_dict = process_function(package_obj, rname, package_name, r_name, galaxy_tool_version)
            
            # Write the tool XML file
            assert rname not in package_dict, f"{rname} already exists!"
            package_dict[rname] = xml_dict
            with open(os.path.join(args.out, f"{xml_dict['id_underscore']}.xml"), 'w+') as out:
                out.write(tool_xml % xml_dict)
            print(f"Created: {os.path.join(args.out, xml_dict['id_underscore'] + '.xml')}")
            
        except Exception as e:
            print(f'Uncaught error in {j}: {name}\n{e}')
            skipped += 1
        print(f'Processed {j}: {name}')

    print('')
    print(f'Created {len(package_dict) + int(args.create_load_matrix_tool)} tool XMLs')
    print(f'Skipped {skipped} functions')


def process_function(package_obj, rname, package_name, r_name, galaxy_tool_version):
    """Process a single R function and generate the XML dictionary for it."""
    xml_dict = {
        'package_name': package_name,
        'id': f"{package_name}_{rname}",
        'galaxy_tool_version': galaxy_tool_version,
        'name': rname,
        'description': '',
        'inputs': '',
        'rscript_content': '',
        'outputs': '',
        'help_rst': '',
        'r_name': r_name,
    }
    
    xml_dict['id_underscore'] = simplify_text(xml_dict['id'])
    xml_dict['id'] = simplify_text(xml_dict['id'])  # ToolShed doesn't like e.g. '-' in ids
    
    # Get help documentation
    help = pages(rname)
    try:
        join_char = ""
        for i, help_page in enumerate(help):
            xml_dict['help_rst'] = join_char.join([xml_dict['help_rst'], to_docstring(help_page)])
            join_char = "\n\n"
            if 'title' in list(help_page.sections.keys()) and not xml_dict['description']:
                xml_dict['description'] = unroll_vector_to_text(help_page.sections['title'])
        if i > 1:
            print(f"{rname} had multiple pages: {i}, {tuple(help)}")
    except Exception as e:
        print(f"Falling back to docstring: {rname}, {e}")
        xml_dict['help_rst'] = package_obj.__doc__
    
    # Process function parameters
    inputs, input_names = process_function_params(package_obj)
    xml_dict['inputs'] = "        %s" % ("\n        ".join(inputs))
    
    # Generate the R script content
    xml_dict['rscript_content'] = generate_r_script(rname, r_name, input_names)
    
    return xml_dict


def process_function_params(package_obj):
    """Process the parameters of an R function."""
    inputs = []
    input_names = []
    
    for i, (formal_name, formal_value) in enumerate(package_obj.formals().items()):
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
            # Extract type information from the parameter
            value_name, value_value = list(formal_value.items())[0]
            r_type = str_typeint(value_value.typeof)
            
            # Set the appropriate input type based on R type
            if r_type == 'INTSXP':
                input_type = 'integer'
                default_value = str(value_value[0])
                input_template = optional_input_integer
                use_quotes = False
                input_dict['integer_selected'] = True
                input_type = 'not_determined'
            elif r_type == 'LGLSXP':  # This seems to have caught NA...FIXME
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
            
            # Handle multiple values
            length = len(list(value_value))
            input_dict['multiple'] = (length > 1)
            
        except Exception as e:
            print(f'Error getting input param info: {e}')
        
        # Final adjustments based on input type
        if input_type == 'dataset':
            input_template = optional_input_dataset
        elif input_type == 'boolean':
            default_value = str((default_value.strip().lower() == 'true'))
        
        input_dict['value'] = quoteattr(default_value)
        input_place_name = input_dict['name']
        
        # Handle ellipsis parameter
        if formal_name in ['...']:
            print('has ... need to replace with a repeat and conditional')
            inputs.append(ellipsis_input % input_dict)
            input_names.append(('...', '___ellipsis___', 'ellipsis', False))
        else:
            inputs.append(input_template % input_dict)
            input_names.append((formal_name, input_place_name, input_type, use_quotes))
    
    return inputs, input_names


def generate_r_script(rname, r_name, input_names):
    """Generate the R script content for the tool."""
    rscript_content = f'{CONFIG_SPLIT_DESIRED_OUTPUTS}\nlibrary({r_name})\n#set $___USE_COMMA___ = ""\nrval <- {rname}('
    
    for i, (inp_name, input_placeholder, input_type, use_quotes) in enumerate(input_names):
        if input_type == 'ellipsis':
            rscript_content = f'''{rscript_content}${{___USE_COMMA___}}
                                #set $___USE_COMMA___ = ","
                                #for eli in $___ellipsis___:
                                    #if str( $eli.argument_type.argument_type_selector ) != 'skip':
                                         #set $___USE_COMMA___ = ","\n
                                         #if str( $eli.argument_type.argument_type_selector ) == 'dataset':
                                             ${{eli.argument_name}} = readRDS("${{eli.argument_type.argument}}")
                                         #elif str( $eli.argument_type.argument_type_selector ) == 'text':
                                             ${{eli.argument_name}} = "${{eli.argument_type.argument}}"
                                         #elif str( $eli.argument_type.argument_type_selector ) == 'integer':
                                             ${{eli.argument_name}} = ${{eli.argument_type.argument}}
                                         #elif str( $eli.argument_type.argument_type_selector ) == 'float':
                                             ${{eli.argument_name}} = ${{eli.argument_type.argument}}
                                         #elif str( $eli.argument_type.argument_type_selector ) == 'boolean':
                                             ${{eli.argument_name}} = ${{eli.argument_type.argument}}
                                         #elif str( $eli.argument_type.argument_type_selector ) == 'select':
                                             #raise ValueError( 'not implemented' )
                                             ${{eli.argument_name}} = "${{eli.argument_type.argument}}"
                                         #elif str( $eli.argument_type.argument_type_selector ) == 'NULL':
                                             ${{eli.argument_name}} = NULL
                                         #end if
                                     #end if
                                #end for
                                '''
        else:
            rscript_content = f'{rscript_content}\n#if str( ${input_placeholder}_type.{input_placeholder}_type_selector ) == "True":\n'
            if input_type == 'dataset':
                rscript_content = f'{rscript_content}${{___USE_COMMA___}}\n#set $___USE_COMMA___ = ","\n{inp_name} = readRDS("${{input_{input_placeholder}}}")'
            elif input_type == 'not_determined':
                rscript_content = f'''{rscript_content}${{___USE_COMMA___}}
                                     #if str( ${input_placeholder}_type.{input_placeholder}_type.{input_placeholder}_type_selector ) != 'skip':
                                         #set $___USE_COMMA___ = ","\n
                                         #if str( ${input_placeholder}_type.{input_placeholder}_type.{input_placeholder}_type_selector ) == 'dataset':
                                             {inp_name} = readRDS("${{{input_placeholder}_type.{input_placeholder}_type.{input_placeholder}}}")
                                         #elif str( ${input_placeholder}_type.{input_placeholder}_type.{input_placeholder}_type_selector ) == 'text':
                                             {inp_name} = "${{ {input_placeholder}_type.{input_placeholder}_type.{input_placeholder} }}"
                                         #elif str( ${input_placeholder}_type.{input_placeholder}_type.{input_placeholder}_type_selector ) == 'integer':
                                             {inp_name} = ${{ {input_placeholder}_type.{input_placeholder}_type.{input_placeholder} }}
                                         #elif str( ${input_placeholder}_type.{input_placeholder}_type.{input_placeholder}_type_selector ) == 'float':
                                             {inp_name} = ${{ {input_placeholder}_type.{input_placeholder}_type.{input_placeholder} }}
                                         #elif str( ${input_placeholder}_type.{input_placeholder}_type.{input_placeholder}_type_selector ) == 'boolean':
                                             {inp_name} = ${{ {input_placeholder}_type.{input_placeholder}_type.{input_placeholder} }}
                                         #elif str( ${input_placeholder}_type.{input_placeholder}_type.{input_placeholder}_type_selector ) == 'select':
                                             #raise ValueError( 'not implemented' )
                                             {inp_name} = "${{ {input_placeholder}_type.{input_placeholder}_type.{input_placeholder} }}"
                                         #elif str( ${input_placeholder}_type.{input_placeholder}_type.{input_placeholder}_type_selector ) == 'NULL':
                                             {inp_name} = NULL
                                         #end if
                                     #end if
                                     '''
            elif use_quotes:
                rscript_content = f'{rscript_content}${{___USE_COMMA___}}\n#set $___USE_COMMA___ = ","\n{inp_name} = "${{ {input_placeholder}_type.{input_placeholder} }}"'
            else:
                rscript_content = f'{rscript_content}${{___USE_COMMA___}}\n#set $___USE_COMMA___ = ","\n{inp_name} = ${{ {input_placeholder}_type.{input_placeholder} }}'
            rscript_content = f'{rscript_content}\n#end if\n'
    
    rscript_content = f'{rscript_content}\n){SAVE_R_OBJECT_TEXT}'
    return rscript_content


if __name__ == "__main__":
    main()
