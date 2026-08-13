// Mirrors vae/operations_panel/src/api/schemas.py. Keep in sync by hand: this
// increment has no generated client, so a backend field rename must be
// applied here too.

export interface LoginRequest {
  username: string;
  password: string;
}

export interface SessionResponse {
  token: string;
  username: string;
  display_name: string;
  authorizations: string[];
  expires_at: string;
}

export interface SystemVersionOption {
  version: string;
  is_effective: boolean;
}

export interface SelectableScopeResponse {
  projects: string[];
  platforms: string[];
  versions: SystemVersionOption[];
  effective_version: string | null;
}

export interface ScopeSelectionRequest {
  project: string;
  platform: string;
  system_version: string;
}

export interface WorkingScopeResponse {
  project: string;
  platform: string;
  system_version: string;
  selected_is_effective: boolean;
  selected_model_setup_data_run_id: string;
}

export interface ModelSetupDataFileResponse {
  run_id: string;
  file_path: string;
  produced_at: string;
  entity_count: number;
  relation_count: number;
  failure_count: number;
}

export type ProductionJobStatus = "in_progress" | "succeeded" | "failed";

export interface ProductionJobResponse {
  job_id: string;
  status: ProductionJobStatus;
  project: string;
  platform: string;
  system_version: string;
  started_by: string;
  started_at: string;
  finished_at: string | null;
  run_id: string;
  file_path: string;
  failure_reason: string;
  entity_count: number;
  relation_count: number;
  error_count: number;
}

export interface ProductionErrorResponse {
  status: string;
  reason: string;
  source_name: string;
  source_type: string;
  occurred_at: string;
  detail: string;
}

export type Accessibility = "reachable" | "unreachable";

export interface SourceStatusResponse {
  source_type: string;
  source_name: string;
  accessibility: Accessibility;
  checked_at: string;
  detail: string;
}

export interface SourceStatusSnapshotResponse {
  checked_at: string;
  all_reachable: boolean;
  statuses: SourceStatusResponse[];
}

export interface DataSourceResponse {
  source_type: string;
  name: string;
  access_method: string;
  connection_address: string;
  username: string;
  secret_set: boolean;
  priority: number;
}

export interface DataSourceConfigureRequest {
  source_type: string;
  name: string;
  access_method: string;
  connection_address: string;
  username: string;
  secret?: string | null;
  priority: number;
}
