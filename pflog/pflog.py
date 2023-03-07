#!/usr/bin/env python
__version__ = '1.0.0'

from    pathlib                 import Path

import  os, sys, json
import  pudb
from    pudb.remote             import set_trace

from    concurrent.futures      import ThreadPoolExecutor
from    threading               import current_thread

from    datetime                import datetime, timezone
from    argparse                import Namespace

from    typing                  import Any

from    pftel_client            import Client
from    pftel_client.models     import log_structured, log_response
from    pftel_client.api.logger_services    import log_write_api_v1_log_post as plog
from    pftel_client.types      import Response

from    argparse                import  Namespace, ArgumentParser
from    argparse                import  RawTextHelpFormatter

from    .                       import  data

def parser_setup(str_desc) -> ArgumentParser:
    parser:ArgumentParser = ArgumentParser(
                description         = str_desc,
                formatter_class     = RawTextHelpFormatter
            )

    parser.add_argument(
                '--version',
                default = False,
                dest    = 'b_version',
                action  = 'store_true',
                help    = 'print version info'
    )
    parser.add_argument(
                '--man',
                default = False,
                action  = 'store_true',
                help    = 'show a man page'
    )
    parser.add_argument(
                '--osenv',
                default = False,
                action  = 'store_true',
                help    = 'show the base os environment'
    )
    parser.add_argument(
                '--synopsis',
                default = False,
                action  = 'store_true',
                help    = 'show a synopsis'
    )
    parser.add_argument(
                '--asyncio',
                default = False,
                action  = 'store_true',
                help    = 'use asyncio to connect to server'
    )
    parser.add_argument(
                '--detailed',
                default = False,
                action  = 'store_true',
                help    = 'provide detailed return reply'
    )
    parser.add_argument(
                '--test',
                default = False,
                action  = 'store_true',
                help    = 'call an internal test method'
    )
    parser.add_argument(
                '--inputdir',
                default = './',
                help    = 'optional directory specifying extra input-relative data'
    )
    parser.add_argument(
                '--outputdir',
                default = './',
                help    = 'optional directory specifying location of any output data'
    )
    parser.add_argument(
                '--pftelURL',
                default = '',
                help    = 'URL (including port if needed) for the pftel server'
    )
    parser.add_argument(
                '--log',
                default = '',
                help    = 'the (telemetry) message to log'
    )
    parser.add_argument(
                '--logObject',
                default = 'default',
                help    = 'the top level pftel log "object"'
    )
    parser.add_argument(
                '--logCollection',
                default = '',
                help    = 'the collection name in the pftel log "object"'
    )
    parser.add_argument(
                '--logEvent',
                default = 'event',
                help    = 'the actual "filename" (event name) to contain the log message'
    )
    parser.add_argument(
                '--appName',
                default = 'slog',
                help    = 'the appName to store in the <logEvent>'
    )
    parser.add_argument(
                '--execTime',
                default = '-1',
                help    = 'the execTime to store in the <logEvent>'
    )
    parser.add_argument(
                '--pftelUser',
                default = 'pftel',
                help    = 'pftel user login'
    )
    parser.add_argument(
                '--pftelPasswd',
                default = 'pftel1234',
                help    = 'pftel user password'
    )
    parser.add_argument(
                '--verbosity',
                default = '0',
                help    = 'verbosity level of app'
    )
    parser.add_argument(
                "--debug",
                help    = "if true, toggle telnet pudb debugging",
                dest    = 'debug',
                action  = 'store_true',
                default = False
    )
    parser.add_argument(
                "--debugTermSize",
                help    = "the terminal 'cols,rows' size for debugging",
                default = '253,62'
    )
    parser.add_argument(
                "--debugPort",
                help    = "the debugging telnet port",
                default = '7900'
    )
    parser.add_argument(
                "--debugHost",
                help    = "the debugging telnet host",
                default = '0.0.0.0'
    )
    return parser

def parser_interpret(parser, *args):
    """
    Interpret the list space of *args, or sys.argv[1:] if
    *args is empty
    """
    if len(args):
        args    = parser.parse_args(*args)
    else:
        args    = parser.parse_args(sys.argv[1:])
    return args

