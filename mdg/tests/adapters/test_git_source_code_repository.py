"""The git adapter with subprocess mocked: clone command, error mapping,
acquired file records and version listing (SRS DSM-MDG req 11, 13-16)."""

import subprocess
from pathlib import Path

import pytest

from fakes import seed
from mdg.adapters.source_code.git_source_code_repository import GitSourceCodeRepository
from mdg.adapters.source_code.mandatory_files import MandatoryFiles
from mdg.domain.data_source import DataSourceConfig, SourceType
from mdg.domain.inventory import SoftwareUnitVersion
from mdg.ports.source_code_repository import SourceRepoAccessError, SourceRepoAuthError, SourceRepoIntegrityError

NAV_APP = SoftwareUnitVersion(seed.NAV_APP, seed.VERSION)


def _repository() -> GitSourceCodeRepository:
    source = DataSourceConfig(SourceType.SOURCE_CODE_REPO, "gitea", "git", seed.SOURCE_REPO_URL, seed.CREDENTIALS)
    return GitSourceCodeRepository.from_data_source_config(source, MandatoryFiles([seed.MAKEFILE_INCLUDE]), seed.SYSTEM_REPO)


def _fake_git(monkeypatch, stdout="", returncode=0, stderr="", captured=None):
    def run(cmd, **kwargs):
        if captured is not None:
            captured.append(cmd)
        return subprocess.CompletedProcess(cmd, returncode, stdout=stdout, stderr=stderr)

    monkeypatch.setattr("mdg.adapters.source_code.git_source_code_repository.subprocess.run", run)


def test_check_access_reads_the_system_repo_with_the_credentials(monkeypatch):
    captured = []
    _fake_git(monkeypatch, captured=captured)

    _repository().check_access()

    assert captured[0][3:] == ["ls-remote", "--heads", "http://dsm:dsm@localhost:3000/dsm-src/system_repo.git"]


def test_check_access_maps_refused_credentials_and_a_missing_repo(monkeypatch):
    _fake_git(monkeypatch, returncode=128, stderr="fatal: Authentication failed")
    with pytest.raises(SourceRepoAuthError, match=seed.SYSTEM_REPO):
        _repository().check_access()

    _fake_git(monkeypatch, returncode=128, stderr="fatal: repository not found")
    with pytest.raises(SourceRepoAccessError, match="repository not found"):
        _repository().check_access()


def test_clone_asks_for_the_version_tag_of_the_org_repository(monkeypatch, tmp_path: Path):
    captured = []
    _fake_git(monkeypatch, captured=captured)

    unit_dir = _repository().clone(NAV_APP, tmp_path)

    assert unit_dir == tmp_path / seed.NAV_APP
    assert captured[0][:6] == ["git", "-c", "http.sslVerify=false", "clone", "--depth", "1"]
    assert captured[0][6:8] == ["--branch", seed.VERSION]
    assert captured[0][8] == "http://dsm:dsm@localhost:3000/dsm-src/nav_app.git"
    assert captured[0][9] == str(unit_dir)


def test_git_failures_map_to_the_port_errors(monkeypatch, tmp_path: Path):
    _fake_git(monkeypatch, returncode=128, stderr="fatal: Authentication failed")
    with pytest.raises(SourceRepoAuthError, match=seed.NAV_APP):
        _repository().clone(NAV_APP, tmp_path)

    _fake_git(monkeypatch, returncode=128, stderr="fatal: repository not found")
    with pytest.raises(SourceRepoAccessError, match="repository not found"):
        _repository().clone(NAV_APP, tmp_path)


def test_acquired_files_record_the_mandatory_files_at_the_paths_found(tmp_path: Path):
    (tmp_path / "build").mkdir()
    (tmp_path / "build" / "Makefile").write_text(seed.VALID_MAKEFILE, encoding="utf-8")
    (tmp_path / "src" / "sub").mkdir(parents=True)
    (tmp_path / "src" / "sub" / "nav_app.xml").write_text(seed.NAV_APP_MANIFEST, encoding="utf-8")

    records = {f.file_name: f for f in _repository().acquired_files(NAV_APP, tmp_path)}

    assert records["Makefile"].file_path == str(tmp_path / "build" / "Makefile")
    assert records["nav_app.xml"].file_path == str(tmp_path / "src" / "sub" / "nav_app.xml")
    assert all(f.package_version == seed.VERSION and f.unit_name == seed.NAV_APP for f in records.values())


def test_acquired_files_skip_what_is_absent_or_invalid(tmp_path: Path):
    (tmp_path / "Makefile").write_text(".PHONY: all\n", encoding="utf-8")

    assert _repository().acquired_files(NAV_APP, tmp_path) == []
    assert _repository().mandatory_files(seed.NAV_APP) == ["Makefile", "nav_app.xml"]


def test_unreadable_file_raises_integrity_error(monkeypatch, tmp_path: Path):
    (tmp_path / "Makefile").write_text(seed.VALID_MAKEFILE, encoding="utf-8")
    monkeypatch.setattr(Path, "read_bytes", lambda self: (_ for _ in ()).throw(OSError("disk error")))

    with pytest.raises(SourceRepoIntegrityError, match="disk error"):
        _repository().acquired_files(NAV_APP, tmp_path)


def test_versions_are_the_tags_newest_first_in_numeric_order(monkeypatch):
    captured = []
    _fake_git(
        monkeypatch,
        stdout="9f1c\trefs/tags/1.0.0\na2b3\trefs/tags/1.0.3\nc4d5\trefs/tags/1.0.10\ne5f6\trefs/heads/main\n",
        captured=captured,
    )

    assert _repository().list_versions(seed.SENSOR_APP) == ["1.0.10", "1.0.3", "1.0.0"]
    assert "ls-remote" in captured[0] and captured[0][-1].endswith("/dsm-src/sensor_app.git")


def test_version_key_orders_text_versions_without_error():
    versions = ["1.0.0", "1.1.0-rc1", "main", "1.0.10", "1.0.9"]

    assert sorted(versions, key=GitSourceCodeRepository.version_key)[:3] == ["1.0.0", "1.0.9", "1.0.10"]


def test_listing_versions_maps_failures_like_cloning(monkeypatch):
    _fake_git(monkeypatch, returncode=128, stderr="fatal: Authentication failed")

    with pytest.raises(SourceRepoAuthError):
        _repository().list_versions(seed.SENSOR_APP)
