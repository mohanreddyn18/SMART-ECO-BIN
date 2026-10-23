import React from 'react';
import { useAuth } from '../../context/AuthContext';
import { FiUser, FiMail, FiShield, FiClock, FiCheckCircle } from 'react-icons/fi';

export default function ProfilePage() {
  const { user, isAdmin } = useAuth();

  return (
    <div>
      <div className="page-header">
        <h1 className="page-title">Researcher Profile</h1>
        <p className="page-subtitle">Personal account credentials, project affiliation, and role assignment</p>
      </div>

      <div className="grid-2">
        <div className="card">
          <div className="card-header">
            <h3 className="card-title">User Information</h3>
            <p className="card-subtitle">Active credentials stored in session</p>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '1.25rem', marginBottom: '1.5rem' }}>
            <div
              style={{
                width: '64px',
                height: '64px',
                borderRadius: '50%',
                backgroundColor: '#2563eb',
                color: '#fff',
                fontSize: '1.75rem',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontWeight: 600
              }}
            >
              {user?.name ? user.name.charAt(0).toUpperCase() : 'U'}
            </div>
            <div>
              <h2 style={{ margin: 0, fontSize: '1.3rem', color: '#111827' }}>
                {user?.name || 'Academic Researcher'}
              </h2>
              <p style={{ margin: '4px 0 0', color: '#6b7280', fontSize: '0.9rem' }}>
                {user?.email || 'user@ecosortai.com'}
              </p>
            </div>
          </div>

          <div className="detail-list">
            <div style={{ display: 'flex', justifyContent: 'space-between', padding: '0.75rem 0', borderBottom: '1px solid #f3f4f6' }}>
              <span style={{ color: '#6b7280', display: 'flex', alignItems: 'center', gap: '8px' }}>
                <FiShield /> System Role
              </span>
              <span className={`badge ${isAdmin ? 'badge-danger' : 'badge-info'}`}>
                {user?.role ? user.role.toUpperCase() : 'USER'}
              </span>
            </div>

            <div style={{ display: 'flex', justifyContent: 'space-between', padding: '0.75rem 0', borderBottom: '1px solid #f3f4f6' }}>
              <span style={{ color: '#6b7280', display: 'flex', alignItems: 'center', gap: '8px' }}>
                <FiMail /> Contact Email
              </span>
              <span style={{ fontWeight: 500 }}>{user?.email}</span>
            </div>

            <div style={{ display: 'flex', justifyContent: 'space-between', padding: '0.75rem 0' }}>
              <span style={{ color: '#6b7280', display: 'flex', alignItems: 'center', gap: '8px' }}>
                <FiClock /> Registered Date
              </span>
              <span style={{ color: '#6b7280' }}>
                {user?.createdAt ? new Date(user.createdAt).toLocaleDateString() : 'Active Session'}
              </span>
            </div>
          </div>
        </div>

        {/* Project Attribution Card */}
        <div className="card">
          <div className="card-header">
            <h3 className="card-title">Project Accreditation</h3>
            <p className="card-subtitle">Final-Year B.Tech Academic Capstone</p>
          </div>

          <div style={{ fontSize: '0.9rem', color: '#4b5563', lineHeight: 1.7 }}>
            <p><strong>Project Code:</strong> RJ 147</p>
            <p><strong>Official Title:</strong> Smart Waste Segregation and Sanitation System</p>
            <p><strong>Department:</strong> B.Tech CSE / AIML</p>
            <p><strong>Application:</strong> EcoSort AI — Web Intelligence Platform</p>
            <p><strong>Architecture:</strong> Pure Software Application (No Physical Hardware)</p>
            <div style={{ marginTop: '1rem', padding: '0.75rem', background: '#eff6ff', borderRadius: '6px', color: '#1e40af' }}>
              <FiCheckCircle style={{ marginRight: '6px' }} />
              Authorized testing and research terminal
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
