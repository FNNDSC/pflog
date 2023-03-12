
from pathlib    import Path

from pflog      import pflog

import  pudb

def test_pfprint() -> None:
    # Extremely hardcoded test URL!
    testURL:str = "http://192.168.1.200:22223/api/v1/new/collection/event"

    d_log:dict = pflog.pfprint(testURL, "hello, world!" , appName = "testApp", execTime = 2.0)
    assert d_log['status'] is True

# def test_main(mocker, tmp_path: Path):
#     """
#     Simulated test run of the app.
#     """
#     inputdir = tmp_path / 'incoming'
#     outputdir = tmp_path / 'outgoing'
#     inputdir.mkdir()
#     outputdir.mkdir()

#     options = parser.parse_args(['--name', 'bar'])

#     mock_print = mocker.patch('builtins.print')
#     main(options, inputdir, outputdir)
#     mock_print.assert_called_once_with(DISPLAY_TITLE)

#     expected_output_file = outputdir / 'bar.txt'
#     assert expected_output_file.exists()
#     assert expected_output_file.read_text() == 'did nothing successfully!'

