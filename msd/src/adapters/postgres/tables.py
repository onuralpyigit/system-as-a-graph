"""
Description: SQLAlchemy table definitions and engine wiring for MSD's own stores.
Created by: Mustafa Can Caliskan
Date: 2026-07-31
"""

from __future__ import annotations

import os

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Integer,
    MetaData,
    String,
    Table,
    Text,
    create_engine,
)
from sqlalchemy.engine import Engine

#: Environment variable holding the connection string. Absent means MSD runs
#: without a database, which the composition root handles by falling back to
#: in-memory repositories.
DATABASE_URL_ENV_VAR = "DATABASE_URL"

metadata = MetaData()

#: Configured external data sources (SRS MSD.8). The secret is encrypted
#: before it reaches this table; only the ciphertext is stored.
data_sources = Table(
    "msd_data_source",
    metadata,
    Column("source_type", String(64), primary_key=True),
    Column("name", String(128), primary_key=True),
    Column("access_method", String(64), nullable=False),
    Column("connection_address", Text, nullable=False),
    Column("username", String(128), nullable=False, default=""),
    Column("encrypted_secret", Text, nullable=False, default=""),
    Column("priority", Integer, nullable=False, default=0),
    Column("parameters", Text, nullable=False, default="{}"),
)

#: Software Unit Version Inventory entries (SRS MSD.14-15). A candidate entry
#: sits alongside the baseline entry for the same unit, so ``is_candidate`` is
#: part of the key.
version_inventory_entries = Table(
    "msd_version_inventory_entry",
    metadata,
    Column("project", String(128), primary_key=True),
    Column("platform", String(128), primary_key=True),
    Column("system_version", String(64), primary_key=True),
    Column("unit_name", String(128), primary_key=True),
    Column("is_candidate", Boolean, primary_key=True, default=False),
    Column("version", String(64), nullable=False),
    Column("source_name", String(128), nullable=False, default=""),
)

#: Acquisition and validation failures (SRS MSD.16, 20, 22).
acquisition_errors = Table(
    "msd_acquisition_error",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("run_id", String(64), nullable=False, index=True),
    Column("status", String(64), nullable=False),
    Column("reason", Text, nullable=False),
    Column("source_name", String(128), nullable=False),
    Column("source_type", String(64), nullable=False),
    Column("project", String(128), nullable=False),
    Column("platform", String(128), nullable=False),
    Column("occurred_at", DateTime(timezone=True), nullable=False),
    Column("detail", Text, nullable=False, default=""),
)

#: Metadata rows pointing at produced Model Setup Data files (SRS MSD.23).
model_setup_data_records = Table(
    "msd_model_setup_data",
    metadata,
    Column("run_id", String(64), primary_key=True),
    Column("project", String(128), nullable=False),
    Column("platform", String(128), nullable=False),
    Column("system_version", String(64), nullable=False),
    # A display name (msd_<date>_<platform>.json), not a filesystem path — the
    # document itself lives in the `document` column, not on disk.
    Column("file_path", Text, nullable=False),
    Column("document", Text, nullable=False),
    Column("produced_at", DateTime(timezone=True), nullable=False),
    Column("entity_count", Integer, nullable=False),
    Column("relation_count", Integer, nullable=False),
    Column("failure_count", Integer, nullable=False),
)


def database_url() -> str | None:
    """Return the configured connection string, or None when unset."""
    return os.getenv(DATABASE_URL_ENV_VAR) or None


def create_schema(engine: Engine) -> None:
    """Create MSD's tables if they do not exist.

    Increment 1 carries no migration tooling; the schema is created from the
    metadata above at startup. A later increment introducing migrations
    replaces this call rather than layering on top of it.

    Args:
        engine: Engine to create the tables through.
    """
    metadata.create_all(engine)


def build_engine(url: str) -> Engine:
    """Build an engine for a connection string.

    Args:
        url: SQLAlchemy connection string.

    Returns:
        An engine with pre-ping enabled, so a connection dropped by an idle
        database is retried rather than surfacing as a request failure.
    """
    return create_engine(url, pool_pre_ping=True, future=True)
