"""The filesystem store: saving a run's file, listing a selection's files and
resolving one (SRS DSM-MDG req 19; DSM-DVE req 5)."""

import json
from pathlib import Path

from fakes import seed
from mdg.adapters.model_setup_data.filesystem_model_setup_data_store import FilesystemModelSetupDataStore
from mdg.domain.inventory import SoftwareUnitVersionInventory
from mdg.domain.model_setup_data import ModelSetupData
from mdg.domain.workspace import Workspace

FILE_NAME = "skywatch_nftw_1.0.0.json"


def _store(tmp_path: Path) -> FilesystemModelSetupDataStore:
    return FilesystemModelSetupDataStore(Workspace(tmp_path))


def _write(tmp_path: Path, run_id: str, generated_at, produced_by=None, units=None, version=seed.VERSION) -> Path:
    run_dir = tmp_path / seed.PROJECT / seed.PLATFORM / version / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    path = run_dir / f"skywatch_nftw_{version}.json"
    payload = {
        "generated_at": generated_at, "produced_by": produced_by,
        "inventory": {"units": units or []}, "graph": {"metadata": {"scale": {"apps": 2}}},
    }
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def test_save_writes_the_selection_named_file_in_the_run_dir(tmp_path: Path):
    data = ModelSetupData(seed.CONTEXT, SoftwareUnitVersionInventory(seed.CONTEXT), [], [], {}, produced_by=seed.PRODUCER)

    path = _store(tmp_path).save(data, seed.RUN_1)

    assert path == tmp_path / seed.PROJECT / seed.PLATFORM / seed.VERSION / seed.RUN_1 / FILE_NAME
    assert json.loads(path.read_text(encoding="utf-8")) == data.to_dict()


def test_list_is_newest_first_with_producer_and_candidate(tmp_path: Path):
    _write(tmp_path, seed.RUN_1, "2026-09-01T09:02:00", produced_by="admin")
    _write(tmp_path, seed.RUN_2, "2026-09-02T14:15:30", produced_by=seed.PRODUCER, units=[
        {"unit_name": seed.SENSOR_APP, "version": seed.CANDIDATE_VERSION, "is_candidate": True},
    ])

    records = _store(tmp_path).list(seed.PROJECT, seed.PLATFORM, seed.VERSION)

    assert [r.run_id for r in records] == [seed.RUN_2, seed.RUN_1]
    assert records[0].produced_by == seed.PRODUCER
    assert records[0].candidate == {"unit_name": seed.SENSOR_APP, "version": seed.CANDIDATE_VERSION}
    assert records[1].candidate is None
    assert records[0].scale == {"apps": 2}


def test_list_covers_only_the_selection_and_skips_bad_run_dirs(tmp_path: Path):
    _write(tmp_path, seed.RUN_1, "2026-09-02T14:15:30")
    _write(tmp_path, seed.RUN_2, "2026-09-03T14:15:30", version=seed.OLD_VERSION)
    broken = tmp_path / seed.PROJECT / seed.PLATFORM / seed.VERSION / "run-broken"
    broken.mkdir()
    (broken / FILE_NAME).write_text("{not json", encoding="utf-8")
    (tmp_path / seed.PROJECT / seed.PLATFORM / seed.VERSION / "run-empty").mkdir()
    _write(tmp_path, "run-undated", None)

    records = _store(tmp_path).list(seed.PROJECT, seed.PLATFORM, seed.VERSION)

    assert [r.run_id for r in records] == [seed.RUN_1, "run-undated"]
    assert _store(tmp_path).list("other", seed.PLATFORM, seed.VERSION) == []


def test_resolve_returns_the_file_or_none(tmp_path: Path):
    path = _write(tmp_path, seed.RUN_1, "2026-09-02T14:15:30")
    store = _store(tmp_path)

    assert store.resolve(seed.PROJECT, seed.PLATFORM, seed.VERSION, seed.RUN_1) == path
    assert store.resolve(seed.PROJECT, seed.PLATFORM, seed.VERSION, "run-missing") is None
    assert store.resolve(seed.PROJECT, seed.PLATFORM, seed.VERSION, "..") is None


def test_resolve_refuses_paths_outside_the_workspace(tmp_path: Path):
    workspace = tmp_path / "ws"
    workspace.mkdir()
    (tmp_path / ".._.._.._...json").write_text("{}", encoding="utf-8")

    assert _store(workspace).resolve("..", "..", "..", "..") is None
