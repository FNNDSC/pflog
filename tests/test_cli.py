"""The pflog command."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from pflog import __version__
from pflog.cli.commands import main, manual_build, parser_build, records_read, table_render


def test_version(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as exit_:
        main(["--version"])
    assert exit_.value.code == 0 and f"pflog {__version__}" in capsys.readouterr().out


def test_manual_noBackticks(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["--man"]) == 0
    out: str = capsys.readouterr().out
    body: str = out.split("DESCRIPTION", 1)[1]
    assert "`" not in body and "THE RECORD" in body and "REPORTERS" in body
    assert main(["--synopsis"]) == 0
    assert "REPORTERS" not in capsys.readouterr().out


def test_manual_build_fillsVersion() -> None:
    assert __version__ in manual_build().text_render()


def test_noCommand_printsHelp_exits2(capsys: pytest.CaptureFixture[str]) -> None:
    assert main([]) == 2
    assert "usage: pflog" in capsys.readouterr().out


def test_demo_reportsSpan_andWritesFile(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    path: Path = tmp_path / "spans.jsonl"
    assert main(["demo", "--seconds", "0", "--file", str(path)]) == 0
    err: str = capsys.readouterr().err
    record = json.loads(err)
    assert record["name"] == "demo" and record["status"] is True
    assert json.loads(path.read_text())["name"] == "demo"


def test_demo_fail_exits1_andRecordsError(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["demo", "--seconds", "0", "--fail"]) == 1
    record = json.loads(capsys.readouterr().err)
    assert record["status"] is False and record["errors"] == ["RuntimeError: the demo was asked to fail"]


def test_read_table_spansAndJobs(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    path: Path = tmp_path / "mixed.jsonl"
    path.write_text(
        json.dumps({"name": "main", "status": True, "startedAt": "t0", "duration": 2.5})
        + "\n"
        + json.dumps({"argv": ["wc", "-l", "a"], "status": False, "startedAt": "t1", "duration": 0.1})
        + "\nnot json\n"
        + json.dumps({"other": 1})
        + "\n"
    )
    assert main(["read", str(path)]) == 0
    out: str = capsys.readouterr().out
    lines: list[str] = out.splitlines()
    assert lines[0].startswith("STARTED") and len(lines) == 3
    assert "main" in lines[1] and "ok" in lines[1]
    assert "wc -l a" in lines[2] and "failed" in lines[2]


def test_read_failed_json(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    path: Path = tmp_path / "s.jsonl"
    path.write_text(
        json.dumps({"name": "a", "status": True}) + "\n" + json.dumps({"name": "b", "status": False}) + "\n"
    )
    assert main(["read", "--failed", "--json", str(path)]) == 0
    out: str = capsys.readouterr().out
    assert out.count("\n") == 1 and json.loads(out)["name"] == "b"


def test_read_missingFile_exits2(tmp_path: Path) -> None:
    with pytest.raises(SystemExit) as exit_:
        main(["read", str(tmp_path / "none.jsonl")])
    assert exit_.value.code == 2


def test_records_read_and_table_render() -> None:
    rows = records_read(['{"name": "n", "status": true, "startedAt": "s", "duration": 1}', "", "{}"])
    assert len(rows) == 1
    assert "n" in table_render(rows)


def test_parser_build_subcommands() -> None:
    args = parser_build().parse_args(["read", "--failed", "a", "b"])
    assert args.command == "read" and args.failed and args.files == ["a", "b"]
