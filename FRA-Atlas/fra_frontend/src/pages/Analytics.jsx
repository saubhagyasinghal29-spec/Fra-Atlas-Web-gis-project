import { useState } from 'react';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, ScatterChart, Scatter, CartesianGrid, Legend } from 'recharts';
import { RISK_COLORS } from '../data/constants';
import { Panel, PanelHeader, PanelBody } from '../components/layout/Panel';
import { useFraData } from '../context/DataContext';
import { Loading, SourceBanner } from '../components/DataState';
import '../components/layout/Panel.css';
import './Analytics.css';

const METRICS = {
  ar:  { label:'Approval Rate (%)',          key:'ar',  scale:100, color:'#138808' },
  pr:  { label:'Pending Claims Rate (%)',     key:'pr',  scale:100, color:'#E67E22' },
  pt:  { label:'Avg Processing Time (days)', key:'pt',  scale:1,   color:'#C0392B' },
  fl:  { label:'Forest Loss Rate (%)',        key:'fl',  scale:1,   color:'#8B4513' },
  cr:  { label:'CFR Recognition Rate (%)',    key:'cr',  scale:100, color:'#003087' },
  rjr: { label:'Rejection Rate (%)',          key:'rjr', scale:100, color:'#9B59B6' },
};

export default function Analytics() {
  const [metric, setMetric] = useState('ar');
  const { data: FRA_DATA, loading, source, error } = useFraData();

  if (loading) return <Loading label="Loading analytics…" />;

  // State averages
  const stateMap = {};
  FRA_DATA.forEach(d => {
    if (!stateMap[d.state]) stateMap[d.state] = { items: [] };
    stateMap[d.state].items.push(d);
  });
  const stateData = Object.entries(stateMap).map(([state, { items }]) => {
    const m = METRICS[metric];
    const avg = items.reduce((s,d) => s + d[m.key], 0) / items.length;
    return { state: state.length > 13 ? state.slice(0,12)+'…' : state, value: +(avg * m.scale).toFixed(2) };
  }).sort((a,b) => b.value - a.value);

  // Scatter data
  const scatterSets = Object.keys(RISK_COLORS).map(level => ({
    level,
    points: FRA_DATA.filter(d => d.rl === level).map(d => ({ x: +(d.ar*100).toFixed(1), y: d.ri, name:`${d.district}, ${d.state}` })),
  }));

  return (
    <div className="analytics-page">
      <div className="analytics-inner">
        <h2 className="page-title">Risk Intelligence &amp; Analytics</h2>
        <SourceBanner source={source} error={error} />

        {/* Heatmap + PCA row */}
        <div className="analytics-grid-2">
          <Panel>
            <PanelHeader icon="🔥" title="Risk Factor Correlation Heatmap" subtitle="ML Pipeline Output" />
            <PanelBody>
              <img src="/images/factor_heatmap.png" alt="Correlation heatmap" className="analysis-img" />
              <div className="insights-grid">
                {[
                  { icon:'📉', title:'Strong Negative Correlation', desc:'Approval Rate ↔ Pending Claims (−0.70) and Processing Time (−0.70)' },
                  { icon:'📈', title:'Core Bottleneck', desc:'Pending Claims ↔ Processing Time = 0.92 — admin backlog drives risk' },
                  { icon:'🌳', title:'Forest Loss Signal', desc:'Forest Loss Rate positively correlated with pending claims (0.65)' },
                  { icon:'🧩', title:'Encroachment is Independent', desc:'Near-zero correlation — needs a distinct intervention strategy' },
                ].map(ins => (
                  <div key={ins.title} className="insight-card">
                    <span className="insight-icon">{ins.icon}</span>
                    <div>
                      <div className="insight-title">{ins.title}</div>
                      <div className="insight-desc">{ins.desc}</div>
                    </div>
                  </div>
                ))}
              </div>
            </PanelBody>
          </Panel>

          <div style={{ display:'flex', flexDirection:'column', gap:20 }}>
            <Panel>
              <PanelHeader icon="🔮" title="PCA Cluster Space" subtitle="K-Means · 2 Clusters" />
              <PanelBody>
                <img src="/images/pca_clusters.png" alt="PCA clusters" className="analysis-img" />
                <div className="cluster-row">
                  <div className="cluster-stat" style={{ background:'var(--risk-critical-bg)' }}>
                    <div style={{ fontSize:22, fontWeight:700, color:'var(--risk-critical)' }}>250</div>
                    <div style={{ fontSize:12, color:'var(--gray-500)' }}>Cluster 1 — High Risk</div>
                  </div>
                  <div className="cluster-stat" style={{ background:'var(--risk-excellent-bg)' }}>
                    <div style={{ fontSize:22, fontWeight:700, color:'var(--risk-excellent)' }}>250</div>
                    <div style={{ fontSize:12, color:'var(--gray-500)' }}>Cluster 2 — Low Risk</div>
                  </div>
                </div>
              </PanelBody>
            </Panel>
            <Panel>
              <PanelHeader icon="🏆" title="District Risk Ranking" subtitle="Top 50" />
              <PanelBody>
                <img src="/images/risk_ranking.png" alt="Risk ranking" className="analysis-img" />
              </PanelBody>
            </Panel>
          </div>
        </div>

        {/* State Metric Chart */}
        <Panel>
          <PanelHeader
            icon="📊"
            title="State-Wise Average Metrics"
            actions={
              <select className="tb-select" value={metric} onChange={e => setMetric(e.target.value)}
                style={{ border:'1px solid var(--gray-300)', borderRadius:5, padding:'5px 9px', fontSize:12.5 }}>
                {Object.entries(METRICS).map(([k,m]) => <option key={k} value={k}>{m.label}</option>)}
              </select>
            }
          />
          <PanelBody>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={stateData} barSize={22}>
                <XAxis dataKey="state" tick={{ fontSize:10.5 }} angle={-30} textAnchor="end" height={60} interval={0} />
                <YAxis tick={{ fontSize:11 }} />
                <Tooltip formatter={(v) => [v + (METRICS[metric].scale === 100 ? '%' : ''), METRICS[metric].label]} />
                <Bar dataKey="value" fill={METRICS[metric].color} radius={[4,4,0,0]} />
              </BarChart>
            </ResponsiveContainer>
          </PanelBody>
        </Panel>

        {/* Scatter Plot */}
        <Panel>
          <PanelHeader icon="📉" title="Risk Index vs Approval Rate — All 500 Districts" />
          <PanelBody>
            <ResponsiveContainer width="100%" height={320}>
              <ScatterChart margin={{ top:10, right:20, bottom:30, left:10 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="var(--gray-100)" />
                <XAxis type="number" dataKey="x" name="Approval Rate" unit="%" tick={{ fontSize:11 }} label={{ value:'Approval Rate (%)', position:'insideBottom', offset:-15, fontSize:12 }} />
                <YAxis type="number" dataKey="y" name="Risk Index" tick={{ fontSize:11 }} label={{ value:'Risk Index', angle:-90, position:'insideLeft', fontSize:12 }} />
                <Tooltip cursor={{ strokeDasharray:'3 3' }} content={({ payload }) => {
                  if (!payload?.length) return null;
                  const p = payload[0]?.payload;
                  return <div style={{ background:'#fff', border:'1px solid var(--gray-300)', borderRadius:6, padding:'8px 12px', fontSize:12 }}>
                    <div style={{ fontWeight:700 }}>{p.name}</div>
                    <div>Approval: {p.x}% · Risk: {p.y}</div>
                  </div>;
                }} />
                <Legend wrapperStyle={{ paddingTop:12, fontSize:12 }} />
                {scatterSets.map(({ level, points }) => (
                  <Scatter key={level} name={level} data={points} fill={RISK_COLORS[level]} opacity={0.7} />
                ))}
              </ScatterChart>
            </ResponsiveContainer>
          </PanelBody>
        </Panel>
      </div>
    </div>
  );
}
