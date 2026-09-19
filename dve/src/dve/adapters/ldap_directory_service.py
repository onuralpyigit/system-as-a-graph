"""Mock: the LDAP directory service as a fixed set of users (SRS DSM-DVE req 3)."""

from __future__ import annotations

from typing import Optional

from dve.domain.user import Role, User
from dve.ports.directory_service import IDirectoryService


class LdapDirectoryService(IDirectoryService):
    """Mock: accepts admin/admin and operator/operator."""

    _USERS = {"admin": ("admin", Role.ADMIN), "operator": ("operator", Role.OPERATOR)}

    def authenticate(self, username: str, password: str) -> Optional[User]:
        entry = self._USERS.get(username)
        if entry is None or entry[0] != password:
            return None
        return User(username, entry[1])
