"""
Description: Seeds the configured data source set from a deployment-supplied file.
Created by: Mustafa Can Caliskan
Date: 2026-08-01
"""

from __future__ import annotations

import json
import os
from pathlib import Path

from msd.src.model.data_source import (
    AccessMethod,
    CredentialReference,
    DataSourceConfiguration,
    DataSourceType,
)

#: File listing the sources a fresh deployment starts with. Unset means no
#: seeding: an operator configures the sources through the API instead, which
#: is what a deployment with no prepared file wants.
SEED_FILE_ENV_VAR = "MSD_SOURCE_SEED_FILE"


def seed_file() -> Path | None:
    """Return the configured seed file, or None when there is none."""
    configured = os.getenv(SEED_FILE_ENV_VAR)
    return Path(configured) if configured else None


def load_seed(path: Path, cipher) -> list[DataSourceConfiguration]:
    """Read source configurations from a seed file.

    The file carries exactly what an operator would type into the source
    configuration screen — including each credential's secret in plaintext,
    since this is a deployment-supplied starting point, not operator input
    over the network. Every secret is encrypted before it reaches the
    returned configurations.

    Args:
        path: File to read.
        cipher: Encrypts each entry's plaintext secret for storage.

    Returns:
        The configurations described by the file.

    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If it names an unknown source type or access method.
    """
    with path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)

    return [_to_configuration(entry, cipher) for entry in payload.get("sources", [])]


def _to_configuration(entry: dict, cipher) -> DataSourceConfiguration:
    credential = entry.get("credential")
    return DataSourceConfiguration(
        source_type=DataSourceType(entry["source_type"]),
        name=entry["name"],
        access_method=AccessMethod(entry["access_method"]),
        connection_address=entry["connection_address"],
        credential=(
            CredentialReference(
                username=credential.get("username", ""),
                encrypted_secret=cipher.encrypt(credential["secret"]),
            )
            if credential
            else None
        ),
        priority=int(entry.get("priority", 0)),
        parameters=dict(entry.get("parameters", {})),
    )
