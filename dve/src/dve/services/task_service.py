"""The background tasks the API starts and tracks: each job is a module-level
function the task runner runs in a child process, started by its own
`start_<job>` (SRS DSM-DVE req 6, 8, 50)."""

from __future__ import annotations

from typing import Callable, Dict, List, Optional

import mdg
from mdg import CandidateUnitVersion, DataSourceConfig, SourceType

from dve.domain.selection import Selection
from dve.domain.task_status import TaskStatus
from dve.ports.task_log import ITaskLog
from dve.ports.task_runner import ITaskRunner


def _data_sources(sources: dict) -> Dict[SourceType, DataSourceConfig]:
    return {SourceType(key): DataSourceConfig.from_dict(value) for key, value in sources.items()}


def run_production(
    run_id: str,
    selection: dict,
    sources: dict,
    produced_by: Optional[str],
    candidates: Optional[list],
    progress: Callable[[int, str], None],
) -> dict:
    """One Model Setup Data production with the task's id as the run id;
    `sources` maps source type values to DataSourceConfig payloads and
    `candidates` are the optional {"unit_name", "version"} entries under evaluation (req 6)."""
    chosen = Selection.from_dict(selection)
    if chosen is None:
        raise ValueError(f"incomplete selection: {selection}")
    data_sources = _data_sources(sources)
    return mdg.produce_model_setup_data(
        mdg.config_management_repository(data_sources[SourceType.CONFIG_MGMT_DB]),
        mdg.source_code_repository(data_sources[SourceType.SOURCE_CODE_REPO]),
        chosen.project_id,
        chosen.platform_id,
        chosen.version_id,
        run_id=run_id,
        produced_by=produced_by,
        candidates=CandidateUnitVersion.list_from(candidates or []),
        progress=progress,
    ).to_dict()


class TaskService:
    """Starts each kind of task on the task runner and reports, cancels and
    reads the log of any of them by its task id."""

    def __init__(self, runner: ITaskRunner, log: ITaskLog):
        self._runner = runner
        self._log = log

    def start_production(
        self,
        selection: Selection,
        sources: Dict[SourceType, DataSourceConfig],
        produced_by: Optional[str] = None,
        candidates: Optional[List[dict]] = None,
    ) -> str:
        """Starts one production for the selection with the session's data sources
        and returns its task id (req 6); `candidates` are the optional
        {"unit_name", "version"} entries under evaluation (SRS DSM-MDG req 11)."""
        payload = {source_type.value: source.to_dict() for source_type, source in sources.items()}
        return self._runner.submit(run_production, selection.to_dict(), payload, produced_by, list(candidates or []))

    def status(self, task_id: str) -> TaskStatus:
        """The current status of a task; an unknown id reports as PENDING (req 6)."""
        return self._runner.status(task_id)

    def cancel(self, task_id: str) -> TaskStatus:
        """Revokes a queued or running task and returns its status (req 6)."""
        return self._runner.cancel(task_id)

    def log_since(self, task_id: str, index: int) -> List[str]:
        """The task's log lines from 0-based `index` to the end (req 8)."""
        return self._log.lines_since(task_id, index)
