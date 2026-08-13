"""
Description: In-memory persistence adapters used when no database is configured and in tests.
Created by: Mustafa Can Caliskan
Date: 2026-07-31
"""

from __future__ import annotations

from copy import deepcopy
from dataclasses import replace

from msd.src.model.data_source import DataSourceConfiguration, DataSourceType
from msd.src.model.model_setup_data import document_file_name
from msd.src.model.version_inventory import SoftwareUnitVersionInventory
from msd.src.ports.repositories import ModelSetupDataRecord
from shared.errors.acquisition import AcquisitionError
from shared.types.identifiers import PlatformRef, SystemVersionRef


class InMemoryDataSourceConfigurationRepository:
    """Keeps configured data sources in process memory."""

    def __init__(self) -> None:
        """Initialize an empty repository."""
        self._items: dict[tuple[DataSourceType, str], DataSourceConfiguration] = {}

    def save(self, configuration: DataSourceConfiguration) -> None:
        """Store a configuration, replacing any with the same type and name."""
        self._items[configuration.key] = configuration

    def delete(self, source_type: DataSourceType, name: str) -> bool:
        """Delete a configuration.

        Returns:
            True when a configuration was removed.
        """
        return self._items.pop((source_type, name), None) is not None

    def get(self, source_type: DataSourceType, name: str) -> DataSourceConfiguration | None:
        """Fetch one configuration, or None when it is not stored."""
        return self._items.get((source_type, name))

    def list_all(self) -> list[DataSourceConfiguration]:
        """Fetch every stored configuration, in type then priority order."""
        return sorted(
            self._items.values(),
            key=lambda item: (item.source_type.value, item.priority, item.name),
        )


class InMemoryVersionInventoryRepository:
    """Keeps Software Unit Version Inventories in process memory."""

    def __init__(self) -> None:
        """Initialize an empty repository."""
        self._items: dict[tuple[str, str, str], SoftwareUnitVersionInventory] = {}

    def save(self, inventory: SoftwareUnitVersionInventory) -> None:
        """Store an inventory, replacing the one for the same system version."""
        self._items[_scope_key(inventory.system_version)] = deepcopy(inventory)

    def get(self, system_version: SystemVersionRef) -> SoftwareUnitVersionInventory | None:
        """Fetch the inventory for a system version, or None when unrecorded."""
        found = self._items.get(_scope_key(system_version))
        return deepcopy(found) if found else None


class InMemoryAcquisitionErrorRepository:
    """Keeps acquisition and validation failures in process memory."""

    def __init__(self) -> None:
        """Initialize an empty repository."""
        self._items: list[tuple[str, AcquisitionError]] = []

    def record(self, run_id: str, error: AcquisitionError) -> None:
        """Store one failure against the run that produced it."""
        self._items.append((run_id, error))

    def list_for_run(self, run_id: str) -> list[AcquisitionError]:
        """Fetch every failure recorded for one run, oldest first."""
        return [error for recorded_run, error in self._items if recorded_run == run_id]

    def list_for_platform(self, platform: PlatformRef) -> list[AcquisitionError]:
        """Fetch every failure recorded for a platform, newest first."""
        return [
            error
            for _, error in reversed(self._items)
            if error.platform.name == platform.name
            and error.platform.project.name == platform.project.name
        ]


class InMemoryModelSetupDataRepository:
    """Keeps documents and their metadata rows in process memory.

    Used when no database is configured, so a database-less run has nothing
    to persist to — documents don't outlive the process either way.
    """

    def __init__(self) -> None:
        """Initialize an empty repository."""
        self._records: dict[str, ModelSetupDataRecord] = {}
        self._documents: dict[str, dict] = {}

    def save(self, record: ModelSetupDataRecord, document: dict) -> str:
        """Store the document and remember its metadata row."""
        name = document_file_name(record.system_version.platform.name, record.produced_at)
        self._records[record.run_id] = replace(record, file_path=name)
        self._documents[record.run_id] = document
        return name

    def list_for(self, system_version: SystemVersionRef) -> list[ModelSetupDataRecord]:
        """Fetch the metadata rows for a system version, newest first."""
        scope = _scope_key(system_version)
        return sorted(
            (
                record
                for record in self._records.values()
                if _scope_key(record.system_version) == scope
            ),
            key=lambda record: record.produced_at,
            reverse=True,
        )

    def load(self, run_id: str) -> dict | None:
        """Read back a produced document by run id, or None when unknown."""
        return self._documents.get(run_id)


def _scope_key(system_version: SystemVersionRef) -> tuple[str, str, str]:
    return (
        system_version.project.name,
        system_version.platform.name,
        system_version.version,
    )
