import { useState, useEffect, useRef } from 'react';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import {
  CROP_DISTRICTS, GROUNDWATER_COLORS, SOIL_TYPES,
  GROUNDWATER_LEVELS, SEASONS, CROP_API_BASE,
} from '../data/constants';
import { recommendOne, checkHealth, ValidationError } from '../utils/cropApi';
import { Panel, PanelHeader, PanelBody } from '../components/layout/Panel';
import './CropRecommender.css';

const scoreColor = (s) => (s >= 80 ? '#1D9E75' : s >= 45 ? '#BA7517' : '#888780');

export default function CropRecommender() {
  const mapRef = useRef(null);
  const leafletMap = useRef(null);
  const markersRef = useRef([]);

  const [apiLive, setApiLive] = useState(null); // null = checking
  const [conditions, setConditions] = useState(CROP_DISTRICTS[0]);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // Health check on mount
  useEffect(() => {
    checkHealth().then(setApiLive);
  }, []);

  // Init map with district markers colored by groundwater
  useEffect(() => {
    if (leafletMap.current) return;
    const map = L.map(mapRef.current, { center: [22.8, 80.0], zoom: 5 });
    leafletMap.current = map;
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      attribution: '© OpenStreetMap', maxZoom: 10,
    }).addTo(map);

    CROP_DISTRICTS.forEach((d) => {
      const marker = L.circleMarker([d.lat, d.lng], {
        radius: 9,
        fillColor: GROUNDWATER_COLORS[d.groundwater],
        color: '#fff',
        weight: 2,
        fillOpacity: 0.9,
      });
      marker.bindTooltip(d.district, { direction: 'top' });
      marker.on('click', () => {
        setConditions(d);
        runRecommend(d);
      });
      marker.addTo(map);
      markersRef.current.push({ marker, district: d.district });
    });
    return () => { map.remove(); leafletMap.current = null; };
  }, []);

  async function runRecommend(cond) {
    setLoading(true);
    setError(null);
    try {
      const data = await recommendOne({
        district: cond.district,
        rainfall_mm: Number(cond.rainfall_mm),
        groundwater: cond.groundwater,
        irrigation_pct: Number(cond.irrigation_pct),
        soil: cond.soil,
        season: cond.season,
        temperature_c: Number(cond.temperature_c),
      });
      setResult(data);
      // Pan to district
      leafletMap.current?.setView([cond.lat ?? 22.8, cond.lng ?? 80], cond.lat ? 7 : 5);
    } catch (e) {
      if (e instanceof ValidationError) {
        setError(formatValidationError(e.detail));
      } else {
        setError('Could not get a recommendation. Check inputs and try again.');
      }
      setResult(null);
    } finally {
      setLoading(false);
    }
  }

  function updateField(field, value) {
    setConditions((c) => ({ ...c, [field]: value }));
  }

  return (
    <div className="crop-page">
      <div className="crop-inner">
        {/* Header */}
        <div className="crop-header-row">
          <div>
            <h2 className="page-title">🌾 Water-Aware Crop Recommender</h2>
            <p className="crop-subtitle">
              Sustainability-conscious crop recommendations for FRA patta-holder farmlands.
              Scores each crop on water budget, groundwater stress, soil, season and temperature.
            </p>
          </div>
          <div className={`api-status ${apiLive === null ? 'checking' : apiLive ? 'live' : 'offline'}`}>
            <span className="status-dot" />
            {apiLive === null ? 'Checking service…' : apiLive ? 'Live API connected' : 'Offline mode (local engine)'}
          </div>
        </div>

        <div className="crop-grid">
          {/* Left: form */}
          <div className="crop-left">
            <Panel>
              <PanelHeader icon="📋" title="District Conditions" />
              <PanelBody>
                <div className="crop-form">
                  <div className="form-group">
                    <label className="form-label">District / Quick-select</label>
                    <select className="form-control" value={conditions.district}
                      onChange={(e) => {
                        const d = CROP_DISTRICTS.find((x) => x.district === e.target.value);
                        if (d) setConditions(d);
                      }}>
                      {CROP_DISTRICTS.map((d) => <option key={d.district} value={d.district}>{d.district}</option>)}
                    </select>
                  </div>

                  <div className="form-row">
                    <div className="form-group">
                      <label className="form-label">Rainfall (mm)</label>
                      <input type="number" className="form-control" min="0" value={conditions.rainfall_mm}
                        onChange={(e) => updateField('rainfall_mm', e.target.value)} />
                    </div>
                    <div className="form-group">
                      <label className="form-label">Temperature (°C)</label>
                      <input type="number" className="form-control" value={conditions.temperature_c}
                        onChange={(e) => updateField('temperature_c', e.target.value)} />
                    </div>
                  </div>

                  <div className="form-group">
                    <label className="form-label">Irrigation cover: {conditions.irrigation_pct}%</label>
                    <input type="range" className="form-range" min="0" max="100" value={conditions.irrigation_pct}
                      onChange={(e) => updateField('irrigation_pct', e.target.value)} />
                  </div>

                  <div className="form-group">
                    <label className="form-label">Groundwater status</label>
                    <select className="form-control" value={conditions.groundwater}
                      onChange={(e) => updateField('groundwater', e.target.value)}>
                      {GROUNDWATER_LEVELS.map((g) => <option key={g} value={g}>{g}</option>)}
                    </select>
                  </div>

                  <div className="form-row">
                    <div className="form-group">
                      <label className="form-label">Soil type</label>
                      <select className="form-control" value={conditions.soil}
                        onChange={(e) => updateField('soil', e.target.value)}>
                        {SOIL_TYPES.map((s) => <option key={s} value={s}>{s}</option>)}
                      </select>
                    </div>
                    <div className="form-group">
                      <label className="form-label">Season</label>
                      <select className="form-control" value={conditions.season}
                        onChange={(e) => updateField('season', e.target.value)}>
                        {SEASONS.map((s) => <option key={s} value={s}>{s}</option>)}
                      </select>
                    </div>
                  </div>

                  <button className="crop-submit" onClick={() => runRecommend(conditions)} disabled={loading}>
                    {loading ? 'Scoring crops…' : '🌱 Recommend Crops'}
                  </button>

                  {error && <div className="crop-error">{error}</div>}
                </div>
              </PanelBody>
            </Panel>

            {/* Map */}
            <Panel>
              <PanelHeader icon="🗺️" title="District Map" subtitle="Coloured by groundwater" />
              <div className="crop-map-wrap">
                <div ref={mapRef} className="crop-map" />
                <div className="crop-legend">
                  <div className="legend-title">Groundwater</div>
                  {GROUNDWATER_LEVELS.map((g) => (
                    <div key={g} className="legend-item">
                      <span className="legend-dot" style={{ background: GROUNDWATER_COLORS[g] }} />{g}
                    </div>
                  ))}
                </div>
              </div>
            </Panel>
          </div>

          {/* Right: results */}
          <div className="crop-right">
            <Panel>
              <PanelHeader
                icon="🌱"
                title="Ranked Crop Recommendations"
                subtitle={result ? `${result.district}` : ''}
                actions={result?.usedFallback && <span className="fallback-tag">local engine</span>}
              />
              <PanelBody>
                {!result ? (
                  <div className="crop-empty">
                    <div style={{ fontSize: 36, marginBottom: 10 }}>🌾</div>
                    <div>Set district conditions and click <strong>Recommend Crops</strong> — or click a district on the map.</div>
                  </div>
                ) : (
                  <>
                    {/* Water budget */}
                    <div className="water-budget">
                      <div className="wb-item">
                        <div className="wb-val">{result.available_water_mm}</div>
                        <div className="wb-label">Available water (mm)</div>
                      </div>
                      <div className="wb-split">
                        <span>💧 {result.effective_rain_mm} mm rain</span>
                        <span>🚰 {result.irrigation_mm} mm irrigation</span>
                      </div>
                      {result.used_ml && <span className="ml-tag">ML model active</span>}
                    </div>

                    {/* Crop cards */}
                    <div className="crop-list">
                      {result.recommendations.slice(0, 8).map((r, i) => (
                        <div key={r.crop} className="crop-card">
                          <div className="crop-card-head">
                            <div className="crop-rank">{i + 1}</div>
                            <div className="crop-name">{r.crop}</div>
                            <div className="crop-season-tag">{r.season}</div>
                            <div className="crop-score" style={{ color: scoreColor(r.final_score) }}>
                              {r.final_score.toFixed(0)}
                            </div>
                          </div>
                          <div className="crop-bar">
                            <div style={{ width: `${r.final_score}%`, background: scoreColor(r.final_score) }} />
                          </div>
                          <div className="crop-meta">
                            <span>Water target: {Math.round(r.water_target_mm)} mm</span>
                            {r.ml_score != null && <span>· ML: {r.ml_score.toFixed(0)}</span>}
                          </div>
                          <ul className="crop-reasons">
                            {r.reasons.map((reason, j) => (
                              <li key={j} className={reason.ok ? 'ok' : 'no'}>
                                {reason.ok ? '✓' : '✕'} {reason.text}
                              </li>
                            ))}
                          </ul>
                        </div>
                      ))}
                    </div>
                  </>
                )}
              </PanelBody>
            </Panel>
          </div>
        </div>

        {/* API note */}
        <div className="crop-api-note">
          <strong>Backend:</strong> This page calls <code>POST {CROP_API_BASE}/recommend</code> (FastAPI).
          When the service isn't running it transparently falls back to the bundled rule engine so the UI keeps working.
          Start the backend with <code>uvicorn croprec.api:app --reload --app-dir src</code>.
        </div>
      </div>
    </div>
  );
}

function formatValidationError(detail) {
  if (Array.isArray(detail?.detail)) {
    return detail.detail.map((d) => `${d.loc?.slice(-1)[0]}: ${d.msg}`).join('; ');
  }
  return 'Some inputs were invalid. Please review the form.';
}
