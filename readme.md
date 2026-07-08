# 🗺️ Vansetu — FRA Atlas | AI-Powered WebGIS & Decision Support System

**Vansetu** (*Van* = Forest, *Setu* = Bridge) is an integrated monitoring and decision-support platform for **Forest Rights Act (FRA), 2006** implementation, built for the Ministry of Tribal Affairs, Government of India. Vansetu combines district-level risk intelligence, interactive WebGIS, forest-fire early-warning, and a water-aware crop recommender into a unified, data-driven React application.

**Serving:** Madhya Pradesh · Tripura · Odisha · Telangana · 16 states in India  
**Design:** india.gov.in inspired (Tiranga palette, Noto Sans/Serif typography)  
**Website:** Vansetu  


---

## 🎯 Why Vansetu?

The Forest Rights Act demands systematic claim processing across 500+ districts. Vansetu cuts through complexity:

- **Risk Intelligence:** ML-driven risk stratification of all 500 districts across 16 states
- **Real-time Monitoring:** Interactive WebGIS for claim status, forest loss, tribal coverage
- **Predictive Fire Alerts:** 7-day forest-fire forecast powered by ensemble ML models
- **Smart Farming:** Water-aware crop recommendations for FRA beneficiary land (18 crops, FAO-56 agronomy)
- **Action Planning:** Convergence-ready scheme eligibility (PM-KISAN, Jal Jeevan, MGNREGA, PMAY-G, SAUBHAGYA, Van Bandhu Kalyan Yojana)

All data flows from **real ML models**—no placeholder demos.

---

## 📊 Modules At a Glance

| Module | Purpose | Page | Data Source |
|--------|---------|------|-------------|
| **Dashboard + FRA Atlas Map** | Risk stratification of 500 districts | `/`, `/map` | K-Means clustering + PCA + risk index (CSV) |
| **Analytics** | ML model introspection + live Recharts | `/analytics` | Heatmap, PCA scatter, factor importance, live data |
| **Decision Support System (DSS)** | Scheme eligibility + action priority | `/dss` | FRA risk profile × CSS/scheme matrix |
| **Fire Alert** | 7-day forest-fire forecast | `/fire` | Random Forest / XGBoost / Ensemble / LSTM classifiers |
| **Crop Recommender** | Water-aware crop suitability + rankings | `/crops` | 18-crop agronomic knowledge base + rule engine |
| **Reports** | Export, data pipeline status | `/reports` | Metadata + download templates |

---

## 🏗️ Tech Stack

| Layer | Technology | Notes |
|-------|-----------|-------|
| **Framework** | React 19 + Vite | ⚡ Lightning-fast HMR |
| **Routing** | React Router v6 | Client-side navigation |
| **Maps** | Leaflet + react-leaflet + clustering | 500 district markers, heatmaps, live scrubbing |
| **Charts** | Recharts | Interactive ML visualizations |
| **Icons** | lucide-react | 350+ icons, lightweight |
| **Backend (Optional)** | FastAPI (Python) | Crop recommender API, `/recommend` endpoint |
| **Styling** | Hand-built design system | No CSS framework; `src/index.css` + per-page CSS |
| **Deployment** | Static SPA (dist/) or embedded | Pairs with Django / Flask / FastAPI backends |

**No external dependencies required for core functionality.** Backend is optional and has a JS fallback.

---

## 📁 Project Structure

