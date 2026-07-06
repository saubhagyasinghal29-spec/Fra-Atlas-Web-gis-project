// Domain API calls + adapters mapping backend JSON onto the shapes the pages
// already expect (the bundled FRA_DATA model).

import { apiFetch } from './client';
import { FRA_DATA as STATIC_FRA_DATA } from '../data/fraData';

// The backend districts endpoint already returns keys matching the FRA_DATA
// model (state, district, ri, rl, rr, cl, ar, pr, pt, fl, tc, cr, rjr, enc).
// We coerce nulls to safe numbers so the existing render code (which calls
// .toFixed) never throws on a partially-populated record.
function coerce(d) {
  const n = (v, f = 0) => (typeof v === 'number' ? v : f);
  return {
    state: d.state, district: d.district, code: d.code,
    ri: n(d.ri), rl: d.rl || 'Good', rr: n(d.rr), cl: n(d.cl, 2),
    pc1: n(d.pc1), pc2: n(d.pc2),
    ar: n(d.ar), pr: n(d.pr), pt: n(d.pt), fl: n(d.fl),
    tc: n(d.tc), cr: n(d.cr), rjr: n(d.rjr), enc: n(d.enc),
  };
}

export async function fetchDistricts() {
  const data = await apiFetch('/api/v1/analytics/districts/');
  const rows = (data.districts || []).map(coerce);
  if (!rows.length) throw new Error('No districts returned');
  return rows;
}

// Live-first with a graceful fallback to the bundled dataset, so the portal is
// always usable for review even if the API is unreachable.
export async function loadAtlasData() {
  try {
    const rows = await fetchDistricts();
    return { data: rows, source: 'live' };
  } catch (err) {
    return { data: STATIC_FRA_DATA, source: 'bundled', error: err.message };
  }
}

export async function generateReport(reportType, exportFormat) {
  return apiFetch('/api/v1/reports/generate/', {
    method: 'POST', body: { report_type: reportType, export_format: exportFormat },
  });
}
export async function reportStatus(jobId) {
  return apiFetch(`/api/v1/reports/${jobId}/status/`);
}
