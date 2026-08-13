"""
Description: Shared fixtures wiring MSD use cases against in-test source doubles.
Created by: Mustafa Can Caliskan
Date: 2026-07-31
"""

from __future__ import annotations

import shutil
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

import pytest

from msd.src.adapters.build.code_generation import PrebuiltCodeGenerator
from msd.src.adapters.extraction.java_imports import JavaImportExtractor
from msd.src.adapters.extraction.system_descriptor import SystemDescriptorExtractor
from msd.src.adapters.extraction.type_support import TypeSupportExtractor
from msd.src.adapters.extraction.unit_descriptor import UnitDescriptorExtractor
from msd.src.adapters.factory import AdapterContext, AdapterFactory
from msd.src.adapters.memory import (
    InMemoryAcquisitionErrorRepository,
    InMemoryDataSourceConfigurationRepository,
    InMemoryModelSetupDataRepository,
    InMemoryVersionInventoryRepository,
)
from msd.src.adapters.rules_config import RulesConfig, load_rules
from msd.src.adapters.support import FixedClock
from msd.src.model.data_source import (
    AccessMethod,
    CredentialReference,
    DataSourceConfiguration,
    DataSourceType,
)
from msd.src.ports.extraction import CodeGenerationPort
from msd.src.use_cases.acquire_configuration_data import AcquireConfigurationDataUseCase
from msd.src.use_cases.acquire_network_topology import AcquireNetworkTopologyUseCase
from msd.src.use_cases.assemble_model_setup_data import AssembleModelSetupDataUseCase
from msd.src.use_cases.ingest_source_repository import IngestSourceRepositoryUseCase
from msd.src.use_cases.manage_data_sources import ManageDataSourcesUseCase
from msd.src.use_cases.manage_version_inventory import ManageVersionInventoryUseCase
from msd.src.use_cases.produce_model_setup_data import ProduceModelSetupDataUseCase
from msd.tests.support.doubles import (
    DoubleConfigurationManagementDatabase,
    DoubleNetworkTopologySource,
    DoublePackageRepository,
    FaultPolicy,
)
from msd.tests.support.fake_source_repository import (
    REPOSITORY_ROOT,
    FakeSourceCodeRepository,
)
from shared.types.identifiers import system_version

#: The sources every test starts with. Access methods are the in-test ones:
#: the doubles are registered against them, so no test ever reaches a server.
STANDIN_SOURCES = [
    ("configuration_management_database", "cmdb-primary", 0),
    ("source_repository", "bitbucket-a", 0),
    ("source_repository", "bitbucket-b", 1),
    ("source_repository", "gitlab-main", 2),
    ("package_repository", "artifactory-main", 0),
    ("network_topology", "topology-source", 0),
]

#: The scope every test works in.
PROJECT = "skyline"
PLATFORM = "avionics"
SYSTEM_VERSION = "1.0.0"

#: Fixed production time, so file names and error times are predictable.
FIXED_NOW = datetime(2026, 7, 31, 9, 30, tzinfo=UTC)


