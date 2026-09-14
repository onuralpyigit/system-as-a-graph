"""Mock: the system repo parser over the cloned system repo, answering with
the dev seed's applications and processor units (SRS DSM-MDG req 2.4, 3)."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Dict, List, Tuple

from mdg.ports.system_repo_parser import ISystemRepoParser

logger = logging.getLogger(__name__)


class SystemRepoParser(ISystemRepoParser):
    """Mock: constructed on the cloned system repo directory of the selected
    project and platform; the getters return fixed data."""

    def __init__(self, system_repo_dir: Path, project_name: str, platform_name: str):
        self.system_repo_dir = system_repo_dir
        self.project_name = project_name
        self.platform_name = platform_name
        logger.info("system repo: parsing %s for %s/%s", system_repo_dir.name, project_name, platform_name)

    def get_app_node_relation(self) -> List[Tuple[str, str]]:
        return [("nav_app", "Node-0"), ("sensor_app", "Node-1")]

    def get_app_role_relation(self) -> Dict[str, List[str]]:
        return {"nav_app": ["publisher", "subscriber"], "sensor_app": ["publisher"]}

    def get_app_criticality_relation(self) -> Dict[str, bool]:
        return {}
