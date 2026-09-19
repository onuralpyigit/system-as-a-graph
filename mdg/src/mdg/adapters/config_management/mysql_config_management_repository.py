"""MySQL adapter of the configuration management database port, over the
schema in dev/mysql/init.sql (SRS DSM-MDG req 2.1, 6-12)."""

from __future__ import annotations

from typing import List, Optional

import pymysql
import pymysql.cursors

from mdg.domain.data_source import DataSourceConfig
from mdg.domain.inventory import SoftwareUnitVersion
from mdg.domain.project_context import PlatformRecord, ProjectRecord, VersionRecord
from mdg.domain.system_hierarchy import SystemHierarchyRecord
from mdg.ports.config_management_repository import ConfigManagementAccessError, IConfigManagementRepository


class MysqlConfigManagementRepository(IConfigManagementRepository):
    """Reads platform_pkg_version, platform_current_atm_version and
    csu_csms_relation; project, platform and version ids are their names."""

    def __init__(self, host: str, port: int, user: str, password: str, database: str):
        self._connection = dict(host=host, port=port, user=user, password=password, database=database)

    @classmethod
    def from_data_source_config(cls, source: DataSourceConfig) -> "MysqlConfigManagementRepository":
        """Builds the repository from a "<host>:<port>/<database>" address and
        "<user>:<password>" user information (req 4)."""
        address, _, database = source.connection_address.partition("/")
        host, _, port = address.partition(":")
        user, _, password = source.user_info.partition(":")
        return cls(host=host, port=int(port or 3306), user=user, password=password, database=database)

    def list_projects(self) -> List[ProjectRecord]:
        rows = self._query("SELECT DISTINCT project_name FROM platform_pkg_version ORDER BY project_name")
        return [ProjectRecord(row["project_name"], row["project_name"]) for row in rows]

    def list_platforms(self, project_id: str) -> List[PlatformRecord]:
        rows = self._query(
            "SELECT DISTINCT platform_name FROM platform_pkg_version WHERE project_name = %s ORDER BY platform_name",
            (project_id,),
        )
        return [PlatformRecord(row["platform_name"], project_id, row["platform_name"]) for row in rows]

    def list_versions(self, project_id: str, platform_id: str) -> List[VersionRecord]:
        rows = self._query(
            "SELECT DISTINCT atm_version FROM platform_pkg_version "
            "WHERE project_name = %s AND platform_name = %s ORDER BY atm_version",
            (project_id, platform_id),
        )
        effective = {row["atm_version"] for row in self._query(
            "SELECT atm_version FROM platform_current_atm_version WHERE project_name = %s AND platform_name = %s",
            (project_id, platform_id),
        )}
        return [
            VersionRecord(row["atm_version"], project_id, platform_id, row["atm_version"], row["atm_version"] in effective)
            for row in rows
        ]

    def list_unit_versions(self, project_id: str, platform_id: str, version_id: str) -> List[SoftwareUnitVersion]:
        rows = self._query(
            "SELECT pkg_name, pkg_version FROM platform_pkg_version "
            "WHERE project_name = %s AND platform_name = %s AND atm_version = %s ORDER BY pkg_name",
            (project_id, platform_id, version_id),
        )
        return [SoftwareUnitVersion(row["pkg_name"], row["pkg_version"]) for row in rows]

    def get_system_hierarchy(self, unit_name: str) -> Optional[SystemHierarchyRecord]:
        rows = self._query(
            "SELECT csu_name, csc_name, csci_name, css_name, csms_name, csu_description "
            "FROM csu_csms_relation WHERE csu_name = %s",
            (unit_name,),
        )
        return SystemHierarchyRecord(**rows[0]) if rows else None

    def _query(self, sql: str, args: tuple = ()) -> list:
        """Runs one query; any MySQL failure raises ConfigManagementAccessError (req 12)."""
        try:
            with pymysql.connect(cursorclass=pymysql.cursors.DictCursor, connect_timeout=5, **self._connection) as conn:
                with conn.cursor() as cursor:
                    cursor.execute(sql, args)
                    return list(cursor.fetchall())
        except pymysql.MySQLError as exc:
            raise ConfigManagementAccessError(f"Configuration management database failure: {exc}") from exc
