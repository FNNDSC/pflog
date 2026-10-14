"""Timing a call: the decorator, the context manager, and the open span between them.

``timed`` wraps a function; ``span_open`` wraps a block. Both note the host's facts
and the clock when the call begins, let it run, and on the way out build a ``Span``
and hand it to a reporter. The call's own outcome is not touched: its return value
comes back unchanged and an exception it raises keeps propagating, after the span
has recorded it. The outcome is read from the call the way a shell reads a program:
an integer returned or a ``SystemExit`` raised is an exit status, 0 meaning success;
a boolean is the status itself; anything else, returned without error, is success.

Key components:
    - timed: the decorator
    - span_open: the context manager
    - SpanBuilder: the open span, for adding errors or an outcome by hand
    - DEFAULT_REPORTER: where a span goes when no reporter is given

Typical usage:
    @timed("shexec")
    def main(options: Namespace, inputdir: Path, outputdir: Path) -> int:
        ...

    with span_open("convert", report=FileReporter("/out/spans.jsonl")) as span:
        ...
        span.error_add("one slice was empty")

Dependencies:
    - hostlib.facts, pflog.models, pflog.report
"""

from __future__ import annotations

import functools
import time
from collections.abc import Callable, Generator
from contextlib import contextmanager
from typing import Any, ParamSpec, TypeVar, overload

from hostlib.facts.facts import facts, timestamp_now

from pflog.models.span import Span
from pflog.report.jsonline import JsonReporter
from pflog.report.protocol import SpanReporter

P = ParamSpec("P")
R = TypeVar("R")

DEFAULT_REPORTER: SpanReporter = JsonReporter()


class SpanBuilder:
    """A span while its call is running.

    Attributes:
        name: the span's name.
        startedAt: when the call began, ISO 8601.
        errors: what has gone wrong so far, in words.
        returncode: the outcome as an exit status, once known.
        status: the outcome, once known; ``None`` until ``close``.
        span: the finished record; ``None`` until ``close``.

    Example:
        >>> builder = SpanBuilder("x")
        >>> builder.close().status
        True
    """

    def __init__(self, name: str) -> None:
        self.name: str = name
        self.startedAt: str = timestamp_now()
        self.startedClock: float = time.perf_counter()
        self.errors: list[str] = []
        self.returncode: int | None = None
        self.status: bool | None = None
        self.span: Span | None = None

    def error_add(self, text: str) -> None:
        """Note something that went wrong; the span will be a failure."""
        self.errors.append(text)
        self.status = False

    def outcome_fromValue(self, value: object) -> None:
        """Read the outcome from what the call returned.

        Args:
            value: the return value. A ``bool`` is the status; an ``int`` is an exit
                status, 0 meaning success; anything else leaves the outcome as it is.
        """
        if isinstance(value, bool):
            self.status = value and self.status is not False
        elif isinstance(value, int):
            self.returncode = value
            self.status = value == 0 and self.status is not False

    def outcome_fromExit(self, code: object) -> None:
        """Read the outcome from a ``SystemExit``'s code, as a shell would."""
        if code is None:
            self.returncode = 0
        elif isinstance(code, int):
            self.returncode = code
        else:
            self.returncode = 1
            self.errors.append(f"SystemExit: {code}")
        self.status = self.returncode == 0 and self.status is not False

    def close(self, status: bool | None = None) -> Span:
        """Finish the span.

        Args:
            status: the outcome, when the caller knows better than the builder.

        Returns:
            The record, also kept as ``span``.
        """
        if status is not None:
            self.status = status
        if self.status is None:
            self.status = not self.errors
        self.span = Span(
            name=self.name,
            status=self.status,
            returncode=self.returncode,
            errors=list(self.errors),
            host=facts(),
            startedAt=self.startedAt,
            endedAt=timestamp_now(),
            duration=round(time.perf_counter() - self.startedClock, 6),
        )
        return self.span


@contextmanager
def span_open(name: str, report: SpanReporter | None = None) -> Generator[SpanBuilder, None, None]:
    """Time a block.

    Args:
        name: the span's name.
        report: where the span goes; ``DEFAULT_REPORTER`` when ``None``.

    Yields:
        The open span, for ``error_add`` or a hand-set ``returncode``.

    Raises:
        Whatever the block raises, after the span has been reported as failed.

    Example:
        >>> from pflog.report.protocol import NullReporter
        >>> with span_open("x", NullReporter()) as span:
        ...     pass
        >>> span.span.status
        True
    """
    reporter: SpanReporter = report if report is not None else DEFAULT_REPORTER
    builder: SpanBuilder = SpanBuilder(name)
    try:
        yield builder
    except SystemExit as exit_:
        builder.outcome_fromExit(exit_.code)
        reporter.report(builder.close())
        raise
    except BaseException as err:
        builder.error_add(f"{type(err).__name__}: {err}")
        reporter.report(builder.close())
        raise
    else:
        reporter.report(builder.close())


@overload
def timed(name: Callable[P, R]) -> Callable[P, R]: ...


@overload
def timed(
    name: str | None = None, report: SpanReporter | None = None
) -> Callable[[Callable[P, R]], Callable[P, R]]: ...


def timed(name: Callable[..., Any] | str | None = None, report: SpanReporter | None = None) -> Any:
    """Time every call of a function.

    Usable bare, ``@timed``, when the function's name is the span's name, or with
    arguments, ``@timed("shexec", report=...)``.

    Args:
        name: the span's name, or the function when used bare.
        report: where each span goes; ``DEFAULT_REPORTER`` when ``None``.

    Returns:
        The function, wrapped; its return value and exceptions pass through.

    Example:
        >>> from pflog.report.protocol import NullReporter
        >>> @timed("x", NullReporter())
        ... def answer() -> int:
        ...     return 42
        >>> answer()
        42
    """

    def decorator(func: Callable[P, R], spanName: str) -> Callable[P, R]:
        @functools.wraps(func)
        def wrapped(*args: P.args, **kwargs: P.kwargs) -> R:
            with span_open(spanName, report) as builder:
                value: R = func(*args, **kwargs)
                builder.outcome_fromValue(value)
            return value

        return wrapped

    if callable(name):
        return decorator(name, name.__name__)
    spanName: str | None = name
    return lambda func: decorator(func, spanName if spanName is not None else func.__name__)
