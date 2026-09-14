"""Port for the parser of the cloned system repo: which application runs on
which processor unit, application roles and criticality
(SRS DSM-MDG req 2.4, 3)."""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Callable, Dict, List, Tuple


class ISystemRepoParser(ABC):
    """Answers the system topology questions for one cloned system repo.
    Implementations are constructed as (system_repo_dir, project_name, platform_name)
    after the system repo has been cloned."""

    @abstractmethod
    def get_app_node_relation(self) -> List[Tuple[str, str]]:
        """(application, processor unit) pairs (req 3)."""

    @abstractmethod
    def get_app_role_relation(self) -> Dict[str, List[str]]:
        """The roles of each application (req 3)."""

    @abstractmethod
    def get_app_criticality_relation(self) -> Dict[str, bool]:
        """The criticality of each application (req 3)."""


SystemRepoParserFactory = Callable[[Path, str, str], ISystemRepoParser]
