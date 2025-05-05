from string import Template as StringTemplate
from xml.sax.saxutils import quoteattr

from configs import (
    DEFAULT_INTERACTIVE_PORT, 
    COLLECTION_UX_FAIL_NOTE_USER, 
    COLLECTION_UX_FAIL_NOTE
)


class Parameter(object):
    """The Parameter object.
    """

    _output_startswith = ('output', 'export')

    _default_default = ''

    def __init__(self, name, arg_short, arg_long, info_dict) -> "Parameter":
        """Initialize a Parameter object.

        Returns
        -------
        Parameter
            A Parameter object.
        """

        self._name = name
        self.name = name.replace("-", '_')
        self.arg_short = arg_short
        self.arg_long = arg_long
        self.info_dict = info_dict
        self.required = info_dict.get('required', False)
        self.is_output = name.lower().startswith(self._output_startswith)
        self.is_input = not self.is_output

    def copy(self, name=None, arg_short=None, arg_long=None, info_dict = None) -> "Parameter":
        """Make a copy of a Parameter obejct.

        Returns
        -------
        Parameter
            A Parameter object.
        """

        orig_dict = self.info_dict.copy()

        if info_dict:
            orig_dict.update(info_dict)

        return self.__class__(name or self.name, arg_short or self.arg_short, arg_long or self.arg_long, orig_dict)

    def get_name(self) -> str:
        """Get the Parameter name.

        Returns
        -------
        str
            The Parameter object name.
        """

        return quoteattr(self.name)

    def get_output_cmd_name(self) -> str:
        """Get the output command name.

        Returns
        -------
        str
            The Parameter object name as the output command name.
        """

        return self.name

    def get_input_cmd_name(self) -> str:
        """Get the input command name.

        Returns
        -------
        str
            The Parameter object name as the input command name.
        """

        return self.name

    def get_type(self) -> str:
        """Get the Parameter type.

        Returns
        -------
        str
            A fixed Parameter type "text".
        """

        return 'text'

    def get_label(self) -> str:
        """Get the Parameter label from its title.

        Returns
        -------
        str
            The Parameter object name as the Parameter label.
        """

        return quoteattr(self.name.replace('_', " ").title())

    def get_default(self) -> str:
        """Get the default value based on the info dict.

        Returns
        -------
        str
            The default value.
        """

        default = self.info_dict.get('default', None)

        if default is None:
            default = self._default_default

        return quoteattr(str(default))

    def get_argument(self):
        return quoteattr(self.arg_long)

    def is_positional_arg(self):
        return not (self.arg_short or self.arg_long)

    def get_arg_text(self):
        arg = self.arg_long or self.arg_short or ''

        return arg

    def get_help(self, extra: str=None):
        """Get the Parameter help string.

        Parameters
        ----------
        extra : str, default None
            Extra information to add to the help string.

        Raises
        ------
        Exception
            In case of failed help formatting.

        Returns
        -------
        str
            The help string.
        """

        class MyTemplate(StringTemplate):
            # This is a custom template to replace $ with an empty character
            # See https://stackoverflow.com/a/71270929
            delimiter = ""

        # In order to avoid the KeyError
        # Solution adapted from https://stackoverflow.com/a/71270929
        help_string = MyTemplate(self.info_dict.get('help', ''))

        try:
            help_string = help_string.safe_substitute(**self.info_dict)

        except KeyError as e:
            raise Exception('FIXME: formatting help failed').with_traceback(e.__traceback__)

        if extra:
            # Add the extra info if any
            help_string = "%s %s" % (help_string, extra)

        # There shouldn't be any new line or tab characters
        help_string = help_string.replace('\n', ' ').replace('\r', ' ').replace('\t', ' ').strip()

        while '  ' in help_string:
            # Get rid of double white spaces
            help_string = help_string.replace('  ', ' ')

        return quoteattr(help_string)

    def get_optional(self) -> bool:
        """Check whether the parameter is optional.

        Returns
        -------
        bool
            True is the Parameter object is optional, False otherwise.
        """

        if self.info_dict.get('required', False):
            return 'False'

        return 'True'

    def to_xml_param(self) -> str:
        """Define the XML code for the current Parameter object.

        Returns
        -------
        str
            The XML code for the parameter.
        """

        return """<param name=%s type="%s" label=%s value=%s optional="%s" argument=%s help=%s/>""" % \
            (
                quoteattr(self.get_input_cmd_name()), 
                self.get_type(),  
                self.get_label(), 
                self.get_default(), 
                self.get_optional(),
                self.get_argument(), 
                self.get_help()
            )

    def to_xml_output(self):
        return ''

    def get_pre_cmd_line(self):
        return ''

    def get_post_cmd_line(self):
        return ''

    def to_cmd_line(self) -> str:
        """Get the command line string.

        Returns
        -------
        str
            The command line string.
        """

        text = ''

        cmd_txt = "%s '${%s}'" % (self.get_arg_text(), self.get_input_cmd_name())

        if not self.required:
            text = """
#if $str($%s):
    %s
#end if\n""" % (self.get_input_cmd_name(), cmd_txt)

        else:
            text = "%s\n" % cmd_txt

        return text

    def __str__(self):
        return "%s\n%s\n" % (self.to_xml_param(), self.to_cmd_line())


