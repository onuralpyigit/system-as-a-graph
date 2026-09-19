"""The error record DSM-MDG keeps for every acquisition or check failure
(SRS DSM-MDG req 12, 15, 16, 18)."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict


class ErrorStatus(Enum):
    """The status a failure marks the run with: an error (req 12, 16) or
    missing data (req 12, 15)."""
    ERROR = "ERROR"
    MISSING_DATA = "MISSING_DATA"


@dataclass(frozen=True)
class ErrorRecord:
    """Error reason, source name, source type, project/platform and error time
    of one failure (req 18)."""
    status: ErrorStatus
    reason: str
    source_name: str
    source_type: str
    project_platform: str
    occurred_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "status": self.status.value,
            "reason": self.reason,
            "source_name": self.source_name,
            "source_type": self.source_type,
            "project_platform": self.project_platform,
            "occurred_at": self.occurred_at.isoformat(),
        }


class DataAcquisitionError(Exception):
    """A failure that stops the data acquisition process, carrying its record
    (req 12). Rebuilt from its message alone when it crosses a process
    boundary, in which case the record is None."""

    def __init__(self, record):
        self.record = record if isinstance(record, ErrorRecord) else None
        super().__init__(self.record.reason if self.record else str(record))
