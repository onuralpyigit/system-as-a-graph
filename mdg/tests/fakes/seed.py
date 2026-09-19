"""The dev seed's names (dev/mysql/init.sql, dev/gitea/seed) as test constants."""

from mdg.domain.inventory import SoftwareUnitVersion
from mdg.domain.project_context import PlatformRecord, ProjectContext, ProjectRecord, VersionRecord

PROJECT = "skywatch"
PLATFORM = "nftw"
VERSION = "1.0.0"
OLD_VERSION = "0.9.0"
SYSTEM_REPO = "system_repo"
NAV_APP = "nav_app"
SENSOR_APP = "sensor_app"
COMMON_LIB = "common_lib"
NAV_POSITION = "nav_position"
SENSOR_DATA = "sensor_data"
NODE_0 = "Node-0"
NODE_1 = "Node-1"
IMPORT_PREFIX = "a.b.c"
DEPENDENCY_SUFFIX = "_lib"
MAKEFILE_INCLUDE = "include/Makefile_java.mk"
CANDIDATE_VERSION = "1.0.3"
PRODUCER = "operator"
RUN_1 = "run-1"
RUN_2 = "run-2"
SOURCE_REPO_URL = "http://localhost:3000/dsm-src"
CONFIG_DB_ADDRESS = "localhost:3306/cmdb"
CREDENTIALS = "dsm:dsm"

VALID_MAKEFILE = f"include {MAKEFILE_INCLUDE}\n\n.PHONY: regenerate_code\nregenerate_code:\n\t@echo no-op\n"
NAV_APP_MANIFEST = f'<unit><topic name="{NAV_POSITION}" role="pub"/><topic name="{SENSOR_DATA}" role="sub"/></unit>'
SENSOR_APP_MANIFEST = f'<unit><topic name="{SENSOR_DATA}" role="pub"/></unit>'
NAV_APP_JAVA = f"package {IMPORT_PREFIX}.{NAV_APP};\n\nimport {IMPORT_PREFIX}.{COMMON_LIB}.Utils;\n\npublic class NavApp {{}}\n"

CONTEXT = ProjectContext(
    project=ProjectRecord(PROJECT, PROJECT),
    platform=PlatformRecord(PLATFORM, PROJECT, PLATFORM),
    version=VersionRecord(VERSION, PROJECT, PLATFORM, VERSION, is_effective=True),
)


def inventory_rows(version: str = VERSION):
    """The platform_pkg_version rows of one system version, as the database yields them."""
    return [
        SoftwareUnitVersion(COMMON_LIB, version),
        SoftwareUnitVersion(NAV_APP, version),
        SoftwareUnitVersion(SENSOR_APP, version),
        SoftwareUnitVersion(SYSTEM_REPO, version),
    ]
