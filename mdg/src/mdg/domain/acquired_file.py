"""The record kept for each file obtained from the source code repository
(SRS DSM-MDG req 14)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict


@dataclass(frozen=True)
class AcquiredFile:
    """File name, file path, package version and update timestamp of one
    obtained file (req 14)."""
    unit_name: str
    file_name: str
    file_path: str
    package_version: str
    updated_at: datetime

    def to_dict(self) -> Dict[str, Any]:
        return {
            "unit_name": self.unit_name,
            "file_name": self.file_name,
            "file_path": self.file_path,
            "package_version": self.package_version,
            "updated_at": self.updated_at.isoformat(),
        }
