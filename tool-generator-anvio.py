#!/usr/bin/env python3
"""A script to convert anvi'o python scripts to Galaxy tools.
"""

import argparse as argparse_original
import sys
import os

from jinja2 import Template

from configs import (
    ANVIO_VERSION,
    DEFAULT_CONTAINERS,
    DEFAULT_INTERACTIVE_PORT,
    TOOLS_TO_SKIP,
    ONLY_DO_TOOLS,
    GALAXY_ANVIO_LOG_XML,
    INTERACTIVE_PROFILE_VERSION,
    PROVIDES_TO_TOOL_TYPE,
    DEFAULT_TOOL_TYPE
)

from templates import (
    TOOL_TEMPLATE, 
    MACROS_TEMPLATE, 
    SHED_YML, 
    galaxy_tool_citation
)

from parameters import *

import anvio


DEFAULT_PARAMETER = Parameter

PARAMETER_BY_METAVAR = {
    'PROFILE_DB': ParameterProfileDB,  # ParameterPROFILE,#ParameterDB,
    'PAN_DB': ParameterPANDB,  # ParameterDB,
    'PAN_OR_PROFILE_DB': ParameterPANorPROFILEDB,  # ParameterDB,
    'DB': ParameterUnknownDB,
    'INT': ParameterINT,
    'INTEGER': ParameterINT,
    'FLOAT': ParameterFLOAT,
    'FILE_PATH': ParameterFILE_PATH,
    'FILE': ParameterFILE_PATH,
    'FASTA': ParameterFASTA,
    'LEEWAY_NTs': ParameterINT,
    'WRAP': ParameterINT,
    'NUM_SAMPLES': ParameterINT,
    #'DIR_PATH': ParameterDIR_PATH,
    'DIR_PATH': ParameterProfileDIR_PATH,  # Should this be profile, or generic anvio, probably generic anvio
    'PERCENT_IDENTITY': ParameterFLOAT,
    'GENE_CALLER_ID': ParameterINT,
    'SMTP_CONFIG_INI': ParameterFILE_PATH,
    'USERS_DATA_DIR': ParameterDIR_PATH,
    'CONTIGS_DB': ParameterContigsDB,  # ParameterDB,
    'FILE_NAME': ParameterFILE_PATH,
    'PROFILE': ParameterPROFILE,
    'SAMPLES-ORDER': ParameterTABULAR,
    'E-VALUE': ParameterFLOAT,
    'SAMPLES-INFO': ParameterTABULAR,  # ParameterDB,
    'NEWICK': ParameterNEWICK,
    'GENOME_NAMES': ParameterListOrFile,
    'RUNINFO_PATH': ParameterFILE_PATH,
    'ADDITIONAL_LAYERS': ParameterTABULAR,
    'VIEW_DATA': ParameterTABULAR,
    'GENOMES_STORAGE': ParameterGenomes,
    'BINS_INFO': ParameterTABULAR,
    'PATH': ParameterFILE_PATH,  # ParameterDIR_PATH, # Used in matrix-to-newick
    'NUM_POSITIONS': ParameterINT,
    'CONTIGS_AND_POS': ParameterTABULAR,
    'GENE-CALLS': ParameterTABULAR,
    'ADDITIONAL_VIEW': ParameterTABULAR,
    'DB_FILE_PATH': ParameterContigsDB,  # ParameterDB, # Fixme should not be contigs, is structure also, should be generic
    'SAMPLES_DB': ParameterContigsDB,  # ParameterDB,
    'NUM_CPUS': ParameterNUM_CPUS,
    'FILENAME_PREFIX': ParamterFILENAME_PREFIX,
    'RATIO': ParameterFLOAT,
    'TAB DELIMITED FILE': ParameterTABULAR,
    'INPUT_BAM': ParameterINPUT_BAM,
    'INPUT_BAM(S)': ParameterINPUT_BAMS,
    'RUNINFO_FILE': ParameterRUNINFO_FILE,
    'FILE(S)': ParameterFILES,
    'SINGLE_PROFILE(S)': ParameterPROFILE,
    'TEXT_FILE': ParameterTABULAR,
    'HMM PROFILE PATH': ParameterHMMProfileDIR_PATH,
    'NUM_THREADS': ParameterNUM_CPUS,
    'VARIABILITY_TABLE': ParameterVARIABILITY_TABLE,
    'VARIABILITY_PROFILE': ParameterVARIABILITY_TABLE,
    'STATE_FILE': ParameterSTATE_FILE,
    'DATABASE': ParameterUnknownDB,
    'STRUCTURE_DB': ParameterStructureDB,
    'BAM_FILE': ParameterINPUT_BAM,
    'REPORT_FILE_PATH': ParameterREPORT_FILE_PATH,
    'FLAT_FILE': ParameterFILE_PATH,
    'STATE': ParameterSTATE_FILE,
    'BINS_DATA': ParameterTABULAR,
    'SUMMARY_DICT': ParameterUnknownRUNINFODB,
    'LINKMER_REPORT': ParameterFILE_PATH,  # Should we add datatype? well output from anvi-report-linkmers is not datatyped due to generic metavar, so can't really
    'DB PATH': ParameterUnknownDB,
    'BAM FILE[S]': ParameterINPUT_BAMS,
    'PAN_DB_DIR': ParameterPANDBDIR,
    'DIRECTORY': ParameterDIR_PATH,
    'FASTA FILE': ParameterFASTA,
    'REPORT FILE': ParameterREPORT_FILE_PATH,
    'GENBANK': ParameterGENBANK,
    'GENBANK_METADATA': ParameterFILE_PATH,
    'OUTPUT_FASTA_TXT': ParameterFILE_PATH,
    'EMAPPER_ANNOTATION_FILE': ParameterFILE_PATH,
    'MATRIX_FILE': ParameterTABULAR,
    'CLASSIFIER_FILE': ParameterClassifierFile,
    'SAAV_FILE': ParameterTABULAR,
    'SCV_FILE': ParameterTABULAR,
    'OUTPUT_FILE': ParameterFILE_PATH,
    'CHECKM TREE': ParameterFILE_PATH,
    'CONFIG_FILE': ParameterFILE_PATH,
    'FASTA_FILE': ParameterFASTA,
    'FASTQ_FILES': ParameterFASTQ,
    'CONTIG DATABASE(S)': ParameterContigsDB,
    'IP_ADDR': ParameterDiscard,
    'DATABASE_PATH': ParameterUnknownDB,
}

