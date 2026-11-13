"""The task status and the payload the API serves for it (SRS DSM-DVE req 6)."""

import pytest

from fakes import seed
from dve.domain.task_status import TaskStatus


@pytest.mark.parametrize("status, payload", [
    (TaskStatus(seed.RUN_1, "PENDING"), {"task_id": seed.RUN_1, "state": "PENDING"}),
    (
        TaskStatus(seed.RUN_1, "STARTED", progress={"percent": 42, "phase": "clone"}, started_at=100.0),
        {"task_id": seed.RUN_1, "state": "STARTED", "progress": {"percent": 42, "phase": "clone"}, "started_at": 100.0},
    ),
    (
        TaskStatus(seed.RUN_1, "SUCCESS", result={}, started_at=100.0, finished_at=122.5),
        {"task_id": seed.RUN_1, "state": "SUCCESS", "result": {}, "started_at": 100.0, "finished_at": 122.5},
    ),
    (TaskStatus(seed.RUN_1, "FAILURE", error="boom"), {"task_id": seed.RUN_1, "state": "FAILURE", "error": "boom"}),
])
def test_to_dict_carries_only_the_parts_that_are_set(status, payload):
    assert status.to_dict() == payload


def test_ended_keeps_the_start_and_stamps_the_end():
    started = TaskStatus(seed.RUN_1, "STARTED", progress={"percent": 42, "phase": "clone"}, started_at=100.0)

    ended = started.ended("SUCCESS", result={"ok": True})

    assert ended == TaskStatus(seed.RUN_1, "SUCCESS", result={"ok": True})
    assert ended.started_at == 100.0
    assert ended.finished_at is not None
