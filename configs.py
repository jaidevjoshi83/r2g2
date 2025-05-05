from collections import OrderedDict

# TODO
# We can automatically retrieve the version of the installed instance of anvi'o
ANVIO_VERSION = "8"  

# Only used in realtime tool currently 
DEFAULT_CONTAINERS = ['<container type="docker">quay.io/biocontainers/anvio:7--0</container>'] 

# Default port for interactive tools
# TODO Could we automatically retrieve this?
DEFAULT_INTERACTIVE_PORT = 8080

# Skip the following tools
TOOLS_TO_SKIP = ['anvi-upgrade', 'anvi-init-bam', 'anvi-gen-variability-matrix']

# Used to generate specific tools only
ONLY_DO_TOOLS = list()

# The XML entry for the anvi'o log file
GALAXY_ANVIO_LOG_XML = '<data name="GALAXY_ANVIO_LOG" format="txt" label="${tool.name} on ${on_string}: Log"/>'

# The profile version for interactive tools only
INTERACTIVE_PROFILE_VERSION = ' profile="19.09"'

PROVIDES_TO_TOOL_TYPE = OrderedDict(interactive='interactive')
DEFAULT_TOOL_TYPE = '' # 'default' #default is not allowed by planemo lint

COLLECTION_UX_FAIL_NOTE_USER = "**NB: This requires a collection of type list for input. See https://galaxyproject.org/tutorials/collections/#a-simple-collection-example for more information.**"
COLLECTION_UX_FAIL_NOTE = "<!-- Unfortunately, we are forced to use an explicit collection input here, see e.g.: https://github.com/galaxyproject/galaxy/issues/7392 -->"
