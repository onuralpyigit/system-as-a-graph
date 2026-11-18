"""Multiprocessing adapter of the task runner port: one spawned process per
task, a pipe per task for its log, progress and outcome, and a bounded number
running at once (SRS DSM-DVE req 6, 8, 50).

The child side (`run_task` and its helpers) runs in the spawned process; the
parent side (`MultiprocessingTaskRunner`) lives in the API process and keeps
every task's status in memory for the process lifetime.
"""

from __future__ import annotations

import logging
import multiprocessing
import os
import signal
import threading
import time
import uuid
from collections import deque
from dataclasses import dataclass
from typing import Any, Callable, Deque, Dict, Optional, Protocol, Tuple

from dve.config import APP_LOGGERS, configure_logging
from dve.domain.task_status import FAILURE, PENDING, REVOKED, STARTED, SUCCESS, TaskStatus
from dve.ports.task_log import ITaskLog
from dve.ports.task_runner import ITaskRunner

logger = logging.getLogger(__name__)

STOP_TIMEOUT_SECONDS = 5.0


# --- child side -------------------------------------------------------------


class Cancelled(BaseException):
    """Raised in the child by SIGTERM: a BaseException so it passes through the
    task's `except Exception` clauses and `subprocess.run` kills its child."""


class TaskEvents(Protocol):
    """What the child writes its (kind, payload) events to: a pipe connection in
    production, a recorder in tests."""

    def send(self, event: Tuple[str, Any]) -> None: ...

    def close(self) -> None: ...


class PipeWriter:
    """The task's log lines as a write-only file over its event channel: each line
    becomes a ("log", line) event; a send failure is logged, never raised (req 8),
    and the guard keeps that very warning from re-entering the writer."""

    def __init__(self, events: TaskEvents):
        self._events = events
        self._writing = False

    def write(self, line: str) -> int:
        if self._writing:
            return len(line)
        self._writing = True
        try:
            self._events.send(("log", line.rstrip("\n")))
        except Exception:
            logger.warning("task log: failed to send a line")
        finally:
            self._writing = False
        return len(line)

    def flush(self) -> None:
        """A line is sent as it is written, so nothing is buffered here."""
        return None


def task_log_handler(events: TaskEvents) -> logging.StreamHandler:
    """The handler that forwards the task's log records (INFO and above) to its
    events; attached to the `APP_LOGGERS` trees, so no other library's records
    reach the task's log."""
    handler = logging.StreamHandler(PipeWriter(events))
    handler.setLevel(logging.INFO)
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)-8s %(message)s", datefmt="%H:%M:%S"))
    handler.terminator = ""
    return handler


class TaskProgress:
    """Forwards each (percent, phase) step as a ("progress", {...}) event; a
    send failure is logged, never raised (req 6)."""

    def __init__(self, events: TaskEvents):
        self._events = events

    def report(self, percent: int, phase: str) -> None:
        try:
            self._events.send(("progress", {"percent": percent, "phase": phase}))
        except Exception:
            logger.warning("task progress: failed to send progress")


def _on_terminate(signum, frame) -> None:
    raise Cancelled()


def _configure_child(task_id: Optional[str] = None) -> None:
    """The child's logging and signals: the task's level to the terminal under its
    own id, Ctrl+C left to the parent, SIGTERM (the parent's cancel) unwinds the task."""
    configure_logging(task_id=task_id)
    signal.signal(signal.SIGINT, signal.SIG_IGN)
    signal.signal(signal.SIGTERM, _on_terminate)


def _send(events: TaskEvents, event: Tuple[str, Any]) -> None:
    """Sends the task's outcome; a failure (the parent is gone) is logged, never raised."""
    try:
        events.send(event)
    except Exception:
        logger.warning("task outcome: failed to send %s", event[0])


def run_task(target: Callable[..., Any], task_id: str, args: tuple, events: TaskEvents) -> None:
    """The child entry: runs `target(task_id, *args, progress=...)` with its log
    forwarded, then sends ("done", result) or ("failed", message) and closes
    the events; a cancelled task sends nothing."""
    _configure_child(task_id)
    handler = task_log_handler(events)
    task_loggers = [logging.getLogger(name) for name in APP_LOGGERS]
    for task_logger in task_loggers:
        task_logger.addHandler(handler)
    try:
        result = target(task_id, *args, progress=TaskProgress(events).report)
        _send(events, ("done", result))
    except Cancelled:
        pass
    except Exception as exc:
        _send(events, ("failed", str(exc) or repr(exc)))
    finally:
        for task_logger in task_loggers:
            task_logger.removeHandler(handler)
        events.close()


