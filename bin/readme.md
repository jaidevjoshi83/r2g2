# R2G2: R to Galaxy Tool Generator

R2G2 is a tool for automatically converting R library functions to Galaxy Tools.

## Project Structure

The project is organized into the following Python modules:

- `main.py`: The main script that orchestrates the conversion process
- `utils.py`: Utility functions for text processing and help documentation
- `templates.py`: Templates for Galaxy tool XML components
- `config.py`: Configuration settings and constants
- `xml_generators.py`: Functions to generate various XML files

## Usage

```bash
python main.py --name <r_package_name> [OPTIONS]
```

### Command-line Options

- `--name`: R package name (required)
- `--package_name`: Conda package name (defaults to R package name)
- `--package_version`: Conda package version (defaults to R package version)
- `--out`: Output directory (defaults to 'out')
- `--create_load_matrix_tool`: Generate a tool for loading tabular data into R (optional)
- `--galaxy_tool_version`: Additional Galaxy tool version (defaults to '0.0.1')

## Output

The tool generates the following files in the output directory:

1. A macro XML file (`<r_name>_macros.xml`) with common configurations
2. Individual tool XML files for each R function
3. Optionally, a matrix loader tool XML file (`r_load_matrix.xml`)

## Requirements

- Python 3.6+
- rpy2 Python package
- An R installation with the target package installed

## Example

```bash
python main.py --name vegan --out vegan_tools --create_load_matrix_tool --galaxy_tool_version 1.0.0
```

This command will:
1. Convert all functions from the R package 'vegan' to Galaxy tools
2. Create a tool for loading tabular data into R
3. Save all files in the 'vegan_tools' directory
4. Set the Galaxy tool version to 1.0.0

## Notes

- Functions with periods in their names can be skipped by enabling the conditional check
- The tool handles various R parameter types (integer, boolean, string, etc.)
- Special cases like ellipsis parameters (`...`) are handled with repeats and conditionals
