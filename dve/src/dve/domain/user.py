"""The user a session belongs to and their role, established by the LDAP
directory service (SRS DSM-DVE req 3)."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class Role(Enum):
    """The authorization level of a user (req 3)."""
    ADMIN = "admin"
    OPERATOR = "operator"


@dataclass(frozen=True)
class User:
    """An authenticated user (req 3)."""
    username: str
    role: Role