class ParameterDiscard(Parameter):
    def get_type(self):
        return "string"

    def to_xml_param(self):
        return ''

    def to_cmd_line(self):
        return ''


class ParameterBooleanAlwaysTrue(Parameter):
    def get_type(self):
        return "boolean"

    def to_xml_param(self):
        return ''

    def to_cmd_line(self):
        return self.arg_long


class ParameterAlwaysDefault(Parameter):
    def get_type(self):
        return "text"

    def to_xml_param(self):
        return ''

    def to_cmd_line(self):
        return "%s '%s'" % (self.arg_long, self.get_default())


class ParameterAlwaysValue(Parameter):
    value = None

    def get_type(self):
        return "text"

    def to_xml_param(self):
        return ''

    def to_cmd_line(self):
        return "%s '%s'" % (self.arg_long, self.value)


class ParameterPortDefault(ParameterAlwaysValue):
    value = DEFAULT_INTERACTIVE_PORT


class ParameterBoolean(Parameter):
    _default_default = 'False'

    def get_type(self):
        return "boolean"

    def to_xml_param(self):
        return """<param name=%s type="%s" label=%s truevalue="%s" falsevalue="" checked=%s optional="%s" argument=%s help=%s/>""" % \
            (
                self.get_name(), 
                self.get_type(),  
                self.get_label(),
                self.arg_long,
                self.get_default(), 
                self.get_optional(),
                self.get_argument(), 
                self.get_help(),
            )

    def to_cmd_line(self):
        return "${%s}\n" % (self.name)


class ParameterINT(Parameter):
    def get_type(self):
        return "integer"


class ParameterFLOAT(Parameter):
    def get_type(self):
        return "float"


class ParameterNUM_CPUS(ParameterINT):
    def to_xml_param(self):
        return ''

    def to_cmd_line(self):
        return '%s "\\${GALAXY_SLOTS:-1}"\n' % (self.get_arg_text())


class ParameterFILE_PATH(Parameter):
    def __init__(self, *args, **kwd):
        super(ParameterFILE_PATH, self).__init__(*args, **kwd)

        self.multiple = False

        if self.info_dict.get('nargs', None) == '+':
            self.multiple = True

    def get_type(self):
        return "data"

    def get_format(self):
        return "txt"

    def get_multiple(self):
        return self.multiple

    def get_output_label(self):
        return quoteattr('${tool.name} on ${on_string}: %s' % (self.name.replace('_', " " ).title()))

    def to_xml_param(self):
        return """<param name=%s type="%s" label=%s format="%s" optional="%s" multiple="%s" argument=%s help=%s/>""" % \
            (
                quoteattr(self.get_input_cmd_name()), 
                self.get_type(),  
                self.get_label(), 
                self.get_format(), 
                self.get_optional(),
                self.get_multiple(),
                self.get_argument(), 
                self.get_help(),
            )

    def get_format_source(self):
        return 'format_source="input_%s"' % (self.name)

    def get_metadata_source(self):
        return 'metadata_source="input_%s"' % (self.name)

    def to_xml_output( self ):
        return """<data name=%s format="%s" %s %s label=%s/>""" % \
            (
                quoteattr(self.get_output_cmd_name()), 
                self.get_format().split(',')[0],
                self.get_format_source(),
                self.get_metadata_source(),
                self.get_output_label(),
            )

    def to_cmd_line(self):
        text = ''

        cmd_txt = "%s '${%s}'" % (self.get_arg_text(), self.get_input_cmd_name())

        if not self.required:
            text = """
#if $%s:
    %s
#end if\n""" % (self.get_input_cmd_name(), cmd_txt)

        else:
            text = "%s\n" % cmd_txt

        return text


