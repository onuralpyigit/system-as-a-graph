"""The data sources each session has connected with its own credentials
(SRS DSM-DVE req 4, 7)."""

from __future__ import annotations

import secrets
from typing import Callable, Dict, Optional

from mdg import DataSourceConfig, IConfigManagementRepository, ISourceCodeRepository, SourceType


class DataSourceConnections:
    """Keeps, per session token, the connected data sources; each source is
    verified with one call when connected (req 7)."""

    def __init__(
        self,
        defaults: Dict[SourceType, DataSourceConfig],
        config_repo_factory: Callable[[DataSourceConfig], IConfigManagementRepository],
        source_repo_factory: Callable[[DataSourceConfig], ISourceCodeRepository],
    ):
        self._defaults = defaults
        self._config_repo_factory = config_repo_factory
        self._source_repo_factory = source_repo_factory
        self._sessions: Dict[str, Dict[SourceType, DataSourceConfig]] = {}

    def open(self, token: Optional[str] = None) -> str:
        """The session's token: the given one when it is known, otherwise a new one."""
        if token in self._sessions:
            return token
        token = secrets.token_urlsafe(16)
        self._sessions[token] = {}
        return token

    def connect(self, token: str, source_type: SourceType, address: str, username: str, password: str) -> None:
        """Connects one data source for the session after verifying it: the
        database with a project read (ConfigManagementAccessError on refusal),
        the source code repository with its access check (SourceRepoAuthError
        or SourceRepoAccessError) (req 4, 7)."""
        default = self._defaults[source_type]
        source = DataSourceConfig(source_type, default.source_name, default.access_method, address, f"{username}:{password}")
        if source_type is SourceType.CONFIG_MGMT_DB:
            self._config_repo_factory(source).list_projects()
        else:
            self._source_repo_factory(source).check_access()
        self._sessions[token][source_type] = source

    def connected(self, token: Optional[str]) -> Dict[SourceType, DataSourceConfig]:
        """The data sources the session has connected (req 7)."""
        return dict(self._sessions.get(token, {}))

    def close(self, token: Optional[str]) -> None:
        self._sessions.pop(token, None)
