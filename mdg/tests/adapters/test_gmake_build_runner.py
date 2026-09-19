"""The gmake build runner with subprocess mocked (SRS DSM-MDG req 13, 19)."""

import subprocess
from pathlib import Path

import pytest

from fakes import seed
from mdg.adapters.source_code.gmake_build_runner import GmakeBuildRunner
from mdg.adapters.source_code.mandatory_files import MandatoryFiles

RUNNER = GmakeBuildRunner(MandatoryFiles([seed.MAKEFILE_INCLUDE]))
TARGET = "mdg.adapters.source_code.gmake_build_runner.subprocess.run"


def _recording_run(calls):
    def run(cmd, **kwargs):
        calls.append((cmd, kwargs.get("cwd")))
        return subprocess.CompletedProcess(cmd, 0, stdout="", stderr="")
    return run


def test_ensure_available_raises_when_gmake_is_missing(monkeypatch):
    monkeypatch.setattr(TARGET, lambda *a, **k: (_ for _ in ()).throw(FileNotFoundError("gmake")))

    with pytest.raises(RuntimeError, match="gmake is not available"):
        RUNNER.ensure_available()


def test_ensure_available_passes_when_gmake_answers(monkeypatch):
    calls = []
    monkeypatch.setattr(TARGET, _recording_run(calls))

    RUNNER.ensure_available()

    assert calls[0][0] == ["gmake", "--version"]


def test_regenerate_code_is_skipped_without_a_valid_makefile(monkeypatch, tmp_path: Path):
    calls = []
    monkeypatch.setattr(TARGET, _recording_run(calls))
    (tmp_path / "Makefile").write_text(".PHONY: all\n", encoding="utf-8")

    RUNNER.regenerate_code(tmp_path)

    assert calls == []


def test_regenerate_code_runs_in_the_makefile_directory(monkeypatch, tmp_path: Path):
    calls = []
    monkeypatch.setattr(TARGET, _recording_run(calls))
    (tmp_path / "build").mkdir()
    (tmp_path / "build" / "Makefile").write_text(seed.VALID_MAKEFILE, encoding="utf-8")

    RUNNER.regenerate_code(tmp_path)

    assert calls == [(["gmake", "regenerate_code"], tmp_path / "build")]


def test_a_failing_build_is_logged_not_raised(monkeypatch, tmp_path: Path):
    monkeypatch.setattr(TARGET, lambda *a, **k: (_ for _ in ()).throw(subprocess.TimeoutExpired("gmake", 1)))
    (tmp_path / "Makefile").write_text(seed.VALID_MAKEFILE, encoding="utf-8")

    RUNNER.regenerate_code(tmp_path)
