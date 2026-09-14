"""In-memory configuration management database with the dev seed's rows (SRS DSM-DVE req 4)."""

from __future__ import annotations

from typing import List, Optional

from fakes import seed
from mdg import IConfigManagementRepository
from mdg.domain.inventory import SoftwareUnitVersion
from mdg.domain.project_context import PlatformRecord, ProjectRecord, VersionRecord
from mdg.domain.system_hierarchy import SystemHierarchyRecord


class FakeConfigManagementRepository(IConfigManagementRepository):
    """Every call raises `error` when one is set."""

    def __init__(self, error: Optional[Exception] = None):
        self._error = error

    def list_projects(self) -> List[ProjectRecord]:
        self._fail()
        return [ProjectRecord(seed.PROJECT, seed.PROJECT)]

    def list_platforms(self, project_id: str) -> List[PlatformRecord]:
        self._fail()
        return [PlatformRecord(seed.PLATFORM, seed.PROJECT, seed.PLATFORM)] if project_id == seed.PROJECT else []

    def list_versions(self, project_id: str, platform_id: str) -> List[VersionRecord]:
        self._fail()
        if (project_id, platform_id) != (seed.PROJECT, seed.PLATFORM):
            return []
        return [
            VersionRecord(seed.VERSION, seed.PROJECT, seed.PLATFORM, seed.VERSION, is_effective=True),
            VersionRecord(seed.OLD_VERSION, seed.PROJECT, seed.PLATFORM, seed.OLD_VERSION, is_effective=False),
        ]

    def list_unit_versions(self, project_id: str, platform_id: str, version_id: str) -> List[SoftwareUnitVersion]:
        self._fail()
        return [SoftwareUnitVersion(name, version_id) for name in (seed.COMMON_LIB, seed.NAV_APP, seed.SENSOR_APP, seed.SYSTEM_REPO)]

    def get_system_hierarchy(self, unit_name: str) -> Optional[SystemHierarchyRecord]:
        raise NotImplementedError("the API never reads the system hierarchy")

    def _fail(self) -> None:
        if self._error is not None:
            raise self._error