class ParameterREPORT_FILE_PATH(ParameterFILE_PATH):
    def __init__(self, *args, **kwd):
        super(ParameterREPORT_FILE_PATH, self).__init__(*args, **kwd)

        self.is_input = False
        self.is_output = True


class ParameterDB(ParameterFILE_PATH):
    def __init__(self, *args, **kwd):
        super(ParameterDB, self).__init__(*args, **kwd)

        self.is_output = True
        self.is_input = not self.name.startswith(self._output_startswith)
        print('is_input', self.name, self.is_input)

    def get_format(self):
        return "anvio_db"

    def to_cmd_line(self):
        if self.is_input:
            return "%s '${%s}'\n" % (self.get_arg_text(), self.get_output_cmd_name())

        else:
            return "%s '%s.db'\n" % (self.get_arg_text(), self.name)

    def get_output_cmd_name(self):
        if self.is_input:
            return "output_%s" % self.name

        else:
            return self.name

    def get_input_cmd_name(self):
        if self.is_output:
            return "input_%s" % self.name

        else:
            return self.name

    def get_pre_cmd_line(self):
        text = ''

        if self.is_input:
            text = ''

            cmd_text = "cp '${%s}' '${%s}'" % (self.get_input_cmd_name(), self.get_output_cmd_name())

            if not self.required:
                text = """
    #if $%s:
        %s
    #else
        echo ''
    #end if""" % (self.get_input_cmd_name(), cmd_text)

            else:
                text = cmd_text

        return text

    def get_post_cmd_line(self):
        if not self.is_input:
            return "mv '%s.db' '${%s}'" % (self.name, self.get_output_cmd_name())

        return ''


class ParameterContigsDB(ParameterDB):
    def __init__(self, *args, **kwd):
        super(ParameterContigsDB, self).__init__(*args, **kwd)

        self.is_output = True
        self.is_input = not self.name.startswith(self._output_startswith)

        print('is_input', self.name, self.is_input)

        self.is_contigs = True
        self.is_samples = False
        self.basename = 'CONTIGS'

        if self.info_dict.get('default', None) in ['SAMPLES.db']:
            self.is_contigs = False
            self.is_samples = True
            self.basename = 'SAMPLES'

        print('is contigs', self.name, self.is_contigs)

    def get_format(self):
        if self.is_samples:
            return 'anvio_samples_db'

        if self.is_contigs:
            return "anvio_contigs_db"

        return super(ParameterContigsDB, self).get_format()

    def to_cmd_line(self):
        if not (self.is_contigs or self.is_samples):
            return super(ParameterContigsDB, self).to_cmd_line()

        if self.is_input:
            return "%s '${%s.extra_files_path}/%s.db'\n" % (self.get_arg_text(), self.get_output_cmd_name(), self.basename)

        else:
            return "%s '${%s.extra_files_path}/%s.db'\n" % (self.get_arg_text(), self.get_output_cmd_name(), self.basename)

    def get_pre_cmd_line( self ):
        if not (self.is_contigs or self.is_samples):
            return super(ParameterContigsDB, self).get_pre_cmd_line()

        text = ''

        if self.is_input:
            text = ''

            cmd_text = "cp -R '${%s.extra_files_path}' '${%s.extra_files_path}'" % (self.get_input_cmd_name(), self.get_output_cmd_name())

            if not self.required:
                text = """
    #if $%s:
        %s
    #else
        echo ''
    #end if""" % (self.get_input_cmd_name(), cmd_text)

            else:
                text = cmd_text

        else:
            text = "mkdir '${%s.extra_files_path}'\n" % (self.get_output_cmd_name())

        return text

    def get_post_cmd_line(self):
        if not (self.is_contigs or self.is_samples):
            return super(ParameterContigsDB, self).get_post_cmd_line()

        return ''


