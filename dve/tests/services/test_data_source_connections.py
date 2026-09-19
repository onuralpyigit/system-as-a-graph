"""Per-session data source connections (SRS DSM-DVE req 4, 7)."""

import pytest

from fakes import seed
from fakes.fake_config_management_repository import FakeConfigManagementRepository
from fakes.fake_source_code_repository import FakeSourceCodeRepository
from mdg import ConfigManagementAccessError, SourceRepoAuthError, SourceType
from dve.services.data_source_connections import DataSourceConnections


def _connections(error=None, repo_error=None) -> DataSourceConnections:
    return DataSourceConnections(
        seed.DEFAULTS,
        lambda source: FakeConfigManagementRepository(error=error),
        lambda source: FakeSourceCodeRepository(error=repo_error),
    )


def test_open_returns_a_known_token_and_makes_a_new_one_otherwise():
    connections = _connections()

    token = connections.open(None)

    assert connections.open(token) == token
    assert connections.open("unknown") not in (token, "unknown")


def test_connect_keeps_the_defaults_name_and_method_with_the_sessions_credentials():
    connections = _connections()
    token = connections.open()

    connections.connect(token, SourceType.SOURCE_CODE_REPO, seed.SOURCE_REPO_URL, seed.USER, seed.PASSWORD)

    source = connections.connected(token)[SourceType.SOURCE_CODE_REPO]
    assert (source.source_name, source.access_method) == ("gitea", "git")
    assert (source.connection_address, source.user_info) == (seed.SOURCE_REPO_URL, "dsm:dsm")
    assert SourceType.CONFIG_MGMT_DB not in connections.connected(token)


def test_config_mgmt_db_is_verified_when_connected():
    connections = _connections(error=ConfigManagementAccessError("bad creds"))
    token = connections.open()

    with pytest.raises(ConfigManagementAccessError, match="bad creds"):
        connections.connect(token, SourceType.CONFIG_MGMT_DB, seed.CONFIG_DB_ADDRESS, seed.USER, "wrong")

    assert connections.connected(token) == {}


def test_source_code_repo_is_verified_when_connected():
    connections = _connections(repo_error=SourceRepoAuthError("authentication failed"))
    token = connections.open()

    with pytest.raises(SourceRepoAuthError, match="authentication failed"):
        connections.connect(token, SourceType.SOURCE_CODE_REPO, seed.SOURCE_REPO_URL, seed.USER, "wrong")

    assert connections.connected(token) == {}


def test_close_forgets_the_session():
    connections = _connections()
    token = connections.open()
    connections.connect(token, SourceType.SOURCE_CODE_REPO, seed.SOURCE_REPO_URL, seed.USER, seed.PASSWORD)

    connections.close(token)

    assert connections.connected(token) == {}
    assert connections.open(token) != token
