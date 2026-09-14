"""The node-relationship graph of the Model Setup Data: processor units,
topics, applications, libraries and the runs_on / publishes_to /
subscribes_to / uses relationships between them (SRS DSM-MDG req 19;
DSM-SMM req 6-7)."""

from __future__ import annotations

import random
from typing import Any, Dict, Iterable, List, Optional, Tuple

from mdg.domain.inventory import SoftwareUnitVersionInventory
from mdg.domain.source_data import RelationKind, Topic, UnitRelation
from mdg.domain.system_hierarchy import SystemHierarchyRecord

NOT_FOUND = "NOT_FOUND"


class ModelSetupDataGraph:
    """Builds the graph payload from the parsed source data and the inventory."""

    _PRIORITIES = ["LOW", "MEDIUM", "HIGH"]
    _HOTSTANDBY = [False, True]

    @classmethod
    def build(
        cls,
        app_node_relations: List[Tuple[str, str]],
        app_roles: Dict[str, List[str]],
        app_criticality: Dict[str, bool],
        relations: List[UnitRelation],
        topics: Iterable[Topic],
        inventory: SoftwareUnitVersionInventory,
        hierarchy_by_unit: Dict[str, Optional[SystemHierarchyRecord]],
    ) -> Dict[str, Any]:
        """The graph of one run (req 19)."""
        versions = {u.unit_name: u.version for u in inventory.units}
        node_ids = cls._ids("N", [node for _, node in app_node_relations if node and node != NOT_FOUND])
        app_ids = cls._ids("A", [app for app, _ in app_node_relations])
        lib_ids = cls._ids("L", [
            r.target for r in relations
            if r.kind is RelationKind.USES and r.unit_name in app_ids and r.target not in app_ids
        ])
        topics_by_name = {t.name: t for t in topics}
        topic_ids = cls._ids("T", list(topics_by_name))

        publishes_to, subscribes_to, uses = [], [], []
        for relation in relations:
            source = app_ids.get(relation.unit_name) or lib_ids.get(relation.unit_name)
            if source is None:
                continue
            if relation.kind is RelationKind.USES:
                target = lib_ids.get(relation.target) or app_ids.get(relation.target)
                if target is not None:
                    uses.append({"from": source, "to": target})
            elif relation.target in topic_ids:
                edges = publishes_to if relation.kind is RelationKind.PUBLISHES else subscribes_to
                edges.append({"from": source, "to": topic_ids[relation.target]})

        applications = [cls._application(name, app_ids[name], versions, app_roles, app_criticality, hierarchy_by_unit)
                        for name in app_ids]
        libraries = [{"id": lib_ids[name], "name": name, "version": versions.get(name, NOT_FOUND),
                      "system_hierarchy": cls._hierarchy(hierarchy_by_unit.get(name))} for name in lib_ids]
        nodes = [{"id": node_ids[name], "name": name} for name in node_ids]
        topic_payload = [cls._topic(topics_by_name[name], topic_ids[name]) for name in topic_ids]

        return {
            "metadata": {"scale": {"apps": len(applications), "topics": len(topic_payload),
                                   "nodes": len(nodes), "libraries": len(libraries)}},
            "nodes": nodes,
            "topics": topic_payload,
            "applications": applications,
            "libraries": libraries,
            "relationships": {
                "runs_on": [{"from": app_ids[app], "to": node_ids[node]}
                            for app, node in app_node_relations if node in node_ids],
                "publishes_to": publishes_to,
                "subscribes_to": subscribes_to,
                "uses": uses,
            },
        }

    @staticmethod
    def _ids(prefix: str, names: List[str]) -> Dict[str, str]:
        return {name: f"{prefix}{i}" for i, name in enumerate(sorted(set(names)))}

    @classmethod
    def _application(cls, name, app_id, versions, app_roles, app_criticality, hierarchy_by_unit) -> Dict[str, Any]:
        rng = random.Random(name)
        return {
            "id": app_id,
            "name": name,
            "version": versions.get(name, NOT_FOUND),
            "role": list(app_roles.get(name, [NOT_FOUND])),
            "criticality": bool(app_criticality.get(name, False)),
            "priority": rng.choice(cls._PRIORITIES),
            "hotstandby": rng.choice(cls._HOTSTANDBY),
            "system_hierarchy": cls._hierarchy(hierarchy_by_unit.get(name)),
        }

    @staticmethod
    def _topic(topic: Topic, topic_id: str) -> Dict[str, Any]:
        return {
            "id": topic_id,
            "name": topic.name,
            "size": topic.size if topic.size is not None else -1,
            "qos": {
                "durability": topic.durability or NOT_FOUND,
                "reliability": topic.reliability or NOT_FOUND,
                "transport_priority": topic.transport_priority or NOT_FOUND,
            },
            "frequency": topic.frequency(),
            "criticality": topic.criticality(),
        }

    @staticmethod
    def _hierarchy(record: Optional[SystemHierarchyRecord]) -> Dict[str, str]:
        if record is None:
            return {key: NOT_FOUND for key in ("csc_name", "csci_name", "css_name", "csms_name", "csu_description")}
        return record.to_dict()
