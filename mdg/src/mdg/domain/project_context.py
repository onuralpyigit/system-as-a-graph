"""Project, platform and system version records from the configuration
management database, and the selection a run operates on (SRS DSM-MDG req 5-9)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict


@dataclass(frozen=True)
class ProjectRecord:
    """A project known to the configuration management database (req 6)."""
    project_id: str
    name: str

    def to_dict(self) -> Dict[str, Any]:
        return {"project_id": self.project_id, "name": self.name}


@dataclass(frozen=True)
class PlatformRecord:
    """A platform of a project (req 7)."""
    platform_id: str
    project_id: str
    name: str

    def to_dict(self) -> Dict[str, Any]:
        return {"platform_id": self.platform_id, "project_id": self.project_id, "name": self.name}


@dataclass(frozen=True)
class VersionRecord:
    """A system version of a project and platform, marked when it is the
    currently effective one (req 8-9)."""
    version_id: str
    project_id: str
    platform_id: str
    label: str
    is_effective: bool

    def to_dict(self) -> Dict[str, Any]:
        return {
            "version_id": self.version_id,
            "project_id": self.project_id,
            "platform_id": self.platform_id,
            "label": self.label,
            "is_effective": self.is_effective,
        }


@dataclass(frozen=True)
class ProjectContext:
    """The selected project, platform and system version a data acquisition
    run is associated with (req 5)."""
    project: ProjectRecord
    platform: PlatformRecord
    version: VersionRecord

    @property
    def project_platform(self) -> str:
        """The project/platform pair error records carry (req 18)."""
        return f"{self.project.name}/{self.platform.name}"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "project": self.project.to_dict(),
            "platform": self.platform.to_dict(),
            "version": self.version.to_dict(),
        }
