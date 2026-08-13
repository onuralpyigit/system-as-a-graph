import type { SessionResponse } from "./api-types";

// Client-only storage for the granted session (SRS VAE-01.3). The token's own
// server-side expiry (VAE_SESSION_MINUTES) is the real boundary; this is just
// where the browser keeps it between requests.
const STORAGE_KEY = "saag.session";

export type StoredSession = SessionResponse;

export function readSession(): StoredSession | null {
  if (typeof window === "undefined") return null;
  const raw = window.localStorage.getItem(STORAGE_KEY);
  if (!raw) return null;
  try {
    return JSON.parse(raw) as StoredSession;
  } catch {
    return null;
  }
}

export function writeSession(session: StoredSession): void {
  window.localStorage.setItem(STORAGE_KEY, JSON.stringify(session));
}

export function clearSession(): void {
  window.localStorage.removeItem(STORAGE_KEY);
}

export function isExpired(session: StoredSession): boolean {
  return new Date(session.expires_at).getTime() <= Date.now();
}
