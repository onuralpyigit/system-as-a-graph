"""Port for regenerating a software unit's build-time code before parsing
(SRS DSM-MDG req 13, 19)."""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path


class IBuildRunner(ABC):
    """Runs a unit's code regeneration build."""

    @abstractmethod
    def ensure_available(self) -> None:
        """Raises RuntimeError when the build tool is not installed."""

    @abstractmethod
    def regenerate_code(self, unit_dir: Path) -> None:
        """Runs the regeneration build of a unit; a unit without a valid build
        file is skipped and a failing build is logged."""
