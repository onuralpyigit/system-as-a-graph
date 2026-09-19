"""Filesystem adapter of the Model Setup Data store: one JSON file per run
under the workspace layout (SRS DSM-MDG req 19; DSM-DVE req 5)."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import List, Optional

from mdg.domain.model_setup_data import ModelSetupData, ModelSetupDataRecord
from mdg.domain.workspace import Workspace
from mdg.ports.model_setup_data_store import IModelSetupDataStore

logger = logging.getLogger(__name__)


class FilesystemModelSetupDataStore(IModelSetupDataStore):
    """Saves and lists <workspace>/<project>/<platform>/<version>/<run_id>/<project>_<platform>_<version>.json."""

    def __init__(self, workspace: Workspace):
        self._workspace = workspace

    def save(self, data: ModelSetupData, run_id: str) -> Path:
        context = data.context
        path = self._workspace.model_setup_data_file(
            context.project.project_id, context.platform.platform_id, context.version.version_id, run_id
        )
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data.to_dict(), indent=2), encoding="utf-8")
        logger.info("model setup data: saved %s", path.name)
        return path

    def list(self, project_id: str, platform_id: str, version_id: str) -> List[ModelSetupDataRecord]:
        selection_dir = self._workspace.selection_dir(project_id, platform_id, version_id)
        if not selection_dir.is_dir():
            return []
        records = []
        for run_dir in sorted(selection_dir.iterdir()):
            path = self._workspace.model_setup_data_file(project_id, platform_id, version_id, run_dir.name)
            record = self._read(path, run_dir.name, project_id, platform_id, version_id)
            if record is not None:
                records.append(record)
        records.sort(key=lambda r: r.generated_at or "", reverse=True)
        return records

    def resolve(self, project_id: str, platform_id: str, version_id: str, run_id: str) -> Optional[Path]:
        path = self._workspace.model_setup_data_file(project_id, platform_id, version_id, run_id).resolve()
        if not self._workspace.contains(path):
            logger.warning("model setup data: %r resolves outside the workspace", run_id)
            return None
        return path if path.is_file() else None

    @staticmethod
    def _read(path: Path, run_id: str, project_id: str, platform_id: str, version_id: str) -> Optional[ModelSetupDataRecord]:
        """The listing record of one file, or None when the file is absent or unreadable."""
        if not path.is_file():
            return None
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            logger.warning("model setup data: skipping unreadable %s: %s", path, exc)
            return None
        record = ModelSetupDataRecord.from_payload(payload, run_id, project_id, platform_id, version_id, path)
        if record is None:
            logger.warning("model setup data: skipping %s, not a Model Setup Data file", path)
        return record
