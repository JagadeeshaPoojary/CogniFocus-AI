import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './hooks/useAuth';
import MainLayout from './layouts/MainLayout';
import Login from './pages/Login';
import Dashboard from './pages/Dashboard';
import LiveMonitoring from './pages/LiveMonitoring';
import SeatMapPage from './pages/SeatMapPage';
import AlertsPage from './pages/AlertsPage';
import StudentsPage from './pages/StudentsPage';
import ClassroomsPage from './pages/ClassroomsPage';
import CamerasPage from './pages/CamerasPage';
import ReportsPage from './pages/ReportsPage';
import ConfigurationPage from './pages/ConfigurationPage';
import NotFound from './pages/NotFound';

export function App() {
  return (
    <AuthProvider>
      <Router>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route path="/" element={<MainLayout />}>
            <Route index element={<Navigate to="/dashboard" replace />} />
            <Route path="dashboard" element={<Dashboard />} />
            <Route path="live-monitoring" element={<LiveMonitoring />} />
            <Route path="seat-map" element={<SeatMapPage />} />
            <Route path="alerts" element={<AlertsPage />} />
            <Route path="students" element={<StudentsPage />} />
            <Route path="classrooms" element={<ClassroomsPage />} />
            <Route path="cameras" element={<CamerasPage />} />
            <Route path="reports" element={<ReportsPage />} />
            <Route path="configuration" element={<ConfigurationPage />} />
            <Route path="*" element={<NotFound />} />
          </Route>
        </Routes>
      </Router>
    </AuthProvider>
  );
}

export default App;
