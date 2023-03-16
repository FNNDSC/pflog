
from    pathlib    import Path

from    pflog      import pflog
import  socket
import  os
os.environ['XDG_CONFIG_HOME'] = '/tmp'
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