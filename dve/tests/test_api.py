"""The Flask API over a runtime of fakes: sign-in and session (req 3), data
source connections (req 4, 7), the catalog reads (req 4), the
produced files (req 5) and the production runs (req 6, 8, 50) (SRS DSM-DVE)."""

import json

import pytest

from fakes import seed
from fakes.fake_config_management_repository import FakeConfigManagementRepository
from fakes.fake_source_code_repository import FakeSourceCodeRepository
from fakes.fake_task_runner import FakeTaskRunner
from fakes.seed import file_payload, files_url
from mdg import ConfigManagementAccessError, SourceRepoAccessError, SourceRepoAuthError, SourceType
from dve.adapters.in_memory_task_log import InMemoryTaskLog
from dve.api import create_app
from dve.domain.task_status import TaskStatus
from dve.services.task_service import run_production

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
    assert client.post("/api/login", json={"username": seed.ADMIN, "password": "wrong"}).status_code == 401  # NOSONAR dummy credential, asserts the 401
    assert client.post("/api/login", json={"username": seed.ADMIN}).get_json() == {"error": "missing field(s): password"}
    assert client.post("/api/login", data=b"x", content_type="application/json").status_code == 400


def test_session_cookie_is_persistent(client, login):
    response = login(client)

    cookie = response.headers["Set-Cookie"]
    assert "Expires=" in cookie or "Max-Age=" in cookie
    assert "SameSite=Lax" in cookie


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


def test_session_survives_a_browser_restart(make_runtime, make_client_for, login, connect_all):
    app = create_app(make_runtime())
    client = make_client_for(app)
    login(client)
    connect_all(client)

    reopened = make_client_for(app)
    reopened.set_cookie("session", client.get_cookie("session").value)

    body = reopened.get("/api/session").get_json()
    assert body["authenticated"] is True
    assert (body["config_mgmt_db_connected"], body["source_code_repo_connected"]) == (True, True)


# ------------------------------------------------------------------ csrf token


def test_the_csrf_token_is_open_before_sign_in(client):
    response = client.get("/api/csrf-token")

    assert response.status_code == 200
    assert response.get_json()["csrf_token"]


def test_an_unsafe_request_without_a_token_is_refused(make_runtime):
    client = create_app(make_runtime()).test_client()

    response = client.post("/api/mdg/run", json=seed.SELECTION)

    assert response.status_code == 403
    assert response.get_json() == {"error": "The CSRF token is missing.", "csrf": True}


def test_a_forged_csrf_token_is_refused(signed_in_client):
    response = signed_in_client.post("/api/logout", headers={"X-CSRFToken": "forged"})  # NOSONAR dummy token, asserts the 403

    assert response.status_code == 403
    assert response.get_json() == {"error": "The CSRF token is invalid.", "csrf": True}
    assert signed_in_client.get("/api/session").get_json()["authenticated"] is True


def test_a_token_carrying_request_is_answered_whatever_its_origin(signed_in_client):
    response = signed_in_client.post("/api/mdg/run", json=seed.SELECTION, headers={"Origin": "http://evil.example"})  # NOSONAR dummy origin, asserts the 202

    assert response.status_code == 202


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

    response = connect_config_mgmt_db(client, password="wrong")  # NOSONAR dummy wrong credential, asserts the 502

    assert response.status_code == 502
    assert "bad creds" in response.get_json()["error"]
    assert client.get("/api/session").get_json()["config_mgmt_db_connected"] is False


def test_refused_source_repo_credentials_map_to_502(make_runtime, make_client, login, connect_source_repo):
    client = make_client(make_runtime(source_repo=FakeSourceCodeRepository(error=SourceRepoAuthError("Authentication failed, could not reach 'system_repo'"))))
    login(client)

    response = connect_source_repo(client, password="wrong")  # NOSONAR dummy wrong credential, asserts the 502

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
    response = client.post(path, json={"connection_address": "a", "username": "u", "password": "p"})  # NOSONAR dummy body, asserts the 401

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
        "generated_at": "2026-09-02T14:15:30", "produced_by": seed.OPERATOR, "scale": {"apps": 2}, "candidates": [],
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

    assert runtime.tasks.status(seed.RUN_1).state == "PENDING"
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


def _upload(client, content: bytes, selection: dict = seed.SELECTION):
    return client.post(files_url(selection=selection), data=content, content_type="application/json")


