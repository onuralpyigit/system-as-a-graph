"""Port for running tasks in the background and tracking them
(SRS DSM-DVE req 6, 50)."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Callable

from dve.domain.task_status import TaskStatus


class ITaskRunner(ABC):
    """Submits, reports and cancels background tasks."""

    @abstractmethod
    def submit(self, target: Callable[..., Any], *args: Any) -> str:
        """Queues `target(task_id, *args, progress=...)` and returns the task id;
        `target` must be a module-level function and `args` plain picklable data."""

    @abstractmethod
    def status(self, task_id: str) -> TaskStatus:
        """The current status of a task; an unknown id reports as PENDING (req 6)."""

    @abstractmethod
    def cancel(self, task_id: str) -> TaskStatus:
        """Revokes a queued or running task and returns its status (req 6)."""
