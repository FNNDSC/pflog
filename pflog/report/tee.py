"""The reporter that forwards a span to several reporters.

Key components:
    - TeeReporter: the reporter

Dependencies:
    - pflog.report.protocol
"""

from __future__ import annotations

from pflog.models.span import Span
from pflog.report.protocol import SpanReporter


class TeeReporter:
    """Report each span to every reporter given, in order.

    Attributes:
        reporters: the reporters.

    Example:
        >>> from pflog.report.protocol import NullReporter
        >>> len(TeeReporter(NullReporter(), NullReporter()).reporters)
        2
    """

    def __init__(self, *reporters: SpanReporter) -> None:
        self.reporters: tuple[SpanReporter, ...] = reporters

    def report(self, span: Span) -> None:
        """Forward."""
        for reporter in self.reporters:
            reporter.report(span)