PARAMETER_BY_NAME = {
    'cog-data-dir': ParameterCOG_DATA_DIR_PATH,
    'pfam-data-dir': ParameterPFAM_DATA_DIR_PATH,
    'just-do-it': ParameterBooleanAlwaysTrue,
    'temporary-dir-path': ParameterDiscard,
    'dump-dir': ParameterOutDIR_PATH,
    'full-report': ParameterREPORT_FILE_PATH,
    'port-number': ParameterPortDefault,  # TODO Read default, or set to something always? always set and then use in realtimetool
    'browser-path': ParameterDiscard,
    'server-only': ParameterBooleanAlwaysTrue,
    'password-protected': ParameterDiscard,
    'user-server-shutdown': ParameterBooleanAlwaysTrue,
    'dry-run': ParameterDiscard,
    'genes-to-add-file': ParameterFILE_PATH,
    'genes-to-remove-file': ParameterFILE_PATH,
    #'export-svg': ParameterSVG,  # Config Error: You want to export SVGs? Well, you need the Python library 'selenium' to be able               to do that but you don't have it. If you are lucky, you probably can install it                by typing 'pip install selenium' or something :/   
    'export-svg': ParameterDiscard,

}

# FIXME Make skip just reuse ParameterDiscard
SKIP_PARAMETER_NAMES = ['help', 'temporary-dir-path', 'modeller-executable', 'program', 'log-file', 'gzip-output']
#modeller-executable would allow commandline injection
#program may do same
#help is shown on screen
#temp dirs are handled by system
#log-file, is redundant with output redirect always to log
#gzip will force-add a .gz suffix
SKIP_PARAMETER_NAMES = list(map(lambda x: x.replace("-", '_'), SKIP_PARAMETER_NAMES))


def get_parameter(param_name, arg_short, arg_long, info_dict):
    if param_name in PARAMETER_BY_NAME:
        param = PARAMETER_BY_NAME[param_name]

    elif 'action' in info_dict and info_dict['action'] not in ['help', 'store']:
        assert info_dict['action'] == 'store_true'

        param = ParameterBoolean

    else:
        metavar = info_dict.get('metavar')

        print("metavar is dan: %s, %s, %s" % (param_name, metavar, info_dict))

        if metavar is None:
            print("metavar is None: %s, %s" % (param_name, metavar))

        elif metavar not in PARAMETER_BY_METAVAR:
            print("metavar not defined for: %s, %s" % (param_name, metavar))

        param = PARAMETER_BY_METAVAR.get(metavar, DEFAULT_PARAMETER)

    return param(param_name, arg_short, arg_long, info_dict)


