"""The dev seed's names (dev/mysql/init.sql, dev/gitea/seed, dve.ini) as test constants."""

from mdg import DataSourceConfig, SourceType

PROJECT = "skywatch"
PLATFORM = "nftw"
VERSION = "1.0.0"
OLD_VERSION = "0.9.0"
NAV_APP = "nav_app"
SENSOR_APP = "sensor_app"
COMMON_LIB = "common_lib"
SYSTEM_REPO = "system_repo"
CANDIDATE_VERSION = "1.0.3"
ADMIN = "admin"
OPERATOR = "operator"
USER = "dsm"
PASSWORD = "dsm"  # NOSONAR dev-stack stand-in from dev/compose.yaml, not a real credential
CONFIG_DB_ADDRESS = "localhost:3306/cmdb"
SOURCE_REPO_URL = "http://localhost:3000/dsm-src"
RUN_1 = "run-1"
RUN_2 = "run-2"
FILE_NAME = f"{PROJECT}_{PLATFORM}_{VERSION}.json"

SELECTION = {"project_id": PROJECT, "platform_id": PLATFORM, "version_id": VERSION}
CANDIDATE = {"unit_name": SENSOR_APP, "version": CANDIDATE_VERSION}
CANDIDATES = [CANDIDATE]
UNIT_VERSIONS = {SENSOR_APP: [CANDIDATE_VERSION, "1.0.1", VERSION]}

DEFAULTS = {
    SourceType.CONFIG_MGMT_DB: DataSourceConfig(SourceType.CONFIG_MGMT_DB, "mysql", "mysql", CONFIG_DB_ADDRESS, ""),
    SourceType.SOURCE_CODE_REPO: DataSourceConfig(SourceType.SOURCE_CODE_REPO, "gitea", "git", SOURCE_REPO_URL, ""),
}


def context(selection: dict = SELECTION) -> dict:
    """The context a Model Setup Data file of a selection carries."""
    project, platform, version = selection["project_id"], selection["platform_id"], selection["version_id"]
    return {
        "project": {"project_id": project, "name": project},
        "platform": {"platform_id": platform, "project_id": project, "name": platform},
        "version": {
            "version_id": version, "project_id": project, "platform_id": platform,
            "label": version, "is_effective": True,
        },
    }


def file_payload(
    generated_at: str = "2026-09-02T14:15:30", produced_by: str = OPERATOR, scale: dict = None, context: dict = None
) -> dict:
    """A produced Model Setup Data file's header, as the store lists it."""
    return {
        "context": context or {}, "inventory": {"units": []}, "acquired_files": [], "errors": [],
        "generated_at": generated_at, "produced_by": produced_by,
        "graph": {"metadata": {"scale": scale or {"apps": 2}}},
    }


def files_url(run_id: str = None, suffix: str = "", selection: dict = SELECTION) -> str:
    """The mdg-files URL of a selection, or of one of its files."""
    base = (
        f"/api/projects/{selection['project_id']}/platforms/{selection['platform_id']}"
        f"/versions/{selection['version_id']}/mdg-files"
    )
    return f"{base}/{run_id}{suffix}" if run_id else base
