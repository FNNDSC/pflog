"""Reporters that write a span as one line of JSON.

One line per span, keys sorted, no indentation: what a log collector parses without
being told the format, and what ``pflog read`` reads back. ``JsonReporter`` writes to
a stream, the process's standard error unless given one, so a program's own standard
output stays its own. ``FileReporter`` appends to a file, creating its directory.

Key components:
    - JsonReporter: one line per span to a stream
    - FileReporter: one line per span appended to a file
    - line_render: the line

Dependencies:
    - pflog.models
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import TextIO

from pflog.models.span import Span


def line_render(span: Span) -> str:
    """The span as one line of JSON, newline-terminated."""
    return span.toJson(indent=None) + "\n"


class JsonReporter:
    """Write each span as one line of JSON to a stream.

    Attributes:
        stream: where the lines go; ``None`` means the process's standard error,
            looked up at each report so a redirected stderr is honoured.

    Example:
        >>> import io
        >>> out = io.StringIO()
        >>> JsonReporter(out).report(Span("x", True, 0))
        >>> out.getvalue().startswith('{"duration": 0.0')
        True
    """

    def __init__(self, stream: TextIO | None = None) -> None:
        self.stream: TextIO | None = stream

    def report(self, span: Span) -> None:
        """Write the line and flush."""
        stream: TextIO = self.stream if self.stream is not None else sys.stderr
        stream.write(line_render(span))
        stream.flush()


class FileReporter:
    """Append each span as one line of JSON to a file.

    Attributes:
        path: the file; its directory is created on the first report.

    Example:
        >>> FileReporter("/tmp/spans.jsonl").path.name
        'spans.jsonl'
    """

    def __init__(self, path: str | Path) -> None:
        self.path: Path = Path(path)

    def report(self, span: Span) -> None:
        """Append the line."""
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a") as handle:
            handle.write(line_render(span))
