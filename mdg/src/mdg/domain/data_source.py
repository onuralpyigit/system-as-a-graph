"""The external data sources DSM-MDG reads and their user-definable connection
information (SRS DSM-MDG req 2, 4)."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict


class SourceType(Enum):
    """The data source categories DSM-MDG accesses (req 2)."""
    CONFIG_MGMT_DB = "config_mgmt_db"
    SOURCE_CODE_REPO = "source_code_repo"


@dataclass(frozen=True)
class DataSourceConfig:
    """Source type, name, access method, connection address and user information
    of one data source (req 4)."""
    source_type: SourceType
    source_name: str
    access_method: str
    connection_address: str
    user_info: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "source_type": self.source_type.value,
            "source_name": self.source_name,
            "access_method": self.access_method,
            "connection_address": self.connection_address,
            "user_info": self.user_info,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DataSourceConfig":
        return cls(
            source_type=SourceType(data["source_type"]),
            source_name=data["source_name"],
            access_method=data["access_method"],
            connection_address=data["connection_address"],
            user_info=data["user_info"],
        )
