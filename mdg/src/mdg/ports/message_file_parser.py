"""Port for parsing the message file of a run into messages and their send or
receive relationships to units (SRS DSM-MDG req 19; DSM-SMM req 6-7)."""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Callable, List, Set

from mdg.domain.source_data import Message, UnitRelation


class IMessageFileParser(ABC):
    """Answers the messages of one run directory. Implementations are
    constructed as (run_dir) once, after every unit is cloned and built."""

    @abstractmethod
    def get_message_list(self) -> Set[Message]:
        """The messages found under the run directory."""

    @abstractmethod
    def get_message_relations(self) -> List[UnitRelation]:
        """The send / receive relationships of each message to a unit."""


MessageFileParserFactory = Callable[[Path], IMessageFileParser]
