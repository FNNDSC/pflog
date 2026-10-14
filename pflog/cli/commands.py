"""The ``pflog`` command: ``read`` span and job lines back as a table, ``demo`` a timed call.

``--help`` is argparse's quick reference; ``--man`` prints the full manual, ``--synopsis``
its first page.

Key components:
    - BANNER_*, SYNOPSIS_CLI, DESCRIPTION, ARGS, RECORD_HELP, REPORTERS_HELP, EXAMPLES: the manual's text
    - synopsis, manual_build: the manual
    - parser_build: the parser, with ``read`` and ``demo`` subcommands
    - records_read, table_render: reading lines back
    - read_command, demo_command: the subcommands
    - main: the entry point, honouring an explicit ``argv``

Typical usage:
    pflog read /out/spans.jsonl
    pflog read --failed /out/*.jsonl
    pflog demo --seconds 0.5

Dependencies:
    - pflog.models, pflog.span, pflog.report, pflog.cli.manual
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any, TextIO

from pflog import __version__
from pflog.cli.manual import Manual, manual_print
from pflog.report.jsonline import FileReporter, JsonReporter
from pflog.report.protocol import SpanReporter
from pflog.report.tee import TeeReporter
from pflog.span.timed import span_open

EXIT_USAGE: int = 2
EXIT_FAILED: int = 1

BANNER_TITLE: str = "pflog: time a call, keep the record"
BANNER_ART: str = r"""
        __ _
       / _| |
 _ __ | |_| | ___   __ _
