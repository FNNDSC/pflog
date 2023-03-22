
from    pathlib    import Path

from    pflog      import pflog
import  socket
import  os
os.environ['XDG_CONFIG_HOME'] = '/tmp'
import  time
import  pudb
from    typing      import Any
from    argparse    import Namespace

def test_pfprint() -> None:
    collection:str  = '%timestamp_chrplc|:|-_'
    IP:str          = socket.gethostbyname(socket.gethostname())
    # This test will fail if a local `pftel` server has not been started!
    pftelURL:str    = f"http://{IP}:22223/api/v1/new/{collection}/event"

    d_log:dict = pflog.pfprint(pftelURL, "hello, world!" , appName = "testApp", execTime = 2.0)
    assert d_log['status'] is True

def test_pfprint_invalidURLspec() -> None:
    # This spec is missing the /api/v1/ !
    pftelURL:str    = r'http://somehost.somewhere.com/logObject/logCollection/logEvent'
    d_log:dict = pflog.pfprint(pftelURL, "hello, world!" , appName = "testApp", execTime = 2.0)
    assert d_log['status'] is False

def test_pfprint_validSpecInvalidURL() -> None:
    # Here we have a valid spec, but the URL is invalid !
    pftelURL:str    = r'http://1.2.3.4:22/api/v1/logObject/logCollection/logEvent'
    d_log:dict = pflog.pfprint(pftelURL, "hello, world!" , appName = "testApp", execTime = 2.0)
    assert d_log['status'] is False

def testmocptelTimedNoArgsDecorator(mocker) -> None:

    mock_print:Any      = mocker.patch('builtins.print')
    @pflog.tel_logTime
    def wait(seconds:float) -> None:
        time.sleep(seconds)
    wait(2)
    assert mock_print.call_count is 1

def test_mocpftelTimed(mocker) -> None:
    """
    Send message to the moc listener with a log time
    """
    mock_print:Any  = mocker.patch('builtins.print')
    pftelURL:str    = r'https://pftel-chris-public.apps.ocp-prod.massopen.cloud/api/v1/timetest/%timestamp/analysis'

    @pflog.tel_logTime(
        pftelDB     = pftelURL,
        event       = 'test_pflog.test_mocpftelTimed',
        log         = 'A two second delay logger'
    )
    def wait(seconds:float) -> None:
        time.sleep(seconds)
    wait(2)
    assert mock_print.call_count is 2

def test_mocpftelInNamespace(mocker) -> None:
    """
    Find pftelDB from the namespace of the called function
    """
    mock_print:Any  = mocker.patch('builtins.print')
    pftelURL:str    = r'https://pftel-chris-public.apps.ocp-prod.massopen.cloud/api/v1/timetest/%timestamp/analysis'
    options: dict[str, str]         = {
        'pftelDB'   : pftelURL,
        'sleep'     : 1
    }
    @pflog.tel_logTime(
        event       = 'test_pflog.test_mocpftelInNamespace',
        log         = 'test retrieving pftelDB from function namespace arg'
    )
    def f(options) -> None:
        time.sleep(options.sleep)
    f(Namespace(**options))
    assert mock_print.call_count is 2

def test_mocNopftelInNamespace(mocker) -> None:
    """
    Test if wrapped function's namespace arg does NOT contain a pftelDB attribute
    """
    mock_print:Any  = mocker.patch('builtins.print')
    options: dict[str, str]         = {
        'sleep'     : 1
    }
    @pflog.tel_logTime(
        event       = 'test_pflog.test_mocpftelInNamespace',
        log         = 'test retrieving pftelDB from function namespace arg'
    )
    def f(options) -> None:
        time.sleep(options.sleep)
    f(Namespace(**options))
    assert mock_print.call_count is 1
