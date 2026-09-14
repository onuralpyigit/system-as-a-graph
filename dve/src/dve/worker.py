"""DVE's Celery worker: the Celery app and the produce_model_setup_data task,
which runs mdg's production with the session's data sources and publishes
its log lines and progress (SRS DSM-DVE req 6, 8).

Run with: python -m dve.worker [--concurrency=N] (the dsm command starts it together with the API).
"""

import logging
import sys
from typing import Dict, List

from celery import Celery, states

import mdg
from mdg import CandidateUnitVersion, DataSourceConfig, SourceType

from dve.adapters.redis_production_log import RedisProductionLog
from dve.config import config
from dve.domain.selection import Selection
from dve.ports.production_log import IProductionLog

logger = logging.getLogger(__name__)


class ProductionLogHandler(logging.Handler):
    """Copies the run's log records (INFO and above) into the production log;
    a log store failure is logged, never raised (req 8)."""

    def __init__(self, log: IProductionLog, run_id: str):
        super().__init__(level=logging.INFO)
        self.setFormatter(logging.Formatter("%(asctime)s %(levelname)-8s %(message)s", datefmt="%H:%M:%S"))
        self._log = log
        self._run_id = run_id
        self._emitting = False

    def emit(self, record: logging.LogRecord) -> None:
        if self._emitting:
            return
        self._emitting = True
        try:
            self._log.append(self._run_id, self.format(record))
        except Exception:
            logger.warning("production log: failed to record a line for run %s", self._run_id)
        finally:
            self._emitting = False


class ProductionProgress:
    """Publishes each (percent, phase) step as the task's STARTED meta; a
    backend failure is logged, never raised (req 6)."""

    def __init__(self, task):
        self._task = task

    def report(self, percent: int, phase: str) -> None:
        try:
            self._task.update_state(state=states.STARTED, meta={"percent": percent, "phase": phase})
        except Exception:
            logger.warning("production progress: failed to record progress for run %s", self._task.request.id)


def make_celery() -> Celery:
    """The Celery app of the [worker] section; run records are kept until Redis is cleared."""
    settings = config().worker
    app = Celery("dve")
    app.config_from_object({
        "broker_url": settings.broker_url,
        "result_backend": settings.result_backend,
        "result_expires": None,
        "task_track_started": True,
        "task_serializer": "json",
        "result_serializer": "json",
        "accept_content": ["json"],
    })
    return app


celery_app = make_celery()


def _production_log() -> IProductionLog:
    return RedisProductionLog(config().worker.result_backend)


def _data_sources(sources: dict) -> Dict[SourceType, DataSourceConfig]:
    return {SourceType(key): DataSourceConfig.from_dict(value) for key, value in sources.items()}


@celery_app.task(bind=True, name="dve.produce_model_setup_data")
def produce_model_setup_data(self, selection: dict, sources: dict, produced_by: str = None, candidate: dict = None) -> dict:
    """One Model Setup Data production, with this task's id as the run id;
    `sources` maps source type values to DataSourceConfig payloads and
    `candidate` is the optional {"unit_name", "version"} under evaluation (req 6)."""
    handler = ProductionLogHandler(_production_log(), self.request.id)
    logging.getLogger().addHandler(handler)
    try:
        chosen = Selection.from_dict(selection)
        if chosen is None:
            raise ValueError(f"incomplete selection: {selection}")
        data_sources = _data_sources(sources)
        return mdg.produce_model_setup_data(
            mdg.config_management_repository(data_sources[SourceType.CONFIG_MGMT_DB]),
            mdg.source_code_repository(data_sources[SourceType.SOURCE_CODE_REPO]),
            chosen.project_id,
            chosen.platform_id,
            chosen.version_id,
            run_id=self.request.id,
            produced_by=produced_by,
            candidate=CandidateUnitVersion.from_dict(candidate),
            progress=ProductionProgress(self).report,
        ).to_dict()
    finally:
        logging.getLogger().removeHandler(handler)


def main(argv: List[str] = None) -> None:
    """Runs the worker in this process; extra arguments go to Celery (e.g. --concurrency=4)."""
    celery_app.worker_main(["worker", "--loglevel=info", *(argv if argv is not None else sys.argv[1:])])


if __name__ == "__main__":
    main()
