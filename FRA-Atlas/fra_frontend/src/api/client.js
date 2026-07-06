// Thin API client for the FRA Atlas backend.
// Base URL comes from the environment so the same build runs against local dev
// or a deployed API: set VITE_API_BASE at build time.

const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8000';
const ACCESS_KEY = 'fra.access';
const REFRESH_KEY = 'fra.refresh';

export function getAccess() { return localStorage.getItem(ACCESS_KEY); }
export function getRefresh() { return localStorage.getItem(REFRESH_KEY); }
export function setTokens(access, refresh) {
  if (access) localStorage.setItem(ACCESS_KEY, access);
  if (refresh) localStorage.setItem(REFRESH_KEY, refresh);
}
export function clearTokens() {
  localStorage.removeItem(ACCESS_KEY);
  localStorage.removeItem(REFRESH_KEY);
}

async function rawFetch(path, { method = 'GET', body, auth = true } = {}) {
  const headers = { 'Content-Type': 'application/json' };
  if (auth && getAccess()) headers.Authorization = `Bearer ${getAccess()}`;
  const res = await fetch(`${API_BASE}${path}`, {
    method, headers, body: body ? JSON.stringify(body) : undefined,
  });
  return res;
}

// Fetch with one transparent token refresh on 401.
export async function apiFetch(path, opts = {}) {
  let res = await rawFetch(path, opts);
  if (res.status === 401 && getRefresh() && opts.auth !== false) {
    const refreshed = await tryRefresh();
    if (refreshed) res = await rawFetch(path, opts);
  }
  if (!res.ok) {
    let detail = `Request failed (${res.status})`;
    try { const j = await res.json(); detail = j.message || j.detail || detail; } catch { /* noop */ }
    const err = new Error(detail);
    err.status = res.status;
    throw err;
  }
  return res.status === 204 ? null : res.json();
}

async function tryRefresh() {
  try {
    const res = await rawFetch('/api/v1/auth/refresh/', {
      method: 'POST', auth: false, body: { refresh: getRefresh() },
    });
    if (!res.ok) { clearTokens(); return false; }
    const data = await res.json();
    setTokens(data.access, data.refresh);
    return true;
  } catch { clearTokens(); return false; }
}

export async function login(username, password) {
  const res = await rawFetch('/api/v1/auth/login/', {
    method: 'POST', auth: false, body: { username, password },
  });
  if (!res.ok) {
    let msg = 'Sign in failed. Check your credentials and try again.';
    try { const j = await res.json(); msg = j.message || j.detail || msg; } catch { /* noop */ }
    throw new Error(msg);
  }
  const data = await res.json();
  // backend returns access_token / refresh_token on login, access/refresh on refresh
  setTokens(data.access_token || data.access, data.refresh_token || data.refresh);
  return data;
}

export async function logout() {
  try { await apiFetch('/api/v1/auth/logout/', { method: 'POST', body: { refresh_token: getRefresh() } }); }
  catch { /* best effort */ }
  clearTokens();
}

export { API_BASE };
