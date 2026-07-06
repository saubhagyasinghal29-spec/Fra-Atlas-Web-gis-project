import { useState, useEffect, useRef } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import { RISK_COLORS, ALL_STATES, DISTRICT_COORDS, STATE_CENTERS } from '../data/constants';
import RiskBadge from '../components/layout/RiskBadge';
import { useFraData } from '../context/DataContext';
import { Loading } from '../components/DataState';
import './MapPage.css';

// Fix default marker icons
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({ iconRetinaUrl: null, iconUrl: null, shadowUrl: null });

function getCoords(d, idx) {
  const base = DISTRICT_COORDS[d.district];
  const sc = STATE_CENTERS[d.state] || [22.0, 82.0];
  const [lat, lng] = base || sc;
  const angle = (idx * 137.508) % 360 * Math.PI / 180;
  const dist = (idx % 6) * 0.22 / 6;
  return [lat + Math.sin(angle) * dist, lng + Math.cos(angle) * dist];
}

function MapView({ FRA_DATA }) {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const mapRef = useRef(null);
  const leafletMap = useRef(null);
  const clusterGroup = useRef(null);
  const allMarkers = useRef([]);
  const tileLayers = useRef({});
  const currentTile = useRef(null);

  const [filterRisk, setFilterRisk] = useState('');
  const [filterState, setFilterState] = useState(searchParams.get('state') || '');
  const [search, setSearch] = useState('');
  const [selected, setSelected] = useState(null);
  const [count, setCount] = useState(FRA_DATA.length);
  const [mapLayer, setMapLayer] = useState('osm');

  const TILES = {
    osm: ['https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', '© OpenStreetMap'],
    satellite: ['https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', '© Esri'],
    topo: ['https://{s}.tile.opentopomap.org/{z}/{x}/{y}.png', '© OpenTopoMap'],
  };

  // Init map
  useEffect(() => {
    if (leafletMap.current) return;

    const map = L.map(mapRef.current, { center: [22.5, 82.0], zoom: 5 });
    leafletMap.current = map;

    const osm = L.tileLayer(TILES.osm[0], { attribution: TILES.osm[1] });
    osm.addTo(map);
    tileLayers.current.osm = osm;
    currentTile.current = osm;

    // Try to use MarkerClusterGroup if available via CDN, else plain LayerGroup
    let group;
    if (typeof window !== 'undefined' && window.L && window.L.markerClusterGroup) {
      group = window.L.markerClusterGroup({
        maxClusterRadius: 45,
        iconCreateFunction(grp) {
          const children = grp.getAllChildMarkers();
          const order = ['Critical','Moderate','Good','Excellent'];
          let topRisk = 'Excellent';
          children.forEach(m => {
            if (order.indexOf(m.options.riskLevel) < order.indexOf(topRisk)) topRisk = m.options.riskLevel;
          });
          const color = RISK_COLORS[topRisk];
          const n = grp.getChildCount();
          const size = n > 100 ? 44 : n > 30 ? 36 : 28;
          return L.divIcon({
            html: `<div style="background:${color};color:#fff;width:${size}px;height:${size}px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:${size<32?10:12}px;font-weight:700;border:2px solid rgba(255,255,255,0.7);box-shadow:0 2px 6px rgba(0,0,0,0.25)">${n}</div>`,
            className: 'fra-cluster',
            iconSize: [size, size],
            iconAnchor: [size/2, size/2],
          });
        }
      });
    } else {
      group = L.layerGroup();
    }
    clusterGroup.current = group;

    FRA_DATA.forEach((d, i) => {
      const [lat, lng] = getCoords(d, i);
      const r = Math.max(5, Math.min(15, d.ri / 9));
      const marker = L.circleMarker([lat, lng], {
        radius: r,
        fillColor: RISK_COLORS[d.rl],
        color: 'rgba(255,255,255,0.85)',
        weight: 1.5,
        fillOpacity: 0.88,
        riskLevel: d.rl,
      });

      marker.bindPopup(() => {
        const el = document.createElement('div');
        el.style.cssText = 'min-width:220px;font-family:Noto Sans,sans-serif;overflow:hidden;border-radius:6px';
        el.innerHTML = `
          <div style="background:#003087;color:#fff;padding:10px 13px">
            <div style="font-weight:700;font-size:14px">${d.district}</div>
            <div style="font-size:11.5px;opacity:.75">${d.state}</div>
          </div>
          <div style="padding:10px 13px">
            ${[
              ['Risk Level', `<span style="font-weight:700;color:${RISK_COLORS[d.rl]}">${d.rl}</span>`],
              ['Risk Index', d.ri.toFixed(1)],
              ['Approval Rate', (d.ar*100).toFixed(1)+'%'],
              ['Pending Claims', `<span style="color:#c0392b">${(d.pr*100).toFixed(1)}%</span>`],
              ['Processing', d.pt+' days'],
            ].map(([k,v]) => `<div style="display:flex;justify-content:space-between;padding:5px 0;border-bottom:1px solid #f0f2f6;font-size:12.5px"><span style="color:#6b6f8a">${k}</span><span style="font-weight:600">${v}</span></div>`).join('')}
          </div>`;
        return el;
      }, { maxWidth: 260 });

      marker.on('click', () => setSelected(d));
      group.addLayer(marker);
      allMarkers.current.push({ marker, data: d });
    });

    map.addLayer(group);

    return () => { map.remove(); leafletMap.current = null; };
  }, []);

  // Tile switch
  useEffect(() => {
    const map = leafletMap.current;
    if (!map) return;
    if (currentTile.current) map.removeLayer(currentTile.current);
    if (!tileLayers.current[mapLayer]) {
      tileLayers.current[mapLayer] = L.tileLayer(TILES[mapLayer][0], { attribution: TILES[mapLayer][1] });
    }
    tileLayers.current[mapLayer].addTo(map);
    tileLayers.current[mapLayer].bringToBack();
    currentTile.current = tileLayers.current[mapLayer];
  }, [mapLayer]);

  // Filter
  useEffect(() => {
    const group = clusterGroup.current;
    if (!group) return;
    group.clearLayers();
    let visible = 0;
    allMarkers.current.forEach(({ marker, data: d }) => {
      const ok = (!filterRisk || d.rl === filterRisk) &&
                 (!filterState || d.state === filterState) &&
                 (!search.trim() || d.district.toLowerCase().includes(search.toLowerCase()) || d.state.toLowerCase().includes(search.toLowerCase()));
      if (ok) { group.addLayer(marker); visible++; }
    });
    setCount(visible);
  }, [filterRisk, filterState, search]);

  function reset() {
    setFilterRisk(''); setFilterState(''); setSearch('');
    leafletMap.current?.setView([22.5, 82.0], 5);
  }

  const metrics = selected ? [
    { l:'Risk Index', v:selected.ri.toFixed(1), hi:selected.ri>60 },
    { l:'Risk Rank', v:'#'+selected.rr+' / 500', hi:selected.rr<=80 },
    { l:'Approval Rate', v:(selected.ar*100).toFixed(1)+'%', hi:false },
    { l:'Pending Claims', v:(selected.pr*100).toFixed(1)+'%', hi:selected.pr>0.3 },
    { l:'Avg Processing', v:selected.pt+' days', hi:selected.pt>110 },
    { l:'Forest Loss Rate', v:selected.fl.toFixed(2)+'%', hi:selected.fl>2 },
    { l:'Tribal Pop. Coverage', v:(selected.tc*100).toFixed(1)+'%', hi:false },
    { l:'CFR Recognition', v:(selected.cr*100).toFixed(1)+'%', hi:false },
    { l:'Rejection Rate', v:(selected.rjr*100).toFixed(1)+'%', hi:selected.rjr>0.15 },
    { l:'Encroachment Density', v:selected.enc.toFixed(3), hi:selected.enc>0.5 },
    { l:'Cluster', v:selected.cl===1?'High-Risk (1)':'Low-Risk (2)', hi:selected.cl===1 },
  ] : [];

  return (
    <div className="map-page">
      <div className="map-toolbar">
        <span className="tb-label">Filter:</span>
        <select className="tb-select" value={filterRisk} onChange={e=>setFilterRisk(e.target.value)}>
          <option value="">All Risk Levels</option>
          {['Critical','Moderate','Good','Excellent'].map(r=><option key={r} value={r}>{r}</option>)}
        </select>
        <select className="tb-select" value={filterState} onChange={e=>setFilterState(e.target.value)}>
          <option value="">All States</option>
          {ALL_STATES.map(s=><option key={s} value={s}>{s}</option>)}
        </select>
        <input className="tb-search" placeholder="🔍 Search district…" value={search} onChange={e=>setSearch(e.target.value)} />
        <div className="tb-sep" />
        <select className="tb-select" value={mapLayer} onChange={e=>setMapLayer(e.target.value)}>
          <option value="osm">Street Map</option>
          <option value="satellite">Satellite</option>
          <option value="topo">Topographic</option>
        </select>
        <div className="tb-sep" />
        <span className="tb-count">Showing <strong>{count}</strong> districts</span>
        <button className="btn-primary" style={{padding:'5px 12px',fontSize:12}} onClick={reset}>Reset</button>
      </div>

      <div className="map-body">
        <div ref={mapRef} id="fraMap" />

        <div className="map-legend">
          <div className="legend-title">Risk Level</div>
          {['Critical','Moderate','Good','Excellent'].map(r=>(
            <div key={r} className="legend-item">
              <span className="legend-dot" style={{background:RISK_COLORS[r]}} />{r}
            </div>
          ))}
          <div className="legend-note">Circle size ∝ Risk Index</div>
        </div>

        {selected && (
          <div className="detail-panel">
            <div className="detail-header">
              <div>
                <div className="detail-name">{selected.district}</div>
                <div className="detail-state">{selected.state}</div>
              </div>
              <button className="detail-close" onClick={()=>setSelected(null)}>✕</button>
            </div>
            <div className="detail-body">
              <RiskBadge level={selected.rl} />
              <div className="detail-bar-wrap">
                <div className="detail-bar"><div style={{width:`${selected.ri}%`,background:RISK_COLORS[selected.rl],height:'100%',borderRadius:4,transition:'width .5s'}} /></div>
                <strong style={{color:RISK_COLORS[selected.rl]}}>{selected.ri.toFixed(1)}</strong>
              </div>
              <div className="detail-metrics">
                {metrics.map(m=>(
                  <div key={m.l} className="detail-metric">
                    <span className="dm-label">{m.l}</span>
                    <span className="dm-val" style={{color:m.hi?'var(--risk-critical)':'var(--gray-900)'}}>{m.v}</span>
                  </div>
                ))}
              </div>
              <button className="btn-primary" style={{width:'100%',justifyContent:'center',marginTop:12,padding:'8px',fontSize:13}}
                onClick={()=>navigate(`/dss?state=${selected.state}&district=${selected.district}`)}>
                🎯 Open in DSS
              </button>
            </div>
          </div>
        )}

        <div className="map-side">
          <div className="side-hdr">
            <div className="side-title">District Inspector</div>
            <div className="side-hint">{selected?`${selected.district}, ${selected.state}`:'Click a marker to inspect'}</div>
          </div>
          {selected ? (
            <div className="side-body">
              <div style={{marginBottom:12}}>
                <div style={{fontSize:17,fontWeight:700}}>{selected.district}</div>
                <div style={{fontSize:12,color:'var(--gray-500)',marginBottom:8}}>{selected.state}</div>
                <RiskBadge level={selected.rl} />
              </div>
              <div className="detail-bar-wrap" style={{marginBottom:14}}>
                <div className="detail-bar" style={{height:10}}><div style={{width:`${selected.ri}%`,background:RISK_COLORS[selected.rl],height:'100%',borderRadius:4}} /></div>
                <strong style={{color:RISK_COLORS[selected.rl],fontSize:14}}>{selected.ri.toFixed(1)}</strong>
              </div>
              {metrics.map(m=>(
                <div key={m.l} className="detail-metric">
                  <span className="dm-label">{m.l}</span>
                  <span className="dm-val" style={{color:m.hi?'var(--risk-critical)':'var(--gray-900)'}}>{m.v}</span>
                </div>
              ))}
              <button className="btn-primary" style={{width:'100%',justifyContent:'center',marginTop:14,fontSize:13}}
                onClick={()=>navigate(`/dss?state=${selected.state}&district=${selected.district}`)}>
                🎯 Open in DSS
              </button>
            </div>
          ) : (
            <div className="side-empty">
              <div style={{fontSize:32,marginBottom:10}}>📍</div>
              <div>Click any marker on the map to view detailed FRA metrics for that district</div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}


export default function MapPage() {
  const { data: FRA_DATA, loading } = useFraData();
  if (loading) return <Loading label="Loading atlas…" />;
  return <MapView FRA_DATA={FRA_DATA} />;
}
