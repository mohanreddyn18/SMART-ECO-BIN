import React from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';

// Layout
import DashboardLayout from './layouts/DashboardLayout';

// Common Route Protectors
import ProtectedRoute from './components/common/ProtectedRoute';
import AdminRoute from './components/common/AdminRoute';

// Public Landing Page
import LandingPage from './pages/public/LandingPage';

// Auth Pages
import LoginPage from './pages/auth/LoginPage';
import RegisterPage from './pages/auth/RegisterPage';
import ForgotPasswordPage from './pages/auth/ForgotPasswordPage';

// User Pages
import DashboardPage from './pages/user/DashboardPage';
import WasteDetectionPage from './pages/user/WasteDetectionPage';
import HistoryPage from './pages/user/HistoryPage';
import AnalyticsPage from './pages/user/AnalyticsPage';
import SanitationPage from './pages/user/SanitationPage';
import AnomalyPage from './pages/user/AnomalyPage';
import PredictionsPage from './pages/user/PredictionsPage';
import WasteAIPage from './pages/user/WasteAIPage';
import ProfilePage from './pages/user/ProfilePage';
import SettingsPage from './pages/user/SettingsPage';

// Admin Pages
import AdminDashboardPage from './pages/admin/AdminDashboardPage';
import UsersPage from './pages/admin/UsersPage';
import WasteRecordsPage from './pages/admin/WasteRecordsPage';
import AdminAnalyticsPage from './pages/admin/AdminAnalyticsPage';
import AdminSanitationPage from './pages/admin/AdminSanitationPage';
import AdminAnomalyPage from './pages/admin/AdminAnomalyPage';
import AdminPredictionsPage from './pages/admin/AdminPredictionsPage';
import SanitationAIPage from './pages/admin/SanitationAIPage';
import AdminSettingsPage from './pages/admin/AdminSettingsPage';

export default function App() {
  return (
    <Routes>
      {/* Public Landing & Discovery Routes */}
      <Route path="/" element={<LandingPage />} />
      <Route path="/welcome" element={<LandingPage />} />

      {/* Public Authentication Routes */}
      <Route path="/login" element={<LoginPage />} />
      <Route path="/register" element={<RegisterPage />} />
      <Route path="/forgot-password" element={<ForgotPasswordPage />} />

      {/* User Protected Routes with Dashboard Layout */}
      <Route
        path="/"
        element={
          <ProtectedRoute>
            <DashboardLayout />
          </ProtectedRoute>
        }
      >
        <Route path="dashboard" element={<DashboardPage />} />
        <Route path="detect" element={<WasteDetectionPage />} />
        <Route path="history" element={<HistoryPage />} />
        <Route path="analytics" element={<AnalyticsPage />} />
        <Route path="sanitation" element={<SanitationPage />} />
        <Route path="anomalies" element={<AnomalyPage />} />
        <Route path="predictions" element={<PredictionsPage />} />
        <Route path="wasteai" element={<WasteAIPage />} />
        <Route path="profile" element={<ProfilePage />} />
        <Route path="settings" element={<SettingsPage />} />
      </Route>

      {/* Admin Protected Routes with Dashboard Layout */}
      <Route
        path="/admin"
        element={
          <AdminRoute>
            <DashboardLayout />
          </AdminRoute>
        }
      >
        <Route index element={<Navigate to="/admin/dashboard" replace />} />
        <Route path="dashboard" element={<AdminDashboardPage />} />
        <Route path="users" element={<UsersPage />} />
        <Route path="records" element={<WasteRecordsPage />} />
        <Route path="analytics" element={<AdminAnalyticsPage />} />
        <Route path="sanitation" element={<AdminSanitationPage />} />
        <Route path="anomalies" element={<AdminAnomalyPage />} />
        <Route path="predictions" element={<AdminPredictionsPage />} />
        <Route path="sanitationai" element={<SanitationAIPage />} />
        <Route path="settings" element={<AdminSettingsPage />} />
      </Route>

      {/* Catch-all redirect */}
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
