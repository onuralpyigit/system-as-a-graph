"""The multiprocessing task runner with real spawned children, and its child-side entry
in-process (SRS DSM-DVE req 6, 8, 50)."""

import logging
import os
import re
import signal
import time
from unittest import mock

import pytest

from fakes.fake_task_runner import scripted_task
from dve.adapters.in_memory_task_log import InMemoryTaskLog
from dve.adapters import multiprocessing_task_runner as task_runner
from dve.adapters.multiprocessing_task_runner import MultiprocessingTaskRunner
from dve.domain.task_status import TaskStatus


def wait_until(predicate, timeout=30.0):
    deadline = time.monotonic() + timeout
    while True:
        value = predicate()
        if value:
            return value
        if time.monotonic() >= deadline:
            raise AssertionError("timed out waiting for the task")
        time.sleep(0.05)


def finished(runner, task_id):
    return lambda: runner.status(task_id) if runner.status(task_id).state in ("SUCCESS", "FAILURE", "REVOKED") else None


@pytest.fixture
def log():
    return InMemoryTaskLog()


@pytest.fixture
def runner(log):
    runner = MultiprocessingTaskRunner(log, concurrency=1)
    yield runner
    for task_id in list(runner._tasks):
        runner.cancel(task_id)


# --- runner, real children ---------------------------------------------------


def test_a_task_carries_its_result_and_its_log_lines_on_success(runner, log):
    task_id = runner.submit(scripted_task, "succeed")

    status = wait_until(finished(runner, task_id))

    assert status == TaskStatus(task_id, "SUCCESS", result={"task_id": task_id})
    assert isinstance(status.started_at, float) and status.finished_at >= status.started_at
    lines = wait_until(lambda: log.lines_since(task_id, 0))
    assert re.fullmatch(r"\d{2}:\d{2}:\d{2} INFO     hello from child", lines[0])


def test_a_task_collects_dsm_logs_and_not_another_librarys(runner, log):
    task_id = runner.submit(scripted_task, "noise")

    assert wait_until(finished(runner, task_id)).state == "SUCCESS"
    lines = wait_until(lambda: log.lines_since(task_id, 0))

    assert len(lines) == 1
    assert "ours" in lines[0]
    assert not any("theirs" in line for line in lines)


def test_a_failing_task_carries_the_childs_message(runner):
    task_id = runner.submit(scripted_task, "fail")

    assert wait_until(finished(runner, task_id)) == TaskStatus(task_id, "FAILURE", error="boom")


def test_a_child_that_dies_without_reporting_is_a_failure(runner):
    task_id = runner.submit(scripted_task, "crash")

    assert wait_until(finished(runner, task_id)) == TaskStatus(task_id, "FAILURE", error="task process exited with code 3")


def test_progress_is_reported_while_running_and_cancel_terminates_the_task(runner):
    task_id = runner.submit(scripted_task, "sleep")
    wait_until(lambda: runner.status(task_id).progress)
    assert runner.status(task_id) == TaskStatus(task_id, "STARTED", progress={"percent": 42, "phase": "clone"})
    assert runner.status(task_id).started_at is not None and runner.status(task_id).finished_at is None

    revoked = runner.cancel(task_id)
    assert revoked == TaskStatus(task_id, "REVOKED")
    assert revoked.finished_at >= revoked.started_at

    process = runner._tasks[task_id].process
    wait_until(lambda: not process.is_alive())
    assert runner.status(task_id) == TaskStatus(task_id, "REVOKED")
    next_id = runner.submit(scripted_task, "succeed")
    assert wait_until(finished(runner, next_id)).state == "SUCCESS"


def test_tasks_beyond_concurrency_wait_as_pending_until_a_slot_frees(runner):
    first = runner.submit(scripted_task, "sleep")
    second = runner.submit(scripted_task, "succeed")
    wait_until(lambda: runner.status(first).state == "STARTED")
    assert runner.status(second) == TaskStatus(second, "PENDING")

    runner.cancel(first)

    assert wait_until(finished(runner, second)).state == "SUCCESS"


def test_cancel_of_a_pending_task_revokes_it_without_starting_it(runner, log):
    first = runner.submit(scripted_task, "sleep")
    second = runner.submit(scripted_task, "succeed")

    assert runner.cancel(second) == TaskStatus(second, "REVOKED")

    runner.cancel(first)
    wait_until(lambda: not runner._tasks[first].process.is_alive())
    assert runner.status(second) == TaskStatus(second, "REVOKED")
    assert log.lines_since(second, 0) == []
    assert runner._tasks[second].process is None


