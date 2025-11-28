from setuptools import setup, find_packages

setup(
    name="r2g2",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "rpy2>=3.6.1",
        "jinja2"
    ],
    entry_points={
        'console_scripts': [
            'r2g2-package=r2g2.scripts.r2g2_package:main',
            'r2g2-script=r2g2.scripts.r2g2_script:run_main',
        ],
    },
    author="Jayadev Joshi",
    description="A tool to convert R scripts and packages to Galaxy wrappers",
)