```
vansetu/  (FRA Atlas — Forest Rights Act WebGIS)
├── backend/
│   └── crop-recommender/              # FastAPI service (optional)
│       ├── src/croprec/
│       │   ├── engine.py              # Core rule engine
│       │   ├── water.py               # Water budget logic (FAO-56)
│       │   ├── api.py                 # /recommend endpoint
│       │   └── knowledge_base.py      # 18-crop definitions
│       ├── data/crops.yaml            # Agronomic knowledge base
│       ├── API_CONTRACT.md            # Frontend/backend integration spec
│       └── requirements.txt           # FastAPI, pydantic, uvicorn
│
├── public/
│   └── images/                        # ML output charts
│       ├── factor_heatmap.png
│       ├── pca_clusters.png
│       ├── risk_ranking.png
│       ├── fire_feature_importance.png
│       ├── fire_roc_curves.png
│       └── fire_pr_curves.png
│
├── scripts/
│   ├── gen_data.py                    # Regenerate fraData.js from CSV
│   └── gen_fire_data.py               # Regenerate fireData.js from CSV
│
├── src/
│   ├── components/
│   │   └── layout/                    # Layout, Panel, RiskBadge (shared UI)
│   │
│   ├── data/
│   │   ├── fraData.js                 # 500 FRA districts (auto-generated)
│   │   ├── fireData.js                # 280 fire forecasts (auto-generated)
│   │   ├── cropKnowledgeBase.js       # 18 crops (mirrors backend)
│   │   └── constants.js               # Colors, states, districts, schemes
│   │
│   ├── utils/
│   │   ├── cropApi.js                 # FastAPI client + fallback logic
│   │   └── cropEngine.js              # JS rule engine (offline scorer)
│   │
│   ├── pages/
│   │   ├── Dashboard.jsx              # / — KPIs, risk distribution, top-15 table
│   │   ├── MapPage.jsx                # /map — Interactive Leaflet WebGIS
│   │   ├── Analytics.jsx              # /analytics — ML charts + live Recharts
│   │   ├── DSS.jsx                    # /dss — CSS scheme eligibility engine
│   │   ├── FireForecast.jsx           # /fire — 7-day fire risk timeline
│   │   ├── CropRecommender.jsx        # /crops — Crop scoring form + results
│   │   └── Reports.jsx                # /reports — Export, status checks
│   │
│   ├── App.jsx                        # Router setup
│   └── main.jsx                       # Entry point
│
├── index.html                         # HTML shell
├── package.json                       # npm dependencies
└── vite.config.js                     # Vite configuration
```

---

## 🚀 Quick Start

### Install & Run

```bash
# Clone the Vansetu repository
git clone https://github.com/saubhagyasinghal29-spec/Fra-Atlas-Web-gis-project.git
cd Fra-Atlas-Web-gis-project  # Vansetu

# Install dependencies
npm install

# Start dev server
npm run dev
# → Open http://localhost:5173
```

### Build for Production

```bash
npm run build        # Creates dist/ folder
npm run preview      # Test production build locally
```

### Optional: Enable Live Crop Scoring

```bash
cd backend/crop-recommender
pip install -r requirements.txt
uvicorn croprec.api:app --reload --app-dir src
# → Accessible at http://127.0.0.1:8000/docs
```

The Crop Recommender works with or without the backend. Without it, the page falls back transparently to a JavaScript implementation of the same scoring logic.

---

## 📍 Module Deep Dives

### 1. Vansetu Risk Dashboard & Atlas Map (`/`, `/map`)

**Data:** `fra_risk_scores.csv` → 500 districts across 16 states

Each district is scored on a **Risk Index** (0–100) derived from:
- K-Means clustering + PCA reduction
- 8 composite factors: approval rate, pending claims, processing time, forest loss, tribal coverage, CFR recognition, rejections, encroachment density

**Dashboard (`/`):**
- Animated KPI counters (total districts, critical alerts, avg processing time)
- Risk distribution donut + state-wise stacked bar chart
- Top-15 high-risk table with drill-down links
- Focused-state card carousel with mini-map preview
- Critical alert digest (top 5 by urgency)

**Map (`/map`):**
- Full-screen Leaflet map with 500 districts as clustered circle markers
- Marker color: Risk level (🔴 Critical / 🟠 Moderate / 🟡 Good / 🟢 Excellent)
- Filter toolbar: risk level, state, free-text search, basemap toggle
- Click district → side panel with all 8 metrics + DSS deeplink
- Performance: clusters dynamically based on zoom

---

### 2. Decision Support System (`/dss`)

**Purpose:** Turn FRA risk intelligence into actionable policy.

