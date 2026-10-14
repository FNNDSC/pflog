"""Where a finished span goes.

Key components:
    - SpanReporter: the protocol
    - NullReporter, JsonReporter, FileReporter, LogReporter, TeeReporter: the reporters

Dependencies:
    - pflog.models
"""

from __future__ import annotations

from pflog.report.jsonline import FileReporter, JsonReporter
from pflog.report.log import LogReporter
from pflog.report.protocol import NullReporter, SpanReporter
from pflog.report.tee import TeeReporter

__all__: list[str] = [
    "FileReporter",
    "JsonReporter",
    "LogReporter",
    "NullReporter",
    "SpanReporter",
    "TeeReporter",
]
