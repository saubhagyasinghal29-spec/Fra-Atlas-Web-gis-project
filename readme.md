# 🗺️ Vansetu — FRA Atlas | AI-Powered WebGIS & Decision Support System

**Vansetu** (*Van* = Forest, *Setu* = Bridge) is an integrated monitoring and decision-support platform for **Forest Rights Act (FRA), 2006** implementation, built for the Ministry of Tribal Affairs, Government of India. Vansetu combines district-level risk intelligence, interactive WebGIS, forest-fire early-warning, and a water-aware crop recommender into a unified, data-driven React application.

**Serving:** Madhya Pradesh · Tripura · Odisha · Telangana · 16 states in India  
**Design:** india.gov.in inspired (Tiranga palette, Noto Sans/Serif typography)  
**Website:** Vansetu  
**Live demo:** [View the dashboard](#getting-started) | **Status:** Production-ready

---
## 👥 Project Team & Credits

**Vansetu** is a collaborative group project developed by:

**Core Development Team:**
- [Saubhagya Singhal] https://github.com/saubhagyasinghal29-spec
- [Rohail Hussain]    https://github.com/TeraCodeRoker
- [Sahil Bhardwaj]    https://github.com/sahilbhardwaj81
- [Sashwat Nain]      https://github.com/sassy121298
- [Sarthak Saini]     https://github.com/nyc-Sarthak
- [Sajan] 

**Advisors & Support:**
- Ministry of Tribal Affairs (MoTA), Government of India
- [Partner University / Organization / Institution Name]

---

## 🤝 Contributing

[Contribution guidelines...]
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
| **Chatbot Assistant (VA)** | Context-aware Q&A + claim guidance | `/chatbot` | RAG pipeline + FRA docs + live data context |
| **Future Analysis** | Multi-year trend forecasting & scenario planning | `/future-analysis` | Time-series ARIMA/Prophet + forest loss projection + climate scenarios |
| **Reports** | Export, data pipeline status | `/reports` | Metadata + download templates |

---

## 🏗️ Tech Stack

| Layer | Technology | Notes |
|-------|-----------|-------|
| **Frontend Framework** | React 19 + Vite | ⚡ Lightning-fast HMR |
| **Routing** | React Router v6 | Client-side navigation |
| **Maps** | Leaflet + react-leaflet + clustering | 500 district markers, heatmaps, live scrubbing |
| **Charts** | Recharts | Interactive ML visualizations |
| **Icons** | lucide-react | 350+ icons, lightweight |
| **Styling** | Hand-built design system | No CSS framework; `src/index.css` + per-page CSS |
| **Crop Recommender Backend** | FastAPI (Python) | Rule engine, FAO-56 water calculations |
| **Chatbot Backend** | FastAPI + LangChain + Sentence Transformers | RAG pipeline, multi-turn memory, live data injection |
| **Forecast Backend** | FastAPI + scikit-learn + statsmodels + TensorFlow | ARIMA, Prophet, LSTM, Bayesian time-series |
| **LLM Integration** | OpenAI / Anthropic / Ollama (pluggable) | 100% abstracted; swap providers in 1 env var |
| **Deployment** | Static SPA (dist/) or embedded | Pairs with Django / Flask / FastAPI backends |

**No external dependencies required for core functionality.** All backends are optional with JavaScript fallbacks.

---

## 📁 Project Structure

```
vansetu/  (FRA Atlas — Forest Rights Act WebGIS)
├── backend/
│   ├── crop-recommender/              # FastAPI service (optional)
│   │   ├── src/croprec/
│   │   │   ├── engine.py              # Core rule engine
│   │   │   ├── water.py               # Water budget logic (FAO-56)
│   │   │   ├── api.py                 # /recommend endpoint
│   │   │   └── knowledge_base.py      # 18-crop definitions
│   │   ├── data/crops.yaml            # Agronomic knowledge base
│   │   ├── API_CONTRACT.md            # Frontend/backend integration spec
│   │   └── requirements.txt           # FastAPI, pydantic, uvicorn
│   │
│   ├── chatbot-va/                    # Chatbot Virtual Assistant (FastAPI)
│   │   ├── src/chatbot/
│   │   │   ├── rag.py                 # Retrieval-augmented generation pipeline
│   │   │   ├── context.py             # Live data injection (FRA, fire, crops)
│   │   │   ├── api.py                 # /chat & /chat/stream endpoints
│   │   │   └── knowledge_base/        # FRA docs, policy guidelines, FAQs
│   │   │       ├── fra_guidelines.md
│   │   │       ├── scheme_rules.md
│   │   │       ├── crop_faqs.md
│   │   │       └── fire_safety.md
│   │   ├── requirements.txt           # langchain, sentence-transformers, llama-index
│   │   └── CHATBOT_SPEC.md            # Architecture & API contract
│   │
│   └── future-analysis/               # Multi-Year Forecasting Service (FastAPI)
│       ├── src/forecast/
│       │   ├── models.py              # ARIMA, Prophet, LSTM, Bayesian models
│       │   ├── scenarios.py           # BAU, Intervention, Climate scenario logic
│       │   ├── climate.py             # IPCC RCP downscaling
│       │   ├── api.py                 # /forecast endpoints
│       │   └── cache.py               # Pre-computed scenarios
│       ├── data/
│       │   ├── historical_fra.csv     # 10+ years FRA trends
│       │   ├── historical_forest.csv  # 10+ years forest cover
│       │   ├── rainfall_series.csv    # Climate data
│       │   └── crop_viability.pkl     # Pre-computed crop suitability matrix
│       ├── requirements.txt           # statsmodels, scikit-learn, tensorflow, pymc
│       └── FORECAST_SPEC.md           # Model documentation & API
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
│   │   ├── forecastData.js            # Time-series forecasts (auto-generated)
│   │   ├── cropKnowledgeBase.js       # 18 crops (mirrors backend)
│   │   ├── chatbotKB.js               # Chatbot RAG knowledge base
│   │   └── constants.js               # Colors, states, districts, schemes
│   │
│   ├── utils/
│   │   ├── cropApi.js                 # FastAPI client + fallback logic
│   │   ├── cropEngine.js              # JS rule engine (offline scorer)
│   │   ├── chatbotEngine.js           # Chatbot RAG retrieval + LLM integration
│   │   ├── forecastEngine.js          # Time-series scenario evaluation
│   │   └── scenarioCalculator.js      # Intervention impact calculations
│   │
│   ├── pages/
│   │   ├── Dashboard.jsx              # / — KPIs, risk distribution, top-15 table
│   │   ├── MapPage.jsx                # /map — Interactive Leaflet WebGIS
│   │   ├── Analytics.jsx              # /analytics — ML charts + live Recharts
│   │   ├── DSS.jsx                    # /dss — CSS scheme eligibility engine
│   │   ├── FireForecast.jsx           # /fire — 7-day fire risk timeline
│   │   ├── CropRecommender.jsx        # /crops — Crop scoring form + results
│   │   ├── Chatbot.jsx                # /chatbot — VA Q&A + multi-turn conversation
│   │   ├── FutureAnalysis.jsx         # /future-analysis — Scenario planning + forecasts
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

### Optional: Enable Live Backend Services

**Crop Recommender** (recommended for demo):
```bash
cd backend/crop-recommender
pip install -r requirements.txt
uvicorn croprec.api:app --reload --app-dir src
# → Accessible at http://127.0.0.1:8000/docs
```

**Chatbot Virtual Assistant** (recommended for demo):
```bash
cd backend/chatbot-va
pip install -r requirements.txt
# Set LLM provider (OpenAI, Anthropic, Llama via Ollama, etc.)
export OPENAI_API_KEY="sk-..."  # or ANTHROPIC_API_KEY, etc.
uvicorn chatbot.api:app --reload --app-dir src --port 8001
# → Accessible at http://127.0.0.1:8001/docs
# → WebSocket endpoint: ws://127.0.0.1:8001/chat/stream (for live streaming)
```

**Future Analysis & Forecasting** (optional, compute-intensive):
```bash
cd backend/future-analysis
pip install -r requirements.txt
uvicorn forecast.api:app --reload --app-dir src --port 8002
# → Accessible at http://127.0.0.1:8002/docs
# → Pre-compute scenarios on first request or schedule async: python scripts/precompute_scenarios.py
```

**Frontend Configuration:**
All three services work with or without backends. Update `src/utils/` configs to point to your service URLs:
```javascript
// src/utils/config.js
export const API_ENDPOINTS = {
  cropRecommender: 'http://127.0.0.1:8000',  // Auto-detected; fallback to JS engine if unavailable
  chatbot: 'http://127.0.0.1:8001',          // Auto-detected; fallback to offline mode if unavailable
  forecast: 'http://127.0.0.1:8002',         // Auto-detected; fallback to pre-computed JSON if unavailable
};
```

The frontend handles missing backends gracefully—no errors, just degraded functionality. Perfect for offline/demo use.

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

### 6. Chatbot Assistant (Vansetu VA) (`/chatbot`)

**Purpose:** Intelligent virtual assistant for real-time Q&A about FRA claims, schemes, crop guidance, and forest-related queries.

**Architecture:**
- **RAG Pipeline** (Retrieval-Augmented Generation): Embeds FRA documentation, policy guidelines, scheme rulebooks, and agronomic FAQs
- **Live Context Integration**: Pulls current district risk data, fire alerts, scheme eligibility, and rainfall forecasts in real-time
- **Multi-turn Conversation**: Maintains user context across messages (e.g., "Show me crops for my district" → chatbot remembers district and soil type)
- **Fallback Logic**: When LLM confidence is low, escalates to human support with full chat transcript

**Key Features:**
- **Guided Q&A:** Pre-built prompts for common queries:
  - *"How do I file an FRA claim?"* → Step-by-step claim process + district-specific status
  - *"Which schemes am I eligible for?"* → DSS eligibility engine + chatbot explanation
  - *"What crops should I grow?"* → Crop Recommender scores + water/soil reasoning
  - *"When is fire season in my area?"* → Fire alert data + fire-safe forestry tips

- **Real-Time Data Injection:** Chatbot cites live sources:
  - "Your district *Indore* has 23 pending claims (2.1% approval rate) — urgent action needed"
  - "High fire risk forecast for 28 June — consider early harvesting"
  - "Soybean scores 92 for Indore in Kharif — water needs 980mm, you have 1100mm rainfall"

- **Multi-Language Support** (planned): Hindi, regional languages via API translation
- **Export Chat as PDF:** User can save conversation for offline reference

**Backend Integration:**
- Calls `POST /chat` endpoint on LLM service (OpenAI, Anthropic, Llama, etc.)
- System prompt baked with FRA knowledge base, scheme rules, agronomic data
- Optional: Fine-tuned model on historical MoTA Q&A datasets

**UI:**
- Sidebar: Pre-set prompt templates + search across past conversations
- Main panel: Chat bubbles (user + bot), loading spinners, sources/citations
- Right panel: Current context card (selected district, date, fire risk, active schemes)
- Mobile: Full-width chat view, collapsible context

**Example Conversation:**
```
User: "I'm from Indore. Can I grow cotton?"
Bot: "Cotton isn't ideal for Indore right now—water needs 700mm, but you only have reliable 500mm during Kharif. 
     Better options: Soybean (92 score), Moong (88 score). 
     See: [Crop Recommender → Indore → Kharif]"

User: "Why is my district high-risk?"
Bot: "Indore's risk score is 72/100 (Moderate-High) due to:
     • Pending claims: 23 (2.1% approval rate—slow processing)
     • Forest loss: 1.2% over 5 years (above average)
     • CFR recognition: 12% (low—means fewer community-managed forests)
     
     Recommendation: [Priority action via DSS: Fast-track claim processing + CFR awareness campaign]"

User: "Any fire risk this week?"
Bot: "High fire risk forecast 27–29 June for your district. 
     → View detailed [Fire Alert Timeline]
     → Safety tip: Clear dead vegetation, ensure water access, alert local authorities."
```

---

### 7. Future Analysis — Multi-Year Forecasting & Scenario Planning (`/future-analysis`)

**Purpose:** Predict FRA implementation outcomes, forest dynamics, and climate impacts over 5–20 years using time-series ML and scenario modeling.

**Data & Models:**
- **Historical Time-Series:** 10+ years of:
  - FRA claim data (filing rates, approval rates, processing time trends)
  - Forest loss/gain (satellite imagery, NDVI trends)
  - Rainfall patterns (seasonal, annual, decadal anomalies)
  - Land-use transitions (cropland ↔ forest ↔ fallow)

- **Forecasting Methods:**
  - **ARIMA/SARIMA:** Time-series decomposition + trend + seasonality (FRA claims, rainfall)
  - **Prophet (Facebook):** Handles multiple seasonalities + trend breaks + holidays
  - **LSTM Neural Networks:** Capture non-linear long-range dependencies in forest loss
  - **Bayesian Structural Time-Series:** Probabilistic intervals (80%, 95% confidence bands)

**Three Scenario Modes:**

#### **Mode 1: Business-as-Usual (BAU)**
Extrapolates current trends without intervention.
- FRA claim approval rate continues at 2.5%/year → 25% by 2034
- Forest loss at −1.2%/year → 15% loss by 2040
- Rainfall variance increases (climate change impact)
- Output: Pessimistic baseline for policy urgency

#### **Mode 2: Intervention Scenarios**
Models impact of specific policy levers:
- "Fast-track claim processing" (reduce processing time by 50%) → +0.8% approval rate/year
- "CFR awareness + support" (increase CFR recognition by 2% annually) → stabilize forest loss
- "Crop diversification subsidy" (promote drought-resilient crops) → reduce crop failure risk by 15%
- "Fire prevention fund" (+$5M/year) → reduce fire incidents by 30%
- Output: Optimistic trajectory showing ROI of interventions

#### **Mode 3: Climate Scenarios**
IPCC-style climate projections:
- **RCP 4.5** (moderate warming): Rainfall −5% by 2050, temp +1.5°C
- **RCP 8.5** (high warming): Rainfall −15% by 2050, temp +3°C
- Maps suitable crops by district (e.g., "Millet becomes ideal in 60% of Rajasthan by 2050")
- Forest loss acceleration/deceleration under climate stress

**UI Components:**

1. **Timeline Scrubber:** 2024 → 2050, play animation showing year-by-year evolution
2. **Scenario Selector:** Dropdown to switch BAU ↔ Intervention ↔ Climate
3. **Multi-Series Chart:**
   - **Left Y-axis:** FRA approval rate (%), forest cover (%)
   - **Right Y-axis:** Average rainfall (mm), temperature (°C)
   - Shaded confidence bands (80%, 95%)
   - Historical data vs. forecasted dotted lines

4. **District Heatmap:** Colors show forecasted risk level in 5, 10, 15, 20 years
   - Red = worsening (higher risk)
   - Green = improving (lower risk)
   - Gray = stable

5. **Intervention Cost-Benefit Panel:**
   - Slider: Adjust intervention budget (0 → $50M)
   - Shows: "Claim approvals in 2034: 12,500 (BAU) → 18,500 (+48%) with $20M/year investment"
   - ROI metric: Benefit/Cost ratio

6. **Crop Viability Atlas:**
   - 18 crops × 500 districts × 5 time horizons
   - Toggle map: "Show districts where Groundnut becomes unsuitable by 2050"
   - Export as GeoTIFF for downstream GIS tools

7. **Download & Report:**
   - Export scenario outputs as CSV (time-series per district)
   - Generate PDF report: Executive summary + key findings + policy recommendations
   - API access: `GET /forecast/district/{id}/scenario/{scenario_type}?year=2050`

**Technical Details:**

```python
# Backend pseudocode (FastAPI)

@app.post("/forecast")
def forecast_fra_trends(
    district_id: str,
    scenario: Literal["bau", "intervention", "climate"],
    intervention_budget: float = 0,  # USD millions/year
    horizon_years: int = 30
) -> ForecastResponse:
    """
    Forecast FRA approval rates, forest cover, and suitable crops.
    """
    # Load historical data
    hist_claims, hist_forest, hist_rainfall = load_timeseries(district_id)
    
    # Fit models
    arima_claims = ARIMA(hist_claims, order=(1,1,1))
    prophet_forest = Prophet()
    lstm_rainfall = LSTMForecaster()
    
    # Generate forecast
    if scenario == "bau":
        forecast_claims = arima_claims.forecast(horizon_years)
        forecast_forest = prophet_forest.forecast(horizon_years)
    elif scenario == "intervention":
        # Apply intervention effect function
        forecast_claims = apply_intervention_boost(
            arima_claims.forecast(horizon_years),
            boost_rate=0.008 * (intervention_budget / 10)  # $10M = +0.8%
        )
    elif scenario == "climate":
        # Apply IPCC downscaling
        forecast_rainfall = adjust_for_climate(lstm_rainfall.forecast(horizon_years))
        forecast_forest = adjust_forest_for_climate(forecast_forest, forecast_rainfall)
    
    # Recommend crops based on forecast conditions
    future_crops = recommend_crops_for_forecast(
        forecast_rainfall, 
        forecast_temp,
        district_id
    )
    
    return ForecastResponse(
        timeseries={
            "claims": forecast_claims,
            "forest": forecast_forest,
            "rainfall": forecast_rainfall,
            "crops": future_crops
        },
        confidence_bands_80=...,
        confidence_bands_95=...,
        policy_impact=calculate_roi(scenario, intervention_budget)
    )
```

**Example Outputs:**

**Chart 1: FRA Approval Rate Forecast**
```
Year  | BAU   | Intervention (+$15M/yr) | Climate (RCP 4.5)
2024  | 2.5%  | 2.5%                   | 2.5%
2030  | 3.2%  | 5.1%                   | 3.1%
2040  | 4.1%  | 7.8%                   | 3.8%
2050  | 4.8%  | 10.2%                  | 3.5%
```

**Chart 2: Forest Cover Forecast (Madhya Pradesh)**
```
Year  | BAU   | Intervention (CFR+Fire) | Climate (RCP 8.5)
2024  | 31%   | 31%                     | 31%
2030  | 29.3% | 30.8%                   | 28.5%
2040  | 27.1% | 31.2%                   | 26.0%
2050  | 24.9% | 31.8%                   | 23.2%
```

**Policy Insight Card:**
```
🎯 SCENARIO ANALYSIS: Intervention Impact
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Investing $15M/year in claim-processing acceleration:

• 2034 Impact: +6,000 additional approvals (19% increase)
• Forest cover gain: +1.5% vs. BAU (climate stabilization)
• Beneficiary income: +₹1,200 crore (net present value)
• Job creation: 3,500 field positions over 10 years
• Cost-benefit ratio: 4.2:1 (₹4.20 return per rupee spent)

Recommendation: Prioritize fast-track processing in 8 high-risk districts.
```

**Deployment:**
- Backend: Time-series forecasting service (Python + scikit-learn + statsmodels + TensorFlow)
- Frontend: React page with Recharts time-series + Leaflet district heatmap
- Cache: Pre-compute BAU + major interventions at deploy time (< 1 min load)
- Real-time: Users can adjust intervention budget with live chart updates (websocket-driven)

---

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
| **Chatbot knowledge base static** | Can't reflect real-time policy updates | Scheduled sync with MoTA knowledge base (planned) |
| **Chatbot LLM hallucination** | May invent scheme details or false crop claims | User warning banner + human escalation for high-risk queries (planned) |
| **Future forecasts assume BAU parameters** | Won't capture unforeseen shocks (pandemics, wars) | Sensitivity analysis + Monte Carlo confidence intervals provided |
| **Climate scenarios (IPCC RCP)** limited to 2050 | Beyond 2050 uncertainty is very high | Use 30-year windows for policy planning |

---

## 🛣️ Roadmap

- [x] Chatbot Assistant (VA) — In development
- [x] Future Analysis (Scenario Planning) — In development
- [ ] Real district boundary polygons (choropleth map instead of points)
- [ ] Live fire-data re-ingestion pipeline (scheduled job to update CSV)
- [ ] Crop yield regression model + `/yield` endpoint
- [ ] Authentication / role-based access (state nodal officers vs. central MoTA staff)
- [ ] PDF export for DSS action plans, fire alerts, and scenario reports
- [ ] Multi-language support for Chatbot (Hindi, regional languages)
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

## 🧪 Testing

### Manual Testing Checklist
- [ ] Dashboard loads all 500 districts
- [ ] Map filters work (by state, risk level, search)
- [ ] Click district → DSS action plan generates
- [ ] Fire timeline animation plays smoothly
- [ ] Crop form submits → scores appear (with or without backend)
- [ ] Analytics charts re-render on state filter
- [ ] Chatbot responds to FRA claims, scheme eligibility, crop, fire queries
- [ ] Chatbot multi-turn memory works (context preserved across messages)
- [ ] Chatbot gracefully falls back to offline mode if service unavailable
- [ ] Future Analysis: BAU scenario loads forecast charts
- [ ] Future Analysis: Intervention budget slider updates charts in real-time
- [ ] Future Analysis: Climate RCP 4.5 vs 8.5 toggle switches scenarios
- [ ] Future Analysis: Export CSV/PDF works
- [ ] Mobile: responsive sidebar collapses

### Unit Tests (TODO)
Scaffold with Vitest:
```bash
npm install -D vitest @testing-library/react
npm run test
```

---

## 🤖 API Contracts

### Crop Recommender

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

### Chatbot Virtual Assistant

```
POST /chat
Content-Type: application/json

{
  "messages": [
    { "role": "user", "content": "How do I file an FRA claim in Indore?" }
  ],
  "district_context": "Indore",  # Optional: inject live district data
  "conversation_id": "conv_abc123"  # For multi-turn memory
}

Response:
{
  "response": "To file an FRA claim in Indore...",
  "sources": [
    { "type": "document", "title": "FRA Guidelines 2023", "url": "..." },
    { "type": "live_data", "metric": "Indore approval rate", "value": "2.1%" }
  ],
  "next_suggestions": [
    "View DSS recommendations for Indore",
    "Check fire alerts for my area",
    "See crop options for my land"
  ],
  "confidence_score": 0.92
}
```

**WebSocket Streaming (for live responses):**
```
WS /chat/stream

Connected → Send:
{
  "messages": [
    { "role": "user", "content": "Explain the RCP 4.5 climate scenario..." }
  ]
}

Receive (streamed):
{ "type": "token", "content": "Based" }
{ "type": "token", "content": " on" }
{ "type": "token", "content": " the" }
...
{ "type": "end", "metadata": { "sources": [...], "confidence": 0.88 } }
```

Full spec: `backend/chatbot-va/CHATBOT_SPEC.md`

---

### Future Analysis & Forecasting

```
POST /forecast
Content-Type: application/json

{
  "district_id": "MP_INDORE",
  "scenario": "intervention",  # "bau" | "intervention" | "climate"
  "intervention_budget_usd_millions": 15,
  "intervention_type": "fast-track-claims",  # "cfr-awareness", "fire-prevention", etc.
  "horizon_years": 30,
  "confidence_level": 95  # 80 or 95
}

Response:
{
  "district": "Indore",
  "scenario": "intervention",
  "timeseries": {
    "years": [2024, 2025, ..., 2054],
    "fra_approval_rate": [2.5, 2.8, 3.1, ..., 10.2],  # % per year
    "forest_cover": [31.0, 30.8, 30.6, ..., 31.8],  # % of district area
    "rainfall": [1100, 1085, 1070, ..., 950],  # mm/year
    "temperature": [24.0, 24.2, 24.4, ..., 26.1],  # °C
    "suitable_crops": [
      { "year": 2024, "rank": 1, "crop": "Soybean", "score": 92 },
      { "year": 2024, "rank": 2, "crop": "Moong", "score": 88 },
      ...
      { "year": 2050, "rank": 1, "crop": "Millet", "score": 91 },  # Shift due to climate
      { "year": 2050, "rank": 2, "crop": "Soybean", "score": 76 }
    ]
  },
  "confidence_bands": {
    "fra_approval_rate_80": { "upper": [3.1, ...], "lower": [2.1, ...] },
    "fra_approval_rate_95": { "upper": [3.5, ...], "lower": [1.7, ...] }
  },
  "policy_impact": {
    "intervention_budget": 15,  # USD millions/year
    "net_present_value": 1200,  # ₹ crores
    "roi": 4.2,  # 4.2:1 benefit:cost
    "additional_approvals_2034": 6000,
    "forest_cover_gain": 1.5  # % vs BAU
  },
  "district_heatmap": [  # Risk levels for each district in 5-year steps
    { "district": "Indore", "year": 2024, "risk_level": "moderate-high" },
    { "district": "Indore", "year": 2029, "risk_level": "moderate" },
    ...
  ]
}
```

**Batch Forecast (all 500 districts):**
```
POST /forecast/batch
Content-Type: application/json

{
  "scenario": "climate",
  "rcp": "4.5",  # or "8.5"
  "horizon_years": 30
}

Response:
{
  "status": "computing",
  "job_id": "job_xyz789",
  "progress_pct": 45
}

# Poll
GET /forecast/batch/job_xyz789/status
→ Eventually returns full results as GeoJSON FeatureCollection
```

Full spec: `backend/future-analysis/FORECAST_SPEC.md`

---

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


## 🙋 Support & Issues

- **Bug reports:** [Open an issue on GitHub](https://github.com/saubhagyasinghal29-spec/Fra-Atlas-Web-gis-project/issues)
- **Feature requests:** [GitHub Discussions](https://github.com/saubhagyasinghal29-spec/Fra-Atlas-Web-gis-project/discussions)

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