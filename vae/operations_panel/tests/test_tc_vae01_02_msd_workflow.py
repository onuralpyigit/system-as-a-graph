"""
Description: TC-VAE01-02 — Model Setup Data Workflow Manager (SRS VAE-01.5-8).
Created by: Mustafa Can Caliskan
Date: 2026-07-31
"""

from __future__ import annotations

import pytest

from vae.operations_panel.src.model.production_job import (
    JobStatus,
    ModelSetupDataFile,
    ProductionError,
)
from vae.operations_panel.src.model.source_status import Accessibility, SourceStatus
from vae.operations_panel.src.ports.model_setup_data import ProductionOutcome
from vae.operations_panel.src.use_cases.manage_model_setup_data import (
    UnknownModelSetupDataFile,
    UnknownProductionJob,
)
from vae.operations_panel.tests.conftest import FIXED_NOW, build_panel


def _file(run_id: str) -> ModelSetupDataFile:
    return ModelSetupDataFile(
        run_id=run_id,
        file_path=f"/var/lib/saag/msd/{run_id}.json",
        produced_at=FIXED_NOW,
        entity_count=13,
        relation_count=12,
    )


def test_produced_files_are_listed_and_one_can_be_selected(panel):
    """The operator picks which produced file to use (SRS VAE-01.5)."""
    panel.select_effective_scope()
    panel.gateway.files = [_file("run-a"), _file("run-b")]

    listed = panel.workflow.list_files(panel.session.current("operator").system_version)
    assert [item.run_id for item in listed] == ["run-a", "run-b"]

    panel.workflow.select_file("operator", "run-b")
    assert panel.session.current("operator").selected_model_setup_data_run_id == "run-b"


def test_selecting_a_file_that_was_not_produced_is_refused(panel):
    """A selection must name a file that exists for the operator's scope."""
    panel.select_effective_scope()
    panel.gateway.files = [_file("run-a")]

    with pytest.raises(UnknownModelSetupDataFile):
        panel.workflow.select_file("operator", "run-z")


def test_changing_the_selected_version_clears_the_selected_file(panel):
    """A file belongs to the version it was produced for."""
    from shared.types.identifiers import system_version
    from vae.operations_panel.tests.conftest import OLDER_VERSION, PLATFORM, PROJECT

    panel.select_effective_scope()
    panel.gateway.files = [_file("run-a")]
    panel.workflow.select_file("operator", "run-a")

    panel.session.select("operator", system_version(PROJECT, PLATFORM, OLDER_VERSION))

    assert panel.session.current("operator").selected_model_setup_data_run_id == ""


def test_production_reports_a_successful_process(panel):
    """A started process reaches the successful state (SRS VAE-01.6)."""
    scope = panel.select_effective_scope().system_version
    panel.gateway.outcome = ProductionOutcome(
        run_id="msd-run-1",
        succeeded=True,
        file_path="/var/lib/saag/msd/msd_2026-07-31_avionics.json",
        entity_count=13,
        relation_count=12,
    )

    job = panel.workflow.start_production("operator", scope)
    status = panel.workflow.status(job.job_id)

    assert status.status is JobStatus.SUCCEEDED
    assert status.run_id == "msd-run-1"
    assert status.entity_count == 13
    assert status.finished_at == panel.clock.now()
    assert panel.gateway.produced == [scope]


def test_a_process_that_produced_nothing_is_reported_failed(panel):
    """Failure carries the reason MSD recorded, not a generic message."""
    scope = panel.select_effective_scope().system_version
    panel.gateway.outcome = ProductionOutcome(
        run_id="msd-run-2",
        succeeded=False,
        errors=[
            ProductionError(
                status="missing_data",
                reason="No Software Unit Version Inventory recorded",
                source_name="cmdb-primary",
                source_type="configuration_management_database",
                occurred_at=FIXED_NOW,
            )
        ],
    )

    job = panel.workflow.start_production("operator", scope)
    status = panel.workflow.status(job.job_id)

    assert status.status is JobStatus.FAILED
    assert "Inventory" in status.failure_reason


def test_a_crashing_process_is_reported_failed_rather_than_hanging(panel):
    """An operator watching a process must never wait on one that never resolves."""
    scope = panel.select_effective_scope().system_version
    panel.gateway.raises = RuntimeError("source repository exploded")

    job = panel.workflow.start_production("operator", scope)
    status = panel.workflow.status(job.job_id)

    assert status.status is JobStatus.FAILED
    assert "exploded" in status.failure_reason


def test_a_successful_process_still_reports_recorded_errors(panel):
    """Production can succeed while having recorded failures (SRS VAE-01.8)."""
    scope = panel.select_effective_scope().system_version
    panel.gateway.outcome = ProductionOutcome(
        run_id="msd-run-3",
        succeeded=True,
        file_path="/var/lib/saag/msd/file.json",
        errors=[
            ProductionError(
                status="format_incompatible",
                reason="descriptor is not well-formed XML",
                source_name="bitbucket-a",
                source_type="source_repository",
                occurred_at=FIXED_NOW,
            )
        ],
    )

    job = panel.workflow.start_production("operator", scope)

    assert panel.workflow.status(job.job_id).status is JobStatus.SUCCEEDED
    assert panel.workflow.status(job.job_id).error_count == 1


