"""The record of one timed call.

A span is to a function call what hostlib's ``JobResult`` is to a process: when it
started, when it ended, how long it took, on which host, and whether it succeeded.
The fields the two records share carry the same names and the same formats, so a
span line and a job line sit in one log and one query reads both.

Key components:
    - Span: the record

Typical usage:
    span.toJson(indent=None)  # one line, for a log

Dependencies:
    - hostlib.models
"""

from __future__ import annotations

import dataclasses
import json
from dataclasses import dataclass, field
from typing import Any

from hostlib.models.facts import HostFacts


@dataclass
class Span:
    """What one timed call was and how it went.

    Attributes:
        name: the span's name; the function's name unless given.
        status: True when the call returned without error and, if it returned an
            exit status, that status was 0.
        returncode: the integer the call returned, or the code of a ``SystemExit`` it
            raised; ``None`` when it returned anything else.
        errors: why a failed span failed, in words; empty on success.
        host: the facts of the host it ran on.
        startedAt: when it started, ISO 8601.
        endedAt: when it ended, ISO 8601.
        duration: seconds from start to end.

    Example:
        >>> span = Span("demo", True, 0, [], HostFacts("h", "u", 1, "linux", "/", "t"), "t0", "t1", 1.5)
        >>> Span.fromDict(span.toDict()) == span
        True
    """

    name: str
    status: bool
    returncode: int | None
    errors: list[str] = field(default_factory=list)
    host: HostFacts = field(default_factory=lambda: HostFacts("", "", 0, "", "", ""))
    startedAt: str = ""
    endedAt: str = ""
    duration: float = 0.0

    def toDict(self) -> dict[str, Any]:
        """The record as plain data, for JSON."""
        return dataclasses.asdict(self)

    def toJson(self, indent: int | None = 4) -> str:
        """The record as JSON text; ``indent=None`` gives one line."""
        return json.dumps(self.toDict(), indent=indent, sort_keys=True)

    @classmethod
    def fromDict(cls, data: dict[str, Any]) -> Span:
        """A span read back from its plain data.

        Args:
            data: what ``toDict`` produced, or a JSON line parsed.

        Returns:
            The span.
        """
        hostData: dict[str, Any] = dict(data.get("host") or {})
        return cls(
            name=str(data.get("name", "")),
            status=bool(data.get("status", False)),
            returncode=data.get("returncode"),
            errors=list(data.get("errors") or []),
            host=HostFacts(**hostData) if hostData else HostFacts("", "", 0, "", "", ""),
            startedAt=str(data.get("startedAt", "")),
            endedAt=str(data.get("endedAt", "")),
            duration=float(data.get("duration", 0.0)),
        )
