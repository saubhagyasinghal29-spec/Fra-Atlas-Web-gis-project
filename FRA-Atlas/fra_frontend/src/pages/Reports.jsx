import { Panel, PanelHeader, PanelBody } from '../components/layout/Panel';
import '../components/layout/Panel.css';
import './Reports.css';

const REPORTS = [
  { icon:'📊', title:'State Summary Report', desc:'Aggregated FRA implementation status across all 16 states with district-wise breakdowns.', fmt:'PDF · Excel', url:'/api/reports/state-summary/' },
  { icon:'🔴', title:'Critical Districts Alert', desc:'87 districts with Risk Index >60 requiring immediate intervention. Includes action plan templates.', fmt:'PDF · CSV', url:'/api/reports/critical-districts/' },
  { icon:'🎯', title:'DSS Convergence Matrix', desc:'CSS scheme eligibility matrix for FRA patta holder categories across priority 4 states.', fmt:'Excel · PDF', url:'/api/reports/dss-matrix/' },
  { icon:'🌲', title:'CFR Recognition Tracker', desc:'Community Forest Resource Rights recognition status, pending cases, and Gram Sabha progress.', fmt:'Excel · GeoJSON', url:'/api/reports/cfr-tracker/' },
  { icon:'🛰️', title:'Satellite Asset Map Export', desc:'GIS layers for land parcels, water bodies, and farms linked to FRA patta boundaries.', fmt:'GeoJSON · Shapefile', url:'/api/reports/satellite-export/' },
  { icon:'📈', title:'ML Risk Score Dataset', desc:'Full 500-district ML risk scores with PCA components, cluster assignments, and all 8 metrics.', fmt:'CSV · JSON', url:'/api/fra-data/export/' },
];

export default function Reports() {
  return (
    <div className="reports-page">
      <div className="reports-inner">
        <h2 className="page-title">Reports &amp; Data Exports</h2>

        <div className="reports-grid">
          {REPORTS.map(r => (
            <Panel key={r.title}>
              <PanelBody>
                <div className="report-card">
                  <div className="report-icon">{r.icon}</div>
                  <h3 className="report-title">{r.title}</h3>
                  <p className="report-desc">{r.desc}</p>
                  <span className="report-fmt">{r.fmt}</span>
                  <div className="report-actions">
                    <button className="btn-outline-navy" onClick={() => window.open(r.url, '_blank')}>👁 View</button>
                    <button className="btn-primary" style={{ padding:'7px 14px', fontSize:13 }} onClick={() => window.open(r.url + '?format=download')}>⬇ Download</button>
                  </div>
                </div>
              </PanelBody>
            </Panel>
          ))}
        </div>

        {/* Data Pipeline Status */}
        <Panel>
          <PanelHeader icon="⚙️" title="ML Data Pipeline Status" />
          <PanelBody>
            <div className="pipeline-grid">
              {[
                { label:'Last CSV Ingestion', value:'fra_risk_scores.csv', status:'✅ Success', time:'Today' },
                { label:'Risk Scoring Model', value:'K-Means + PCA', status:'✅ Active', time:'500 records' },
                { label:'Factor Heatmap', value:'factor_heatmap.png', status:'✅ Generated', time:'8 variables' },
                { label:'PCA Visualization', value:'pca_clusters.png', status:'✅ Generated', time:'2 clusters' },
                { label:'Risk Ranking Chart', value:'risk_ranking.png', status:'✅ Generated', time:'Top 50' },
                { label:'API Endpoint', value:'/api/fra-data/', status:'✅ Live', time:'JSON · 500 records' },
              ].map(p => (
                <div key={p.label} className="pipeline-row">
                  <div>
                    <div className="pipe-label">{p.label}</div>
                    <div className="pipe-val">{p.value}</div>
                  </div>
                  <div style={{ textAlign:'right' }}>
                    <div className="pipe-status">{p.status}</div>
                    <div className="pipe-time">{p.time}</div>
                  </div>
                </div>
              ))}
            </div>
          </PanelBody>
        </Panel>
      </div>
    </div>
  );
}
