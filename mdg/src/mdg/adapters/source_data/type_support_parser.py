"""Mock: the type support parser over the run directory, answering with the
dev seed's topics and placeholder QoS (SRS DSM-MDG req 19)."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Set

from mdg.domain.source_data import Topic
from mdg.ports.type_support_parser import ITypeSupportParser

logger = logging.getLogger(__name__)


class TypeSupportParser(ITypeSupportParser):
    """Mock: constructed on the run directory once every unit is cloned and
    built; the getter returns fixed data."""

    def __init__(self, run_dir: Path):
        self.run_dir = run_dir
        logger.info("type support: parsing run %s", run_dir.name)

    def get_topic_list(self) -> Set[Topic]:
        return {
            Topic("nav_position", size=6138, durability="PERSISTENT", reliability="BEST_EFFORT", transport_priority="LOW"),
            Topic("sensor_data", size=1207, durability="TRANSIENT", reliability="BEST_EFFORT", transport_priority="MEDIUM"),
        }