class FakeArg(argparse_original.ArgumentParser):
    def __init__(self, *args, **kwd):
        print('init')
        print('args', args)
        print('kwd', kwd)

        self._oynaxraoret_args = list()

        super(FakeArg, self).__init__(*args, **kwd)

    def add_argument(self, *args, **kwd):
        print('add argument')
        print('args', args)
        print('kwd', kwd)

        self._oynaxraoret_args.append((args, kwd))

        super(FakeArg, self).add_argument(*args, **kwd)

    def oynaxraoret_params_by_name(self, params):
        rval = dict()  # odict()

        for args in self._oynaxraoret_args:
            name = ''

            for arg in args[0]:
                if arg.startswith('--'):
                    name = arg[2:]

                elif arg.startswith('-'):
                    if not name:
                        name = arg[1]

                else:
                    name = arg

            rval[name] = args[1]

            if 'metavar' not in args[1]:
                print('no metavar', name)

        return rval

    def oynaxraoret_get_params(self, params):
        rval = list()

        print('oynaxraoret_get_params params', params)

        for args in self._oynaxraoret_args:
            name = ''
            arg_short = ''
            arg_long = ''

            for arg in args[0]:
                if arg.startswith( '--' ):
                    name = arg[2:]
                    arg_long = arg

                elif arg.startswith( '-' ):
                    arg_short = arg

                    if not name:
                        name = arg[1:]

                elif not name:
                    name = arg

            param = None

            if name in params:
                print("%s (name) is in params" % (name))
                param = params[name]

            if param is None:
                if name in PARAMETER_BY_NAME:
                    param = PARAMETER_BY_NAME[name](name, arg_short, arg_long, args[1])

            if param is None:
                print("Param is None")

                metavar = args[1].get('metavar', None)

                print("asdf metavar", args[1], metavar)

                if metavar and metavar in PARAMETER_BY_METAVAR:
                    param = PARAMETER_BY_METAVAR[metavar](name, arg_short, arg_long, args[1])

            if param is None:
                print('no meta_var, using default', name, args[1])

                param = get_parameter(name, arg_short, arg_long, args[1])

            param = param.copy(name=name, arg_short=arg_short, arg_long=arg_long, info_dict=args[1])

            rval.append(param)

        return rval

    def oynaxraoret_to_cmd_line(self, params, filename=None):
        pre_cmd = list()
        post_cmd = list()
        rval = filename or self.prog

        for param in self.oynaxraoret_get_params(params):
            if param.name not in SKIP_PARAMETER_NAMES:
                pre = param.get_pre_cmd_line()

                if pre:
                    pre_cmd.append(pre)

                post = param.get_post_cmd_line()

                if post:
                    post_cmd.append( post )

                cmd = param.to_cmd_line()

                if cmd:
                    rval = "%s\n%s" % (rval, cmd)

        pre_cmd = "\n && \n".join(pre_cmd)
        post_cmd = "\n && \n".join(post_cmd)

        if pre_cmd:
            rval = "%s\n &&\n %s" % (pre_cmd, rval)

        rval = "%s\n&> '${GALAXY_ANVIO_LOG}'\n" % (rval)

        if post_cmd:
            rval = "%s\n &&\n %s" % (rval, post_cmd)

        return rval  #+ "\n && \nls -lahR"  # Debug with showing directory listing in stdout

    def oynaxraoret_to_inputs(self, params):
        rval = list()

        for param in self.oynaxraoret_get_params(params):
            if param.name not in SKIP_PARAMETER_NAMES and param.is_input:
                inp_xml = param.to_xml_param()

                if inp_xml:
                    rval.append(inp_xml)

        return rval

    def oynaxraoret_to_outputs(self, params):
        rval = list()

        for param in self.oynaxraoret_get_params(params):
            if param.name not in SKIP_PARAMETER_NAMES and param.is_output:
                rval.append(param.to_xml_output())

        rval.append(GALAXY_ANVIO_LOG_XML)

        return rval


def format_help(help_text):
    # Just cheat and make it a huge block quote
    rval = "::\n"

    for line in help_text.split('\n'):
        rval = "%s\n  %s" % (rval, line.rstrip())

    return "%s\n\n" % (rval)


