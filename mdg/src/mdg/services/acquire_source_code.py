"""Acquires one software unit from the source code repository and records its
files, missing mandatory files and access failures (SRS DSM-MDG req 13-16)."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

from mdg.domain.acquired_file import AcquiredFile
from mdg.domain.data_source import SourceType
from mdg.domain.error_record import ErrorRecord, ErrorStatus
from mdg.domain.inventory import SoftwareUnitVersion
from mdg.domain.model_setup_data import UnitStatus
from mdg.domain.project_context import ProjectContext
from mdg.ports.source_code_repository import (
    ISourceCodeRepository,
    SourceRepoAccessError,
    SourceRepoAuthError,
    SourceRepoIntegrityError,
)

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class Acquisition:
    """The outcome of acquiring one unit: its directory when cloned, the files
    recorded (req 14) and the errors recorded (req 15-16)."""
    unit: SoftwareUnitVersion
    unit_dir: Optional[Path]
    files: List[AcquiredFile]
    errors: List[ErrorRecord]

    @property
    def status(self) -> UnitStatus:
        if self.unit_dir is None:
            return UnitStatus.ERROR
        if any(e.status is ErrorStatus.MISSING_DATA for e in self.errors):
            return UnitStatus.MISSING_DATA
        return UnitStatus.ERROR if self.errors else UnitStatus.OK


class AcquireSourceCode:
    """Clones a repository into a destination directory (req 13); an access,
    authorization or integrity failure is recorded instead of raised (req 16).
    The mandatory-file rule applies to software units; a repository that is
    not one is cloned only (req 15)."""

    def __init__(self, source_repo: ISourceCodeRepository):
        self._source_repo = source_repo

    def execute(self, unit: SoftwareUnitVersion, dest_dir: Path, context: ProjectContext, mandatory: bool = True) -> Acquisition:
        try:
            unit_dir = self._source_repo.clone(unit, dest_dir)
            files = self._source_repo.acquired_files(unit, unit_dir) if mandatory else []
        except (SourceRepoAccessError, SourceRepoAuthError, SourceRepoIntegrityError) as exc:
            logger.warning("acquire: %s %s failed: %s", unit.unit_name, unit.version, exc)
            return Acquisition(unit, None, [], [self._record(ErrorStatus.ERROR, str(exc), unit, context)])
        if not mandatory:
            logger.info("acquire: %s %s cloned", unit.unit_name, unit.version)
            return Acquisition(unit, unit_dir, [], [])
        found = {f.file_name for f in files}
        errors = [
            self._record(ErrorStatus.MISSING_DATA, f"mandatory file '{name}' is missing", unit, context)
            for name in self._source_repo.mandatory_files(unit.unit_name) if name not in found
        ]
        logger.info("acquire: %s %s cloned, %d file(s), %d missing", unit.unit_name, unit.version, len(files), len(errors))
        return Acquisition(unit, unit_dir, files, errors)

    @staticmethod
    def _record(status: ErrorStatus, reason: str, unit: SoftwareUnitVersion, context: ProjectContext) -> ErrorRecord:
        return ErrorRecord(status, reason, unit.unit_name, SourceType.SOURCE_CODE_REPO.value, context.project_platform)
