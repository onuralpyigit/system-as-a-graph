"""Git adapter of the source code repository port: shallow clones by version
tag from one organization on a git server (SRS DSM-MDG req 2.2, 11, 13-16)."""

from __future__ import annotations

import logging
import re
import shutil
import subprocess
from datetime import datetime
from pathlib import Path
from typing import List, Tuple

from mdg.adapters.source_code.mandatory_files import MandatoryFiles
from mdg.domain.acquired_file import AcquiredFile
from mdg.domain.data_source import DataSourceConfig
from mdg.domain.inventory import SoftwareUnitVersion
from mdg.ports.source_code_repository import (
    ISourceCodeRepository,
    SourceRepoAccessError,
    SourceRepoAuthError,
    SourceRepoIntegrityError,
)

logger = logging.getLogger(__name__)

CLONE_TIMEOUT_SECONDS = 300
LS_REMOTE_TIMEOUT_SECONDS = 60
CHECK_TIMEOUT_SECONDS = 15
_TAG_PREFIX = "refs/tags/"


class GitSourceCodeRepository(ISourceCodeRepository):
    """Clones <base_url>/<org>/<unit>.git at the tag named by the unit version;
    the system repo is the repository the credential check reads."""

    def __init__(self, base_url: str, org: str, user: str, password: str, files: MandatoryFiles, system_repo: str):
        self._base_url = base_url.rstrip("/")
        self._org = org
        self._user = user
        self._password = password
        self._files = files
        self._system_repo = system_repo

    @classmethod
    def from_data_source_config(cls, source: DataSourceConfig, files: MandatoryFiles, system_repo: str) -> "GitSourceCodeRepository":
        """Builds the repository from a "<base_url>/<org>" address and
        "<user>:<password>" user information (req 4)."""
        base_url, _, org = source.connection_address.rpartition("/")
        user, _, password = source.user_info.partition(":")
        return cls(base_url, org, user, password, files, system_repo)

    def check_access(self) -> None:
        self._git(
            ["ls-remote", "--heads", self._url(self._system_repo)],
            f"reach '{self._system_repo}'",
            CHECK_TIMEOUT_SECONDS,
        )

    def clone(self, unit: SoftwareUnitVersion, dest_dir: Path) -> Path:
        unit_dir = dest_dir / unit.unit_name
        self._git(
            ["clone", "--depth", "1", "--branch", unit.version, self._url(unit.unit_name), str(unit_dir)],
            f"clone '{unit.unit_name}' at '{unit.version}'",
            CLONE_TIMEOUT_SECONDS,
        )
        shutil.rmtree(unit_dir / ".git", ignore_errors=True)
        return unit_dir

    def acquired_files(self, unit: SoftwareUnitVersion, unit_dir: Path) -> List[AcquiredFile]:
        now = datetime.now()
        records = []
        for path in self._files.locate(unit_dir, unit.unit_name).values():
            if path is None:
                continue
            try:
                path.read_bytes()
            except OSError as exc:
                raise SourceRepoIntegrityError(f"Cannot read '{path}' of '{unit.unit_name}': {exc}") from exc
            records.append(AcquiredFile(unit.unit_name, path.name, str(path), unit.version, now))
        return records

    def mandatory_files(self, unit_name: str) -> List[str]:
        return self._files.expected(unit_name)

    def list_versions(self, unit_name: str) -> List[str]:
        result = self._git(
            ["ls-remote", "--tags", "--refs", self._url(unit_name)],
            f"list the versions of '{unit_name}'",
            LS_REMOTE_TIMEOUT_SECONDS,
        )
        versions = [
            line.partition("\t")[2].strip()[len(_TAG_PREFIX):]
            for line in result.stdout.splitlines()
            if line.partition("\t")[2].strip().startswith(_TAG_PREFIX)
        ]
        versions.sort(key=self.version_key, reverse=True)
        return versions

    @staticmethod
    def version_key(version: str) -> Tuple[tuple, ...]:
        """Sort key ordering digit runs numerically, so 1.0.10 follows 1.0.9."""
        return tuple(
            (0, int(part), "") if part.isdigit() else (1, 0, part)
            for part in re.split(r"(\d+)", version) if part
        )

    def _url(self, unit_name: str) -> str:
        scheme, _, rest = self._base_url.partition("://")
        return f"{scheme}://{self._user}:{self._password}@{rest}/{self._org}/{unit_name}.git"

    def _git(self, args: List[str], attempt: str, timeout: int) -> subprocess.CompletedProcess:
        """Runs one git command; every failure raises SourceRepoAuthError or
        SourceRepoAccessError (req 16)."""
        command = ["git", "-c", "http.sslVerify=false", *args]
        try:
            result = subprocess.run(command, capture_output=True, text=True, timeout=timeout)
        except (subprocess.TimeoutExpired, OSError) as exc:
            raise SourceRepoAccessError(f"Could not {attempt}: {exc}") from exc
        if result.returncode != 0:
            stderr = result.stderr.strip()
            if "Authentication" in stderr or "401" in stderr or "403" in stderr:
                raise SourceRepoAuthError(f"Authentication failed, could not {attempt}: {stderr}")
            raise SourceRepoAccessError(f"Could not {attempt}: {stderr}")
        return result
