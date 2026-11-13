"""Produces the Model Setup Data of one run: acquires the context, the
inventory, the system repo and the ansible repo (both cloned without the unit
file rule) and parses them, clones and parses the software units the system
repo names, merges the ansible repo's connects into the relations, and saves
the file (SRS DSM-MDG req 2.4, 3, 5-19)."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple, Union

from mdg.domain.data_source import SourceType
from mdg.domain.error_record import DataAcquisitionError, ErrorRecord, ErrorStatus
from mdg.domain.inventory import CandidateUnitVersion, SoftwareUnitVersion
from mdg.domain.model_setup_data import ModelSetupData, UnitStatus
from mdg.domain.model_setup_data_graph import ModelSetupDataGraph
from mdg.domain.source_data import ConnectsTo, UnitRelation
from mdg.domain.workspace import Workspace
from mdg.ports.ansible_repo_parser import AnsibleRepoParserFactory
from mdg.ports.build_runner import IBuildRunner
from mdg.ports.config_management_repository import IConfigManagementRepository
from mdg.ports.message_file_parser import MessageFileParserFactory
from mdg.ports.model_setup_data_store import IModelSetupDataStore
from mdg.ports.source_code_parser import ISourceCodeParser
from mdg.ports.system_repo_parser import SystemRepoParserFactory
from mdg.ports.type_support_parser import TypeSupportParserFactory
from mdg.services.acquire_project_context import AcquireProjectContext
from mdg.services.acquire_source_code import AcquireSourceCode, Acquisition
from mdg.services.build_software_unit_inventory import BuildSoftwareUnitInventory
from mdg.services.check_mandatory_fields import CheckMandatoryFields

logger = logging.getLogger(__name__)

ProgressCallback = Callable[[int, str], None]


@dataclass(frozen=True)
class ProductionResult:
    """The outcome of one run: the file saved, each inventory unit's status,
    the graph scale, how many files were acquired, the candidates and the
    errors recorded."""
    run_id: str
    file: Path
    units: List[Tuple[SoftwareUnitVersion, UnitStatus]]
    scale: Dict[str, int]
    acquired_files: int
    candidates: List[CandidateUnitVersion]
    errors: List[ErrorRecord]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "run_id": self.run_id,
            "file": str(self.file),
            "units": [{**unit.to_dict(), "status": status.value} for unit, status in self.units],
            "scale": self.scale,
            "acquired_files": self.acquired_files,
            "candidates": [candidate.to_dict() for candidate in self.candidates],
            "errors": [e.to_dict() for e in self.errors],
        }


class _Progress:
    """Counts the run's work units and reports the percent done with the phase name."""

    def __init__(self, report: Optional[ProgressCallback], total: int):
        self._report = report
        self._total = total
        self._done = 0

    def advance(self, phase: str) -> None:
        self._done += 1
        if self._report is not None:
            self._report(min(100, 100 * self._done // self._total), phase)

    def retotal(self, total: int) -> None:
        """Corrects the total once the work is known; the percent never falls back."""
        self._total = max(total, self._done)


class ProduceModelSetupData:
    """Runs the production process in a run directory keyed by run id and
    returns the ProductionResult; a failure to acquire the context, the
    system repo or the ansible repo raises DataAcquisitionError (req 12)."""

    def __init__(
        self,
        config_repo: IConfigManagementRepository,
        acquire_context: AcquireProjectContext,
        build_inventory: BuildSoftwareUnitInventory,
        acquire_source_code: AcquireSourceCode,
        system_repo_parser: SystemRepoParserFactory,
        ansible_repo_parser: AnsibleRepoParserFactory,
        source_code_parser: ISourceCodeParser,
        type_support_parser: TypeSupportParserFactory,
        message_file_parser: MessageFileParserFactory,
        build_runner: IBuildRunner,
        check_mandatory_fields: CheckMandatoryFields,
        store: IModelSetupDataStore,
        workspace: Workspace,
        system_repo_name: str,
        ansible_repo_name: str,
        run_regenerate_code: bool = False,
    ):
        self._config_repo = config_repo
        self._acquire_context = acquire_context
        self._build_inventory = build_inventory
        self._acquire = acquire_source_code
        self._system_repo_parser = system_repo_parser
        self._ansible_repo_parser = ansible_repo_parser
        self._source_code_parser = source_code_parser
        self._type_support_parser = type_support_parser
        self._message_file_parser = message_file_parser
        self._build_runner = build_runner
        self._check = check_mandatory_fields
        self._store = store
        self._workspace = workspace
        self._system_repo_name = system_repo_name
        self._ansible_repo_name = ansible_repo_name
        self._run_regenerate_code = run_regenerate_code

    def execute(
        self,
        project_id: str,
        platform_id: str,
        version_id: str,
        run_id: str,
        produced_by: Optional[str] = None,
        candidates: Sequence[CandidateUnitVersion] = (),
        progress: Optional[ProgressCallback] = None,
    ) -> ProductionResult:
        if self._run_regenerate_code:
            self._build_runner.ensure_available()
        context = self._acquire_context.execute(project_id, platform_id, version_id)
        inventory = self._build_inventory.execute(context, candidates)
        run_dir = self._workspace.run_dir(project_id, platform_id, version_id, run_id)
        run_dir.mkdir(parents=True, exist_ok=True)
        logger.info("produce: %s/%s/%s run %s", project_id, platform_id, version_id, run_id)

        system_unit = inventory.find(self._system_repo_name)
        if system_unit is None:
            raise DataAcquisitionError(self._missing(f"system repo '{self._system_repo_name}' is not in the inventory", self._system_repo_name, context))
        inventory = inventory.without(system_unit.unit_name)
        ansible_unit = inventory.find(self._ansible_repo_name)
        if ansible_unit is None:
            raise DataAcquisitionError(self._missing(f"ansible repo '{self._ansible_repo_name}' is not in the inventory", self._ansible_repo_name, context))
        inventory = inventory.without(ansible_unit.unit_name)
        # Context, the system repo and the ansible repo cloned and parsed, every unit
        # cloned and parsed, and the file saved; the inventory bounds the units until
        # the system repo names them.
        steps = _Progress(progress, total=6 + 2 * len(inventory.units))
        steps.advance("context")
        system = self._acquire.execute(system_unit, run_dir, context, mandatory=False)
        if system.unit_dir is None:
            raise DataAcquisitionError(system.errors[0])
        steps.advance("system")
        parser = self._system_repo_parser(system.unit_dir, context.project.name, context.platform.name)
        app_node_relations = parser.get_app_node_relation()
        steps.advance("system")
        ansible = self._acquire.execute(ansible_unit, run_dir, context, mandatory=False)
        if ansible.unit_dir is None:
            raise DataAcquisitionError(ansible.errors[0])
        steps.advance("ansible")
        ansible_parser = self._ansible_repo_parser(ansible.unit_dir, context.project.name, context.platform.name)
        ansible_nodes, ansible_networks = ansible_parser.get_nodes(), ansible_parser.get_networks()
        ansible_connects = ansible_parser.get_connects_to()
        steps.advance("ansible")

        files, errors = [*system.files, *ansible.files], [*system.errors, *ansible.errors]
        units: List[SoftwareUnitVersion] = []
        for app_name in dict.fromkeys(app for app, _ in app_node_relations):
            unit = inventory.find(app_name)
            if unit is None:
                errors.append(self._missing(f"application '{app_name}' is not in the inventory", app_name, context))
            else:
                units.append(unit)
        steps.retotal(6 + 2 * len(units))

        acquisitions: List[Acquisition] = []
        for unit in units:
            acquisition = self._acquire.execute(unit, run_dir, context)
            acquisitions.append(acquisition)
            files.extend(acquisition.files)
            errors.extend(acquisition.errors)
            steps.advance("clone")

        relations = []
        for acquisition in acquisitions:
            if acquisition.unit_dir is not None:
                if self._run_regenerate_code:
                    self._build_runner.regenerate_code(acquisition.unit_dir)
                relations.extend(self._source_code_parser.parse(acquisition.unit_dir, acquisition.unit.unit_name))
            steps.advance("parse")

        topics = self._type_support_parser(run_dir).get_topic_list()
        message_parser = self._message_file_parser(run_dir)
        messages = message_parser.get_message_list()
        all_relations: List[Union[UnitRelation, ConnectsTo]] = [*relations, *message_parser.get_message_relations(), *ansible_connects]
        errors.extend(self._check.execute([*files, *all_relations, *topics, *messages], context))
        hierarchy = {u.unit_name: self._config_repo.get_system_hierarchy(u.unit_name) for u in inventory.units}
        graph = ModelSetupDataGraph.build(
            app_node_relations, parser.get_app_role_relation(), parser.get_app_criticality_relation(),
            all_relations, topics, messages, inventory, hierarchy, ansible_nodes, ansible_networks,
        )
        data = ModelSetupData(context, inventory, files, errors, graph, produced_by=produced_by)
        path = self._store.save(data, run_id)
        steps.advance("finalize")

        status_by_unit = {a.unit.unit_name: a.status for a in acquisitions}
        return ProductionResult(
            run_id=run_id,
            file=path,
            units=[(u, status_by_unit.get(u.unit_name, UnitStatus.NOT_ACQUIRED)) for u in inventory.units],
            scale=data.scale,
            acquired_files=len(files),
            candidates=list(candidates),
            errors=errors,
        )

    @staticmethod
    def _missing(reason: str, source_name: str, context) -> ErrorRecord:
        return ErrorRecord(ErrorStatus.MISSING_DATA, reason, source_name, SourceType.CONFIG_MGMT_DB.value, context.project_platform)
