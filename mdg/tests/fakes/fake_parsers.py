"""Recording fakes of the parser and build runner ports, sharing one `calls`
log so a test can assert the order the run invokes them in."""

from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Set, Tuple

from fakes import seed
from mdg.domain.source_data import RelationKind, Topic, UnitRelation
from mdg.ports.build_runner import IBuildRunner
from mdg.ports.source_code_parser import ISourceCodeParser
from mdg.ports.system_repo_parser import ISystemRepoParser
from mdg.ports.type_support_parser import ITypeSupportParser


class Calls:
    """The ordered (step, argument) log the fakes append to."""

    def __init__(self):
        self.log: List[Tuple[str, str]] = []

    def steps(self) -> List[str]:
        return [step for step, _ in self.log]


def system_repo_parser_class(calls: Calls, app_nodes: List[Tuple[str, str]] = None):
    """A fake ISystemRepoParser class the run constructs on the cloned system repo."""

    class FakeSystemRepoParser(ISystemRepoParser):
        def __init__(self, system_repo_dir: Path, project_name: str, platform_name: str):
            self.system_repo_dir = system_repo_dir
            self.project_name = project_name
            self.platform_name = platform_name
            calls.log.append(("system_repo_parser", str(system_repo_dir)))
            FakeSystemRepoParser.instances.append(self)

        def get_app_node_relation(self) -> List[Tuple[str, str]]:
            return list(app_nodes if app_nodes is not None else [(seed.NAV_APP, seed.NODE_0), (seed.SENSOR_APP, seed.NODE_1)])

        def get_app_role_relation(self) -> Dict[str, List[str]]:
            return {seed.NAV_APP: ["publisher", "subscriber"], seed.SENSOR_APP: ["publisher"]}

        def get_app_criticality_relation(self) -> Dict[str, bool]:
            return {}

    FakeSystemRepoParser.instances = []
    return FakeSystemRepoParser


class FakeSourceCodeParser(ISourceCodeParser):
    def __init__(self, calls: Calls):
        self._calls = calls

    def parse(self, unit_dir: Path, unit_name: str) -> List[UnitRelation]:
        self._calls.log.append(("parse", unit_name))
        return [UnitRelation(unit_name, seed.NAV_POSITION, RelationKind.PUBLISHES)]


def type_support_parser_class(calls: Calls):
    """A fake ITypeSupportParser class the run constructs on the run dir."""

    class FakeTypeSupportParser(ITypeSupportParser):
        def __init__(self, run_dir: Path):
            self.run_dir = run_dir
            calls.log.append(("type_support", str(run_dir)))

        def get_topic_list(self) -> Set[Topic]:
            return {Topic(seed.NAV_POSITION, size=1, durability="VOLATILE", reliability="RELIABLE", transport_priority="LOW")}

    return FakeTypeSupportParser


class FakeBuildRunner(IBuildRunner):
    def __init__(self, calls: Calls, available: bool = True):
        self._calls = calls
        self._available = available

    def ensure_available(self) -> None:
        self._calls.log.append(("ensure_available", ""))
        if not self._available:
            raise RuntimeError("gmake is not available")

    def regenerate_code(self, unit_dir: Path) -> None:
        self._calls.log.append(("regenerate_code", unit_dir.name))
