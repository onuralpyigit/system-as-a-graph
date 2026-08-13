"""
Description: Composition root wiring the operations panel to its adapters.
Created by: Mustafa Can Caliskan
Date: 2026-07-31
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import UTC, timedelta
from functools import lru_cache

from msd.src.adapters.postgres.tables import build_engine, database_url
from msd.src.api.dependencies import get_container as get_msd_container
from shared.types.identifiers import system_version
from vae.operations_panel.src.adapters.job_queue import (
    ImmediateJobQueue,
    ProcrastinateJobQueue,
)
from vae.operations_panel.src.adapters.jwt_tokens import JwtTokenService
from vae.operations_panel.src.adapters.ldap.directory_service import (
    LdapDirectoryService,
)
from vae.operations_panel.src.adapters.memory import (
    InMemoryProductionJobRepository,
    InMemorySourceStatusRepository,
    InMemoryWorkingScopeRepository,
)
from vae.operations_panel.src.adapters.msd_gateway import InProcessModelSetupDataGateway
from vae.operations_panel.src.adapters.postgres.repositories import (
    PostgresProductionJobRepository,
    PostgresSourceStatusRepository,
    PostgresWorkingScopeRepository,
)
from vae.operations_panel.src.adapters.postgres.tables import create_schema
from vae.operations_panel.src.model.production_job import ProductionJobRequest
from vae.operations_panel.src.ports.repositories import (
    ProductionJobRepository,
    SourceStatusRepository,
    WorkingScopeRepository,
)
from vae.operations_panel.src.use_cases.manage_model_setup_data import (
    ModelSetupDataWorkflowUseCase,
)
from vae.operations_panel.src.use_cases.manage_session import (
    SessionAndAuthenticationUseCase,
)

#: How long an issued session token stays valid, in minutes.
SESSION_LIFETIME_ENV_VAR = "VAE_SESSION_MINUTES"

_DEFAULT_SESSION_MINUTES = 480


class SystemClock:
    """Returns the current UTC time."""

    def now(self):
        """Return the current time, timezone-aware in UTC."""
        from datetime import datetime

        return datetime.now(tz=UTC)


@dataclass
class PanelContainer:
    """The wired object graph the panel serves requests from.

    One field per SDD §3.6.1.2 design element in this increment's scope.

    Attributes:
        session: Session & Authentication Manager.
        workflow: Model Setup Data Workflow Manager.
    """

    session: SessionAndAuthenticationUseCase
    workflow: ModelSetupDataWorkflowUseCase


def build_panel_container() -> PanelContainer:
    """Wire the panel from the environment.

    Falls back to in-memory repositories and an inline job queue when no
    database is configured, so the panel still runs without infrastructure —
    the only thing lost is the observable in-progress state.

    Returns:
        The wired container.
    """
    clock = SystemClock()
    gateway = InProcessModelSetupDataGateway(get_msd_container())

    scopes: WorkingScopeRepository
    jobs: ProductionJobRepository
    statuses: SourceStatusRepository

    url = database_url()
    if url:
        engine = build_engine(url)
        create_schema(engine)
        scopes = PostgresWorkingScopeRepository(engine)
        jobs = PostgresProductionJobRepository(engine)
        statuses = PostgresSourceStatusRepository(engine)
    else:
        scopes = InMemoryWorkingScopeRepository()
        jobs = InMemoryProductionJobRepository()
        statuses = InMemorySourceStatusRepository()

    return PanelContainer(
        session=SessionAndAuthenticationUseCase(
            directory=LdapDirectoryService(),
            tokens=JwtTokenService(clock=clock, lifetime=_session_lifetime()),
            gateway=gateway,
            scopes=scopes,
            clock=clock,
        ),
        workflow=ModelSetupDataWorkflowUseCase(
            gateway=gateway,
            jobs=jobs,
            queue=_build_queue(),
            scopes=scopes,
            statuses=statuses,
            clock=clock,
        ),
    )


@lru_cache(maxsize=1)
def get_panel_container() -> PanelContainer:
    """Return the process-wide panel container, building it on first use."""
    return build_panel_container()


def run_production_job(
    job_id: str, project: str, platform: str, version: str, started_by: str, run_id: str = ""
) -> None:
    """Execute a queued production process.

    The Procrastinate worker calls this by name, in its own process, so it
    rebuilds the container rather than sharing the API's.

    Args:
        job_id: Job row to update.
        project: Project to produce for.
        platform: Platform to produce for.
        version: System version to produce for.
        started_by: Operator who started the process.
        run_id: MSD run identifier assigned at start time.
    """
    get_panel_container().workflow.run(
        ProductionJobRequest(
            job_id=job_id,
            system_version=system_version(project, platform, version),
            started_by=started_by,
            run_id=run_id,
        )
    )


def _build_queue():
    """Pick the job queue for the configured environment.

    With a database configured the process is deferred to a Procrastinate
    worker, which is what makes the in-progress state observable; without one
    it runs inline so the panel still works.
    """
    if database_url():
        from vae.operations_panel.src.adapters.procrastinate_app import (
            PRODUCTION_TASK_NAME,
            ensure_schema,
            procrastinate_app,
        )

        ensure_schema()
        return ProcrastinateJobQueue(procrastinate_app(), PRODUCTION_TASK_NAME)

    return ImmediateJobQueue(lambda: get_panel_container().workflow)


def _session_lifetime() -> timedelta:
    minutes = os.getenv(SESSION_LIFETIME_ENV_VAR)
    return timedelta(minutes=int(minutes) if minutes else _DEFAULT_SESSION_MINUTES)
