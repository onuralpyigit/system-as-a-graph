"""
Description: In-process gateway through which the panel drives Model Setup Data Generation.
Created by: Mustafa Can Caliskan
Date: 2026-07-31
"""

from __future__ import annotations

from uuid import uuid4

from msd.src.adapters.support import SystemClock
from msd.src.api.dependencies import Container
from msd.src.model.data_source import (
    AccessMethod,
    CredentialReference,
    DataSourceConfiguration,
    DataSourceType,
)
from msd.src.model.version_inventory import SoftwareUnitVersion
from msd.src.use_cases._recording import RunRecorder
from shared.errors.acquisition import AcquisitionFailure
from shared.types.identifiers import PlatformRef, ProjectRef, SystemVersionRef
from vae.operations_panel.src.model.data_source import DataSourceConfig
from vae.operations_panel.src.model.production_job import (
    AvailableSystemVersion,
    ModelSetupDataFile,
    ProductionError,
)
from vae.operations_panel.src.model.source_status import Accessibility, SourceStatus
from vae.operations_panel.src.ports.model_setup_data import ProductionOutcome

#: Placeholder used when a probe needs a scope it has not been given.
_UNKNOWN = "unknown"

#: Unit name a repository probe asks about. It is not expected to exist; the
#: point is to make the adapter touch its source, not to find anything.
_PROBE_UNIT = SoftwareUnitVersion(unit_name="__accessibility_probe__", version="0.0.0")


