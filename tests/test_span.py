"""timed and span_open: outcomes, pass-through, failure, reporting."""

from __future__ import annotations

import time

import pytest

from pflog.models import Span
from pflog.span import SpanBuilder, span_open, timed


class Keep:
    """A reporter that keeps every span."""

    def __init__(self) -> None:
        self.spans: list[Span] = []

    def report(self, span: Span) -> None:
        self.spans.append(span)


def test_timed_passesValueThrough_andTimes() -> None:
    keep = Keep()

    @timed("wait", keep)
    def wait(seconds: float) -> str:
        time.sleep(seconds)
        return "done"

    assert wait(0.05) == "done"
    assert len(keep.spans) == 1
    span: Span = keep.spans[0]
    assert span.name == "wait" and span.status is True and span.returncode is None
    assert span.duration >= 0.05 and span.startedAt and span.endedAt and span.host.pid > 0


def test_timed_bare_usesFunctionName() -> None:
    keep = Keep()

    @timed
    def plain() -> None:
        pass

    plain()
    assert keep.spans == []  # bare form reports to the default reporter, not ours


def test_timed_intReturn_isExitStatus() -> None:
    keep = Keep()

    @timed("main", keep)
    def main(code: int) -> int:
        return code

    assert main(0) == 0 and keep.spans[-1].status is True and keep.spans[-1].returncode == 0
    assert main(3) == 3 and keep.spans[-1].status is False and keep.spans[-1].returncode == 3


def test_timed_boolReturn_isStatus() -> None:
    keep = Keep()

    @timed("check", keep)
    def check(ok: bool) -> bool:
        return ok

    assert check(False) is False and keep.spans[-1].status is False and keep.spans[-1].returncode is None


def test_timed_exception_recordedAndReraised() -> None:
    keep = Keep()

    @timed("broken", keep)
    def broken() -> None:
        raise ValueError("bad input")

    with pytest.raises(ValueError, match="bad input"):
        broken()
    span: Span = keep.spans[0]
    assert span.status is False and span.errors == ["ValueError: bad input"]


def test_timed_systemExit_isExitStatus() -> None:
    keep = Keep()

    @timed("cli", keep)
    def cli(code: int | str | None) -> None:
        raise SystemExit(code)

    with pytest.raises(SystemExit):
        cli(2)
    assert keep.spans[-1].returncode == 2 and keep.spans[-1].status is False
    with pytest.raises(SystemExit):
        cli(None)
    assert keep.spans[-1].returncode == 0 and keep.spans[-1].status is True
    with pytest.raises(SystemExit):
        cli("usage: wrong")
    assert keep.spans[-1].returncode == 1 and keep.spans[-1].errors == ["SystemExit: usage: wrong"]


def test_spanOpen_errorAdd_failsSpan() -> None:
    keep = Keep()
    with span_open("block", keep) as span:
        span.error_add("one slice was empty")
    assert keep.spans[0].status is False and keep.spans[0].errors == ["one slice was empty"]
    assert span.span is keep.spans[0]


def test_spanOpen_handSetReturncode() -> None:
    keep = Keep()
    with span_open("block", keep) as span:
        span.returncode = 0
    assert keep.spans[0].returncode == 0 and keep.spans[0].status is True


def test_builder_close_explicitStatus() -> None:
    builder = SpanBuilder("x")
    assert builder.close(status=False).status is False
    assert builder.span is not None and builder.span.name == "x"


def test_timed_default_writesJsonLineToStderr(capsys: pytest.CaptureFixture[str]) -> None:
    @timed("default")
    def quick() -> int:
        return 0

    quick()
    err: str = capsys.readouterr().err
    assert err.count("\n") == 1 and '"name": "default"' in err and '"status": true' in err