# --- parent side ------------------------------------------------------------


@dataclass
class _Task:
    task_id: str
    target: Callable[..., Any]
    args: tuple
    status: TaskStatus
    process: Optional[multiprocessing.process.BaseProcess] = None


class MultiprocessingTaskRunner(ITaskRunner):
    """Submits, reports and cancels tasks; at most `concurrency` run at once,
    the rest wait as PENDING. `target` must be a module-level function and
    `args` plain picklable data, since the child is spawned."""

    def __init__(self, log: ITaskLog, concurrency: Optional[int] = None):
        self._log = log
        self._concurrency = max(1, concurrency or os.cpu_count() or 1)
        self._ctx = multiprocessing.get_context("spawn")
        self._lock = threading.Lock()
        self._tasks: Dict[str, _Task] = {}
        self._pending: Deque[str] = deque()
        self._running = 0

    @property
    def concurrency(self) -> int:
        return self._concurrency

    def submit(self, target: Callable[..., Any], *args: Any) -> str:
        """Queues `target(task_id, *args, progress=...)` and returns the task id."""
        task_id = uuid.uuid4().hex
        with self._lock:
            self._tasks[task_id] = _Task(task_id, target, args, TaskStatus(task_id, PENDING))
            self._pending.append(task_id)
        self._dispatch()
        return task_id

    def status(self, task_id: str) -> TaskStatus:
        """The task's status; an unknown id reports as PENDING."""
        with self._lock:
            task = self._tasks.get(task_id)
            return task.status if task is not None else TaskStatus(task_id, PENDING)

    def cancel(self, task_id: str) -> TaskStatus:
        """Revokes a pending or running task and returns its status; a finished
        task keeps its status, an unknown id is recorded as REVOKED."""
        process = None
        with self._lock:
            task = self._tasks.get(task_id)
            if task is None:
                task = self._tasks[task_id] = _Task(task_id, None, (), TaskStatus(task_id, REVOKED))
            elif task.status.state == PENDING:
                self._pending.remove(task_id)
                task.status = TaskStatus(task_id, REVOKED)
            elif task.status.state == STARTED:
                task.status = task.status.ended(REVOKED)
                process = task.process
            status = task.status
        if process is not None:
            process.terminate()
        return status

    def _dispatch(self) -> None:
        with self._lock:
            while self._pending and self._running < self._concurrency:
                task = self._tasks[self._pending.popleft()]
                parent_conn, child_conn = self._ctx.Pipe(duplex=False)
                process = self._ctx.Process(
                    target=run_task, args=(task.target, task.task_id, task.args, child_conn),
                    daemon=True, name=f"dve-task-{task.task_id[:8]}",
                )
                process.start()
                child_conn.close()
                task.process = process
                task.status = TaskStatus(task.task_id, STARTED, started_at=time.time())
                self._running += 1
                threading.Thread(target=self._watch, args=(task, parent_conn), daemon=True).start()

    def _watch(self, task: _Task, conn) -> None:
        """Applies the child's events until its end of the pipe closes, then
        reaps it and frees the slot."""
        try:
            while True:
                try:
                    kind, payload = conn.recv()
                except (EOFError, OSError):
                    break
                self._apply(task, kind, payload)
        finally:
            conn.close()
        task.process.join(STOP_TIMEOUT_SECONDS)
        if task.process.is_alive():
            task.process.kill()
            task.process.join()
        with self._lock:
            if task.status.state == STARTED:
                task.status = task.status.ended(FAILURE, error=f"task process exited with code {task.process.exitcode}")
            self._running -= 1
        self._dispatch()

    def _apply(self, task: _Task, kind: str, payload: Any) -> None:
        if kind == "log":
            self._log.append(task.task_id, payload)
            return
        with self._lock:
            if task.status.state != STARTED:
                return
            if kind == "progress":
                task.status = TaskStatus(task.task_id, STARTED, progress=payload, started_at=task.status.started_at)
            elif kind == "done":
                task.status = task.status.ended(SUCCESS, result=payload)
            elif kind == "failed":
                task.status = task.status.ended(FAILURE, error=payload)
