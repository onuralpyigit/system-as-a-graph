"""Recording fakes of the parser and build runner ports, sharing one `calls`
log so a test can assert the order the run invokes them in."""

from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Set, Tuple

from fakes import seed
from mdg.domain.source_data import ConnectsTo, Message, Network, Node, RelationKind, Topic, UnitRelation
from mdg.ports.ansible_repo_parser import IAnsibleRepoParser
from mdg.ports.build_runner import IBuildRunner
from mdg.ports.message_file_parser import IMessageFileParser
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


def ansible_repo_parser_class(calls: Calls):
    """A fake IAnsibleRepoParser class the run constructs on the cloned ansible
    repo; its connects include one to an undeclared network for the drop test."""

    class FakeAnsibleRepoParser(IAnsibleRepoParser):
        def __init__(self, ansible_repo_dir: Path, project_name: str, platform_name: str):
            self.ansible_repo_dir = ansible_repo_dir
            self.project_name = project_name
            self.platform_name = platform_name
            calls.log.append(("ansible_repo_parser", str(ansible_repo_dir)))
            FakeAnsibleRepoParser.instances.append(self)

        def get_nodes(self):
            return [
                Node(seed.NODE_0, group="processors", hw="x86-64/8c", os="Linux 5.15", mw="DDS", gpu="none", display="none"),
                Node(seed.NODE_1, group="processors", hw="x86-64/4c", os="Linux 5.15", mw="DDS", gpu="integrated", display="hdmi"),
            ]

        def get_networks(self):
            return [Network(seed.SWITCH_0)]

        def get_connects_to(self):
            return [
                ConnectsTo(seed.NODE_0, seed.SWITCH_0, device="eth0", dev_raw="ens1f0", bandwidth=1.0),
                ConnectsTo(seed.NODE_1, seed.SWITCH_0, device="eth0", dev_raw="ens1f0", bandwidth=1.0),
                ConnectsTo(seed.NODE_0, seed.GHOST_SWITCH, device="eth1", dev_raw="ens1f1", bandwidth=0.1),
            ]

    FakeAnsibleRepoParser.instances = []
    return FakeAnsibleRepoParser


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


def message_file_parser_class(calls: Calls):
    """A fake IMessageFileParser class the run constructs on the run dir."""

    class FakeMessageFileParser(IMessageFileParser):
        def __init__(self, run_dir: Path):
            self.run_dir = run_dir
            calls.log.append(("messages", str(run_dir)))

        def get_message_list(self) -> Set[Message]:
            return {Message("MSG-001", seed.MSG_NAV_POSITION, size=6138, frequency=20.0)}

        def get_message_relations(self) -> List[UnitRelation]:
            return [UnitRelation(seed.NAV_APP, seed.MSG_NAV_POSITION, RelationKind.SEND)]

    return FakeMessageFileParser


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
