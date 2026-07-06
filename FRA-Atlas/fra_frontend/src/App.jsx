import { BrowserRouter, Routes, Route, Navigate, useLocation } from 'react-router-dom';
import Layout from './components/layout/Layout';
import Dashboard from './pages/Dashboard';
import MapPage from './pages/MapPage';
import Analytics from './pages/Analytics';
import DSS from './pages/DSS';
import Reports from './pages/Reports';
import FireForecast from './pages/FireForecast';
import CropRecommender from './pages/CropRecommender';
import Login from './pages/Login';
import { AuthProvider, useAuth } from './context/AuthContext';
import { DataProvider } from './context/DataContext';
import './index.css';
import './components/DataState.css';

function RequireAuth({ children }) {
  const { authed } = useAuth();
  const location = useLocation();
  if (!authed) return <Navigate to="/login" replace state={{ from: location }} />;
  return children;
}

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <DataProvider>
          <Routes>
            <Route path="/login" element={<Login />} />
            <Route path="/" element={<RequireAuth><Layout /></RequireAuth>}>
              <Route index element={<Dashboard />} />
              <Route path="map" element={<MapPage />} />
              <Route path="analytics" element={<Analytics />} />
              <Route path="dss" element={<DSS />} />
              <Route path="fire" element={<FireForecast />} />
              <Route path="crops" element={<CropRecommender />} />
              <Route path="reports" element={<Reports />} />
            </Route>
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </DataProvider>
      </AuthProvider>
    </BrowserRouter>
  );
}
