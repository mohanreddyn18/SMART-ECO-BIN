import React, { useEffect, useState } from 'react';
import { FiCheckCircle, FiShield, FiXCircle } from 'react-icons/fi';
import { api } from '../../services/api';
import { isFirebaseConfigured } from '../../services/firebase';

function StatusBadge({ available, label }) {
  return available
    ? <span className="badge badge-success"><FiCheckCircle /> {label}</span>
    : <span className="badge badge-warning"><FiXCircle /> Not configured / unavailable</span>;
}

export default function AdminSettingsPage() {
  const [health, setHealth] = useState(null);
  const [storage, setStorage] = useState(null);
  const [security, setSecurity] = useState(null);
  const [error, setError] = useState('');

  useEffect(() => {
    let active = true;
    Promise.all([api.getHealth(), api.getStorageStatus(), api.getSecurityPosture()])
      .then(([backendHealth, storageStatus, securityStatus]) => {
        if (!active) return;
        setHealth(backendHealth);
        setStorage(storageStatus);
        setSecurity(securityStatus);
      })
      .catch((requestError) => {
        if (active) setError(requestError.message || 'Could not load live backend status.');
      });

    return () => {
      active = false;
    };
  }, []);

  return (
    <div>
      <div className="page-header">
        <h1 className="page-title">System Infrastructure & Admin Settings</h1>
        <p className="page-subtitle">
          Live integration health, cloud service status, and security configuration
        </p>
      </div>

      {error && <div className="alert alert-error" role="alert">{error}</div>}

      <div className="grid-2">
        <div className="card">
          <div className="card-header">
            <h3 className="card-title">Backend & Cloud Integration Status</h3>
            <p className="card-subtitle">Values reported by the production API, not assumed configuration</p>
          </div>

          <div className="detail-list">
            <div style={{ display: 'flex', justifyContent: 'space-between', padding: '0.75rem 0', borderBottom: '1px solid #f3f4f6' }}>
              <strong>MobileNetV2 Classifier</strong>
              <StatusBadge available={health?.classifier_loaded} label="Loaded" />
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', padding: '0.75rem 0', borderBottom: '1px solid #f3f4f6' }}>
              <strong>Waste Object Detector</strong>
              <StatusBadge available={health?.detector_loaded} label="Loaded" />
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', padding: '0.75rem 0', borderBottom: '1px solid #f3f4f6' }}>
              <strong>Firebase Authentication</strong>
              <StatusBadge available={isFirebaseConfigured && security?.server_side_token_verification} label="Configured" />
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', padding: '0.75rem 0', borderBottom: '1px solid #f3f4f6' }}>
              <strong>Persistent Cloud Storage</strong>
              <StatusBadge available={storage?.persistent_cloud_enabled} label={storage?.cloud_provider || 'Connected'} />
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', padding: '0.75rem 0' }}>
              <strong>Gemini AI Assistant</strong>
              <StatusBadge available={health?.gemini_configured} label="Configured" />
            </div>
          </div>
          {health && (
            <p style={{ marginTop: '1rem', fontSize: '0.85rem', color: '#6b7280' }}>
              API status: {health.status}. Storage mode: {storage?.mode || 'Unavailable'}.
            </p>
          )}
        </div>

        <div className="card">
          <div className="card-header">
            <h3 className="card-title">Security & Environment Guardrails</h3>
            <p className="card-subtitle">Sensitive configuration is server-side and is not editable in this browser.</p>
          </div>
          <div className="detail-list">
            <p><strong>API Gateway Endpoint</strong><br />{import.meta.env.VITE_API_BASE_URL || 'Same origin / local Vite proxy'}</p>
            <p><strong>Authentication Provider</strong><br />{security?.admin_auth_mode || 'Unavailable'}</p>
            <p><strong>Role-based access control</strong><br />{security?.rbac_enforced ? 'Enabled' : 'Unavailable'}</p>
            <p><strong>Allowed frontend origins</strong><br />{security?.cors_origins_count ?? 'Unavailable'}</p>
            <p style={{ display: 'flex', alignItems: 'center', gap: '6px', color: '#6b7280' }}>
              <FiShield /> Configure secrets and access policy in the hosting provider, never in this page.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
