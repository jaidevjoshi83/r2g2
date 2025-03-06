#!/usr/bin/env python
# -*- coding: utf-8 -*-



package_name = None
package_version = None
r_name = None
galaxy_tool_version = None


CONFIG_SPLIT_DESIRED_OUTPUTS = '''#set $include_files = str( $include_outputs ).split( "," )'''

# Template code for saving R objects
SAVE_R_OBJECT_TEXT = '''
#if "output_r_dataset" in $include_files:
    saveRDS(rval, file = "${output_r_dataset}", ascii = FALSE, version = 2, compress = TRUE )
#end if
'''
