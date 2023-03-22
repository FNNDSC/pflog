
from    pathlib    import Path

from    pflog      import pflog
import  socket
import  os
os.environ['XDG_CONFIG_HOME'] = '/tmp'
import  time
import  pudb

def test_pfprint() -> None:
    collection:str  = '%timestamp_chrplc|:|-_'
    IP:str          = socket.gethostbyname(socket.gethostname())
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

def test_mocpftelTimed() -> None:
    """
    Send message to the moc listener with a log time
    """
    pudb.set_trace()
    pftelURL:str    = r' https://pftel-chris-public.apps.ocp-prod.massopen.cloud/api/v1/timetest/%timestamp/analysis'
    @pflog.tel_logTime(
        someother   = 'something',
        pftelDB     = pftelURL,
        name        = 'pytest',
        log         = 'A two second delay logger',
        isthis      = pftelURL
    )
    # @pflog.tel_logTime
    def wait(seconds:float):
        time.sleep(seconds)
    wait(2)
    assert True     == True

