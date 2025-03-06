#!/usr/bin/env python
# -*- coding: utf-8 -*-


# R script templates
CONFIG_SPLIT_DESIRED_OUTPUTS = '''#set $include_files = str($include_outputs).split(",")'''

SAVE_R_OBJECT_TEXT = '''
#if "output_r_dataset" in $include_files:
    saveRDS(rval, file = "${output_r_dataset}", ascii = FALSE, version = 2, compress = TRUE)
#end if
'''

# Default dictionary values for input types
INPUT_NOT_DETERMINED_DICT = {
    'dataset_selected': False,
    'text_selected': False,
    'integer_selected': False,
    'float_selected': False,
    'boolean_selected': False,
    'skip_selected': False,
    'NULL_selected': False,
    'NA_selected': False
}

#  dictionary for templates
INPUT_NOT_DETERMINED_PASS_DICT = {
    'dataset_selected': "%(dataset_selected)s",
    'text_selected': "%(text_selected)s",
    'integer_selected': "%(integer_selected)s",
    'float_selected': "%(float_selected)s",
    'boolean_selected': "%(boolean_selected)s",
    'skip_selected': "%(skip_selected)s",
    'NULL_selected': "%(NULL_selected)s",
    'NA_selected': "%(NA_selected)s"
}

# Template strings for XML
XML_TEMPLATES = {
    'input_dataset': '''<param name="%(name)s" type="data" format="rds" label=%(label)s help=%(help)s/>''',
    'input_text': '''<param name="%(name)s" type="text" value=%(value)s label=%(label)s help=%(help)s/>''',
    'input_boolean': '''<param name="%(name)s" type="boolean" truevalue="TRUE" falsevalue="FALSE" checked=%(value)s label=%(label)s help=%(help)s/>''',
    'input_integer': '''<param name="%(name)s" type="integer" value=%(value)s label=%(label)s help=%(help)s/>''',
    'input_float': '''<param name="%(name)s" type="float" value=%(value)s label=%(label)s help=%(help)s/>''',
    'input_select': '''<param name="%(name)s" type="text" value=%(value)s label=%(label)s help=%(help)s/><!-- Should be select? -->'''
}

# Help section names to extract from R documentation
DEFAULT_HELP_SECTIONS = [
    'title',
    'description',
    'usage',
    'arguments',
    'details',
    'value',
    'examples',
    'see also',
    'references'
]
