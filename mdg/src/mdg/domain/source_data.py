"""Source data parsed from the acquired software units and the ansible repo:
the relationships a unit has with topics and libraries, topics with their QoS,
the nodes and their enrichment, networks and connects of the ansible repo
(SRS DSM-MDG req 2.4, 3, 19; DSM-SMM req 6-7)."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import ClassVar, Dict, List, Optional, Tuple


class RelationKind(Enum):
    """The relationship kinds the graph's relations pipeline carries: those a
    software unit source declares (DSM-SMM req 7) and the ansible repo's
    connects (SRS DSM-MDG req 2.4, 3)."""
    PUBLISHES = "publishes"
    SUBSCRIBES = "subscribes"
    USES = "uses"
    SEND = "send"
    RECEIVE = "receive"
    CONNECTS_TO = "connects_to"


@dataclass(frozen=True)
class UnitRelation:
    """One relationship from a software unit to a topic, a library or a message."""
    unit_name: str
    target: str
    kind: RelationKind


@dataclass(frozen=True)
class Topic:
    """A topic with its QoS parameters; equal to another topic of the same name."""
    name: str
    size: Optional[int] = None
    durability: Optional[str] = None
    reliability: Optional[str] = None
    transport_priority: Optional[str] = None

    _FREQUENCY_HZ: ClassVar[List[float]] = [
        1.0, 1.0, 5.0, 10.0, 10.0, 20.0, 20.0, 50.0,
        50.0, 100.0, 100.0, 150.0, 150.0, 200.0, 200.0, 200.0,
    ]
    _CRITICALITY: ClassVar[List[Tuple[float, str]]] = [
        (0.00, "minimal"), (0.19, "low"), (0.43, "medium"), (0.64, "high"), (1.00, "critical"),
    ]
    _RELIABILITY: ClassVar[Dict[str, float]] = {"BEST_EFFORT": 0.0, "RELIABLE": 1.0}
    _DURABILITY: ClassVar[Dict[str, float]] = {"VOLATILE": 0.0, "TRANSIENT_LOCAL": 0.5, "TRANSIENT": 0.6, "PERSISTENT": 1.0}
    _PRIORITY: ClassVar[Dict[str, float]] = {"LOW": 0.0, "MEDIUM": 0.33, "HIGH": 0.66, "URGENT": 1.0}

    def __hash__(self) -> int:
        return hash(self.name)

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Topic) and self.name == other.name

    def frequency(self) -> float:
        """The publishing frequency in Hz derived from reliability and transport priority."""
        score = self._RELIABILITY.get(self.reliability or "", 0.0) * self._PRIORITY.get(self.transport_priority or "", 0.0)
        index = min(int(score * len(self._FREQUENCY_HZ)), len(self._FREQUENCY_HZ) - 1)
        return self._FREQUENCY_HZ[index]

    def criticality(self) -> str:
        """The criticality label derived from durability, reliability and transport priority."""
        score = (
            0.30 * self._RELIABILITY.get(self.reliability or "", 0.0)
            + 0.40 * self._DURABILITY.get(self.durability or "", 0.0)
            + 0.30 * self._PRIORITY.get(self.transport_priority or "", 0.0)
        )
        return next(label for threshold, label in self._CRITICALITY if score <= threshold)


@dataclass(frozen=True)
class Message:
    """A message with its size and frequency; equal to another message of the same name.
    A message is sent or received by a unit via a UnitRelation of kind SEND/RECEIVE."""
    id: str
    name: str
    size: Optional[int] = None
    frequency: Optional[float] = None

    def __hash__(self) -> int:
        return hash(self.name)

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Message) and self.name == other.name


@dataclass(frozen=True)
class Node:
    """A node the ansible repo declares by name, with its enrichment; the
    graph merges these with the nodes the system repo names, so an ansible
    node the system repo omits is added (SRS DSM-MDG req 2.4, 3)."""
    name: str
    group: Optional[str] = None
    hw: Optional[str] = None
    os: Optional[str] = None
    mw: Optional[str] = None
    gpu: Optional[str] = None
    display: Optional[str] = None


@dataclass(frozen=True)
class Network:
    """A network the ansible repo declares (SRS DSM-MDG req 2.4, 3)."""
    name: str


@dataclass(frozen=True)
class ConnectsTo:
    """One connection between a node and a network with its device names and
    the bandwidth of that link in Gb/s, the relation record of kind
    CONNECTS_TO mirroring UnitRelation's role
    (SRS DSM-MDG req 2.4, 3; DSM-SMM req 7)."""
    from_name: str
    to_name: str
    kind: RelationKind = RelationKind.CONNECTS_TO
    device: Optional[str] = None
    dev_raw: Optional[str] = None
    bandwidth: Optional[float] = None
