"""The records pflog produces, and the hostlib records it builds on.

A program that uses pflog imports every record from here: its own ``Span`` and
hostlib's ``HostFacts``, ``JobResult`` and ``JobSpec``, so nothing has to reach past
pflog into the layer below.

Key components:
    - Span: the record of one timed call
    - HostFacts, JobResult, JobSpec, JobStarted, JobLogs: hostlib's records, re-exported

Dependencies:
    - hostlib.models
"""

from __future__ import annotations

from hostlib.models.facts import HostFacts
from hostlib.models.proc import JobLogs, JobResult, JobSpec, JobStarted

from pflog.models.span import Span

__all__: list[str] = ["HostFacts", "JobLogs", "JobResult", "JobSpec", "JobStarted", "Span"]
