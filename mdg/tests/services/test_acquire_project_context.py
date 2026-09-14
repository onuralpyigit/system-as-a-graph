"""Acquiring the project context and marking its failures (SRS DSM-MDG req 5-9, 12)."""

import pytest

from fakes import seed
from fakes.fake_config_management_repository import FakeConfigManagementRepository
from mdg.domain.error_record import DataAcquisitionError, ErrorStatus
from mdg.ports.config_management_repository import ConfigManagementAccessError
from mdg.services.acquire_project_context import AcquireProjectContext


def test_selected_ids_resolve_to_their_records_with_the_effective_version_marked():
    context = AcquireProjectContext(FakeConfigManagementRepository()).execute(seed.PROJECT, seed.PLATFORM, seed.VERSION)

    assert context == seed.CONTEXT
    assert context.version.is_effective is True
    assert context.project_platform == "skywatch/nftw"


@pytest.mark.parametrize("ids, missing", [
    (("unknown", seed.PLATFORM, seed.VERSION), "project_id 'unknown'"),
    ((seed.PROJECT, "unknown", seed.VERSION), "platform_id 'unknown'"),
    ((seed.PROJECT, seed.PLATFORM, "2.0.0"), "version_id '2.0.0'"),
])
def test_unknown_id_is_missing_data(ids, missing):
    with pytest.raises(DataAcquisitionError) as failure:
        AcquireProjectContext(FakeConfigManagementRepository()).execute(*ids)

    assert failure.value.record.status is ErrorStatus.MISSING_DATA
    assert missing in failure.value.record.reason
    assert failure.value.record.source_type == "config_mgmt_db"


def test_database_failure_is_an_error():
    repo = FakeConfigManagementRepository(error=ConfigManagementAccessError("db unreachable"))

    with pytest.raises(DataAcquisitionError) as failure:
        AcquireProjectContext(repo).execute(seed.PROJECT, seed.PLATFORM, seed.VERSION)

    assert failure.value.record.status is ErrorStatus.ERROR
    assert "db unreachable" in failure.value.record.reason
    assert failure.value.record.project_platform == "skywatch/nftw"
