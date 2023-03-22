#!/usr/bin/env python
import os
os.environ['XDG_CONFIG_HOME'] = '/tmp'
import pudb

try:
    from    .                   import pflog
except:
    from pflog                  import pflog

from    pathlib                 import Path
from    argparse                import ArgumentParser,                  \
                                       Namespace,                       \
                                       ArgumentDefaultsHelpFormatter,   \
                                       RawTextHelpFormatter

from importlib.metadata import Distribution

__pkg       = Distribution.from_name(__package__)
__version__ = __pkg.version

import  sys, json
import  pudb
from    pudb.remote             import set_trace
from    pflog.pflog             import parser_setup, parser_interpret, parser_JSONinterpret


DISPLAY_TITLE = r"""

        __ _
       / _| |
 _ __ | |_| | ___   __ _
| '_ \|  _| |/ _ \ / _` |
| |_) | | | | (_) | (_| |
| .__/|_| |_|\___/ \__, |
| |                 __/ |
|_|                |___/
"""

str_desc: str                =  DISPLAY_TITLE + """

                        -- version """ + __version__ + """ --

        A logging client to a pftel telemetry server. This package provides
        both a CLI client as well as a python module.


"""

package_CLIself         = """
        --pftelURL <pftelURL> | --pftelDB <URLDBpath>                           \\
        --log <logMessage>                                                      \\
        [--asyncio]                                                             \\
        [--detailed]                                                            \\
        [--test]                                                                \\
        [--logObject <logObjectInPTFEL>]                                        \\
        [--logCollection <logCollectionInPFTEL>]                                \\
        [--logEvent <logEventInPFTEL>]                                          \\
        [--appName <appName>]                                                   \\
        [--execTime <execTime>]                                                 \\
        [--pftelUser <user>]                                                    \\
        [--pftelPasswd <password>]                                              \\
        [--inputdir <inputdir>]                                                 \\
        [--outputdir <outputdir>]                                               \\
        [--man]                                                                 \\
        [--verbosity <level>]                                                   \\
        [--debug]                                                               \\
        [--debugTermsize <cols,rows>]                                           \\
        [--debugHost <0.0.0.0>]                                                 \\
        [--debugPort <7900>]"""

package_CLIsynpsisArgs = """
    ARGUMENTS

        --pftelURL <pftelURL> | --pftelDB <URLDBpath>
        The URL of the pftel instance. Typically:

                --pftelURL http://some.location.somewhere:22223

        either this or '--pftelDB' MUST be specified. See below for --pftelDB.

        --log <logMessage>
        The actual message to log. Use quotes to protect messages that
        contain spaces:

                --log "Hello, world!"

        [--logObject <logObjectInPTFEL>] "default"
        [--logCollection <logCollectionInPFTEL>] `timestamp`
        [--logEvent <logEventInPFTEL>] "event"
        [--appName <appName>]
        [--execTime <execTime>]
        Logs are stored within the pftel database in

            `{logObjectInPFTEL}`/`{logCollectionInPFTEL}`/`{logEventInPFTEL}`

        if not specified, use defaults as shown. The <appName> and <execTime>
        are stored within the <logEventInPFTEL>.

        [--pftelDB <DBURLpath>]
        This is an alternate CLI that specifies a DB POST URL:

            --pftelDB   <URLpath>/<logObject>/<logCollection>/<logEvent>

        for example

            --pftelDB http://localhost:22223/api/v1/weather/massachusetts/boston

        Indirect parsing of each of the object, collection, event strings is
        available through `pftag` so any embedded pftag SGML is supported. So

            http://localhost:22223/api/vi/%platform/%timestamp_strmsk|**********_/%name

        would be parsed to, for example:

            http://localhost:22223/api/vi/Linux/2023-03-11/posix

        [--asyncio]
        If specified, use asyncio, else do sync calls.

        [--detailed]
        If specified, return detailed responses from the server.

        [--test]
        If specified, run a small internal test on multi-logger calls.

        [--pftelUser <user>] ("chris")
        The name of the pftel user. Reserved for future use.

        [--inputdir <inputdir>]
        An optional input directory specifier. Reserverd for future use.

        [--outputdir <outputdir>]
        An optional output directory specifier. Reserved for future use.

        [--man]
        If specified, show this help page and quit.

        [--verbosity <level>]
        Set the verbosity level. The app is currently chatty at level 0 and level 1
        provides even more information.

        [--debug]
        If specified, toggle internal debugging. This will break at any breakpoints
        specified with 'Env.set_trace()'

        [--debugTermsize <253,62>]
        Debugging is via telnet session. This specifies the <cols>,<rows> size of
        the terminal.

        [--debugHost <0.0.0.0>]
        Debugging is via telnet session. This specifies the host to which to connect.

        [--debugPort <7900>]
        Debugging is via telnet session. This specifies the port on which the telnet
        session is listening.
"""

