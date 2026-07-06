import { createContext, useContext, useEffect, useState } from 'react';
import { loadAtlasData } from '../api/fraApi';
import { useAuth } from './AuthContext';

const DataCtx = createContext(null);

export function DataProvider({ children }) {
  const { authed } = useAuth();
  const [state, setState] = useState({ data: [], loading: true, source: null, error: null });

  useEffect(() => {
    let alive = true;
    if (!authed) { setState({ data: [], loading: false, source: null, error: null }); return; }
    setState((s) => ({ ...s, loading: true }));
    loadAtlasData().then((res) => {
      if (!alive) return;
      setState({ data: res.data, loading: false, source: res.source, error: res.error || null });
    });
    return () => { alive = false; };
  }, [authed]);

  return <DataCtx.Provider value={state}>{children}</DataCtx.Provider>;
}

// Returns { data, loading, source, error }. `source` is 'live' or 'bundled'.
export function useFraData() {
  const ctx = useContext(DataCtx);
  if (!ctx) throw new Error('useFraData must be used within DataProvider');
  return ctx;
}
