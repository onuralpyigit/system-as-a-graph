"""The node-relationship graph and the QoS-derived topic attributes
(SRS DSM-MDG req 2.4, 19; DSM-SMM req 6-7)."""

from fakes import seed
from mdg.domain.inventory import SoftwareUnitVersionInventory
from mdg.domain.model_setup_data_graph import NOT_FOUND, ModelSetupDataGraph
from mdg.domain.source_data import ConnectsTo, Message, Network, Node, RelationKind, Topic, UnitRelation

APP_NODES = [(seed.NAV_APP, seed.NODE_0), (seed.SENSOR_APP, seed.NODE_1)]
RELATIONS = [
    UnitRelation(seed.NAV_APP, seed.NAV_POSITION, RelationKind.PUBLISHES),
    UnitRelation(seed.NAV_APP, seed.SENSOR_DATA, RelationKind.SUBSCRIBES),
    UnitRelation(seed.NAV_APP, seed.COMMON_LIB, RelationKind.USES),
    UnitRelation(seed.SENSOR_APP, seed.SENSOR_DATA, RelationKind.PUBLISHES),
    UnitRelation(seed.NAV_APP, seed.MSG_NAV_POSITION, RelationKind.SEND),
    UnitRelation(seed.SENSOR_APP, seed.MSG_NAV_POSITION, RelationKind.RECEIVE),
]
NODE_ATTRS = [
    Node(seed.NODE_0, group="processors", hw="x86-64/8c", os="Linux 5.15", mw="DDS", gpu="none", display="none"),
]
NETWORKS = [Network(seed.SWITCH_0), Network(seed.SWITCH_1)]
CONNECTS = [
    ConnectsTo(seed.NODE_0, seed.SWITCH_0, device="eth0", dev_raw="ens1f0", bandwidth=1.0),
    ConnectsTo(seed.NODE_1, seed.SWITCH_1, device="eth0", dev_raw="ens1f0", bandwidth=0.1),
    ConnectsTo(seed.NODE_0, seed.GHOST_SWITCH, device="eth1", dev_raw="ens1f1", bandwidth=0.1),
]
TOPICS = [
    Topic(seed.NAV_POSITION, 6138, "PERSISTENT", "BEST_EFFORT", "LOW"),
    Topic(seed.SENSOR_DATA, 1207, "TRANSIENT", "BEST_EFFORT", "MEDIUM"),
]
MESSAGES = [
    Message("MSG-001", seed.MSG_NAV_POSITION, 6138, 20.0),
    Message("MSG-002", seed.MSG_SENSOR_DATA, 1207, 100.0),
]


def _graph(app_roles=None, app_criticality=None, nodes=NODE_ATTRS, networks=NETWORKS, connects=CONNECTS):
    inventory = SoftwareUnitVersionInventory(seed.CONTEXT, seed.inventory_rows()).without(seed.SYSTEM_REPO).without(seed.ANSIBLE_REPO)
    return ModelSetupDataGraph.build(
        APP_NODES, app_roles or {}, app_criticality or {}, [*RELATIONS, *connects], TOPICS, MESSAGES, inventory, {},
        nodes, networks,
    )


def test_entities_get_sorted_ids_and_inventory_versions():
    graph = _graph()

    assert graph["nodes"] == [
        {"id": "N0", "name": seed.NODE_0, "group": "processors", "hw": "x86-64/8c", "os": "Linux 5.15", "mw": "DDS", "gpu": "none", "display": "none"},
        {"id": "N1", "name": seed.NODE_1, "group": "NOT_FOUND", "hw": "NOT_FOUND", "os": "NOT_FOUND", "mw": "NOT_FOUND", "gpu": "NOT_FOUND", "display": "NOT_FOUND"},
    ]
    assert [(w["id"], w["name"]) for w in graph["networks"]] == [("W0", seed.SWITCH_0), ("W1", seed.SWITCH_1)]
    assert [(a["id"], a["name"], a["version"]) for a in graph["applications"]] == [
        ("A0", seed.NAV_APP, seed.VERSION), ("A1", seed.SENSOR_APP, seed.VERSION),
    ]
    assert [(l["id"], l["name"], l["version"]) for l in graph["libraries"]] == [("L0", seed.COMMON_LIB, seed.VERSION)]
    assert [(t["id"], t["name"], t["size"]) for t in graph["topics"]] == [("T0", seed.NAV_POSITION, 6138), ("T1", seed.SENSOR_DATA, 1207)]
    assert [(m["id"], m["message_id"], m["name"], m["size"], m["frequency"]) for m in graph["messages"]] == [
        ("M0", "MSG-001", seed.MSG_NAV_POSITION, 6138, 20.0),
        ("M1", "MSG-002", seed.MSG_SENSOR_DATA, 1207, 100.0),
    ]
    assert graph["metadata"]["scale"] == {"apps": 2, "topics": 2, "messages": 2, "nodes": 2, "libraries": 1, "networks": 2}


