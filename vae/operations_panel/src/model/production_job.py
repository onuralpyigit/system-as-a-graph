"""
Description: The Model Setup Data production process an operator starts and monitors (SRS VAE-01.6).
Created by: Mustafa Can Caliskan
Date: 2026-07-31
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

from shared.types.identifiers import SystemVersionRef


class JobStatus(str, Enum):
    """The three states VAE-01.6 requires a production process to report.

    ``IN_PROGRESS`` covers both queued and running: from the operator's side
    they are the same statement — the process has started and has not finished.
    """

    IN_PROGRESS = "in_progress"
    SUCCEEDED = "succeeded"
    FAILED = "failed"


@dataclass
class ProductionJob:
    """One Model Setup Data production run, as the panel sees it.

    Attributes:
        job_id: Identifier the operator monitors the process by.
        system_version: Scope the production was started for.
        started_by: Operator who started it.
        status: Current state.
        started_at: When the process was started.
        finished_at: When it reached a terminal state; None while in progress.
        run_id: MSD's own run identifier, once production has begun.
        file_path: Where the produced document was written, on success.
        failure_reason: Why it failed; empty otherwise.
        entity_count: Entities in the produced document.
        relation_count: Relations in the produced document.
        error_count: Failures MSD recorded during the run — a successful
            production may still carry recorded errors (SRS VAE-01.8).
    """

    job_id: str
    system_version: SystemVersionRef
    started_by: str
    status: JobStatus
    started_at: datetime
    finished_at: datetime | None = None
    run_id: str = ""
    file_path: str = ""
    failure_reason: str = ""
    entity_count: int = 0
    relation_count: int = 0
    error_count: int = 0

    @property
    def is_finished(self) -> bool:
        """Whether the process has reached a terminal state."""
        return self.status is not JobStatus.IN_PROGRESS

    def succeed(
        self,
        finished_at: datetime,
        run_id: str,
        file_path: str,
        entity_count: int,
        relation_count: int,
        error_count: int,
    ) -> None:
        """Mark the process successful.

        Args:
            finished_at: Completion time.
            run_id: MSD run identifier.
            file_path: Where the document was written.
            entity_count: Entities in the document.
            relation_count: Relations in the document.
            error_count: Failures recorded during the run.
        """
        self.status = JobStatus.SUCCEEDED
        self.finished_at = finished_at
        self.run_id = run_id
        self.file_path = file_path
        self.entity_count = entity_count
        self.relation_count = relation_count
        self.error_count = error_count

    def fail(
        self, finished_at: datetime, reason: str, run_id: str = "", error_count: int = 0
    ) -> None:
        """Mark the process failed.

        Args:
            finished_at: Completion time.
            reason: Why it failed, in terms an operator can act on.
            run_id: MSD run identifier, when production got far enough to have one.
            error_count: Failures recorded during the run, when it got that far.
        """
        self.status = JobStatus.FAILED
        self.finished_at = finished_at
        self.failure_reason = reason
        self.run_id = run_id
        self.error_count = error_count


@dataclass
class ProductionJobRequest:
    """What the queue needs to run a production process.

    Attributes:
        job_id: Job to update.
        system_version: Scope to produce for.
        started_by: Operator who started it.
        run_id: MSD run identifier, generated at start time so it is known
            (and errors are attributable) even while the job is in progress.
    """

    job_id: str
    system_version: SystemVersionRef
    started_by: str = ""
    run_id: str = ""


@dataclass
class ProductionError:
    """One failure MSD recorded during a production run (SRS VAE-01.8).

    Presented to the operator as-is; the panel classifies nothing itself.

    Attributes:
        status: Missing-data, access, authorization, format, or integrity.
        reason: What went wrong.
        source_name: Configured source it is attributed to.
        source_type: Type of that source.
        occurred_at: When it was detected.
        detail: Extra context.
    """

    status: str
    reason: str
    source_name: str
    source_type: str
    occurred_at: datetime
    detail: str = ""


@dataclass
class ModelSetupDataFile:
    """A produced Model Setup Data file the operator can select (SRS VAE-01.5).

    Attributes:
        run_id: Identifier the file is selected by.
        file_path: Where it was written.
        produced_at: When it was produced.
        entity_count: Entities it carries.
        relation_count: Relations it carries.
        failure_count: Failures recorded during its production.
    """

    run_id: str
    file_path: str
    produced_at: datetime
    entity_count: int = 0
    relation_count: int = 0
    failure_count: int = 0


@dataclass
class AvailableSystemVersion:
    """A system version the operator may select (SRS VAE-01.4).

    Attributes:
        version: The version number.
        is_effective: Whether it is the currently effective one.
    """

    version: str
    is_effective: bool = False


@dataclass
class SelectableScope:
    """What the operator may choose between, for one project and platform.

    Attributes:
        projects: Project names available.
        platforms: Platform names available under the chosen project.
        versions: Versions available under the chosen platform.
    """

    projects: list[str] = field(default_factory=list)
    platforms: list[str] = field(default_factory=list)
    versions: list[AvailableSystemVersion] = field(default_factory=list)

    @property
    def effective_version(self) -> AvailableSystemVersion | None:
        """The version marked as currently effective, if any."""
        for version in self.versions:
            if version.is_effective:
                return version
        return None
