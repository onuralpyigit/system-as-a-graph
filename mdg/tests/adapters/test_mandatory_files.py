"""Locating a unit's mandatory files anywhere under its directory (SRS DSM-MDG req 15)."""

from pathlib import Path

from fakes import seed
from mdg.adapters.source_code.mandatory_files import MandatoryFiles

FILES = MandatoryFiles([seed.MAKEFILE_INCLUDE])


def _write(path: Path, content: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path


def test_expected_names_are_the_makefile_and_the_unit_manifest():
    assert FILES.expected(seed.NAV_APP) == ["Makefile", "nav_app.xml"]


def test_makefile_is_found_recursively_when_it_has_a_configured_include(tmp_path: Path):
    _write(tmp_path / "Makefile", ".PHONY: all\n")
    nested = _write(tmp_path / "build" / "Makefile", seed.VALID_MAKEFILE)

    assert FILES.makefile(tmp_path) == nested


def test_makefile_include_inside_a_comment_does_not_count(tmp_path: Path):
    _write(tmp_path / "Makefile", f"# include {seed.MAKEFILE_INCLUDE}\n.PHONY: all\n")

    assert FILES.makefile(tmp_path) is None
    assert MandatoryFiles([]).has_valid_include(seed.VALID_MAKEFILE) is False


def test_topic_manifest_is_found_anywhere_under_the_unit_dir(tmp_path: Path):
    manifest = _write(tmp_path / "generated" / "nav_app.xml", seed.NAV_APP_MANIFEST)
    _write(tmp_path / "src" / "sensor_app.xml", seed.SENSOR_APP_MANIFEST)

    assert FILES.topic_manifest(tmp_path, seed.NAV_APP) == manifest
    assert FILES.topic_manifest(tmp_path, seed.COMMON_LIB) is None


def test_first_sorted_manifest_wins(tmp_path: Path):
    first = _write(tmp_path / "src" / "a" / "nav_app.xml", seed.NAV_APP_MANIFEST)
    _write(tmp_path / "src" / "b" / "nav_app.xml", seed.NAV_APP_MANIFEST)

    assert FILES.topic_manifest(tmp_path, seed.NAV_APP) == first


def test_locate_maps_every_expected_name(tmp_path: Path):
    makefile = _write(tmp_path / "Makefile", seed.VALID_MAKEFILE)

    assert FILES.locate(tmp_path, seed.NAV_APP) == {"Makefile": makefile, "nav_app.xml": None}
