class FakeArg( argparse_original.ArgumentParser ):
    def __init__( self, *args, **kwd ):
        print('init')

        self._blankenberg_args = []
        super( FakeArg, self ).__init__( *args, **kwd )

    def add_argument( self, *args, **kwd ):
        # print('add argument')
        # print("##############################, 1248")
        # # print('args', args)
        # # print('kwd', kwd)
        # print("############################## 1251")
        self._blankenberg_args.append( ( args, kwd ) )
        super( FakeArg, self ).add_argument( *args, **kwd )

    #def add_argument_group( self, *args, **kwd ):
    #    #cheat and return self, no groups!
    #    print 'arg group'
    #    print 'args', args
    #    print 'kwd', kwd
    #    return self

    def blankenberg_params_by_name( self, params ):
        rval = {}#odict()
        for args in self._blankenberg_args:
            name = ''
            for arg in args[0]:
                if arg.startswith( '--' ):
                    name = arg[2:]
                elif arg.startswith( '-'):
                    if not name:
                        name = arg[1]
                else:
                    name = arg
            rval[name] = args[1]
            if 'metavar' not in args[1]:
                print('no metavar', name)
        return rval
    def blankenberg_get_params( self, params ):
        rval = []
        # print('blankenberg_get_params params', params)
        for args in self._blankenberg_args:
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
                print("%s (name) is in params" % (name) )
                param = params[name]
            #if 'metavar' in args[1]:
                #if args[1]['metavar'] in params:
            #        param = params[args[1]['metavar']]
            if param is None:
                if name in PARAMETER_BY_NAME:
                    param = PARAMETER_BY_NAME[name]( name, arg_short, arg_long, args[1] )
            if param is None:
                print("Param is None")
                metavar = args[1].get( 'metavar', None )
                # print("asdf metavar",args[1],metavar)
                if metavar and metavar in PARAMETER_BY_METAVAR:
                    param = PARAMETER_BY_METAVAR[metavar]( name, arg_short, arg_long, args[1] )
            if param is None:
                # print('no meta_var, using default', name, args[1])
                #param = DEFAULT_PARAMETER( name, arg_short, arg_long, args[1] )
                param = get_parameter( name, arg_short, arg_long, args[1] )

            #print 'before copy', param.name, type(param)
            param = param.copy( name=name, arg_short=arg_short, arg_long=arg_long, info_dict=args[1] )
            #print 'after copy', type(param)
            rval.append(param)
        return rval
    def blankenberg_to_cmd_line( self, params, filename=None ):
        pre_cmd = []
        post_cmd = []
        rval = filename or self.prog
        for param in self.blankenberg_get_params( params ):
            if param.name not in SKIP_PARAMETER_NAMES:
                pre = param.get_pre_cmd_line()
                if pre:
                    pre_cmd.append( pre )
                post = param.get_post_cmd_line()
                if post:
                    post_cmd.append( post )
                cmd = param.to_cmd_line()
                if cmd:
                    rval = "%s\n%s" % ( rval, cmd )
        pre_cmd = "\n && \n".join( pre_cmd )
        post_cmd = "\n && \n".join( post_cmd )
        if pre_cmd:
            rval = "%s\n &&\n %s" % ( pre_cmd, rval )
        rval = "%s\n&> '${GALAXY_ANVIO_LOG}'\n" % (rval)
        if post_cmd:
            rval = "%s\n &&\n %s" % ( rval, post_cmd )
        return rval #+ "\n && \nls -lahR" #Debug with showing directory listing in stdout
    def blankenberg_to_inputs( self, params ):
        rval = []
        for param in self.blankenberg_get_params( params ):
            if param.name not in SKIP_PARAMETER_NAMES and param.is_input:
                inp_xml = param.to_xml_param()
                if inp_xml:
                    rval.append( inp_xml )
        return rval
    def blankenberg_to_outputs( self, params ):
        rval = []
        for param in self.blankenberg_get_params( params ):
            if param.name not in SKIP_PARAMETER_NAMES and param.is_output:
                rval.append( param.to_xml_output() )
        rval.append( GALAXY_ANVIO_LOG_XML )
        return rval