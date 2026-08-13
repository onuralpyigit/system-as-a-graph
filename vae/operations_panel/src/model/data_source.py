"""
Description: A configured external data source as the panel sees it (SRS MSD.2-8).
Created by: Mustafa Can Caliskan
Date: 2026-08-10
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class DataSourceConfig:
    """One configured external data source, credential status only.

    The secret itself never crosses this port in either direction: it is
    write-only going in (§ the gateway encrypts it before MSD ever stores it)
    and never read back out, so this type carries only whether one is set.

    Attributes:
        source_type: Which of the four external source types this serves.
        name: Operator-chosen name, unique within the source type.
        access_method: Vendor/protocol used to reach it.
        connection_address: Base URL, DSN, or path, depending on access method.
        username: Connection user name; empty when the source needs none.
        secret_set: Whether a secret is currently stored for this source.
        priority: Search order when several sources of one type are candidates.
    """

    source_type: str
    name: str
    access_method: str
    connection_address: str
    username: str = ""
    secret_set: bool = False
    priority: int = 0
