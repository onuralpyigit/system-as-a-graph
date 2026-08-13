"""
Description: Composition root wiring MSD's use cases to concrete adapters.
Created by: Mustafa Can Caliskan
Date: 2026-07-31
"""

from __future__ import annotations

import os
import tempfile
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from msd.src.adapters.build.code_generation import (
    GmakeCodeGenerator,
    PrebuiltCodeGenerator,
)
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
from msd.src.adapters.postgres.repositories import (
    PostgresAcquisitionErrorRepository,
    PostgresDataSourceConfigurationRepository,
    PostgresModelSetupDataRepository,
    PostgresVersionInventoryRepository,
)
from msd.src.adapters.postgres.tables import build_engine, create_schema, database_url
from msd.src.adapters.rules_config import RulesConfig, get_rules
from msd.src.adapters.source_seed import load_seed, seed_file
from msd.src.adapters.support import (
    CipherCredentialResolver,
    FernetSecretCipher,
    SystemClock,
)
from msd.src.model.data_source import DataSourceRegistry, DataSourceType
from msd.src.ports.repositories import (
    AcquisitionErrorRepository,
    DataSourceConfigurationRepository,
    ModelSetupDataRepository,
    VersionInventoryRepository,
)
from msd.src.use_cases.acquire_configuration_data import AcquireConfigurationDataUseCase
from msd.src.use_cases.acquire_network_topology import AcquireNetworkTopologyUseCase
from msd.src.use_cases.assemble_model_setup_data import AssembleModelSetupDataUseCase
from msd.src.use_cases.ingest_source_repository import IngestSourceRepositoryUseCase
from msd.src.use_cases.manage_data_sources import ManageDataSourcesUseCase
from msd.src.use_cases.manage_version_inventory import ManageVersionInventoryUseCase
from msd.src.use_cases.produce_model_setup_data import ProduceModelSetupDataUseCase

#: Directory transferred files are copied into. Kept separate from every
#: source so generation and extraction never write back into one.
WORKSPACE_ENV_VAR = "MSD_WORKSPACE_DIR"


@dataclass
class Container:
    """The wired object graph one process serves requests from.

    Attributes:
        rules: Pattern-driven rules every adapter reads its behaviour from.
        data_sources: Data source configuration use case.
        configurations: Repository the configurations live in.
        inventory: Version inventory use case.
        errors: Repository failures are recorded in.
        documents: Repository produced documents are written through.
        workspace: Directory transferred files are copied into.
        factory: Builds one adapter per configured source.
        cipher: Encrypts/decrypts operator-entered source credentials.
    """

    rules: RulesConfig
    data_sources: ManageDataSourcesUseCase
    configurations: DataSourceConfigurationRepository
    inventory: ManageVersionInventoryUseCase
    errors: AcquisitionErrorRepository
    documents: ModelSetupDataRepository
    workspace: Path
    factory: AdapterFactory
    cipher: FernetSecretCipher

    def registry(self) -> DataSourceRegistry:
        """Build a registry over the currently configured sources."""
        return self.data_sources.registry()

    def configuration_data(self) -> AcquireConfigurationDataUseCase:
        """Build the configuration-data acquisition use case for this request."""
        return AcquireConfigurationDataUseCase(
            self.factory.build_all(
                self.registry(), DataSourceType.CONFIGURATION_MANAGEMENT_DATABASE
            )
        )

    def topology(self) -> AcquireNetworkTopologyUseCase:
        """Build the topology acquisition use case for this request."""
        return AcquireNetworkTopologyUseCase(
            sources=self.factory.build_all(self.registry(), DataSourceType.NETWORK_TOPOLOGY),
            configurations=self.configurations,
        )

    def production(self) -> ProduceModelSetupDataUseCase:
        """Build the full production workflow for this request.

        Adapters are built per request rather than held, so an edited source
        configuration takes effect on the next run without a restart.
        """
        registry = self.registry()
        repositories = self.factory.build_all(registry, DataSourceType.SOURCE_REPOSITORY)

        return ProduceModelSetupDataUseCase(
            inventory=self.inventory,
            ingestion=IngestSourceRepositoryUseCase(
                adapters={adapter.source_name: adapter for adapter in repositories},
                configurations=registry.configurations,
                mandatory_files=self.rules.mandatory_files,
            ),
            assembler=AssembleModelSetupDataUseCase(
                generator=_build_generator(self.rules),
                unit_extractors=[
                    UnitDescriptorExtractor(self.rules.unit_descriptor_extraction),
                    TypeSupportExtractor(self.rules.type_support_extraction),
                    JavaImportExtractor(self.rules.java_import_extraction),
                ],
                model_extractors=[
                    SystemDescriptorExtractor(self.rules.system_descriptor_extraction)
                ],
                mandatory_fields=self.rules.mandatory_fields,
                clock=SystemClock(),
            ),
            topology=self.topology(),
            package_repositories=self.factory.build_all(
                registry, DataSourceType.PACKAGE_REPOSITORY
            ),
            documents=self.documents,
            errors=self.errors,
            clock=SystemClock(),
        )


def build_container() -> Container:
    """Wire the object graph from the environment.

    Falls back to in-memory repositories when no database is configured, so the
    service still starts and the fake profile stays runnable without
    infrastructure.

    Returns:
        The wired container.
    """
    rules = get_rules()
    workspace = Path(os.getenv(WORKSPACE_ENV_VAR) or Path(tempfile.gettempdir()) / "saag-msd")
    cipher = FernetSecretCipher()

    configurations: DataSourceConfigurationRepository
    inventory_repository: VersionInventoryRepository
    errors: AcquisitionErrorRepository
    documents: ModelSetupDataRepository

    url = database_url()
    if url:
        engine = build_engine(url)
        create_schema(engine)
        configurations = PostgresDataSourceConfigurationRepository(engine)
        inventory_repository = PostgresVersionInventoryRepository(engine)
        errors = PostgresAcquisitionErrorRepository(engine)
        documents = PostgresModelSetupDataRepository(engine)
    else:
        configurations = InMemoryDataSourceConfigurationRepository()
        inventory_repository = InMemoryVersionInventoryRepository()
        errors = InMemoryAcquisitionErrorRepository()
        documents = InMemoryModelSetupDataRepository()

    data_sources = ManageDataSourcesUseCase(configurations)
    seed = seed_file()
    if seed is not None:
        data_sources.seed(load_seed(seed, cipher))

    return Container(
        rules=rules,
        data_sources=data_sources,
        configurations=configurations,
        inventory=ManageVersionInventoryUseCase(inventory_repository),
        errors=errors,
        documents=documents,
        workspace=workspace,
        cipher=cipher,
        factory=AdapterFactory(
            AdapterContext(
                workspace=workspace,
                classifier=rules.classifier,
                credentials=CipherCredentialResolver(cipher),
            )
        ),
    )


@lru_cache(maxsize=1)
def get_container() -> Container:
    """Return the process-wide container, building it on first use."""
    return build_container()


def _build_generator(rules: RulesConfig):
    """Pick the code generation adapter the rules file asks for.

    ``prebuilt`` consumes sources the repository already carries, for
    environments without the project's build toolchain; ``make`` runs the build.
    The port contract is identical either way.
    """
    settings = rules.code_generation
    if str(settings.get("mode", "prebuilt")).strip().lower() != "make":
        return PrebuiltCodeGenerator()

    return GmakeCodeGenerator(
        command=list(settings.get("command", ["gmake", "regenerate_code"])),
        timeout_seconds=int(settings.get("timeout_seconds", 300)),
    )
