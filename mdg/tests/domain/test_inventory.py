"""The Software Unit Version Inventory and the candidate versions (SRS DSM-MDG req 10-11)."""

from fakes import seed
from mdg.domain.inventory import CandidateUnitVersion, SoftwareUnitVersionInventory


def _inventory() -> SoftwareUnitVersionInventory:
    return SoftwareUnitVersionInventory(seed.CONTEXT, seed.inventory_rows())


def test_candidate_replaces_that_units_version_and_keeps_the_others():
    inventory = _inventory().with_candidate(CandidateUnitVersion(seed.SENSOR_APP, seed.CANDIDATE_VERSION))

    by_name = {u.unit_name: u for u in inventory.units}
    assert by_name[seed.SENSOR_APP].version == seed.CANDIDATE_VERSION
    assert by_name[seed.SENSOR_APP].is_candidate is True
    assert by_name[seed.NAV_APP].version == seed.VERSION
    assert by_name[seed.NAV_APP].is_candidate is False


def test_candidate_keeps_the_inventory_order():
    inventory = _inventory().with_candidate(CandidateUnitVersion(seed.SENSOR_APP, seed.CANDIDATE_VERSION))

    assert [u.unit_name for u in inventory.units] == [u.unit_name for u in seed.inventory_rows()]


def test_candidate_of_a_unit_the_system_version_does_not_define_is_appended():
    inventory = _inventory().with_candidate(CandidateUnitVersion("weather_app", "0.1.0"))

    assert inventory.units[-1].unit_name == "weather_app"
    assert inventory.units[-1].is_candidate is True


def test_candidates_are_applied_together_and_keep_the_order():
    inventory = _inventory().with_candidates([
        CandidateUnitVersion(seed.SENSOR_APP, seed.CANDIDATE_VERSION),
        CandidateUnitVersion(seed.NAV_APP, "2.0.0"),
        CandidateUnitVersion("weather_app", "0.1.0"),
    ])

    by_name = {u.unit_name: u for u in inventory.units}
    assert (by_name[seed.SENSOR_APP].version, by_name[seed.SENSOR_APP].is_candidate) == (seed.CANDIDATE_VERSION, True)
    assert (by_name[seed.NAV_APP].version, by_name[seed.NAV_APP].is_candidate) == ("2.0.0", True)
    assert by_name[seed.COMMON_LIB].is_candidate is False
    assert [u.unit_name for u in inventory.units] == [u.unit_name for u in seed.inventory_rows()] + ["weather_app"]


def test_no_candidates_leave_the_inventory_as_it_is():
    assert _inventory().with_candidates([]) == _inventory()


def test_find_and_without():
    inventory = _inventory()

    assert inventory.find(seed.SYSTEM_REPO).version == seed.VERSION
    assert inventory.find("weather_app") is None
    assert seed.SYSTEM_REPO not in [u.unit_name for u in inventory.without(seed.SYSTEM_REPO).units]


def test_candidate_from_dict_accepts_only_a_complete_payload():
    assert CandidateUnitVersion.from_dict({"unit_name": seed.NAV_APP, "version": seed.CANDIDATE_VERSION}) == (
        CandidateUnitVersion(seed.NAV_APP, seed.CANDIDATE_VERSION)
    )
    assert CandidateUnitVersion.from_dict({"unit_name": seed.NAV_APP}) is None
    assert CandidateUnitVersion.from_dict(None) is None


def test_candidates_list_from_keeps_only_complete_entries():
    payload = [{"unit_name": seed.NAV_APP, "version": "2.0.0"}, {"unit_name": seed.SENSOR_APP}, "x", None]

    assert CandidateUnitVersion.list_from(payload) == [CandidateUnitVersion(seed.NAV_APP, "2.0.0")]
    assert CandidateUnitVersion.list_from(None) == []
    assert CandidateUnitVersion.list_from({"unit_name": seed.NAV_APP, "version": "2.0.0"}) == []
