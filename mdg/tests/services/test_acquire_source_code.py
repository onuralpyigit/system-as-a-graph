"""Acquiring one software unit: file records, missing mandatory files and
repository failures (SRS DSM-MDG req 13-16)."""

from pathlib import Path

from fakes import seed
from fakes.fake_source_code_repository import FakeSourceCodeRepository
from mdg.domain.error_record import ErrorStatus
from mdg.domain.inventory import SoftwareUnitVersion
from mdg.domain.model_setup_data import UnitStatus
from mdg.ports.source_code_repository import SourceRepoAuthError
from mdg.services.acquire_source_code import AcquireSourceCode

NAV_APP = SoftwareUnitVersion(seed.NAV_APP, seed.VERSION)


def test_cloned_unit_records_its_mandatory_files(tmp_path: Path):
    acquisition = AcquireSourceCode(FakeSourceCodeRepository()).execute(NAV_APP, tmp_path, seed.CONTEXT)

    assert acquisition.unit_dir == tmp_path / seed.NAV_APP
    assert [(f.file_name, f.package_version) for f in acquisition.files] == [("Makefile", seed.VERSION), ("nav_app.xml", seed.VERSION)]
    assert acquisition.errors == []
    assert acquisition.status is UnitStatus.OK


def test_missing_mandatory_file_is_recorded_as_missing_data(tmp_path: Path):
    repo = FakeSourceCodeRepository(without_manifest=[seed.NAV_APP])

    acquisition = AcquireSourceCode(repo).execute(NAV_APP, tmp_path, seed.CONTEXT)

    assert [f.file_name for f in acquisition.files] == ["Makefile"]
    assert [(e.status, e.source_name, e.source_type) for e in acquisition.errors] == [
        (ErrorStatus.MISSING_DATA, seed.NAV_APP, "source_code_repo"),
    ]
    assert "nav_app.xml" in acquisition.errors[0].reason
    assert acquisition.errors[0].project_platform == "skywatch/nftw"
    assert acquisition.status is UnitStatus.MISSING_DATA


def test_a_repository_that_is_not_a_unit_is_cloned_without_the_file_rule(tmp_path: Path):
    system_repo = SoftwareUnitVersion(seed.SYSTEM_REPO, seed.VERSION)

    acquisition = AcquireSourceCode(FakeSourceCodeRepository()).execute(system_repo, tmp_path, seed.CONTEXT, mandatory=False)

    assert acquisition.unit_dir == tmp_path / seed.SYSTEM_REPO
    assert (acquisition.files, acquisition.errors) == ([], [])
    assert acquisition.status is UnitStatus.OK

    failed = AcquireSourceCode(FakeSourceCodeRepository(fail_units=[seed.SYSTEM_REPO])).execute(
        system_repo, tmp_path, seed.CONTEXT, mandatory=False
    )
    assert failed.unit_dir is None
    assert failed.errors[0].status is ErrorStatus.ERROR


def test_repository_failure_is_recorded_as_an_error(tmp_path: Path):
    repo = FakeSourceCodeRepository(error=SourceRepoAuthError("authentication failed"))

    acquisition = AcquireSourceCode(repo).execute(NAV_APP, tmp_path, seed.CONTEXT)

    assert acquisition.unit_dir is None
    assert acquisition.files == []
    assert acquisition.errors[0].status is ErrorStatus.ERROR
    assert "authentication failed" in acquisition.errors[0].reason
    assert acquisition.status is UnitStatus.ERROR
