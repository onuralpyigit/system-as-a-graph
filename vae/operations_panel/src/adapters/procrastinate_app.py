"""
Description: Procrastinate application and the deferred Model Setup Data production task.
Created by: Mustafa Can Caliskan
Date: 2026-07-31
"""

from __future__ import annotations

from functools import lru_cache

from procrastinate import App, PsycopgConnector

from msd.src.adapters.postgres.tables import database_url

#: Name the production task is registered and deferred under. The worker
#: resolves the task by this name, so it must stay stable across releases.
PRODUCTION_TASK_NAME = "vae01.produce_model_setup_data"


def _connection_info(url: str) -> str:
    """Convert a SQLAlchemy URL into the libpq form psycopg expects.

    The deployment configures one ``DATABASE_URL`` for everything; SQLAlchemy
    wants its driver in the scheme and psycopg does not understand it.

    Args:
        url: SQLAlchemy-style connection URL.

    Returns:
        A libpq connection string.
    """
    return url.replace("postgresql+psycopg://", "postgresql://").replace(
        "postgresql+psycopg2://", "postgresql://"
    )


@lru_cache(maxsize=1)
def procrastinate_app() -> App:
    """Build the process-wide Procrastinate application.

    Returns:
        The application, with the production task registered on it.

    Raises:
        RuntimeError: If no database is configured; the queue is
            database-backed and has nowhere to keep jobs without one.
    """
    url = database_url()
    if not url:
        raise RuntimeError("A database is required for the Procrastinate job queue")

    app = App(connector=PsycopgConnector(conninfo=_connection_info(url)))

    @app.task(name=PRODUCTION_TASK_NAME)
    def produce_model_setup_data(
        job_id: str,
        project: str,
        platform: str,
        system_version: str,
        started_by: str,
        run_id: str = "",
    ) -> None:
        """Run one queued Model Setup Data production process.

        Imported lazily so the worker builds the panel in its own process
        rather than inheriting the API's wiring. ``run_id`` defaults to empty
        only for a job deferred before this parameter existed; run() falls
        back to generating one for that case.
        """
        from vae.operations_panel.src.api.dependencies import run_production_job

        run_production_job(job_id, project, platform, system_version, started_by, run_id)

    return app


@lru_cache(maxsize=1)
def ensure_schema() -> None:
    """Create Procrastinate's own tables once, if they are not already there.

    Created at startup rather than by a migration step, matching how the rest
    of Increment 1 creates its schema. Safe to call from both the API and the
    worker: whichever starts first wins and the other finds the tables
    present.
    """
    from sqlalchemy import text

    from msd.src.adapters.postgres.tables import build_engine

    engine = build_engine(database_url())
    with engine.connect() as connection:
        exists = connection.execute(
            text("SELECT to_regclass('public.procrastinate_jobs')")
        ).scalar()

    if exists:
        return

    app = procrastinate_app()
    with app.open():
        app.schema_manager.apply_schema()
