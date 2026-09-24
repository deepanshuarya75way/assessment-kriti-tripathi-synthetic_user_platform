/**
 * Thin fetch wrapper: attaches the JWT, parses the backend's uniform error
 * envelope ({success:false, error:{code,message}}) into a typed ApiError, and
 * exposes a raw-response helper for the PDF download.
 */
const API_BASE = import.meta.env.VITE_API_BASE_URL ?? "/api/v1";
const TOKEN_KEY = "sur_token";

export function getToken(): string | null {
  try {
    return localStorage.getItem(TOKEN_KEY);
  } catch {
    return null;
  }
}

export function setToken(token: string | null): void {
  try {
    if (token) localStorage.setItem(TOKEN_KEY, token);
    else localStorage.removeItem(TOKEN_KEY);
  } catch {
    /* storage unavailable (private mode) — auth simply won't persist */
  }
}

export class ApiError extends Error {
  code: string;
  status: number;
  constructor(message: string, code: string, status: number) {
    super(message);
    this.code = code;
    this.status = status;
  }
}

function authHeaders(): Record<string, string> {
  const token = getToken();
  return token ? { Authorization: `Bearer ${token}` } : {};
}

async function parseError(res: Response): Promise<ApiError> {
  let message = "Request failed.";
  let code = "ERROR";
  try {
    const body = await res.json();
    if (body?.error) {
      message = body.error.message ?? message;
      code = body.error.code ?? code;
    }
  } catch {
    /* non-JSON error body */
  }
  return new ApiError(message, code, res.status);
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...authHeaders(),
      ...(options.headers ?? {}),
    },
  });
  if (!res.ok) throw await parseError(res);
  if (res.status === 204) return undefined as T;
  return (await res.json()) as T;
}

export const api = {
  get: <T>(path: string) => request<T>(path),
  post: <T>(path: string, body?: unknown) =>
    request<T>(path, { method: "POST", body: body ? JSON.stringify(body) : undefined }),
  del: <T>(path: string) => request<T>(path, { method: "DELETE" }),

  /** Fetch the report PDF as a Blob (bypasses JSON parsing). */
  async getBlob(path: string): Promise<Blob> {
    const res = await fetch(`${API_BASE}${path}`, { headers: authHeaders() });
    if (!res.ok) throw await parseError(res);
    return res.blob();
  },
};
