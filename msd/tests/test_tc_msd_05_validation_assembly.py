"""
Description: TC-MSD-05 — Data Validation & Model Setup Data Assembler (SRS MSD.21-23).
Created by: Mustafa Can Caliskan
Date: 2026-07-31
"""

from __future__ import annotations

from msd.src.adapters.build.code_generation import (
    GmakeCodeGenerator,
    PrebuiltCodeGenerator,
)
from msd.src.ports.extraction import GenerationResult
from shared.contracts.model_setup_data import (
    SCHEMA_VERSION,
    ModelSetupDataDocument,
    NodeType,
    RelationType,
)
from shared.errors.acquisition import AcquisitionStatus


def test_complete_source_data_assembles_into_one_document(harness):
    """Data with every mandatory field present passes and is assembled (SRS MSD.21, 23)."""
    harness.record_inventory()

    result = harness.production().produce(harness.scope, run_id="tc05")

    assert result.succeeded
    assert result.errors == []
    assert result.document.project == "skyline"
    assert result.document.platform == "avionics"
    assert result.document.system_version == "1.0.0"
    assert result.document.schema_version == SCHEMA_VERSION


def test_the_document_is_stored_where_csm_can_read_it(harness):
    """The document round-trips through the repository under the agreed name (CDR-24)."""
    harness.record_inventory()

    result = harness.production().produce(harness.scope, run_id="tc05")

    assert result.file_path == "msd_2026-07-31_avionics.json"

    stored = harness.documents.load(result.run_id)
    reloaded = ModelSetupDataDocument.from_dict(stored)
    assert len(reloaded.entities) == len(result.document.entities)
    assert len(reloaded.relations) == len(result.document.relations)


def test_data_failing_the_mandatory_field_check_is_excluded_and_recorded(harness):
    """A topic with no QoS is left out, and its failure is fully attributed (SRS MSD.22)."""
    generated = harness.unit_path("bitbucket-a", "nav_app_1.2.0") / "generated"
    (generated / "NavStateTypeSupport.java").unlink()
    harness.record_inventory()

    result = harness.production().produce(harness.scope, run_id="tc05")

    topics = {
        entity.name for entity in result.document.entities if entity.node_type is NodeType.TOPIC
    }
    assert "NavState" not in topics
    assert "SensorReading" in topics

    failure = next(
        error for error in result.errors if "NavState" in error.reason
    )
    assert failure.status is AcquisitionStatus.MISSING_DATA
    assert failure.platform.project.name == "skyline"
    assert failure.occurred_at == harness.clock.now()
    assert "durability" in failure.reason


def test_relations_to_excluded_entities_are_dropped_too(harness):
    """A relation pointing at a rejected node would be invalid downstream."""
    (harness.unit_path("bitbucket-a", "nav_app_1.2.0") / "generated" /
     "NavStateTypeSupport.java").unlink()
    harness.record_inventory()

    result = harness.production().produce(harness.scope, run_id="tc05")

    assert all(
        relation.target_name != "NavState" for relation in result.document.relations
    )


def test_manually_entered_source_data_reaches_the_document(harness):
    """Manually entered data is verified and assembled like fetched data (SRS MSD.21)."""
    from msd.src.model.network_topology import NetworkComponent

    harness.record_inventory()
    harness.topology().enter_manually(
        harness.scope.platform,
        [NetworkComponent(name="switch-lab-1", component_type="switch")],
    )

    result = harness.production().produce(harness.scope, run_id="tc05")

    components = {
        entity.name
        for entity in result.document.entities
        if entity.node_type is NodeType.NETWORK_COMPONENT
    }
    assert components == {"switch-lab-1"}
    assert "manual-entry" in result.document.provenance.sources