def test_unknown_ids_report_pending_and_cancel_as_revoked(log):
    runner = MultiprocessingTaskRunner(log)

    assert runner.status("nope") == TaskStatus("nope", "PENDING")
    assert runner.cancel("nope") == TaskStatus("nope", "REVOKED")
    assert runner.status("nope") == TaskStatus("nope", "REVOKED")


def test_concurrency_defaults_to_the_cpu_count(log):
    assert MultiprocessingTaskRunner(log).concurrency == os.cpu_count()
    assert MultiprocessingTaskRunner(log, 0).concurrency == os.cpu_count()
    assert MultiprocessingTaskRunner(log, 3).concurrency == 3


# --- child side, in-process --------------------------------------------------


class RecordingSink:
    def __init__(self, raises=False):
        self.events = []
        self.closed = False
        self.raises = raises

    def send(self, event):
        if self.raises:
            raise BrokenPipeError("gone")
        self.events.append(event)

    def close(self):
        self.closed = True


@pytest.fixture
def quiet_child(monkeypatch):
    monkeypatch.setattr(task_runner, "_configure_child", lambda task_id=None: None)


def task_log_handlers():
    """The handlers attached to DSM's own logger trees, which is where a task's log comes from."""
    return [
        handler
        for name in task_runner.APP_LOGGERS
        for handler in logging.getLogger(name).handlers
        if isinstance(getattr(handler, "stream", None), task_runner.PipeWriter)
    ]


def test_run_task_calls_the_target_with_the_id_and_progress_then_sends_done_and_closes(quiet_child):
    sink = RecordingSink()
    target = mock.Mock(return_value={"ok": True})

    task_runner.run_task(target, "t-1", ("a", 2), sink)

    target.assert_called_once_with("t-1", "a", 2, progress=mock.ANY)
    assert sink.events == [("done", {"ok": True})]
    assert sink.closed is True
    assert task_log_handlers() == []


def test_run_task_sends_failed_with_the_message_or_the_repr(quiet_child):
    sink = RecordingSink()
    task_runner.run_task(mock.Mock(side_effect=ValueError("boom")), "t-1", (), sink)
    assert sink.events == [("failed", "boom")]

    sink = RecordingSink()
    task_runner.run_task(mock.Mock(side_effect=ValueError()), "t-1", (), sink)
    assert sink.events[0][0] == "failed" and "ValueError" in sink.events[0][1]


def test_run_task_stays_silent_when_cancelled(quiet_child):
    sink = RecordingSink()

    task_runner.run_task(mock.Mock(side_effect=task_runner.Cancelled()), "t-1", (), sink)

    assert sink.events == []
    assert sink.closed is True


def test_progress_and_log_lines_are_sent_as_events(quiet_child, caplog):
    caplog.set_level(logging.INFO)
    sink = RecordingSink()

    def target(task_id, progress):
        progress(42, "clone")
        logging.getLogger("mdg.services.acquire_source_code").info("acquire: nav_app 1.0.0 cloned")
        return {}

    task_runner.run_task(target, "t-1", (), sink)

    assert sink.events[0] == ("progress", {"percent": 42, "phase": "clone"})
    kind, line = sink.events[1]
    assert kind == "log"
    assert re.fullmatch(r"\d{2}:\d{2}:\d{2} INFO     acquire: nav_app 1\.0\.0 cloned", line)
    assert sink.events[2] == ("done", {})


def test_a_dead_events_channel_does_not_fail_the_task(quiet_child, caplog):
    caplog.set_level(logging.INFO)
    sink = RecordingSink(raises=True)

    def target(task_id, progress):
        progress(42, "clone")
        logging.getLogger("mdg").info("still fine")
        return {}

    task_runner.run_task(target, "t-1", (), sink)

    assert sink.events == []
    assert sink.closed is True


def test_the_child_ignores_ctrl_c_and_unwinds_on_sigterm(monkeypatch):
    calls = {}
    monkeypatch.setattr(task_runner.signal, "signal", lambda signum, handler: calls.__setitem__(signum, handler))
    monkeypatch.setattr(task_runner, "configure_logging", lambda **kwargs: None)

    task_runner._configure_child("t-1")

    assert calls[signal.SIGINT] is signal.SIG_IGN
    with pytest.raises(task_runner.Cancelled):
        calls[signal.SIGTERM](signal.SIGTERM, None)
