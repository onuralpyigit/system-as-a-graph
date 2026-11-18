"""Test doubles around the task runner port: a synchronous runner that stands
in for the port, and a scripted task for the real runner to spawn
(SRS DSM-DVE req 6)."""

from __future__ import annotations

import logging
import os
import time
import uuid
from typing import Any, Callable, Dict, List, Union

from dve.domain.task_status import TaskStatus
from dve.ports.task_runner import ITaskRunner


class FakeTaskRunner(ITaskRunner):
    """Records every submit as (target, args) and reports the task as
    succeeded, never calling the target; `states` are statuses reported in
    order before the recorded outcome."""

    def __init__(self, states: List[Union[str, TaskStatus]] = ()):
        self._states = list(states)
        self._reported = 0
        self._tasks: Dict[str, TaskStatus] = {}
        self.submitted: List[tuple] = []

    def submit(self, target: Callable[..., Any], *args: Any) -> str:
        task_id = uuid.uuid4().hex
        self.submitted.append((target, args))
        self._tasks[task_id] = TaskStatus(task_id, "SUCCESS", result={"selection": args[0]})
        return task_id

    def status(self, task_id: str) -> TaskStatus:
        known = self._tasks.get(task_id)
        if known is None:
            return TaskStatus(task_id, "PENDING")
        if self._reported < len(self._states):
            entry = self._states[self._reported]
            self._reported += 1
            if isinstance(entry, TaskStatus):
                return TaskStatus(task_id, entry.state, progress=entry.progress)
            return TaskStatus(task_id, entry)
        return known

    def cancel(self, task_id: str) -> TaskStatus:
        known = self._tasks.get(task_id)
        if known is not None and known.state in ("SUCCESS", "FAILURE"):
            return known
        self._tasks[task_id] = TaskStatus(task_id, "REVOKED")
        return self._tasks[task_id]


def scripted_task(task_id: str, mode: str, progress) -> dict:
    """A task the task runner tests spawn: a module-level target the child can
    import without pytest, scripted by its `mode` argument.

    succeed: logs a line and returns; fail: raises; crash: exits without
    reporting; sleep: reports progress and waits to be terminated; noise: logs one
    line under DSM's own tree and one under another library's, to show which of
    them the task collects."""
    if mode == "succeed":
        logging.getLogger("dve.fakes.child").info("hello from child")
        return {"task_id": task_id}
    if mode == "noise":
        logging.getLogger("dve.fakes.child").info("ours")
        logging.getLogger("someclient.pool").info("theirs")
        return {"task_id": task_id}
    if mode == "fail":
        raise ValueError("boom")
    if mode == "crash":
        os._exit(3)
    if mode == "sleep":
        progress(42, "clone")
        while True:
            time.sleep(0.1)
    raise AssertionError(f"unknown mode {mode}")
