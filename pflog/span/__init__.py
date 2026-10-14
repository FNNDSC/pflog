"""Timing a call.

Key components:
    - timed: the decorator
    - span_open: the context manager
    - SpanBuilder: the open span

Dependencies:
    - pflog.models, pflog.report
"""

from __future__ import annotations

from pflog.span.timed import DEFAULT_REPORTER, SpanBuilder, span_open, timed

__all__: list[str] = ["DEFAULT_REPORTER", "SpanBuilder", "span_open", "timed"]
