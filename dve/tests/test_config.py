"""dve.ini loading, the logging it drives and the runtime's check for the two
data source sections (SRS DSM-DVE req 4, 7, 8)."""

import logging
import os
import sys

import pytest

import dve
from fakes import seed
from mdg import SourceType
from dve.adapters.in_memory_task_log import InMemoryTaskLog
from dve.adapters.multiprocessing_task_runner import MultiprocessingTaskRunner
from dve.config import APP_LOGGERS, ApiConfig, DVE_INI, Config, configure_logging, load, log_level_of
from dve.services.task_service import TaskService

CONFIG_MODULE = sys.modules["dve.config"]
"""The module itself, since `dve/__init__.py` binds the name `dve.config` to a function."""


def test_shipped_dve_ini_is_loaded():
    config = load(DVE_INI)

    sources = {s.source_type: s for s in config.data_sources}
    assert sources[SourceType.CONFIG_MGMT_DB].connection_address == seed.CONFIG_DB_ADDRESS
    assert sources[SourceType.CONFIG_MGMT_DB].access_method == "mysql"
    assert sources[SourceType.SOURCE_CODE_REPO].connection_address == seed.SOURCE_REPO_URL
    assert sources[SourceType.SOURCE_CODE_REPO].user_info == ""
    assert (config.api.host, config.api.port, config.api.session_lifetime) == ("127.0.0.1", 8080, 86400)
    assert config.api.log_level == "INFO"


def test_missing_file_yields_defaults(tmp_path):
    config = load(tmp_path / "absent.ini")

    assert config.data_sources == []
    assert config.api.port == 8080
    assert config.api.log_level == "INFO"


def test_options_override_defaults(tmp_path):
    ini = tmp_path / "dve.ini"
    ini.write_text("[api]\nport = 9090\nsession_lifetime = 60\nlog_level = debug\n", encoding="utf-8")

    config = load(ini)

    assert (config.api.port, config.api.session_lifetime) == (9090, 60)
    assert config.api.log_level == "DEBUG"


def test_runtime_refuses_an_ini_without_both_data_sources(monkeypatch):
    monkeypatch.setattr(dve, "config", lambda: Config(data_sources=[seed.DEFAULTS[SourceType.CONFIG_MGMT_DB]]))

    with pytest.raises(RuntimeError, match=r"missing data source\(s\) \[source_code_repo\]"):
        dve.runtime()


def test_runtime_wires_the_task_service_over_the_runner_and_its_log(monkeypatch):
    monkeypatch.setattr(dve, "config", lambda: Config(data_sources=list(seed.DEFAULTS.values())))

    runtime = dve.runtime()

    assert isinstance(runtime.tasks, TaskService)
    assert isinstance(runtime.tasks._runner, MultiprocessingTaskRunner)
    assert runtime.tasks._runner.concurrency == os.cpu_count()
    assert isinstance(runtime.tasks._log, InMemoryTaskLog)
    assert runtime.tasks._runner._log is runtime.tasks._log


@pytest.fixture
def logging_state():
    """The process's logging as the test found it, put back afterwards."""
    root = logging.getLogger()
    level = root.level
    app_levels = {name: logging.getLogger(name).level for name in APP_LOGGERS}
    yield
    for handler in [handler for handler in root.handlers if getattr(handler, "dsm_console", False)]:
        root.removeHandler(handler)
    CONFIG_MODULE._console = None
    root.setLevel(level)
    for name, value in app_levels.items():
        logging.getLogger(name).setLevel(value)


def dsm_consoles():
    """The console handlers this module's own configure_logging installed."""
    return [handler for handler in logging.getLogger().handlers if getattr(handler, "dsm_console", False)]


def test_configure_logging_leaves_another_library_at_warning(logging_state):
    configure_logging(level=logging.INFO)

    assert logging.getLogger().level == logging.WARNING
    assert [logging.getLogger(name).level for name in APP_LOGGERS] == [logging.INFO] * len(APP_LOGGERS)


def test_configure_logging_installs_one_console_handler_of_its_own(logging_state):
    configure_logging(level=logging.INFO)
    assert len(dsm_consoles()) == 1

    configure_logging(level=logging.DEBUG)

    assert len(dsm_consoles()) == 1


def test_configure_logging_follows_the_ini_level_when_none_is_given(monkeypatch, logging_state):
    monkeypatch.setattr(CONFIG_MODULE, "config", lambda: Config(api=ApiConfig(log_level="WARNING")))

    configure_logging()

    assert [logging.getLogger(name).level for name in APP_LOGGERS] == [logging.WARNING] * len(APP_LOGGERS)


def test_an_unknown_level_name_is_info():
    assert log_level_of("debug") == logging.DEBUG
    assert log_level_of("NotALevel") == logging.INFO
    assert log_level_of("") == logging.INFO
