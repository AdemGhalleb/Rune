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
