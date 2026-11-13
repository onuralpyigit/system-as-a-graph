"""The mock ansible repo parser over a cloned ansible repo (SRS DSM-MDG req 2.4, 3)."""

from fakes import seed
from mdg.adapters.source_data.ansible_repo_parser import AnsibleRepoParser
from mdg.domain.source_data import RelationKind


def _parser(tmp_path) -> AnsibleRepoParser:
    return AnsibleRepoParser(tmp_path / seed.ANSIBLE_REPO, seed.PROJECT, seed.PLATFORM)


def test_nodes_enrich_the_seeded_processor_units(tmp_path):
    parser = _parser(tmp_path)

    nodes = parser.get_nodes()
    assert all(node.name and node.group and node.hw and node.os and node.mw and node.gpu and node.display for node in nodes)
    assert {node.name for node in parser.get_nodes()} >= {seed.NODE_0, seed.NODE_1}


def test_networks_are_named(tmp_path):
    networks = _parser(tmp_path).get_networks()

    assert networks and all(n.name for n in networks)


def test_connects_are_typed_and_reference_the_seeded_entities(tmp_path):
    parser = _parser(tmp_path)

    connects = parser.get_connects_to()
    node_names = {n.name for n in parser.get_nodes()}
    network_names = {n.name for n in parser.get_networks()}
    assert connects and all(c.kind is RelationKind.CONNECTS_TO and c.device and c.dev_raw for c in connects)
    assert all(c.bandwidth and c.bandwidth > 0 for c in connects)
    assert all(c.from_name in node_names and c.to_name in network_names for c in connects)
