"""Port for starting and tracking Model Setup Data production runs in the
background (SRS DSM-DVE req 6, 50)."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Dict, Optional

from mdg import DataSourceConfig, SourceType

from dve.domain.production_status import ProductionStatus
from dve.domain.selection import Selection


class IProductionRunner(ABC):
    """Starts, reports and cancels production runs."""

    @abstractmethod
    def start(
        self,
        selection: Selection,
        sources: Dict[SourceType, DataSourceConfig],
        produced_by: Optional[str] = None,
        candidate: Optional[dict] = None,
    ) -> str:
        """Starts one production for the selection with the session's data sources
        and returns its run id (req 6); `candidate` is the optional
        {"unit_name", "version"} under evaluation (SRS DSM-MDG req 11)."""

    @abstractmethod
    def status(self, run_id: str) -> ProductionStatus:
        """The current status of a run; an unknown id reports as PENDING (req 6)."""

    @abstractmethod
    def cancel(self, run_id: str) -> ProductionStatus:
        """Revokes a queued or running run and returns its status (req 6)."""
