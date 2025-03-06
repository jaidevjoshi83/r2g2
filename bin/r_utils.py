#!/usr/bin/env python
# -*- coding: utf-8 -*-



import rpy2.robjects.packages as rpackages
from rpy2 import robjects
from rpy2.robjects.help import pages

def setup_r_environment():
    """Setup the R environment with necessary configuration."""
    robjects.r('''
        ctr <- 0
        dlBrowser <- function(url) {
            print(paste("Fetching", url))
            #Sys.sleep(5)
            download.file(url, destfile = paste0("./html/", ctr, ".html"), method="wget")
            ctr <- ctr + 1
            ctr
        }
        options(browser=dlBrowser)
    ''')

def get_package_info(args):
    """Get information about the R package.
    
    Args:
        args: Command line arguments
        
    Returns:
        Tuple containing (r_name, package_name, package_importr, package_version, galaxy_tool_version)
    """
    r_name = args.name
    package_name = args.package_name or r_name
    package_importr = rpackages.importr(r_name)
    package_version = args.package_version or package_importr.__version__
    galaxy_tool_version = args.galaxy_tool_version
    
    return r_name, package_name, package_importr, package_version, galaxy_tool_version

def get_r_help_pages(rname):
    """Get help pages for an R function.
    
    Args:
        rname: Name of the R function
        
    Returns:
        List of help pages
    """
    return pages(rname)
