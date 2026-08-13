"""
Description: HTTP-level coverage for the session-guarded data-source endpoints (SRS MSD.8).
Created by: Mustafa Can Caliskan
Date: 2026-08-10
"""

from __future__ import annotations

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from vae.operations_panel.src.api import routes
from vae.operations_panel.src.api.dependencies import get_panel_container
from vae.operations_panel.tests.conftest import build_panel


@pytest.fixture
def client(users_file):
    """A panel exposed over HTTP, with the stub gateway reachable for assertions."""
    panel = build_panel(users_file)
    app = FastAPI()
    app.include_router(routes.router)
    app.dependency_overrides[get_panel_container] = lambda: panel

    with TestClient(app) as test_client:
        yield test_client, panel


def _bearer(panel, username: str = "operator", password: str = "operator") -> dict:
    granted = panel.log_in(username, password)
    return {"Authorization": f"Bearer {granted.token}"}


def test_configuring_a_source_never_returns_its_secret(client):
    test_client, panel = client

    response = test_client.post(
        "/vae/operations-panel/data-sources",
        headers=_bearer(panel),
        json={
            "source_type": "source_repository",
            "name": "bitbucket-a",
            "access_method": "git_https",
            "connection_address": "https://bitbucket.example/scm/saag",
            "username": "ops",
            "secret": "s3cr3t-token",
            "priority": 0,
        },
    )

    assert response.status_code == 201
    body = response.json()
    assert body["secret_set"] is True
    assert "secret" not in body
    assert "s3cr3t-token" not in response.text


def test_listing_sources_carries_no_secret_either(client):
    test_client, panel = client
    test_client.post(
        "/vae/operations-panel/data-sources",
        headers=_bearer(panel),
        json={
            "source_type": "source_repository",
            "name": "bitbucket-a",
            "access_method": "git_https",
            "connection_address": "https://bitbucket.example/scm/saag",
            "username": "ops",
            "secret": "s3cr3t-token",
            "priority": 0,
        },
    )

    response = test_client.get("/vae/operations-panel/data-sources", headers=_bearer(panel))

    assert response.status_code == 200
    assert "s3cr3t-token" not in response.text


def test_a_view_only_operator_cannot_configure_a_source(client):
    test_client, panel = client

    response = test_client.post(
        "/vae/operations-panel/data-sources",
        headers=_bearer(panel, "viewer", "viewer"),
        json={
            "source_type": "source_repository",
            "name": "bitbucket-a",
            "access_method": "git_https",
            "connection_address": "https://bitbucket.example/scm/saag",
            "username": "ops",
            "secret": "s3cr3t-token",
            "priority": 0,
        },
    )

    assert response.status_code == 403


def test_configuring_a_source_requires_a_session(client):
    test_client, _panel = client

    response = test_client.get("/vae/operations-panel/data-sources")

    assert response.status_code == 401


def test_deleting_an_unknown_source_is_a_404(client):
    test_client, panel = client

    response = test_client.delete(
        "/vae/operations-panel/data-sources/source_repository/no-such-source",
        headers=_bearer(panel),
    )

    assert response.status_code == 404