def build_tool00000(plink_text_version):
    tool_type = 'default'
    description = ''

    script_path = os.path.dirname(os.path.realpath(sys.argv[0]))
    asset_path = os.path.join(script_path, 'assets')
    versioned_asset_path = os.path.join(asset_path, 'versions', plink_text_version)

    with open(os.path.join(versioned_asset_path, 'info.json')) as fh:
        info = json.load(fh)

    tool_id = info.get('tool_id')
    plink_cmd = info.get('plink_cmd')
    tool_name = info.get('tool_name')
    plink_help_input_start = info.get('plink_help_input_start')
    plink_help_input_stop = info.get('plink_help_input_stop')

    with open(os.path.join(versioned_asset_path, 'help.txt')) as fh:
        plink_help = fh.read()

    # Copy&Pasted From https://www.cog-genomics.org/plink/1.9/output
    with open(os.path.join(versioned_asset_path, 'outputs.txt')) as fh:
        PLINK_OUTPUTS_TXT = fh.read()

    with open(os.path.join(asset_path, 'tool_template.txt')) as fh:
        TOOL_TEMPLATE = fh.read()


def main():
    params = dict()

    for param_name, param_tup in list(anvio.D.items()):
        arguments, param_dict = param_tup
        arg_long = ''
        arg_short = ''

        for arg in arguments:
            if arg.startswith('--'):
                arg_long = arg

            else:
                arg_short = arg

        param = get_parameter(param_name, arg_short, arg_long, param_dict)
        params[param_name] = param

    outpath = os.path.join(os.curdir, 'output')

    if not os.path.exists(outpath):
        os.mkdir(outpath)

    with open(os.path.join(outpath, '.shed.yml'), 'w') as fh:
        fh.write(SHED_YML)

    scripts_outpath = os.path.join(outpath, 'scripts')

    if not os.path.exists(scripts_outpath):
        os.mkdir(scripts_outpath)

    xml_count = 0

    for read_dir, write_dir in [(os.path.join(os.curdir, '..', 'bin'), outpath), (os.path.join(os.curdir, '..', 'sandbox'), scripts_outpath)]:
        for dirpath, dirnames, filenames in os.walk(read_dir):
            for filename in sorted(filenames):
                arg_groups = list()

                if filename in TOOLS_TO_SKIP:
                    # We don't want these tools
                    continue

                if ONLY_DO_TOOLS and filename not in ONLY_DO_TOOLS:
                    print('skipping', filename)
                    continue

                with open(os.path.join(dirpath, filename), 'r') as fh:
                    input = fh.read()
                    print(filename, end=' ')

                    # FIXME
                    parser_name = 'parser'

                    if 'parent_parser' in input:
                        parser_name = 'parent_parser'

                    if input.startswith("#!/usr/bin/env python"):
                        print('python')

                        # TODO There should be a smarter way to search for single and double quotes
                        if "if __name__ == '__main__':" in input:
                            input = input.replace("if __name__ == '__main__':", "def oynaxraoret_parsing(parent_locals):\n    globals().update(parent_locals)", 1)

                        elif 'if __name__ == "__main__":' in input:
                            input = input.replace('if __name__ == "__main__":', "def oynaxraoret_parsing(parent_locals):\n    globals().update(parent_locals)", 1)

                        input = input.replace("argparse.ArgumentParser", "FakeArg")
                        input = input.replace("ArgumentParser(", "FakeArg(")

                        if not ('%s.get_args(%s)' % (parser_name, parser_name) in input or 'anvio.get_args(%s)' % (parser_name) in input or '%s.parse_args()' % (parser_name) in input or '%s.parse_known_args()' % (parser_name) in input):
                            print("ERROR: Can't find end! %s" % (filename))
                            continue

                        inp_list = input.split('\n')

                        for i, line in enumerate(inp_list):
                            if '%s.get_args(%s)' % (parser_name, parser_name) in line:
                                indent = len(line) - len(line.lstrip(' '))
                                inp_list[i] = " " * indent + "return %s" % (parser_name)  # "return parser.parse_args()"

                            if '%s.parse_args()' % (parser_name) in line:
                                indent = len(line) - len(line.lstrip(' '))
                                inp_list[i] = " " * indent + "return %s" % (parser_name)  # "return parser.parse_args()"

                            if 'anvio.get_args(%s)' % (parser_name) in line:
                                indent = len(line) - len(line.lstrip(' '))
                                inp_list[i] = " " * indent + "return %s" % (parser_name)  # "return parser.parse_args()"

                            if '%s.parse_known_args()' % (parser_name) in line:
                                indent = len(line) - len(line.lstrip(' '))
                                inp_list[i] = " " * indent + "return %s" % (parser_name)  # "return parser.parse_args()"

                            if 'import ' in line and '"' not in line and line.strip().startswith('import') and '\\' not in line:
                                indent = len(line) - len(line.lstrip(' '))
                                line2 = """%stry:
%s    %s
%sexcept Exception as e:
%s    print ('Failed import', e)
""" % (" " * indent, " " * indent, line.lstrip(' '), " " * indent, " " * indent)
                                inp_list[i] = line2

                            if 'add_argument_group' in line:
                                group_name = line.strip().split()[0]
                                arg_groups.append(group_name)

                            else:
                                for group_name in arg_groups:
                                    if group_name in line.strip().split('.'):
                                        line = line.replace(group_name, parser_name)
                                        inp_list[i] = line

                        output = '\n'.join(inp_list)
                        output = """%s
oynaxraoret_parameters = oynaxraoret_parsing(dict(locals()))""" % output
                        print(output)

                        local_dict = dict()
                        global_dict = dict()

                        sys.argv[0] = filename  # anvio will do introspection to get prog name to build help, etc
                        exec(output, globals(), local_dict)
                        oynaxraoret_parameters = local_dict.get('oynaxraoret_parameters')

                        print('oynaxraoret_parameters', oynaxraoret_parameters)
                        print(dir(oynaxraoret_parameters))
                        print('desc', oynaxraoret_parameters.description)

                        __provides__ = local_dict.get('__provides__', list())

                        print('_oynaxraoret_args', oynaxraoret_parameters._oynaxraoret_args)

                        print('oynaxraoret_get_params', oynaxraoret_parameters.oynaxraoret_get_params(params))

                        print('__provides__ %s' % __provides__)

                        tool_type = DEFAULT_TOOL_TYPE

                        for provides, ttype in PROVIDES_TO_TOOL_TYPE.items():
                            if provides in __provides__:
                                tool_type = ttype
                                break

                        if tool_type == 'interactive':
                            containers = DEFAULT_CONTAINERS
                            # TODO: grab port from args, right now setting all to 8080
                            #ports = ['<port name="%s server" type="tcp">%s</port>' % (filename, DEFAULT_INTERACTIVE_PORT)]

                            realtime = [dict(
                                            name="%s server" % (filename),
                                            port=DEFAULT_INTERACTIVE_PORT,
                                            url=None
                                        )]

                            profile = INTERACTIVE_PROFILE_VERSION
                            print("%s is an InteractiveTool." % (filename))

                        else:
                            containers = list()
                            realtime = None
                            profile = ''

                        if tool_type:
                            tool_type=' tool_type="%s"' % (tool_type)

                        template_dict = {
                            'id': filename.replace('-', '_'),
                            'tool_type': tool_type,
                            'profile': profile,
                            'name': filename,
                            'version': ANVIO_VERSION,
                            'description': oynaxraoret_parameters.description,
                            #'macros': None,
                            'version_command': '%s --version' % filename,
                            'requirements': ['<requirement type="package" version="%s">anvio</requirement>' % ANVIO_VERSION],
                            'containers': containers,
                            'realtime': realtime,
                            'command': oynaxraoret_parameters.oynaxraoret_to_cmd_line(params, filename),
                            'inputs': oynaxraoret_parameters.oynaxraoret_to_inputs(params),
                            'outputs': oynaxraoret_parameters.oynaxraoret_to_outputs(params),
                            #'tests': None,
                            #'tests': { output:'' },
                            'help': format_help(oynaxraoret_parameters.format_help().replace(os.path.basename(__file__), filename)),
                            'doi': ['10.7717/peerj.1319'],
                            'bibtex_citations': [galaxy_tool_citation]
                        }

                        print('template_dict', template_dict)

                        tool_xml = Template(TOOL_TEMPLATE).render(**template_dict)
                        print('tool_xml', tool_xml)

                        with open(os.path.join (write_dir, "%s.xml" % filename), 'w') as out:
                            out.write(tool_xml)
                            xml_count += 1

                    else:
                        print('not python')

    print("Created %i anvi'o Galaxy tools." % (xml_count))


if __name__ == '__main__':
    main()