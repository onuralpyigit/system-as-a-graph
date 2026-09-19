"""Source code repository that only checks access and lists versions; the API
never clones or acquires files (SRS DSM-DVE req 7; DSM-MDG req 11)."""

from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Optional

from fakes import seed
from mdg import ISourceCodeRepository
from mdg.domain.acquired_file import AcquiredFile
from mdg.domain.inventory import SoftwareUnitVersion


class FakeSourceCodeRepository(ISourceCodeRepository):
    """Every call raises `error` when one is set."""

    def __init__(self, versions: Optional[Dict[str, List[str]]] = None, error: Optional[Exception] = None):
        self._versions = versions if versions is not None else seed.UNIT_VERSIONS
        self._error = error

    def check_access(self) -> None:
        if self._error is not None:
            raise self._error

    def list_versions(self, unit_name: str) -> List[str]:
        if self._error is not None:
            raise self._error
        return list(self._versions.get(unit_name, []))

    def clone(self, unit: SoftwareUnitVersion, dest_dir: Path) -> Path:
        raise NotImplementedError("the API never clones")

    def acquired_files(self, unit: SoftwareUnitVersion, unit_dir: Path) -> List[AcquiredFile]:
        raise NotImplementedError("the API never acquires files")

    def mandatory_files(self, unit_name: str) -> List[str]:
        raise NotImplementedError("the API never acquires files")
