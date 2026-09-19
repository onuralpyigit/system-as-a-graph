"""The workspace layout and the Model Setup Data file name (SRS DSM-MDG req 19)."""

from pathlib import Path

from fakes import seed
from mdg.domain.workspace import Workspace


def test_run_dir_is_the_run_id_under_the_selection_dir(tmp_path: Path):
    workspace = Workspace(tmp_path)

    assert workspace.selection_dir(seed.PROJECT, seed.PLATFORM, seed.VERSION) == tmp_path / seed.PROJECT / seed.PLATFORM / seed.VERSION
    assert workspace.run_dir(seed.PROJECT, seed.PLATFORM, seed.VERSION, seed.RUN_1) == (
        tmp_path / seed.PROJECT / seed.PLATFORM / seed.VERSION / seed.RUN_1
    )


def test_model_setup_data_file_is_named_after_the_selection(tmp_path: Path):
    path = Workspace(tmp_path).model_setup_data_file(seed.PROJECT, seed.PLATFORM, seed.VERSION, seed.RUN_1)

    assert path == tmp_path / seed.PROJECT / seed.PLATFORM / seed.VERSION / seed.RUN_1 / "skywatch_nftw_1.0.0.json"


def test_ids_are_sanitized_into_directory_names(tmp_path: Path):
    path = Workspace(tmp_path).model_setup_data_file("sky watch", "nftw/x", "1.0.0", "run 1")

    assert path == tmp_path / "sky_watch" / "nftw_x" / "1.0.0" / "run_1" / "sky_watch_nftw_x_1.0.0.json"


def test_contains_rejects_paths_outside_the_root(tmp_path: Path):
    workspace = Workspace(tmp_path / "ws")

    assert workspace.contains(tmp_path / "ws" / "a" / "b.json") is True
    assert workspace.contains(tmp_path / "ws" / ".." / "b.json") is False
