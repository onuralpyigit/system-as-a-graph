import type {
  DataSourceConfigureRequest,
  DataSourceResponse,
  LoginRequest,
  ModelSetupDataFileResponse,
  ProductionErrorResponse,
  ProductionJobResponse,
  ScopeSelectionRequest,
  SelectableScopeResponse,
  SessionResponse,
  SourceStatusSnapshotResponse,
  WorkingScopeResponse,
} from "./api-types";

// The Operations Panel is the sole interaction surface (SDD 3.6.1.1): every
// call from this app goes through the panel's API, never MSD's or another
// CSC's directly.
const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
const PANEL_PREFIX = "/vae/operations-panel";

export class ApiError extends Error {
  status: number;
  detail: string;

  constructor(status: number, detail: string) {
    super(detail);
    this.name = "ApiError";
    this.status = status;
    this.detail = detail;
  }
}

interface RequestOptions {
  method?: "GET" | "POST" | "PUT" | "DELETE";
  body?: unknown;
  token?: string | null;
  signal?: AbortSignal;
}

async function request<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const { method = "GET", body, token, signal } = options;
  const headers: Record<string, string> = {};
  if (body !== undefined) headers["Content-Type"] = "application/json";
  if (token) headers.Authorization = `Bearer ${token}`;

  const response = await fetch(`${API_BASE}${PANEL_PREFIX}${path}`, {
    method,
    headers,
    body: body !== undefined ? JSON.stringify(body) : undefined,
    signal,
  });

  if (!response.ok) {
    let detail = response.statusText;
    try {
      const payload = await response.json();
      if (typeof payload?.detail === "string") detail = payload.detail;
    } catch {
      // Response carried no JSON body; the status text stands.
    }
    throw new ApiError(response.status, detail);
  }

  if (response.status === 204) return undefined as T;
  return (await response.json()) as T;
}

const get = <T>(path: string, token?: string | null, signal?: AbortSignal) =>
  request<T>(path, { token, signal });
const post = <T>(path: string, body: unknown, token?: string | null) =>
  request<T>(path, { method: "POST", body, token });
const put = <T>(path: string, body: unknown, token?: string | null) =>
  request<T>(path, { method: "PUT", body, token });
const del = (path: string, token?: string | null) =>
  request<void>(path, { method: "DELETE", token });

export const authApi = {
  login: (payload: LoginRequest) => post<SessionResponse>("/session", payload),
  currentSession: (token: string) => get<SessionResponse>("/session", token),
};

export const scopeApi = {
  listProjects: (token: string) => get<SelectableScopeResponse>("/scope/projects", token),
  listPlatforms: (token: string, project: string) =>
    get<SelectableScopeResponse>(`/scope/projects/${encodeURIComponent(project)}/platforms`, token),
  listVersions: (token: string, project: string, platform: string) =>
    get<SelectableScopeResponse>(
      `/scope/projects/${encodeURIComponent(project)}/platforms/${encodeURIComponent(platform)}/versions`,
      token,
    ),
  select: (token: string, payload: ScopeSelectionRequest) =>
    put<WorkingScopeResponse>("/scope", payload, token),
  current: (token: string) => get<WorkingScopeResponse>("/scope", token),
};

export const setupApi = {
  listFiles: (token: string) => get<ModelSetupDataFileResponse[]>("/model-setup-data", token),
  selectFile: (token: string, runId: string) =>
    put<WorkingScopeResponse>("/model-setup-data/selected", { run_id: runId }, token),
  startProduction: (token: string) =>
    post<ProductionJobResponse>("/production", undefined, token),
  productionStatus: (token: string, jobId: string) =>
    get<ProductionJobResponse>(`/production/${encodeURIComponent(jobId)}`, token),
  productionHistory: (token: string) => get<ProductionJobResponse[]>("/production", token),
  productionErrorsForRun: (token: string, runId: string) =>
    get<ProductionErrorResponse[]>(`/production-errors/${encodeURIComponent(runId)}`, token),
  sourceStatus: (token: string) => get<SourceStatusSnapshotResponse>("/source-status", token),
  sourceStatusStreamUrl: (token: string) =>
    `${API_BASE}${PANEL_PREFIX}/source-status/stream?${new URLSearchParams({ token }).toString()}`,
  listDataSources: (token: string) => get<DataSourceResponse[]>("/data-sources", token),
  configureDataSource: (token: string, payload: DataSourceConfigureRequest) =>
    post<DataSourceResponse>("/data-sources", payload, token),
  deleteDataSource: (token: string, sourceType: string, name: string) =>
    del(`/data-sources/${encodeURIComponent(sourceType)}/${encodeURIComponent(name)}`, token),
};
