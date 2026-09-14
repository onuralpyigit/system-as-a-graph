"""In-memory configuration management database (SRS DSM-MDG req 6-12)."""

from __future__ import annotations

from typing import Dict, List, Optional

from fakes import seed
from mdg.domain.inventory import SoftwareUnitVersion
from mdg.domain.project_context import PlatformRecord, ProjectRecord, VersionRecord
from mdg.domain.system_hierarchy import SystemHierarchyRecord
from mdg.ports.config_management_repository import IConfigManagementRepository


class FakeConfigManagementRepository(IConfigManagementRepository):
    """The dev seed's project, platform and versions; unit rows per version are
    given, and every call raises `error` when one is set."""

    def __init__(
        self,
        unit_versions: Optional[Dict[str, List[SoftwareUnitVersion]]] = None,
        system_hierarchies: Optional[Dict[str, SystemHierarchyRecord]] = None,
        error: Optional[Exception] = None,
    ):
        self._unit_versions = unit_versions if unit_versions is not None else {seed.VERSION: seed.inventory_rows()}
        self._system_hierarchies = system_hierarchies or {}
        self._error = error

    def list_projects(self) -> List[ProjectRecord]:
        self._fail()
        return [seed.CONTEXT.project]

    def list_platforms(self, project_id: str) -> List[PlatformRecord]:
        self._fail()
        return [seed.CONTEXT.platform] if project_id == seed.PROJECT else []

    def list_versions(self, project_id: str, platform_id: str) -> List[VersionRecord]:
        self._fail()
        if (project_id, platform_id) != (seed.PROJECT, seed.PLATFORM):
            return []
        return [
            seed.CONTEXT.version,
            VersionRecord(seed.OLD_VERSION, seed.PROJECT, seed.PLATFORM, seed.OLD_VERSION, is_effective=False),
        ]

    def list_unit_versions(self, project_id: str, platform_id: str, version_id: str) -> List[SoftwareUnitVersion]:
        self._fail()
        return list(self._unit_versions.get(version_id, []))

    def get_system_hierarchy(self, unit_name: str) -> Optional[SystemHierarchyRecord]:
        self._fail()
        return self._system_hierarchies.get(unit_name)

    def _fail(self) -> None:
        if self._error is not None:
            raise self._error
