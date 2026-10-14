"""pflog: time a call and keep the record.

A span around any function or block, built on hostlib's records, reported as one
line of JSON.

Key components:
    - timed, span_open: time a function or a block
    - Span: the record
    - JsonReporter, FileReporter, LogReporter, TeeReporter, NullReporter: where it goes
    - HostFacts, JobResult, JobSpec: hostlib's records, re-exported

Typical usage:
    from pflog import timed

    @timed("shexec")
    def main(options, inputdir, outputdir) -> int:
        ...

Dependencies:
    - hostlib
"""

from __future__ import annotations

from pflog.models import HostFacts, JobLogs, JobResult, JobSpec, JobStarted, Span
from pflog.report import FileReporter, JsonReporter, LogReporter, NullReporter, SpanReporter, TeeReporter
from pflog.span import SpanBuilder, span_open, timed

__version__: str = "2.0.0"

__all__: list[str] = [
    "FileReporter",
    "HostFacts",
    "JobLogs",
    "JobResult",
    "JobSpec",
    "JobStarted",
    "JsonReporter",
    "LogReporter",
    "NullReporter",
    "Span",
    "SpanBuilder",
    "SpanReporter",
    "TeeReporter",
    "__version__",
    "span_open",
    "timed",
]
