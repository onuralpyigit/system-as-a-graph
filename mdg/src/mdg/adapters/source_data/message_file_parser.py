"""Mock: the message file parser over the run directory, answering with the
dev seed's messages and their send or receive relationships to units
(SRS DSM-MDG req 19; DSM-SMM req 6-7)."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import List, Set

from mdg.domain.source_data import Message, RelationKind, UnitRelation
from mdg.ports.message_file_parser import IMessageFileParser

logger = logging.getLogger(__name__)


class MessageFileParser(IMessageFileParser):
    """Mock: constructed on the run directory once every unit is cloned and
    built; the getters return fixed data."""

    def __init__(self, run_dir: Path):
        self.run_dir = run_dir
        logger.info("message file: parsing run %s", run_dir.name)

    def get_message_list(self) -> Set[Message]:
        return {
            Message("MSG-001", "nav_position_msg", size=6138, frequency=20.0),
            Message("MSG-002", "sensor_data_msg", size=1207, frequency=100.0),
        }

    def get_message_relations(self) -> List[UnitRelation]:
        return [
            UnitRelation("nav_app", "nav_position_msg", RelationKind.SEND),
            UnitRelation("sensor_app", "nav_position_msg", RelationKind.RECEIVE),
            UnitRelation("sensor_app", "sensor_data_msg", RelationKind.SEND),
            UnitRelation("nav_app", "sensor_data_msg", RelationKind.RECEIVE),
        ]
