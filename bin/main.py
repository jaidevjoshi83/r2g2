#!/usr/bin/env python
# -*- coding: utf-8 -*-



import argparse
import os
from utils import simplify_text, to_docstring, unroll_vector_to_text
from r_utils import setup_r_environment, get_package_info
from r2g2_templates import (
    generate_macro_xml,
    generate_LOAD_MATRIX_TOOL_XML,
    create_tool_xml,
    process_function_inputs
)

def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--name", help="Package Name", required=False)
    parser.add_argument("--package_name", help="[Conda] Package Name", default=None)
    parser.add_argument("--package_version", help="[Conda] Package Version", default=None)
    parser.add_argument("--out", help="Output directory", default='out')
    parser.add_argument("--create_load_matrix_tool", help="Output a tool that will create an RDS from a tabular matrix", action='store_true')
    parser.add_argument("--galaxy_tool_version", help="Additional Galaxy Tool Version", default='0.0.1')
    return parser.parse_args()

def create_output_directory(directory):
    """Create output directory if it doesn't exist."""
    try:
        os.makedirs(directory)
    except os.error:
        pass

def main():
    """Main function to run the script."""
    args = parse_arguments()
    
    # Get package information
    r_name, package_name, package_importr, package_version, galaxy_tool_version = get_package_info(args)
    
    # Setup output directory
    create_output_directory(args.out)
    
    # Generate and write macro XML
    with open(os.path.join(args.out, f"{r_name}_macros.xml"), 'w+') as out:
        out.write(generate_macro_xml(package_name, package_version, r_name, galaxy_tool_version))
    
    # Create load matrix tool if requested
    if args.create_load_matrix_tool:
        with open(os.path.join(args.out, "r_load_matrix.xml"), 'w+') as out:
            out.write(generate_LOAD_MATRIX_TOOL_XML(package_name, package_version, r_name, galaxy_tool_version))
    
    # Process package functions
    package_dict = {}
    skipped = 0
    
    for j, name in enumerate(dir(package_importr)):
        try:
            package_obj = getattr(package_importr, name)
            rname = package_obj.__rname__
            
            # Skip functions with dots in name (optional)
            if '.' in rname and False:
                print(f"Skipping: {rname}")
                skipped += 1
                continue
                
            # Create XML tool definition for this R function
            xml_dict = create_tool_xml(package_name, rname, r_name, galaxy_tool_version, package_obj)
            
            # Write the XML file
            assert rname not in package_dict, f"{rname} already exists!"
            package_dict[rname] = xml_dict
            output_file = os.path.join(args.out, f"{xml_dict['id_underscore']}.xml")
            with open(output_file, 'w+') as out:
                out.write(xml_dict['tool_xml'])
            print(f"Created: {output_file}")
            
        except Exception as e:
            print(f'Uncaught error in {j}: {name}\n{e}')
            skipped += 1
            
    print('')
    print(f'Created {len(package_dict) + int(args.create_load_matrix_tool)} tool XMLs')
    print(f'Skipped {skipped} functions')

if __name__ == "__main__":
    # Setup R environment first
    setup_r_environment()
    main()