def test_an_uploaded_file_is_stored_unchanged_listed_and_served(tmp_path, make_runtime, make_signed_in_client):
    content = json.dumps(file_payload(context=seed.context()), indent=4).encode("utf-8")
    client = make_signed_in_client(make_runtime(workspace=tmp_path))

    response = _upload(client, content)

    assert response.status_code == 201
    record = response.get_json()
    assert record == {
        "run_id": record["run_id"], "project_id": seed.PROJECT, "platform_id": seed.PLATFORM,
        "version_id": seed.VERSION, "generated_at": "2026-09-02T14:15:30", "produced_by": seed.OPERATOR,
        "scale": {"apps": 2}, "candidates": [],
    }
    assert client.get(files_url()).get_json() == {"files": [record]}
    assert client.get(files_url(record["run_id"], "/model")).data == content


def test_each_upload_is_a_file_of_its_own(tmp_path, make_runtime, make_signed_in_client):
    content = json.dumps(file_payload(context=seed.context())).encode("utf-8")
    client = make_signed_in_client(make_runtime(workspace=tmp_path))

    first, second = _upload(client, content).get_json(), _upload(client, content).get_json()

    assert first["run_id"] != second["run_id"]
    assert len(client.get(files_url()).get_json()["files"]) == 2


@pytest.mark.parametrize("content, error", [
    (b"", "file is empty"),
    (b"{not json", "not a JSON file"),
    (b"\xff\xfe", "not a JSON file"),
    (b"[]", "not a Model Setup Data file: a JSON object is expected"),
    (json.dumps(file_payload()).encode(), "not a Model Setup Data file: 'context.project.project_id' is missing"),
    (
        json.dumps(file_payload(context=seed.context(dict(seed.SELECTION, version_id=seed.OLD_VERSION)))).encode(),
        f"file is for {seed.PROJECT}/{seed.PLATFORM}/{seed.OLD_VERSION}, "
        f"not the selected {seed.PROJECT}/{seed.PLATFORM}/{seed.VERSION}",
    ),
])
def test_an_upload_that_is_not_the_selections_file_is_refused(tmp_path, make_runtime, make_signed_in_client, content, error):
    client = make_signed_in_client(make_runtime(workspace=tmp_path))

    response = _upload(client, content)

    assert response.status_code == 400
    assert response.get_json() == {"error": error}
    assert client.get(files_url()).get_json() == {"files": []}
    assert not any(path.is_file() for path in tmp_path.rglob("*"))


def test_an_oversized_upload_reports_413_as_json(tmp_path, make_runtime, make_signed_in_client):
    client = make_signed_in_client(make_runtime(workspace=tmp_path))
    client.application.config["MAX_CONTENT_LENGTH"] = 16

    response = _upload(client, json.dumps(file_payload(context=seed.context())).encode("utf-8"))

    assert response.status_code == 413
    assert response.get_json() == {"error": "file is larger than 50 MB"}


def test_upload_requires_login_and_the_database(client, login):
    content = json.dumps(file_payload(context=seed.context())).encode("utf-8")

    assert _upload(client, content).status_code == 401
    login(client)
    assert _upload(client, content).status_code == 401


# -------------------------------------------------------------- production


def test_run_starts_a_production_with_the_sessions_sources_and_user(make_runtime, make_signed_in_client, login):
    runner = FakeTaskRunner()
    client = make_signed_in_client(make_runtime(task_runner=runner))
    login(client, seed.OPERATOR)

    response = client.post("/api/mdg/run", json=dict(seed.SELECTION, candidates=seed.CANDIDATES))

    assert response.status_code == 202
    task_id = response.get_json()["task_id"]
    target, (selection, sources, produced_by, candidates) = runner.submitted[0]
    assert target is run_production
    assert selection == seed.SELECTION
    assert sources[SourceType.CONFIG_MGMT_DB.value]["user_info"] == f"{seed.USER}:{seed.PASSWORD}"
    assert sources[SourceType.SOURCE_CODE_REPO.value]["connection_address"] == seed.SOURCE_REPO_URL
    assert (produced_by, candidates) == (seed.OPERATOR, seed.CANDIDATES)
    assert task_id


def test_run_without_candidates_submits_an_empty_list(make_runtime, make_signed_in_client):
    runner = FakeTaskRunner()
    client = make_signed_in_client(make_runtime(task_runner=runner))

    assert client.post("/api/mdg/run", json=seed.SELECTION).status_code == 202

    assert runner.submitted[0][1][3] == []


def test_run_submits_every_candidate(make_runtime, make_signed_in_client):
    runner = FakeTaskRunner()
    client = make_signed_in_client(make_runtime(task_runner=runner))
    candidates = [seed.CANDIDATE, {"unit_name": seed.NAV_APP, "version": "2.0.0"}]

    assert client.post("/api/mdg/run", json=dict(seed.SELECTION, candidates=candidates)).status_code == 202

    assert runner.submitted[0][1][3] == candidates


