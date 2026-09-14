"""The Flask API over a runtime of fakes: sign-in and session (req 3), data
source connections (req 4, 7), the catalog reads (req 4), the
produced files (req 5) and the production runs (req 6, 8, 50) (SRS DSM-DVE)."""

import pytest

from fakes import seed
from fakes.fake_config_management_repository import FakeConfigManagementRepository
from fakes.fake_production_runner import FakeProductionRunner
from fakes.fake_source_code_repository import FakeSourceCodeRepository
from fakes.seed import file_payload, files_url
from mdg import ConfigManagementAccessError, SourceRepoAccessError, SourceRepoAuthError, SourceType
from dve.api import create_app
from dve.domain.production_status import ProductionStatus
from dve.domain.selection import Selection

UNITS_URL = f"/api/projects/{seed.PROJECT}/platforms/{seed.PLATFORM}/versions/{seed.VERSION}/units"


# ------------------------------------------------------------------ session


def test_index_serves_the_ui(client):
    response = client.get("/")

    assert response.status_code == 200
    assert 'id="login-form"' in response.text


def test_login_returns_the_user_and_the_data_source_defaults(client):
    response = client.post("/api/login", json={"username": seed.OPERATOR, "password": seed.OPERATOR})

    assert response.status_code == 200
    assert response.get_json() == {
        "username": seed.OPERATOR, "role": "operator",
        "defaults": {"config_mgmt_db": seed.CONFIG_DB_ADDRESS, "source_code_repo": seed.SOURCE_REPO_URL},
    }


def test_login_refuses_bad_credentials_and_bad_bodies(client):
    assert client.post("/api/login", json={"username": seed.ADMIN, "password": "wrong"}).status_code == 401
    assert client.post("/api/login", json={"username": seed.ADMIN}).get_json() == {"error": "missing field(s): password"}
    assert client.post("/api/login", data=b"x", content_type="application/json").status_code == 400


def test_session_cookie_is_persistent(client, login):
    response = login(client)

    cookie = response.headers["Set-Cookie"]
    assert "Expires=" in cookie or "Max-Age=" in cookie


def test_session_reports_unauthenticated_then_the_full_state(client, login, connect_all):
    assert client.get("/api/session").get_json() == {"authenticated": False}

    login(client)
    connect_all(client)

    assert client.get("/api/session").get_json() == {
        "authenticated": True, "username": seed.ADMIN, "role": "admin",
        "defaults": {"config_mgmt_db": seed.CONFIG_DB_ADDRESS, "source_code_repo": seed.SOURCE_REPO_URL},
        "config_mgmt_db_connected": True, "source_code_repo_connected": True,
    }


def test_logout_ends_the_session_and_its_connections(signed_in_client, login):
    assert signed_in_client.get("/api/projects").status_code == 200

    assert signed_in_client.post("/api/logout").status_code == 204

    assert signed_in_client.get("/api/projects").status_code == 401
    login(signed_in_client)
    assert signed_in_client.get("/api/projects").get_json() == {"error": "config management database connection required"}


def test_session_survives_a_browser_restart(make_runtime, login, connect_all):
    app = create_app(make_runtime())
    client = app.test_client()
    login(client)
    connect_all(client)

    reopened = app.test_client()
    reopened.set_cookie("session", client.get_cookie("session").value)

    body = reopened.get("/api/session").get_json()
    assert body["authenticated"] is True
    assert (body["config_mgmt_db_connected"], body["source_code_repo_connected"]) == (True, True)


# ------------------------------------------------------------- data sources


def test_sources_are_peers_connected_in_either_order(client, login, connect_config_mgmt_db, connect_source_repo):
    login(client)

    assert connect_source_repo(client).get_json() == {"connected": True}
    body = client.get("/api/session").get_json()
    assert (body["config_mgmt_db_connected"], body["source_code_repo_connected"]) == (False, True)

    assert connect_config_mgmt_db(client).get_json() == {"connected": True}
    body = client.get("/api/session").get_json()
    assert (body["config_mgmt_db_connected"], body["source_code_repo_connected"]) == (True, True)


def test_refused_config_mgmt_db_credentials_map_to_502(make_runtime, make_client, login, connect_config_mgmt_db):
    client = make_client(make_runtime(config_repo=FakeConfigManagementRepository(error=ConfigManagementAccessError("bad creds"))))
    login(client)

    response = connect_config_mgmt_db(client, password="wrong")

    assert response.status_code == 502
    assert "bad creds" in response.get_json()["error"]
    assert client.get("/api/session").get_json()["config_mgmt_db_connected"] is False


