import { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, PieChart, Pie, Cell, Legend } from 'recharts';
import { RISK_COLORS, RISK_BG, FOCUSED_STATES } from '../data/constants';
import { Panel, PanelHeader, PanelBody } from '../components/layout/Panel';
import RiskBadge from '../components/layout/RiskBadge';
import { useFraData } from '../context/DataContext';
import { Loading, SourceBanner } from '../components/DataState';
import '../components/layout/Panel.css';
import './Dashboard.css';

function useCounter(target, duration = 1200) {
  const [val, setVal] = useState(0);
  useEffect(() => {
    let start = null;
    const step = (ts) => {
      if (!start) start = ts;
      const p = Math.min((ts - start) / duration, 1);
      setVal(Math.round(p * target));
      if (p < 1) requestAnimationFrame(step);
    };
    requestAnimationFrame(step);
  }, [target, duration]);
  return val;
}

function StatCard({ value, label, color }) {
  const c = useCounter(value);
  return (
    <div className="hero-stat">
      <div className="hero-stat-val" style={{ color }}>{c}</div>
      <div className="hero-stat-label">{label}</div>
    </div>
  );
}

export default function Dashboard() {
  const navigate = useNavigate();
  const { data: FRA_DATA, loading, source, error } = useFraData();

  if (loading) return <Loading label="Loading district risk data…" />;

  // Counts
  const counts = { Critical: 0, Moderate: 0, Good: 0, Excellent: 0 };
  FRA_DATA.forEach(d => { if (counts[d.rl] !== undefined) counts[d.rl]++; });

  // State breakdown data for bar chart
  const stateMap = {};
  FRA_DATA.forEach(d => {
    if (!stateMap[d.state]) stateMap[d.state] = { Critical:0, Moderate:0, Good:0, Excellent:0 };
    stateMap[d.state][d.rl]++;
  });
  const topStates = Object.entries(stateMap)
    .sort((a,b) => (b[1].Critical + b[1].Moderate) - (a[1].Critical + a[1].Moderate))
    .slice(0, 8)
    .map(([state, v]) => ({ state: state.length > 12 ? state.slice(0,11)+'…' : state, ...v }));

  const pieData = Object.entries(counts).map(([name, value]) => ({ name, value }));

  const topRisk = FRA_DATA.filter(d => d.rl === 'Critical' || d.rl === 'Moderate')
    .sort((a,b) => b.ri - a.ri).slice(0, 12);

  return (
    <div className="dashboard-page">
      <SourceBanner source={source} error={error} />
      {/* Hero */}
      <section className="hero">
        <div className="hero-inner">
          <div className="hero-text">
            <div className="hero-eyebrow">🌳 Forest Rights Act, 2006 — Integrated Monitoring System</div>
            <h1 className="hero-title">AI-Powered <span>FRA Atlas</span> &amp; Decision Support System</h1>
            <p className="hero-desc">
              Real-time monitoring of IFR, Community Rights, and CFR Rights across India's forest-dwelling communities.
              Focused on <strong>Madhya Pradesh · Tripura · Odisha · Telangana</strong>.
            </p>
            <div className="hero-btns">
              <button className="btn-primary" onClick={() => navigate('/map')}>🗺️ Open FRA Atlas Map</button>
              <button className="btn-outline" onClick={() => navigate('/dss')}>🎯 Launch DSS</button>
            </div>
          </div>
          <div className="hero-stats-grid">
            <div className="hero-stat-card"><StatCard value={500} label="Districts Tracked" color="#fff" /></div>
            <div className="hero-stat-card"><StatCard value={16} label="States Covered" color="#FFB366" /></div>
            <div className="hero-stat-card"><StatCard value={counts.Critical} label="Critical Districts" color="#ff7b7b" /></div>
            <div className="hero-stat-card"><StatCard value={counts.Excellent} label="Excellent Districts" color="#86f0a8" /></div>
          </div>
        </div>
        <div className="tiranga-bar" />
      </section>

      {/* KPI Strip */}
      <section className="kpi-strip">
        <div className="kpi-inner">
          {[
            { key:'Critical',  icon:'🔴', label:'Critical Risk' },
            { key:'Moderate',  icon:'🟠', label:'Moderate Risk' },
            { key:'Good',      icon:'🟡', label:'Good Performance' },
            { key:'Excellent', icon:'🟢', label:'Excellent Performance' },
          ].map(({ key, icon, label }) => (
            <div key={key} className={`kpi-card kpi-${key.toLowerCase()}`}>
              <div className="kpi-icon">{icon}</div>
              <div>
                <div className="kpi-value" style={{ color: RISK_COLORS[key] }}>{counts[key]}</div>
                <div className="kpi-label">{label}</div>
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* Body */}
      <div className="dash-body">
        <div className="dash-grid">
          {/* LEFT */}
          <div className="dash-main">
            {/* Top Risk Table */}
            <Panel>
              <PanelHeader
                icon="🔴"
                title="Top Critical &amp; High-Risk Districts"
                actions={<button className="link-btn" onClick={() => navigate('/analytics')}>View All →</button>}
              />
              <PanelBody noPad>
                <div className="table-wrap">
                  <table className="risk-table">
                    <thead>
                      <tr>
                        <th>#</th><th>District</th><th>State</th>
                        <th>Risk Index</th><th>Level</th>
                        <th>Approval</th><th>Pending</th><th>Processing</th>
                      </tr>
                    </thead>
                    <tbody>
                      {topRisk.map((d, i) => (
                        <tr key={i} onClick={() => navigate(`/dss?state=${d.state}&district=${d.district}`)} style={{ cursor:'pointer' }}>
                          <td className="rank-cell">{i+1}</td>
                          <td style={{ fontWeight:600 }}>{d.district}</td>
                          <td className="muted">{d.state}</td>
                          <td>
                            <div className="mini-bar-wrap">
                              <div className="mini-bar">
                                <div style={{ width:`${d.ri}%`, background: RISK_COLORS[d.rl], height:'100%', borderRadius:4 }} />
                              </div>
                              <span>{d.ri.toFixed(1)}</span>
                            </div>
                          </td>
                          <td><RiskBadge level={d.rl} size="sm" /></td>
                          <td className="num-cell">{(d.ar*100).toFixed(1)}%</td>
                          <td className="num-cell danger">{(d.pr*100).toFixed(1)}%</td>
                          <td className="num-cell">{d.pt}d</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </PanelBody>
            </Panel>

            {/* Charts row */}
            <div className="charts-row">
              <Panel>
                <PanelHeader icon="📊" title="Risk Distribution" />
                <PanelBody>
                  <ResponsiveContainer width="100%" height={200}>
                    <PieChart>
                      <Pie data={pieData} cx="50%" cy="50%" innerRadius={55} outerRadius={80} paddingAngle={2} dataKey="value">
                        {pieData.map((entry) => (
                          <Cell key={entry.name} fill={RISK_COLORS[entry.name]} />
                        ))}
                      </Pie>
                      <Tooltip formatter={(v, n) => [`${v} districts`, n]} />
                      <Legend iconType="circle" iconSize={10} wrapperStyle={{ fontSize:12 }} />
                    </PieChart>
                  </ResponsiveContainer>
                </PanelBody>
              </Panel>
              <Panel>
                <PanelHeader icon="📈" title="State-wise Breakdown" />
                <PanelBody>
                  <ResponsiveContainer width="100%" height={200}>
                    <BarChart data={topStates} barSize={8}>
                      <XAxis dataKey="state" tick={{ fontSize:10 }} />
                      <YAxis tick={{ fontSize:10 }} />
                      <Tooltip wrapperStyle={{ fontSize:12 }} />
                      <Bar dataKey="Critical" fill={RISK_COLORS.Critical} stackId="s" />
                      <Bar dataKey="Moderate" fill={RISK_COLORS.Moderate} stackId="s" />
                      <Bar dataKey="Good" fill={RISK_COLORS.Good} stackId="s" />
                      <Bar dataKey="Excellent" fill={RISK_COLORS.Excellent} stackId="s" radius={[3,3,0,0]} />
                    </BarChart>
                  </ResponsiveContainer>
                </PanelBody>
              </Panel>
            </div>

            {/* Focused States */}
            <Panel>
              <PanelHeader icon="🎯" title="Priority States — Deep Dive" />
              <PanelBody>
                <div className="focus-grid">
                  {FOCUSED_STATES.map(state => {
                    const sr = stateMap[state] || {};
                    const total = Object.values(sr).reduce((s,v) => s+v, 0) || 1;
                    const avg = (FRA_DATA.filter(d=>d.state===state).reduce((s,d)=>s+d.ri,0) / (FRA_DATA.filter(d=>d.state===state).length||1)).toFixed(1);
                    return (
                      <div key={state} className="focus-card" onClick={() => navigate(`/map?state=${state}`)}>
                        <div className="focus-top">
                          <div className="focus-name">{state}</div>
                          <div className="focus-avg">Avg Risk: <strong style={{ color: sr.Critical > sr.Good ? 'var(--risk-critical)' : 'var(--risk-good)' }}>{avg}</strong></div>
                        </div>
                        <div className="focus-count">{total} districts</div>
                        <div className="focus-bar">
                          {[['Critical',sr.Critical],['Moderate',sr.Moderate],['Good',sr.Good],['Excellent',sr.Excellent]].map(([k,v]) => (
                            <div key={k} title={`${k}: ${v}`} style={{ flex: v||0, background: RISK_COLORS[k], minWidth: v ? 2 : 0 }} />
                          ))}
                        </div>
                        <div className="focus-legend">
                          {[['Critical',sr.Critical],['Moderate',sr.Moderate],['Good',sr.Good],['Excellent',sr.Excellent]].map(([k,v]) => (
                            <span key={k} style={{ color: RISK_COLORS[k], fontSize:11 }}>● {v||0}</span>
                          ))}
                        </div>
                      </div>
                    );
                  })}
                </div>
              </PanelBody>
            </Panel>
          </div>

          {/* RIGHT SIDEBAR */}
          <div className="dash-side">
            {/* Map CTA */}
            <Panel>
              <PanelHeader icon="🗺️" title="FRA Atlas" actions={<button className="link-btn" onClick={() => navigate('/map')}>Full Map →</button>} />
              <div className="map-cta" onClick={() => navigate('/map')}>
                <div className="map-cta-content">
                  <div className="map-cta-icon">🗺️</div>
                  <div className="map-cta-text">Interactive WebGIS Map</div>
                  <div className="map-cta-sub">500 districts · Leaflet · MarkerCluster</div>
                  <button className="btn-primary" style={{ marginTop:12, padding:'8px 16px', fontSize:13 }}>Open Map →</button>
                </div>
              </div>
            </Panel>

            {/* Alerts */}
            <Panel>
              <PanelHeader icon="🚨" title="Critical Alerts" />
              <PanelBody>
                <div className="alert-list">
                  {FRA_DATA.filter(d=>d.rl==='Critical').sort((a,b)=>b.ri-a.ri).slice(0,5).map((d,i) => (
                    <div key={i} className="alert-item">
                      <span className="alert-icon">🚨</span>
                      <div>
                        <div className="alert-name">{d.district}, {d.state}</div>
                        <div className="alert-meta">Risk: {d.ri.toFixed(1)} · Pending: {(d.pr*100).toFixed(0)}% · {d.pt}d</div>
                      </div>
                    </div>
                  ))}
                </div>
              </PanelBody>
            </Panel>

            {/* CSS Schemes */}
            <Panel>
              <PanelHeader icon="📋" title="CSS Scheme Coverage" actions={<button className="link-btn" onClick={() => navigate('/dss')}>DSS →</button>} />
              <PanelBody>
                {[
                  { icon:'🌾', name:'PM-KISAN', pct:74 },
                  { icon:'💧', name:'Jal Jeevan Mission', pct:61 },
                  { icon:'🔨', name:'MGNREGA', pct:88 },
                  { icon:'🏠', name:'PMAY-G', pct:52 },
                  { icon:'⚡', name:'SAUBHAGYA', pct:43 },
                ].map(s => (
                  <div key={s.name} className="scheme-mini">
                    <span className="scheme-mini-icon">{s.icon}</span>
                    <div style={{ flex:1 }}>
                      <div className="scheme-mini-name">{s.name}</div>
                      <div className="mini-bar-wrap" style={{ marginTop:3 }}>
                        <div className="mini-bar"><div style={{ width:`${s.pct}%`, background:'var(--navy)', height:'100%', borderRadius:4 }} /></div>
                        <span style={{ fontSize:11, color:'var(--gray-500)' }}>{s.pct}%</span>
                      </div>
                    </div>
                  </div>
                ))}
              </PanelBody>
            </Panel>
          </div>
        </div>
      </div>
    </div>
  );
}
