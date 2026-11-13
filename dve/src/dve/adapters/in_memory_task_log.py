"""In-memory adapter of the task log port: one line list per task, kept for the
process lifetime and bounded so a chatty run cannot grow it without end
(SRS DSM-DVE req 6, 8)."""

from __future__ import annotations

import threading
from typing import Dict, List

from dve.ports.task_log import ITaskLog

MAX_LINES = 5000
"""The lines one task's log may hold. A longer run stops collecting instead of
dropping its oldest lines, since a polling client reads by those indexes."""

TRUNCATION_NOTICE = "... log truncated at %d lines"


class InMemoryTaskLog(ITaskLog):
    """Appends and reads under a lock, since task threads write while request threads read."""

    def __init__(self, max_lines: int = MAX_LINES) -> None:
        self._lock = threading.Lock()
        self._lines: Dict[str, List[str]] = {}
        self._max_lines = max_lines

    def append(self, task_id: str, line: str) -> None:
        """Records one line at the end, once; after the bound the log ends with its
        truncation notice and stays as it is."""
        with self._lock:
            lines = self._lines.setdefault(task_id, [])
            if len(lines) >= self._max_lines:
                notice = TRUNCATION_NOTICE % self._max_lines
                if not lines or lines[-1] != notice:
                    lines.append(notice)
                return
            lines.append(line)

    def lines_since(self, task_id: str, index: int) -> List[str]:
        with self._lock:
            return list(self._lines.get(task_id, ())[max(index, 0):])