def test_refused_source_repo_credentials_map_to_502(make_runtime, make_client, login, connect_source_repo):
    client = make_client(make_runtime(source_repo=FakeSourceCodeRepository(error=SourceRepoAuthError("Authentication failed, could not reach 'system_repo'"))))
    login(client)

    response = connect_source_repo(client, password="wrong")

    assert response.status_code == 502
    assert "Authentication failed" in response.get_json()["error"]
    assert client.get("/api/session").get_json()["source_code_repo_connected"] is False


def test_reconnecting_config_mgmt_db_leaves_the_sibling_source_alone(signed_in_client, connect_config_mgmt_db):
    assert connect_config_mgmt_db(signed_in_client).status_code == 200

    body = signed_in_client.get("/api/session").get_json()
    assert (body["config_mgmt_db_connected"], body["source_code_repo_connected"]) == (True, True)


def test_connect_validates_the_body(client, login, connect_config_mgmt_db):
    login(client)

    response = connect_config_mgmt_db(client, password="")

    assert response.status_code == 400
    assert response.get_json() == {"error": "missing field(s): password"}


@pytest.mark.parametrize("path", ["/api/data-sources/connect/config-mgmt-db", "/api/data-sources/connect/source-code-repo"])
def test_connect_requires_login(client, path):
    response = client.post(path, json={"connection_address": "a", "username": "u", "password": "p"})

    assert response.status_code == 401


@pytest.mark.parametrize("method, path, connect, message", [
    ("get", "/api/projects", None, "authentication required"),
    ("get", "/api/projects", "login", "config management database connection required"),
    ("get", f"/api/units/{seed.SENSOR_APP}/versions", "login", "source code repo connection required"),
    ("get", f"/api/units/{seed.SENSOR_APP}/versions", "config_db", "source code repo connection required"),
    ("post", "/api/mdg/run", "config_db", "source code repo connection required"),
])
def test_guards_name_what_is_missing(client, login, connect_config_mgmt_db, method, path, connect, message):
    if connect in ("login", "config_db"):
        login(client)
    if connect == "config_db":
        connect_config_mgmt_db(client)

    response = getattr(client, method)(path, json=seed.SELECTION)

    assert response.status_code == 401
    assert response.get_json() == {"error": message}


# ---------------------------------------------------- selection and catalog


def test_projects_platforms_versions_and_units_are_read_from_the_database(signed_in_client):
    client = signed_in_client

    assert client.get("/api/projects").get_json()["projects"] == [{"project_id": seed.PROJECT, "name": seed.PROJECT}]
    assert client.get(f"/api/projects/{seed.PROJECT}/platforms").get_json()["platforms"][0]["platform_id"] == seed.PLATFORM
    versions = client.get(f"/api/projects/{seed.PROJECT}/platforms/{seed.PLATFORM}/versions").get_json()["versions"]
    assert [(v["version_id"], v["is_effective"]) for v in versions] == [(seed.VERSION, True), (seed.OLD_VERSION, False)]
    units = client.get(UNITS_URL).get_json()["units"]
    assert units[1] == {"unit_name": seed.NAV_APP, "version": seed.VERSION, "is_candidate": False}


def test_reads_need_only_the_config_mgmt_db_connection(client, login, connect_config_mgmt_db):
    login(client)
    connect_config_mgmt_db(client)

    assert client.get("/api/projects").status_code == 200
    assert client.get(UNITS_URL).status_code == 200


def test_database_failure_maps_to_502(make_runtime, make_signed_in_client):
    class BrokenUnitsRepository(FakeConfigManagementRepository):
        def list_unit_versions(self, project_id, platform_id, version_id):
            raise ConfigManagementAccessError("config db down")

    client = make_signed_in_client(make_runtime(config_repo=BrokenUnitsRepository()))

    response = client.get(UNITS_URL)

    assert response.status_code == 502
    assert "config db down" in response.get_json()["error"]


def test_unit_versions_come_from_the_source_repository(signed_in_client):
    assert signed_in_client.get(f"/api/units/{seed.SENSOR_APP}/versions").get_json() == {"versions": seed.UNIT_VERSIONS[seed.SENSOR_APP]}
    assert signed_in_client.get("/api/units/no_such_app/versions").get_json() == {"versions": []}


def test_unit_versions_access_error_maps_to_502(make_runtime, make_signed_in_client):
    class BrokenVersionsRepository(FakeSourceCodeRepository):
        def list_versions(self, unit_name):
            raise SourceRepoAccessError("gitea down")

    client = make_signed_in_client(make_runtime(source_repo=BrokenVersionsRepository()))

    response = client.get(f"/api/units/{seed.SENSOR_APP}/versions")

    assert response.status_code == 502
    assert "gitea down" in response.get_json()["error"]


