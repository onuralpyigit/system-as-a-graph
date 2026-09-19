"""In-memory production log (SRS DSM-DVE req 6, 8)."""

from __future__ import annotations

from typing import Dict, List

from dve.ports.production_log import IProductionLog


class FakeProductionLog(IProductionLog):
    def __init__(self) -> None:
        self._lines: Dict[str, List[str]] = {}

    def append(self, run_id: str, line: str) -> None:
        self._lines.setdefault(run_id, []).append(line)

    def lines_since(self, run_id: str, index: int) -> List[str]:
        return list(self._lines.get(run_id, ())[max(index, 0):])
