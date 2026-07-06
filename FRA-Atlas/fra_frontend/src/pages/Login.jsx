import { useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import './Login.css';

export default function Login() {
  const { signIn } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);

  const from = location.state?.from?.pathname || '/';

  async function submit(e) {
    e.preventDefault();
    setError('');
    setBusy(true);
    try {
      await signIn(username.trim(), password);
      navigate(from, { replace: true });
    } catch (err) {
      setError(err.message || 'Sign in failed.');
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="login-shell">
      <div className="login-utility">
        <span>भारत सरकार · Government of India</span>
        <span>Ministry of Tribal Affairs</span>
      </div>
      <div className="login-band" />

      <main className="login-main" id="main">
        <div className="login-card">
          <div className="login-brand">
            <span className="login-emblem" aria-hidden="true">🌿</span>
            <div>
              <div className="login-title">National FRA Atlas</div>
              <div className="login-sub">Forest Rights Act Decision Support System</div>
            </div>
          </div>

          <form className="login-form" onSubmit={submit} noValidate>
            <label className="login-label" htmlFor="username">Username</label>
            <input
              id="username" className="login-input" autoComplete="username"
              value={username} onChange={(e) => setUsername(e.target.value)}
              required autoFocus
            />

            <label className="login-label" htmlFor="password">Password</label>
            <input
              id="password" type="password" className="login-input"
              autoComplete="current-password"
              value={password} onChange={(e) => setPassword(e.target.value)}
              required
            />

            {error && <div className="login-error" role="alert">{error}</div>}

            <button className="login-btn" type="submit" disabled={busy}>
              {busy ? 'Signing in…' : 'Sign in'}
            </button>
          </form>

          <div className="login-demo">
            Demo access — <strong>analyst</strong> / <strong>FraAtlas@2026</strong>
          </div>
        </div>
        <p className="login-foot">
          Authorized officials only. Access is monitored and recorded under the
          Forest Rights Act, 2006 and the DPDP Act, 2023.
        </p>
      </main>
      <div className="login-tiranga" aria-hidden="true" />
    </div>
  );
}
