import { useState, useEffect } from 'react';
import { NavLink, Outlet, useLocation } from 'react-router-dom';
import { Map, BarChart2, Target, FileText, Home, Menu, X, Flame, Sprout, LogOut } from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import './Layout.css';

const NAV = [
  { to: '/', icon: Home, label: 'Dashboard', end: true },
  { to: '/map', icon: Map, label: 'FRA Atlas Map' },
  { to: '/analytics', icon: BarChart2, label: 'Analytics' },
  { to: '/dss', icon: Target, label: 'DSS' },
  { to: '/fire', icon: Flame, label: 'Fire Alert' },
  { to: '/crops', icon: Sprout, label: 'Crop Advisor' },
  { to: '/reports', icon: FileText, label: 'Reports' },
];

export default function Layout() {
  const [menuOpen, setMenuOpen] = useState(false);
  const [largeText, setLargeText] = useState(false);
  const [hindi, setHindi] = useState(false);
  const location = useLocation();
  const isMapPage = location.pathname === '/map';
  const { signOut } = useAuth();

  useEffect(() => {
    document.body.classList.toggle('a11y-large', largeText);
  }, [largeText]);
  useEffect(() => {
    document.documentElement.lang = hindi ? 'hi' : 'en';
  }, [hindi]);

  function skipToMain(e) {
    e.preventDefault();
    const el = document.getElementById('main');
    if (el) { el.focus(); el.scrollIntoView(); }
  }

  return (
    <div className="app-shell">
      {/* Utility Bar */}
      <div className="utility-bar">
        <div className="utility-inner">
          <div className="ministry-row">
            <svg className="emblem" viewBox="0 0 100 80" fill="currentColor">
              <circle cx="50" cy="26" r="16" fill="none" stroke="currentColor" strokeWidth="3.5"/>
              <circle cx="50" cy="26" r="5" />
              <line x1="50" y1="10" x2="50" y2="42" stroke="currentColor" strokeWidth="1.8"/>
              <line x1="34" y1="26" x2="66" y2="26" stroke="currentColor" strokeWidth="1.8"/>
              <line x1="39" y1="15" x2="61" y2="37" stroke="currentColor" strokeWidth="1.8"/>
              <line x1="61" y1="15" x2="39" y2="37" stroke="currentColor" strokeWidth="1.8"/>
              <rect x="28" y="48" width="44" height="5" rx="2"/>
              <rect x="20" y="56" width="60" height="4" rx="2"/>
            </svg>
            <div>
              <div className="ministry-name">Ministry of Tribal Affairs, Government of India</div>
              <div className="ministry-hindi">वन अधिकार अधिनियम कार्यान्वयन निगरानी प्रणाली</div>
            </div>
          </div>
          <div className="utility-links">
            <a className="util-link" href="#main" onClick={skipToMain}>Skip to Main</a>
            <span className="util-sep">|</span>
            <button className="util-link" type="button" aria-pressed={largeText}
              onClick={() => setLargeText(v => !v)}>
              {largeText ? 'Standard Text' : 'Larger Text'}
            </button>
            <span className="util-sep">|</span>
            <button className="util-link lang-btn" type="button" aria-pressed={hindi}
              onClick={() => setHindi(v => !v)}>
              {hindi ? 'English' : 'हिंदी'}
            </button>
            <span className="util-sep">|</span>
            <button className="util-link signout" type="button" onClick={signOut}>
              <LogOut size={13} /> Sign out
            </button>
          </div>
        </div>
      </div>

      {/* Header */}
      <header className="site-header">
        <div className="header-inner">
          <NavLink to="/" className="brand">
            <div className="brand-logo">🌿</div>
            <div>
              <div className="brand-title">FRA Atlas</div>
              <div className="brand-sub">AI-Powered Decision Support System</div>
            </div>
          </NavLink>

          <nav className={`main-nav ${menuOpen ? 'open' : ''}`}>
            {NAV.map(({ to, icon: Icon, label, end }) => (
              <NavLink
                key={to} to={to} end={end}
                className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}
                onClick={() => setMenuOpen(false)}
              >
                <Icon size={15} />
                {label}
              </NavLink>
            ))}
          </nav>

          <button className="hamburger" onClick={() => setMenuOpen(o => !o)} aria-label="Toggle menu">
            {menuOpen ? <X size={20} /> : <Menu size={20} />}
          </button>
        </div>
      </header>

      {/* Breadcrumb */}
      {!isMapPage && (
        <div className="breadcrumb-bar">
          <div className="breadcrumb-inner">
            <NavLink to="/">Home</NavLink>
            {location.pathname !== '/' && (
              <>
                <span className="bc-sep">›</span>
                <span>{NAV.find(n => n.to === location.pathname)?.label}</span>
              </>
            )}
          </div>
        </div>
      )}

      {/* Page Content */}
      <main id="main" tabIndex={-1} className={`main-content ${isMapPage ? 'map-layout' : ''}`}>
        <Outlet />
      </main>

      {/* Footer */}
      {!isMapPage && (
        <footer className="site-footer">
          <div className="footer-inner">
            <div className="footer-grid">
              <div>
                <div className="footer-heading">FRA Atlas</div>
                <p className="footer-text">AI-powered monitoring for Forest Rights Act implementation across India's forest-dwelling communities.</p>
              </div>
              <div>
                <div className="footer-heading">Resources</div>
                <div className="footer-links">
                  <a href="#">FRA, 2006 Act Text</a>
                  <a href="#">MoTA Guidelines</a>
                  <a href="#">State Nodal Officers</a>
                </div>
              </div>
              <div>
                <div className="footer-heading">Priority States</div>
                <div className="footer-links">
                  <a href="#">Madhya Pradesh</a>
                  <a href="#">Tripura</a>
                  <a href="#">Odisha</a>
                  <a href="#">Telangana</a>
                </div>
              </div>
              <div>
                <div className="footer-heading">Contact</div>
                <p className="footer-text">Ministry of Tribal Affairs<br/>Shastri Bhawan, New Delhi — 110 001<br/>
                <a href="mailto:fra-atlas@tribal.gov.in">fra-atlas@tribal.gov.in</a></p>
              </div>
            </div>
            <div className="footer-bottom">
              <span>© 2025 Ministry of Tribal Affairs, Government of India</span>
              <span>Last Updated: {new Date().toLocaleDateString('en-IN', { day:'2-digit', month:'long', year:'numeric' })}</span>
            </div>
          </div>
        </footer>
      )}
    </div>
  );
}
