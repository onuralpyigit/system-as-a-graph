"""The status of one Model Setup Data production run as the production runner
reports it (SRS DSM-DVE req 6)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass(frozen=True)
class ProductionStatus:
    """State (Celery's PENDING, STARTED, SUCCESS, FAILURE, REVOKED), the result
    or error of a finished run, and the progress a running one published (req 6)."""
    run_id: str
    state: str
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    progress: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """The status payload the API serves, carrying only the parts that are set."""
        payload: Dict[str, Any] = {"task_id": self.run_id, "state": self.state}
        for key in ("result", "error", "progress"):
            if getattr(self, key) is not None:
                payload[key] = getattr(self, key)
        return payload
