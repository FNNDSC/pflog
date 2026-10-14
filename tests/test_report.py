"""The reporters."""

from __future__ import annotations

import io
import json
import logging
from pathlib import Path

import pytest

from pflog.models import HostFacts, Span
from pflog.report import FileReporter, JsonReporter, LogReporter, NullReporter, SpanReporter, TeeReporter

HOST: HostFacts = HostFacts("h", "u", 1, "linux", "/", "t")
SPAN: Span = Span("x", True, 0, [], HOST, "t0", "t1", 1.25)
FAILED: Span = Span("y", False, 1, ["ValueError: bad"], HOST, "t0", "t1", 0.5)


def test_everyReporter_isASpanReporter() -> None:
    for reporter in (NullReporter(), JsonReporter(), FileReporter("/tmp/x"), LogReporter(), TeeReporter()):
        assert isinstance(reporter, SpanReporter)


def test_json_oneLine() -> None:
    out = io.StringIO()
    JsonReporter(out).report(SPAN)
    JsonReporter(out).report(FAILED)
    lines: list[str] = out.getvalue().splitlines()
    assert len(lines) == 2 and json.loads(lines[1])["errors"] == ["ValueError: bad"]


def test_json_defaultsToStderr(capsys: pytest.CaptureFixture[str]) -> None:
    JsonReporter().report(SPAN)
    captured = capsys.readouterr()
    assert captured.out == "" and '"name": "x"' in captured.err


def test_file_appends_andCreatesDirectory(tmp_path: Path) -> None:
    path: Path = tmp_path / "out" / "spans.jsonl"
    reporter = FileReporter(path)
    reporter.report(SPAN)
    reporter.report(FAILED)
    assert len(path.read_text().splitlines()) == 2


def test_log_message(caplog: pytest.LogCaptureFixture) -> None:
    with caplog.at_level(logging.INFO, logger="pflog"):
        LogReporter().report(SPAN)
        LogReporter(level=logging.WARNING).report(FAILED)
    assert "x: 1.250 s, ok" in caplog.text
    assert "y: 0.500 s, failed: ValueError: bad" in caplog.text


def test_tee_forwardsInOrder() -> None:
    first = io.StringIO()
    second = io.StringIO()
    TeeReporter(JsonReporter(first), JsonReporter(second)).report(SPAN)
    assert first.getvalue() == second.getvalue() != ""
