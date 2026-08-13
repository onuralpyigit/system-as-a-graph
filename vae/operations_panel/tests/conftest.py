"""
Description: Fixtures wiring the operations panel against stub adapters for tests.
Created by: Mustafa Can Caliskan
Date: 2026-07-31
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from shared.types.identifiers import (
    PlatformRef,
    ProjectRef,
    SystemVersionRef,
    system_version,
)
from vae.operations_panel.src.adapters.job_queue import ImmediateJobQueue
from vae.operations_panel.src.adapters.jwt_tokens import JwtTokenService
from vae.operations_panel.src.adapters.memory import (
    InMemoryProductionJobRepository,
    InMemorySourceStatusRepository,
    InMemoryWorkingScopeRepository,
)
from vae.operations_panel.src.model.data_source import DataSourceConfig
from vae.operations_panel.src.model.production_job import (
    AvailableSystemVersion,
    ModelSetupDataFile,
    ProductionError,
)
from vae.operations_panel.src.model.source_status import Accessibility, SourceStatus
from vae.operations_panel.src.ports.model_setup_data import ProductionOutcome
from vae.operations_panel.src.use_cases.manage_model_setup_data import (
    ModelSetupDataWorkflowUseCase,
)
from vae.operations_panel.src.use_cases.manage_session import (
    SessionAndAuthenticationUseCase,
)
from vae.operations_panel.tests.support.fake_directory_service import (
    FakeDirectoryService,
)

#: The scope every test works in.
PROJECT = "skyline"
PLATFORM = "avionics"
EFFECTIVE_VERSION = "1.0.0"
OLDER_VERSION = "0.9.0"

FIXED_NOW = datetime(2026, 7, 31, 9, 30, tzinfo=UTC)


class FixedClock:
    """Returns a pinned time, so token expiry and job timing are deterministic."""

    def __init__(self, moment: datetime) -> None:
        self._moment = moment

    def now(self) -> datetime:
        """Return the pinned time."""
        return self._moment


@dataclass
class StubModelSetupDataGateway:
    """Stands in for MSD so the panel's tests exercise only the panel.

    Attributes:
        files: Files reported as produced for the scope.
        errors: Failures reported for the platform.
        sources: Accessibility results the probe returns.
        outcome: What the next production run returns.
        raises: When set, production raises this instead of returning.
        produced: Scopes production was invoked for, in order.
    """

    files: list[ModelSetupDataFile] = field(default_factory=list)
    errors: list[ProductionError] = field(default_factory=list)
    errors_by_run: dict[str, list[ProductionError]] = field(default_factory=dict)
    sources: list[SourceStatus] = field(default_factory=list)
    outcome: ProductionOutcome | None = None
    raises: Exception | None = None
    produced: list[SystemVersionRef] = field(default_factory=list)
    data_sources: dict[tuple[str, str], DataSourceConfig] = field(default_factory=dict)
    stored_secrets: dict[tuple[str, str], str] = field(default_factory=dict)

    def list_projects(self) -> list[str]:
        """List the one project the stub knows."""
        return [PROJECT]

    def list_platforms(self, project: ProjectRef) -> list[str]:
        """List the one platform the stub knows."""
        return [PLATFORM] if project.name == PROJECT else []

    def list_system_versions(self, platform: PlatformRef) -> list[AvailableSystemVersion]:
        """List two versions, the newer one marked effective."""
        if platform.name != PLATFORM:
            return []
        return [
            AvailableSystemVersion(version=EFFECTIVE_VERSION, is_effective=True),
            AvailableSystemVersion(version=OLDER_VERSION, is_effective=False),
        ]

    def list_model_setup_data_files(
        self, system_version: SystemVersionRef
    ) -> list[ModelSetupDataFile]:
        """List the configured files."""
        del system_version
        return list(self.files)

    def produce(self, system_version: SystemVersionRef, run_id: str) -> ProductionOutcome:
        """Return the configured outcome, or raise the configured failure."""
        self.produced.append(system_version)
        if self.raises is not None:
            raise self.raises
        return self.outcome or ProductionOutcome(run_id=run_id, succeeded=True)

    def probe_sources(self, platform: PlatformRef | None = None) -> list[SourceStatus]:
        """Return the configured accessibility results."""
        del platform
        return list(self.sources)

    def list_errors(self, platform: PlatformRef) -> list[ProductionError]:
        """Return the configured failures."""
        del platform
        return list(self.errors)

    def list_errors_for_run(self, run_id: str) -> list[ProductionError]:
        """Return the failures configured for one run."""
        return list(self.errors_by_run.get(run_id, []))

    def list_data_sources(self) -> list[DataSourceConfig]:
        """Return the configured sources, as a real gateway would list them."""
        return list(self.data_sources.values())

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
        """Store a source, keeping any previously stored secret when none is given."""
        key = (source_type, name)
        if secret:
            self.stored_secrets[key] = secret
        config = DataSourceConfig(
            source_type=source_type,
            name=name,
            access_method=access_method,
            connection_address=connection_address,
            username=username,
            secret_set=key in self.stored_secrets,
            priority=priority,
        )
        self.data_sources[key] = config
        return config

    def delete_data_source(self, source_type: str, name: str) -> bool:
        """Remove a stored source, reporting whether one existed."""
        key = (source_type, name)
        self.stored_secrets.pop(key, None)
        return self.data_sources.pop(key, None) is not None


@dataclass
class Panel:
    """A wired operations panel with its stub gateway exposed.

    Attributes:
        gateway: The stub MSD gateway the test configures.
        session: Session & Authentication Manager.
        workflow: Model Setup Data Workflow Manager.
        clock: The pinned clock.
    """

    gateway: StubModelSetupDataGateway
    session: SessionAndAuthenticationUseCase
    workflow: ModelSetupDataWorkflowUseCase
    clock: FixedClock

    def log_in(self, username: str = "operator", password: str = "operator"):
        """Log in and return the granted session."""
        return self.session.log_in(username, password)

    def select_effective_scope(self, username: str = "operator"):
        """Select the effective version, the common starting point for tests."""
        return self.session.select(
            username, system_version(PROJECT, PLATFORM, EFFECTIVE_VERSION)
        )


#: The account file the in-test directory double reads.
PACKAGED_USERS_FILE = (
    Path(FakeDirectoryService.__module__.replace(".", "/")).parent / "users.json"
)


@pytest.fixture
def users_file(tmp_path: Path) -> Path:
    """A private copy of the account file, so a test may edit it."""
    target = tmp_path / "users.json"
    target.write_text(PACKAGED_USERS_FILE.read_text(encoding="utf-8"), encoding="utf-8")
    return target


def build_panel(users_file: Path, queue=None) -> Panel:
    """Wire the panel against stubs and in-memory stores.

    Args:
        users_file: Account file the directory service reads.
        queue: Job queue to use; the default runs production inline.
    """
    clock = FixedClock(FIXED_NOW)
    gateway = StubModelSetupDataGateway(
        sources=[
            SourceStatus(
                source_type="configuration_management_database",
                source_name="cmdb-primary",
                accessibility=Accessibility.REACHABLE,
                checked_at=FIXED_NOW,
            )
        ]
    )

    scopes = InMemoryWorkingScopeRepository()

    workflow = ModelSetupDataWorkflowUseCase(
        gateway=gateway,
        jobs=InMemoryProductionJobRepository(),
        queue=queue or ImmediateJobQueue(lambda: workflow),
        scopes=scopes,
        statuses=InMemorySourceStatusRepository(),
        clock=clock,
    )

    return Panel(
        gateway=gateway,
        session=SessionAndAuthenticationUseCase(
            directory=FakeDirectoryService(users_file),
            tokens=JwtTokenService(
                clock=clock,
                lifetime=timedelta(hours=8),
                secret="test-secret-long-enough-for-hmac-sha256",
            ),
            gateway=gateway,
            scopes=scopes,
            clock=clock,
        ),
        workflow=workflow,
        clock=clock,
    )


@pytest.fixture
def panel(users_file: Path) -> Panel:
    """A panel whose production runs inline."""
    return build_panel(users_file)
