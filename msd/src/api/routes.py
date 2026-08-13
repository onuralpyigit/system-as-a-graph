"""
Description: REST endpoints exposing the MSD use cases.
Created by: Mustafa Can Caliskan
Date: 2026-07-31
"""

from __future__ import annotations

from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Query

from msd.src.adapters.support import SystemClock
from msd.src.api.dependencies import Container, get_container
from msd.src.api.schemas import (
    AcquisitionResponse,
    AddCandidateRequest,
    DataSourceModel,
    DocumentRecordModel,
    ErrorModel,
    InventoryResponse,
    ManualTopologyRequest,
    NetworkComponentModel,
    PlatformModel,
    ProduceRequest,
    ProductionResponse,
    ProjectModel,
    RecordInventoryRequest,
    ScopeModel,
    SoftwareUnitModel,
    SystemVersionModel,
    TopologyResponse,
)
from msd.src.model.data_source import DataSourceConfiguration
from msd.src.model.network_topology import NetworkComponent, NetworkTopology
from msd.src.model.version_inventory import (
    SoftwareUnitVersion,
    SoftwareUnitVersionInventory,
)
from msd.src.use_cases._recording import RunRecorder
from msd.src.use_cases.acquire_configuration_data import AcquisitionOutcome
from shared.errors.acquisition import AcquisitionError, AcquisitionStatus
from shared.types.identifiers import (
    PlatformRef,
    ProjectRef,
    SystemVersionRef,
    system_version,
)

#: Placeholder scope for acquisitions that run before a project is known, so a
#: failure recorded during project discovery is still attributable.
_UNKNOWN = "unknown"

router = APIRouter(prefix="/msd", tags=["msd"])


@router.get("/health")
def health():
    """Report that the MSD service is up."""
    return {"status": "ok", "csc": "msd"}


@router.get("/data-sources", response_model=list[DataSourceModel])
def list_data_sources(container: Container = Depends(get_container)):
    """List every configured external data source (SRS MSD.2-5, 8).

    Read-only and carries no secret, so it stays open on MSD's own API; saving
    or deleting a configuration is credential-bearing and goes only through
    the Operations Panel's session-guarded proxy (SDD 3.6.1.1), not here.
    """
    return [_to_source_model(item) for item in container.data_sources.list_all()]


@router.get("/projects", response_model=AcquisitionResponse)
def list_projects(container: Container = Depends(get_container)):
    """Retrieve the known projects from every configured CM database (SRS MSD.10)."""
    recorder = _recorder(container, PlatformRef(ProjectRef(_UNKNOWN), _UNKNOWN))
    outcome = container.configuration_data().list_projects(recorder)
    return AcquisitionResponse(
        status=outcome.status,
        projects=[
            ProjectModel(name=item.ref.name, source_name=item.source_name)
            for item in outcome.data.projects
        ],
        errors=[_to_error_model(error) for error in outcome.errors],
    )


@router.get("/projects/{project}/platforms", response_model=AcquisitionResponse)
def list_platforms(project: str, container: Container = Depends(get_container)):
    """Retrieve a project's platforms (SRS MSD.11)."""
    project_ref = ProjectRef(project)
    recorder = _recorder(container, PlatformRef(project_ref, _UNKNOWN))
    outcome = container.configuration_data().list_platforms(project_ref, recorder)
    return AcquisitionResponse(
        status=outcome.status,
        platforms=[
            PlatformModel(name=item.ref.name, source_name=item.source_name)
            for item in outcome.data.platforms
        ],
        errors=[_to_error_model(error) for error in outcome.errors],
    )


