# Overview 

This program generates Galaxy tool wrappers for the Anvi'o platform.

# License

This program is released as open source software under the terms of [MIT License](https://raw.githubusercontent.com/blankenberglab/tool-generator-anvio/master/LICENSE).

# Installing and using

Create and a conda environment containing anvio and jinja2
conda create -n anvio-galaxy anvio jinja2 -y && conda activate anvio-galaxy

Make a version matching git clone of anvio and change into the directory
git clone https://github.com/merenlab/anvio.git && cd anvio

Make a galaxy directory, and enter it.
mkdir galaxy && cd galaxy

Download the Galaxy tool generator script and run it
wget 'https://raw.githubusercontent.com/blankenberglab/tool-generator-anvio/master/tool-generator-anvio.py'
python tool-generator-anvio.py




# Bug reporting and feature requests

Please submit bug reports and feature requests to the issue tracker on GitHub:

[tool-generator-plink issue tracker](https://github.com/blankenberglab/tool-generator-anvio/issues)
