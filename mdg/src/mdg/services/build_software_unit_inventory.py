"""Builds the Software Unit Version Inventory of a selection, with the
candidate version applied (SRS DSM-MDG req 10-11)."""

from __future__ import annotations

from typing import Optional

from mdg.domain.inventory import CandidateUnitVersion, SoftwareUnitVersionInventory
from mdg.domain.project_context import ProjectContext
from mdg.ports.config_management_repository import IConfigManagementRepository


class BuildSoftwareUnitInventory:
    """Records the unit name and version pairs of the selected system version (req 10),
    replacing or adding the candidate unit at its candidate version (req 11)."""

    def __init__(self, config_repo: IConfigManagementRepository):
        self._config_repo = config_repo

    def execute(self, context: ProjectContext, candidate: Optional[CandidateUnitVersion] = None) -> SoftwareUnitVersionInventory:
        units = self._config_repo.list_unit_versions(
            context.project.project_id, context.platform.platform_id, context.version.version_id
        )
        inventory = SoftwareUnitVersionInventory(context=context, units=units)
        return inventory if candidate is None else inventory.with_candidate(candidate)
