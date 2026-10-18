// Shared API types. Mirrors the backend response schemas.

export interface HealthResponse {
  status: string;
  service: string;
  version: string;
  env: string;
}

export interface ApiError {
  error: {
    code: string;
    message: string;
    request_id: string;
  };
}
