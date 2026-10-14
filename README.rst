pflog
=====

**Time any function or block, and get back a record you can log, parse and query.**

``pflog`` puts a span around a call: when it began, when it ended, how long it took, on which host, and whether it succeeded. The span is a small typed record, written by default as one line of JSON on standard error, so a log collector indexes it without being told the format and ``pflog read`` turns a day of them back into a table.

.. code-block:: python

    from pflog import timed

    @timed("convert")
    def convert(inputFile: str, outputFile: str) -> int:
        ...
        return 0

    convert("in.dcm", "out.nii.gz")

.. code-block:: text

    {"duration": 4.213, "endedAt": "2026-10-14T16:02:11-04:00", "errors": [], "host": {...}, "name": "convert", "returncode": 0, "startedAt": "2026-10-14T16:02:07-04:00", "status": true}

The gap
-------

Every long-running program ends up wanting to know how long its main step took, and the answer is usually a ``print`` of a subtraction between two timestamps. That line is prose: a collector cannot query it, a second program cannot parse it, and it says nothing about whether the step worked. Platform telemetry sees the other side, pods and containers and their resource use, but it cannot know what the program meant by a step, and the volume of what it does know becomes an obstacle to finding the one number that mattered.

``pflog`` is the small piece in between: a record shaped by the program, emitted where the platform already looks. The program names the span and nothing else. The record carries the outcome, so a failed call is a failed span, not a number that looks like every other.

The record
----------

A span has these fields. The last six are the same fields, in the same formats, as `hostlib <https://github.com/FNNDSC/hostlib>`_ keeps for a process, so a log of spans and a log of jobs read as one.

==================  ======================================================================
``name``            The span's name; the function's name when none is given.
``status``          ``True`` when the call returned without error and, if it returned an exit status, that status was 0.
``returncode``      The integer the call returned, or the code of a ``SystemExit`` it raised; ``None`` otherwise.
``errors``          Why a failed span failed, in words: ``"ValueError: bad input"``.
``host``            Hostname, user, pid, platform, working directory.
``startedAt``       When it started, ISO 8601 with the local offset.
``endedAt``         When it ended.
``duration``        Seconds, from a monotonic clock.
==================  ======================================================================

The outcome is read from the call the way a shell reads a program. An integer returned, or a ``SystemExit`` raised, is an exit status with 0 meaning success. A boolean is the status itself. Anything else returned without error is success. An exception is a failure, recorded and then raised on as if the span were not there.

Timing a function
-----------------

The decorator takes a name and, optionally, a reporter. The function's return value and exceptions pass through untouched.

.. code-block:: python

    from pflog import timed, FileReporter

    @timed("recon", report=FileReporter("/out/spans.jsonl"))
    def recon(subject: str) -> int:
        ...

Used bare, ``@timed`` names the span after the function and reports to standard error.

A command-line program's ``main`` is the span that matters most. For a ChRIS plugin, the span goes on standard error, where CUBE keeps it with the rest of the plugin's output.

.. code-block:: python

    @chris_plugin(...)
    @timed("shexec")
    def main(options: Namespace, inputdir: Path, outputdir: Path) -> int:
        ...

Timing a block
--------------

The context manager times a block and gives the open span a handle, for noting an error the block survived or an outcome the block knows better than the library.

.. code-block:: python

    from pflog import span_open

    with span_open("slices") as span:
        for slice_ in slices:
            if not slice_.process():
                span.error_add(f"{slice_.name} was empty")

A span with errors is a failed span, however the block ended.

Where the record goes
---------------------

A reporter is anything with a ``report(span)`` method. Five come with the library.

==========================  ==================================================================
``JsonReporter(stream)``    One line of JSON per span; the process's standard error by default.
``FileReporter(path)``      One line of JSON per span, appended; the directory is created.
``LogReporter(logger)``     ``recon: 4.213 s, ok`` through Python's logging, for programs that already log.
``TeeReporter(a, b)``       Every span to each reporter given.
``NullReporter()``          Nothing.
==========================  ==================================================================

Standard error is the default on purpose. A program's standard output may be data that another program parses; its standard error is where a line about the run belongs, and it is captured by every container runtime and log collector.

Reading it back
---------------

The ``pflog`` command reads files of JSON lines, span lines and hostlib job lines alike, and prints one row each.

.. code-block:: bash

    pflog read /out/*/spans.jsonl
    pflog read --failed /out/*/spans.jsonl
    pflog read --json --failed /out/*/spans.jsonl | jq .errors

.. code-block:: text

    STARTED                     DURATION  STATUS  NAME
    2026-10-14T09:14:51-04:00      0.306  ok      demo
    2026-10-14T09:14:51-04:00      0.002  failed  demo
    2026-10-14T09:14:52-04:00      0.003  failed  wc -l /nonexistent

``pflog demo --file /tmp/spans.jsonl`` times a sleep and reports it, for seeing a span without writing code. ``pflog --man`` is the full manual.

What pflog is not
-----------------

It is not a transport. A span is written where the program's output already goes, and whatever collects that output carries it on; the library opens no sockets and posts to no server. It is not a profiler: one span per call, named by the program, not a trace of every function. It is not a logger: ``LogReporter`` writes through Python's logging when a program wants spans in its log, but the library has no levels, no handlers and no configuration of its own.

Install
-------

.. code-block:: bash

    pip install pflog

Python 3.11 or later. One dependency, ``hostlib``, for the host facts and the record formats shared with it.

Layout
------

.. code-block:: text

    pflog/
    ├── models/    Span, and hostlib's records re-exported
    ├── span/      timed, span_open, SpanBuilder
    ├── report/    JsonReporter, FileReporter, LogReporter, TeeReporter, NullReporter
    └── cli/       the pflog command: read, demo, --man

``docs/purpose.adoc`` says why the library exists, ``docs/architecture.adoc`` how it is built, ``docs/history.adoc`` where it came from.
