"""DVE's Flask API: sign-in, data source connections, the selection, the
produced Model Setup Data files and the production runs
(SRS DSM-DVE req 3-8, 50).

Endpoints:
  GET    /
  POST   /api/login                                    {"username", "password"}
  POST   /api/logout
  GET    /api/session
  POST   /api/data-sources/connect/config-mgmt-db      {"connection_address", "username", "password"}   [login]
  POST   /api/data-sources/connect/source-code-repo    {"connection_address", "username", "password"}   [login]
  GET    /api/projects                                                                                  [login + config_mgmt_db]
  GET    /api/projects/<project_id>/platforms                                                            [login + config_mgmt_db]
  GET    /api/projects/<project_id>/platforms/<platform_id>/versions                                     [login + config_mgmt_db]
  GET    /api/projects/<project_id>/platforms/<platform_id>/versions/<version_id>/units                  [login + config_mgmt_db]
  GET    /api/projects/.../versions/<version_id>/mdg-files                                               [login + config_mgmt_db]
  GET    /api/projects/.../versions/<version_id>/mdg-files/<run_id>/model                                [login + config_mgmt_db]
  GET    /api/projects/.../versions/<version_id>/mdg-files/<run_id>/download                             [login + config_mgmt_db]
  GET    /api/units/<unit_name>/versions                                                                 [login + source_code_repo]
  POST   /api/mdg/run                                  selection fields + "candidate"?                   [login + both]
  GET    /api/mdg/tasks/<task_id>?after=<line>                                                           [login]
  POST   /api/mdg/tasks/<task_id>/cancel                                                                 [login]

Run with: python -m dve.api (the dsm command starts it together with the worker).
"""

from __future__ import annotations

import functools
import logging
from datetime import timedelta

from flask import Flask, jsonify, render_template, request, send_file, session

from mdg import ConfigManagementAccessError, SourceRepoAccessError, SourceRepoAuthError, SourceType

from dve import Runtime, runtime as load_runtime
from dve.config import config
from dve.domain.selection import Selection

logger = logging.getLogger(__name__)

_CREDENTIALS = ("username", "password")
_CONNECT_FIELDS = ("connection_address", "username", "password")
_CANDIDATE_FIELDS = ("unit_name", "version")
_CONNECT_SOURCES = {
    "config-mgmt-db": SourceType.CONFIG_MGMT_DB,
    "source-code-repo": SourceType.SOURCE_CODE_REPO,
}


def _error(message: str, code: int):
    return jsonify({"error": message}), code


def _json_body(*required: str):
    """The request's JSON object, or a 400 response when a required field is missing."""
    body = request.get_json(silent=True, force=True)
    if not isinstance(body, dict):
        return None, _error("request body must be a JSON object", 400)
    missing = [field for field in required if not body.get(field)]
    if missing:
        return None, _error(f"missing field(s): {', '.join(missing)}", 400)
    return body, None


def _candidate(body: dict):
    """The candidate unit version in the body (SRS DSM-MDG req 11): None when absent, a 400 response when malformed."""
    candidate = body.get("candidate")
    if candidate is None:
        return None, None
    if not isinstance(candidate, dict):
        return None, _error("candidate must be a JSON object", 400)
    missing = [field for field in _CANDIDATE_FIELDS if not candidate.get(field)]
    if missing:
        return None, _error(f"candidate missing field(s): {', '.join(missing)}", 400)
    return {field: candidate[field] for field in _CANDIDATE_FIELDS}, None


def login_required(view):
    """Answers 401 unless the session is signed in (req 3)."""
    @functools.wraps(view)
    def wrapped(*args, **kwargs):
        if "username" not in session:
            return _error("authentication required", 401)
        return view(*args, **kwargs)
    return wrapped


