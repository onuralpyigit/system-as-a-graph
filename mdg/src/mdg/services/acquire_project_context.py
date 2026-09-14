"""Acquires the selected project, platform and system version from the
configuration management database (SRS DSM-MDG req 5-9, 12)."""

from __future__ import annotations

from typing import Iterable, TypeVar

from mdg.domain.data_source import SourceType
from mdg.domain.error_record import DataAcquisitionError, ErrorRecord, ErrorStatus
from mdg.domain.project_context import ProjectContext
from mdg.ports.config_management_repository import ConfigManagementAccessError, IConfigManagementRepository

T = TypeVar("T")


class AcquireProjectContext:
    """Resolves the selected ids to their records, with the effective version
    marked (req 6-9); an unknown id or a database failure raises
    DataAcquisitionError carrying a MISSING_DATA or ERROR record (req 12)."""

    def __init__(self, config_repo: IConfigManagementRepository):
        self._config_repo = config_repo

    def execute(self, project_id: str, platform_id: str, version_id: str) -> ProjectContext:
        project_platform = f"{project_id}/{platform_id}"
        try:
            project = self._one(self._config_repo.list_projects(), "project_id", project_id, project_platform)
            platform = self._one(self._config_repo.list_platforms(project_id), "platform_id", platform_id, project_platform)
            version = self._one(self._config_repo.list_versions(project_id, platform_id), "version_id", version_id, project_platform)
        except ConfigManagementAccessError as exc:
            raise DataAcquisitionError(self._record(ErrorStatus.ERROR, str(exc), project_platform)) from exc
        return ProjectContext(project=project, platform=platform, version=version)

    def _one(self, records: Iterable[T], id_field: str, wanted: str, project_platform: str) -> T:
        record = next((r for r in records if getattr(r, id_field) == wanted), None)
        if record is None:
            raise DataAcquisitionError(self._record(ErrorStatus.MISSING_DATA, f"{id_field} '{wanted}' not found", project_platform))
        return record

    @staticmethod
    def _record(status: ErrorStatus, reason: str, project_platform: str) -> ErrorRecord:
        return ErrorRecord(status, reason, SourceType.CONFIG_MGMT_DB.value, SourceType.CONFIG_MGMT_DB.value, project_platform)