def test_package_artifacts_are_carried_into_the_model(harness):
    """What the package repository supplied is recorded, not merely checked (SRS MSD.4)."""
    harness.record_inventory()

    result = harness.production().produce(harness.scope, run_id="tc05")

    nav_app = next(
        entity
        for entity in result.document.entities
        if entity.node_type is NodeType.CSU and entity.name == "nav_app"
    )
    artifact = nav_app.attributes["package_artifact"]
    assert artifact["source_name"] == "artifactory-main"
    assert artifact["path"].endswith("nav_app-1.2.0.tar.gz")
    assert "artifactory-main" in result.document.provenance.sources


def test_the_document_records_its_own_provenance_and_gaps(harness):
    """Sources, exclusions, and unsupplied node types are all stated (SRS MSD.23)."""
    harness.record_inventory()

    result = harness.production().produce(harness.scope, run_id="tc05")

    provenance = result.document.provenance
    assert provenance.run_id == "tc05"
    assert provenance.produced_at == harness.clock.now()
    assert "bitbucket-a" in provenance.sources
    assert "topology-source" in provenance.sources
    assert NodeType.MESSAGE in provenance.not_supplied
    assert NodeType.TOPIC not in provenance.not_supplied


def test_production_without_an_inventory_records_why_it_produced_nothing(harness):
    """Producing with nothing recorded fails loudly rather than writing an empty file."""
    result = harness.production().produce(harness.scope, run_id="tc05")

    assert not result.succeeded
    assert result.file_path == ""
    assert result.errors[0].status is AcquisitionStatus.MISSING_DATA


# --- Extraction: the model-shaped data the mandatory-field check runs over ---


def _entities(document, node_type):
    return {entity.name for entity in document.entities if entity.node_type is node_type}


def _relations(document, relation_type):
    return {
        (relation.source_name, relation.target_name)
        for relation in document.relations
        if relation.relation_type is relation_type
    }


def test_topics_and_pubsub_relations_come_from_the_unit_descriptors(harness):
    """Declared topics become nodes with publish/consume relations."""
    harness.record_inventory()

    document = harness.production().produce(harness.scope, run_id="tc05").document

    assert _entities(document, NodeType.TOPIC) == {"NavState", "SensorReading"}
    assert ("nav_app", "NavState") in _relations(document, RelationType.PUBLISHES)
    assert ("nav_app", "SensorReading") in _relations(document, RelationType.CONSUMES)


def test_a_pubsub_role_expands_into_both_relations(harness):
    """One declaration of role 'pubsub' yields a publish and a consume."""
    harness.record_inventory()

    document = harness.production().produce(harness.scope, run_id="tc05").document

    assert ("sensor_app", "SensorReading") in _relations(document, RelationType.PUBLISHES)
    assert ("sensor_app", "SensorReading") in _relations(document, RelationType.CONSUMES)


def test_dummy_topics_are_filtered_out(harness):
    """Placeholder topics named in the rules file never reach the model."""
    harness.record_inventory()

    document = harness.production().produce(harness.scope, run_id="tc05").document

    assert "DummyTopic" not in _entities(document, NodeType.TOPIC)


def test_dependencies_come_from_java_imports(harness):
    """An import under the configured domain prefix becomes a depends_on relation."""
    harness.record_inventory()

    document = harness.production().produce(harness.scope, run_id="tc05").document

    assert ("nav_app", "helper_lib") in _relations(document, RelationType.DEPENDS_ON)
    assert ("sensor_app", "helper_lib") in _relations(document, RelationType.DEPENDS_ON)


def test_qos_comes_from_the_generated_type_support_sources(harness):
    """Topic size and QoS are read from the generated sources, not the descriptor."""
    harness.record_inventory()

    document = harness.production().produce(harness.scope, run_id="tc05").document

    nav_state = next(
        entity
        for entity in document.entities
        if entity.node_type is NodeType.TOPIC and entity.name == "NavState"
    )
    assert nav_state.attributes == {
        "size": "2048",
        "durability": "TRANSIENT_LOCAL",
        "reliability": "RELIABLE",
        "transport_priority": "HIGH",
    }