def test_recorded_failures_are_presented_to_the_operator(panel):
    """Missing-data, access, authorization, format, integrity — all one list."""
    scope = panel.select_effective_scope().system_version
    panel.gateway.errors = [
        ProductionError(
            status=status,
            reason=f"{status} happened",
            source_name="bitbucket-b",
            source_type="source_repository",
            occurred_at=FIXED_NOW,
        )
        for status in (
            "missing_data",
            "access_error",
            "authorization_error",
            "format_incompatible",
            "integrity_error",
        )
    ]

    presented = panel.workflow.errors(scope)

    assert {item.status for item in presented} == {
        "missing_data",
        "access_error",
        "authorization_error",
        "format_incompatible",
        "integrity_error",
    }


def test_a_configured_source_is_listed_with_its_secret_status_only(panel):
    """The secret itself never comes back out of the workflow (SRS MSD.8)."""
    panel.workflow.configure_data_source(
        source_type="source_repository",
        name="bitbucket-a",
        access_method="git_https",
        connection_address="https://bitbucket.example/scm/saag",
        username="ops",
        secret="s3cr3t-token",
        priority=0,
    )

    listed = panel.workflow.list_data_sources()

    assert len(listed) == 1
    assert listed[0].username == "ops"
    assert listed[0].secret_set is True
    assert not hasattr(listed[0], "secret")


def test_editing_a_source_without_a_secret_keeps_the_stored_one(panel):
    """Address/priority can change without re-entering the secret."""
    panel.workflow.configure_data_source(
        source_type="source_repository",
        name="bitbucket-a",
        access_method="git_https",
        connection_address="https://bitbucket.example/scm/saag",
        username="ops",
        secret="s3cr3t-token",
        priority=0,
    )

    edited = panel.workflow.configure_data_source(
        source_type="source_repository",
        name="bitbucket-a",
        access_method="git_https",
        connection_address="https://bitbucket.example/scm/saag-v2",
        username="ops",
        secret=None,
        priority=1,
    )

    assert edited.connection_address == "https://bitbucket.example/scm/saag-v2"
    assert edited.priority == 1
    assert edited.secret_set is True


def test_a_deleted_source_no_longer_appears(panel):
    """Removing a source's configuration removes it from the listing."""
    panel.workflow.configure_data_source(
        source_type="network_topology",
        name="ansible-tree",
        access_method="ansible",
        connection_address="/etc/saag/ansible",
        username="",
        secret=None,
        priority=0,
    )

    assert panel.workflow.delete_data_source("network_topology", "ansible-tree") is True
    assert panel.workflow.list_data_sources() == []
    assert panel.workflow.delete_data_source("network_topology", "ansible-tree") is False


def test_an_unknown_process_identifier_is_refused(panel):
    """Monitoring something that was never started is an error, not an empty status."""
    with pytest.raises(UnknownProductionJob):
        panel.workflow.status("no-such-job")


def test_source_accessibility_is_probed_and_recorded(panel):
    """The status is traceable afterwards, not only visible at the moment (VAE-01.7)."""
    panel.gateway.sources = [
        SourceStatus(
            source_type="source_repository",
            source_name="bitbucket-a",
            accessibility=Accessibility.REACHABLE,
            checked_at=FIXED_NOW,
        ),
        SourceStatus(
            source_type="source_repository",
            source_name="bitbucket-b",
            accessibility=Accessibility.UNREACHABLE,
            checked_at=FIXED_NOW,
            detail="connection refused",
        ),
    ]

    snapshot = panel.workflow.check_sources()

    assert snapshot.all_reachable is False
    assert [item.source_name for item in snapshot.unreachable] == ["bitbucket-b"]
    assert panel.workflow.latest_source_status().checked_at == snapshot.checked_at
    assert len(panel.workflow.latest_source_status().statuses) == 2


class _DeferringQueue:
    """A queue that records the request and runs nothing.

    Stands in for the Procrastinate worker not having picked the job up yet,
    which is the only way to observe the in-progress state from outside.
    """

    def __init__(self) -> None:
        self.deferred = []

    def enqueue(self, request) -> None:
        """Record the request without executing it."""
        self.deferred.append(request)


def test_a_started_process_is_in_progress_until_the_worker_runs_it(users_file):
    """The third of VAE-01.6's statuses is real, not a value that never appears."""
    queue = _DeferringQueue()
    panel = build_panel(users_file, queue=queue)
    scope = panel.select_effective_scope().system_version

    job = panel.workflow.start_production("operator", scope)

    assert panel.workflow.status(job.job_id).status is JobStatus.IN_PROGRESS
    assert panel.workflow.status(job.job_id).finished_at is None
    # The run this job will execute under is known while still in progress,
    # not only once it resolves — that's what makes its errors fetchable
    # (list_errors_for_run) before completion.
    assert panel.workflow.status(job.job_id).run_id != ""
    assert [request.job_id for request in queue.deferred] == [job.job_id]

    panel.workflow.run(queue.deferred[0])

    assert panel.workflow.status(job.job_id).status is JobStatus.SUCCEEDED
    assert panel.workflow.status(job.job_id).finished_at == panel.clock.now()
