 ### Installation Instructions and Requirements
 
```
conda create  -n r2g2 conda-forge::rpy2=3.6.2 
conda activate r2g2
conda install r-r6=2.6.1 r-argparse=2.2.5
pip install request packaging


python=3.13
R=4.4.3

```


# R2-G2 Automatically Generates Galaxy tools on a per-function basis from any R Library

```
$ ./bin/r2g2_on_package.py --help
usage: r2g2_on_package.py [-h] --name NAME [--package_name PACKAGE_NAME]
                          [--package_version PACKAGE_VERSION] [--out OUT]
                          [--create_load_matrix_tool]
                          [--galaxy_tool_version GALAXY_TOOL_VERSION]

optional arguments:
  -h, --help            show this help message and exit
  --name NAME           Package Name
  --package_name PACKAGE_NAME
                        [Conda] Package Name
  --package_version PACKAGE_VERSION
                        [Conda] Package Version
  --out OUT             Output directory
  --create_load_matrix_tool
                        Output a tool that will create an RDS from a tabular
                        matrix
  --galaxy_tool_version GALAXY_TOOL_VERSION
                        Additional Galaxy Tool Version
```

# R2-G2 Automatically Generates Galaxy tools on R-Script based on argument parsing

```
usage: r_script/r2g2_on_r_script.py [-h] -r R_FILE_NAME [-o OUTPUT_DIR]

optional arguments:
  -h, --help            show this help message and exit
  -r R_SCRIPT_NAME, --r_script_name R_SCRIPT_NAME
                        Provide the path of an R script...
  -o OUTPUT_DIR, --output_dir OUTPUT_DIR
```


