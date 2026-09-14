"""The project, platform and system version the user selected to work on
(SRS DSM-DVE req 4)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, ClassVar, Dict, Optional, Tuple


@dataclass(frozen=True)
class Selection:
    """One selected project, platform and system version (req 4)."""
    project_id: str
    platform_id: str
    version_id: str

    FIELDS: ClassVar[Tuple[str, ...]] = ("project_id", "platform_id", "version_id")

    @classmethod
    def from_dict(cls, payload: Any) -> Optional["Selection"]:
        """The selection a payload names, or None when a field is missing or empty."""
        if not isinstance(payload, dict) or not all(payload.get(field) for field in cls.FIELDS):
            return None
        return cls(*(str(payload[field]) for field in cls.FIELDS))

    def to_dict(self) -> Dict[str, str]:
        return {"project_id": self.project_id, "platform_id": self.platform_id, "version_id": self.version_id}
