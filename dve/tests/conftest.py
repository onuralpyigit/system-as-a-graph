"""Fixtures for the API tests: a runtime wired with fakes, clients that are
signed in and have the data sources connected, and produced files."""

from __future__ import annotations

import json
from pathlib import Path

import mdg
import pytest
from flask.testing import FlaskClient

from fakes import seed
from fakes.fake_config_management_repository import FakeConfigManagementRepository
from dve.adapters.in_memory_task_log import InMemoryTaskLog
from fakes.fake_source_code_repository import FakeSourceCodeRepository
from fakes.fake_task_runner import FakeTaskRunner
from dve import Runtime
from dve.adapters.ldap_directory_service import LdapDirectoryService
from dve.api import create_app
from dve.services.data_source_service import DataSourceService
from dve.services.task_service import TaskService


def _refused_token(response) -> bool:
    """Whether this 403 is the API's "send a fresh CSRF token" answer."""
    payload = response.get_json(silent=True)
    return isinstance(payload, dict) and payload.get("csrf") is True


class CsrfClient(FlaskClient):
    """A client that carries the X-CSRFToken an unsafe request gets from the UI's browser:
    read once from GET /api/csrf-token and sent on every state-changing request. Like the UI
    it answers a refused token with one fresh read and a retry, which is how a test signs out
    and back in on one client. A test that sends its own X-CSRFToken is left alone, which is
    how it sends a forged one."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._token = None

    def open(self, *args, **kwargs):
        if kwargs.get("method") in (None, "GET", "HEAD", "OPTIONS"):
            return super().open(*args, **kwargs)
        headers = dict(kwargs.pop("headers", None) or {})
        if any(name.lower() == "x-csrftoken" for name in headers):
            return super().open(*args, headers=headers, **kwargs)
        for _attempt in (1, 2):
            headers["X-CSRFToken"] = self.token()
            response = super().open(*args, headers=headers, **kwargs)
            if response.status_code != 403 or not _refused_token(response):
                return response
            self._token = None
        return response

    def token(self) -> str:
        if self._token is None:
            self._token = self.get("/api/csrf-token").get_json()["csrf_token"]
        return self._token


@pytest.fixture
def make_runtime():
    """Factory of a Runtime over fakes; mdg's real file store serves `workspace`."""
    def factory(workspace: Path = None, task_runner=None, task_log=None, source_repo=None, config_repo=None) -> Runtime:
        config_repo_factory = lambda source: config_repo or FakeConfigManagementRepository()
        source_repo_factory = lambda source: source_repo or FakeSourceCodeRepository()
        return Runtime(
            defaults=seed.DEFAULTS,
            data_sources=DataSourceService(seed.DEFAULTS, config_repo_factory, source_repo_factory),
            config_repo_factory=config_repo_factory,
            source_repo_factory=source_repo_factory,
            directory_service=LdapDirectoryService(),
            tasks=TaskService(task_runner or FakeTaskRunner(), task_log or InMemoryTaskLog()),
            model_setup_data_store=mdg.model_setup_data_store(workspace or Path("/nonexistent-workspace")),
        )
    return factory


@pytest.fixture
def make_client_for():
    """Factory of a client over an application the test built itself."""
    def factory(app):
        app.test_client_class = CsrfClient
        return app.test_client()
    return factory


@pytest.fixture
def make_client(make_runtime, make_client_for):
    """Factory of a test client over a runtime, the default one when none is given."""
    return lambda runtime=None: make_client_for(create_app(runtime or make_runtime()))


@pytest.fixture
def client(make_client):
    return make_client()


@pytest.fixture
def login():
    def action(client, username=seed.ADMIN, password=None):
        response = client.post("/api/login", json={"username": username, "password": password or username})
        assert response.status_code == 200
        return response
    return action


@pytest.fixture
def connect_config_mgmt_db():
    def action(client, address=seed.CONFIG_DB_ADDRESS, username=seed.USER, password=seed.PASSWORD):
        return client.post(
            "/api/data-sources/connect/config-mgmt-db",
            json={"connection_address": address, "username": username, "password": password},
        )
    return action


@pytest.fixture
def connect_source_repo():
    def action(client, address=seed.SOURCE_REPO_URL, username=seed.USER, password=seed.PASSWORD):
        return client.post(
            "/api/data-sources/connect/source-code-repo",
            json={"connection_address": address, "username": username, "password": password},
        )
    return action


@pytest.fixture
def connect_all(connect_config_mgmt_db, connect_source_repo):
    def action(client):
        assert connect_config_mgmt_db(client).status_code == 200
        assert connect_source_repo(client).status_code == 200
    return action


@pytest.fixture
def make_signed_in_client(make_client, login, connect_all):
    """Factory of a client signed in as admin with both sources connected."""
    def factory(runtime=None, connect=True):
        client = make_client(runtime)
        login(client)
        if connect:
            connect_all(client)
        return client
    return factory


@pytest.fixture
def signed_in_client(make_signed_in_client):
    return make_signed_in_client()


@pytest.fixture
def produce():
    """Writes a produced file where mdg's production would have left it and returns its path."""
    def action(workspace: Path, run_id: str, payload: dict, selection: dict = seed.SELECTION) -> Path:
        run_dir = workspace / selection["project_id"] / selection["platform_id"] / selection["version_id"] / run_id
        run_dir.mkdir(parents=True, exist_ok=True)
        path = run_dir / f"{selection['project_id']}_{selection['platform_id']}_{selection['version_id']}.json"
        path.write_text(json.dumps(payload), encoding="utf-8")
        return path
    return action
