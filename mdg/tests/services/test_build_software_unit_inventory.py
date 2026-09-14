"""Building the Software Unit Version Inventory of a selection (SRS DSM-MDG req 10-11)."""

from fakes import seed
from fakes.fake_config_management_repository import FakeConfigManagementRepository
from mdg.domain.inventory import CandidateUnitVersion
from mdg.services.build_software_unit_inventory import BuildSoftwareUnitInventory


def test_inventory_is_the_selected_versions_rows():
    inventory = BuildSoftwareUnitInventory(FakeConfigManagementRepository()).execute(seed.CONTEXT)

    assert inventory.context is seed.CONTEXT
    assert inventory.units == seed.inventory_rows()


def test_candidate_is_applied_to_the_inventory():
    candidate = CandidateUnitVersion(seed.SENSOR_APP, seed.CANDIDATE_VERSION)

    inventory = BuildSoftwareUnitInventory(FakeConfigManagementRepository()).execute(seed.CONTEXT, candidate)

    assert inventory.find(seed.SENSOR_APP).version == seed.CANDIDATE_VERSION
    assert inventory.find(seed.SENSOR_APP).is_candidate is True
    assert inventory.find(seed.NAV_APP).version == seed.VERSION
