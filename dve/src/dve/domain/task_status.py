"""The status of one background task as the task runner reports it
(SRS DSM-DVE req 6)."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Dict, Optional

PENDING, STARTED, SUCCESS, FAILURE, REVOKED = "PENDING", "STARTED", "SUCCESS", "FAILURE", "REVOKED"


@dataclass(frozen=True)
class TaskStatus:
    """State (PENDING, STARTED, SUCCESS, FAILURE, REVOKED), the result or error
    of a finished task, the progress a running one reported, and when it started
    and finished (epoch seconds; not part of equality) (req 6)."""
    task_id: str
    state: str
    result: Optional[Any] = None
    error: Optional[str] = None
    progress: Optional[Dict[str, Any]] = None
    started_at: Optional[float] = field(default=None, compare=False)
    finished_at: Optional[float] = field(default=None, compare=False)

    def ended(self, state: str, **fields: Any) -> "TaskStatus":
        """This task's status at `state`, keeping its start and stamping its end."""
        return TaskStatus(self.task_id, state, started_at=self.started_at, finished_at=time.time(), **fields)

    def to_dict(self) -> Dict[str, Any]:
        """The status payload the API serves, carrying only the parts that are set."""
        payload: Dict[str, Any] = {"task_id": self.task_id, "state": self.state}
        for key in ("result", "error", "progress", "started_at", "finished_at"):
            if getattr(self, key) is not None:
                payload[key] = getattr(self, key)
        return payload
