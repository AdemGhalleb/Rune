const DEFAULT_BACKEND_URL = "http://127.0.0.1:18742";

export interface HealthResponse {
  status: string;
  version: string;
  app: string;
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
