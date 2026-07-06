# National FRA Atlas — Portal (First Build)

React 19 + Vite frontend for the Forest Rights Act Decision Support System,
wired to the FRA Atlas backend API.

## Run

```bash
npm install
# point at your backend (defaults to http://localhost:8000)
echo "VITE_API_BASE=http://localhost:8000" > .env
npm run dev          # dev server on http://localhost:5173
npm run build        # production build to dist/
```

Backend must be running with CORS allowing the frontend origin
(`CORS_ALLOWED_ORIGINS`), and a user seeded via `python manage.py seed_demo_user`.

**Demo sign-in:** `analyst` / `FraAtlas@2026`

## Architecture

- `src/api/client.js` — fetch wrapper, JWT storage, transparent refresh, login/logout.
- `src/api/fraApi.js` — domain calls + adapter mapping backend JSON to the page data model; live-first with a bundled fallback so the portal is usable if the API is down.
- `src/context/AuthContext.jsx` — auth state; `RequireAuth` gates all routes behind `/login`.
- `src/context/DataContext.jsx` — loads district data once after sign-in; exposes `useFraData()` with `{ data, loading, source, error }`.
- Pages (Dashboard, Map, Analytics, DSS) consume `useFraData()` with loading and
  data-source states. Fire Forecast and Crop Advisor use their own data sources
  per the agreed design.

## Accessibility

Skip-to-main link, larger-text toggle, language toggle, keyboard focus styles,
and reduced-motion support are wired in the layout utility bar.
