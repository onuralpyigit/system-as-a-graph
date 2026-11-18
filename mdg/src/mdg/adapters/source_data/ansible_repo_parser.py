"""Mock: the ansible repo parser over the cloned ansible repo, answering with
the dev seed's nodes, networks and connects (SRS DSM-MDG req 2.4, 3)."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import List

from mdg.domain.source_data import ConnectsTo, Network, Node
from mdg.ports.ansible_repo_parser import IAnsibleRepoParser

logger = logging.getLogger(__name__)


class AnsibleRepoParser(IAnsibleRepoParser):
    """Mock: constructed on the cloned ansible repo directory of the selected
    project and platform; the getters return fixed data."""

    def __init__(self, ansible_repo_dir: Path, project_name: str, platform_name: str):
        self.ansible_repo_dir = ansible_repo_dir
        self.project_name = project_name
        self.platform_name = platform_name
        logger.info("ansible repo: parsing %s for %s/%s", ansible_repo_dir.name, project_name, platform_name)

    def get_nodes(self) -> List[Node]:
        return [
            Node("Node-0", group="processors", hw="x86-64/8c", os="Linux 5.15", mw="DDS", gpu="none", display="none"),
            Node("Node-1", group="processors", hw="x86-64/4c", os="Linux 5.15", mw="DDS", gpu="integrated", display="hdmi"),
        ]

    def get_networks(self) -> List[Network]:
        return [Network("Switch-0"), Network("Switch-1")]

    def get_connects_to(self) -> List[ConnectsTo]:
        return [
            ConnectsTo("Node-0", "Switch-0", device="eth0", dev_raw="ens1f0", bandwidth=1.0),
            ConnectsTo("Node-1", "Switch-0", device="eth0", dev_raw="ens1f0", bandwidth=1.0),
            ConnectsTo("Node-0", "Switch-1", device="eth1", dev_raw="ens1f1", bandwidth=0.1),
        ]
