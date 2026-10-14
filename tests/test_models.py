"""Span: serialisation, round trip, and the fields it shares with hostlib's JobResult."""

from __future__ import annotations

import dataclasses
import json

from hostlib.models.proc import JobResult

from pflog.models import HostFacts, Span

HOST: HostFacts = HostFacts("h", "u", 1, "linux", "/", "2026-01-01T00:00:00+00:00")


def test_toJson_oneLineSorted() -> None:
    span = Span("x", True, 0, [], HOST, "t0", "t1", 1.5)
    line: str = span.toJson(indent=None)
    assert "\n" not in line
    assert json.loads(line)["name"] == "x"
    assert list(json.loads(line)) == sorted(json.loads(line))


def test_fromDict_roundTrip() -> None:
    span = Span("x", False, 3, ["boom"], HOST, "t0", "t1", 0.25)
    assert Span.fromDict(json.loads(span.toJson())) == span


def test_fromDict_tolerant() -> None:
    span = Span.fromDict({"name": "y"})
    assert span.name == "y" and span.status is False and span.returncode is None and span.host.hostname == ""


def test_sharedFields_matchJobResult() -> None:
    spanFields: dict[str, type | str] = {f.name: f.type for f in dataclasses.fields(Span)}
    jobFields: dict[str, type | str] = {f.name: f.type for f in dataclasses.fields(JobResult)}
    shared: set[str] = set(spanFields) & set(jobFields)
    assert shared == {"status", "returncode", "errors", "host", "startedAt", "endedAt", "duration"}
    for name in shared:
        assert spanFields[name] == jobFields[name], name