class ParameterFASTA(ParameterFILE_PATH):
    def get_format(self):
        return "fasta"


class ParameterFASTQ(ParameterFILE_PATH):
    def get_format(self):
        return "fastq"


class ParameterGENBANK(ParameterFILE_PATH):
    def get_format(self):
        return "genbank"


class ParameterVARIABILITY_TABLE(ParameterFILE_PATH):
    def get_format(self):
        return 'anvio_variability'


class ParameterClassifierFile(ParameterFILE_PATH):
    def get_format(self):
        return 'anvio_classifier'


class ParameterSVG(ParameterFILE_PATH):
    def get_format(self):
        return 'svg'


class ParameterProfileDB(ParameterDB):
    def __init__(self, *args, **kwd):
        super(ParameterProfileDB, self).__init__(*args, **kwd)

        self.is_output = True
        self.is_input = not self.name.startswith(self._output_startswith)

        print('is_input', self.name, self.is_input)

        self.basename='PROFILE'

    def get_format(self):
        return 'anvio_profile_db'

    def to_cmd_line(self):
        if self.is_input:
            return "%s '${%s.extra_files_path}/%s.db'\n" % (self.get_arg_text(), self.get_output_cmd_name(), self.basename)

        else:
            return "%s '${%s.extra_files_path}/%s.db'\n" % (self.get_arg_text(), self.get_output_cmd_name(), self.basename)

    def get_pre_cmd_line(self):
        text = ''

        if self.is_input:
            text = ''

            cmd_text = "cp -R '${%s.extra_files_path}' '${%s.extra_files_path}'" % (self.get_input_cmd_name(), self.get_output_cmd_name())

            if not self.required:
                text = """
    #if $%s:
        %s
    #else
        echo ''
    #end if""" % (self.get_input_cmd_name(), cmd_text)

            else:
                text = cmd_text

        else:
            text = "mkdir '${%s.extra_files_path}'\n" % (self.get_output_cmd_name())

        return text

    def get_post_cmd_line(self):
        return ''


class ParameterPROFILE(ParameterFILE_PATH):
    def get_format(self):
        return "anvio_profile_db"

    def to_cmd_line(self):
        text = ''

        if self.multiple:
            cmd_text = """
            #for $gxy_%s in $%s:
                %s '${gxy_%s.extra_files_path}/PROFILE.db'
            #end for
            """ % (self.name, self.name, self.get_arg_text(), self.name)

        else:
            cmd_text = "%s '${%s.extra_files_path}/PROFILE.db'" % (self.get_arg_text(), self.name)

        if not self.multiple:
            text = """
#if $%s:
    %s
#end if\n""" % (self.name, cmd_text)

        else:
            text = cmd_text

        return text