def create_app(runtime: Runtime | None = None) -> Flask:
    """The Flask application over a runtime; the dve.ini runtime when none is given."""
    runtime = runtime or load_runtime()
    app = Flask(__name__)
    app.secret_key = config().api.secret_key
    app.permanent_session_lifetime = timedelta(seconds=config().api.session_lifetime)

    def sources():
        return runtime.connections.connected(session.get("conn_token"))

    def connected(source_type: SourceType, message: str):
        """Answers 401 until the session has connected the data source (req 7)."""
        def decorator(view):
            @functools.wraps(view)
            def wrapped(*args, **kwargs):
                if source_type not in sources():
                    return _error(message, 401)
                return view(*args, **kwargs)
            return wrapped
        return decorator

    config_db_required = connected(SourceType.CONFIG_MGMT_DB, "config management database connection required")
    source_repo_required = connected(SourceType.SOURCE_CODE_REPO, "source code repo connection required")

    def defaults():
        return {source_type.value: runtime.defaults[source_type].connection_address for source_type in SourceType}

    def catalog(key: str, read):
        """A configuration management database listing as {key: [...]}, or 502 (req 4)."""
        try:
            records = read(runtime.config_repo_factory(sources()[SourceType.CONFIG_MGMT_DB]))
        except ConfigManagementAccessError as exc:
            return _error(str(exc), 502)
        return jsonify({key: [record.to_dict() for record in records]})

    def produced_file(project_id, platform_id, version_id, run_id):
        """The Model Setup Data file of one run, or a 404 response (req 5)."""
        path = runtime.model_setup_data_store.resolve(project_id, platform_id, version_id, run_id)
        if path is None:
            return None, _error("model setup data file not found", 404)
        return path, None

    @app.route("/")
    def index():
        return render_template("index.html")

    @app.route("/api/login", methods=["POST"])
    def api_login():
        """Signs the session in through the directory service (req 3)."""
        body, error = _json_body(*_CREDENTIALS)
        if error:
            return error
        user = runtime.directory_service.authenticate(body["username"], body["password"])
        if user is None:
            return _error("invalid username or password", 401)
        session.permanent = True
        session["username"] = user.username
        session["role"] = user.role.value
        return jsonify({"username": user.username, "role": user.role.value, "defaults": defaults()})

    @app.route("/api/logout", methods=["POST"])
    def api_logout():
        """Ends the session and drops its data source connections."""
        runtime.connections.close(session.get("conn_token"))
        session.clear()
        return "", 204

    @app.route("/api/session")
    def api_session():
        """The session the UI resumes from: user, defaults and connected data sources (req 3, 7)."""
        if "username" not in session:
            return jsonify({"authenticated": False})
        connected_sources = sources()
        return jsonify({
            "authenticated": True,
            "username": session["username"],
            "role": session.get("role"),
            "defaults": defaults(),
            "config_mgmt_db_connected": SourceType.CONFIG_MGMT_DB in connected_sources,
            "source_code_repo_connected": SourceType.SOURCE_CODE_REPO in connected_sources,
        })

    @app.route("/api/data-sources/connect/<source>", methods=["POST"])
    @login_required
    def api_connect(source):
        """Connects one data source with the credentials in the body; a refused source answers 502 (req 4, 7)."""
        source_type = _CONNECT_SOURCES.get(source)
        if source_type is None:
            return _error("unknown data source", 404)
        body, error = _json_body(*_CONNECT_FIELDS)
        if error:
            return error
        token = runtime.connections.open(session.get("conn_token"))
        session["conn_token"] = token
        try:
            runtime.connections.connect(token, source_type, body["connection_address"], body["username"], body["password"])
        except (ConfigManagementAccessError, SourceRepoAccessError, SourceRepoAuthError) as exc:
            return _error(str(exc), 502)
        return jsonify({"connected": True})

    @app.route("/api/projects")
    @login_required
    @config_db_required
    def api_projects():
        """The projects (req 4)."""
        return catalog("projects", lambda repo: repo.list_projects())

    @app.route("/api/projects/<project_id>/platforms")
    @login_required
    @config_db_required
    def api_platforms(project_id):
        """The platforms of a project (req 4)."""
        return catalog("platforms", lambda repo: repo.list_platforms(project_id))

    @app.route("/api/projects/<project_id>/platforms/<platform_id>/versions")
    @login_required
    @config_db_required
    def api_versions(project_id, platform_id):
        """The system versions of a platform, the effective one marked (req 4)."""
        return catalog("versions", lambda repo: repo.list_versions(project_id, platform_id))

    @app.route("/api/projects/<project_id>/platforms/<platform_id>/versions/<version_id>/units")
    @login_required
    @config_db_required
    def api_units(project_id, platform_id, version_id):
        """The Software Unit Version Inventory of a selection (SRS DSM-MDG req 10)."""
        return catalog("units", lambda repo: repo.list_unit_versions(project_id, platform_id, version_id))

    @app.route("/api/units/<unit_name>/versions")
    @login_required
    @source_repo_required
    def api_unit_versions(unit_name):
        """The versions the source code repository publishes for a unit (SRS DSM-MDG req 11)."""
        source_repo = runtime.source_repo_factory(sources()[SourceType.SOURCE_CODE_REPO])
        try:
            versions = source_repo.list_versions(unit_name)
        except (SourceRepoAccessError, SourceRepoAuthError) as exc:
            return _error(str(exc), 502)
        return jsonify({"versions": versions})

    @app.route("/api/projects/<project_id>/platforms/<platform_id>/versions/<version_id>/mdg-files")
    @login_required
    @config_db_required
    def api_mdg_files(project_id, platform_id, version_id):
        """The Model Setup Data files produced for a selection, newest first (req 5)."""
        records = runtime.model_setup_data_store.list(project_id, platform_id, version_id)
        return jsonify({"files": [record.to_dict() for record in records]})

    @app.route("/api/projects/<project_id>/platforms/<platform_id>/versions/<version_id>/mdg-files/<run_id>/model")
    @login_required
    @config_db_required
    def api_mdg_file_model(project_id, platform_id, version_id, run_id):
        """One produced file, served inline (req 5)."""
        path, error = produced_file(project_id, platform_id, version_id, run_id)
        if error is not None:
            return error
        return send_file(path, mimetype="application/json", as_attachment=False)

    @app.route("/api/projects/<project_id>/platforms/<platform_id>/versions/<version_id>/mdg-files/<run_id>/download")
    @login_required
    @config_db_required
    def api_mdg_file_download(project_id, platform_id, version_id, run_id):
        """One produced file, served as an attachment under its own name (req 5)."""
        path, error = produced_file(project_id, platform_id, version_id, run_id)
        if error is not None:
            return error
        return send_file(path, mimetype="application/json", as_attachment=True, download_name=path.name)

    @app.route("/api/mdg/run", methods=["POST"])
    @login_required
    @config_db_required
    @source_repo_required
    def api_mdg_run():
        """Starts a Model Setup Data production for the selection and returns its task id (req 6)."""
        body, error = _json_body(*Selection.FIELDS)
        if error:
            return error
        candidate, error = _candidate(body)
        if error is not None:
            return error
        selection = Selection.from_dict(body)
        try:
            task_id = runtime.production_runner.start(
                selection, sources(), produced_by=session["username"], candidate=candidate
            )
        except Exception as exc:
            logger.warning("mdg/run: submission failed: %s", exc)
            return _error(str(exc), 502)
        return jsonify({"task_id": task_id}), 202

    @app.route("/api/mdg/tasks/<task_id>/cancel", methods=["POST"])
    @login_required
    def api_mdg_task_cancel(task_id):
        """Cancels a queued or running production (req 6)."""
        try:
            status = runtime.production_runner.cancel(task_id)
        except Exception as exc:
            logger.warning("mdg/tasks/%s: cancellation failed: %s", task_id, exc)
            return _error(str(exc), 502)
        return jsonify(status.to_dict())

    @app.route("/api/mdg/tasks/<task_id>")
    @login_required
    def api_mdg_task_state(task_id):
        """One poll of a production: its status plus the log lines after `after` (req 6, 8, 50)."""
        try:
            after = int(request.args.get("after"))
        except (TypeError, ValueError):
            after = -1
        try:
            status = runtime.production_runner.status(task_id)
            lines = runtime.production_log.lines_since(task_id, after + 1)
        except Exception as exc:
            logger.warning("mdg/tasks/%s: state read failed: %s", task_id, exc)
            return _error(str(exc), 502)
        return jsonify({**status.to_dict(), "lines": lines})

    return app


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    api = config().api
    print(f"DVE API on http://{api.host}:{api.port}", flush=True)
    create_app().run(host=api.host, port=api.port)


if __name__ == "__main__":
    main()
