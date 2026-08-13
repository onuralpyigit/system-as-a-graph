"""
Description: Small outbound ports for credential resolution and time.
Created by: Mustafa Can Caliskan
Date: 2026-07-31
"""

from __future__ import annotations

from datetime import datetime
from typing import Protocol, runtime_checkable

from msd.src.model.data_source import CredentialReference


@runtime_checkable
class CredentialResolverPort(Protocol):
    """Turns a stored credential reference into a usable secret.

    The secret is encrypted at rest with the source configuration; resolution
    decrypts it at connection time, so the plaintext never lives longer than
    one call.
    """

    def resolve(self, reference: CredentialReference) -> str:
        """Resolve a credential reference to its secret.

        Args:
            reference: The stored reference.

        Returns:
            The secret value.

        Raises:
            AcquisitionFailure: With AUTHORIZATION_ERROR when the reference
                cannot be decrypted, since the connection cannot be authorized.
        """
        ...


@runtime_checkable
class SecretCipherPort(Protocol):
    """Encrypts and decrypts secrets stored alongside source configuration."""

    def encrypt(self, plaintext: str) -> str:
        """Encrypt a secret for storage.

        Args:
            plaintext: The secret as the operator entered it.

        Returns:
            The ciphertext to persist.
        """
        ...

    def decrypt(self, ciphertext: str) -> str:
        """Decrypt a stored secret.

        Args:
            ciphertext: The stored value.

        Returns:
            The plaintext secret.
        """
        ...


@runtime_checkable
class ClockPort(Protocol):
    """Supplies the current time.

    Error records carry an error time (SRS MSD.22) and documents carry a
    production time, both of which must be deterministic under test.
    """

    def now(self) -> datetime:
        """Return the current time."""
        ...
