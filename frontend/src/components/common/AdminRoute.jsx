import React from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';

export default function AdminRoute({ children }) {
  const { user, isAdmin, loading } = useAuth();
  const location = useLocation();

  if (loading) {
    return (
      <div className="loading-state" style={{ minHeight: '100vh' }}>
        <div className="spinner"></div>
        <p>Checking admin privileges...</p>
      </div>
    );
  }

  if (!user) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  if (!isAdmin) {
    return (
      <div className="empty-state" style={{ minHeight: '80vh' }}>
        <div className="empty-icon" style={{ fontSize: '3rem' }}>🚫</div>
        <h3>Access Restricted</h3>
        <p>You need administrator privileges to view this management console.</p>
        <div style={{ marginTop: '1rem' }}>
          <a href="/dashboard" className="btn btn-primary">Return to User Dashboard</a>
        </div>
      </div>
    );
  }

  return children;
}