Given a state + district, DSS layers Central Sector Scheme (CSS) eligibility and generates a **priority action plan**:

**Schemes Checked:**
- PM-KISAN (income support)
- Jal Jeevan Mission (water access)
- MGNREGA (rural employment)
- PMAY-G (rural housing)
- SAUBHAGYA (electricity)
- Van Bandhu Kalyan Yojana (tribal welfare)
- + 4 other schemes

**Output:** Action priorities tagged by urgency:
- **Immediate** (pending claims > 35%, processing time > 180 days, forest loss > 2%)
- **Short-term** (moderate thresholds)
- **Medium-term** (preventive/monitoring)

**Convergence Panel:** DAJGUA 3-ministry view (Ministry of Environment / Ministry of Tribal Affairs / Ministry of Agriculture)

---

### 3. Analytics (`/analytics`)

Embeds ML team's evaluation charts alongside **live Recharts computations**:

**Static Outputs:**
- Factor correlation heatmap (8 metrics × 8 metrics)
- PCA cluster scatter (Risk Index vs. PC1/PC2)
- District risk ranking (top 50)

**Live Interactive Charts:**
- State-metric bar chart (switchable between 6 metrics, 500 points)
- Risk Index vs. Approval Rate scatter (colored by risk level, click to filter)

All data sourced from the same `fraData.js` for consistency.

---

### 4. Fire Alert — 7-Day Forecast (`/fire`)

**Data:** `fire_forecast_7day.csv` → 280 records (40 locations × 7 days, 24–30 June)

**Models Evaluated:**
- Random Forest (ROC-AUC 0.68, PR-AUC 0.65)
- XGBoost (ROC-AUC 0.70, PR-AUC 0.67)
- Ensemble (ROC-AUC 0.69, PR-AUC 0.66)
- LSTM (ROC-AUC 0.67, PR-AUC 0.64)

**Features Ranked:** LST (Land Surface Temperature), day-of-year, NDVI, month, rainfall, wind speed, forest cover

**UI:**
- Interactive Leaflet map (40 locations)
- Circle marker size ∝ fire probability; color ∝ risk (High/Medium/Low)
- **7-day timeline scrubber** with ▶ Play/Pause animation
- Risk-level filter + per-location popups
- Top-8 highest-risk list (click to fly-to location)
- 7-day trend chart (stacked High/Medium/Low zone counts)
- Model performance comparison panel + ROC/PR curve images

---

### 5. Crop Recommender (`/crops`)

**Data:** `crops.yaml` — 18-crop pan-India agronomic knowledge base (FAO-56 water requirements, ICAR package-of-practices)

**Input Form:**
- District (dropdown, 150+ districts, color-coded by groundwater status)
- Rainfall, temperature, irrigation cover, groundwater status, soil type, season

