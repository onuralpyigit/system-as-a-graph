"""Build runner adapter running `gmake regenerate_code` in a unit's Makefile
directory (SRS DSM-MDG req 13, 19)."""

from __future__ import annotations

import logging
import subprocess
from pathlib import Path

from mdg.adapters.source_code.mandatory_files import MandatoryFiles
from mdg.ports.build_runner import IBuildRunner

logger = logging.getLogger(__name__)

TIMEOUT_SECONDS = 300


class GmakeBuildRunner(IBuildRunner):
    """Runs the regeneration build of the Makefile MandatoryFiles locates."""

    def __init__(self, files: MandatoryFiles):
        self._files = files

    def ensure_available(self) -> None:
        try:
            available = subprocess.run(["gmake", "--version"], capture_output=True, text=True).returncode == 0
        except OSError:
            available = False
        if not available:
            raise RuntimeError("gmake is not available but run_regenerate_code is on")

    def regenerate_code(self, unit_dir: Path) -> None:
        makefile = self._files.makefile(unit_dir)
        if makefile is None:
            return
        try:
            result = subprocess.run(
                ["gmake", "regenerate_code"], cwd=makefile.parent, capture_output=True, text=True, timeout=TIMEOUT_SECONDS
            )
            logger.info("build: gmake regenerate_code in %s exited %s", unit_dir.name, result.returncode)
        except (subprocess.TimeoutExpired, OSError) as exc:
            logger.error("build: gmake regenerate_code in %s failed: %s", makefile.parent, exc)
