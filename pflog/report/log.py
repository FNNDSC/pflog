"""The reporter that writes a span through Python's logging.

One record per span, at one level, on one logger: ``name: 4.213 s, ok`` or
``name: 0.004 s, failed: ValueError: bad input``. For a program that already
configures logging and wants spans in the same stream.

Key components:
    - LogReporter: the reporter
    - line_render: the message

Dependencies:
    - pflog.models
"""

from __future__ import annotations

import logging

from pflog.models.span import Span


def line_render(span: Span) -> str:
    """The span as a log message."""
    outcome: str = "ok" if span.status else "failed"
    if span.errors:
        outcome += ": " + "; ".join(span.errors)
    return f"{span.name}: {span.duration:.3f} s, {outcome}"


class LogReporter:
    """Log each span.

    Attributes:
        logger: the logger; ``pflog`` unless given.
        level: the level; INFO unless given.

    Example:
        >>> LogReporter().logger.name
        'pflog'
    """

    def __init__(self, logger: logging.Logger | None = None, level: int = logging.INFO) -> None:
        self.logger: logging.Logger = logger if logger is not None else logging.getLogger("pflog")
        self.level: int = level

    def report(self, span: Span) -> None:
        """Log the message."""
        self.logger.log(self.level, line_render(span))
