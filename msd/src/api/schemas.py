"""
Description: Request and response models for the MSD REST interface.
Created by: Mustafa Can Caliskan
Date: 2026-07-31
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from msd.src.model.data_source import AccessMethod, DataSourceType
from shared.errors.acquisition import AcquisitionStatus


class CredentialModel(BaseModel):
    """A credential's status. The secret itself is never returned."""

    username: str = ""
    secret_set: bool = False


class DataSourceModel(BaseModel):
    """One configured external data source (SRS MSD.8)."""

    source_type: DataSourceType
    name: str
    access_method: AccessMethod
    connection_address: str
    credential: CredentialModel | None = None
    priority: int = 0


class CredentialInput(BaseModel):
    """A credential as the operator enters it. Write-only: never echoed back."""

    username: str = ""
    secret: str | None = Field(
        default=None,
        description=(
            "The secret, in plaintext, encrypted before storage. Omit or leave "
            "blank on an update to keep the previously stored secret unchanged."
        ),
    )


class DataSourceConfigureRequest(BaseModel):
    """Request to save a data source configuration (SRS MSD.8)."""

    source_type: DataSourceType
    name: str
    access_method: AccessMethod
    connection_address: str
    credential: CredentialInput | None = None
    priority: int = 0


class ScopeModel(BaseModel):
    """The project/platform/system-version scope an operation applies to."""

    project: str
    platform: str
    system_version: str


class ProjectModel(BaseModel):
    """A project reported by a configuration management database."""

    name: str
    source_name: str


class PlatformModel(BaseModel):
    """A platform reported by a configuration management database."""

    name: str
    source_name: str


class SystemVersionModel(BaseModel):
    """A system version, with the effective one marked (SRS MSD.13)."""

    version: str
    is_effective: bool
    source_name: str


class AcquisitionResponse(BaseModel):
    """An acquisition result and the status it ended in (SRS MSD.16)."""

    status: AcquisitionStatus
    projects: list[ProjectModel] = Field(default_factory=list)
    platforms: list[PlatformModel] = Field(default_factory=list)
    versions: list[SystemVersionModel] = Field(default_factory=list)
    errors: list[ErrorModel] = Field(default_factory=list)


class SoftwareUnitModel(BaseModel):
    """One Software Unit Version Inventory entry."""

    unit_name: str
    version: str
    source_name: str = ""
    is_candidate: bool = False


class InventoryResponse(BaseModel):
    """The recorded inventory for one system version (SRS MSD.14-15).

    Carries the acquisition status because recording the inventory reads the
    configuration management database: a source that failed must not look like
    an empty estate (SRS MSD.16).
    """

    scope: ScopeModel
    status: AcquisitionStatus = AcquisitionStatus.OK
    baseline: list[SoftwareUnitModel] = Field(default_factory=list)
    candidates: list[SoftwareUnitModel] = Field(default_factory=list)
    errors: list[ErrorModel] = Field(default_factory=list)


class RecordInventoryRequest(BaseModel):
    """Request to record the baseline inventory from the CM databases."""

    scope: ScopeModel


class AddCandidateRequest(BaseModel):
    """Request to add a candidate version for installation evaluation."""

    scope: ScopeModel
    unit: SoftwareUnitModel


class NetworkComponentModel(BaseModel):
    """One network component."""

    name: str
    component_type: str = ""
    attributes: dict[str, str] = Field(default_factory=dict)


class ManualTopologyRequest(BaseModel):
    """Request carrying a manually entered network topology (SRS MSD.7)."""

    project: str
    platform: str
    components: list[NetworkComponentModel]


class TopologyResponse(BaseModel):
    """An acquired or entered network topology."""

    method: str
    source_name: str
    components: list[NetworkComponentModel] = Field(default_factory=list)


class ProduceRequest(BaseModel):
    """Request to produce a Model Setup Data file (SRS MSD.23)."""

    scope: ScopeModel


class ErrorModel(BaseModel):
    """A recorded acquisition or validation failure (SRS MSD.22)."""

    status: AcquisitionStatus
    reason: str
    source_name: str
    source_type: str
    project: str
    platform: str
    occurred_at: datetime
    detail: str = ""


class ProductionResponse(BaseModel):
    """Outcome of a production run."""

    run_id: str
    succeeded: bool
    file_path: str = ""
    entity_count: int = 0
    relation_count: int = 0
    excluded_units: dict[str, str] = Field(default_factory=dict)
    errors: list[ErrorModel] = Field(default_factory=list)


class DocumentRecordModel(BaseModel):
    """Metadata row for a produced Model Setup Data file."""

    run_id: str
    scope: ScopeModel
    file_path: str
    produced_at: datetime
    entity_count: int
    relation_count: int
    failure_count: int


AcquisitionResponse.model_rebuild()
InventoryResponse.model_rebuild()
