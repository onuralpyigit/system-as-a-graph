"""Port for the system configuration management database
(SRS DSM-MDG req 2.1, 6-12)."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List, Optional

from mdg.domain.inventory import SoftwareUnitVersion
from mdg.domain.project_context import PlatformRecord, ProjectRecord, VersionRecord
from mdg.domain.system_hierarchy import SystemHierarchyRecord


class ConfigManagementAccessError(Exception):
    """Deficiency, access error or format incompatibility in the configuration
    management database (req 12)."""


class IConfigManagementRepository(ABC):
    """Reads projects, platforms, system versions, unit versions and system
    hierarchy naming. Every method raises ConfigManagementAccessError on failure (req 12)."""

    @abstractmethod
    def list_projects(self) -> List[ProjectRecord]:
        """The current projects (req 6)."""

    @abstractmethod
    def list_platforms(self, project_id: str) -> List[PlatformRecord]:
        """The platforms of a project (req 7)."""

    @abstractmethod
    def list_versions(self, project_id: str, platform_id: str) -> List[VersionRecord]:
        """The system versions of a project and platform, the effective one marked (req 8-9)."""

    @abstractmethod
    def list_unit_versions(self, project_id: str, platform_id: str, version_id: str) -> List[SoftwareUnitVersion]:
        """The software unit name and version pairs of a system version (req 10)."""

    @abstractmethod
    def get_system_hierarchy(self, unit_name: str) -> Optional[SystemHierarchyRecord]:
        """The system hierarchy naming of a software unit, or None (req 6-8)."""
