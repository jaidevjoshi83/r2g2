#!/usr/bin/env python
# -*- coding: utf-8 -*-


from rpy2.rinterface import str_typeint
from xml.sax.saxutils import quoteattr
from utils import simplify_text

def analyze_r_argument(formal_name, formal_value, input_dict_template):
    """Analyze an R function argument and determine its type and properties.
    
    Args:
        formal_name: Name of the R function parameter
        formal_value: Default value of the parameter
        input_dict_template: Template dictionary for input
        
    Returns:
        Tuple of (input_type, default_value, input_template, use_quotes, input_dict)
    """
    from template_generator import (
        optional_input_text, optional_input_integer, optional_input_boolean,
        optional_input_float, optional_input_not_determined
    )
    
    input_dict = input_dict_template.copy()
    default_value = ''
    input_type = 'text'
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
        print(f'Error analyzing R argument {formal_name}: {e}')
    
    if input_type == 'boolean':
        default_value = str((default_value.strip().lower() == 'true'))
    
    input_dict['value'] = quoteattr(default_value)
    
    return input_type, default_value, input_template, use_quotes, input_dict

def generate_r_argument_code(inp_name, input_placeholder, input_type, use_quotes):
    """Generate the R code for handling a function argument in the script.
    
    Args:
        inp_name: Original name of the R parameter
        input_placeholder: The simplified name used in Galaxy
        input_type: The type of the input
        use_quotes: Whether the value should be quoted in R
    
    Returns:
        String containing the R code snippet for this argument
    """
    if input_type == 'ellipsis':
        return '''${___USE_COMMA___}
                #set $___USE_COMMA___ = ","
                #for eli in $___ellipsis___:
                    #if str($eli.argument_type.argument_type_selector) != 'skip':
                         #set $___USE_COMMA___ = ","\n
                         #if str($eli.argument_type.argument_type_selector) == 'dataset':
                             ${eli.argument_name} = readRDS("${eli.argument_type.argument}")
                         #elif str($eli.argument_type.argument_type_selector) == 'text':
                             ${eli.argument_name} = "${eli.argument_type.argument}"
                         #elif str($eli.argument_type.argument_type_selector) == 'integer':
                             ${eli.argument_name} = ${eli.argument_type.argument}
                         #elif str($eli.argument_type.argument_type_selector) == 'float':
                             ${eli.argument_name} = ${eli.argument_type.argument}
                         #elif str($eli.argument_type.argument_type_selector) == 'boolean':
                             ${eli.argument_name} = ${eli.argument_type.argument}
                         #elif str($eli.argument_type.argument_type_selector) == 'select':
                             #raise ValueError('not implemented')
                             ${eli.argument_name} = "${eli.argument_type.argument}"
                         #elif str($eli.argument_type.argument_type_selector) == 'NULL':
                             ${eli.argument_name} = NULL
                         #end if
                     #end if
                #end for
                '''
    
    code = f'\n#if str(${input_placeholder}_type.{input_placeholder}_type_selector) == "True":\n'
    
    if input_type == 'not_determined':
        code += f'''${{___USE_COMMA___}}
                 #if str(${input_placeholder}_type.{input_placeholder}_type.{input_placeholder}_type_selector) != 'skip':
                     #set $___USE_COMMA___ = ","\n
                     #if str(${input_placeholder}_type.{input_placeholder}_type.{input_placeholder}_type_selector) == 'dataset':
                         {inp_name} = readRDS("${{{input_placeholder}_type.{input_placeholder}_type.{input_placeholder}}}")
                     #elif str(${input_placeholder}_type.{input_placeholder}_type.{input_placeholder}_type_selector) == 'text':
                         {inp_name} = "${{ {input_placeholder}_type.{input_placeholder}_type.{input_placeholder} }}"
                     #elif str(${input_placeholder}_type.{input_placeholder}_type.{input_placeholder}_type_selector) == 'integer':
                         {inp_name} = ${{ {input_placeholder}_type.{input_placeholder}_type.{input_placeholder} }}
                     #elif str(${input_placeholder}_type.{input_placeholder}_type.{input_placeholder}_type_selector) == 'float':
                         {inp_name} = ${{ {input_placeholder}_type.{input_placeholder}_type.{input_placeholder} }}
                     #elif str(${input_placeholder}_type.{input_placeholder}_type.{input_placeholder}_type_selector) == 'boolean':
                         {inp_name} = ${{ {input_placeholder}_type.{input_placeholder}_type.{input_placeholder} }}
                     #elif str(${input_placeholder}_type.{input_placeholder}_type.{input_placeholder}_type_selector) == 'select':
                         #raise ValueError('not implemented')
                         {inp_name} = "${{ {input_placeholder}_type.{input_placeholder}_type.{input_placeholder} }}"
                     #elif str(${input_placeholder}_type.{input_placeholder}_type.{input_placeholder}_type_selector) == 'NULL':
                         {inp_name} = NULL
                     #end if
                 #end if
                 '''
    elif use_quotes:
        code += f'${{___USE_COMMA___}}\n#set $___USE_COMMA___ = ","\n{inp_name} = "${{ {input_placeholder}_type.{input_placeholder} }}"'
    else:
        code += f'${{___USE_COMMA___}}\n#set $___USE_COMMA___ = ","\n{inp_name} = ${{ {input_placeholder}_type.{input_placeholder} }}'
    
    code += '\n#end if\n'
    return code