package_CLIexample = """
    BRIEF EXAMPLE

        pflog                                                                   \\
            --pftelURL http://192.168.1.200:22223                               \\
            --log "Hello from the python client"                                \\
            --logObject test                                                    \\
            --logEvent test-run

   or with docker:

        docker run --rm --name pflog fnndsc/pflog                               \\
        pflog                                                                   \\
            --pftelURL http://192.168.1.200:22223                               \\
            --log "Hello from the python client"                                \\
            --logObject test                                                    \\
            --logEvent test-run

"""

def synopsis(ab_shortOnly = False):
    scriptName = os.path.basename(sys.argv[0])
    shortSynopsis =  '''
    NAME

        pflog

    SYNOPSIS

        pflog                                                               \ '''\
        + package_CLIself + '''

    '''

    description = '''
    DESCRIPTION

        `pflog` is both a script and python module for transmitting log
        (or telemetry) events to a pftel server.

    ''' + package_CLIsynpsisArgs + package_CLIexample
    if ab_shortOnly:
        return shortSynopsis
    else:
        return shortSynopsis + description

parser                  = ArgumentParser(
    description         = '''
A client for logging to a pftel server
''',
    formatter_class     = RawTextHelpFormatter
)

def earlyExit_check(args) -> int:
    """
    Perform some preliminary checks

    If version or synospis are requested, print these and return
    code for early exit.
    """
    str_help:str = ''
    if args.man or args.synopsis:
        print(str_desc)
        if args.man:
            str_help     = synopsis(False)
        else:
            str_help     = synopsis(True)
        print(str_help)
        return 1
    if args.b_version:
        print("Name:    %s\nVersion: %s" % (__pkg.name, __version__))
        return 1
    if int(args.verbosity) > 1: print(DISPLAY_TITLE)
    return 0

def test_multi(options:Namespace, logger:pflog.Pflog) -> None:
    # If you wanted to reuse this logger with a new message, simply just
    # call it again with the message in the arglist -- be aware of the
    # implications this has in the pftel database -- the location of
    # these new messages will depend on the patten of
    # <logObject>/<logCollection>/<logEvent>
    logger("Here is another message")
    logger("And another!")

    # Here we create another logger without the CLI parser, but a JSON
    # object.
    tlog:pflog.Pflog        = pflog.Pflog( {
            'log'           : 'Hello from tlog!',
            'pftelURL'      : options.pftelURL,
            'logObject'     : 'test-feed',
            'logCollection' : 'run1',
            'verbosity'     : options.verbosity
        }
    )
    d_tlog:dict             = tlog.run()

def main(argv=None) -> int:
    """
    Main method for the programmatical calling the pflog
    module
    """

    # Call the following to collect the logger Namespace
    # and then edit values in the options:Namespace if needed
    parser:ArgumentParser   = parser_setup('A client for logging to a pftel server')
    options:Namespace       = parser_interpret(parser)

    # any reason we should not continue?
    if earlyExit_check(options): return 1

    # set_trace(term_size=(253, 62), host = '0.0.0.0', port = 7900)

    logger:pflog.Pflog      = pflog.Pflog(options)
    d_pflog:dict            = logger.run()

    return 0 if d_pflog['status'] else 2

if __name__ == '__main__':
    sys.exit(main(sys.argv))