class ParameterUnknownDB(ParameterFILE_PATH):
    # TODO Should we copy the inputs to to outputs?
    def __init__(self, *args, **kwd):
        super(ParameterUnknownDB, self).__init__(*args, **kwd)

        self.is_output = True
        self.is_input = not self.name.startswith(self._output_startswith)

    def get_format(self):
        return "anvio_db"

    def get_output_cmd_name(self):
        if self.is_input:
            return "output_%s" % self.name

        else:
            return self.name

    def get_input_cmd_name(self):
        if self.is_output:
            return "input_%s" % self.name

        else:
            return self.name

    def get_base_filename(self, multiple=False):
        if multiple:
            return "${gxy_%s.metadata.anvio_basename}" % self.get_output_cmd_name()

        return "${%s.metadata.anvio_basename}" % self.get_output_cmd_name()

    def to_cmd_line(self):
        text = ''

        if self.multiple:
            cmd_text = """
            #for $gxy_%s in $%s:
                %s "${gxy_%s.extra_files_path}/%s"
            #end for
            """ % (self.get_output_cmd_name(), self.get_output_cmd_name(), self.get_arg_text(), self.get_output_cmd_name(), self.get_base_filename(multiple=True))

        else:
            cmd_text = "%s '${%s.extra_files_path}/%s'" % (self.get_arg_text(), self.get_output_cmd_name(), self.get_base_filename())

        if not self.multiple:
            text = """
#if $%s:
    %s
#end if\n""" % (self.get_output_cmd_name(), cmd_text)

        else:
            text = cmd_text

        return text

    def get_pre_cmd_line(self):
        text = ''

        if self.is_input:
            if self.multiple:
                cmd_text = """
                #for $GXY_I, ($gxy_%s, $gxy_%s) in $enumerate( $zip( $%s, $%s ) ):
                    #if $GXY_I != 0:
                        &&
                    #end if
                    cp -R '${gxy_%s.extra_files_path}' '${gxy_%s.extra_files_path}'
                #end for
                """ % (self.get_input_cmd_name(), self.get_output_cmd_name(), self.get_input_cmd_name(), self.get_output_cmd_name(), self.get_input_cmd_name(), self.get_output_cmd_name())

            else:
                cmd_text = "cp -R '${%s.extra_files_path}' '${%s.extra_files_path}'" % (self.get_input_cmd_name(), self.get_output_cmd_name())

            if not self.required:
                text = """
    #if $%s:
        %s
    #else
        echo ''
    #end if""" % (self.get_input_cmd_name(), cmd_text)

            else:
                text = cmd_text

        else:
            text = "mkdir '${%s.extra_files_path}'\n" % (self.get_output_cmd_name())

        return text

    def get_post_cmd_line(self):
        return ''

    def to_xml_param(self):
        if self.is_input and self.multiple:
            return """<param name=%s type="%s" collection_type="%s" label=%s format="%s" optional="%s" multiple="%s" argument=%s help=%s/>%s""" % \
                        (
                            quoteattr(self.get_input_cmd_name()), 
                            'data_collection'
                            'list',
                            self.get_label(), 
                            self.get_format(), 
                            self.get_optional(),
                            self.get_multiple(),
                            self.get_argument(), 
                            self.get_help(extra=COLLECTION_UX_FAIL_NOTE_USER),
                            COLLECTION_UX_FAIL_NOTE,
                        )

        return super(ParameterUnknownDB, self).to_xml_param()

    def to_xml_output(self):
        if self.is_input and self.multiple:
            return """<collection name=%s type="%s" format="%s" %s %s %s inherit_format="True" label=%s />""" % \
                (
                    quoteattr(self.get_output_cmd_name()),
                    'list',
                    self.get_format().split(',')[0],
                    self.get_format_source(),
                    self.get_metadata_source(),
                    self.get_structured_like(),
                    self.get_output_label(),
                )

        return super(ParameterUnknownDB, self).to_xml_output()

    def get_structured_like(self):
        if self.is_input and self.multiple:
            return 'structured_like="input_%s"' % (self.name)

        return ''


class ParameterGenomes(ParameterUnknownDB):
    def get_format(self):
        return "anvio_genomes_db"


class ParameterUnknownRUNINFODB(ParameterUnknownDB):
    def get_base_filename(self, multiple=False):
        return 'RUNINFO.cp'


class ParameterStructureDB(ParameterUnknownDB):
    def get_format(self):
        return "anvio_structure_db"


class ParameterPANorPROFILEDB(ParameterUnknownDB):
    # Add directory copying
    def get_format(self):
        return "anvio_profile_db,anvio_pan_db"


class ParameterPANDB(ParameterPANorPROFILEDB):
    def get_format(self):
        return "anvio_pan_db"


class ParameterPANDBDIR(ParameterPANDB):
    def get_base_filename(self, multiple=False):
        return ''


class ParameterDIR_PATH(ParameterFILE_PATH):
    def get_format(self):
        return "anvio_composite"

    def to_cmd_line(self):
        text = ''

        if self.multiple:
            cmd_text = """
            #for $gxy_%s in $%s:
                %s '${gxy_%s.extra_files_path}'
            #end for
            """ % (self.name, self.name, self.get_arg_text(), self.name)

        else:
            cmd_text = "%s '${%s.extra_files_path}'" % (self.get_arg_text(), self.name)

        if not self.multiple:
            text = """
#if $%s:
    %s
#end if\n""" % (self.name, cmd_text)

        else:
            text = cmd_text

        return text