class InProcessModelSetupDataGateway:
    """Calls MSD's use cases directly, in the same process.

    The panel and MSD ship in one FastAPI application, so no network hop is
    needed between them; keeping the call behind this port is what preserves
    the CSC boundary anyway — the panel depends on the port, never on MSD's
    internals, and a later split into separate services replaces this adapter
    alone.
    """

    def __init__(self, container: Container) -> None:
        """Initialize the gateway.

        Args:
            container: MSD's wired object graph.
        """
        self._container = container

    def list_projects(self) -> list[str]:
        """List the projects the operator may select."""
        outcome = self._container.configuration_data().list_projects(
            self._recorder(PlatformRef(ProjectRef(_UNKNOWN), _UNKNOWN))
        )
        return [project.ref.name for project in outcome.data.projects]

    def list_platforms(self, project: ProjectRef) -> list[str]:
        """List a project's platforms."""
        outcome = self._container.configuration_data().list_platforms(
            project, self._recorder(PlatformRef(project, _UNKNOWN))
        )
        return [platform.ref.name for platform in outcome.data.platforms]

    def list_system_versions(self, platform: PlatformRef) -> list[AvailableSystemVersion]:
        """List a platform's system versions, marking the effective one."""
        outcome = self._container.configuration_data().list_system_versions(
            platform, self._recorder(platform)
        )
        return [
            AvailableSystemVersion(
                version=version.ref.version, is_effective=version.is_effective
            )
            for version in outcome.data.versions
        ]

    def list_model_setup_data_files(
        self, system_version: SystemVersionRef
    ) -> list[ModelSetupDataFile]:
        """List the Model Setup Data files produced for a system version."""
        return [
            ModelSetupDataFile(
                run_id=record.run_id,
                file_path=record.file_path,
                produced_at=record.produced_at,
                entity_count=record.entity_count,
                relation_count=record.relation_count,
                failure_count=record.failure_count,
            )
            for record in self._container.documents.list_for(system_version)
        ]

    def produce(self, system_version: SystemVersionRef, run_id: str) -> ProductionOutcome:
        """Run Model Setup Data production and report what it produced.

        Production reads a previously recorded Software Unit Version
        Inventory rather than acquiring one itself (SDD 3.1.2) — MSD.14
        records it as its own step. The panel is the operator's one
        "Produce" action, so it refreshes the inventory from CMDB here,
        under this run, rather than requiring a separate step nothing in
        the UI exposes.
        """
        self._refresh_inventory(system_version, run_id)
        result = self._container.production().produce(system_version, run_id=run_id)
        return ProductionOutcome(
            run_id=result.run_id,
            succeeded=result.succeeded,
            file_path=result.file_path,
            entity_count=len(result.document.entities) if result.document else 0,
            relation_count=len(result.document.relations) if result.document else 0,
            # Not result.errors: that's only what the production step itself
            # recorded. _refresh_inventory above records under this same
            # run_id too, so the count reported here must match what
            # list_errors_for_run(run_id) — the expandable detail view —
            # would show, or the two silently disagree.
            errors=[_to_error(error) for error in self._container.errors.list_for_run(run_id)],
        )

    def _refresh_inventory(self, system_version: SystemVersionRef, run_id: str) -> None:
        recorder = RunRecorder(
            run_id=run_id,
            platform=system_version.platform,
            errors=self._container.errors,
            clock=SystemClock(),
        )
        units, _ = self._container.configuration_data().list_software_units(
            system_version.platform, system_version.version, recorder
        )
        self._container.inventory.record(system_version, units)

    def probe_sources(self, platform: PlatformRef | None = None) -> list[SourceStatus]:
        """Touch every configured source and report whether it answered.

        Each source type is probed with the cheapest call its adapter offers,
        so an unreachable address, a missing credential, or a malformed
        response all surface the same way an acquisition would have found them.
        """
        scope = platform or PlatformRef(ProjectRef(_UNKNOWN), _UNKNOWN)
        checked_at = SystemClock().now()
        registry = self._container.registry()
        factory = self._container.factory

        statuses: list[SourceStatus] = []
        for configuration in registry.configurations:
            detail = ""
            try:
                adapter = factory.build(configuration)
                self._touch(configuration.source_type, adapter, scope)
            except AcquisitionFailure as failure:
                detail = failure.reason
            except KeyError:
                detail = (
                    f"No adapter registered for access method "
                    f"'{configuration.access_method.value}'"
                )

            statuses.append(
                SourceStatus(
                    source_type=configuration.source_type.value,
                    source_name=configuration.name,
                    accessibility=(
                        Accessibility.UNREACHABLE if detail else Accessibility.REACHABLE
                    ),
                    checked_at=checked_at,
                    detail=detail,
                )
            )

        return statuses

    def list_errors(self, platform: PlatformRef) -> list[ProductionError]:
        """List the failures MSD recorded for a platform (SRS VAE-01.8)."""
        return [
            _to_error(error) for error in self._container.errors.list_for_platform(platform)
        ]

    def list_errors_for_run(self, run_id: str) -> list[ProductionError]:
        """List the failures MSD recorded for one production run (SRS VAE-01.8)."""
        return [_to_error(error) for error in self._container.errors.list_for_run(run_id)]

    def list_data_sources(self) -> list[DataSourceConfig]:
        """List every configured external data source (SRS MSD.2-5, 8)."""
        return [_to_source_config(item) for item in self._container.data_sources.list_all()]

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
        """Save a data source configuration, encrypting any newly entered secret.

        Leaves a previously stored secret untouched when the operator edits a
        source's address/priority without re-entering its secret.
        """
        existing = self._container.data_sources.get(DataSourceType(source_type), name)
        if secret:
            encrypted = self._container.cipher.encrypt(secret)
        elif existing and existing.credential:
            encrypted = existing.credential.encrypted_secret
        else:
            encrypted = ""

        saved = self._container.data_sources.configure(
            DataSourceConfiguration(
                source_type=DataSourceType(source_type),
                name=name,
                access_method=AccessMethod(access_method),
                connection_address=connection_address,
                credential=(
                    CredentialReference(username=username, encrypted_secret=encrypted)
                    if encrypted
                    else None
                ),
                priority=priority,
            )
        )
        return _to_source_config(saved)

    def delete_data_source(self, source_type: str, name: str) -> bool:
        """Delete a data source configuration."""
        return self._container.data_sources.remove(DataSourceType(source_type), name)

    @staticmethod
    def _touch(source_type: DataSourceType, adapter, platform: PlatformRef) -> None:
        if source_type is DataSourceType.CONFIGURATION_MANAGEMENT_DATABASE:
            adapter.list_projects()
        elif source_type is DataSourceType.SOURCE_REPOSITORY:
            adapter.check_access()
        elif source_type is DataSourceType.PACKAGE_REPOSITORY:
            adapter.find_artifact(_PROBE_UNIT)
        elif source_type is DataSourceType.NETWORK_TOPOLOGY:
            adapter.fetch(platform)

    def _recorder(self, platform: PlatformRef) -> RunRecorder:
        return RunRecorder(
            run_id=uuid4().hex,
            platform=platform,
            errors=self._container.errors,
            clock=SystemClock(),
        )


def _to_source_config(configuration: DataSourceConfiguration) -> DataSourceConfig:
    return DataSourceConfig(
        source_type=configuration.source_type.value,
        name=configuration.name,
        access_method=configuration.access_method.value,
        connection_address=configuration.connection_address,
        username=configuration.credential.username if configuration.credential else "",
        secret_set=bool(
            configuration.credential and configuration.credential.encrypted_secret
        ),
        priority=configuration.priority,
    )


def _to_error(error) -> ProductionError:
    return ProductionError(
        status=error.status.value,
        reason=error.reason,
        source_name=error.source_name,
        source_type=error.source_type,
        occurred_at=error.occurred_at,
        detail=error.detail,
    )
