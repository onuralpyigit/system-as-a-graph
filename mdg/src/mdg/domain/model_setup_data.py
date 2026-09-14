"""The Model Setup Data handed to model construction, the listing record of a
saved Model Setup Data file, and the per-unit acquisition status
(SRS DSM-MDG req 19; DSM-DVE req 5)."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

from mdg.domain.acquired_file import AcquiredFile
from mdg.domain.error_record import ErrorRecord
from mdg.domain.inventory import SoftwareUnitVersionInventory
from mdg.domain.project_context import ProjectContext


class UnitStatus(Enum):
    """The acquisition outcome of one software unit in a run (req 12, 15, 16)."""
    OK = "ok"
    MISSING_DATA = "missing_data"
    ERROR = "error"
    NOT_ACQUIRED = "not_acquired"


@dataclass(frozen=True)
class ModelSetupData:
    """The verified source data of one run: context, inventory, acquired files,
    errors and the node-relationship graph (req 19)."""
    context: ProjectContext
    inventory: SoftwareUnitVersionInventory
    acquired_files: List[AcquiredFile]
    errors: List[ErrorRecord]
    graph: Dict[str, Any]
    generated_at: datetime = field(default_factory=datetime.now)
    produced_by: Optional[str] = None

    @property
    def scale(self) -> Dict[str, int]:
        return self.graph.get("metadata", {}).get("scale", {})

    def to_dict(self) -> Dict[str, Any]:
        return {
            "context": self.context.to_dict(),
            "inventory": self.inventory.to_dict(),
            "acquired_files": [f.to_dict() for f in self.acquired_files],
            "errors": [e.to_dict() for e in self.errors],
            "generated_at": self.generated_at.isoformat(),
            "produced_by": self.produced_by,
            "graph": self.graph,
        }


@dataclass(frozen=True)
class ModelSetupDataRecord:
    """The listing entry of one saved Model Setup Data file, read from the
    file's own header (DSM-DVE req 5)."""
    run_id: str
    project_id: str
    platform_id: str
    version_id: str
    path: Path
    generated_at: Optional[str] = None
    produced_by: Optional[str] = None
    scale: Dict[str, int] = field(default_factory=dict)
    candidate: Optional[Dict[str, str]] = None

    @classmethod
    def from_payload(
        cls, payload: Any, run_id: str, project_id: str, platform_id: str, version_id: str, path: Path
    ) -> Optional["ModelSetupDataRecord"]:
        """The record of a saved file's JSON payload, or None when the payload is
        not a Model Setup Data file."""
        if not isinstance(payload, dict) or "generated_at" not in payload:
            return None
        units = (payload.get("inventory") or {}).get("units")
        candidate = next(
            ({"unit_name": u.get("unit_name"), "version": u.get("version")}
             for u in (units if isinstance(units, list) else []) if isinstance(u, dict) and u.get("is_candidate")),
            None,
        )
        return cls(
            run_id=run_id,
            project_id=project_id,
            platform_id=platform_id,
            version_id=version_id,
            path=path,
            generated_at=payload.get("generated_at"),
            produced_by=payload.get("produced_by"),
            scale=(payload.get("graph") or {}).get("metadata", {}).get("scale", {}),
            candidate=candidate,
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "run_id": self.run_id,
            "project_id": self.project_id,
            "platform_id": self.platform_id,
            "version_id": self.version_id,
            "generated_at": self.generated_at,
            "produced_by": self.produced_by,
            "scale": self.scale,
            "candidate": self.candidate,
        }
