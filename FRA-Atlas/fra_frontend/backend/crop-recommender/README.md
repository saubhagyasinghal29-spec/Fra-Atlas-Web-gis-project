# Pan-India crop recommender (water-aware, sustainability-conscious)

Given a district's water, soil, and climate conditions, this system recommends
**which crops to grow** — and, unlike yield-maximising recommenders, it
penalises crops that are unsustainable for the area's groundwater.

It is a **two-layer hybrid**:

1. **Rule engine** (no machine learning, no training data) — encodes agronomy.
   For each crop it scores water match, groundwater sustainability, soil
   compatibility, season, and temperature suitability. This layer alone gives a
   working, fully explainable recommender.
2. **Optional ML layer** — a classifier trained on historical district records
   refines the ranking as a weighted assist (`0.6 × rule + 0.4 × ML`). The
   system runs perfectly without it; drop a trained model in and the same code
   blends it in automatically.

```
District conditions ─┐
                     ├─▶ Rule engine (5 checks) ─▶ rule scores ─┐
Crop knowledge base ─┘                                          ├─▶ combine ─▶ rank + explain ─▶ API / map
                        Historical data ─▶ ML model ─▶ probs ───┘   (ML optional)
```

## Why "sustainability-conscious" is the point

In much of India, what gets grown is driven by MSP procurement and subsidised
power for pumping — which is *why* thirsty crops dominate even in
over-exploited blocks. A recommender trained naively on "what was grown" learns
to repeat that. This system deliberately fights it: the groundwater penalty
scales with each crop's water intensity, so a water-guzzling crop in an
over-exploited block is pushed down even when water is physically available.

## Quick start

```bash
pip install -r requirements.txt

# 1. See it work (no install of the package needed)
python demo.py                      # pan-India worked examples
python tests/test_engine.py         # test suite (also runs under pytest)

# 2. Serve the API
uvicorn croprec.api:app --reload --app-dir src
#   POST /recommend          one district
#   POST /recommend/batch    many districts (the map consumes this)
#   GET  /crops              the knowledge base
#   GET  /health

# 3. Open the map prototype
#   open web/index.html  (it calls the API, or falls back to sample data)

# 4. (optional) Train the ML layer
python train.py --demo              # synthetic data: proves the pipeline runs
python train.py --csv your_data.csv # real labelled data
```

## Layout

```
data/crops.yaml          agronomic knowledge base (extend this for more crops)
src/croprec/
  knowledge_base.py      load + validate crops (pure lookup)
  water.py               available-water calculator (documented coefficients)
  engine.py              the 5 checks + rule scoring (all constants in CONFIG)
  explain.py             per-crop ✓/✕ reasons
  features.py            shared encoder — train & inference use the SAME one
  recommend.py           orchestrator + the ML seam
  api.py                 FastAPI service
train.py                 offline training: time-split, baselines, model.joblib
demo.py                  pan-India examples
tests/test_engine.py     unit tests
web/index.html           Leaflet map prototype
```

## Pan-India scope

The architecture is data-driven, so going national is a data exercise, not a
rewrite. District is a free parameter — any of India's ~750 districts works the
same way. The knowledge base spans major field crops across agro-climatic zones
(rice, wheat, maize, the millets, pulses, oilseeds, cotton, sugarcane, jute,
potato…). Plantation/horticulture crops (tea, coffee, coconut) are out of scope
for v1 because they need a different (perennial) model.

The **temperature check** matters specifically at national scale: without it a
purely water-based model would happily recommend a tropical crop in a cold
Himalayan district. It keeps recommendations inside each crop's viable climate band.

### Where the data comes from

| Need | Source |
|---|---|
| Rainfall, temperature, ET₀ | NASA POWER API (global, free), IMD |
| Groundwater category | Central Ground Water Board (CGWB) block assessment |
| Soil type / properties | ICAR–NBSS&LUP, state soil surveys |
| Historical crop + yield (ML labels) | ICRISAT District Level Database, data.gov.in |
| District boundaries (GIS) | DataMeet, GADM, Survey of India |

## The ML layer (for the optional classifier)

- **Features = the same variables the rule engine uses**, via `features.encode`
  — imported by both `train.py` and `recommend.py` so train/serve can't drift.
- **Label on yield-*success***, not merely "crop grown" — otherwise the model
  re-learns the MSP/subsidy bias the sustainability layer exists to counter.
- **Time-based split** (train early years, test later) — never random, which
  leaks future seasons.
- **Honest baselines** — `train.py` reports majority-class and rule-engine-alone
  accuracy alongside the model. On the synthetic demo the rule engine is hard to
  beat (the labels are derived from it); on real data the model earns its keep
  as a tie-breaker. Either way, the comparison is the point.
- The `0.6 / 0.4` blend weight is a hyperparameter — tune it on validation data;
  don't treat it as fixed.

## Web GIS

The map is a thin frontend over the batch endpoint: it sends all districts to
`POST /recommend/batch` and joins each result to its geometry. The prototype
uses point markers for simplicity; the production path is district **polygons**
(GeoJSON in EPSG:4326, simplified with mapshaper/TopoJSON for performance, or
vector tiles at national scale) for a true choropleth, with toggleable layers
for groundwater stress, rainfall, and soil so the recommended-crop and
groundwater-stress maps can be visually compared.

## Honest limitations

- **District resolution.** Outputs are district averages; a single farm may
  differ. The UI should communicate this rather than imply field-level precision.
- **No economics yet.** Real crop choice is dominated by price, MSP and input
  cost. An economics layer (expected price × yield − cost, shown beside the
  water score) is the highest-value next addition — more than any ML tuning.
- **Water coefficients are assumptions.** `EFFECTIVE_RAINFALL_FRACTION` and
  `MAX_IRRIGATION_SUPPLEMENT_MM` in `water.py` are planning defaults to be
  calibrated against real data.
- **Best used as decision support**, layered with local agronomic and economic
  judgement — not as a standalone command to a farmer.

## Roadmap

- [x] Rule engine + knowledge base (pan-India) + tests
- [x] FastAPI service (single + batch) + ML seam
- [x] Training pipeline (time-split, baselines)
- [x] Map prototype
- [ ] Real data integration (NASA POWER, CGWB, ICRISAT)
- [ ] Polygon choropleth + layer toggles
- [ ] Economics layer
- [ ] Hindi / multi-language; explain-only assistant (grounded, no free-form advice)
```
