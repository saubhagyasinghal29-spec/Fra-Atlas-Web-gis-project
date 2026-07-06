# API contract — for frontend integration

This service is the **integration surface**. You do not embed the Python code in
your frontend; your frontend (React, Vue, Angular, mobile, anything) calls these
HTTP/JSON endpoints. The recommendation logic stays a backend service behind them.

Base URL (dev): `http://127.0.0.1:8000`
Interactive docs (auto-generated): `GET /docs`
Machine-readable schema: `GET /openapi.json` — you can auto-generate a typed
client from this (e.g. `openapi-typescript`, `openapi-generator`) instead of
hand-writing request/response types.

CORS is open in dev so a frontend on another origin/port can call it. Lock this
down to your real origin before production.

---

## Endpoints

### `GET /health`
Liveness probe. Returns `{ "status": "ok", "crops_loaded": 18 }`.

### `GET /crops`
The knowledge base **and the valid enum values**. Use this to build your form
dropdowns dynamically (soil types, groundwater levels, seasons) instead of
hardcoding them in the frontend — when the backend adds a crop or soil type, your
UI updates for free.

```json
{
  "soil_types": ["sandy", "sandy loam", "loam", "clay loam", "clay"],
  "groundwater_levels": ["safe", "semi-critical", "critical", "over-exploited"],
  "crops": [
    {
      "name": "Rice", "season": "kharif", "water_mm": [1200.0, 1800.0],
      "intensity": "high", "temp_c": [20.0, 37.0], "soils": ["clay", "clay loam"]
    }
  ]
}
```

### `POST /recommend`
One district in, a ranked + explained list out.

**Request body**
```json
{
  "district": "Hisar (Haryana)",
  "rainfall_mm": 450,
  "groundwater": "critical",
  "irrigation_pct": 55,
  "soil": "sandy loam",
  "season": "rabi",
  "temperature_c": 22
}
```

**Response** (recommendations are pre-sorted best-first; `ml_score` is `null`
until a model is trained)
```json
{
  "district": "Hisar (Haryana)",
  "available_water_mm": 543.5,
  "effective_rain_mm": 351.0,
  "irrigation_mm": 192.5,
  "used_ml": false,
  "recommendations": [
    {
      "crop": "Mustard",
      "final_score": 97.5,
      "rule_score": 97.5,
      "ml_score": null,
      "season": "rabi",
      "water_target_mm": 325.0,
      "reasons": [
        { "ok": true,  "text": "Water need met (~325 mm, 544 mm available)" },
        { "ok": false, "text": "Penalised -8: low-water crop in critical block" },
        { "ok": true,  "text": "Soil suits it (sandy loam)" },
        { "ok": true,  "text": "Right season (rabi crop)" },
        { "ok": true,  "text": "Temperature suits it (10-25C)" }
      ]
    }
  ]
}
```

Field meanings: `final_score` is what you rank/colour by (0–100). `rule_score`
and `ml_score` are the two components behind it (show them if you want
transparency). `reasons` is the explanation list — render `ok:true` as ✓ green,
`ok:false` as ✕ red.

### `POST /recommend/batch`
Many districts at once. Body is an **array** of the same objects as `/recommend`.
Response is an **object keyed by district name**, each value identical in shape to
the `/recommend` response. This is what a map/GIS frontend uses: send every
visible district, then join each result onto its boundary polygon by the key.

```json
[ { "district": "Hisar (Haryana)", "rainfall_mm": 450, "...": "..." },
  { "district": "Ludhiana (Punjab)", "rainfall_mm": 700, "...": "..." } ]
```
→
```json
{ "Hisar (Haryana)": { "...recommendation..." },
  "Ludhiana (Punjab)": { "...recommendation..." } }
```

---

## Calling it from a frontend

```js
const res = await fetch("http://127.0.0.1:8000/recommend", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({
    district: "Hisar (Haryana)", rainfall_mm: 450, groundwater: "critical",
    irrigation_pct: 55, soil: "sandy loam", season: "rabi", temperature_c: 22,
  }),
});
const data = await res.json();
data.recommendations.forEach(r => console.log(r.crop, r.final_score));
```

Validation errors (e.g. `irrigation_pct` > 100, missing field) come back as HTTP
`422` with a JSON body describing the offending field — surface these inline.

---

## Notes for the bigger project

- **Versioning.** Before you have other teams depending on it, mount the routes
  under `/v1` so you can evolve the contract without breaking them.
- **Deployment.** The service is stateless — containerise it (Docker) and run
  behind your existing gateway/load balancer. No DB is required for the rule
  layer; add one (e.g. PostGIS) only when you store boundaries or cache results.
- **The ML model is a file, not a service dependency.** When `models/model.joblib`
  exists the same endpoints start returning `ml_score` and `used_ml: true` — no
  contract change, so your frontend needs no update when ML is switched on.
- **Where your team's work plugs in.** Your frontend owns presentation and the
  map; this service owns the recommendation logic and its explanations. The clean
  line between them is this JSON contract.
