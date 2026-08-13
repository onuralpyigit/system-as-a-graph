"""
Description: Model Setup Data Workflow Manager design element (SRS VAE-01.5-8).
Created by: Mustafa Can Caliskan
Date: 2026-07-31
"""

from __future__ import annotations

from dataclasses import replace
from uuid import uuid4

from shared.types.identifiers import PlatformRef, SystemVersionRef
from vae.operations_panel.src.model.data_source import DataSourceConfig
from vae.operations_panel.src.model.production_job import (
    JobStatus,
    ModelSetupDataFile,
    ProductionError,
    ProductionJob,
    ProductionJobRequest,
)
from vae.operations_panel.src.model.source_status import SourceStatusSnapshot
from vae.operations_panel.src.ports.model_setup_data import ModelSetupDataGatewayPort
from vae.operations_panel.src.ports.repositories import (
    JobQueuePort,
    ProductionJobRepository,
    SourceStatusRepository,
    WorkingScopeRepository,
)
from vae.operations_panel.src.ports.support import ClockPort


class UnknownModelSetupDataFile(Exception):
    """Raised when an operator selects a file that was not produced for their scope."""


class UnknownProductionJob(Exception):
    """Raised when a production process identifier is not recognized."""


class ModelSetupDataWorkflowUseCase:
    """Lists and selects produced files, starts production, and reports its status.

    The panel never produces anything itself (SDD §3.6.1.1): it starts MSD's
    process and reports back. Starting returns as soon as the job is recorded,
    which is what lets the operator observe the in-progress state VAE-01.6
    requires rather than waiting out a synchronous call.

    Data source accessibility belongs to this element too (SDD §3.6.1.2): it is
    the same screen's status line, and it is what tells an operator whether a
    production run is worth starting at all.
    """

    def __init__(
        self,
        gateway: ModelSetupDataGatewayPort,
        jobs: ProductionJobRepository,
        queue: JobQueuePort,
        scopes: WorkingScopeRepository,
        statuses: SourceStatusRepository,
        clock: ClockPort,
    ) -> None:
        """Initialize the use case.

        Args:
            gateway: The panel's view of MSD.
            jobs: Store production processes are recorded in.
            queue: Runs the process outside the request that started it.
            scopes: Store each operator's selection lives in.
            statuses: Store accessibility snapshots are recorded in.
            clock: Supplies start and finish times.
        """
        self._gateway = gateway
        self._jobs = jobs
        self._queue = queue
        self._scopes = scopes
        self._statuses = statuses
        self._clock = clock

    def list_files(self, scope: SystemVersionRef) -> list[ModelSetupDataFile]:
        """List the Model Setup Data files produced for a scope (SRS VAE-01.5).

        Args:
            scope: Project/platform/system version to list for.
        """
        return self._gateway.list_model_setup_data_files(scope)

    def select_file(self, username: str, run_id: str) -> ModelSetupDataFile:
        """Record which produced file the operator will use (SRS VAE-01.5).

        Args:
            username: Operator making the selection.
            run_id: Identifier of the file to select.

        Returns:
            The selected file.

        Raises:
            UnknownProductionJob: If the operator has selected no scope yet.
            UnknownModelSetupDataFile: If no such file exists for that scope.
        """
        selection = self._scopes.get(username)
        if selection is None:
            raise UnknownProductionJob("No project/platform/version selected yet")

        for candidate in self.list_files(selection.system_version):
            if candidate.run_id == run_id:
                self._scopes.save(
                    replace(selection, selected_model_setup_data_run_id=run_id)
                )
                return candidate

        raise UnknownModelSetupDataFile(
            f"No Model Setup Data file '{run_id}' for {selection.system_version}"
        )

    def start_production(self, username: str, scope: SystemVersionRef) -> ProductionJob:
        """Start the Model Setup Data production process (SRS VAE-01.6).

        Args:
            username: Operator starting the process.
            scope: Project/platform/system version to produce for.

        Returns:
            The recorded process, in progress.
        """
        # Generated here, not inside run(), so the run this job will execute
        # under is known — and its errors fetchable — from the moment it's
        # in progress, not only once it resolves.
        run_id = uuid4().hex
        job = ProductionJob(
            job_id=uuid4().hex,
            system_version=scope,
            started_by=username,
            status=JobStatus.IN_PROGRESS,
            started_at=self._clock.now(),
            run_id=run_id,
        )
        self._jobs.save(job)

        self._queue.enqueue(
            ProductionJobRequest(
                job_id=job.job_id, system_version=scope, started_by=username, run_id=run_id
            )
        )
        return job

    def status(self, job_id: str) -> ProductionJob:
        """Report a production process's status (SRS VAE-01.6).

        Args:
            job_id: Identifier returned when the process was started.

        Returns:
            The process, in whichever of the three states it is now.

        Raises:
            UnknownProductionJob: If the identifier is not recognized.
        """
        job = self._jobs.get(job_id)
        if job is None:
            raise UnknownProductionJob(f"No production process '{job_id}'")
        return job

    def history(self, scope: SystemVersionRef) -> list[ProductionJob]:
        """List the production processes started for a scope, newest first.

        Args:
            scope: Project/platform/system version to list for.
        """
        return self._jobs.list_for(scope)

    def errors(self, scope: SystemVersionRef) -> list[ProductionError]:
        """List the failures recorded during production (SRS VAE-01.8).

        Missing-data, access, authorization, format, and integrity failures all
        arrive through this one list, exactly as MSD recorded them; the panel
        classifies nothing itself.

        Args:
            scope: Project/platform/system version to list for.
        """
        return self._gateway.list_errors(scope.platform)

    def errors_for_run(self, run_id: str) -> list[ProductionError]:
        """List the failures recorded during one production run (SRS VAE-01.8).

        Args:
            run_id: MSD's identifier for the run, as reported on a production
                job once it has begun.
        """
        return self._gateway.list_errors_for_run(run_id)

    def list_data_sources(self) -> list[DataSourceConfig]:
        """List every configured external data source (SRS MSD.2-5, 8)."""
        return self._gateway.list_data_sources()

    def configure_data_source(
        self,
        source_type: str,
        name: str,
        access_method: str,
        connection_address: str,
        username: str,
        secret: str | None,
        priority: int,
    ) -> DataSourceConfig:
        """Save a data source configuration (SRS MSD.8).

        Args:
            source_type: Which of the four external source types this serves.
            name: Operator-chosen name, unique within the source type.
            access_method: Vendor/protocol used to reach it.
            connection_address: Base URL, DSN, or path, depending on method.
            username: Connection user name; empty when the source needs none.
            secret: The secret, in plaintext, encrypted before storage. None
                or blank on an update keeps the previously stored secret.
            priority: Search order when several sources of one type compete.

        Returns:
            The saved configuration's status, never the secret.
        """
        return self._gateway.configure_data_source(
            source_type=source_type,
            name=name,
            access_method=access_method,
            connection_address=connection_address,
            username=username,
            secret=secret,
            priority=priority,
        )

    def delete_data_source(self, source_type: str, name: str) -> bool:
        """Delete a data source configuration.

        Args:
            source_type: Type of the source.
            name: Name of the source.

        Returns:
            True when a configuration was deleted.
        """
        return self._gateway.delete_data_source(source_type, name)

    def check_sources(self, platform: PlatformRef | None = None) -> SourceStatusSnapshot:
        """Probe every configured source now and record the result (SRS VAE-01.7).

        "Continuously and traceably" is two requirements in one. Continuous is
        the caller's job — the UI subscribes to a stream, the CLI polls.
        Traceable is this method's: every probe is recorded, so an operator
        investigating a failed production run can see whether a source was
        already unreachable at the time, not merely whether it is now.

        Args:
            platform: Scope for sources whose probe needs one; None uses a
                placeholder.

        Returns:
            The snapshot taken.
        """
        snapshot = SourceStatusSnapshot(
            checked_at=self._clock.now(),
            statuses=self._gateway.probe_sources(platform),
        )
        self._statuses.record(snapshot)
        return snapshot

    def latest_source_status(self) -> SourceStatusSnapshot | None:
        """Return the most recent snapshot without probing again.

        Returns:
            The last recorded snapshot, or None when none has been taken.
        """
        return self._statuses.latest()

    def run(self, request: ProductionJobRequest) -> ProductionJob:
        """Execute a queued production process and record its outcome.

        Called by the queue adapter rather than by a request handler. Any
        failure is caught and recorded as a failed process, because a worker
        crashing would leave the operator watching a process that never
        resolves.

        Args:
            request: Which job to run and what to produce.

        Returns:
            The finished process.

        Raises:
            UnknownProductionJob: If the job row is missing.
        """
        job = self._jobs.get(request.job_id)
        if job is None:
            raise UnknownProductionJob(f"No production process '{request.job_id}'")

        # Falls back to a fresh id only for a request queued before run_id
        # existed on it; every request start_production() enqueues now
        # carries one already.
        run_id = request.run_id or uuid4().hex

        try:
            outcome = self._gateway.produce(request.system_version, run_id=run_id)
        except Exception as exc:  # noqa: BLE001 - the operator must see any failure
            job.fail(finished_at=self._clock.now(), reason=str(exc), run_id=run_id)
            self._jobs.save(job)
            return job

        if outcome.succeeded:
            job.succeed(
                finished_at=self._clock.now(),
                run_id=outcome.run_id,
                file_path=outcome.file_path,
                entity_count=outcome.entity_count,
                relation_count=outcome.relation_count,
                error_count=len(outcome.errors),
            )
        else:
            job.fail(
                finished_at=self._clock.now(),
                reason=_first_reason(outcome.errors),
                run_id=outcome.run_id,
                error_count=len(outcome.errors),
            )

        self._jobs.save(job)
        return job


def _first_reason(errors: list[ProductionError]) -> str:
    """Return the first recorded reason, or a generic one when there is none."""
    return errors[0].reason if errors else "Model Setup Data production produced no file"