# ------------------------------------------------------------------- files


def test_files_are_listed_newest_first_for_every_producer(tmp_path, produce, make_runtime, make_signed_in_client):
    produce(tmp_path, seed.RUN_1, file_payload("2026-09-01T09:02:00", seed.ADMIN))
    produce(tmp_path, seed.RUN_2, file_payload("2026-09-02T14:15:30", seed.OPERATOR))
    produce(tmp_path, "run-old", file_payload(), selection=dict(seed.SELECTION, version_id=seed.OLD_VERSION))

    files = make_signed_in_client(make_runtime(workspace=tmp_path)).get(files_url()).get_json()["files"]

    assert [f["run_id"] for f in files] == [seed.RUN_2, seed.RUN_1]
    assert files[0] == {
        "run_id": seed.RUN_2, "project_id": seed.PROJECT, "platform_id": seed.PLATFORM, "version_id": seed.VERSION,
        "generated_at": "2026-09-02T14:15:30", "produced_by": seed.OPERATOR, "scale": {"apps": 2}, "candidate": None,
    }


def test_a_selection_without_files_lists_empty(tmp_path, make_runtime, make_signed_in_client):
    assert make_signed_in_client(make_runtime(workspace=tmp_path)).get(files_url()).get_json() == {"files": []}


def test_model_is_served_inline_and_download_as_an_attachment(tmp_path, produce, make_runtime, make_signed_in_client):
    produce(tmp_path, seed.RUN_1, file_payload())
    client = make_signed_in_client(make_runtime(workspace=tmp_path))

    inline = client.get(files_url(seed.RUN_1, "/model"))
    assert inline.status_code == 200
    assert inline.content_type == "application/json"
    assert "attachment" not in inline.headers.get("Content-Disposition", "")
    assert inline.get_json()["produced_by"] == seed.OPERATOR

    download = client.get(files_url(seed.RUN_1, "/download"))
    assert download.status_code == 200
    assert "attachment" in download.headers["Content-Disposition"]
    assert seed.FILE_NAME in download.headers["Content-Disposition"]


def test_a_file_outlives_the_runs_record(tmp_path, produce, make_runtime, make_signed_in_client):
    produce(tmp_path, seed.RUN_1, file_payload())
    runtime = make_runtime(workspace=tmp_path)
    client = make_signed_in_client(runtime)

    assert runtime.production_runner.status(seed.RUN_1).state == "PENDING"
    assert client.get(files_url(seed.RUN_1, "/model")).status_code == 200


@pytest.mark.parametrize("suffix", ["/model", "/download"])
def test_unknown_or_escaping_run_ids_report_404(tmp_path, make_runtime, make_signed_in_client, suffix):
    (tmp_path / "outside.json").write_text('{"generated_at": "2026-09-02T00:00:00"}', encoding="utf-8")
    client = make_signed_in_client(make_runtime(workspace=tmp_path / "ws"))

    response = client.get(files_url("does-not-exist", suffix))
    assert response.status_code == 404
    assert response.get_json() == {"error": "model setup data file not found"}

    escaping = {"project_id": "..", "platform_id": "..", "version_id": ".."}
    assert client.get(files_url("..", suffix, selection=escaping)).status_code == 404


@pytest.mark.parametrize("suffix", ["", "/model", "/download"])
def test_file_routes_require_login_and_the_database(client, suffix):
    assert client.get(files_url(seed.RUN_1, suffix) if suffix else files_url()).status_code == 401


# -------------------------------------------------------------- production


def test_run_starts_a_production_with_the_sessions_sources_and_user(make_runtime, make_signed_in_client, login):
    runner = FakeProductionRunner()
    client = make_signed_in_client(make_runtime(production_runner=runner))
    login(client, seed.OPERATOR)

    response = client.post("/api/mdg/run", json=dict(seed.SELECTION, candidate=seed.CANDIDATE))

    assert response.status_code == 202
    task_id = response.get_json()["task_id"]
    selection, sources, produced_by, candidate = runner.started[0]
    assert selection == Selection(seed.PROJECT, seed.PLATFORM, seed.VERSION)
    assert sources[SourceType.CONFIG_MGMT_DB].user_info == f"{seed.USER}:{seed.PASSWORD}"
    assert sources[SourceType.SOURCE_CODE_REPO].connection_address == seed.SOURCE_REPO_URL
    assert (produced_by, candidate) == (seed.OPERATOR, seed.CANDIDATE)
    assert task_id


