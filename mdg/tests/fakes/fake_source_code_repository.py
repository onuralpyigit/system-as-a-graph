"""Source code repository that writes a unit directory on clone: a valid
Makefile and the unit's topic manifest, plus nav_app's Java import of
common_lib; the system repo gets only a README (SRS DSM-MDG req 13-16)."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple

from fakes import seed
from mdg.domain.acquired_file import AcquiredFile
from mdg.domain.inventory import SoftwareUnitVersion
from mdg.ports.source_code_repository import ISourceCodeRepository, SourceRepoAccessError

MANIFESTS = {seed.NAV_APP: seed.NAV_APP_MANIFEST, seed.SENSOR_APP: seed.SENSOR_APP_MANIFEST}


class FakeSourceCodeRepository(ISourceCodeRepository):
    """Records every clone attempt as (unit_name, version); units in
    `fail_units` raise SourceRepoAccessError, units in `without_manifest`
    are written without their topic manifest."""

    def __init__(
        self,
        fail_units: Iterable[str] = (),
        without_manifest: Iterable[str] = (),
        versions: Optional[Dict[str, List[str]]] = None,
        error: Optional[Exception] = None,
    ):
        self._fail_units = set(fail_units)
        self._without_manifest = set(without_manifest)
        self._versions = versions or {}
        self._error = error
        self.cloned: List[Tuple[str, str]] = []

    def check_access(self) -> None:
        if self._error is not None:
            raise self._error

    def clone(self, unit: SoftwareUnitVersion, dest_dir: Path) -> Path:
        self.cloned.append((unit.unit_name, unit.version))
        if self._error is not None:
            raise self._error
        if unit.unit_name in self._fail_units:
            raise SourceRepoAccessError(f"cannot clone '{unit.unit_name}'")
        unit_dir = dest_dir / unit.unit_name
        (unit_dir / "src").mkdir(parents=True, exist_ok=True)
        if unit.unit_name == seed.SYSTEM_REPO:
            (unit_dir / "README.md").write_text("# system_repo\n", encoding="utf-8")
            return unit_dir
        (unit_dir / "Makefile").write_text(seed.VALID_MAKEFILE, encoding="utf-8")
        if unit.unit_name not in self._without_manifest:
            manifest = MANIFESTS.get(unit.unit_name, "<unit/>")
            (unit_dir / "src" / f"{unit.unit_name}.xml").write_text(manifest, encoding="utf-8")
        if unit.unit_name == seed.NAV_APP:
            (unit_dir / "NavApp.java").write_text(seed.NAV_APP_JAVA, encoding="utf-8")
        return unit_dir

    def acquired_files(self, unit: SoftwareUnitVersion, unit_dir: Path) -> List[AcquiredFile]:
        now = datetime.now()
        return [
            AcquiredFile(unit.unit_name, path.name, str(path), unit.version, now)
            for name in self.mandatory_files(unit.unit_name)
            for path in sorted(unit_dir.rglob(name))[:1]
        ]

    def mandatory_files(self, unit_name: str) -> List[str]:
        return ["Makefile", f"{unit_name}.xml"]

    def list_versions(self, unit_name: str) -> List[str]:
        if self._error is not None:
            raise self._error
        return list(self._versions.get(unit_name, []))
