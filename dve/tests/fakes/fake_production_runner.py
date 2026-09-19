"""Synchronous production runner: start() runs a callable in-process and
records the outcome as the run's status (SRS DSM-DVE req 6)."""

from __future__ import annotations

import uuid
from typing import Callable, Dict, List, Optional, Union

from mdg import DataSourceConfig, SourceType

from dve.domain.production_status import ProductionStatus
from dve.domain.selection import Selection
from dve.ports.production_runner import IProductionRunner


class FakeProductionRunner(IProductionRunner):
    """Records every start as (selection, sources, produced_by, candidate);
    `states` are statuses reported in order before the recorded outcome."""

    def __init__(self, run: Optional[Callable[..., dict]] = None, states: List[Union[str, ProductionStatus]] = ()):
        self._run = run or (lambda selection, sources, produced_by, candidate: {"selection": selection.to_dict()})
        self._states = list(states)
        self._reported = 0
        self._runs: Dict[str, ProductionStatus] = {}
        self.started: List[tuple] = []

    def start(
        self,
        selection: Selection,
        sources: Dict[SourceType, DataSourceConfig],
        produced_by: Optional[str] = None,
        candidate: Optional[dict] = None,
    ) -> str:
        run_id = uuid.uuid4().hex
        self.started.append((selection, sources, produced_by, candidate))
        try:
            result = self._run(selection, sources, produced_by, candidate)
        except Exception as exc:
            self._runs[run_id] = ProductionStatus(run_id, "FAILURE", error=str(exc) or repr(exc))
        else:
            self._runs[run_id] = ProductionStatus(run_id, "SUCCESS", result=result)
        return run_id

    def status(self, run_id: str) -> ProductionStatus:
        known = self._runs.get(run_id)
        if known is None:
            return ProductionStatus(run_id, "PENDING")
        if self._reported < len(self._states):
            entry = self._states[self._reported]
            self._reported += 1
            if isinstance(entry, ProductionStatus):
                return ProductionStatus(run_id, entry.state, progress=entry.progress)
            return ProductionStatus(run_id, entry)
        return known

    def cancel(self, run_id: str) -> ProductionStatus:
        known = self._runs.get(run_id)
        if known is not None and known.state in ("SUCCESS", "FAILURE"):
            return known
        self._runs[run_id] = ProductionStatus(run_id, "REVOKED")
        return self._runs[run_id]