def parser_JSONinterpret(parser, d_JSONargs):
    """
    Interpret a JSON dictionary in lieu of CLI.
    For each <key>:<value> in the d_JSONargs, append to
    list two strings ["--<key>", "<value>"] and then
    argparse.
    """
    l_args  = []
    for k, v in d_JSONargs.items():
        if type(v) == type(True):
            if v: l_args.append('--%s' % k)
            continue
        l_args.append('--%s' % k)
        l_args.append('%s' % v)
    return parser_interpret(parser, l_args)

class Pflog:

    def env_setup(self, options: Namespace) -> bool:
        """
        Setup the environment

        Args:
            options (Namespace):    options passed from the CLI caller
        """
        status  : bool          = True
        options.inputdir        = Path(options.inputdir)
        options.outputdir       = Path(options.outputdir)
        self.env.inputdir       = options.inputdir
        self.env.outputdir      = options.outputdir
        self.env.PFTEL.url      = str(options.pftelURL)
        self.env.PFTEL.user     = str(options.pftelUser)
        self.env.PFTEL.password = str(options.pftelPasswd)
        self.env.debug_setup(
                    debug       = options.debug,
                    termsize    = options.debugTermSize,
                    port        = options.debugPort,
                    host        = options.debugHost
        )
        if not len(options.log):
            self.env.ERROR("The '--log <message>' CLI MUST be specified!")
            status              = False
        return status

    def __init__(self, options, *args, **kwargs):
        """
        constructor

        Responsible primarily for setting up the client connection
        to the pftel server.

        Possible TODO? How to check _elegantly_ on dead server?
        """
        global Env

        self.env:data.env               = data.env()
        self.options:Namespace          = options
        self.envOK:bool                 = True
        if not self.env_setup(options):
            self.env.ERROR("Env setup failure, exiting...")
            self.envOK                  = False
        else:
            self.env_show()
            self.client:Client          = Client(base_url=self.env.PFTEL.url)

    def env_show(self) -> None:
        """
        Perform some setup

        Args:
            None (internal self)

        Returns:
            None
        """

        if int(self.options.verbosity) < 4: return

        self.self.env.DEBUG("app arguments...", level = 3)
        for k,v in self.options.__dict__.items():
             self.self.env.DEBUG("%25s:  [%s]" % (k, v), level = 3)
        self.self.env.DEBUG("", level = 3)

        if self.options.osenv:
            self.self.env.DEBUG("base environment...")
            for k,v in os.environ.items():
                self.self.env.DEBUG("%25s:  [%s]" % (k, v), level = 3)
            self.self.env.DEBUG("")

    def log_bodyBuild(self) -> log_structured.LogStructured:
        """Build the log json_body

        Returns:
            log_structured.LogStructured: a structured log object
        """
        timenow         = lambda: datetime.now(timezone.utc).astimezone().isoformat()

        d_post:log_structured   = log_structured.LogStructured()
        d_post.log_object       = self.options.logObject
        d_post.log_collection   = timenow() if not len(self.options.logCollection) \
                                    else self.options.logCollection
        d_post.log_event        = self.options.logEvent
        d_post.app_name         = self.options.appName
        d_post.exec_time        = float(self.options.execTime)
        d_post.payload          = self.options.log
        return d_post

    def log_do(self) -> log_response:
        """
        Just log it!

        Returns:
            dict: the JSON return from the logging server
        """
        reply:log_response
        if not(self.options.asyncio):
            reply = plog.sync(client    = self.client,
                              json_body = self.log_bodyBuild() )
        return reply

    def run(self) -> dict:
        """
        Main entry point into the module

        Returns:
            dict: results from the registration
        """
        b_status:bool       = False
        if not self.envOK:
            return {'status': b_status}
        # pudb.set_trace()
        reply:log_response  = self.log_do()
        if reply: b_status  = True

        if int(self.options.verbosity):
            if reply:
                print(reply.message)
            else:
                print("No reply received!")

        return {
            'status'    : b_status,
            'reply'     : reply
        }

    def __call__(self, message:str, *args: Any, **kwds: Any) -> Any:
        self.options.log = message
        return self.run()