@dataclass
class Harness:
    """A fully wired MSD, backed by a private copy of the fake data tree.

    Attributes:
        data_root: The test's own copy of the fake data tree, safe to mutate.
        workspace: Directory transferred files are copied into.
        rules: Rules the adapters read their behaviour from.
        faults: Fault policy the test can inject into.
        data_sources: Data source configuration use case.
        configurations: Store the configurations live in.
        inventory: Version inventory use case.
        errors: Recorded failures.
        documents: Produced documents.
        clock: Fixed clock.
    """

    data_root: Path
    workspace: Path
    rules: RulesConfig
    faults: FaultPolicy
    data_sources: ManageDataSourcesUseCase
    configurations: InMemoryDataSourceConfigurationRepository
    inventory: ManageVersionInventoryUseCase
    errors: InMemoryAcquisitionErrorRepository
    documents: InMemoryModelSetupDataRepository
    clock: FixedClock

    @property
    def scope(self):
        """The system version every test operates on."""
        return system_version(PROJECT, PLATFORM, SYSTEM_VERSION)

    def factory(self) -> AdapterFactory:
        """Build a factory whose adapters are this harness's doubles."""
        factory = AdapterFactory(
            AdapterContext(
                workspace=self.workspace,
                classifier=self.rules.classifier,
                credentials=_AlwaysResolves(),
            )
        )
        factory.register(
            DataSourceType.CONFIGURATION_MANAGEMENT_DATABASE,
            AccessMethod.SQL,
            lambda configuration, secret: DoubleConfigurationManagementDatabase(
                configuration, self.faults
            ),
        )
        factory.register(
            DataSourceType.SOURCE_REPOSITORY,
            AccessMethod.GIT_HTTPS,
            lambda configuration, secret: FakeSourceCodeRepository(
                configuration=configuration,
                workspace=self.workspace,
                classifier=self.rules.classifier,
                faults=self.faults,
                root=self.data_root,
            ),
        )
        factory.register(
            DataSourceType.PACKAGE_REPOSITORY,
            AccessMethod.REST,
            lambda configuration, secret: DoublePackageRepository(configuration, self.faults),
        )
        factory.register(
            DataSourceType.NETWORK_TOPOLOGY,
            AccessMethod.ANSIBLE,
            lambda configuration, secret: DoubleNetworkTopologySource(
                configuration, self.faults
            ),
        )
        return factory

    def configuration_data(self) -> AcquireConfigurationDataUseCase:
        """Build the configuration-data acquisition use case."""
        return AcquireConfigurationDataUseCase(
            self.factory().build_all(
                self.data_sources.registry(), DataSourceType.CONFIGURATION_MANAGEMENT_DATABASE
            )
        )

    def topology(self) -> AcquireNetworkTopologyUseCase:
        """Build the topology acquisition use case."""
        return AcquireNetworkTopologyUseCase(
            sources=self.factory().build_all(
                self.data_sources.registry(), DataSourceType.NETWORK_TOPOLOGY
            ),
            configurations=self.configurations,
        )

    def ingestion(self) -> IngestSourceRepositoryUseCase:
        """Build the source ingestion use case over every configured repository."""
        registry = self.data_sources.registry()
        adapters = self.factory().build_all(registry, DataSourceType.SOURCE_REPOSITORY)
        return IngestSourceRepositoryUseCase(
            adapters={adapter.source_name: adapter for adapter in adapters},
            configurations=registry.configurations,
            mandatory_files=self.rules.mandatory_files,
        )

    def assembler(self, generator: CodeGenerationPort | None = None):
        """Build the validation-and-assembly use case.

        Args:
            generator: Code generation adapter; defaults to the prebuilt one.
        """
        return AssembleModelSetupDataUseCase(
            generator=generator or PrebuiltCodeGenerator(),
            unit_extractors=[
                UnitDescriptorExtractor(self.rules.unit_descriptor_extraction),
                TypeSupportExtractor(self.rules.type_support_extraction),
                JavaImportExtractor(self.rules.java_import_extraction),
            ],
            model_extractors=[
                SystemDescriptorExtractor(self.rules.system_descriptor_extraction)
            ],
            mandatory_fields=self.rules.mandatory_fields,
            clock=self.clock,
        )

    def production(self, generator: CodeGenerationPort | None = None):
        """Build the full production workflow."""
        return ProduceModelSetupDataUseCase(
            inventory=self.inventory,
            ingestion=self.ingestion(),
            assembler=self.assembler(generator),
            topology=self.topology(),
            package_repositories=self.factory().build_all(
                self.data_sources.registry(), DataSourceType.PACKAGE_REPOSITORY
            ),
            documents=self.documents,
            errors=self.errors,
            clock=self.clock,
        )

    def record_inventory(self):
        """Record the baseline inventory from the fake CM database."""
        from msd.src.use_cases._recording import RunRecorder

        recorder = RunRecorder(
            run_id="setup", platform=self.scope.platform, errors=self.errors, clock=self.clock
        )
        units, _ = self.configuration_data().list_software_units(
            self.scope.platform, SYSTEM_VERSION, recorder
        )
        return self.inventory.record(self.scope, units)

    def unit_path(self, source_name: str, versioned_name: str) -> Path:
        """Return a unit's directory inside this harness's private tree."""
        return self.data_root / source_name / versioned_name


#: Which access method each source type is configured with in tests. Real
#: protocol names, so the wiring under test is the production wiring; only the
#: adapters registered against them are doubles.
_ACCESS_METHODS = {
    "configuration_management_database": AccessMethod.SQL,
    "source_repository": AccessMethod.GIT_HTTPS,
    "package_repository": AccessMethod.REST,
    "network_topology": AccessMethod.ANSIBLE,
}


class _AlwaysResolves:
    """Credential resolver that never fails, so tests need no environment setup."""

    def resolve(self, reference) -> str:
        """Return a placeholder secret for any reference."""
        return f"secret-for-{reference.encrypted_secret}"


@pytest.fixture
def harness(tmp_path: Path) -> Harness:
    """Wire MSD against a private copy of the fake data tree."""
    data_root = tmp_path / "repositories"
    shutil.copytree(REPOSITORY_ROOT, data_root)

    configurations = InMemoryDataSourceConfigurationRepository()
    data_sources = ManageDataSourcesUseCase(configurations)
    data_sources.seed(
        [
            DataSourceConfiguration(
                source_type=DataSourceType(source_type),
                name=name,
                access_method=_ACCESS_METHODS[source_type],
                connection_address=f"double://{name}",
                credential=CredentialReference(
                    username="saag", encrypted_secret=f"TEST_{name.upper().replace('-', '_')}"
                ),
                priority=priority,
            )
            for source_type, name, priority in STANDIN_SOURCES
        ]
    )

    return Harness(
        data_root=data_root,
        workspace=tmp_path / "workspace",
        rules=load_rules(),
        faults=FaultPolicy(),
        data_sources=data_sources,
        configurations=configurations,
        inventory=ManageVersionInventoryUseCase(InMemoryVersionInventoryRepository()),
        errors=InMemoryAcquisitionErrorRepository(),
        documents=InMemoryModelSetupDataRepository(),
        clock=FixedClock(FIXED_NOW),
    )
