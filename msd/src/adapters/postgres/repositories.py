"""
Description: PostgreSQL-backed implementations of MSD's persistence ports.
Created by: Mustafa Can Caliskan
Date: 2026-07-31
"""

from __future__ import annotations

import json

from sqlalchemy import delete, insert, select
from sqlalchemy.engine import Engine

from msd.src.adapters.postgres.tables import (
    acquisition_errors,
    data_sources,
    model_setup_data_records,
    version_inventory_entries,
)
from msd.src.model.data_source import (
    AccessMethod,
    CredentialReference,
    DataSourceConfiguration,
    DataSourceType,
)
from msd.src.model.model_setup_data import document_file_name
from msd.src.model.version_inventory import (
    SoftwareUnitVersion,
    SoftwareUnitVersionInventory,
)
from msd.src.ports.repositories import ModelSetupDataRecord
from shared.errors.acquisition import AcquisitionError, AcquisitionStatus
from shared.types.identifiers import PlatformRef, ProjectRef, SystemVersionRef


class PostgresDataSourceConfigurationRepository:
    """Stores configured data sources in PostgreSQL."""

    def __init__(self, engine: Engine) -> None:
        """Initialize the repository.

        Args:
            engine: Engine to run statements through.
        """
        self._engine = engine

    def save(self, configuration: DataSourceConfiguration) -> None:
        """Store a configuration, replacing any with the same type and name."""
        credential = configuration.credential
        with self._engine.begin() as connection:
            connection.execute(
                delete(data_sources).where(
                    data_sources.c.source_type == configuration.source_type.value,
                    data_sources.c.name == configuration.name,
                )
            )
            connection.execute(
                insert(data_sources).values(
                    source_type=configuration.source_type.value,
                    name=configuration.name,
                    access_method=configuration.access_method.value,
                    connection_address=configuration.connection_address,
                    username=credential.username if credential else "",
                    encrypted_secret=credential.encrypted_secret if credential else "",
                    priority=configuration.priority,
                    parameters=json.dumps(configuration.parameters),
                )
            )

    def delete(self, source_type: DataSourceType, name: str) -> bool:
        """Delete a configuration.

        Returns:
            True when a row was deleted.
        """
        with self._engine.begin() as connection:
            result = connection.execute(
                delete(data_sources).where(
                    data_sources.c.source_type == source_type.value,
                    data_sources.c.name == name,
                )
            )
        return result.rowcount > 0

    def get(self, source_type: DataSourceType, name: str) -> DataSourceConfiguration | None:
        """Fetch one configuration, or None when it is not stored."""
        with self._engine.connect() as connection:
            row = connection.execute(
                select(data_sources).where(
                    data_sources.c.source_type == source_type.value,
                    data_sources.c.name == name,
                )
            ).mappings().first()
        return _to_configuration(row) if row else None

    def list_all(self) -> list[DataSourceConfiguration]:
        """Fetch every stored configuration, in type then priority order."""
        with self._engine.connect() as connection:
            rows = connection.execute(
                select(data_sources).order_by(
                    data_sources.c.source_type, data_sources.c.priority, data_sources.c.name
                )
            ).mappings().all()
        return [_to_configuration(row) for row in rows]


class PostgresVersionInventoryRepository:
    """Stores the Software Unit Version Inventory in PostgreSQL."""

    def __init__(self, engine: Engine) -> None:
        """Initialize the repository.

        Args:
            engine: Engine to run statements through.
        """
        self._engine = engine

    def save(self, inventory: SoftwareUnitVersionInventory) -> None:
        """Store an inventory, replacing the one for the same system version."""
        scope = inventory.system_version
        with self._engine.begin() as connection:
            connection.execute(
                delete(version_inventory_entries).where(
                    version_inventory_entries.c.project == scope.project.name,
                    version_inventory_entries.c.platform == scope.platform.name,
                    version_inventory_entries.c.system_version == scope.version,
                )
            )
            for entry in inventory.entries:
                connection.execute(
                    insert(version_inventory_entries).values(
                        project=scope.project.name,
                        platform=scope.platform.name,
                        system_version=scope.version,
                        unit_name=entry.unit_name,
                        is_candidate=entry.is_candidate,
                        version=entry.version,
                        source_name=entry.source_name,
                    )
                )

    def get(self, system_version: SystemVersionRef) -> SoftwareUnitVersionInventory | None:
        """Fetch the inventory for a system version, or None when unrecorded."""
        with self._engine.connect() as connection:
            rows = connection.execute(
                select(version_inventory_entries)
                .where(
                    version_inventory_entries.c.project == system_version.project.name,
                    version_inventory_entries.c.platform == system_version.platform.name,
                    version_inventory_entries.c.system_version == system_version.version,
                )
                .order_by(
                    version_inventory_entries.c.unit_name,
                    version_inventory_entries.c.is_candidate,
                )
            ).mappings().all()

        if not rows:
            return None

        return SoftwareUnitVersionInventory(
            system_version=system_version,
            entries=[
                SoftwareUnitVersion(
                    unit_name=row["unit_name"],
                    version=row["version"],
                    source_name=row["source_name"],
                    is_candidate=bool(row["is_candidate"]),
                )
                for row in rows
            ],
        )


