"""Loads dve.ini: the data source addresses and the API settings, and configures
the logging of the process that loaded it (SRS DSM-DVE req 4, 7, 8)."""

from __future__ import annotations

import configparser
import logging
import sys
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path
from typing import List, Optional

from mdg import DataSourceConfig, SourceType

DVE_INI = Path(__file__).resolve().parent / "dve.ini"

APP_LOGGERS = ("dve", "mdg")
"""The logger trees DSM owns: the only ones whose records reach a task's log, and
the ones `configure_logging` brings up to the configured level."""

_console: Optional[logging.StreamHandler] = None
"""The console handler this module installed, so a second call replaces its own."""


@dataclass(frozen=True)
class ApiConfig:
    """Where the API listens, how long a session cookie lives, in seconds, how
    large a file an upload may carry, in megabytes, and how verbose the logs are."""
    host: str = "127.0.0.1"
    port: int = 8080
    secret_key: str = "dev-insecure-change-me"
    session_lifetime: int = 86400
    max_upload_mb: int = 50
    log_level: str = "INFO"


@dataclass(frozen=True)
class Config:
    data_sources: List[DataSourceConfig] = field(default_factory=list)
    api: ApiConfig = field(default_factory=ApiConfig)


def load(path: Path = DVE_INI) -> Config:
    """The configuration in an ini file; a missing file or option yields its default."""
    ini = configparser.ConfigParser(interpolation=None)
    ini.read(path, encoding="utf-8")

    def text(section: str, option: str, default: str) -> str:
        return ini.get(section, option, fallback=default).strip() or default

    data_sources = [
        DataSourceConfig(
            source_type,
            text(source_type.value, "source_name", ""),
            text(source_type.value, "access_method", ""),
            text(source_type.value, "connection_address", ""),
            "",
        )
        for source_type in SourceType if ini.has_section(source_type.value)
    ]
    return Config(
        data_sources=data_sources,
        api=ApiConfig(
            host=text("api", "host", ApiConfig.host),
            port=ini.getint("api", "port", fallback=ApiConfig.port),
            secret_key=text("api", "secret_key", ApiConfig.secret_key),
            session_lifetime=ini.getint("api", "session_lifetime", fallback=ApiConfig.session_lifetime),
            max_upload_mb=ini.getint("api", "max_upload_mb", fallback=ApiConfig.max_upload_mb),
            log_level=text("api", "log_level", ApiConfig.log_level).upper(),
        ),
    )


@lru_cache
def config() -> Config:
    """The shipped dve.ini, loaded once."""
    return load()


def log_level_of(name: str) -> int:
    """A level name from dve.ini as a logging level; an unknown name is INFO."""
    level = logging.getLevelName((name or "").strip().upper())
    return level if isinstance(level, int) else logging.INFO


def configure_logging(level: Optional[int] = None, task_id: Optional[str] = None) -> None:
    """The one place DSM configures logging, called once per process: one console
    handler on the root logger, the root left at WARNING and `APP_LOGGERS` raised to
    `level` (the ini's when none is given), so a record of another library is never
    created and can never reach a task's log (req 8). `task_id` only says which task
    a child's lines belong to on the shared terminal; calling this again replaces the
    handler this installed and nothing else."""
    global _console
    if level is None:
        level = log_level_of(config().api.log_level)
    root = logging.getLogger()
    if _console is not None:
        root.removeHandler(_console)
    console = logging.StreamHandler(sys.stderr)
    console.setFormatter(
        logging.Formatter(
            (f"[dve-task-{task_id[:8]}] " if task_id else "") + "%(asctime)s %(levelname)s %(name)s: %(message)s"
        )
    )
    console.dsm_console = True
    root.addHandler(console)
    _console = console
    root.setLevel(logging.WARNING)
    for name in APP_LOGGERS:
        logging.getLogger(name).setLevel(level)
