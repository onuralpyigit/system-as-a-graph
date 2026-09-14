"""Source code parser adapter: topic publishes / subscribes from the unit's
topic manifest and library uses from its Java imports (SRS DSM-MDG req 13, 19)."""

from __future__ import annotations

import logging
import re
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import List, Set

from mdg.adapters.source_code.mandatory_files import MandatoryFiles
from mdg.config import SourceParserConfig
from mdg.domain.source_data import RelationKind, UnitRelation
from mdg.ports.source_code_parser import ISourceCodeParser

logger = logging.getLogger(__name__)

_ROLES = {
    "pub": [RelationKind.PUBLISHES],
    "sub": [RelationKind.SUBSCRIBES],
    "pubsub": [RelationKind.PUBLISHES, RelationKind.SUBSCRIBES],
}
_IMPORT = re.compile(r"^\s*import\s+(?:static\s+)?([^;]+);", re.MULTILINE)
_JAVA_COMMENT = re.compile(r"//.*?$|/\*.*?\*/", re.MULTILINE | re.DOTALL)


class SourceCodeParser(ISourceCodeParser):
    """Reads the manifest MandatoryFiles locates and every *.java file under the unit."""

    def __init__(self, config: SourceParserConfig, files: MandatoryFiles):
        self._config = config
        self._files = files
        self._dummy_topics = {name.lower() for name in config.dummy_topic_names}

    def parse(self, unit_dir: Path, unit_name: str) -> List[UnitRelation]:
        relations: List[UnitRelation] = []
        manifest = self._files.topic_manifest(unit_dir, unit_name)
        if manifest is not None:
            relations.extend(self._topics(manifest, unit_name))
        relations.extend(
            UnitRelation(unit_name, dependency, RelationKind.USES)
            for dependency in sorted(self._dependencies(unit_dir)) if dependency != unit_name
        )
        logger.info("parse: %s has %d relationship(s)", unit_name, len(relations))
        return relations

    def _topics(self, manifest: Path, unit_name: str) -> List[UnitRelation]:
        """Topic relations of <topic_element name="..." role="pub|sub|pubsub"/> elements."""
        try:
            root = ET.parse(manifest).getroot()
        except ET.ParseError as exc:
            logger.error("parse: invalid manifest %s: %s", manifest, exc)
            return []
        relations = []
        for element in root.iter(self._config.topic_element):
            name, role = element.get("name"), (element.get("role") or "").lower()
            if not name or role not in _ROLES or name.strip().lower() in self._dummy_topics:
                continue
            relations.extend(UnitRelation(unit_name, name, kind) for kind in _ROLES[role])
        return relations

    def _dependencies(self, unit_dir: Path) -> Set[str]:
        """Names of the imported packages under the domain prefix ending in a dependency suffix."""
        prefix = f"{self._config.import_domain_prefix}." if self._config.import_domain_prefix else None
        suffixes = tuple(self._config.dependency_suffixes)
        dependencies: Set[str] = set()
        if prefix is None:
            return dependencies
        for java_file in unit_dir.rglob("*.java"):
            try:
                content = _JAVA_COMMENT.sub("", java_file.read_text(encoding="utf-8"))
            except OSError as exc:
                logger.error("parse: cannot read %s: %s", java_file, exc)
                continue
            for target in _IMPORT.findall(content):
                target = target.strip()
                if not target.startswith(prefix):
                    continue
                name = target[len(prefix):].split(".", 1)[0].strip()
                if name and (not suffixes or name.endswith(suffixes)):
                    dependencies.add(name)
        return dependencies
