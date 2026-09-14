"""dve.ini loading and the runtime's check for the two data source sections (SRS DSM-DVE req 4, 7)."""

import pytest

import dve
from fakes import seed
from mdg import SourceType
from dve.config import DVE_INI, Config, load


def test_shipped_dve_ini_is_loaded():
    config = load(DVE_INI)

    sources = {s.source_type: s for s in config.data_sources}
    assert sources[SourceType.CONFIG_MGMT_DB].connection_address == seed.CONFIG_DB_ADDRESS
    assert sources[SourceType.CONFIG_MGMT_DB].access_method == "mysql"
    assert sources[SourceType.SOURCE_CODE_REPO].connection_address == seed.SOURCE_REPO_URL
    assert sources[SourceType.SOURCE_CODE_REPO].user_info == ""
    assert (config.api.host, config.api.port, config.api.session_lifetime) == ("127.0.0.1", 8080, 86400)
    assert config.worker.broker_url == "redis://localhost:6379/0"
    assert config.worker.result_backend == "redis://localhost:6379/1"
    assert (config.redis.container, config.redis.image, config.redis.port) == ("dsm-redis", "redis:8.4", 6379)


def test_missing_file_yields_defaults(tmp_path):
    config = load(tmp_path / "absent.ini")

    assert config.data_sources == []
    assert config.api.port == 8080
    assert config.redis.container == "dsm-redis"


def test_options_override_defaults(tmp_path):
    ini = tmp_path / "dve.ini"
    ini.write_text("[api]\nport = 9090\nsession_lifetime = 60\n[redis]\nport = 6380\nimage = redis:7\n", encoding="utf-8")

    config = load(ini)

    assert (config.api.port, config.api.session_lifetime) == (9090, 60)
    assert (config.redis.port, config.redis.image) == (6380, "redis:7")


def test_runtime_refuses_an_ini_without_both_data_sources(monkeypatch):
    monkeypatch.setattr(dve, "config", lambda: Config(data_sources=[seed.DEFAULTS[SourceType.CONFIG_MGMT_DB]]))

    with pytest.raises(RuntimeError, match=r"missing data source\(s\) \[source_code_repo\]"):
        dve.runtime()
