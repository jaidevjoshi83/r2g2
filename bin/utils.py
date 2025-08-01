#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Utility functions for R2G2."""

import os
import string

SAFE_CHARS = list(x for x in string.ascii_letters + string.digits + '_')

def simplify_text(text):
    """Replace special characters with underscores for safe filenames and ids."""
    return ''.join([x if x in SAFE_CHARS else '_' for x in text])

def to_docstring(page, section_names=None):
    """
    Convert R help page to a Python docstring.
    
    Parameters:
    page: R help page object
    section_names: list of section names to consider. If None all sections are used.
    
    Returns:
    A string that can be used as a Python docstring.
    """
    if section_names is None:
        section_names = list(page.sections.keys())
        
    def walk(s, tree, depth=0):
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
        rval.append('::')
        rval.append(os.linesep)
        s = []
        walk(s, page.sections[name], depth=1)
        
        rval.append('  %s  ' % (os.linesep))
        rval.append("".join(s).replace(os.linesep, '%s  ' % (os.linesep)))
        rval.append(os.linesep)
        rval.append(os.linesep)
    return ''.join(rval).strip()

def unroll_vector_to_text(section):
    """Convert an R vector section to plain text."""
    def walk(s, tree, depth=0):
        if not isinstance(tree, str):
            for elt in tree:
                walk(s, elt, depth=depth+1)
        else:
            s.append(tree)
            s.append(' ')

    rval = []
    walk(rval, section, depth=1)
    return ''.join(rval).strip()

# Mapping of R internal type codes to their string names
SEXPTYPE_MAP = {
    0: "NILSXP",      # NULL
    1: "SYMSXP",      # Symbols
    2: "LISTSXP",     # Pairlists
    3: "CLOSXP",      # Closures (functions)
    4: "ENVSXP",      # Environments
    5: "PROMSXP",     # Promises
    6: "LANGSXP",     # Language constructs
    7: "SPECIALSXP",  # Special functions
    8: "BUILTINSXP",  # Built-in functions
    9: "CHARSXP",     # Single characters
    10: "LGLSXP",     # Logical vectors
    13: "INTSXP",     # Integer vectors
    14: "REALSXP",    # Numeric vectors
    15: "CPLXSXP",    # Complex vectors
    16: "STRSXP",     # Character vectors
    17: "DOTSXP",     # ...
    18: "ANYSXP",     # Any object
    19: "VECSXP",     # Lists
    20: "EXPRSXP",    # Expressions
    21: "BCODESXP",   # Byte code
    22: "EXTPTRSXP",  # External pointer
    23: "WEAKREFSXP", # Weak reference
    24: "RAWSXP",     # Raw bytes
    25: "S4SXP",      # S4 object
    30: "FUNSXP",     # Any function
}

# Replacement for str_typeint
def str_typeint(type_code: int) -> str:
    return SEXPTYPE_MAP.get(type_code, f"UNKNOWN_TYPE({type_code})")