class ParameterOutDIR_PATH(ParameterDIR_PATH):
    def __init__(self, *args, **kwd):
        super(ParameterOutDIR_PATH, self).__init__(*args, **kwd)

        self.is_output = True
        self.is_input = False


class ParameterProfileDIR_PATH(ParameterDIR_PATH):
    def get_format(self):
        return "anvio_profile_db"


class ParameterHMMProfileDIR_PATH(ParameterDIR_PATH):
    def get_format(self):
        return "anvio_hmm_profile"


class ParameterINOUTCOMPOSITE_DATA_DIR_PATH(ParameterDB):
    def __init__(self, *args, **kwd):
        super(ParameterDB, self).__init__(*args, **kwd)

        self.is_output = True
        self.is_input = True

    def get_format(self):
        return "anvio_composite"

    def to_cmd_line(self):
        if self.is_input:
            return "%s '${%s.extra_files_path}'\n" % (self.get_arg_text(), self.get_output_cmd_name())

        return "%s '${%s.extra_files_path}'\n" % (self.get_arg_text(), self.get_output_cmd_name())

    def get_pre_cmd_line(self):
        text = ''

        if self.is_input:
            text = ''

            cmd_text = "cp -R '${%s.extra_files_path}' '${%s.extra_files_path}'" % (self.get_input_cmd_name(), self.get_output_cmd_name())

            if not self.required:
                text = """
    #if $%s:
        %s
    #else
        echo ''
    #end if""" % (self.get_input_cmd_name(), cmd_text)

            else:
                text = cmd_text

        else:
            text = "mkdir '${%s.extra_files_path}'\n" % (self.get_output_cmd_name())

        return text

    def get_post_cmd_line(self):
        return ''


class ParameterCOG_DATA_DIR_PATH(ParameterINOUTCOMPOSITE_DATA_DIR_PATH):
    def get_format(self):
        return "anvio_cog_profile"


class ParameterPFAM_DATA_DIR_PATH(ParameterINOUTCOMPOSITE_DATA_DIR_PATH):
    def get_format(self):
        return "anvio_pfam_profile"


class ParameterRUNINFO_FILE(ParameterDIR_PATH):
    def to_cmd_line(self):
        text = ''

        if self.multiple:
            cmd_text = """
            #for $gxy_%s in $%s:
                %s '${gxy_%s.extra_files_path}/RUNINFO.cp'
            #end for
            """ % (self.name, self.name, self.get_arg_text(), self.name)

        else:
            cmd_text = "%s '${%s.extra_files_path}/RUNINFO.cp'" % (self.get_arg_text(), self.name)

        if not self.multiple:
            text = """
#if $%s:
    %s
#end if\n""" % (self.name, cmd_text)

        else:
            text = cmd_text

        return text


class ParamterFILENAME_PREFIX(ParameterDIR_PATH):
    def get_format(self):
        return "anvio_composite"

    def to_cmd_line(self):
        text = ''

        cmd_txt = "%s '%s'" % (self.get_arg_text(), self.name)

        if not self.required:
            text = """
#if $str( $%s ):
    %s
#end if\n""" % (self.name, cmd_txt)

        else:
            text = "%s\n" % cmd_txt

        return text

    def get_pre_cmd_line(self):
        return 'mkdir ${%s.extra_files_path}' % (self.name)

    def get_post_cmd_line(self):
        return '''( cp %s* '${%s.extra_files_path}/' || echo '' )''' % (self.name, self.name)


class ParameterFILES(ParameterFILE_PATH):
    def get_format(self):
        return "data"


class ParameterTABULAR(ParameterFILE_PATH):
    def get_format(self):
        return "tabular"


class ParameterNEWICK(ParameterFILE_PATH):
    def get_format(self):
        return "newick"


class ParameterSTATE_FILE(ParameterFILE_PATH):
    def get_format(self):
        return "anvio_state"


