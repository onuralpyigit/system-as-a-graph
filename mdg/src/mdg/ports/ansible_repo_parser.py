"""Port for the parser of the cloned ansible repo: the nodes with their
enrichment, the networks and the connects between them
(SRS DSM-MDG req 2.4, 3)."""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Callable, List

from mdg.domain.source_data import ConnectsTo, Network, Node


class IAnsibleRepoParser(ABC):
    """Answers the network topology questions for one cloned ansible repo.
    Implementations are constructed as (ansible_repo_dir, project_name, platform_name)
    after the ansible repo has been cloned."""

    @abstractmethod
    def get_nodes(self) -> List[Node]:
        """The nodes with their enrichment, by name (req 3)."""

    @abstractmethod
    def get_networks(self) -> List[Network]:
        """The networks, by name (req 3)."""

    @abstractmethod
    def get_connects_to(self) -> List[ConnectsTo]:
        """The connections between nodes and networks with their device names
        and the bandwidth of each link in Gb/s (req 3)."""


AnsibleRepoParserFactory = Callable[[Path, str, str], IAnsibleRepoParser]
