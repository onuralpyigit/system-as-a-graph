"""Port for parsing the type support code of a run into topics with their QoS
(SRS DSM-MDG req 19)."""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Callable, Set

from mdg.domain.source_data import Topic


class ITypeSupportParser(ABC):
    """Answers the topics of one run directory. Implementations are constructed
    as (run_dir) once, after every unit is cloned and built."""

    @abstractmethod
    def get_topic_list(self) -> Set[Topic]:
        """The topics with QoS found under the run directory."""


TypeSupportParserFactory = Callable[[Path], ITypeSupportParser]
