import { createContext, useContext, useEffect, useState } from 'react';
import { login as apiLogin, logout as apiLogout, getAccess } from '../api/client';

const AuthCtx = createContext(null);

export function AuthProvider({ children }) {
  const [authed, setAuthed] = useState(!!getAccess());
  const [user, setUser] = useState(null);

  useEffect(() => { setAuthed(!!getAccess()); }, []);

  async function signIn(username, password) {
    const data = await apiLogin(username, password);
    setUser(data.user || { username });
    setAuthed(true);
    return data;
  }
  async function signOut() {
    await apiLogout();
    setUser(null);
    setAuthed(false);
  }
  return (
    <AuthCtx.Provider value={{ authed, user, signIn, signOut }}>
      {children}
    </AuthCtx.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthCtx);
  if (!ctx) throw new Error('useAuth must be used within AuthProvider');
  return ctx;
}
