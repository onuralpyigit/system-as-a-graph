"""The mock system repo parser over a cloned system repo (SRS DSM-MDG req 3)."""

from fakes import seed
from mdg.adapters.source_data.system_repo_parser import SystemRepoParser


def _parser(tmp_path) -> SystemRepoParser:
    return SystemRepoParser(tmp_path / seed.SYSTEM_REPO, seed.PROJECT, seed.PLATFORM)


def test_applications_run_on_the_seeded_processor_units(tmp_path):
    assert _parser(tmp_path).get_app_node_relation() == [(seed.NAV_APP, seed.NODE_0), (seed.SENSOR_APP, seed.NODE_1)]


def test_every_placed_application_has_roles(tmp_path):
    parser = _parser(tmp_path)

    roles = parser.get_app_role_relation()
    for app, _ in parser.get_app_node_relation():
        assert roles[app] and all(isinstance(role, str) for role in roles[app])


def test_criticality_is_a_mapping_of_application_to_bool(tmp_path):
    assert all(isinstance(v, bool) for v in _parser(tmp_path).get_app_criticality_relation().values())
