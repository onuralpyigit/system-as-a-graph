"""The Celery worker: its app settings, the produce_model_setup_data task's
call into mdg, its progress channel and its log capture (SRS DSM-DVE req 6, 8)."""

import logging
import re
from unittest import mock

from celery import Celery, states

from fakes import seed
from fakes.fake_production_log import FakeProductionLog
from mdg import CandidateUnitVersion
from dve import worker
from dve.config import config

SOURCES = {source_type.value: source.to_dict() for source_type, source in seed.DEFAULTS.items()}


def test_main_runs_the_worker_with_the_given_arguments():
    with mock.patch.object(worker.celery_app, "worker_main") as worker_main:
        worker.main(["--concurrency=2"])

    worker_main.assert_called_once_with(["worker", "--loglevel=info", "--concurrency=2"])


def test_celery_app_comes_from_dve_ini_and_keeps_results_forever():
    assert isinstance(worker.celery_app, Celery)
    assert worker.celery_app.conf.broker_url == config().worker.broker_url
    assert worker.celery_app.conf.result_backend == config().worker.result_backend
    assert worker.celery_app.conf.result_expires is None
    assert "dve.produce_model_setup_data" in worker.celery_app.tasks


class _NullBackend:
    def store_result(self, *args, **kwargs):
        pass

    def mark_as_done(self, *args, **kwargs):
        pass

    def mark_as_failure(self, *args, **kwargs):
        pass

    def mark_as_retry(self, *args, **kwargs):
        pass


class _RecordingBackend(_NullBackend):
    def __init__(self):
        self.stored = []

    def store_result(self, *args, **kwargs):
        self.stored.append((args, kwargs))


class _FailingBackend(_NullBackend):
    def store_result(self, *args, **kwargs):
        raise RuntimeError("redis down")


def _apply(produce, args=(), backend=None):
    with mock.patch("dve.worker.mdg.produce_model_setup_data", produce), \
         mock.patch("dve.worker.mdg.config_management_repository") as config_repo, \
         mock.patch("dve.worker.mdg.source_code_repository") as source_repo, \
         mock.patch.object(Celery, "backend", new=property(lambda self: backend or _NullBackend())), \
         mock.patch("dve.worker._production_log", return_value=FakeProductionLog()):
        result = worker.produce_model_setup_data.apply(args=[seed.SELECTION, SOURCES, *args], task_id="task-eager")
    return result, config_repo, source_repo


def _produce(result=None):
    produce = mock.Mock()
    produce.return_value.to_dict.return_value = result if result is not None else {}
    return produce


def test_task_rebuilds_the_sources_and_calls_mdg_with_the_task_id_as_run_id():
    produce = _produce({"run_id": "sentinel"})

    result, config_repo, source_repo = _apply(produce)

    assert result.successful()
    assert result.result == {"run_id": "sentinel"}
    assert config_repo.call_args.args[0] == seed.DEFAULTS[worker.SourceType.CONFIG_MGMT_DB]
    assert source_repo.call_args.args[0] == seed.DEFAULTS[worker.SourceType.SOURCE_CODE_REPO]
    produce.assert_called_once_with(
        config_repo.return_value, source_repo.return_value, seed.PROJECT, seed.PLATFORM, seed.VERSION,
        run_id="task-eager", produced_by=None, candidate=None, progress=mock.ANY,
    )


def test_task_forwards_the_producer_and_converts_the_candidate():
    produce = _produce()

    _apply(produce, args=[seed.OPERATOR, seed.CANDIDATE])

    assert produce.call_args.kwargs["produced_by"] == seed.OPERATOR
    assert produce.call_args.kwargs["candidate"] == CandidateUnitVersion(seed.SENSOR_APP, seed.CANDIDATE_VERSION)


def test_task_ignores_an_unusable_candidate():
    produce = _produce()

    _apply(produce, args=[seed.OPERATOR, {"unit_name": seed.SENSOR_APP}])

    assert produce.call_args.kwargs["candidate"] is None


def _produce_reporting_progress(percent=42, phase="clone"):
    def execute(*args, **kwargs):
        kwargs["progress"](percent, phase)
        return mock.Mock()
    return mock.Mock(side_effect=execute)


def test_progress_is_published_as_the_tasks_started_meta():
    backend = _RecordingBackend()

    result, _, _ = _apply(_produce_reporting_progress(), backend=backend)

    assert result.successful()
    args, _ = next((a, k) for a, k in backend.stored if a and a[1] == {"percent": 42, "phase": "clone"})
    assert (args[0], args[2]) == ("task-eager", states.STARTED)


def test_a_dead_progress_channel_does_not_fail_the_run():
    result, _, _ = _apply(_produce_reporting_progress(), backend=_FailingBackend())

    assert result.successful()


def _record(message: str) -> logging.LogRecord:
    return logging.LogRecord("mdg.services.acquire_source_code", logging.INFO, __file__, 1, message, None, None)


def test_log_handler_appends_formatted_lines_and_swallows_store_errors():
    log = mock.Mock()
    handler = worker.ProductionLogHandler(log, seed.RUN_1)

    handler.emit(_record("acquire: nav_app 1.0.0 cloned"))

    run_id, line = log.append.call_args.args
    assert run_id == seed.RUN_1
    assert re.fullmatch(r"\d{2}:\d{2}:\d{2} INFO     acquire: nav_app 1\.0\.0 cloned", line)

    log.append.side_effect = RuntimeError("redis down")
    handler.emit(_record("still fine"))
