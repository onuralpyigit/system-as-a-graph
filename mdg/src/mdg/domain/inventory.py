"""The Software Unit Version Inventory and the candidate versions under
evaluation (SRS DSM-MDG req 10-11)."""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from typing import Any, Dict, Iterable, List, Optional

from mdg.domain.project_context import ProjectContext


@dataclass(frozen=True)
class SoftwareUnitVersion:
    """One software unit at one version (req 10), flagged when it is a
    candidate under evaluation (req 11)."""
    unit_name: str
    version: str
    is_candidate: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {"unit_name": self.unit_name, "version": self.version, "is_candidate": self.is_candidate}


@dataclass(frozen=True)
class CandidateUnitVersion:
    """The version of one software unit being evaluated for installation into
    the target environment (req 11)."""
    unit_name: str
    version: str

    def to_dict(self) -> Dict[str, Any]:
        return {"unit_name": self.unit_name, "version": self.version}

    @classmethod
    def from_dict(cls, payload: Any) -> Optional["CandidateUnitVersion"]:
        """The candidate a JSON payload names, or None when it names none."""
        if not isinstance(payload, dict) or not payload.get("unit_name") or not payload.get("version"):
            return None
        return cls(unit_name=str(payload["unit_name"]), version=str(payload["version"]))

    @classmethod
    def list_from(cls, payload: Any) -> List["CandidateUnitVersion"]:
        """The candidates a JSON array names, skipping entries that name none."""
        if not isinstance(payload, list):
            return []
        candidates = (cls.from_dict(item) for item in payload)
        return [candidate for candidate in candidates if candidate is not None]


@dataclass(frozen=True)
class SoftwareUnitVersionInventory:
    """The software units and versions that will run in the selected system
    environment (req 10)."""
    context: ProjectContext
    units: List[SoftwareUnitVersion] = field(default_factory=list)

    def with_candidate(self, candidate: CandidateUnitVersion) -> "SoftwareUnitVersionInventory":
        """The inventory with the candidate's unit at the candidate version and
        every other unit as it was (req 11)."""
        unit = SoftwareUnitVersion(candidate.unit_name, candidate.version, is_candidate=True)
        units = [unit if u.unit_name == unit.unit_name else u for u in self.units]
        if self.find(unit.unit_name) is None:
            units.append(unit)
        return replace(self, units=units)

    def with_candidates(self, candidates: Iterable[CandidateUnitVersion]) -> "SoftwareUnitVersionInventory":
        """The inventory with every candidate's unit at its candidate version and
        every other unit as the system version defines it (req 11)."""
        inventory = self
        for candidate in candidates:
            inventory = inventory.with_candidate(candidate)
        return inventory

    def find(self, unit_name: str) -> Optional[SoftwareUnitVersion]:
        return next((u for u in self.units if u.unit_name == unit_name), None)

    def without(self, unit_name: str) -> "SoftwareUnitVersionInventory":
        return replace(self, units=[u for u in self.units if u.unit_name != unit_name])

    def to_dict(self) -> Dict[str, Any]:
        return {"context": self.context.to_dict(), "units": [u.to_dict() for u in self.units]}
