"""Celery adapter of the production runner port over dve's worker task
(SRS DSM-DVE req 6, 50)."""

from __future__ import annotations

from typing import Any, Dict, Optional

from celery import states
from celery.result import AsyncResult

from mdg import DataSourceConfig, SourceType

from dve.domain.production_status import ProductionStatus
from dve.domain.selection import Selection
from dve.ports.production_runner import IProductionRunner
from dve.worker import celery_app, produce_model_setup_data


class CeleryProductionRunner(IProductionRunner):
    """Submits the produce_model_setup_data task and reads its state from the result backend."""

    def __init__(self, app=None):
        self._app = app or celery_app

    def start(
        self,
        selection: Selection,
        sources: Dict[SourceType, DataSourceConfig],
        produced_by: Optional[str] = None,
        candidate: Optional[dict] = None,
    ) -> str:
        payload = {source_type.value: source.to_dict() for source_type, source in sources.items()}
        return produce_model_setup_data.delay(selection.to_dict(), payload, produced_by, candidate).id

    def status(self, run_id: str) -> ProductionStatus:
        result = AsyncResult(run_id, app=self._app)
        state, value = result.state, result.result
        if state == states.FAILURE:
            return ProductionStatus(run_id, state, error=self._failure_message(value))
        if state == states.SUCCESS:
            return ProductionStatus(run_id, state, result=self._result(value))
        progress = value if isinstance(value, dict) and "percent" in value else None
        return ProductionStatus(run_id, state, progress=progress)

    def cancel(self, run_id: str) -> ProductionStatus:
        AsyncResult(run_id, app=self._app).revoke(terminate=True)
        return self.status(run_id)

    @staticmethod
    def _failure_message(value: Any) -> str:
        if value is None:
            return "task failed without a stored error"
        return str(value) or repr(value)

    @staticmethod
    def _result(value: Any) -> Optional[Dict[str, Any]]:
        if value is None or isinstance(value, dict):
            return value
        return {"value": value}
