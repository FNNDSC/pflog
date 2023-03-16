str_about = '''
    This module is responsible for handling some state related information
    which is mostly information about the pftel server.

    Core data includes information on the server (address) as well as
    possible future WIP for authentication/etc
'''
import  os
os.environ['XDG_CONFIG_HOME'] = '/tmp'

from    pudb.remote             import set_trace
from    curses                  import meta
from    pathlib                 import Path
from    argparse                import Namespace
from    loguru                  import logger
import  pudb
import  json
import  inspect
import  sys

logger_format = (
    "<green>{time:YYYY-MM-DD HH:mm:ss}</green> │ "
    "<level>{level: <5}</level> │ "
    "<yellow>{name: >28}</yellow>::"
    "<cyan>{function: <30}</cyan> @"
    "<cyan>{line: <4}</cyan> ║ "
    "<level>{message}</level>"
)
logger.remove()
logger.add(sys.stderr, format=logger_format)

class env:
    '''
    A class that contains environmental data -- mostly information about pftel
    as well as data pertaining to the orthanc instance
    '''

    def __init__(self, *args, **kwargs):
        '''
        Constructor
        '''
        self._version   : str               = ''
        self._options   : Namespace         = None
        self._inputdir  : Path              = None
        self._outputdir : Path              = None
        self.PFTEL      : PFTEL             = PFTEL()
        self.debug      : dict              = {
            'do'        : False,
            'termsize'  : (80,25),
            'port'      : 7900,
            'host'      : '0.0.0.0'
        }

    def DEBUG(self, *args, **kwargs):
        level   : int   = 1
        for k,v in kwargs.items():
            if k == 'level' : level = v
        if int(self.options.verbosity) >= level:
            logger.opt(depth=1, colors=True).debug(*args)

    def INFO(self, *args, **kwargs):
        level   : int   = 1
        for k,v in kwargs.items():
            if k == 'level' : level = v
        if int(self.options.verbosity) >= level:
            logger.opt(depth=1, colors=True).info(*args)

    def ERROR(self, *args, **kwargs):
        level   : int   = 0
        for k,v in kwargs.items():
            if k == 'level' : level = v
        if int(self.options.verbosity) >= level:
            logger.opt(depth=1).error(*args)

    @property
    def version(self):
        return self._version

    @version.setter
    def version(self, a):
        self._version   = a

    @property
    def options(self):
        return self._options

    @options.setter
    def options(self, a):
        self._options   = a

    @property
    def inputdir(self):
        return self._inputdir

    @inputdir.setter
    def inputdir(self, a):
        self._inputdir = a
        os.chdir(self._inputdir)

    @property
    def outputdir(self):
        return self._outputdir

    @outputdir.setter
    def outputdir(self, a):
        self._outputdir = a

    def debug_setup(self, **kwargs) -> dict:
        """
        Setup the debugging structure based on <kwargs>

        Returns:
            dict: the debug structure
        """
        str_termsize    : str   = ""
        str_port        : str   = ""
        str_host        : str   = "0.0.0.0"
        b_debug         : bool  = False
        for k,v in kwargs.items():
            if k == 'debug'     :   b_debug         = v
            if k == 'termsize'  :   str_termsize    = v
            if k == 'port'      :   str_port        = v
            if k == 'host'      :   str_host        = v

        cols, rows  = str_termsize.split(',')
        self.debug['do']        = b_debug
        self.debug['termsize']  = (int(cols), int(rows))
        self.debug['port']      = int(str_port)
        self.debug['host']      = str_host
        return self.debug

    def set_telnet_trace_if_specified(self) -> None:
        """
        If specified in the env, pause for a telnet debug.

        If you are debugging, just "step" to return to the location
        in your code where you specified to break!
        """
        if self.debug['do']:
            set_trace(
                term_size   = self.debug['termsize'],
                host        = self.debug['host'],
                port        = self.debug['port']
            )

    def set_trace(self) -> None:
        """
        Simple "override" for setting a trace. If the Env is configured
        for debugging, then this set_trace will be called. Otherwise it
        will be skipped.

        This is useful for leaving debugging set_traces in the code, and
        being able to at runtime choose to debug or not.

        If you are debugging, just "step" to return to the location
        in your code where you specified to break!

        Returns:
            _type_: _description_
        """
        if self.debug['do']:
            pudb.set_trace()

class PFTEL:
    '''
    A class that contains data pertinent to a specific pftel instance
    '''

    def __init__(self, *args, **kwargs):
        self.d_pftel: dict[str, str] = {
            'user'      : '',
            'password'  : '',
            'address'   : '',
            'port'      : '',
            'route'     : '',
            'protocol'  : '',
            'url'       : ''
        }
        self.d_logSpec: dict[str, str] = {
            'logObject'     : '',
            'logCollection' : '',
            'logEvent'      : ''
        }

    @property
    def user(self) -> str:
        return self.d_pftel['user']

    @user.setter
    def user(self, a) -> None:
        self.d_pftel['user'] = a

    @property
    def password(self) -> str:
        return self.d_pftel['password']

    @password.setter
    def password(self, a) -> None:
        self.d_pftel['password'] = a

    @property
    def url(self) -> str:
        return self.d_pftel['url']

    @url.setter
    def url(self, a) -> None:
        self.d_pftel['url'] = a

    @property
    def IP(self) -> str:
        return self.d_pftel['address']

    @IP.setter
    def IP(self, a) -> None:
        self.d_pftel['address'] = a

    @property
    def port(self) -> str:
        return self.d_pftel['port']

    @port.setter
    def port(self, a) -> None:
        self.d_pftel['port'] = a

    def url_decompose(self, *args) -> dict:
        """
        Decompose a URL into its constituent parts

        Returns:
            dict: self.d_pftel
        """
        if len(args):
            self.d_pftel['url']  = args[0]

        self.d_pftel['protocol'], str_rest = self.d_pftel['url'].split('://')
        l_IPport:list[str] = str_rest.split(':')
        if len(l_IPport) == 2:
            self.d_pftel['address'], self.d_pftel['port'] = l_IPport
        else:
            self.d_pftel['address']  = l_IPport[0]
        return self.d_pftel

    def furl(self, *args):
        '''
        get/set the URL
        '''
        str_colon : str = ""
        if len(self.d_pftel['port']):
            str_colon   = ":"
        if len(args):
            self.d_pftel['url']  = args[0]
        else:
            self.d_pftel['url']  = '%s://%s%s%s%s' % (
                self.d_pftel['protocol'],
                self.d_pftel['address'],
                str_colon,
                self.d_pftel['port'],
                self.d_pftel['route']
            )
        return self.d_pftel['url']

    def user(self, *args) -> str:
        '''
        get/set the pftel user
        '''
        if len(args): self.d_pftel['user']  = args[0]
        return self.d_pftel['user']

    def password(self, *args) -> str:
        '''
        get/set the pftel user
        '''
        if len(args): self.d_pftel['password']  = args[0]
        return self.d_pftel['password']

    def set(self, str_key, str_val):
        '''
        set str_key to str_val
        '''
        if str_key in self.d_pftel.keys():
            self.d_pftel[str_key]    = str_val

    def __call__(self, str_key):
        '''
        get a value for a str_key
        '''
        if str_key in self.d_pftel.keys():
            return self.d_pftel[str_key]
        else:
            return ''
