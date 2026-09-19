"""Produces the Model Setup Data of one run: acquires the context, the
inventory, the system repo (cloned without the unit file rule) and the
software units it names, parses them and saves the file (SRS DSM-MDG req 3, 5-19)."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

from mdg.domain.data_source import SourceType
from mdg.domain.error_record import DataAcquisitionError, ErrorRecord, ErrorStatus
from mdg.domain.inventory import CandidateUnitVersion, SoftwareUnitVersion
from mdg.domain.model_setup_data import ModelSetupData, UnitStatus
from mdg.domain.model_setup_data_graph import ModelSetupDataGraph
from mdg.domain.workspace import Workspace
from mdg.ports.build_runner import IBuildRunner
from mdg.ports.config_management_repository import IConfigManagementRepository
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
    the graph scale, the candidate and the errors recorded."""
    run_id: str
    file: Path
    units: List[Tuple[SoftwareUnitVersion, UnitStatus]]
    scale: Dict[str, int]
    candidate: Optional[CandidateUnitVersion]
    errors: List[ErrorRecord]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "run_id": self.run_id,
            "file": str(self.file),
            "units": [{**unit.to_dict(), "status": status.value} for unit, status in self.units],
            "scale": self.scale,
            "candidate": self.candidate.to_dict() if self.candidate else None,
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
            self._report(100 * self._done // self._total, phase)


class ProduceModelSetupData:
    """Runs the production process in a run directory keyed by run id and
    returns the ProductionResult; a failure to acquire the context or the
    system repo raises DataAcquisitionError (req 12)."""

    def __init__(
        self,
        config_repo: IConfigManagementRepository,
        acquire_context: AcquireProjectContext,
        build_inventory: BuildSoftwareUnitInventory,
        acquire_source_code: AcquireSourceCode,
        system_repo_parser: SystemRepoParserFactory,
        source_code_parser: ISourceCodeParser,
        type_support_parser: TypeSupportParserFactory,
        build_runner: IBuildRunner,
        check_mandatory_fields: CheckMandatoryFields,
        store: IModelSetupDataStore,
        workspace: Workspace,
        system_repo_name: str,
        run_regenerate_code: bool = False,
    ):
        self._config_repo = config_repo
        self._acquire_context = acquire_context
        self._build_inventory = build_inventory
        self._acquire = acquire_source_code
        self._system_repo_parser = system_repo_parser
        self._source_code_parser = source_code_parser
        self._type_support_parser = type_support_parser
        self._build_runner = build_runner
        self._check = check_mandatory_fields
        self._store = store
        self._workspace = workspace
        self._system_repo_name = system_repo_name
        self._run_regenerate_code = run_regenerate_code

    def execute(
        self,
        project_id: str,
        platform_id: str,
        version_id: str,
        run_id: str,
        produced_by: Optional[str] = None,
        candidate: Optional[CandidateUnitVersion] = None,
        progress: Optional[ProgressCallback] = None,
    ) -> ProductionResult:
        if self._run_regenerate_code:
            self._build_runner.ensure_available()
        context = self._acquire_context.execute(project_id, platform_id, version_id)
        inventory = self._build_inventory.execute(context, candidate)
        run_dir = self._workspace.run_dir(project_id, platform_id, version_id, run_id)
        run_dir.mkdir(parents=True, exist_ok=True)
        logger.info("produce: %s/%s/%s run %s", project_id, platform_id, version_id, run_id)

        system_unit = inventory.find(self._system_repo_name)
        if system_unit is None:
            raise DataAcquisitionError(self._missing(f"system repo '{self._system_repo_name}' is not in the inventory", self._system_repo_name, context))
        inventory = inventory.without(system_unit.unit_name)
        system = self._acquire.execute(system_unit, run_dir, context, mandatory=False)
        if system.unit_dir is None:
            raise DataAcquisitionError(system.errors[0])
        parser = self._system_repo_parser(system.unit_dir, context.project.name, context.platform.name)
        app_node_relations = parser.get_app_node_relation()

        files, errors = list(system.files), list(system.errors)
        units: List[SoftwareUnitVersion] = []
        for app_name in dict.fromkeys(app for app, _ in app_node_relations):
            unit = inventory.find(app_name)
            if unit is None:
                errors.append(self._missing(f"application '{app_name}' is not in the inventory", app_name, context))
            else:
                units.append(unit)
        steps = _Progress(progress, total=2 * len(units) + 2)
        steps.advance("system")

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
        errors.extend(self._check.execute([*files, *relations, *topics], context))
        hierarchy = {u.unit_name: self._config_repo.get_system_hierarchy(u.unit_name) for u in inventory.units}
        graph = ModelSetupDataGraph.build(
            app_node_relations, parser.get_app_role_relation(), parser.get_app_criticality_relation(),
            relations, topics, inventory, hierarchy,
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
            candidate=candidate,
            errors=errors,
        )

    @staticmethod
    def _missing(reason: str, source_name: str, context) -> ErrorRecord:
        return ErrorRecord(ErrorStatus.MISSING_DATA, reason, source_name, SourceType.CONFIG_MGMT_DB.value, context.project_platform)
