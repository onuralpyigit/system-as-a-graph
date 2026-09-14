"""The run order of the production process with recording fakes: system repo
first, only the placed units, build before parse, type support last
(SRS DSM-MDG req 3, 10-13, 19)."""

from pathlib import Path

import pytest

from fakes import seed
from fakes.fake_config_management_repository import FakeConfigManagementRepository
from fakes.fake_parsers import Calls, FakeBuildRunner, FakeSourceCodeParser, system_repo_parser_class, type_support_parser_class
from fakes.fake_source_code_repository import FakeSourceCodeRepository
from mdg import MANDATORY_FIELD_RULES
from mdg.adapters.model_setup_data.filesystem_model_setup_data_store import FilesystemModelSetupDataStore
from mdg.domain.error_record import DataAcquisitionError, ErrorStatus
from mdg.domain.inventory import SoftwareUnitVersion
from mdg.domain.workspace import Workspace
from mdg.services.acquire_project_context import AcquireProjectContext
from mdg.services.acquire_source_code import AcquireSourceCode
from mdg.services.build_software_unit_inventory import BuildSoftwareUnitInventory
from mdg.services.check_mandatory_fields import CheckMandatoryFields
from mdg.services.produce_model_setup_data import ProduceModelSetupData


class Run:
    """One production wired with fakes over a workspace under tmp_path."""

    def __init__(self, tmp_path: Path, source_repo=None, config_repo=None, app_nodes=None, run_regenerate_code=False, system_repo_name=seed.SYSTEM_REPO):
        self.calls = Calls()
        self.source_repo = source_repo or FakeSourceCodeRepository()
        self.parser_class = system_repo_parser_class(self.calls, app_nodes)
        config_repo = config_repo or FakeConfigManagementRepository()
        workspace = Workspace(tmp_path / "ws")
        self.production = ProduceModelSetupData(
            config_repo=config_repo,
            acquire_context=AcquireProjectContext(config_repo),
            build_inventory=BuildSoftwareUnitInventory(config_repo),
            acquire_source_code=AcquireSourceCode(self.source_repo),
            system_repo_parser=self.parser_class,
            source_code_parser=FakeSourceCodeParser(self.calls),
            type_support_parser=type_support_parser_class(self.calls),
            build_runner=FakeBuildRunner(self.calls),
            check_mandatory_fields=CheckMandatoryFields(MANDATORY_FIELD_RULES),
            store=FilesystemModelSetupDataStore(workspace),
            workspace=workspace,
            system_repo_name=system_repo_name,
            run_regenerate_code=run_regenerate_code,
        )
        self.run_dir = workspace.run_dir(seed.PROJECT, seed.PLATFORM, seed.VERSION, seed.RUN_1)

    def execute(self, **kwargs):
        return self.production.execute(seed.PROJECT, seed.PLATFORM, seed.VERSION, seed.RUN_1, **kwargs)


def test_system_repo_is_cloned_first_and_the_parser_is_constructed_on_it(tmp_path: Path):
    run = Run(tmp_path)

    run.execute()

    assert run.source_repo.cloned[0] == (seed.SYSTEM_REPO, seed.VERSION)
    parser = run.parser_class.instances[0]
    assert parser.system_repo_dir == run.run_dir / seed.SYSTEM_REPO
    assert (parser.project_name, parser.platform_name) == (seed.PROJECT, seed.PLATFORM)
    assert run.calls.steps()[0] == "system_repo_parser"


def test_only_the_applications_the_system_repo_places_are_cloned(tmp_path: Path):
    run = Run(tmp_path)

    result = run.execute()

    assert run.source_repo.cloned == [(seed.SYSTEM_REPO, seed.VERSION), (seed.NAV_APP, seed.VERSION), (seed.SENSOR_APP, seed.VERSION)]
    assert {u.unit_name: s.value for u, s in result.units} == {seed.COMMON_LIB: "not_acquired", seed.NAV_APP: "ok", seed.SENSOR_APP: "ok"}
    assert seed.SYSTEM_REPO not in {u.unit_name for u, _ in result.units}
    assert result.errors == []


def test_build_runs_before_each_parse_and_type_support_runs_last_over_the_run_dir(tmp_path: Path):
    run = Run(tmp_path, run_regenerate_code=True)

    run.execute()

    assert run.calls.log == [
        ("ensure_available", ""),
        ("system_repo_parser", str(run.run_dir / seed.SYSTEM_REPO)),
        ("regenerate_code", seed.NAV_APP), ("parse", seed.NAV_APP),
        ("regenerate_code", seed.SENSOR_APP), ("parse", seed.SENSOR_APP),
        ("type_support", str(run.run_dir)),
    ]


def test_an_application_missing_from_the_inventory_is_recorded_and_skipped(tmp_path: Path):
    run = Run(tmp_path, app_nodes=[(seed.NAV_APP, seed.NODE_0), ("weather_app", seed.NODE_1)])

    result = run.execute()

    assert run.source_repo.cloned == [(seed.SYSTEM_REPO, seed.VERSION), (seed.NAV_APP, seed.VERSION)]
    assert [(e.status, e.source_name, e.source_type) for e in result.errors] == [
        (ErrorStatus.MISSING_DATA, "weather_app", "config_mgmt_db"),
    ]


def test_system_repo_missing_from_the_inventory_fails_the_run(tmp_path: Path):
    config_repo = FakeConfigManagementRepository(unit_versions={seed.VERSION: [SoftwareUnitVersion(seed.NAV_APP, seed.VERSION)]})

    with pytest.raises(DataAcquisitionError) as failure:
        Run(tmp_path, config_repo=config_repo).execute()

    assert failure.value.record.status is ErrorStatus.MISSING_DATA
    assert seed.SYSTEM_REPO in failure.value.record.reason


def test_system_repo_clone_failure_fails_the_run(tmp_path: Path):
    run = Run(tmp_path, source_repo=FakeSourceCodeRepository(fail_units=[seed.SYSTEM_REPO]))

    with pytest.raises(DataAcquisitionError) as failure:
        run.execute()

    assert failure.value.record.status is ErrorStatus.ERROR
    assert run.parser_class.instances == []


def test_progress_counts_system_clone_parse_and_finalize(tmp_path: Path):
    reports = []

    Run(tmp_path).execute(progress=lambda percent, phase: reports.append((percent, phase)))

    assert reports == [(16, "system"), (33, "clone"), (50, "clone"), (66, "parse"), (83, "parse"), (100, "finalize")]


def test_progress_of_a_single_unit_moves_in_quarters(tmp_path: Path):
    reports = []

    Run(tmp_path, app_nodes=[(seed.NAV_APP, seed.NODE_0)]).execute(progress=lambda p, phase: reports.append((p, phase)))

    assert reports == [(25, "system"), (50, "clone"), (75, "parse"), (100, "finalize")]