def test_a_network_carries_only_its_id_and_name():
    graph = _graph(networks=[Network(seed.SWITCH_0)])

    assert graph["networks"] == [{"id": "W0", "name": seed.SWITCH_0}]


def test_a_connect_without_a_bandwidth_is_minus_one():
    graph = _graph(connects=[ConnectsTo(seed.NODE_0, seed.SWITCH_0, device="eth0", dev_raw="ens1f0")])

    assert graph["relationships"]["connects_to"] == [
        {"from": "N0", "to": "W0", "device": "eth0", "dev_raw": "ens1f0", "bandwidth": -1},
    ]


def test_connects_to_join_node_and_network_ids_by_name_and_drop_unresolvable():
    relationships = _graph()["relationships"]

    assert relationships["connects_to"] == [
        {"from": "N0", "to": "W0", "device": "eth0", "dev_raw": "ens1f0", "bandwidth": 1.0},
        {"from": "N1", "to": "W1", "device": "eth0", "dev_raw": "ens1f0", "bandwidth": 0.1},
    ]


def test_connects_to_is_a_node_on_a_network_only():
    graph = _graph(connects=[
        ConnectsTo(seed.SWITCH_0, seed.SWITCH_1, device="uplink", dev_raw="xe-0/0/0", bandwidth=1.0),
        ConnectsTo(seed.SWITCH_0, seed.NODE_0, device="eth0", dev_raw="ens1f0", bandwidth=1.0),
        ConnectsTo(seed.NODE_1, seed.SWITCH_0, device="eth0", dev_raw="ens1f0", bandwidth=1.0),
    ])

    assert graph["relationships"]["connects_to"] == [
        {"from": "N1", "to": "W0", "device": "eth0", "dev_raw": "ens1f0", "bandwidth": 1.0}
    ]


def test_connects_device_fields_default_to_not_found():
    graph = _graph(connects=[ConnectsTo(seed.NODE_0, seed.SWITCH_0)])

    assert graph["relationships"]["connects_to"] == [
        {"from": "N0", "to": "W0", "device": "NOT_FOUND", "dev_raw": "NOT_FOUND", "bandwidth": -1}
    ]


def test_without_ansible_data_nodes_are_not_found_and_network_lists_empty():
    graph = _graph(nodes=[], networks=[], connects=[])

    assert graph["networks"] == []
    assert graph["relationships"]["connects_to"] == []
    assert all(graph["nodes"][1][key] == "NOT_FOUND" for key in ("group", "hw", "os", "mw", "gpu", "display"))


def test_ansible_nodes_merge_with_the_system_repo_nodes():
    graph = _graph(nodes=[*NODE_ATTRS, Node("Node-2", group="processors", hw="x86-64/16c")])

    assert [(n["id"], n["name"], n["group"], n["hw"]) for n in graph["nodes"]] == [
        ("N0", seed.NODE_0, "processors", "x86-64/8c"),
        ("N1", seed.NODE_1, "NOT_FOUND", "NOT_FOUND"),
        ("N2", "Node-2", "processors", "x86-64/16c"),
    ]
    assert graph["metadata"]["scale"]["nodes"] == 3
    assert graph["relationships"]["runs_on"] == [{"from": "A0", "to": "N0"}, {"from": "A1", "to": "N1"}]


def test_connects_to_from_an_ansible_only_node_resolves():
    graph = _graph(
        nodes=[*NODE_ATTRS, Node("Node-2", group="processors")],
        connects=[ConnectsTo("Node-2", seed.SWITCH_0, device="eth0", dev_raw="ens1f0", bandwidth=1.0)],
    )

    assert graph["relationships"]["connects_to"] == [
        {"from": "N2", "to": "W0", "device": "eth0", "dev_raw": "ens1f0", "bandwidth": 1.0}
    ]


def test_ansible_nodes_without_a_name_are_ignored():
    graph = _graph(nodes=[*NODE_ATTRS, Node(""), Node(NOT_FOUND, group="processors")])

    assert [n["name"] for n in graph["nodes"]] == [seed.NODE_0, seed.NODE_1]


def test_relationships_join_by_entity_id():
    relationships = _graph()["relationships"]

    assert relationships["runs_on"] == [{"from": "A0", "to": "N0"}, {"from": "A1", "to": "N1"}]
    assert relationships["publishes_to"] == [{"from": "A0", "to": "T0"}, {"from": "A1", "to": "T1"}]
    assert relationships["subscribes_to"] == [{"from": "A0", "to": "T1"}]
    assert relationships["sends"] == [{"from": "A0", "to": "M0"}]
    assert relationships["receives"] == [{"from": "A1", "to": "M0"}]
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