def test_placement_roles_and_criticality_come_from_the_deployment_descriptor(harness):
    """The descriptor inside a cloned repository supplies runs_on, roles, criticality."""
    harness.record_inventory()

    document = harness.production().produce(harness.scope, run_id="tc05").document

    assert _entities(document, NodeType.PROCESSOR_UNIT) == {"console-1", "console-2"}
    assert _entities(document, NodeType.ROLE) == {"publisher", "monitor"}
    assert ("nav_app", "console-1") in _relations(document, RelationType.RUNS_ON)
    assert ("nav_app", "monitor") in _relations(document, RelationType.ASSIGNED_TO_ROLE)

    nav_app = next(
        entity
        for entity in document.entities
        if entity.node_type is NodeType.CSU and entity.name == "nav_app"
    )
    assert nav_app.attributes["criticality"] == "high"


def test_a_missing_deployment_descriptor_is_reported_not_invented(harness):
    """Without the descriptor there is no placement data, and the gap is recorded."""
    descriptor = (
        harness.unit_path("bitbucket-a", "system_repo_1.0.0") / "deployment" / "system.xml"
    )
    descriptor.unlink()
    harness.record_inventory()

    result = harness.production().produce(harness.scope, run_id="tc05")

    # The topology source still reports the machines; what the descriptor alone
    # supplies — which unit runs where, and how critical it is — is gone.
    assert not _relations(result.document, RelationType.RUNS_ON)
    assert _entities(result.document, NodeType.ROLE) == set()
    assert any("deployment descriptor" in error.reason for error in result.errors)


def test_an_unparsable_deployment_descriptor_is_a_format_error(harness):
    """A malformed descriptor is reported rather than silently skipped."""
    descriptor = (
        harness.unit_path("bitbucket-a", "system_repo_1.0.0") / "deployment" / "system.xml"
    )
    descriptor.write_text("<system><unit name='nav_app'>", encoding="utf-8")
    harness.record_inventory()

    result = harness.production().produce(harness.scope, run_id="tc05")

    assert any("not well-formed XML" in error.reason for error in result.errors)
    assert not _relations(result.document, RelationType.RUNS_ON)


def test_a_generation_failure_drops_only_its_own_unit(harness):
    """A unit whose generation fails is excluded; every other unit still contributes."""
    harness.record_inventory()

    result = harness.production(generator=_FailsFor("nav_app")).produce(
        harness.scope, run_id="tc05"
    )

    assert set(result.excluded_units) == {"nav_app"}
    assert "NavState" not in _entities(result.document, NodeType.TOPIC)
    assert "SensorReading" in _entities(result.document, NodeType.TOPIC)
    assert any("generation refused" in error.reason for error in result.errors)


def test_a_missing_build_toolchain_is_reported_per_unit(harness):
    """Without the toolchain no unit generates, and each says so (CDR-31)."""
    harness.record_inventory()
    unavailable_toolchain = GmakeCodeGenerator(
        command=["saag-nonexistent-build-tool"], timeout_seconds=5
    )

    result = harness.production(generator=unavailable_toolchain).produce(
        harness.scope, run_id="tc05"
    )

    assert set(result.excluded_units) == {"system_repo", "nav_app", "sensor_app", "helper_lib"}
    assert any("toolchain not available" in error.reason for error in result.errors)
    assert _entities(result.document, NodeType.NETWORK_COMPONENT)


class _FailsFor:
    """Code generation stub that fails for one named unit and succeeds for the rest."""

    def __init__(self, unit_name: str) -> None:
        self._unit_name = unit_name

    def generate(self, unit, unit_tree) -> GenerationResult:
        """Refuse the configured unit; locate pre-generated output for the others."""
        if unit.unit_name == self._unit_name:
            return GenerationResult(
                succeeded=False, reason=f"generation refused for '{unit.versioned_name}'"
            )
        return PrebuiltCodeGenerator().generate(unit, unit_tree)