@pytest.mark.parametrize("candidates, message", [
    (seed.CANDIDATE, "candidates must be a JSON array"),
    ([seed.SENSOR_APP], "candidates[0] must be a JSON object"),
    ([seed.CANDIDATE, {"unit_name": seed.NAV_APP}], "candidates[1] missing field(s): version"),
    ([{"version": seed.CANDIDATE_VERSION}], "unit_name"),
    ([seed.CANDIDATE, {"unit_name": seed.SENSOR_APP, "version": "1.0.1"}], f"candidates name a unit twice: {seed.SENSOR_APP}"),
])
def test_run_refuses_malformed_candidates(signed_in_client, candidates, message):
    response = signed_in_client.post("/api/mdg/run", json=dict(seed.SELECTION, candidates=candidates))

    assert response.status_code == 400
    assert message in response.get_json()["error"]


def test_run_validates_the_selection(signed_in_client):
    assert "missing field" in signed_in_client.post("/api/mdg/run", json={}).get_json()["error"]
    assert signed_in_client.post("/api/mdg/run", data=b"not json", content_type="application/json").status_code == 400


def test_runner_failure_to_start_maps_to_502(make_runtime, make_signed_in_client):
    class BrokenRunner(FakeTaskRunner):
        def submit(self, target, *args):
            raise RuntimeError("runner down")

    response = make_signed_in_client(make_runtime(task_runner=BrokenRunner())).post("/api/mdg/run", json=seed.SELECTION)

    assert response.status_code == 502
    assert "runner down" in response.get_json()["error"]


def test_task_state_serves_the_status_and_the_lines_after_the_cursor(make_runtime, make_signed_in_client):
    log = InMemoryTaskLog()
    client = make_signed_in_client(make_runtime(task_log=log))
    task_id = client.post("/api/mdg/run", json=seed.SELECTION).get_json()["task_id"]
    for line in ("line one", "line two", "line three"):
        log.append(task_id, line)

    body = client.get(f"/api/mdg/tasks/{task_id}").get_json()
    assert body["state"] == "SUCCESS"
    assert body["result"] == {"selection": seed.SELECTION}
    assert body["lines"] == ["line one", "line two", "line three"]
    assert isinstance(body["now"], float)

    assert client.get(f"/api/mdg/tasks/{task_id}?after=1").get_json()["lines"] == ["line three"]
    assert client.get(f"/api/mdg/tasks/{task_id}?after=not-a-number").get_json()["lines"] == ["line one", "line two", "line three"]


def test_task_state_reports_progress_while_the_state_holds(make_runtime, make_signed_in_client):
    runner = FakeTaskRunner(states=[
        "PENDING",
        TaskStatus("t", "STARTED", progress={"percent": 10, "phase": "clone"}),
        TaskStatus("t", "STARTED", progress={"percent": 25, "phase": "clone"}),
    ])
    client = make_signed_in_client(make_runtime(task_runner=runner))
    task_id = client.post("/api/mdg/run", json=seed.SELECTION).get_json()["task_id"]

    polls = [client.get(f"/api/mdg/tasks/{task_id}").get_json() for _ in range(4)]

    assert [p["state"] for p in polls] == ["PENDING", "STARTED", "STARTED", "SUCCESS"]
    assert [p.get("progress", {}).get("percent") for p in polls] == [None, 10, 25, None]


def test_cancel_revokes_a_queued_run_and_reports_a_finished_one(signed_in_client):
    task_id = signed_in_client.post("/api/mdg/run", json=seed.SELECTION).get_json()["task_id"]

    assert signed_in_client.post("/api/mdg/tasks/does-not-exist/cancel").get_json() == {"task_id": "does-not-exist", "state": "REVOKED"}
    assert signed_in_client.post(f"/api/mdg/tasks/{task_id}/cancel").get_json()["state"] == "SUCCESS"


def test_cancel_and_state_failures_map_to_502(make_runtime, make_signed_in_client):
    class BrokenRunner(FakeTaskRunner):
        def cancel(self, task_id):
            raise RuntimeError("runner down")

        def status(self, task_id):
            raise RuntimeError("status unavailable")

    client = make_signed_in_client(make_runtime(task_runner=BrokenRunner()))

    assert "runner down" in client.post("/api/mdg/tasks/x/cancel").get_json()["error"]
    assert "status unavailable" in client.get("/api/mdg/tasks/x").get_json()["error"]


@pytest.mark.parametrize("method, path", [("post", "/api/mdg/tasks/x/cancel"), ("get", "/api/mdg/tasks/x")])
def test_task_routes_require_login(client, method, path):
    response = getattr(client, method)(path)

    assert response.status_code == 401
    assert response.get_json() == {"error": "authentication required"}
