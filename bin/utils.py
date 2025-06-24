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
