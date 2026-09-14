"""The facade end to end with fake data sources: the run result, the saved
file and the errors recorded (SRS DSM-MDG req 5-19)."""

import json
from pathlib import Path

import pytest

import mdg
from fakes import seed
from fakes.fake_config_management_repository import FakeConfigManagementRepository
from fakes.fake_source_code_repository import FakeSourceCodeRepository
from mdg.ports.config_management_repository import ConfigManagementAccessError

FILE_NAME = "skywatch_nftw_1.0.0.json"


def _produce(tmp_path: Path, source_repo=None, config_repo=None, run_id=seed.RUN_1, **kwargs) -> dict:
    return mdg.produce_model_setup_data(
        config_repo or FakeConfigManagementRepository(),
        source_repo or FakeSourceCodeRepository(),
        seed.PROJECT, seed.PLATFORM, seed.VERSION, run_id,
        workspace=tmp_path / "ws", **kwargs,
    ).to_dict()


def _file(result: dict) -> dict:
    return json.loads(Path(result["file"]).read_text(encoding="utf-8"))


def test_result_names_the_file_the_units_the_scale_and_no_errors(tmp_path: Path):
    result = _produce(tmp_path, produced_by=seed.PRODUCER)

    assert set(result) == {"run_id", "file", "units", "scale", "candidate", "errors"}
    assert result["run_id"] == seed.RUN_1
    assert Path(result["file"]) == tmp_path / "ws" / seed.PROJECT / seed.PLATFORM / seed.VERSION / seed.RUN_1 / FILE_NAME
    assert result["units"] == [
        {"unit_name": seed.COMMON_LIB, "version": seed.VERSION, "is_candidate": False, "status": "not_acquired"},
        {"unit_name": seed.NAV_APP, "version": seed.VERSION, "is_candidate": False, "status": "ok"},
        {"unit_name": seed.SENSOR_APP, "version": seed.VERSION, "is_candidate": False, "status": "ok"},
    ]
    assert result["scale"] == {"apps": 2, "topics": 2, "nodes": 2, "libraries": 1}
    assert result["candidate"] is None
    assert result["errors"] == []


def test_saved_file_holds_the_whole_model_setup_data(tmp_path: Path):
    payload = _file(_produce(tmp_path, produced_by=seed.PRODUCER))

    assert set(payload) == {"context", "inventory", "acquired_files", "errors", "generated_at", "produced_by", "graph"}
    assert payload["context"]["version"]["label"] == seed.VERSION
    assert [u["unit_name"] for u in payload["inventory"]["units"]] == [seed.COMMON_LIB, seed.NAV_APP, seed.SENSOR_APP]
    assert [(f["unit_name"], f["file_name"]) for f in payload["acquired_files"]] == [
        (seed.NAV_APP, "Makefile"), (seed.NAV_APP, "nav_app.xml"),
        (seed.SENSOR_APP, "Makefile"), (seed.SENSOR_APP, "sensor_app.xml"),
    ]
    assert payload["errors"] == []
    assert payload["produced_by"] == seed.PRODUCER
    graph = payload["graph"]
    assert [a["name"] for a in graph["applications"]] == [seed.NAV_APP, seed.SENSOR_APP]
    assert [(l["name"], l["version"]) for l in graph["libraries"]] == [(seed.COMMON_LIB, seed.VERSION)]
    assert graph["relationships"]["uses"] == [{"from": "A0", "to": "L0"}]
    assert graph["relationships"]["runs_on"] == [{"from": "A0", "to": "N0"}, {"from": "A1", "to": "N1"}]
    assert graph["relationships"]["publishes_to"] == [{"from": "A0", "to": "T0"}, {"from": "A1", "to": "T1"}]
    assert graph["relationships"]["subscribes_to"] == [{"from": "A0", "to": "T1"}]


def test_no_producer_is_recorded_when_none_is_named(tmp_path: Path):
    assert _file(_produce(tmp_path))["produced_by"] is None


def test_candidate_version_is_cloned_and_flagged_in_the_inventory(tmp_path: Path):
    source_repo = FakeSourceCodeRepository()
    candidate = mdg.CandidateUnitVersion(seed.SENSOR_APP, seed.CANDIDATE_VERSION)

    result = _produce(tmp_path, source_repo=source_repo, candidate=candidate)

    assert (seed.SENSOR_APP, seed.CANDIDATE_VERSION) in source_repo.cloned
    assert result["candidate"] == candidate.to_dict()
    payload = _file(result)
    assert payload["inventory"]["units"][2] == {"unit_name": seed.SENSOR_APP, "version": seed.CANDIDATE_VERSION, "is_candidate": True}
    assert {a["name"]: a["version"] for a in payload["graph"]["applications"]}[seed.SENSOR_APP] == seed.CANDIDATE_VERSION


def test_clone_failure_and_missing_file_land_in_errors_and_unit_status(tmp_path: Path):
    source_repo = FakeSourceCodeRepository(fail_units=[seed.NAV_APP], without_manifest=[seed.SENSOR_APP])

    result = _produce(tmp_path, source_repo=source_repo)

    assert [(e["status"], e["source_name"], e["source_type"], e["project_platform"]) for e in result["errors"]] == [
        ("ERROR", seed.NAV_APP, "source_code_repo", "skywatch/nftw"),
        ("MISSING_DATA", seed.SENSOR_APP, "source_code_repo", "skywatch/nftw"),
    ]
    assert {u["unit_name"]: u["status"] for u in result["units"]} == {
        seed.COMMON_LIB: "not_acquired", seed.NAV_APP: "error", seed.SENSOR_APP: "missing_data",
    }
    assert _file(result)["errors"] == result["errors"]


def test_context_failures_fail_the_run(tmp_path: Path):
    with pytest.raises(mdg.DataAcquisitionError, match="db down"):
        _produce(tmp_path, config_repo=FakeConfigManagementRepository(error=ConfigManagementAccessError("db down")))

    with pytest.raises(mdg.DataAcquisitionError, match="platform_id 'unknown'"):
        mdg.produce_model_setup_data(
            FakeConfigManagementRepository(), FakeSourceCodeRepository(),
            seed.PROJECT, "unknown", seed.VERSION, seed.RUN_1, workspace=tmp_path / "ws",
        )


def test_runs_of_one_selection_get_sibling_run_dirs(tmp_path: Path):
    first = Path(_produce(tmp_path, run_id=seed.RUN_1)["file"])
    second = Path(_produce(tmp_path, run_id=seed.RUN_2)["file"])

    assert first.parent != second.parent
    assert first.parent.parent == second.parent.parent
    assert (first.parent / seed.NAV_APP / "Makefile").is_file()
    assert (second.parent / seed.NAV_APP / "Makefile").is_file()
    assert mdg.model_setup_data_store(tmp_path / "ws").list(seed.PROJECT, seed.PLATFORM, seed.VERSION)[0].run_id in (seed.RUN_1, seed.RUN_2)


def test_progress_reports_the_percent_and_phase_after_each_work_unit(tmp_path: Path):
    reports = []

    _produce(tmp_path, progress=lambda percent, phase: reports.append((percent, phase)))

    assert reports == [(16, "system"), (33, "clone"), (50, "clone"), (66, "parse"), (83, "parse"), (100, "finalize")]
