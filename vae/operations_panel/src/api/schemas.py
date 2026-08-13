"""
Description: Request and response models for the operations panel REST interface.
Created by: Mustafa Can Caliskan
Date: 2026-07-31
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    """Credentials presented at login (SRS VAE-01.3)."""

    username: str
    password: str


class SessionResponse(BaseModel):
    """A granted session. The token is presented as a bearer credential."""

    token: str
    username: str
    display_name: str
    authorizations: list[str] = Field(default_factory=list)
    expires_at: datetime


class SystemVersionOption(BaseModel):
    """A selectable system version, with the effective one marked."""

    version: str
    is_effective: bool = False


class SelectableScopeResponse(BaseModel):
    """What the operator may choose between (SRS VAE-01.4)."""

    projects: list[str] = Field(default_factory=list)
    platforms: list[str] = Field(default_factory=list)
    versions: list[SystemVersionOption] = Field(default_factory=list)
    effective_version: str | None = None


class ScopeSelectionRequest(BaseModel):
    """The project/platform/system version the operator selects."""

    project: str
    platform: str
    system_version: str


class WorkingScopeResponse(BaseModel):
    """The operator's current selection.

    ``selected_is_effective`` is reported separately from the selection itself
    so the UI can show that an operator is deliberately working on a version
    other than the effective one.
    """

    project: str
    platform: str
    system_version: str
    selected_is_effective: bool
    selected_model_setup_data_run_id: str = ""


class ModelSetupDataFileResponse(BaseModel):
    """A produced Model Setup Data file the operator can select (SRS VAE-01.5)."""

    run_id: str
    file_path: str
    produced_at: datetime
    entity_count: int = 0
    relation_count: int = 0
    failure_count: int = 0


class SelectFileRequest(BaseModel):
    """Which produced file the operator picks."""

    run_id: str


class ProductionJobResponse(BaseModel):
    """A production process and its status (SRS VAE-01.6)."""

    job_id: str
    status: str
    project: str
    platform: str
    system_version: str
    started_by: str
    started_at: datetime
    finished_at: datetime | None = None
    run_id: str = ""
    file_path: str = ""
    failure_reason: str = ""
    entity_count: int = 0
    relation_count: int = 0
    error_count: int = 0


class ProductionErrorResponse(BaseModel):
    """A failure recorded during production (SRS VAE-01.8)."""

    status: str
    reason: str
    source_name: str
    source_type: str
    occurred_at: datetime
    detail: str = ""


class SourceStatusResponse(BaseModel):
    """One configured source's accessibility."""

    source_type: str
    source_name: str
    accessibility: str
    checked_at: datetime
    detail: str = ""


class SourceStatusSnapshotResponse(BaseModel):
    """Every configured source's accessibility at one moment (SRS VAE-01.7)."""

    checked_at: datetime
    all_reachable: bool
    statuses: list[SourceStatusResponse] = Field(default_factory=list)


class DataSourceResponse(BaseModel):
    """One configured external data source (SRS MSD.2-5, 8). No secret in it."""

    source_type: str
    name: str
    access_method: str
    connection_address: str
    username: str = ""
    secret_set: bool = False
    priority: int = 0


class DataSourceConfigureRequest(BaseModel):
    """Request to save a data source configuration (SRS MSD.8)."""

    source_type: str
    name: str
    access_method: str
    connection_address: str
    username: str = ""
    secret: str | None = Field(
        default=None,
        description=(
            "The secret, in plaintext, encrypted before storage. Omit or "
            "leave blank on an update to keep the previously stored secret."
        ),
    )
    priority: int = 0