@router.get(
    "/projects/{project}/platforms/{platform}/versions", response_model=AcquisitionResponse
)
def list_system_versions(
    project: str, platform: str, container: Container = Depends(get_container)
):
    """Retrieve a platform's system versions, marking the effective one (SRS MSD.12-13)."""
    platform_ref = PlatformRef(ProjectRef(project), platform)
    recorder = _recorder(container, platform_ref)
    outcome = container.configuration_data().list_system_versions(platform_ref, recorder)
    return AcquisitionResponse(
        status=outcome.status,
        versions=[
            SystemVersionModel(
                version=item.ref.version,
                is_effective=item.is_effective,
                source_name=item.source_name,
            )
            for item in outcome.data.versions
        ],
        errors=[_to_error_model(error) for error in outcome.errors],
    )


@router.post("/version-inventory", response_model=InventoryResponse)
def record_inventory(
    payload: RecordInventoryRequest, container: Container = Depends(get_container)
):
    """Record the baseline Software Unit Version Inventory (SRS MSD.14)."""
    scope = _scope(payload.scope)
    recorder = _recorder(container, scope.platform)

    units, outcome = container.configuration_data().list_software_units(
        scope.platform, scope.version, recorder
    )
    inventory = container.inventory.record(scope, units)
    return _to_inventory_response(payload.scope, inventory, outcome)


@router.post("/version-inventory/candidate", response_model=InventoryResponse)
def add_candidate(payload: AddCandidateRequest, container: Container = Depends(get_container)):
    """Add a candidate version alongside the defined versions (SRS MSD.15)."""
    scope = _scope(payload.scope)
    inventory = container.inventory.add_candidate(
        scope,
        SoftwareUnitVersion(
            unit_name=payload.unit.unit_name,
            version=payload.unit.version,
            source_name=payload.unit.source_name,
            is_candidate=True,
        ),
    )
    return _to_inventory_response(payload.scope, inventory)


@router.get("/version-inventory", response_model=InventoryResponse)
def get_inventory(
    project: str = Query(...),
    platform: str = Query(...),
    version: str = Query(...),
    container: Container = Depends(get_container),
):
    """Fetch the recorded inventory for a system version.

    Raises:
        HTTPException: 404 when nothing has been recorded for the scope.
    """
    scope_model = ScopeModel(project=project, platform=platform, system_version=version)
    inventory = container.inventory.get(_scope(scope_model))
    if inventory is None:
        raise HTTPException(status_code=404, detail="No inventory recorded for this scope")
    return _to_inventory_response(scope_model, inventory)


@router.get("/network-topology", response_model=TopologyResponse)
def acquire_topology(
    project: str = Query(...),
    platform: str = Query(...),
    container: Container = Depends(get_container),
):
    """Acquire the network topology automatically (SRS MSD.6).

    Raises:
        HTTPException: 404 when no configured source supplied a topology.
    """
    platform_ref = PlatformRef(ProjectRef(project), platform)
    recorder = _recorder(container, platform_ref)
    topology = container.topology().acquire(platform_ref, recorder)
    if topology is None:
        raise HTTPException(
            status_code=404, detail="No configured source supplied a network topology"
        )
    return _to_topology_response(topology)


@router.post("/network-topology/manual", response_model=TopologyResponse)
def enter_topology(
    payload: ManualTopologyRequest, container: Container = Depends(get_container)
):
    """Record a manually entered network topology (SRS MSD.7)."""
    topology = container.topology().enter_manually(
        PlatformRef(ProjectRef(payload.project), payload.platform),
        [
            NetworkComponent(
                name=component.name,
                component_type=component.component_type,
                attributes=component.attributes,
            )
            for component in payload.components
        ],
    )
    return _to_topology_response(topology)


@router.post("/model-setup-data", response_model=ProductionResponse)
def produce_model_setup_data(
    payload: ProduceRequest, container: Container = Depends(get_container)
):
    """Produce the Model Setup Data file for a system version (SRS MSD.21-23)."""
    result = container.production().produce(_scope(payload.scope), run_id=uuid4().hex)

    return ProductionResponse(
        run_id=result.run_id,
        succeeded=result.succeeded,
        file_path=result.file_path,
        entity_count=len(result.document.entities) if result.document else 0,
        relation_count=len(result.document.relations) if result.document else 0,
        excluded_units=result.excluded_units,
        errors=[_to_error_model(error) for error in result.errors],
    )


