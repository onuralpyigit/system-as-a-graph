"""The files mandatory to obtain for a software unit and where they are found
under its cloned directory (SRS DSM-MDG req 15). The acquisition scan, the
source code parser and the build runner all locate files through this class."""

from __future__ import annotations

import logging
import re
from pathlib import Path
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

MAKEFILE = "Makefile"


class MandatoryFiles:
    """Locates a unit's Makefile and topic manifest anywhere under the unit
    directory; the Makefile must contain one of the configured include patterns."""

    _COMMENT = re.compile(r"#.*$", re.MULTILINE)

    def __init__(self, makefile_include_patterns: List[str]):
        self._patterns = makefile_include_patterns

    def expected(self, unit_name: str) -> List[str]:
        """The mandatory file names of a unit (req 15)."""
        return [MAKEFILE, self.manifest_name(unit_name)]

    @staticmethod
    def manifest_name(unit_name: str) -> str:
        return f"{unit_name}.xml"

    def locate(self, unit_dir: Path, unit_name: str) -> Dict[str, Optional[Path]]:
        """Each mandatory file name mapped to the path found, or None."""
        return {MAKEFILE: self.makefile(unit_dir), self.manifest_name(unit_name): self.topic_manifest(unit_dir, unit_name)}

    def makefile(self, unit_dir: Path) -> Optional[Path]:
        """The first Makefile under the unit directory whose non-comment content
        contains one of the include patterns."""
        for path in sorted(unit_dir.rglob(MAKEFILE)):
            try:
                content = path.read_text(encoding="utf-8")
            except OSError as exc:
                logger.error("mandatory files: cannot read %s: %s", path, exc)
                continue
            if self.has_valid_include(content):
                return path
        return None

    def topic_manifest(self, unit_dir: Path, unit_name: str) -> Optional[Path]:
        """The first <unit_name>.xml under the unit directory."""
        return next(iter(sorted(unit_dir.rglob(self.manifest_name(unit_name)))), None)

    def has_valid_include(self, content: str) -> bool:
        """Whether Makefile content contains one of the include patterns outside comments."""
        active = self._COMMENT.sub("", content)
        return any(pattern in active for pattern in self._patterns)
