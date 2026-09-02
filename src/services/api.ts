/**
 * Centralized API client. Attaches the session token and surfaces FastAPI errors.
 *
 * Local `npm run dev` leaves the base empty so `/api/*` stays same-origin and the
 * Vite proxy forwards to http://127.0.0.1:8000. Production builds must call Render
 * even if VITE_API_BASE_URL is missing or accidentally set to localhost.
 */

const RENDER_API_ORIGIN = 'https://reclaim-financial-control-center.onrender.com';

function resolveApiBase(): string {
  const configured = (import.meta.env.VITE_API_BASE_URL || '').trim().replace(/\/$/, '');
  if (import.meta.env.PROD) {
    return configured || RENDER_API_ORIGIN;
  }
  return configured;
}

const API_BASE = resolveApiBase();
const TOKEN_KEY = 'reclaim_session_token';
const UNAUTHORIZED_EVENT = 'reclaim:unauthorized';

export class ApiError extends Error {
  public status: number;
  public details?: unknown;

  constructor(message: string, status: number, details?: unknown) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.details = details;
  }
}

export function getSessionToken(): string | null {
  try {
    return sessionStorage.getItem(TOKEN_KEY);
  } catch {
    return null;
  }
}

export function setSessionToken(token: string | null): void {
  try {
    if (token) {
      sessionStorage.setItem(TOKEN_KEY, token);
      sessionStorage.setItem('reclaim_auth', 'true');
    } else {
      sessionStorage.removeItem(TOKEN_KEY);
      sessionStorage.removeItem('reclaim_auth');
    }
  } catch {
    // ignore storage failures
  }
}

function expireClientSession() {
  setSessionToken(null);
  if (typeof window !== 'undefined') {
    window.dispatchEvent(new Event(UNAUTHORIZED_EVENT));
  }
}

function detailMessage(body: unknown, fallback: string): string {
  if (!body || typeof body !== 'object') return fallback;
  const detail = (body as { detail?: unknown }).detail;
  if (typeof detail === 'string') return detail;
  if (detail && typeof detail === 'object' && 'message' in detail) {
    return String((detail as { message: string }).message);
  }
  return fallback;
}

export async function fetchApi<T>(endpoint: string, options?: RequestInit): Promise<T> {
  const url = endpoint.startsWith('http') ? endpoint : `${API_BASE}${endpoint}`;
  const token = getSessionToken();
  const headers = new Headers(options?.headers || {});
  if (!headers.has('Accept')) {
    headers.set('Accept', 'application/json');
  }
  const method = (options?.method || 'GET').toUpperCase();
  if (method !== 'GET' && method !== 'HEAD' && !headers.has('Content-Type')) {
    headers.set('Content-Type', 'application/json');
  }
  if (token && !headers.has('Authorization')) {
    headers.set('Authorization', `Bearer ${token}`);
  }

  try {
    const response = await fetch(url, {
      ...options,
      headers,
      credentials: 'include',
    });

    if (response.status === 401 && !url.includes('/api/auth/login')) {
      expireClientSession();
      throw new ApiError('Session expired. Please sign in again.', 401);
    }

    if (!response.ok) {
      let errorBody: unknown;
      try {
        errorBody = await response.json();
      } catch {
        errorBody = await response.text();
      }
      throw new ApiError(
        detailMessage(errorBody, `Request failed (${response.status})`),
        response.status,
        errorBody
      );
    }

    const contentType = response.headers.get('content-type') || '';
    if (contentType.includes('application/json')) {
      return (await response.json()) as T;
    }
    return (await response.text()) as T;
  } catch (error: unknown) {
    if (error instanceof ApiError) {
      throw error;
    }
    const message = error instanceof Error ? error.message : 'Network error';
    throw new ApiError(`Unable to connect to financial server: ${message}`, 0, error);
  }
}

export async function downloadFile(endpoint: string, fallbackName: string): Promise<void> {
  const url = endpoint.startsWith('http') ? endpoint : `${API_BASE}${endpoint}`;
  const token = getSessionToken();
  const headers: HeadersInit = { Authorization: token ? `Bearer ${token}` : '' };
  const response = await fetch(url, { credentials: 'include', headers });
  if (response.status === 401) {
    expireClientSession();
    throw new ApiError('Session expired. Please sign in again.', 401);
  }
  if (!response.ok) {
    throw new ApiError('Download failed.', response.status);
  }
  const blob = await response.blob();
  const disposition = response.headers.get('content-disposition') || '';
  const match = disposition.match(/filename="([^"]+)"/);
  const filename = match?.[1] || fallbackName;
  const objectUrl = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = objectUrl;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  link.remove();
  URL.revokeObjectURL(objectUrl);
}
