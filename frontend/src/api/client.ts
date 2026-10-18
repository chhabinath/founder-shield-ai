// Typed API client. No secrets live in browser code; only the public
// API base URL is read from a build-time env var.
import type { ApiError, HealthResponse } from "./types";

const BASE_URL: string =
  import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

export class ApiClientError extends Error {
  code: string;
  requestId?: string;
  constructor(message: string, code: string, requestId?: string) {
    super(message);
    this.name = "ApiClientError";
    this.code = code;
    this.requestId = requestId;
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  let resp: Response;
  try {
    resp = await fetch(`${BASE_URL}${path}`, {
      headers: { "Content-Type": "application/json" },
      ...init,
    });
  } catch {
    throw new ApiClientError("Network request failed", "network_error");
  }

  if (!resp.ok) {
    let code = "error";
    let message = `Request failed (${resp.status})`;
    let requestId: string | undefined;
    try {
      const body = (await resp.json()) as ApiError;
      code = body.error?.code ?? code;
      message = body.error?.message ?? message;
      requestId = body.error?.request_id;
    } catch {
      // Non-JSON error body; keep defaults.
    }
    throw new ApiClientError(message, code, requestId);
  }
  return (await resp.json()) as T;
}

export const api = {
  health: () => request<HealthResponse>("/health"),
};
