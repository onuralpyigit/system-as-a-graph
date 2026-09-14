"""Port for the log lines a production run writes while it runs, shown to the
user as the run's output (SRS DSM-DVE req 6, 8)."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List


class IProductionLog(ABC):
    """Appends and reads the ordered log lines of a run."""

    @abstractmethod
    def append(self, run_id: str, line: str) -> None:
        """Records one line at the end of the run's log."""

    @abstractmethod
    def lines_since(self, run_id: str, index: int) -> List[str]:
        """The lines from 0-based `index` to the end; empty for an unknown run."""
