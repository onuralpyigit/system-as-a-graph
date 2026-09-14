"""Port for saving and finding Model Setup Data files
(SRS DSM-MDG req 19; DSM-DVE req 5)."""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Optional

from mdg.domain.model_setup_data import ModelSetupData, ModelSetupDataRecord


class IModelSetupDataStore(ABC):
    """Stores the Model Setup Data file of a run and lists the files of a selection."""

    @abstractmethod
    def save(self, data: ModelSetupData, run_id: str) -> Path:
        """Saves the Model Setup Data file of a run and returns its path (req 19)."""

    @abstractmethod
    def list(self, project_id: str, platform_id: str, version_id: str) -> List[ModelSetupDataRecord]:
        """The files produced for a selection, newest first (DSM-DVE req 5)."""

    @abstractmethod
    def resolve(self, project_id: str, platform_id: str, version_id: str, run_id: str) -> Optional[Path]:
        """The path of one produced file, or None when there is none."""
