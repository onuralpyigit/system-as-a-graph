"""
Description: Environment-backed credential resolver and system clock adapters.
Created by: Mustafa Can Caliskan
Date: 2026-07-31
"""

from __future__ import annotations

import base64
import hashlib
import os
from datetime import UTC, datetime

from cryptography.fernet import Fernet, InvalidToken

from msd.src.model.data_source import CredentialReference
from shared.errors.acquisition import AcquisitionFailure, AcquisitionStatus

#: Environment variable holding the key secrets are encrypted/decrypted with.
CREDENTIAL_ENCRYPTION_KEY_ENV_VAR = "MSD_CREDENTIAL_ENCRYPTION_KEY"


class FernetSecretCipher:
    """Encrypts/decrypts data-source secrets with a key from the environment.

    The key itself is the only thing that ever lives in the environment; the
    secrets it protects are operator-entered and stored encrypted alongside
    their source configuration (SRS MSD.8).

    Raises:
        RuntimeError: If the encryption key environment variable is unset.
    """

    def __init__(self) -> None:
        """Initialize the cipher from the configured key."""
        key = os.getenv(CREDENTIAL_ENCRYPTION_KEY_ENV_VAR)
        if not key:
            raise RuntimeError(
                f"'{CREDENTIAL_ENCRYPTION_KEY_ENV_VAR}' is not set in the environment"
            )
        self._fernet = Fernet(_to_fernet_key(key))

    def encrypt(self, plaintext: str) -> str:
        """Encrypt a secret for storage."""
        return self._fernet.encrypt(plaintext.encode("utf-8")).decode("ascii")

    def decrypt(self, ciphertext: str) -> str:
        """Decrypt a stored secret.

        Raises:
            AcquisitionFailure: AUTHORIZATION_ERROR when the ciphertext cannot
                be decrypted with the configured key.
        """
        try:
            return self._fernet.decrypt(ciphertext.encode("ascii")).decode("utf-8")
        except InvalidToken as error:
            raise AcquisitionFailure(
                AcquisitionStatus.AUTHORIZATION_ERROR,
                "Stored credential could not be decrypted",
            ) from error


def _to_fernet_key(key: str) -> bytes:
    """Derive a valid 32-byte urlsafe-base64 Fernet key from any configured string."""
    return base64.urlsafe_b64encode(hashlib.sha256(key.encode("utf-8")).digest())


class CipherCredentialResolver:
    """Resolves credential references by decrypting their stored secret."""

    def __init__(self, cipher) -> None:
        """Initialize the resolver.

        Args:
            cipher: Cipher the stored secret is decrypted with.
        """
        self._cipher = cipher

    def resolve(self, reference: CredentialReference) -> str:
        """Resolve a credential reference to its secret.

        Args:
            reference: The stored reference.

        Returns:
            The secret value.

        Raises:
            AcquisitionFailure: AUTHORIZATION_ERROR when the stored secret
                cannot be decrypted.
        """
        return self._cipher.decrypt(reference.encrypted_secret)


class SystemClock:
    """Returns the current UTC time."""

    def now(self) -> datetime:
        """Return the current time, timezone-aware in UTC."""
        return datetime.now(tz=UTC)


class FixedClock:
    """Returns a fixed time, so error times and file names are deterministic in tests."""

    def __init__(self, moment: datetime) -> None:
        """Initialize the clock.

        Args:
            moment: The time every call returns.
        """
        self._moment = moment

    def now(self) -> datetime:
        """Return the configured time."""
        return self._moment