class PostgresAcquisitionErrorRepository:
    """Stores acquisition and validation failures in PostgreSQL."""

    def __init__(self, engine: Engine) -> None:
        """Initialize the repository.

        Args:
            engine: Engine to run statements through.
        """
        self._engine = engine

    def record(self, run_id: str, error: AcquisitionError) -> None:
        """Store one failure against the run that produced it."""
        with self._engine.begin() as connection:
            connection.execute(
                insert(acquisition_errors).values(
                    run_id=run_id,
                    status=error.status.value,
                    reason=error.reason,
                    source_name=error.source_name,
                    source_type=error.source_type,
                    project=error.platform.project.name,
                    platform=error.platform.name,
                    occurred_at=error.occurred_at,
                    detail=error.detail,
                )
            )

    def list_for_run(self, run_id: str) -> list[AcquisitionError]:
        """Fetch every failure recorded for one run, oldest first."""
        with self._engine.connect() as connection:
            rows = connection.execute(
                select(acquisition_errors)
                .where(acquisition_errors.c.run_id == run_id)
                .order_by(acquisition_errors.c.id)
            ).mappings().all()
        return [_to_error(row) for row in rows]

    def list_for_platform(self, platform: PlatformRef) -> list[AcquisitionError]:
        """Fetch every failure recorded for a platform, newest first."""
        with self._engine.connect() as connection:
            rows = connection.execute(
                select(acquisition_errors)
                .where(
                    acquisition_errors.c.project == platform.project.name,
                    acquisition_errors.c.platform == platform.name,
                )
                .order_by(acquisition_errors.c.id.desc())
            ).mappings().all()
        return [_to_error(row) for row in rows]


class PostgresModelSetupDataRepository:
    """Stores Model Setup Data documents and their metadata rows in PostgreSQL.

    The document lives in the same row as its metadata (a single INSERT covers
    both), rather than on disk: CSM-01 will read it back through this
    repository (INT-IF-01), not off a shared filesystem.
    """

    def __init__(self, engine: Engine) -> None:
        """Initialize the repository.

        Args:
            engine: Engine to run statements through.
        """
        self._engine = engine

    def save(self, record: ModelSetupDataRecord, document: dict) -> str:
        """Store the document and its metadata row together.

        Args:
            record: Metadata to store; its ``file_path`` is replaced with the
                document's display name.
            document: The serialized document.

        Returns:
            The document's display name (``msd_<date>_<platform>.json``).
        """
        name = document_file_name(record.system_version.platform.name, record.produced_at)

        with self._engine.begin() as connection:
            connection.execute(
                delete(model_setup_data_records).where(
                    model_setup_data_records.c.run_id == record.run_id
                )
            )
            connection.execute(
                insert(model_setup_data_records).values(
                    run_id=record.run_id,
                    project=record.system_version.project.name,
                    platform=record.system_version.platform.name,
                    system_version=record.system_version.version,
                    file_path=name,
                    document=json.dumps(document),
                    produced_at=record.produced_at,
                    entity_count=record.entity_count,
                    relation_count=record.relation_count,
                    failure_count=record.failure_count,
                )
            )

        return name

    def list_for(self, system_version: SystemVersionRef) -> list[ModelSetupDataRecord]:
        """Fetch the metadata rows for a system version, newest first."""
        with self._engine.connect() as connection:
            rows = connection.execute(
                select(model_setup_data_records)
                .where(
                    model_setup_data_records.c.project == system_version.project.name,
                    model_setup_data_records.c.platform == system_version.platform.name,
                    model_setup_data_records.c.system_version == system_version.version,
                )
                .order_by(model_setup_data_records.c.produced_at.desc())
            ).mappings().all()
        return [_to_record(row) for row in rows]

    def load(self, run_id: str) -> dict | None:
        """Read back a produced document by run id, or None when unknown."""
        with self._engine.connect() as connection:
            row = connection.execute(
                select(model_setup_data_records).where(
                    model_setup_data_records.c.run_id == run_id
                )
            ).mappings().first()

        if row is None:
            return None
        return json.loads(row["document"])


def _to_configuration(row) -> DataSourceConfiguration:
    return DataSourceConfiguration(
        source_type=DataSourceType(row["source_type"]),
        name=row["name"],
        access_method=AccessMethod(row["access_method"]),
        connection_address=row["connection_address"],
        credential=(
            CredentialReference(
                username=row["username"], encrypted_secret=row["encrypted_secret"]
            )
            if row["encrypted_secret"]
            else None
        ),
        priority=row["priority"],
        parameters=json.loads(row["parameters"] or "{}"),
    )


def _to_error(row) -> AcquisitionError:
    return AcquisitionError(
        status=AcquisitionStatus(row["status"]),
        reason=row["reason"],
        source_name=row["source_name"],
        source_type=row["source_type"],
        platform=PlatformRef(ProjectRef(row["project"]), row["platform"]),
        occurred_at=row["occurred_at"],
        detail=row["detail"],
    )


def _to_record(row) -> ModelSetupDataRecord:
    return ModelSetupDataRecord(
        run_id=row["run_id"],
        system_version=SystemVersionRef(
            PlatformRef(ProjectRef(row["project"]), row["platform"]), row["system_version"]
        ),
        file_path=row["file_path"],
        produced_at=row["produced_at"],
        entity_count=row["entity_count"],
        relation_count=row["relation_count"],
        failure_count=row["failure_count"],
    )
