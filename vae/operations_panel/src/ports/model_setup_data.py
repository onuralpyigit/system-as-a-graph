"""
Description: Outbound port through which the panel drives Model Setup Data Generation.
Created by: Mustafa Can Caliskan
Date: 2026-07-31
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, runtime_checkable

from shared.types.identifiers import PlatformRef, ProjectRef, SystemVersionRef
from vae.operations_panel.src.model.data_source import DataSourceConfig
from vae.operations_panel.src.model.production_job import (
    AvailableSystemVersion,
    ModelSetupDataFile,
    ProductionError,
)
from vae.operations_panel.src.model.source_status import SourceStatus


@dataclass
class ProductionOutcome:
    """What one Model Setup Data production run produced.

    Attributes:
        run_id: MSD's identifier for the run.
        succeeded: Whether a document was produced at all.
        file_path: Where it was written; empty when none was.
        entity_count: Entities in the document.
        relation_count: Relations in the document.
        errors: Failures recorded during the run.
    """

    run_id: str
    succeeded: bool
    file_path: str = ""
    entity_count: int = 0
    relation_count: int = 0
    errors: list[ProductionError] = None  # type: ignore[assignment]

    def __post_init__(self) -> None:
        if self.errors is None:
            self.errors = []


@runtime_checkable
class ModelSetupDataGatewayPort(Protocol):
    """The panel's view of MSD (SRS VAE-01.2).

    VAE-01 drives MSD but owns none of it: everything the panel needs from the
    Model Setup Data Generation component passes through this port, so the two
    CSCs stay separable and the panel can be tested without MSD's adapters.
    """

    def list_projects(self) -> list[str]:
        """List the projects the operator may select."""
        ...

    def list_platforms(self, project: ProjectRef) -> list[str]:
        """List a project's platforms."""
        ...

    def list_system_versions(self, platform: PlatformRef) -> list[AvailableSystemVersion]:
        """List a platform's system versions, marking the effective one."""
        ...

    def list_model_setup_data_files(
        self, system_version: SystemVersionRef
    ) -> list[ModelSetupDataFile]:
        """List the Model Setup Data files produced for a system version."""
        ...

    def produce(self, system_version: SystemVersionRef, run_id: str) -> ProductionOutcome:
        """Run Model Setup Data production.

        Args:
            system_version: Scope to produce for.
            run_id: Identifier to record the run under.

        Returns:
            What the run produced, including everything it recorded as failed.
        """
        ...

    def probe_sources(self, platform: PlatformRef | None = None) -> list[SourceStatus]:
        """Check every configured data source's accessibility.

        Args:
            platform: Scope for sources whose probe needs one (the topology
                source); None probes them with a placeholder.

        Returns:
            One status per configured source; a source that cannot be reached
            is reported, never omitted.
        """
        ...

    def list_errors(self, platform: PlatformRef) -> list[ProductionError]:
        """List the failures MSD recorded for a platform (SRS VAE-01.8)."""
        ...

    def list_errors_for_run(self, run_id: str) -> list[ProductionError]:
        """List the failures MSD recorded for one production run (SRS VAE-01.8)."""
        ...

    def list_data_sources(self) -> list[DataSourceConfig]:
        """List every configured external data source (SRS MSD.2-5, 8)."""
        ...

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
        """Save a data source configuration, replacing one with the same key.

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
        ...

    def delete_data_source(self, source_type: str, name: str) -> bool:
        """Delete a data source configuration.

        Args:
            source_type: Type of the source.
            name: Name of the source.

        Returns:
            True when a configuration was deleted.
        """
        ...
