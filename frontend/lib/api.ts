// Thin API client wired to the FastAPI backend (backend/app/routers). Every
// function calls a real endpoint with the httpOnly session cookie attached
// via credentials: "include" — the backend's CORS config
// (allow_credentials=True, CORS_ORIGINS) is set up for exactly this.
// Wire format is camelCase on both sides (backend/app/schemas/base.py's
// CamelModel), so responses map onto lib/types.ts with no translation.

import type { Domain, ScanReport, ScanSummary, User, VerificationStatus } from "./types";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  let res: Response;
  try {
    res = await fetch(`${API_URL}${path}`, {
      credentials: "include",
      headers: { "Content-Type": "application/json" },
      ...init,
    });
  } catch {
    // Backend unreachable (down, wrong NEXT_PUBLIC_API_URL, CORS misconfigured, etc.)
    throw new Error("Could not reach the Postura API — is the backend running?");
  }

  if (res.status === 204) return undefined as T;

  const body = await res.json().catch(() => null);
  if (!res.ok) {
    const detail = body && typeof body.detail === "string" ? body.detail : res.statusText;
    throw new Error(detail || "Something went wrong");
  }
  return body as T;
}

// POST /auth/register
export function register(email: string, password: string): Promise<User> {
  return apiFetch<User>("/auth/register", { method: "POST", body: JSON.stringify({ email, password }) });
}

// POST /auth/login
export function login(email: string, password: string): Promise<User> {
  return apiFetch<User>("/auth/login", { method: "POST", body: JSON.stringify({ email, password }) });
}

// POST /auth/logout
export function logout(): Promise<void> {
  return apiFetch<void>("/auth/logout", { method: "POST" });
}

// GET /auth/me — resolves the logged-in user from the session cookie; also
// doubles as the frontend's auth check (401 means "not logged in").
export function me(): Promise<User> {
  return apiFetch<User>("/auth/me");
}

// GET /domains
export function listDomains(): Promise<Domain[]> {
  return apiFetch<Domain[]>("/domains");
}

// POST /domains
export function addDomain(hostname: string): Promise<Domain> {
  return apiFetch<Domain>("/domains", { method: "POST", body: JSON.stringify({ hostname }) });
}

// POST /domains/:id/verify
export function verifyDomain(domainId: string): Promise<{ verificationStatus: VerificationStatus; verified: boolean }> {
  return apiFetch(`/domains/${domainId}/verify`, { method: "POST" });
}

// GET /scans (history, optionally filtered by domain)
export function listScans(domainId?: string): Promise<ScanSummary[]> {
  const qs = domainId ? `?domainId=${encodeURIComponent(domainId)}` : "";
  return apiFetch<ScanSummary[]>(`/scans${qs}`);
}

// POST /scans  { domainId }
export function startScan(domainId: string): Promise<ScanSummary> {
  return apiFetch<ScanSummary>("/scans", { method: "POST", body: JSON.stringify({ domainId }) });
}

// GET /scans/:id — polled by TanStack Query (see scans/[id]/page.tsx) while
// scan.status hasn't reached a terminal state (complete/failed).
export function getScan(scanId: string): Promise<ScanReport> {
  return apiFetch<ScanReport>(`/scans/${scanId}`);
}
