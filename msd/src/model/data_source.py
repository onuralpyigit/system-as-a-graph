"""
Description: External data source configuration and registry for MSD (SRS MSD.2-5, 8).
Created by: Mustafa Can Caliskan
Date: 2026-07-31
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class DataSourceType(str, Enum):
    """The four external data source types MSD acquires from (SRS MSD.2-5)."""

    CONFIGURATION_MANAGEMENT_DATABASE = "configuration_management_database"
    SOURCE_REPOSITORY = "source_repository"
    PACKAGE_REPOSITORY = "package_repository"
    NETWORK_TOPOLOGY = "network_topology"


class AccessMethod(str, Enum):
    """Vendor/protocol a configured source is reached by.

    This is the discriminator the adapter factory keys on: a source type may be
    served by several vendors at once (two Bitbucket servers plus a GitLab), so
    the protocol belongs to the individual source, not to the source type.
    Adding a vendor means adding a member here and registering its adapter — no
    use case changes.
    """

    #: Git over HTTP(S). One adapter serves every git host — Gitea, Bitbucket,
    #: GitLab — because they differ in deployment, not in protocol.
    GIT_HTTPS = "git_https"
    #: Any database SQLAlchemy can reach; the driver comes from the URL.
    SQL = "sql"
    #: JSON over HTTP, for package repositories.
    REST = "rest"
    #: An Ansible tree on a mounted filesystem.
    ANSIBLE = "ansible"
    #: Data the operator typed in rather than a source supplying it.
    MANUAL = "manual"


@dataclass(frozen=True)
class CredentialReference:
    """A credential as the operator entered it, encrypted at rest.

    The secret is submitted once through the Operations Panel and encrypted
    before it is stored; only the ciphertext travels with the configuration
    from then on. Resolution (decryption) happens at connection time through
    the credential resolver port, never returning the secret to storage or to
    an API response.

    Attributes:
        username: Connection user name; not a secret, so it is stored directly.
        encrypted_secret: The secret, encrypted at rest.

    Raises:
        ValueError: If the encrypted secret is empty.
    """

    username: str
    encrypted_secret: str

    def __post_init__(self) -> None:
        if not self.encrypted_secret or not self.encrypted_secret.strip():
            raise ValueError("Credential reference needs an encrypted secret")


@dataclass(frozen=True)
class DataSourceConfiguration:
    """One configured external data source (SRS MSD.8).

    A source type has many of these, not one: the deployment may reach several
    repositories, each with its own address, credentials, and vendor protocol.
    Identity is ``(source_type, name)``.

    Attributes:
        source_type: Which of the four external source types this serves.
        name: Operator-chosen name, unique within the source type.
        access_method: Vendor/protocol used to reach it.
        connection_address: Base URL, DSN, or path, depending on access method.
        credential: Credential reference, or None for sources needing no
            authentication (a local file, manual entry).
        priority: Search order when several sources of one type are candidates;
            lower runs first.
        parameters: Source data the operator supplied directly rather than the
            adapter fetching it. A manually entered network topology (MSD.7)
            lives here: its "configuration" *is* the data, and MSD.8 already
            makes per-source configuration savable, so it needs no store of its
            own. Empty for every source whose data is fetched.

    Raises:
        ValueError: If the name is empty.
    """

    source_type: DataSourceType
    name: str
    access_method: AccessMethod
    connection_address: str
    credential: CredentialReference | None = None
    priority: int = 0
    parameters: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.name or not self.name.strip():
            raise ValueError("Data source name must not be empty")

    @property
    def key(self) -> tuple[DataSourceType, str]:
        """Identity of this configuration."""
        return (self.source_type, self.name)


@dataclass
class DataSourceRegistry:
    """The set of configured sources, grouped by type.

    Attributes:
        configurations: All configured sources, in insertion order.
    """

    configurations: list[DataSourceConfiguration] = field(default_factory=list)

    def add(self, configuration: DataSourceConfiguration) -> None:
        """Add a configuration, replacing any existing one with the same key.

        Args:
            configuration: The configuration to store.
        """
        self.configurations = [
            existing for existing in self.configurations if existing.key != configuration.key
        ]
        self.configurations.append(configuration)

    def remove(self, source_type: DataSourceType, name: str) -> bool:
        """Remove a configuration.

        Args:
            source_type: Type of the source to remove.
            name: Name of the source to remove.

        Returns:
            True if a configuration was removed, False if none matched.
        """
        remaining = [
            existing
            for existing in self.configurations
            if existing.key != (source_type, name)
        ]
        removed = len(remaining) != len(self.configurations)
        self.configurations = remaining
        return removed

    def of_type(self, source_type: DataSourceType) -> list[DataSourceConfiguration]:
        """Return every configuration of one type, in priority then name order.

        Args:
            source_type: Type to filter by.

        Returns:
            Matching configurations; empty when the type is unconfigured.
        """
        return sorted(
            (item for item in self.configurations if item.source_type == source_type),
            key=lambda item: (item.priority, item.name),
        )

    def get(self, source_type: DataSourceType, name: str) -> DataSourceConfiguration | None:
        """Look up a single configuration by its key.

        Args:
            source_type: Type of the source.
            name: Name of the source.

        Returns:
            The configuration, or None when it is not configured.
        """
        for item in self.configurations:
            if item.key == (source_type, name):
                return item
        return None
