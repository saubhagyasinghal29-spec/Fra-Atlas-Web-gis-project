import { useState, useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';
import { RISK_COLORS, RISK_BG, ALL_STATES, CSS_SCHEMES } from '../data/constants';
import { Panel, PanelHeader, PanelBody } from '../components/layout/Panel';
import RiskBadge from '../components/layout/RiskBadge';
import { useFraData } from '../context/DataContext';
import { Loading } from '../components/DataState';
import '../components/layout/Panel.css';
import './DSS.css';

function pct(v) { return (v*100).toFixed(1)+'%'; }

export default function DSS() {
  const [searchParams] = useSearchParams();
  const [state, setState] = useState(searchParams.get('state') || 'Madhya Pradesh');
  const [district, setDistrict] = useState(searchParams.get('district') || '');
  const [rightsType, setRightsType] = useState('all');
  const [result, setResult] = useState(null);
  const { data: FRA_DATA, loading } = useFraData();

  const districts = [...new Set(FRA_DATA.filter(d => d.state === state).map(d => d.district))].sort();

  useEffect(() => {
    if (districts.length && !district) setDistrict(districts[0]);
  }, [state]);

  function analyse() {
    const records = FRA_DATA.filter(d => d.state === state && d.district === district);
    if (!records.length) return;
    const top = records.sort((a,b) => b.ri - a.ri)[0];
    setResult(top);
  }

  const actions = result ? [
    result.pr > 0.35 && { icon:'⚡', text:`Pending claims at ${pct(result.pr)} — target below 15% within 6 months`, urgency:'Immediate' },
    result.pt > 110  && { icon:'⏱️', text:`Processing time ${result.pt} days — digitize records for 30-day target`, urgency:'Immediate' },
    result.cr < 0.4  && { icon:'🌳', text:`CFR recognition ${pct(result.cr)} is low — facilitate Gram Sabha workshops`, urgency:'Short-term' },
    result.fl > 2.0  && { icon:'🛡️', text:`Forest loss ${result.fl.toFixed(2)}% — strengthen CFR protection committees`, urgency:'Immediate' },
    result.ar < 0.5  && { icon:'📋', text:`Approval rate ${pct(result.ar)} below 50% — review SDLC/DLC capacity`, urgency:'Short-term' },
    result.rjr > 0.15 && { icon:'📝', text:`Rejection rate ${pct(result.rjr)} — provide documentation support to applicants`, urgency:'Short-term' },
    { icon:'📡', text:'Integrate satellite-based asset mapping for IFR boundary verification', urgency:'Medium-term' },
    { icon:'🔗', text:'Link FRA patta database with PM-KISAN, MGNREGA, and PMAY-G portals', urgency:'Medium-term' },
  ].filter(Boolean) : [];

  const urgencyColor = { Immediate:'var(--risk-critical)', 'Short-term':'var(--risk-moderate)', 'Medium-term':'var(--risk-good)' };
  const urgencyBg = { Immediate:'var(--risk-critical-bg)', 'Short-term':'var(--risk-moderate-bg)', 'Medium-term':'var(--risk-good-bg)' };

  if (loading) return <Loading label="Loading decision support data…" />;

  return (
    <div className="dss-page">
      <div className="dss-inner">
        <div className="dss-header-row">
          <div>
            <h2 className="page-title">Decision Support System</h2>
            <p className="dss-subtitle">Identify eligible Central Sector Scheme benefits for FRA patta holders. Select a location to generate a tailored DSS recommendation.</p>
          </div>
        </div>

        <div className="dss-grid">
          {/* Filter Panel */}
          <div className="dss-left">
            <Panel>
              <PanelHeader icon="🔍" title="Select Location" />
              <PanelBody>
                <div className="form-group">
                  <label className="form-label">State</label>
                  <select className="form-control" value={state} onChange={e => { setState(e.target.value); setResult(null); }}>
                    {ALL_STATES.map(s => <option key={s} value={s}>{s}</option>)}
                  </select>
                </div>
                <div className="form-group">
                  <label className="form-label">District</label>
                  <select className="form-control" value={district} onChange={e => { setDistrict(e.target.value); setResult(null); }}>
                    {districts.map(d => <option key={d} value={d}>{d}</option>)}
                  </select>
                </div>
                <div className="form-group">
                  <label className="form-label">Rights Type</label>
                  <select className="form-control" value={rightsType} onChange={e => setRightsType(e.target.value)}>
                    <option value="all">All Rights Types</option>
                    <option value="ifr">Individual Forest Rights (IFR)</option>
                    <option value="cr">Community Rights (CR)</option>
                    <option value="cfr">CFR Rights</option>
                  </select>
                </div>
                <button className="btn-primary" style={{ width:'100%', justifyContent:'center', marginTop:16, padding:'10px' }} onClick={analyse}>
                  🎯 Generate DSS Report
                </button>
              </PanelBody>
            </Panel>

            {result && (
              <Panel style={{ marginTop:0 }}>
                <PanelHeader icon="📍" title="District Risk Profile" />
                <PanelBody>
                  <div className="profile-top">
                    <div className="profile-name">{result.district}</div>
                    <div className="profile-state">{result.state}</div>
                    <div style={{ marginTop:8 }}><RiskBadge level={result.rl} /></div>
                  </div>
                  <div className="profile-stats">
                    {[
                      { l:'Risk Index', v:result.ri.toFixed(1), hi:result.ri>60 },
                      { l:'Rank', v:'#'+result.rr, hi:result.rr<=100 },
                      { l:'Approval', v:pct(result.ar), hi:false },
                      { l:'Pending', v:pct(result.pr), hi:true },
                      { l:'Proc. Time', v:result.pt+'d', hi:result.pt>100 },
                      { l:'Forest Loss', v:result.fl.toFixed(1)+'%', hi:result.fl>2 },
                    ].map(m => (
                      <div key={m.l} className="profile-stat">
                        <div className="ps-label">{m.l}</div>
                        <div className="ps-val" style={{ color: m.hi ? 'var(--risk-critical)' : 'var(--gray-900)' }}>{m.v}</div>
                      </div>
                    ))}
                  </div>
                </PanelBody>
              </Panel>
            )}
          </div>

          {/* Results */}
          <div className="dss-right">
            <Panel>
              <PanelHeader
                icon="📋"
                title="Eligible CSS Scheme Recommendations"
                subtitle={result ? `${CSS_SCHEMES.filter(s => s.rights.includes(rightsType) || s.rights.includes('all')).length} schemes eligible` : ''}
              />
              <PanelBody>
                {!result ? (
                  <div className="empty-state">
                    <div style={{ fontSize:36, marginBottom:10 }}>🎯</div>
                    <div>Select a location and click <strong>Generate DSS Report</strong> to view scheme eligibility</div>
                  </div>
                ) : (
                  <div className="schemes-list">
                    {CSS_SCHEMES.filter(s => s.rights.includes(rightsType) || s.rights.includes('all')).map(s => {
                      const urgency = result.rl === 'Critical' ? 'High Priority' : result.rl === 'Moderate' ? 'Medium Priority' : 'Standard';
                      const urgColor = result.rl === 'Critical' ? 'var(--risk-critical)' : result.rl === 'Moderate' ? 'var(--risk-moderate)' : 'var(--risk-good)';
                      return (
                        <div key={s.id} className="scheme-card">
                          <div className="scheme-icon">{s.icon}</div>
                          <div style={{ flex:1 }}>
                            <div className="scheme-title-row">
                              <span className="scheme-name">{s.name}</span>
                              <span className="scheme-badge eligible">✓ Eligible</span>
                              <span style={{ fontSize:11, fontWeight:700, color:urgColor }}>{urgency}</span>
                            </div>
                            <div className="scheme-desc">{s.desc}</div>
                            <div className="scheme-tags">
                              <span className="scheme-tag">{s.tag}</span>
                              <span className="scheme-tag ministry">{s.ministry}</span>
                            </div>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                )}
              </PanelBody>
            </Panel>

            {result && actions.length > 0 && (
              <Panel>
                <PanelHeader icon="⚡" title="Priority Action Plan" />
                <PanelBody>
                  <div style={{ marginBottom:12, fontSize:13.5, color:'var(--gray-700)' }}>
                    Tailored for <strong>{result.district}, {result.state}</strong> — <RiskBadge level={result.rl} size="sm" />
                  </div>
                  {actions.map((a, i) => (
                    <div key={i} className="action-item">
                      <span style={{ fontSize:18, flexShrink:0 }}>{a.icon}</span>
                      <div style={{ flex:1, fontSize:13.5 }}>{a.text}</div>
                      <span style={{ fontSize:11, fontWeight:700, padding:'3px 8px', borderRadius:10, flexShrink:0, background:urgencyBg[a.urgency], color:urgencyColor[a.urgency] }}>{a.urgency}</span>
                    </div>
                  ))}
                </PanelBody>
              </Panel>
            )}

            {/* DAJGUA */}
            <Panel>
              <PanelHeader icon="🏛️" title="DAJGUA — 3-Ministry Convergence" actions={<span style={{ background:'var(--saffron)', color:'#fff', fontSize:11, padding:'2px 8px', borderRadius:10 }}>Active</span>} />
              <PanelBody>
                <div className="ministry-grid">
                  {[
                    { icon:'🌲', name:'Ministry of Environment', sub:'Forest Rights & Conservation' },
                    { icon:'🏘️', name:'Ministry of Tribal Affairs', sub:'Patta & IFR Processing' },
                    { icon:'🌾', name:'Ministry of Agriculture', sub:'PM-KISAN & Soil Health' },
                  ].map(m => (
                    <div key={m.name} className="ministry-card">
                      <div style={{ fontSize:26, marginBottom:6 }}>{m.icon}</div>
                      <div style={{ fontWeight:700, fontSize:12.5, color:'var(--navy)' }}>{m.name}</div>
                      <div style={{ fontSize:11.5, color:'var(--gray-500)', marginTop:4 }}>{m.sub}</div>
                    </div>
                  ))}
                </div>
                <div className="dajgua-note">
                  Districts with pending FRA claims receive priority convergence treatment across all 3 ministries. The DSS flags districts where cross-ministry benefit delivery is both urgent and feasible.
                </div>
              </PanelBody>
            </Panel>
          </div>
        </div>
      </div>
    </div>
  );
}
