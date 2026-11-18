"""Port for the log lines a background task writes while it runs, shown to the
user as the task's output (SRS DSM-DVE req 6, 8)."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List


class ITaskLog(ABC):
    """Appends and reads the ordered log lines of a task."""

    @abstractmethod
    def append(self, task_id: str, line: str) -> None:
        """Records one line at the end of the task's log."""

    @abstractmethod
    def lines_since(self, task_id: str, index: int) -> List[str]:
        """The lines from 0-based `index` to the end; empty for an unknown task."""
