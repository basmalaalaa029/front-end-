/**
 * Unified CV Agent HTTP client — requires backend-issued JWT on all :8000 requests.
 */
import { useAuthStore } from "@/features/auth/stores/auth-store";
import {
  mergeAbortSignals,
  timeoutSignal,
} from "@/features/cv-analysis/lib/abort-signal";

const RAW_BASE =
  (import.meta.env.VITE_CV_AGENT_URL as string | undefined) ??
  "http://localhost:8000";

export const CV_AGENT_BASE = RAW_BASE.replace(/\/+$/, "");

export class CvAgentClientError extends Error {
  status?: number;
  constructor(message: string, status?: number) {
    super(message);
    this.name = "CvAgentClientError";
    this.status = status;
  }
}

function handleUnauthorized(): void {
  const { logout } = useAuthStore.getState();
  logout();
  if (window.location.pathname !== "/login") {
    window.location.href = "/login";
  }
}

export async function readCvAgentError(res: Response): Promise<string> {
  try {
    const body = await res.json();
    if (typeof body?.detail === "string") return body.detail;
    if (body?.detail) return JSON.stringify(body.detail);
    return JSON.stringify(body);
  } catch {
    try {
      return await res.text();
    } catch {
      return res.statusText || `HTTP ${res.status}`;
    }
  }
}

function requireToken(): string {
  const token = useAuthStore.getState().token;
  if (!token) {
    throw new CvAgentClientError("Not authenticated", 401);
  }
  return token;
}

function authHeaders(
  extra?: HeadersInit,
  body?: BodyInit | null,
): HeadersInit {
  const token = requireToken();
  const base: Record<string, string> = {
    Accept: "application/json",
    Authorization: `Bearer ${token}`,
  };
  // FormData: browser must set Content-Type with multipart boundary.
  const skipContentType = body instanceof FormData;

  const merge = (key: string, value: string) => {
    if (skipContentType && key.toLowerCase() === "content-type") return;
    base[key] = value;
  };

  if (extra instanceof Headers) {
    extra.forEach((value, key) => merge(key, value));
    return base;
  }
  if (Array.isArray(extra)) {
    for (const [key, value] of extra) merge(key, value);
    return base;
  }
  if (extra && typeof extra === "object") {
    for (const [key, value] of Object.entries(extra)) {
      if (value != null) merge(key, String(value));
    }
  }
  return base;
}

export type CvAgentFetchOptions = RequestInit & {
  timeoutMs?: number;
  signal?: AbortSignal;
};

async function handleCvAgentResponse(res: Response): Promise<void> {
  if (res.status === 401) {
    handleUnauthorized();
  }
  if (!res.ok) {
    throw new CvAgentClientError(await readCvAgentError(res), res.status);
  }
}

export async function cvAgentFetch<T>(
  path: string,
  init: CvAgentFetchOptions = {},
): Promise<T> {
  requireToken();

  const { timeoutMs, signal, body, ...rest } = init;
  let fetchSignal = signal;
  if (timeoutMs) {
    const timeout = timeoutSignal(timeoutMs);
    fetchSignal = signal ? mergeAbortSignals(signal, timeout) : timeout;
  }

  const res = await fetch(`${CV_AGENT_BASE}${path}`, {
    ...rest,
    body,
    signal: fetchSignal,
    headers: authHeaders(rest.headers, body),
  });

  await handleCvAgentResponse(res);

  if (res.status === 204) {
    return undefined as T;
  }

  const contentType = res.headers.get("content-type") ?? "";
  if (contentType.includes("application/json")) {
    return (await res.json()) as T;
  }

  return (await res.blob()) as T;
}

export async function cvAgentFetchRaw(
  path: string,
  init: CvAgentFetchOptions = {},
): Promise<Response> {
  requireToken();

  const { timeoutMs, signal, body, ...rest } = init;
  let fetchSignal = signal;
  if (timeoutMs) {
    const timeout = timeoutSignal(timeoutMs);
    fetchSignal = signal ? mergeAbortSignals(signal, timeout) : timeout;
  }

  const res = await fetch(`${CV_AGENT_BASE}${path}`, {
    ...rest,
    body,
    signal: fetchSignal,
    headers: authHeaders(rest.headers, body),
  });

  await handleCvAgentResponse(res);

  return res;
}
