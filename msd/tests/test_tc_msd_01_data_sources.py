"""
Description: TC-MSD-01 — Data Source Connector & Configuration Manager (SRS MSD.2-8).
Created by: Mustafa Can Caliskan
Date: 2026-07-31
"""

from __future__ import annotations

from msd.src.model.data_source import (
    AccessMethod,
    CredentialReference,
    DataSourceConfiguration,
    DataSourceType,
)
from msd.src.model.network_topology import NetworkComponent, TopologyAcquisitionMethod
from msd.src.use_cases._recording import RunRecorder
from shared.types.identifiers import PlatformRef, ProjectRef


def test_every_source_type_accepts_and_persists_configuration(harness):
    """All four external source types are configurable and retrievable."""
    stored_types = {item.source_type for item in harness.data_sources.list_all()}

    assert stored_types == set(DataSourceType)


def test_one_source_type_holds_several_configured_servers(harness):
    """A source type is a one-to-many binding, not a single system."""
    repositories = harness.data_sources.registry().of_type(DataSourceType.SOURCE_REPOSITORY)

    assert [item.name for item in repositories] == [
        "bitbucket-a",
        "bitbucket-b",
        "gitlab-main",
    ]


def test_configuration_can_be_edited_and_deleted(harness):
    """Saving over a key replaces it; deleting removes it (SRS MSD.8)."""
    edited = DataSourceConfiguration(
        source_type=DataSourceType.SOURCE_REPOSITORY,
        name="bitbucket-a",
        access_method=AccessMethod.GIT_HTTPS,
        connection_address="https://bitbucket.example/scm/saag",
        credential=CredentialReference(username="ops", encrypted_secret="BB_A_TOKEN"),
        priority=5,
    )
    harness.data_sources.configure(edited)

    stored = harness.data_sources.get(DataSourceType.SOURCE_REPOSITORY, "bitbucket-a")
    assert stored.access_method is AccessMethod.GIT_HTTPS
    assert stored.connection_address == "https://bitbucket.example/scm/saag"
    assert stored.priority == 5

    assert harness.data_sources.remove(DataSourceType.SOURCE_REPOSITORY, "bitbucket-a") is True
    assert harness.data_sources.get(DataSourceType.SOURCE_REPOSITORY, "bitbucket-a") is None


def test_configuration_never_stores_the_secret_itself(harness):
    """Only the encrypted secret is persisted, never a plaintext one."""
    stored = harness.data_sources.get(DataSourceType.SOURCE_REPOSITORY, "bitbucket-a")

    assert stored.credential.encrypted_secret == "TEST_BITBUCKET_A"
    assert not hasattr(stored.credential, "secret")


def test_topology_is_acquired_automatically_from_the_configured_source(harness):
    """Automatic acquisition reads the configured topology source (SRS MSD.6)."""
    recorder = RunRecorder(
        run_id="tc01", platform=harness.scope.platform, errors=harness.errors, clock=harness.clock
    )

    topology = harness.topology().acquire(harness.scope.platform, recorder)

    assert topology is not None
    assert topology.method is TopologyAcquisitionMethod.AUTOMATIC
    assert topology.source_name == "topology-source"
    assert {component.name for component in topology.components} == {
        "switch-core-1",
        "switch-core-2",
        "segment-mission",
    }


def test_topology_can_be_entered_manually(harness):
    """Manual entry produces the same domain object, marked as manual (SRS MSD.7)."""
    topology = harness.topology().enter_manually(
        harness.scope.platform,
        [NetworkComponent(name="switch-lab-1", component_type="switch")],
    )

    assert topology.method is TopologyAcquisitionMethod.MANUAL
    assert [component.name for component in topology.components] == ["switch-lab-1"]


def test_a_manually_entered_topology_is_saved_and_scoped_to_its_platform(harness):
    """The entry survives the request that made it, per platform (SRS MSD.7-8)."""
    harness.topology().enter_manually(
        harness.scope.platform,
        [NetworkComponent(name="switch-lab-1", component_type="switch")],
    )

    stored = harness.topology().stored_manual(harness.scope.platform)
    assert stored is not None
    assert [component.name for component in stored.components] == ["switch-lab-1"]

    other_platform = PlatformRef(ProjectRef("skyline"), "ground-station")
    assert harness.topology().stored_manual(other_platform) is None


def test_a_manually_entered_topology_wins_over_the_automatic_source(harness):
    """Entering a topology and having it ignored would make MSD.7 pointless."""
    recorder = RunRecorder(
        run_id="tc01", platform=harness.scope.platform, errors=harness.errors, clock=harness.clock
    )
    harness.topology().enter_manually(
        harness.scope.platform,
        [NetworkComponent(name="switch-lab-1", component_type="switch")],
    )

    resolved = harness.topology().resolve(harness.scope.platform, recorder)

    assert resolved.method is TopologyAcquisitionMethod.MANUAL
    assert [component.name for component in resolved.components] == ["switch-lab-1"]
