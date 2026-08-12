const DEFAULT_BACKEND_URL = "http://127.0.0.1:18742";

export interface HealthResponse {
  status: string;
  version: string;
  app: string;
}

export interface Workspace {
  id: number;
  root_path: string;
  name: string;
  created_at: string;
  updated_at: string;
}

export interface WorkspaceSetRequest {
  root_path: string;
  name?: string;
}

export interface ScanJob {
  id: number;
  workspace_id: number;
  status: "queued" | "running" | "completed" | "failed" | "cancelled";
  started_at: string | null;
  finished_at: string | null;
  files_discovered: number;
  files_processed: number;
  error: string | null;
}

export interface WorkspaceFile {
  id: number;
  workspace_id: number;
  relative_path: string;
  filename: string;
  extension: string;
  category: string;
  size_bytes: number;
  modified_at: string;
  fs_status: string;
  last_scanned_at: string;
}

export interface WorkspaceFileList {
  items: WorkspaceFile[];
  total: number;
  offset: number;
  limit: number;
}

export interface WorkspaceOverview {
  workspace_id: number;
  total_files: number;
  total_size_bytes: number;
  files_by_category: Record<string, number>;
  files_by_status: Record<string, number>;
  pending_changes_count: number;
  recent_files: WorkspaceFile[];
  latest_scan: ScanJob | null;
}

function getBackendBaseUrl(): string {
  return import.meta.env.VITE_BACKEND_URL ?? DEFAULT_BACKEND_URL;
}

export async function fetchHealth(): Promise<HealthResponse> {
  const response = await fetch(`${getBackendBaseUrl()}/api/v1/health`);
  if (!response.ok) {
    throw new Error(`Backend returned ${response.status}`);
  }
  return response.json() as Promise<HealthResponse>;
}

export function getBackendUrl(): string {
  return getBackendBaseUrl();
}

export async function fetchWorkspace(): Promise<Workspace | null> {
  const response = await fetch(`${getBackendBaseUrl()}/api/v1/workspace`);
  if (!response.ok) throw new Error(`Backend returned ${response.status}`);
  return response.json() as Promise<Workspace | null>;
}

export async function putWorkspace(payload: WorkspaceSetRequest): Promise<Workspace> {
  const response = await fetch(`${getBackendBaseUrl()}/api/v1/workspace`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!response.ok) {
    const body = (await response.json().catch(() => null)) as {
      detail?: string | Array<{ msg?: string }>;
    } | null;
    let message: string | undefined;
    if (typeof body?.detail === "string") {
      message = body.detail;
    } else if (Array.isArray(body?.detail) && body.detail[0]?.msg) {
      message = body.detail[0].msg;
    }
    throw new Error(message ?? `Backend returned ${response.status}`);
  }
  return response.json() as Promise<Workspace>;
}

export async function deleteWorkspace(): Promise<void> {
  const response = await fetch(`${getBackendBaseUrl()}/api/v1/workspace`, { method: "DELETE" });
  if (!response.ok) throw new Error(`Backend returned ${response.status}`);
}

export async function postWorkspaceScan(): Promise<ScanJob> {
  const response = await fetch(`${getBackendBaseUrl()}/api/v1/workspace/scan`, {
    method: "POST",
  });
  if (!response.ok) throw new Error(`Backend returned ${response.status}`);
  return response.json() as Promise<ScanJob>;
}

export async function fetchWorkspaceScanLatest(): Promise<ScanJob | null> {
  const response = await fetch(`${getBackendBaseUrl()}/api/v1/workspace/scan/latest`);
  if (!response.ok) throw new Error(`Backend returned ${response.status}`);
  return response.json() as Promise<ScanJob | null>;
}

export async function postWorkspaceScanCancel(): Promise<{ cancelled: boolean }> {
  const response = await fetch(`${getBackendBaseUrl()}/api/v1/workspace/scan/cancel`, {
    method: "POST",
  });
  if (!response.ok) throw new Error(`Backend returned ${response.status}`);
  return response.json() as Promise<{ cancelled: boolean }>;
}

export async function fetchWorkspaceOverview(): Promise<WorkspaceOverview> {
  const response = await fetch(`${getBackendBaseUrl()}/api/v1/workspace/overview`);
  if (!response.ok) throw new Error(`Backend returned ${response.status}`);
  return response.json() as Promise<WorkspaceOverview>;
}

export async function fetchWorkspaceFiles(params?: {
  category?: string;
  fs_status?: string;
  search?: string;
  offset?: number;
  limit?: number;
}): Promise<WorkspaceFileList> {
  const query = new URLSearchParams();
  if (params?.category) query.set("category", params.category);
  if (params?.fs_status) query.set("fs_status", params.fs_status);
  if (params?.search) query.set("search", params.search);
  if (params?.offset !== undefined) query.set("offset", params.offset.toString());
  if (params?.limit !== undefined) query.set("limit", params.limit.toString());

  const response = await fetch(`${getBackendBaseUrl()}/api/v1/workspace/files?${query.toString()}`);
  if (!response.ok) throw new Error(`Backend returned ${response.status}`);
  return response.json() as Promise<WorkspaceFileList>;
}
