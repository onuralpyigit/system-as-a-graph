"""The MySQL adapter: data source parsing and the error mapping of
connection and query failures (SRS DSM-MDG req 4, 12)."""

import pymysql
import pytest

from fakes import seed
from mdg.adapters.config_management.mysql_config_management_repository import MysqlConfigManagementRepository
from mdg.domain.data_source import DataSourceConfig, SourceType
from mdg.ports.config_management_repository import ConfigManagementAccessError


def _repository() -> MysqlConfigManagementRepository:
    source = DataSourceConfig(SourceType.CONFIG_MGMT_DB, "mysql", "mysql", seed.CONFIG_DB_ADDRESS, seed.CREDENTIALS)
    return MysqlConfigManagementRepository.from_data_source_config(source)


def test_data_source_address_and_user_info_are_split():
    assert _repository()._connection == {
        "host": "localhost", "port": 3306, "user": "dsm", "password": "dsm", "database": "cmdb",
    }


def test_connection_failure_maps_to_config_management_access_error(monkeypatch):
    def connect(**kwargs):
        raise pymysql.err.OperationalError(2003, "Can't connect to MySQL server")

    monkeypatch.setattr(pymysql, "connect", connect)

    with pytest.raises(ConfigManagementAccessError, match="Can't connect"):
        _repository().list_projects()


def test_query_failure_maps_to_config_management_access_error(monkeypatch):
    class Cursor:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def execute(self, sql, args=None):
            raise pymysql.err.ProgrammingError(1146, "Table 'cmdb.csu_csms_relation' doesn't exist")

    class Connection:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def cursor(self):
            return Cursor()

    monkeypatch.setattr(pymysql, "connect", lambda **kwargs: Connection())

    with pytest.raises(ConfigManagementAccessError, match="doesn't exist"):
        _repository().get_system_hierarchy(seed.NAV_APP)
