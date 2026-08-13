"""
Description: Drives the MSD production workflow across its five design elements (SRS MSD.1).
Created by: Mustafa Can Caliskan
Date: 2026-07-31
"""

from __future__ import annotations

from dataclasses import dataclass, field

from msd.src.model.data_source import DataSourceType
from msd.src.model.version_inventory import SoftwareUnitVersion
from msd.src.ports.external_sources import PackageRepositoryPort
from msd.src.ports.repositories import (
    AcquisitionErrorRepository,
    ModelSetupDataRecord,
    ModelSetupDataRepository,
)
from msd.src.ports.support import ClockPort
from msd.src.use_cases._recording import RunRecorder
from msd.src.use_cases.acquire_network_topology import AcquireNetworkTopologyUseCase
from msd.src.use_cases.assemble_model_setup_data import AssembleModelSetupDataUseCase
from msd.src.use_cases.ingest_source_repository import IngestSourceRepositoryUseCase
from msd.src.use_cases.manage_version_inventory import ManageVersionInventoryUseCase
from shared.contracts.model_setup_data import ModelSetupDataDocument
from shared.errors.acquisition import AcquisitionError, AcquisitionFailure
from shared.types.identifiers import SystemVersionRef


@dataclass
class ProductionResult:
    """Outcome of one Model Setup Data production run.

    Attributes:
        run_id: Identifier of this run.
        document: The assembled document, or None when nothing survived
            verification.
        file_path: The document's display name; empty when none was produced.
        errors: Every failure recorded during the run.
        excluded_units: Units left out of the model, mapped to why.
    """

    run_id: str
    document: ModelSetupDataDocument | None = None
    file_path: str = ""
    errors: list[AcquisitionError] = field(default_factory=list)
    excluded_units: dict[str, str] = field(default_factory=dict)

    @property
    def succeeded(self) -> bool:
        """Whether a document was produced at all.

        True even when some units were excluded: a partial model that names its
        gaps is a usable result, and SRS MSD.23 asks for the data that passed
        verification, not for all-or-nothing.
        """
        return self.document is not None


class ProduceModelSetupDataUseCase:
    """Drives acquisition, extraction, verification, and assembly end to end.

    This is the workflow SRS MSD.1 describes: everything acquired is validated
    through one path and only what passes reaches the Model Setup Data file.
    Failures never abort the run — they are recorded, the affected unit is
    excluded, and the exclusion is written into the document's provenance so
    the gap is visible to whoever builds the model from it.
    """

    def __init__(
        self,
        inventory: ManageVersionInventoryUseCase,
        ingestion: IngestSourceRepositoryUseCase,
        assembler: AssembleModelSetupDataUseCase,
        topology: AcquireNetworkTopologyUseCase,
        package_repositories: list[PackageRepositoryPort],
        documents: ModelSetupDataRepository,
        errors: AcquisitionErrorRepository,
        clock: ClockPort,
    ) -> None:
        """Initialize the use case.

        Args:
            inventory: Supplies the software units in scope.
            ingestion: Transfers those units' files.
            assembler: Verifies the acquired data and assembles the document.
            topology: Supplies network topology.
            package_repositories: Confirm each unit has a package artifact.
            documents: Store the produced document is written to.
            errors: Store failures are recorded in.
            clock: Supplies error and production times.
        """
        self._inventory = inventory
        self._ingestion = ingestion
        self._assembler = assembler
        self._topology = topology
        self._package_repositories = package_repositories
        self._documents = documents
        self._errors = errors
        self._clock = clock

    def produce(self, system_version: SystemVersionRef, run_id: str) -> ProductionResult:
        """Produce the Model Setup Data file for one system version.

        Args:
            system_version: Scope to produce for.
            run_id: Identifier to record this run under.

        Returns:
            The production result, including every recorded failure.
        """
        recorder = RunRecorder(
            run_id=run_id,
            platform=system_version.platform,
            errors=self._errors,
            clock=self._clock,
        )
        result = ProductionResult(run_id=run_id)

        recorded = self._inventory.get(system_version)
        if recorded is None or not recorded.entries:
            recorder.record_missing(
                reason=(
                    f"No Software Unit Version Inventory recorded for "
                    f"'{system_version}'; nothing to produce from"
                ),
                source_name="",
                source_type=DataSourceType.CONFIGURATION_MANAGEMENT_DATABASE.value,
            )
            result.errors = recorder.recorded
            return result

        units = recorded.entries
        artifacts = self._confirm_packages(units, recorder)

        ingestion = self._ingestion.ingest(units, recorder)
        topology = self._topology.resolve(system_version.platform, recorder)

        assembly = self._assembler.assemble(
            system_version=system_version,
            ingestion=ingestion,
            topology=topology,
            artifacts=artifacts,
            run_id=run_id,
            recorder=recorder,
        )
        document = assembly.document
        result.excluded_units.update(assembly.excluded_units)

        produced_at = document.provenance.produced_at

        result.document = document
        result.errors = recorder.recorded
        result.file_path = self._documents.save(
            ModelSetupDataRecord(
                run_id=run_id,
                system_version=system_version,
                file_path="",
                produced_at=produced_at,
                entity_count=len(document.entities),
                relation_count=len(document.relations),
                failure_count=len(result.errors),
            ),
            document.to_dict(),
        )

        return result

    def _confirm_packages(
        self, units: list[SoftwareUnitVersion], recorder: RunRecorder
    ) -> dict[str, dict[str, str]]:
        """Confirm every inventory entry has a package artifact (SRS MSD.4).

        A unit with no artifact anywhere is recorded as a validation failure
        rather than passing silently, but it is not excluded: its source code
        may still be transferable, and the missing artifact is the operator's
        call to act on.

        Returns:
            Artifact metadata per unit name, each carrying the repository that
            supplied it, so what was obtained from the package repositories is
            traceable rather than merely checked and discarded.
        """
        artifacts: dict[str, dict[str, str]] = {}
        if not self._package_repositories:
            return artifacts

        for unit in units:
            found = False
            for repository in self._package_repositories:
                try:
                    artifact = repository.find_artifact(unit)
                    if artifact is not None:
                        artifacts[unit.unit_name] = {
                            **artifact,
                            "source_name": repository.source_name,
                        }
                        found = True
                        break
                except AcquisitionFailure as failure:
                    recorder.record_failure(
                        failure,
                        source_name=repository.source_name,
                        source_type=DataSourceType.PACKAGE_REPOSITORY.value,
                    )

            if not found:
                recorder.record_missing(
                    reason=(
                        f"No package artifact found for '{unit.versioned_name}' in any "
                        f"configured package repository"
                    ),
                    source_name=",".join(
                        repository.source_name for repository in self._package_repositories
                    ),
                    source_type=DataSourceType.PACKAGE_REPOSITORY.value,
                )

        return artifacts