| '_ \|  _| |/ _ \ / _` |
| |_) | | | | (_) | (_| |
| .__/|_| |_|\___/ \__, |
| |                 __/ |
|_|                |___/
"""
BANNER_TEXT: str = """
                        pflog: time a call, keep the record

                            -- version {version} --

    A span around any function or block: when it began, when it ended, how long it
    took, on which host, and whether it succeeded. The span is a record of the same
    shape as hostlib's record of a process, written as one line of JSON, so a log
    collector parses it and ``pflog read`` reads it back.
"""

SYNOPSIS_CLI: str = """
        pflog read [--failed] [--json] [<file> ...]

        pflog demo [--seconds <n>] [--fail] [--file <path>]

        pflog [--man] [--synopsis] [--version]"""

DESCRIPTION: str = """
    DESCRIPTION

        pflog is first a Python module. A function wearing ``@timed("name")``, or a
        block inside ``with span_open("name") as span:``, produces a Span when it
        ends: name, status, returncode, errors, host, startedAt, endedAt, duration.
        The call's own result is untouched: its return value comes back as it was,
        and an exception it raises keeps propagating, after the span has recorded
        it as a failure. The outcome is read as a shell reads a program: an integer
        returned, or a SystemExit raised, is an exit status with 0 meaning success;
        a boolean is the status itself; anything else, returned without error, is
        success.

        Each span goes to a reporter. The default writes one line of JSON to the
        process's standard error, so a program's own standard output stays its own.
        Other reporters append to a file, write through Python's logging, or fan out
        to several.

        The ``pflog`` command reads those lines back. ``read`` takes files of JSON
        lines, span lines and hostlib job lines alike, and prints one row each:
        when it started, how long it took, how it ended, and its name or command.
"""

ARGS: str = """
    ARGUMENTS

        read [--failed] [--json] [<file> ...]
        Read span and job lines from the files, or from standard input when no
        file is given, and print a table. A span line is recognised by its ``name``,
        a job line by its ``argv``; other lines are skipped. --failed keeps only the
        rows whose status is false. --json prints the kept lines as they were
        instead of the table.

        demo [--seconds <n>] [--fail] [--file <path>]
        Time a call that sleeps for <n> seconds (0.2 by default) and report the
        span on standard error. --fail makes the call raise, to show a failed
        span; the command then exits 1. --file also appends the span to <path>,
        which ``pflog read`` can then read back.

        --man, --synopsis, --version
        The full manual, its first page, the version.
"""

RECORD_HELP: str = """
    THE RECORD

        A Span has these fields, in JSON as a flat object with ``host`` nested:

            name          the span's name; the function's name unless given
            status        true when the call returned without error and, if it
                          returned an exit status, that status was 0
            returncode    the integer returned or the SystemExit code; null otherwise
            errors        why a failed span failed, in words; empty on success
            host          hostname, user, pid, platform, cwd, timestamp
            startedAt     ISO 8601 with the local offset
            endedAt       ISO 8601 with the local offset
            duration      seconds, from a monotonic clock

        status, errors, host, startedAt, endedAt and duration are the same fields,
        in the same formats, as hostlib's JobResult carries for a process. A log that
        holds both kinds of line is read by one query.
"""

REPORTERS_HELP: str = """
    REPORTERS

        JsonReporter(stream=None)    one line of JSON per span; stderr by default
        FileReporter(path)           one line of JSON per span, appended to the file
        LogReporter(logger, level)   ``name: 4.213 s, ok`` through Python's logging
        TeeReporter(a, b, ...)       every span to each reporter given
        NullReporter()               nothing

        Pass one as ``report=`` to ``timed`` or ``span_open``. Any object with a
        ``report(span)`` method is a reporter.
"""

EXAMPLES: str = """
    EXAMPLES

        Time a ChRIS plugin's main, the span on stderr where CUBE keeps it:

            @chris_plugin(...)
            @timed("shexec")
            def main(options: Namespace, inputdir: Path, outputdir: Path) -> int:
                ...

        Time a block and keep the spans in a file beside the results:

            with span_open("recon-all", report=FileReporter(outputdir / "spans.jsonl")):
                job_run(JobSpec(["recon-all", "-all", "-s", subject]))

        Read a day's spans back, failures only:

            pflog read --failed /out/*/spans.jsonl

        See a span without writing any code:

            pflog demo --seconds 1 --file /tmp/spans.jsonl
            pflog read /tmp/spans.jsonl
"""


def synopsis(shortOnly: bool = False) -> str:
    """Assemble the manual text.

    Args:
        shortOnly: NAME, SYNOPSIS and a brief example only.

    Returns:
        The manual text, without the banner.
    """
    shortSynopsis: str = (
        """
    NAME

        pflog - time a call, keep the record

    SYNOPSIS
"""
        + SYNOPSIS_CLI
        + """

    BRIEF EXAMPLE

        pflog demo --file /tmp/spans.jsonl && pflog read /tmp/spans.jsonl
    """
    )
    if shortOnly:
        return shortSynopsis
    return shortSynopsis + DESCRIPTION + ARGS + RECORD_HELP + REPORTERS_HELP + EXAMPLES


def manual_build() -> Manual:
    """The manual, ready to render."""
    return Manual(
        command="pflog",
        art=BANNER_ART,
        title=BANNER_TITLE,
        text=BANNER_TEXT,
        version=__version__,
        synopsisShort=synopsis(shortOnly=True),
        synopsisFull=synopsis(shortOnly=False),
    )


def parser_build() -> argparse.ArgumentParser:
    """The command's parser: top-level manual flags, then ``read`` and ``demo``."""
    parser: argparse.ArgumentParser = argparse.ArgumentParser(
        prog="pflog",
        description="Time a call, keep the record. Full manual: pflog --man",
    )
    parser.add_argument("--version", action="version", version=f"pflog {__version__}")
    parser.add_argument("--man", action="store_true", help="print the full manual")
    parser.add_argument("--synopsis", action="store_true", help="print the manual's first page")
    commands: argparse._SubParsersAction[argparse.ArgumentParser] = parser.add_subparsers(dest="command")

    read: argparse.ArgumentParser = commands.add_parser(
        "read", help="read span and job lines back as a table"
    )
    read.add_argument("--failed", action="store_true", help="only rows whose status is false")
    read.add_argument("--json", action="store_true", help="print the kept lines instead of the table")
    read.add_argument("files", nargs="*", help="files of JSON lines; standard input when none")

    demo: argparse.ArgumentParser = commands.add_parser("demo", help="time a call and report the span")
    demo.add_argument("--seconds", type=float, default=0.2, help="how long the call sleeps")
    demo.add_argument("--fail", action="store_true", help="make the call raise")
    demo.add_argument("--file", default=None, help="also append the span to this file")
    return parser


@dataclass
class Row:
    """One line of the table ``read`` prints.

    Attributes:
        startedAt: when the span or job started.
        duration: seconds.
        status: how it ended.
        label: the span's name or the job's command.
        line: the JSON line it came from.

    Example:
        >>> Row("t", 1.0, True, "x", "{}").status
        True
    """

    startedAt: str
    duration: float
    status: bool
    label: str
    line: str


def row_fromRecord(record: dict[str, Any], line: str) -> Row | None:
    """A table row from one parsed line, or ``None`` when the line is neither a span nor a job."""
    if "name" in record:
        label: str = str(record["name"])
    elif "argv" in record:
        label = " ".join(str(part) for part in record["argv"])
    else:
        return None
    return Row(
        startedAt=str(record.get("startedAt", "")),
        duration=float(record.get("duration", 0.0) or 0.0),
        status=bool(record.get("status", False)),
        label=label,
        line=line,
    )


def records_read(lines: Iterable[str]) -> list[Row]:
    """Parse JSON lines into rows, skipping what is not JSON or not a record."""
    rows: list[Row] = []
    for raw in lines:
        line: str = raw.rstrip("\n")
        if not line.strip():
            continue
        try:
            record: Any = json.loads(line)
        except json.JSONDecodeError:
            continue
        if not isinstance(record, dict):
            continue
        row: Row | None = row_fromRecord(record, line)
        if row is not None:
            rows.append(row)
    return rows


def table_render(rows: list[Row]) -> str:
    """The rows as aligned text, a header first."""
    header: str = f"{'STARTED':<25} {'DURATION':>10}  {'STATUS':<6}  NAME"
    body: list[str] = [
        f"{row.startedAt:<25} {row.duration:>10.3f}  {'ok' if row.status else 'failed':<6}  {row.label}"
        for row in rows
    ]
    return "\n".join([header, *body]) + "\n"


def lines_open(files: list[str]) -> list[str]:
    """Every line of the files, or of standard input when there are none.

    Raises:
        OSError: a file cannot be read.
    """
    if not files:
        return sys.stdin.readlines()
    lines: list[str] = []
    for name in files:
        lines.extend(Path(name).read_text().splitlines(keepends=True))
    return lines


def read_command(args: argparse.Namespace, parser: argparse.ArgumentParser, out: TextIO | None = None) -> int:
    """``pflog read``.

    Returns:
        0; 2 when a file cannot be read.
    """
    stream: TextIO = out if out is not None else sys.stdout
    try:
        rows: list[Row] = records_read(lines_open(args.files))
    except OSError as err:
        parser.error(str(err))
    if args.failed:
        rows = [row for row in rows if not row.status]
    if args.json:
        stream.write("".join(row.line + "\n" for row in rows))
    else:
        stream.write(table_render(rows))
    return 0


def demo_command(args: argparse.Namespace) -> int:
    """``pflog demo``: time a sleep, reporting on stderr and optionally to a file.

    Returns:
        0; 1 when ``--fail`` made the call raise.
    """
    reporter: SpanReporter = JsonReporter()
    if args.file:
        reporter = TeeReporter(reporter, FileReporter(args.file))
    try:
        with span_open("demo", reporter):
            time.sleep(max(args.seconds, 0.0))
            if args.fail:
                raise RuntimeError("the demo was asked to fail")
    except RuntimeError:
        return EXIT_FAILED
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    """Run the command.

    Args:
        argv: arguments without the program name; ``None`` reads ``sys.argv``.

    Returns:
        The exit status.
    """
    parser: argparse.ArgumentParser = parser_build()
    args: argparse.Namespace = parser.parse_args(argv)
    if args.man or args.synopsis:
        manual_print(manual_build(), shortOnly=not args.man)
        return 0
    if args.command == "read":
        return read_command(args, parser)
    if args.command == "demo":
        return demo_command(args)
    parser.print_help()
    return EXIT_USAGE


if __name__ == "__main__":
    sys.exit(main())
