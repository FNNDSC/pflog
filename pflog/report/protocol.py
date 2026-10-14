"""What a reporter is: where a finished span goes.

A reporter receives each span as it closes. ``SpanReporter`` is the structural type;
``NullReporter`` discards.

Key components:
    - SpanReporter: the protocol
    - NullReporter: discards every span

Dependencies:
    - pflog.models
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from pflog.models.span import Span


@runtime_checkable
class SpanReporter(Protocol):
    """Where a finished span goes."""

    def report(self, span: Span) -> None:
        """A span has closed.

        Args:
            span: its record.
        """


class NullReporter:
    """Discard every span.

    Example:
        >>> isinstance(NullReporter(), SpanReporter)
        True
    """

    def report(self, span: Span) -> None:
        """Discard."""
