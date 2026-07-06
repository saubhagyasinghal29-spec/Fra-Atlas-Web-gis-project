import { useState, useEffect, useRef, useMemo } from 'react';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell, LineChart, Line, CartesianGrid, Legend } from 'recharts';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import { FIRE_DATA, FIRE_DATES } from '../data/fireData';
import { FIRE_RISK_COLORS, FIRE_RISK_BG, FIRE_MODELS, FIRE_DRIVERS } from '../data/constants';
import { Panel, PanelHeader, PanelBody } from '../components/layout/Panel';
import './FireForecast.css';

const RISK_ORDER = { High: 0, Medium: 1, Low: 2 };

function FireBadge({ level }) {
  return (
    <span className="fire-badge" style={{ background: FIRE_RISK_BG[level], color: FIRE_RISK_COLORS[level] }}>
      {level === 'High' ? '🔥' : level === 'Medium' ? '⚠️' : '🌿'} {level}
    </span>
  );
}

export default function FireForecast() {
  const mapRef = useRef(null);
  const leafletMap = useRef(null);
  const layerGroup = useRef(null);

  const [dateIdx, setDateIdx] = useState(0);
  const [playing, setPlaying] = useState(false);
  const [riskFilter, setRiskFilter] = useState('');
  const [selected, setSelected] = useState(null);

  const activeDate = FIRE_DATES[dateIdx];

  // Records for the active day
  const dayRecords = useMemo(
    () => FIRE_DATA.filter((d) => d.date === activeDate),
    [activeDate]
  );

  const dayCounts = useMemo(() => {
    const c = { High: 0, Medium: 0, Low: 0 };
    dayRecords.forEach((d) => { c[d.risk]++; });
    return c;
  }, [dayRecords]);

  // 7-day trend: count of High-risk locations per day
  const trend = useMemo(
    () =>
      FIRE_DATES.map((date) => {
        const recs = FIRE_DATA.filter((d) => d.date === date);
        const avg = recs.reduce((s, d) => s + d.prob, 0) / (recs.length || 1);
        return {
          date: date.slice(5), // MM-DD
          High: recs.filter((d) => d.risk === 'High').length,
          Medium: recs.filter((d) => d.risk === 'Medium').length,
          Low: recs.filter((d) => d.risk === 'Low').length,
          avgProb: +(avg * 100).toFixed(1),
        };
      }),
    []
  );

  // Init map once
  useEffect(() => {
    if (leafletMap.current) return;
    const map = L.map(mapRef.current, { center: [21, 80.5], zoom: 6 });
    leafletMap.current = map;
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      attribution: '© OpenStreetMap', maxZoom: 12,
    }).addTo(map);
    layerGroup.current = L.layerGroup().addTo(map);
    return () => { map.remove(); leafletMap.current = null; };
  }, []);

  // Redraw markers whenever day / filter changes
  useEffect(() => {
    const group = layerGroup.current;
    if (!group) return;
    group.clearLayers();

    dayRecords
      .filter((d) => !riskFilter || d.risk === riskFilter)
      .forEach((d) => {
        const radius = 5 + d.prob * 14;
        const marker = L.circleMarker([d.lat, d.lng], {
          radius,
          fillColor: FIRE_RISK_COLORS[d.risk],
          color: 'rgba(255,255,255,0.85)',
          weight: 1.3,
          fillOpacity: 0.78,
        });
        marker.bindPopup(`
          <div style="font-family:'Noto Sans',sans-serif;min-width:170px">
            <div style="font-weight:700;font-size:13px;margin-bottom:4px">📍 Location #${d.id}</div>
            <div style="font-size:12px;color:#6b6f8a">${d.lat.toFixed(3)}, ${d.lng.toFixed(3)}</div>
            <div style="margin-top:6px;display:flex;justify-content:space-between;font-size:12.5px">
              <span style="color:#6b6f8a">Fire probability</span>
              <span style="font-weight:700;color:${FIRE_RISK_COLORS[d.risk]}">${(d.prob * 100).toFixed(1)}%</span>
            </div>
            <div style="margin-top:3px;display:flex;justify-content:space-between;font-size:12.5px">
              <span style="color:#6b6f8a">Risk level</span>
              <span style="font-weight:700;color:${FIRE_RISK_COLORS[d.risk]}">${d.risk}</span>
            </div>
            <div style="margin-top:3px;font-size:11.5px;color:#8a8472">${d.date}</div>
          </div>
        `);
        marker.on('click', () => setSelected(d));
        group.addLayer(marker);
      });
  }, [dayRecords, riskFilter]);

  // Animation loop
  useEffect(() => {
    if (!playing) return;
    const id = setInterval(() => {
      setDateIdx((i) => (i + 1) % FIRE_DATES.length);
    }, 1100);
    return () => clearInterval(id);
  }, [playing]);

  const topRisk = useMemo(
    () => dayRecords.slice().sort((a, b) => b.prob - a.prob).slice(0, 8),
    [dayRecords]
  );

  return (
    <div className="fire-page">
      <div className="fire-inner">
        {/* Header */}
        <div className="fire-header">
          <div>
            <h2 className="page-title">🔥 Forest Fire Early-Warning System</h2>
            <p className="fire-subtitle">
              7-day fire-probability forecast across {dayRecords.length} monitored forest locations.
              Powered by an LSTM + Random Forest ensemble trained on LST, NDVI, rainfall and seasonal signals.
            </p>
          </div>
        </div>

        {/* KPI strip for active day */}
        <div className="fire-kpi-strip">
          {[
            { key: 'High',   icon: '🔥', label: 'High Risk Zones' },
            { key: 'Medium', icon: '⚠️', label: 'Medium Risk Zones' },
            { key: 'Low',    icon: '🌿', label: 'Low Risk Zones' },
          ].map(({ key, icon, label }) => (
            <div key={key} className="fire-kpi" style={{ borderLeftColor: FIRE_RISK_COLORS[key] }}>
              <span className="fire-kpi-icon">{icon}</span>
              <div>
                <div className="fire-kpi-val" style={{ color: FIRE_RISK_COLORS[key] }}>{dayCounts[key]}</div>
                <div className="fire-kpi-label">{label}</div>
              </div>
            </div>
          ))}
          <div className="fire-kpi" style={{ borderLeftColor: 'var(--navy)' }}>
            <span className="fire-kpi-icon">📅</span>
            <div>
              <div className="fire-kpi-val" style={{ color: 'var(--navy)' }}>{activeDate.slice(5)}</div>
              <div className="fire-kpi-label">Forecast Date</div>
            </div>
          </div>
        </div>

        {/* Timeline scrubber */}
        <Panel>
          <PanelBody>
            <div className="timeline-row">
              <button className="play-btn" onClick={() => setPlaying((p) => !p)}>
                {playing ? '⏸ Pause' : '▶ Play 7-day'}
              </button>
              <div className="timeline-track">
                {FIRE_DATES.map((date, i) => (
                  <button
                    key={date}
                    className={`timeline-day ${i === dateIdx ? 'active' : ''}`}
                    onClick={() => { setDateIdx(i); setPlaying(false); }}
                  >
                    <span className="td-dow">{new Date(date).toLocaleDateString('en-IN', { weekday: 'short' })}</span>
                    <span className="td-date">{date.slice(8)}/{date.slice(5, 7)}</span>
                  </button>
                ))}
              </div>
            </div>
          </PanelBody>
        </Panel>

        {/* Map + side */}
        <div className="fire-map-grid">
          <Panel>
            <PanelHeader
              icon="🗺️"
              title="Fire Risk Map"
              subtitle={`${activeDate} · ${dayRecords.length} locations`}
              actions={
                <select className="fire-select" value={riskFilter} onChange={(e) => setRiskFilter(e.target.value)}>
                  <option value="">All risk levels</option>
                  <option value="High">🔥 High only</option>
                  <option value="Medium">⚠️ Medium only</option>
                  <option value="Low">🌿 Low only</option>
                </select>
              }
            />
            <div className="fire-map-wrap">
              <div ref={mapRef} className="fire-map" />
              <div className="fire-legend">
                <div className="legend-title">Risk Level</div>
                {['High', 'Medium', 'Low'].map((r) => (
                  <div key={r} className="legend-item">
                    <span className="legend-dot" style={{ background: FIRE_RISK_COLORS[r] }} />{r}
                  </div>
                ))}
                <div className="legend-note">Circle size ∝ fire probability</div>
              </div>
            </div>
          </Panel>

          {/* Top risk list */}
          <Panel>
            <PanelHeader icon="🚨" title="Highest-Risk Locations" subtitle={activeDate.slice(5)} />
            <PanelBody noPad>
              <div className="fire-risk-list">
                {topRisk.map((d) => (
                  <div
                    key={d.id}
                    className={`fire-risk-item ${selected?.id === d.id ? 'sel' : ''}`}
                    onClick={() => {
                      setSelected(d);
                      leafletMap.current?.setView([d.lat, d.lng], 8);
                    }}
                  >
                    <div>
                      <div className="fri-name">Location #{d.id}</div>
                      <div className="fri-coords">{d.lat.toFixed(2)}, {d.lng.toFixed(2)}</div>
                    </div>
                    <div className="fri-right">
                      <div className="fri-prob" style={{ color: FIRE_RISK_COLORS[d.risk] }}>
                        {(d.prob * 100).toFixed(0)}%
                      </div>
                      <FireBadge level={d.risk} />
                    </div>
                  </div>
                ))}
              </div>
            </PanelBody>
          </Panel>
        </div>

        {/* 7-day trend */}
        <Panel>
          <PanelHeader icon="📈" title="7-Day Fire-Risk Trend" subtitle="Zone counts + avg probability" />
          <PanelBody>
            <ResponsiveContainer width="100%" height={260}>
              <LineChart data={trend} margin={{ top: 8, right: 16, bottom: 4, left: -8 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="var(--gray-100)" />
                <XAxis dataKey="date" tick={{ fontSize: 11 }} />
                <YAxis tick={{ fontSize: 11 }} />
                <Tooltip wrapperStyle={{ fontSize: 12 }} />
                <Legend wrapperStyle={{ fontSize: 12 }} />
                <Line type="monotone" dataKey="High" stroke={FIRE_RISK_COLORS.High} strokeWidth={2.5} dot={{ r: 3 }} />
                <Line type="monotone" dataKey="Medium" stroke={FIRE_RISK_COLORS.Medium} strokeWidth={2} dot={{ r: 3 }} />
                <Line type="monotone" dataKey="Low" stroke={FIRE_RISK_COLORS.Low} strokeWidth={2} dot={{ r: 3 }} />
              </LineChart>
            </ResponsiveContainer>
          </PanelBody>
        </Panel>

        {/* Model evaluation section */}
        <h3 className="fire-section-title">Model Performance &amp; Drivers</h3>
        <div className="fire-eval-grid">
          {/* Model scores */}
          <Panel>
            <PanelHeader icon="🏆" title="Model Comparison" subtitle="ROC-AUC &amp; PR-AUC" />
            <PanelBody>
              <div className="model-table">
                {FIRE_MODELS.map((m) => (
                  <div key={m.name} className={`model-row ${m.best ? 'best' : ''}`}>
                    <div className="model-name">
                      {m.name} {m.best && <span className="best-tag">Best</span>}
                    </div>
                    <div className="model-scores">
                      <div className="model-metric">
                        <span className="mm-label">ROC</span>
                        <div className="mm-bar"><div style={{ width: `${m.roc * 100}%`, background: m.best ? 'var(--saffron)' : 'var(--navy)' }} /></div>
                        <span className="mm-val">{m.roc.toFixed(2)}</span>
                      </div>
                      <div className="model-metric">
                        <span className="mm-label">PR</span>
                        <div className="mm-bar"><div style={{ width: `${m.pr * 100}%`, background: m.best ? 'var(--saffron)' : 'var(--gov-green)' }} /></div>
                        <span className="mm-val">{m.pr.toFixed(2)}</span>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </PanelBody>
          </Panel>

          {/* Feature importance chart (live recharts) */}
          <Panel>
            <PanelHeader icon="🎯" title="Fire-Driver Importance" subtitle="Random Forest" />
            <PanelBody>
              <ResponsiveContainer width="100%" height={240}>
                <BarChart data={FIRE_DRIVERS} layout="vertical" margin={{ left: 30, right: 16 }}>
                  <XAxis type="number" domain={[0, 0.25]} tick={{ fontSize: 10 }} />
                  <YAxis type="category" dataKey="feature" tick={{ fontSize: 10 }} width={120} />
                  <Tooltip formatter={(v) => [v.toFixed(3), 'Importance']} />
                  <Bar dataKey="importance" radius={[0, 4, 4, 0]}>
                    {FIRE_DRIVERS.map((_, i) => (
                      <Cell key={i} fill={`rgba(215, 38, 61, ${1 - i * 0.1})`} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </PanelBody>
          </Panel>
        </div>

        {/* Evaluation charts (the uploaded ML images) */}
        <div className="fire-curves-grid">
          <Panel>
            <PanelHeader icon="📉" title="ROC Curves" subtitle="ML Pipeline Output" />
            <PanelBody>
              <img src="/images/fire_roc_curves.png" alt="ROC curves" className="fire-img" />
            </PanelBody>
          </Panel>
          <Panel>
            <PanelHeader icon="📊" title="Precision-Recall Curves" subtitle="ML Pipeline Output" />
            <PanelBody>
              <img src="/images/fire_pr_curves.png" alt="Precision-Recall curves" className="fire-img" />
            </PanelBody>
          </Panel>
        </div>

        {selected && (
          <div className="fire-detail-toast">
            <span>📍 Location #{selected.id} — {(selected.prob * 100).toFixed(1)}% fire probability ({selected.risk})</span>
            <button onClick={() => setSelected(null)}>✕</button>
          </div>
        )}
      </div>
    </div>
  );
}
