"""Port for the software units and installation scripts source code repository
(SRS DSM-MDG req 2.2, 11, 13-16)."""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import List

from mdg.domain.acquired_file import AcquiredFile
from mdg.domain.inventory import SoftwareUnitVersion


class SourceRepoAccessError(Exception):
    """The repository could not be accessed (req 16)."""


class SourceRepoAuthError(Exception):
    """The repository refused the credentials (req 16)."""


class SourceRepoIntegrityError(Exception):
    """An obtained file could not be read intact (req 16)."""


class ISourceCodeRepository(ABC):
    """Clones software unit repositories and records the mandatory files they hold."""

    @abstractmethod
    def check_access(self) -> None:
        """Verifies the repository accepts the credentials by reading the system
        repo; raises SourceRepoAuthError or SourceRepoAccessError (req 16)."""

    @abstractmethod
    def clone(self, unit: SoftwareUnitVersion, dest_dir: Path) -> Path:
        """Transfers the unit's repository at its version into <dest_dir>/<unit_name>
        and returns that directory (req 13). Raises SourceRepoAccessError or
        SourceRepoAuthError (req 16)."""

    @abstractmethod
    def acquired_files(self, unit: SoftwareUnitVersion, unit_dir: Path) -> List[AcquiredFile]:
        """The records of the mandatory files present under a cloned unit
        directory (req 14). Raises SourceRepoIntegrityError (req 16)."""

    @abstractmethod
    def mandatory_files(self, unit_name: str) -> List[str]:
        """The file names that are mandatory to obtain for a unit (req 15)."""

    @abstractmethod
    def list_versions(self, unit_name: str) -> List[str]:
        """The versions the repository publishes for a unit, newest first, from
        which a candidate version is chosen (req 11)."""
