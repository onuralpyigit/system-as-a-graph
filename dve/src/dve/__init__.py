"""DSM-DVE, Design Verification Engine (SRS DSM-DVE req 1-8,
50): the serving layer over mdg. `runtime()` wires the data source defaults
and per-session connections (req 4, 7), the LDAP directory service (req 3),
the task service over the task runner and log (req 6, 8) and the Model Setup
Data store (req 5) from dve.ini; `dve.api.create_app` serves them, productions
run as child processes of the API, and `python -m dve` (the dsm command)
starts it.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Dict

import mdg
from mdg import DataSourceConfig, IConfigManagementRepository, IModelSetupDataStore, ISourceCodeRepository, SourceType

from dve.adapters.ldap_directory_service import LdapDirectoryService
from dve.adapters.in_memory_task_log import InMemoryTaskLog
from dve.config import DVE_INI, Config, config
from dve.ports.directory_service import IDirectoryService
from dve.services.data_source_service import DataSourceService
from dve.services.task_service import TaskService

__all__ = ["Config", "Runtime", "config", "runtime"]


@dataclass
class Runtime:
    """The wired process: data source defaults and connections, the mdg
    factories, and the adapters the API serves."""
    defaults: Dict[SourceType, DataSourceConfig]
    data_sources: DataSourceService
    config_repo_factory: Callable[[DataSourceConfig], IConfigManagementRepository]
    source_repo_factory: Callable[[DataSourceConfig], ISourceCodeRepository]
    directory_service: IDirectoryService
    tasks: TaskService
    model_setup_data_store: IModelSetupDataStore


def runtime() -> Runtime:
    """The runtime dve.ini describes; raises RuntimeError when a data source
    section is missing (req 4)."""
    from dve.adapters.multiprocessing_task_runner import MultiprocessingTaskRunner

    settings = config()
    defaults = {source.source_type: source for source in settings.data_sources}
    missing = sorted(s.value for s in set(SourceType) - defaults.keys())
    if missing:
        raise RuntimeError(f"missing data source(s) [{', '.join(missing)}] in {DVE_INI}")
    log = InMemoryTaskLog()
    return Runtime(
        defaults=defaults,
        data_sources=DataSourceService(defaults, mdg.config_management_repository, mdg.source_code_repository),
        config_repo_factory=mdg.config_management_repository,
        source_repo_factory=mdg.source_code_repository,
        directory_service=LdapDirectoryService(),
        tasks=TaskService(MultiprocessingTaskRunner(log), log),
        model_setup_data_store=mdg.model_setup_data_store(),
    )