@router.get("/model-setup-data", response_model=list[DocumentRecordModel])
def list_model_setup_data(
    project: str = Query(...),
    platform: str = Query(...),
    version: str = Query(...),
    container: Container = Depends(get_container),
):
    """List the Model Setup Data files produced for a system version."""
    scope_model = ScopeModel(project=project, platform=platform, system_version=version)
    return [
        DocumentRecordModel(
            run_id=record.run_id,
            scope=scope_model,
            file_path=record.file_path,
            produced_at=record.produced_at,
            entity_count=record.entity_count,
            relation_count=record.relation_count,
            failure_count=record.failure_count,
        )
        for record in container.documents.list_for(_scope(scope_model))
    ]


@router.get("/model-setup-data/{run_id}")
def get_model_setup_data(run_id: str, container: Container = Depends(get_container)):
    """Return a produced Model Setup Data document (INT-IF-01).

    Raises:
        HTTPException: 404 when no document was produced under that run id.
    """
    document = container.documents.load(run_id)
    if document is None:
        raise HTTPException(status_code=404, detail=f"No document for run '{run_id}'")
    return document


@router.get("/errors", response_model=list[ErrorModel])
def list_errors(
    project: str = Query(...),
    platform: str = Query(...),
    container: Container = Depends(get_container),
):
    """List the failures recorded for a platform (SRS MSD.16, 20, 22)."""
    platform_ref = PlatformRef(ProjectRef(project), platform)
    return [
        _to_error_model(error) for error in container.errors.list_for_platform(platform_ref)
    ]


def _scope(model: ScopeModel) -> SystemVersionRef:
    return system_version(model.project, model.platform, model.system_version)


def _recorder(container: Container, platform: PlatformRef) -> RunRecorder:
    return RunRecorder(
        run_id=uuid4().hex,
        platform=platform,
        errors=container.errors,
        clock=SystemClock(),
    )


def _to_source_model(configuration: DataSourceConfiguration) -> DataSourceModel:
    return DataSourceModel(
        source_type=configuration.source_type,
        name=configuration.name,
        access_method=configuration.access_method,
        connection_address=configuration.connection_address,
        credential=(
            {
                "username": configuration.credential.username,
                "secret_set": bool(configuration.credential.encrypted_secret),
            }
            if configuration.credential
            else None
        ),
        priority=configuration.priority,
    )


def _to_inventory_response(
    scope: ScopeModel,
    inventory: SoftwareUnitVersionInventory,
    outcome: AcquisitionOutcome | None = None,
) -> InventoryResponse:
    return InventoryResponse(
        scope=scope,
        status=outcome.status if outcome else AcquisitionStatus.OK,
        baseline=[_to_unit_model(entry) for entry in inventory.baseline],
        candidates=[_to_unit_model(entry) for entry in inventory.candidates],
        errors=[_to_error_model(error) for error in outcome.errors] if outcome else [],
    )


def _to_unit_model(entry: SoftwareUnitVersion) -> SoftwareUnitModel:
    return SoftwareUnitModel(
        unit_name=entry.unit_name,
        version=entry.version,
        source_name=entry.source_name,
        is_candidate=entry.is_candidate,
    )


def _to_topology_response(topology: NetworkTopology) -> TopologyResponse:
    return TopologyResponse(
        method=topology.method.value,
        source_name=topology.source_name,
        components=[
            NetworkComponentModel(
                name=component.name,
                component_type=component.component_type,
                attributes=component.attributes,
            )
            for component in topology.components
        ],
    )


def _to_error_model(error: AcquisitionError) -> ErrorModel:
    return ErrorModel(
        status=error.status,
        reason=error.reason,
        source_name=error.source_name,
        source_type=error.source_type,
        project=error.platform.project.name,
        platform=error.platform.name,
        occurred_at=error.occurred_at,
        detail=error.detail,
    )
