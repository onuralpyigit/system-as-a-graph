"""The task service over a recording task runner and log, and its child-side
production with mdg mocked (SRS DSM-DVE req 6, 8)."""

from unittest import mock

import pytest

from fakes import seed
from mdg import CandidateUnitVersion, SourceType
from dve.adapters.in_memory_task_log import InMemoryTaskLog
from dve.domain.selection import Selection
from dve.domain.task_status import TaskStatus
from dve.services import task_service
from dve.services.task_service import TaskService, run_production

SELECTION = Selection(seed.PROJECT, seed.PLATFORM, seed.VERSION)
SOURCES = {source_type.value: source.to_dict() for source_type, source in seed.DEFAULTS.items()}


class _Runner:
    def __init__(self, status=None):
        self.submitted = None
        self.cancelled = None
        self._status = status or TaskStatus(seed.RUN_1, "PENDING")

    def submit(self, target, *args):
        self.submitted = (target, args)
        return seed.RUN_1

    def status(self, task_id):
        return self._status

    def cancel(self, task_id):
        self.cancelled = task_id
        return self._status


def test_start_production_submits_the_production_with_json_payloads():
    runner = _Runner()

    task_id = TaskService(runner, InMemoryTaskLog()).start_production(
        SELECTION, seed.DEFAULTS, produced_by=seed.OPERATOR, candidates=seed.CANDIDATES
    )

    assert task_id == seed.RUN_1
    assert runner.submitted == (run_production, (seed.SELECTION, SOURCES, seed.OPERATOR, seed.CANDIDATES))


def test_status_and_cancel_report_the_runners_status():
    status = TaskStatus(seed.RUN_1, "STARTED", progress={"percent": 42, "phase": "clone"}, started_at=100.0)
    runner = _Runner(status)
    tasks = TaskService(runner, InMemoryTaskLog())

    assert tasks.status(seed.RUN_1) is status
    assert tasks.cancel(seed.RUN_1) is status
    assert runner.cancelled == seed.RUN_1


def test_log_since_reads_the_tasks_lines_from_the_log():
    log = InMemoryTaskLog()
    for line in ("one", "two", "three"):
        log.append(seed.RUN_1, line)
    tasks = TaskService(_Runner(), log)

    assert tasks.log_since(seed.RUN_1, 1) == ["two", "three"]
    assert tasks.log_since(seed.RUN_2, 0) == []


def _produce(result=None):
    produce = mock.Mock()
    produce.return_value.to_dict.return_value = result if result is not None else {}
    return produce


def _run(produce, produced_by=None, candidates=None, selection=seed.SELECTION):
    progress = mock.Mock()
    with mock.patch.object(task_service.mdg, "produce_model_setup_data", produce), \
         mock.patch.object(task_service.mdg, "config_management_repository") as config_repo, \
         mock.patch.object(task_service.mdg, "source_code_repository") as source_repo:
        result = run_production(seed.RUN_1, selection, SOURCES, produced_by, candidates, progress)
    return result, config_repo, source_repo, progress


def test_production_rebuilds_the_sources_and_calls_mdg_with_the_run_id():
    produce = _produce({"run_id": "sentinel"})

    result, config_repo, source_repo, progress = _run(produce)

    assert result == {"run_id": "sentinel"}
    assert config_repo.call_args.args[0] == seed.DEFAULTS[SourceType.CONFIG_MGMT_DB]
    assert source_repo.call_args.args[0] == seed.DEFAULTS[SourceType.SOURCE_CODE_REPO]
    produce.assert_called_once_with(
        config_repo.return_value, source_repo.return_value, seed.PROJECT, seed.PLATFORM, seed.VERSION,
        run_id=seed.RUN_1, produced_by=None, candidates=[], progress=progress,
    )


def test_production_forwards_the_producer_and_converts_the_candidates():
    produce = _produce()

    _run(produce, produced_by=seed.OPERATOR, candidates=[seed.CANDIDATE, {"unit_name": seed.NAV_APP, "version": "2.0.0"}])

    assert produce.call_args.kwargs["produced_by"] == seed.OPERATOR
    assert produce.call_args.kwargs["candidates"] == [
        CandidateUnitVersion(seed.SENSOR_APP, seed.CANDIDATE_VERSION),
        CandidateUnitVersion(seed.NAV_APP, "2.0.0"),
    ]


def test_production_ignores_an_unusable_candidate():
    produce = _produce()

    _run(produce, produced_by=seed.OPERATOR, candidates=[{"unit_name": seed.SENSOR_APP}, seed.CANDIDATE])

    assert produce.call_args.kwargs["candidates"] == [CandidateUnitVersion(seed.SENSOR_APP, seed.CANDIDATE_VERSION)]


def test_production_refuses_an_incomplete_selection():
    with pytest.raises(ValueError, match="incomplete selection"):
        _run(_produce(), selection={"project_id": seed.PROJECT})
