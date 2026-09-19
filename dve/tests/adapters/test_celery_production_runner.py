"""The Celery production runner with the task and AsyncResult mocked (SRS DSM-DVE req 6)."""

from unittest import mock

from celery import states

from fakes import seed
from dve.adapters.celery_production_runner import CeleryProductionRunner
from dve.domain.production_status import ProductionStatus
from dve.domain.selection import Selection

SELECTION = Selection(seed.PROJECT, seed.PLATFORM, seed.VERSION)


class _AsyncResult:
    def __init__(self, state, result=None, task_id=seed.RUN_1):
        self.id = task_id
        self.state = state
        self.result = result


def _status(state, result=None) -> ProductionStatus:
    with mock.patch("dve.adapters.celery_production_runner.AsyncResult", return_value=_AsyncResult(state, result)):
        return CeleryProductionRunner().status(seed.RUN_1)


def test_start_submits_the_selection_and_sources_as_json_payloads():
    with mock.patch("dve.adapters.celery_production_runner.produce_model_setup_data") as task:
        task.delay.return_value = _AsyncResult(states.PENDING)

        run_id = CeleryProductionRunner().start(SELECTION, seed.DEFAULTS, produced_by=seed.OPERATOR, candidate=seed.CANDIDATE)

    assert run_id == seed.RUN_1
    task.delay.assert_called_once_with(
        seed.SELECTION,
        {t.value: s.to_dict() for t, s in seed.DEFAULTS.items()},
        seed.OPERATOR,
        seed.CANDIDATE,
    )


def test_cancel_revokes_with_terminate_and_reports_the_status():
    with mock.patch("dve.adapters.celery_production_runner.AsyncResult") as async_result:
        async_result.return_value.state = states.REVOKED

        status = CeleryProductionRunner().cancel(seed.RUN_1)

    async_result.return_value.revoke.assert_called_once_with(terminate=True)
    assert status == ProductionStatus(seed.RUN_1, "REVOKED")


def test_success_carries_the_result_and_failure_the_message():
    assert _status(states.SUCCESS, {"run_id": seed.RUN_1}) == ProductionStatus(seed.RUN_1, "SUCCESS", result={"run_id": seed.RUN_1})
    assert _status(states.SUCCESS, "plain").result == {"value": "plain"}
    assert _status(states.FAILURE, ValueError("boom")).error == "boom"
    assert "ValueError" in _status(states.FAILURE, ValueError()).error
    assert _status(states.FAILURE).error == "task failed without a stored error"


def test_started_carries_only_a_progress_shaped_meta():
    assert _status(states.STARTED, {"percent": 42, "phase": "clone"}).progress == {"percent": 42, "phase": "clone"}
    assert _status(states.STARTED, {"pid": 42, "hostname": "celery@host"}).progress is None
    assert _status(states.STARTED, "not-a-dict").progress is None
    assert _status(states.PENDING) == ProductionStatus(seed.RUN_1, "PENDING")