**Scoring Logic (0–100 per crop):**
1. Water-budget match (rainfall + irrigation − crop requirement)
2. Groundwater sustainability penalty (−% × water intensity)
3. Soil compatibility (% supported soil types)
4. Season match (current season in crop's growing window?)
5. Temperature suitability (within FAO range?)

**Output:**
- Ranked list of crops (1st = highest score)
- Each with ✓/✕ reasons (e.g., *"Penalised −8: low-water crop in critical block"*)
- Interactive district map, groundwater color-coded
- ML-score placeholder wired through (reserved for future trained model)

**Backend Integration:**
- Calls `POST /recommend` on FastAPI when reachable (documented in `API_CONTRACT.md`)
- Falls back transparently to JavaScript version (`src/utils/cropEngine.js`) if service unavailable
- **Page never breaks in demos.**

---

## 🔄 Data Pipeline

```
ML Training (Colab / Jupyter)
    │
    ├─→ fra_risk_scores.csv ──→ scripts/gen_data.py ──→ src/data/fraData.js
    ├─→ fire_forecast_7day.csv ──→ scripts/gen_fire_data.py ──→ src/data/fireData.js
    ├─→ factor_heatmap.png ──→ public/images/
    ├─→ pca_clusters.png ──→ public/images/
    ├─→ risk_ranking.png ──→ public/images/
    ├─→ fire_feature_importance.png ──→ public/images/
    ├─→ fire_roc_curves.png ──→ public/images/
    ├─→ fire_pr_curves.png ──→ public/images/
    └─→ crops.yaml ──→ backend/crop-recommender/data/
                      (served live via FastAPI OR mirrored
                       in src/data/cropKnowledgeBase.js
                       for offline fallback)
```

**All data pre-baked at build time** except crop recommendations, which prefer live API calls.

---

## 🔗 Backend Integration

This is a **frontend-only deliverable** designed to integrate with any backend:

### Django Backend
```python
# Serve dist/ as a static template
npm run build
# Then mount your API under /api/ and configure CORS in your views.py
```

### FastAPI (Crop Module)
Already bundled and documented — see `backend/crop-recommender/API_CONTRACT.md`.

### CORS Configuration
The bundled FastAPI crop service has `allow_origins=["*"]` in dev. **Lock this to your real origin before production deployment.**

---

## 🔄 Updating Data When Models Re-run

### FRA Risk Scores
```bash
python3 scripts/gen_data.py path/to/fra_risk_scores.csv
```

### Fire Forecast
```bash
python3 scripts/gen_fire_data.py path/to/fire_forecast_7day.csv
```

### Rebuild & Deploy
```bash
npm run build
# Deploy dist/ to your server
```

### Crop Knowledge Base
Edit `backend/crop-recommender/data/crops.yaml` directly — the live API will serve it immediately. Regenerate `src/data/cropKnowledgeBase.js` to keep the offline fallback in sync (use `gen_crop_kb.py` following the same pattern as above).

### ML Chart Images
Drop updated charts (heatmap, PCA, risk ranking, ROC/PR curves, feature importance) into `public/images/` with matching filenames.

---

## ⚠️ Known Limitations & Caveats

| Limitation | Impact | Workaround |
|-----------|--------|-----------|
| **Fire forecast dates fixed** (24–30 June 2024) | Timeline won't update without re-ingestion | Implement live re-ingestion pipeline (planned) |
| **District coordinates are centroids** (not official boundaries) | Map shows points, not polygons | Use DataMeet/GADM shapefiles for choropleth |
| **Crop Recommender demo districts** (5–7 sample points) | Not full district coverage | Extend `CROP_DISTRICTS` in `constants.js` |
| **No yield prediction** (only suitability ranking) | Can't forecast tons/hectare | ML yield regressor would plug into `ml_score` field (pending) |
| **Water-budget coefficients uncalibrated** | FAO-56 planning defaults, not validated | See `water.py` docstring; calibrate for your region |

---

## 🛣️ Roadmap

- [ ] Real district boundary polygons (choropleth map instead of points)
- [ ] Live fire-data re-ingestion pipeline (scheduled job to update CSV)
- [ ] Crop yield regression model + `/yield` endpoint
- [ ] Authentication / role-based access (state nodal officers vs. central MoTA staff)
- [ ] PDF export for DSS action plans and fire alerts
- [ ] Mobile-responsive optimization (currently desktop-optimized)
- [ ] Dark mode support
- [ ] Scheme convergence visualization (sankey / flowchart view)

---

## 📦 Deployment

### Development
```bash
npm run dev
```

### Production
```bash
npm run build
# Serve dist/ via your CDN or web server (Nginx, Apache, Vercel, Netlify, etc.)
```

### With Django Backend
```
MyDjangoApp/
├── static/
│   └── dist/          # Symlink or copy from npm run build
├── templates/
│   └── index.html     # Serve dist/index.html here
└── views.py           # API endpoints at /api/
```

### With FastAPI Backend (Crop Module)
```bash
# Start FastAPI service
uvicorn croprec.api:app --host 0.0.0.0 --port 8000 --reload

# Start React dev server (proxies to 8000 for /recommend)
npm run dev
```

---

## 📊 Sample Data Files

The project includes sample data for immediate demo use:

- **fraData.js** — 500 districts with risk scores (auto-generated from CSV)
- **fireData.js** — 280 fire forecasts for 40 locations over 7 days
- **cropKnowledgeBase.js** — 18 crops with water/soil/temperature profiles
- **ML output charts** — PCA scatter, heatmap, ROC/PR curves, feature importance

All generated from real ML models—not templates.

---

## 🧪 Testing

### Manual Testing Checklist
- [ ] Dashboard loads all 500 districts
- [ ] Map filters work (by state, risk level, search)
- [ ] Click district → DSS action plan generates
- [ ] Fire timeline animation plays smoothly
- [ ] Crop form submits → scores appear (with or without backend)
- [ ] Analytics charts re-render on state filter
- [ ] Mobile: responsive sidebar collapses

### Unit Tests (TODO)
Scaffold with Vitest:
```bash
npm install -D vitest @testing-library/react
npm run test
```

---

## 📝 API Contract (Crop Recommender)

```
POST /recommend
Content-Type: application/json

{
  "district": "Indore",
  "rainfall_mm": 1100,
  "temp_celsius": 24,
  "irrigation_cover_pct": 45,
  "groundwater_status": "critical",
  "soil_type": "black",
  "season": "kharif"
}

Response:
{
  "district": "Indore",
  "recommendations": [
    {
      "crop": "Soybean",
      "score": 92,
      "used_ml": false,
      "ml_score": null,
      "reasons": [
        { "type": "✓", "text": "Excellent water-budget match: 980mm needed" },
        { "type": "✕", "text": "Penalised −5: groundwater critical block" }
      ]
    },
    ...
  ]
}
```

Full spec: `backend/crop-recommender/API_CONTRACT.md`

---

## 🤝 Contributing

1. **Fork** the repository
2. **Create a branch** (`git checkout -b feature/your-feature`)
3. **Commit changes** (`git commit -am 'Add feature'`)
4. **Push** (`git push origin feature/your-feature`)
5. **Open a Pull Request**

### Adding a New Scheme to DSS
Edit `src/data/constants.js` → `SCHEMES` array, then update `src/pages/DSS.jsx` eligibility logic.

### Adding a New Crop
1. Append to `backend/crop-recommender/data/crops.yaml`
2. Regenerate `src/data/cropKnowledgeBase.js` (use `gen_crop_kb.py`)
3. Test in CropRecommender page

---

## 📄 License

[Specify your license here — e.g., MIT, Apache 2.0, or Government of India standard]

---

## 🙋 Support & Issues

- **Bug reports:** [Open an issue on GitHub](https://github.com/saubhagyasinghal29-spec/Fra-Atlas-Web-gis-project/issues)
- **Feature requests:** [GitHub Discussions](https://github.com/saubhagyasinghal29-spec/Fra-Atlas-Web-gis-project/discussions)
- **Contact:** For MoTA integration support, reach out to [your contact/organization]

---

## 🎓 References & Resources

- **Forest Rights Act, 2006:** [Ministry of Tribal Affairs](https://tribal.nic.in)
- **FAO-56 Crop Water Requirements:** [FAO Irrigation & Drainage Paper 56](http://www.fao.org/3/x0490e/x0490e00.htm)
- **GIS Base Layers:** [OpenStreetMap](https://www.openstreetmap.org/), [Leaflet Documentation](https://leafletjs.com/)
- **React Best Practices:** [React Docs](https://react.dev)
- **Vite Guide:** [Vite Documentation](https://vitejs.dev)

---

## 🙏 Acknowledgments

**Vansetu** is built with data and insights from ML models trained on real FRA, fire, and agronomic datasets. Designed for the **Ministry of Tribal Affairs, Government of India**, in service of transparent, data-driven policy for tribal land rights and sustainable forest management.

---

**Made with ❤️ for the Forest Rights Act, 2006 | Vansetu — Bridging Forests & Communities**