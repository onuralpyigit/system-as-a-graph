"""Port for parsing one cloned software unit into its topic and library
relationships (SRS DSM-MDG req 13, 19)."""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import List

from mdg.domain.source_data import UnitRelation


class ISourceCodeParser(ABC):
    """Parses a unit's topic manifest and source code."""

    @abstractmethod
    def parse(self, unit_dir: Path, unit_name: str) -> List[UnitRelation]:
        """The publishes / subscribes / uses relationships of the unit."""
