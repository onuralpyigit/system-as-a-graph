"""The workspace layout: one directory per selection holding one directory per
run, each with its cloned repositories and its Model Setup Data file
(SRS DSM-MDG req 19; DSM-DVE req 5)."""

from __future__ import annotations

import os
import re
from pathlib import Path


class Workspace:
    """Resolves selection directories, run directories and Model Setup Data
    file paths under one root."""

    def __init__(self, root: Path):
        self.root = Path(root)

    def selection_dir(self, project_id: str, platform_id: str, version_id: str) -> Path:
        """<root>/<project>/<platform>/<version>."""
        return self.root / self._name(project_id) / self._name(platform_id) / self._name(version_id)

    def run_dir(self, project_id: str, platform_id: str, version_id: str, run_id: str) -> Path:
        """<selection dir>/<run_id>."""
        return self.selection_dir(project_id, platform_id, version_id) / self._name(run_id)

    def model_setup_data_file(self, project_id: str, platform_id: str, version_id: str, run_id: str) -> Path:
        """<run dir>/<project>_<platform>_<version>.json (req 19)."""
        name = "_".join(self._name(part) for part in (project_id, platform_id, version_id))
        return self.run_dir(project_id, platform_id, version_id, run_id) / f"{name}.json"

    def contains(self, path: Path) -> bool:
        """Whether a resolved path lies inside the workspace root."""
        root = str(self.root.resolve())
        try:
            return os.path.commonpath([root, str(path.resolve())]) == root
        except ValueError:
            return False

    @staticmethod
    def _name(component: str) -> str:
        return re.sub(r"[^A-Za-z0-9._-]", "_", component) or "_"
