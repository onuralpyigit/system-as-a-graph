"""
Description: Verifies MSD's PostgreSQL repositories against a real database.
Created by: Mustafa Can Caliskan
Date: 2026-07-31
"""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from msd.src.adapters.postgres.repositories import (
    PostgresAcquisitionErrorRepository,
    PostgresDataSourceConfigurationRepository,
    PostgresModelSetupDataRepository,
    PostgresVersionInventoryRepository,
)
from msd.src.adapters.postgres.tables import (
    acquisition_errors,
    build_engine,
    create_schema,
    data_sources,
    database_url,
    model_setup_data_records,
    version_inventory_entries,
)
from msd.src.model.data_source import (
    AccessMethod,
    CredentialReference,
    DataSourceConfiguration,
    DataSourceType,
)
from msd.src.model.version_inventory import (
    SoftwareUnitVersion,
    SoftwareUnitVersionInventory,
)
from msd.src.ports.repositories import ModelSetupDataRecord
from shared.errors.acquisition import AcquisitionError, AcquisitionStatus
from shared.types.identifiers import system_version

pytestmark = pytest.mark.skipif(
    database_url() is None,
    reason="DATABASE_URL is not set; PostgreSQL repositories are not exercised",
)

SCOPE = system_version("skyline", "avionics", "1.0.0")


@pytest.fixture
def engine():
    """An engine against a freshly-created, empty MSD schema."""
    from sqlalchemy import delete

    engine = build_engine(database_url())
    create_schema(engine)

    with engine.begin() as connection:
        for table in (
            acquisition_errors,
            model_setup_data_records,
            version_inventory_entries,
            data_sources,
        ):
            connection.execute(delete(table))

    return engine


def test_data_source_configuration_round_trips(engine):
    """A configuration survives a write/read cycle, encrypted secret included."""
    repository = PostgresDataSourceConfigurationRepository(engine)
    configuration = DataSourceConfiguration(
        source_type=DataSourceType.SOURCE_REPOSITORY,
        name="bitbucket-a",
        access_method=AccessMethod.GIT_HTTPS,
        connection_address="https://bitbucket.example/scm/saag",
        credential=CredentialReference(username="ops", encrypted_secret="ciphertext-BB-A"),
        priority=2,
    )

    repository.save(configuration)

    assert repository.get(DataSourceType.SOURCE_REPOSITORY, "bitbucket-a") == configuration
    assert repository.list_all() == [configuration]
    assert repository.delete(DataSourceType.SOURCE_REPOSITORY, "bitbucket-a") is True
    assert repository.list_all() == []


def test_inventory_keeps_baseline_and_candidate_side_by_side(engine):
    """Both rows for one unit persist, distinguished by the candidate flag."""
    repository = PostgresVersionInventoryRepository(engine)
    inventory = SoftwareUnitVersionInventory(system_version=SCOPE)
    inventory.record(SoftwareUnitVersion(unit_name="nav_app", version="1.2.0"))
    inventory.add_candidate(SoftwareUnitVersion(unit_name="nav_app", version="1.3.0"))

    repository.save(inventory)

    stored = repository.get(SCOPE)
    assert [entry.version for entry in stored.baseline] == ["1.2.0"]
    assert [entry.version for entry in stored.candidates] == ["1.3.0"]


def test_acquisition_errors_are_queryable_by_run_and_platform(engine):
    """A recorded failure comes back with its full attribution intact."""
    repository = PostgresAcquisitionErrorRepository(engine)
    error = AcquisitionError(
        status=AcquisitionStatus.ACCESS_ERROR,
        reason="repository unreachable",
        source_name="bitbucket-b",
        source_type=DataSourceType.SOURCE_REPOSITORY.value,
        platform=SCOPE.platform,
        occurred_at=datetime(2026, 7, 31, 9, 30, tzinfo=UTC),
        detail="timeout",
    )

    repository.record("run-1", error)

    assert repository.list_for_run("run-1") == [error]
    assert repository.list_for_platform(SCOPE.platform) == [error]


def test_documents_are_stored_in_the_database_and_indexed_by_scope(engine):
    """The document round-trips through PostgreSQL; the row lists by scope."""
    repository = PostgresModelSetupDataRepository(engine)
    produced_at = datetime(2026, 7, 31, 9, 30, tzinfo=UTC)
    document = {
        "schema_version": "1.0",
        "project": "skyline",
        "platform": "avionics",
        "system_version": "1.0.0",
        "entities": [],
        "relations": [],
        "source_files": [],
        "provenance": {
            "produced_at": produced_at.isoformat(),
            "run_id": "run-1",
            "sources": [],
            "excluded_units": {},
            "not_supplied": [],
        },
    }

    path = repository.save(
        ModelSetupDataRecord(
            run_id="run-1",
            system_version=SCOPE,
            file_path="",
            produced_at=produced_at,
            entity_count=0,
            relation_count=0,
            failure_count=0,
        ),
        document,
    )

    assert path == "msd_2026-07-31_avionics.json"
    assert [record.run_id for record in repository.list_for(SCOPE)] == ["run-1"]
    assert repository.load("run-1") == document
    assert repository.load("missing-run") is None
