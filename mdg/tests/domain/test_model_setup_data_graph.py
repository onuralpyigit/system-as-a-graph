"""The node-relationship graph and the QoS-derived topic attributes
(SRS DSM-MDG req 19; DSM-SMM req 6-7)."""

from fakes import seed
from mdg.domain.inventory import SoftwareUnitVersionInventory
from mdg.domain.model_setup_data_graph import ModelSetupDataGraph
from mdg.domain.source_data import RelationKind, Topic, UnitRelation

APP_NODES = [(seed.NAV_APP, seed.NODE_0), (seed.SENSOR_APP, seed.NODE_1)]
RELATIONS = [
    UnitRelation(seed.NAV_APP, seed.NAV_POSITION, RelationKind.PUBLISHES),
    UnitRelation(seed.NAV_APP, seed.SENSOR_DATA, RelationKind.SUBSCRIBES),
    UnitRelation(seed.NAV_APP, seed.COMMON_LIB, RelationKind.USES),
    UnitRelation(seed.SENSOR_APP, seed.SENSOR_DATA, RelationKind.PUBLISHES),
]
TOPICS = [
    Topic(seed.NAV_POSITION, 6138, "PERSISTENT", "BEST_EFFORT", "LOW"),
    Topic(seed.SENSOR_DATA, 1207, "TRANSIENT", "BEST_EFFORT", "MEDIUM"),
]


def _graph(app_roles=None, app_criticality=None):
    inventory = SoftwareUnitVersionInventory(seed.CONTEXT, seed.inventory_rows()).without(seed.SYSTEM_REPO)
    return ModelSetupDataGraph.build(APP_NODES, app_roles or {}, app_criticality or {}, RELATIONS, TOPICS, inventory, {})


def test_entities_get_sorted_ids_and_inventory_versions():
    graph = _graph()

    assert graph["nodes"] == [{"id": "N0", "name": seed.NODE_0}, {"id": "N1", "name": seed.NODE_1}]
    assert [(a["id"], a["name"], a["version"]) for a in graph["applications"]] == [
        ("A0", seed.NAV_APP, seed.VERSION), ("A1", seed.SENSOR_APP, seed.VERSION),
    ]
    assert [(l["id"], l["name"], l["version"]) for l in graph["libraries"]] == [("L0", seed.COMMON_LIB, seed.VERSION)]
    assert [(t["id"], t["name"], t["size"]) for t in graph["topics"]] == [("T0", seed.NAV_POSITION, 6138), ("T1", seed.SENSOR_DATA, 1207)]
    assert graph["metadata"]["scale"] == {"apps": 2, "topics": 2, "nodes": 2, "libraries": 1}


def test_relationships_join_by_entity_id():
    relationships = _graph()["relationships"]

    assert relationships["runs_on"] == [{"from": "A0", "to": "N0"}, {"from": "A1", "to": "N1"}]
    assert relationships["publishes_to"] == [{"from": "A0", "to": "T0"}, {"from": "A1", "to": "T1"}]
    assert relationships["subscribes_to"] == [{"from": "A0", "to": "T1"}]
    assert relationships["uses"] == [{"from": "A0", "to": "L0"}]


def test_application_roles_default_to_not_found_and_are_copied():
    roles = {seed.NAV_APP: ["publisher", "subscriber"]}

    apps = {a["name"]: a for a in _graph(app_roles=roles)["applications"]}

    assert apps[seed.NAV_APP]["role"] == ["publisher", "subscriber"]
    assert apps[seed.SENSOR_APP]["role"] == ["NOT_FOUND"]
    assert apps[seed.NAV_APP]["role"] is not roles[seed.NAV_APP]
    assert apps[seed.NAV_APP]["system_hierarchy"]["csc_name"] == "NOT_FOUND"


def test_application_priority_and_hotstandby_are_reproducible_by_name():
    first = {a["name"]: (a["priority"], a["hotstandby"]) for a in _graph()["applications"]}
    second = {a["name"]: (a["priority"], a["hotstandby"]) for a in _graph()["applications"]}

    assert first == second
    assert all(priority in ("LOW", "MEDIUM", "HIGH") for priority, _ in first.values())


def test_topic_frequency_and_criticality_bins():
    assert Topic("t", reliability="RELIABLE", transport_priority="URGENT").frequency() == 200.0
    assert Topic("t", reliability="RELIABLE", transport_priority="HIGH").frequency() == 100.0
    assert Topic("t", reliability="BEST_EFFORT", transport_priority="URGENT").frequency() == 1.0
    assert Topic("t").frequency() == 1.0
    assert Topic("t", durability="VOLATILE", reliability="BEST_EFFORT", transport_priority="LOW").criticality() == "minimal"
    assert Topic("t", durability="PERSISTENT", reliability="BEST_EFFORT", transport_priority="LOW").criticality() == "medium"
    assert Topic("t", durability="PERSISTENT", reliability="BEST_EFFORT", transport_priority="HIGH").criticality() == "high"
    assert Topic("t", durability="PERSISTENT", reliability="RELIABLE", transport_priority="URGENT").criticality() == "critical"
    assert Topic("t").criticality() == "minimal"


def test_topic_qos_defaults_to_not_found_in_the_graph():
    topics = _graph()["topics"]

    assert topics[0]["qos"] == {"durability": "PERSISTENT", "reliability": "BEST_EFFORT", "transport_priority": "LOW"}
    assert topics[0]["frequency"] == 1.0
    assert topics[0]["criticality"] == "medium"
    assert Topic(seed.NAV_POSITION) == Topic(seed.NAV_POSITION, size=1)
