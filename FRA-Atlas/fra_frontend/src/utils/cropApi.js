/**
 * Crop recommender API client.
 *
 * Talks to the FastAPI service documented in the backend's API_CONTRACT.md.
 * Every call degrades gracefully to the local engine (cropEngine.js) when the
 * service is unreachable, so the UI works offline. The `usedFallback` flag on
 * each result lets the UI tell the user which path produced the data.
 */
import { CROP_API_BASE } from '../data/constants';
import { recommendLocal } from './cropEngine';

const TIMEOUT_MS = 2500;

function withTimeout(promise, ms) {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), ms);
  return { signal: controller.signal, done: () => clearTimeout(timer) };
}

/** GET /health → true if the live service is reachable. */
export async function checkHealth() {
  const t = withTimeout(null, TIMEOUT_MS);
  try {
    const res = await fetch(`${CROP_API_BASE}/health`, { signal: t.signal });
    t.done();
    if (!res.ok) return false;
    const data = await res.json();
    return data.status === 'ok';
  } catch {
    t.done();
    return false;
  }
}

/** POST /recommend → ranked crops for one district (falls back to local engine). */
export async function recommendOne(conditions) {
  const t = withTimeout(null, TIMEOUT_MS);
  try {
    const res = await fetch(`${CROP_API_BASE}/recommend`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(conditions),
      signal: t.signal,
    });
    t.done();
    if (res.status === 422) {
      const err = await res.json();
      throw new ValidationError(err);
    }
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();
    return { ...data, usedFallback: false };
  } catch (e) {
    t.done();
    if (e instanceof ValidationError) throw e;
    // Network / service down → local engine
    return { ...recommendLocal(conditions), usedFallback: true };
  }
}

/** POST /recommend/batch → object keyed by district (falls back to local engine). */
export async function recommendBatch(conditionsList) {
  const t = withTimeout(null, TIMEOUT_MS);
  try {
    const res = await fetch(`${CROP_API_BASE}/recommend/batch`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(conditionsList),
      signal: t.signal,
    });
    t.done();
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();
    const out = {};
    for (const k of Object.keys(data)) out[k] = { ...data[k], usedFallback: false };
    return out;
  } catch {
    t.done();
    const out = {};
    for (const c of conditionsList) {
      out[c.district] = { ...recommendLocal(c), usedFallback: true };
    }
    return out;
  }
}

export class ValidationError extends Error {
  constructor(detail) {
    super('Validation failed');
    this.name = 'ValidationError';
    this.detail = detail;
  }
}
