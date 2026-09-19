"""Loads mdg.ini: the workspace and system repo name, the mandatory file rules,
the source parser settings and the build switch (SRS DSM-MDG req 3, 13, 15, 19)."""

from __future__ import annotations

import configparser
from dataclasses import dataclass, field
from pathlib import Path
from typing import List

MDG_INI = Path(__file__).resolve().parent / "mdg.ini"
PACKAGE_DIR = Path(__file__).resolve().parent


@dataclass(frozen=True)
class WorkspaceConfig:
    """Where runs are written and which inventory entry is the system repo."""
    path: str = "workspace"
    system_repo: str = "system_repo"

    def root(self) -> Path:
        """The workspace root, relative to the mdg package directory unless absolute."""
        path = Path(self.path)
        return path if path.is_absolute() else PACKAGE_DIR / path


@dataclass(frozen=True)
class MandatoryFilesConfig:
    """The include patterns a Makefile must contain to count as found (req 15)."""
    makefile_include_patterns: List[str] = field(default_factory=list)


@dataclass(frozen=True)
class SourceParserConfig:
    """What the source code parser skips, which imports count as dependencies
    and which XML element declares a topic (req 19)."""
    dummy_topic_names: List[str] = field(default_factory=list)
    import_domain_prefix: str = ""
    dependency_suffixes: List[str] = field(default_factory=list)
    topic_element: str = "topic"


@dataclass(frozen=True)
class BuildConfig:
    """Whether gmake regenerate_code runs in each unit before parsing."""
    run_regenerate_code: bool = False


@dataclass(frozen=True)
class Config:
    workspace: WorkspaceConfig = field(default_factory=WorkspaceConfig)
    mandatory_files: MandatoryFilesConfig = field(default_factory=MandatoryFilesConfig)
    source_parser: SourceParserConfig = field(default_factory=SourceParserConfig)
    build: BuildConfig = field(default_factory=BuildConfig)


def load(path: Path = MDG_INI) -> Config:
    """The configuration in an ini file; a missing file or option yields its default."""
    ini = configparser.ConfigParser(interpolation=None)
    ini.read(path, encoding="utf-8")

    def text(section: str, option: str, default: str) -> str:
        return ini.get(section, option, fallback=default).strip() or default

    def items(section: str, option: str) -> List[str]:
        return [item.strip() for item in ini.get(section, option, fallback="").split(",") if item.strip()]

    return Config(
        workspace=WorkspaceConfig(
            path=text("workspace", "path", WorkspaceConfig.path),
            system_repo=text("workspace", "system_repo", WorkspaceConfig.system_repo),
        ),
        mandatory_files=MandatoryFilesConfig(
            makefile_include_patterns=items("mandatory_files", "makefile_include_patterns"),
        ),
        source_parser=SourceParserConfig(
            dummy_topic_names=items("source_parser", "dummy_topic_names"),
            import_domain_prefix=text("source_parser", "import_domain_prefix", ""),
            dependency_suffixes=items("source_parser", "dependency_suffixes"),
            topic_element=text("source_parser", "topic_element", SourceParserConfig.topic_element),
        ),
        build=BuildConfig(run_regenerate_code=ini.getboolean("build", "run_regenerate_code", fallback=False)),
    )