def test_run_without_a_candidate_submits_none(make_runtime, make_signed_in_client):
    runner = FakeProductionRunner()
    client = make_signed_in_client(make_runtime(production_runner=runner))

    assert client.post("/api/mdg/run", json=seed.SELECTION).status_code == 202

    assert runner.started[0][3] is None


@pytest.mark.parametrize("candidate, message", [
    (seed.SENSOR_APP, "candidate must be a JSON object"),
    ({"unit_name": seed.SENSOR_APP}, "version"),
    ({"version": seed.CANDIDATE_VERSION}, "unit_name"),
])
def test_run_refuses_a_malformed_candidate(signed_in_client, candidate, message):
    response = signed_in_client.post("/api/mdg/run", json=dict(seed.SELECTION, candidate=candidate))

    assert response.status_code == 400
    assert message in response.get_json()["error"]


def test_run_validates_the_selection(signed_in_client):
    assert "missing field" in signed_in_client.post("/api/mdg/run", json={}).get_json()["error"]
    assert signed_in_client.post("/api/mdg/run", data=b"not json", content_type="application/json").status_code == 400


def test_runner_failure_to_start_maps_to_502(make_runtime, make_signed_in_client):
    class BrokenRunner(FakeProductionRunner):
        def start(self, *args, **kwargs):
            raise RuntimeError("broker down")

    response = make_signed_in_client(make_runtime(production_runner=BrokenRunner())).post("/api/mdg/run", json=seed.SELECTION)

    assert response.status_code == 502
    assert "broker down" in response.get_json()["error"]


def test_task_state_serves_the_status_and_the_lines_after_the_cursor(make_runtime, make_signed_in_client):
    runtime = make_runtime()
    client = make_signed_in_client(runtime)
    task_id = client.post("/api/mdg/run", json=seed.SELECTION).get_json()["task_id"]
    for line in ("line one", "line two", "line three"):
        runtime.production_log.append(task_id, line)

    body = client.get(f"/api/mdg/tasks/{task_id}").get_json()
    assert body["state"] == "SUCCESS"
    assert body["result"] == {"selection": seed.SELECTION}
    assert body["lines"] == ["line one", "line two", "line three"]

    assert client.get(f"/api/mdg/tasks/{task_id}?after=1").get_json()["lines"] == ["line three"]
    assert client.get(f"/api/mdg/tasks/{task_id}?after=not-a-number").get_json()["lines"] == ["line one", "line two", "line three"]


def test_task_state_reports_progress_while_the_state_holds(make_runtime, make_signed_in_client):
    runner = FakeProductionRunner(states=[
        "PENDING",
        ProductionStatus("t", "STARTED", progress={"percent": 10, "phase": "clone"}),
        ProductionStatus("t", "STARTED", progress={"percent": 25, "phase": "clone"}),
    ])
    client = make_signed_in_client(make_runtime(production_runner=runner))
    task_id = client.post("/api/mdg/run", json=seed.SELECTION).get_json()["task_id"]

    polls = [client.get(f"/api/mdg/tasks/{task_id}").get_json() for _ in range(4)]

    assert [p["state"] for p in polls] == ["PENDING", "STARTED", "STARTED", "SUCCESS"]
    assert [p.get("progress", {}).get("percent") for p in polls] == [None, 10, 25, None]


def test_cancel_revokes_a_queued_run_and_reports_a_finished_one(signed_in_client):
    task_id = signed_in_client.post("/api/mdg/run", json=seed.SELECTION).get_json()["task_id"]

    assert signed_in_client.post("/api/mdg/tasks/does-not-exist/cancel").get_json() == {"task_id": "does-not-exist", "state": "REVOKED"}
    assert signed_in_client.post(f"/api/mdg/tasks/{task_id}/cancel").get_json()["state"] == "SUCCESS"


def test_cancel_and_state_failures_map_to_502(make_runtime, make_signed_in_client):
    class BrokenRunner(FakeProductionRunner):
        def cancel(self, run_id):
            raise RuntimeError("broker down")

        def status(self, run_id):
            raise RuntimeError("backend down")

    client = make_signed_in_client(make_runtime(production_runner=BrokenRunner()))

    assert "broker down" in client.post("/api/mdg/tasks/x/cancel").get_json()["error"]
    assert "backend down" in client.get("/api/mdg/tasks/x").get_json()["error"]


@pytest.mark.parametrize("method, path", [("post", "/api/mdg/tasks/x/cancel"), ("get", "/api/mdg/tasks/x")])
def test_task_routes_require_login(client, method, path):
    response = getattr(client, method)(path)

    assert response.status_code == 401
    assert response.get_json() == {"error": "authentication required"}
