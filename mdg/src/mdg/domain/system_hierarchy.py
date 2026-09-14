"""The system hierarchy naming of a software unit (CSU, CSC, CSCI, CSS, CSMS)
from the configuration management database (SRS DSM-MDG req 6-8, 19)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict


@dataclass(frozen=True)
class SystemHierarchyRecord:
    """One row of the csu_csms_relation table, keyed by software unit name."""
    csu_name: str
    csc_name: str
    csci_name: str
    css_name: str
    csms_name: str
    csu_description: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "csc_name": self.csc_name,
            "csci_name": self.csci_name,
            "css_name": self.css_name,
            "csms_name": self.csms_name,
            "csu_description": self.csu_description,
        }
