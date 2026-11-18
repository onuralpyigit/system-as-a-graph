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


class InvalidModelSetupData(ValueError):
    """A payload offered as a Model Setup Data file is not one, or belongs to
    another selection."""


_CONTEXT_IDS = (("project", "project_id"), ("platform", "platform_id"), ("version", "version_id"))


def check_payload(payload: Any, project_id: str, platform_id: str, version_id: str) -> None:
    """Raises InvalidModelSetupData unless the payload has the shape of a Model
    Setup Data file (req 19) and its context is the selection."""
    if not isinstance(payload, dict):
        raise InvalidModelSetupData("not a Model Setup Data file: a JSON object is expected")
    if not isinstance(payload.get("generated_at"), str) or not payload["generated_at"]:
        raise InvalidModelSetupData("not a Model Setup Data file: 'generated_at' is missing")
    context = payload.get("context")
    if not isinstance(context, dict):
        raise InvalidModelSetupData("not a Model Setup Data file: 'context' is missing")
    ids = []
    for part, key in _CONTEXT_IDS:
        record = context.get(part)
        value = record.get(key) if isinstance(record, dict) else None
        if not isinstance(value, str) or not value:
            raise InvalidModelSetupData(f"not a Model Setup Data file: 'context.{part}.{key}' is missing")
        ids.append(value)
    inventory = payload.get("inventory")
    if not isinstance(inventory, dict) or not isinstance(inventory.get("units"), list):
        raise InvalidModelSetupData("not a Model Setup Data file: 'inventory.units' is missing")
    if not isinstance(payload.get("graph"), dict):
        raise InvalidModelSetupData("not a Model Setup Data file: 'graph' is missing")
    for key in ("acquired_files", "errors"):
        if key in payload and not isinstance(payload[key], list):
            raise InvalidModelSetupData(f"not a Model Setup Data file: '{key}' must be a list")
    if ids != [project_id, platform_id, version_id]:
        raise InvalidModelSetupData(
            f"file is for {'/'.join(ids)}, not the selected {project_id}/{platform_id}/{version_id}"
        )


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
    candidates: List[Dict[str, str]] = field(default_factory=list)

    @classmethod
    def from_payload(
        cls, payload: Any, run_id: str, project_id: str, platform_id: str, version_id: str, path: Path
    ) -> Optional["ModelSetupDataRecord"]:
        """The record of a saved file's JSON payload, or None when the payload is
        not a Model Setup Data file."""
        if not isinstance(payload, dict) or "generated_at" not in payload:
            return None
        units = (payload.get("inventory") or {}).get("units")
        candidates = [
            {"unit_name": u.get("unit_name"), "version": u.get("version")}
            for u in (units if isinstance(units, list) else [])
            if isinstance(u, dict) and u.get("is_candidate")
        ]
        return cls(
            run_id=run_id,
            project_id=project_id,
            platform_id=platform_id,
            version_id=version_id,
            path=path,
            generated_at=payload.get("generated_at"),
            produced_by=payload.get("produced_by"),
            scale=(payload.get("graph") or {}).get("metadata", {}).get("scale", {}),
            candidates=candidates,
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
            "candidates": self.candidates,
        }