class ParameterINPUT_BAM(ParameterFILE_PATH):
    def get_format(self):
        return 'bam'

    def get_pre_cmd_line(self):
        text = ''

        cmd_text = "ln -s '${%s}' '%s.bam' && ln -s '${%s.metadata.bam_index}' '%s.bam.bai'" % (self.get_input_cmd_name(), self.name, self.get_input_cmd_name(), self.name)

        if not self.required:
            text = """
    #if $%s:
        %s
    #else
        echo ''
    #end if""" % (self.get_input_cmd_name(), cmd_text)

        else:
            text = cmd_text

        return text

    def to_cmd_line(self):
        text = ''

        cmd_txt = "%s '%s.bam'" % (self.get_arg_text(), self.name)

        if not self.required:
            text = """
#if $%s:
    %s
#end if\n""" % (self.get_input_cmd_name(), cmd_txt)

        else:
            text = "%s\n" % cmd_txt

        return text


class ParameterINPUT_BAMS(ParameterFILE_PATH):
    def get_format(self):
        return 'bam'

    def get_pre_cmd_line(self):
        text = ''

        cmd_text = """
        #for $gxy_i, $input_galaxy_bam in enumerate( $%s ):
        #if $gxy_i != 0:
            &&
        #end if
        ln -s '${input_galaxy_bam}' '${gxy_i}_%s.bam' && ln -s '${input_galaxy_bam.metadata.bam_index}' '${gxy_i}_%s.bam.bai'
        #end for
        """ % (self.get_input_cmd_name(), self.name, self.name)

        if not self.required:
            text = """
    #if $%s:
        %s
    #else
        echo ''
    #end if""" % (self.get_input_cmd_name(), cmd_text)

        else:
            text = cmd_text

        return text

    def to_cmd_line(self):
        text = ''

        cmd_text = """
        #for $gxy_i, $input_galaxy_bam in enumerate( $%s ):
        %s '${gxy_i}_%s.bam'
        #end for
        """ % (self.get_input_cmd_name(), self.get_arg_text(), self.name)

        if not self.required:
            text = """
#if $%s:
    %s
#end if\n""" % (self.get_input_cmd_name(), cmd_text)

        else:
            text = "%s\n" % cmd_text

        return text


class ParameterListOrFile(ParameterFILE_PATH):
    def get_conditional_name(self):
        return "%s_source" % self.name

    def get_conditional_selector_name(self):
        return "%s_source_selector" % self.name

    def get_conditional_name_q(self):
        return quoteattr(self.get_conditional_name())

    def get_conditional_selector_name_q(self):
        return quoteattr(self.get_conditional_selector_name())

    def to_xml_param(self):
        return """<conditional name=%s>
                      <param name=%s type="select" label="Use a file or list">
                          <option value="file" selected="True">Values from File</option>
                          <option value="list">Values from List</option>
                      </param>
                      <when value="file">
                          <param name=%s type="%s" label=%s format="%s" optional="%s" argument=%s help=%s/>
                      </when>
                      <when value="list">
                          <param name=%s type="text" label=%s value=%s optional="%s" argument=%s help=%s/>
                      </when>
                  </conditional>""" % \
            (
                self.get_conditional_name_q(),
                self.get_conditional_selector_name_q(),
                self.get_name(), 
                self.get_type(),  
                self.get_label(), 
                self.get_format(), 
                self.get_optional(),
                self.get_argument(), 
                self.get_help(),
                self.get_name(), 
                self.get_label(), 
                self.get_default(), 
                self.get_optional(),
                self.get_argument(), 
                self.get_help(),
            )

    def to_cmd_line(self):
        cmd_txt = "%s '${%s.%s}'" % (self.get_arg_text(), self.get_conditional_name(), self.name)

        text = """
#if $str( $%s.%s ) == "file":
    #if $%s.%s:
        %s
    #end if
#else:
    #if $str( $%s.%s ):
        %s
    #end if
#end if
""" % (self.get_conditional_name(), 
            self.get_conditional_selector_name(),
            self.get_conditional_name(), 
            self.name,
            cmd_txt,
            self.get_conditional_name(), 
            self.name,
            cmd_txt
        )

        return text
