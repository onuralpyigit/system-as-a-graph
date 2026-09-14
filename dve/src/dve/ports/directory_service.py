"""Port for the LDAP directory service that authenticates users (SRS DSM-DVE req 3)."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional

from dve.domain.user import User


class IDirectoryService(ABC):
    """Authenticates a username and password pair."""

    @abstractmethod
    def authenticate(self, username: str, password: str) -> Optional[User]:
        """The user the credentials belong to, or None when they are refused (req 3)."""
