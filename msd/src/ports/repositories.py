"""
Description: Outbound persistence ports for MSD's own stores.
Created by: Mustafa Can Caliskan
Date: 2026-07-31
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Protocol, runtime_checkable

from msd.src.model.data_source import DataSourceConfiguration, DataSourceType
from msd.src.model.version_inventory import SoftwareUnitVersionInventory
from shared.errors.acquisition import AcquisitionError
from shared.types.identifiers import PlatformRef, SystemVersionRef


@dataclass(frozen=True)
class ModelSetupDataRecord:
    """Metadata row for a produced Model Setup Data document (SDD §2.4).

    The document itself lives in PostgreSQL, alongside this row; this row is
    what CSM-01 lists and looks it up by.

    Attributes:
        run_id: Identifier of the production run that created it.
        system_version: Scope it was produced for.
        file_path: The document's display name (not a filesystem path).
        produced_at: Production time.
        entity_count: Number of entities in the document.
        relation_count: Number of relations in the document.
        failure_count: Number of failures recorded during the run.
    """

    run_id: str
    system_version: SystemVersionRef
    file_path: str
    produced_at: datetime
    entity_count: int
    relation_count: int
    failure_count: int


@runtime_checkable
class DataSourceConfigurationRepository(Protocol):
    """Persists the configured external data sources (SRS MSD.8)."""

    def save(self, configuration: DataSourceConfiguration) -> None:
        """Store a configuration, replacing any with the same type and name."""
        ...

    def delete(self, source_type: DataSourceType, name: str) -> bool:
        """Delete a configuration.

        Returns:
            True when a configuration was deleted.
        """
        ...

    def get(self, source_type: DataSourceType, name: str) -> DataSourceConfiguration | None:
        """Fetch one configuration, or None when it is not stored."""
        ...

    def list_all(self) -> list[DataSourceConfiguration]:
        """Fetch every stored configuration."""
        ...


@runtime_checkable
class VersionInventoryRepository(Protocol):
    """Persists the Software Unit Version Inventory (SRS MSD.14-15)."""

    def save(self, inventory: SoftwareUnitVersionInventory) -> None:
        """Store an inventory, replacing the one for the same system version."""
        ...

    def get(self, system_version: SystemVersionRef) -> SoftwareUnitVersionInventory | None:
        """Fetch the inventory for a system version, or None when unrecorded."""
        ...


@runtime_checkable
class AcquisitionErrorRepository(Protocol):
    """Persists acquisition and validation failures (SRS MSD.16, 20, 22)."""

    def record(self, run_id: str, error: AcquisitionError) -> None:
        """Store one failure against the run that produced it."""
        ...

    def list_for_run(self, run_id: str) -> list[AcquisitionError]:
        """Fetch every failure recorded for one run."""
        ...

    def list_for_platform(self, platform: PlatformRef) -> list[AcquisitionError]:
        """Fetch every failure recorded for a platform, newest first."""
        ...


@runtime_checkable
class ModelSetupDataRepository(Protocol):
    """Persists produced Model Setup Data documents (SRS MSD.23)."""

    def save(self, record: ModelSetupDataRecord, document: dict) -> str:
        """Store the document and its metadata row.

        Args:
            record: Metadata to store; its ``file_path`` may be replaced by the
                adapter with the document's display name.
            document: The serialized Model Setup Data document.

        Returns:
            The document's display name.
        """
        ...

    def list_for(self, system_version: SystemVersionRef) -> list[ModelSetupDataRecord]:
        """Fetch the metadata rows for a system version, newest first."""
        ...

    def load(self, run_id: str) -> dict | None:
        """Read back a produced document by run id, or None when unknown."""
        ...
