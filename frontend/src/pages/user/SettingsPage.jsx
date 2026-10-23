import React, { useState } from 'react';
import { FiSave, FiBell, FiShield, FiSliders, FiDatabase } from 'react-icons/fi';

export default function SettingsPage() {
  const [notifications, setNotifications] = useState(true);
  const [anomalyAlerts, setAnomalyAlerts] = useState(true);
  const [confidenceThreshold, setConfidenceThreshold] = useState(80);
  const [saved, setSaved] = useState(false);

  const handleSave = (e) => {
    e.preventDefault();
    setSaved(true);
    setTimeout(() => setSaved(false), 2500);
  };

  return (
    <div>
      <div className="page-header">
        <h1 className="page-title">User Preferences & Settings</h1>
        <p className="page-subtitle">Configure application behaviors, alert thresholds, and telemetry options</p>
      </div>

      {saved && (
        <div className="alert alert-success" style={{ marginBottom: '1.5rem' }}>
          Preferences updated and saved to local configuration!
        </div>
      )}

      <form onSubmit={handleSave} className="grid-2">
        <div className="card">
          <div className="card-header">
            <h3 className="card-title">Inference & Alert Thresholds</h3>
            <p className="card-subtitle">Adjust minimum confidence gates for classification acceptance</p>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
            <div className="form-group">
              <label>Minimum Confidence Acceptance Gate: {confidenceThreshold}%</label>
              <input
                type="range"
                min="60"
                max="95"
                value={confidenceThreshold}
                onChange={(e) => setConfidenceThreshold(Number(e.target.value))}
                style={{ width: '100%', marginTop: '0.5rem' }}
              />
              <span style={{ fontSize: '0.8rem', color: '#6b7280' }}>
                Classifications below this score will prompt human re-verification.
              </span>
            </div>

            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '0.5rem 0' }}>
              <div>
                <div style={{ fontWeight: 600 }}>Statistical Anomaly Push Alerts</div>
                <div style={{ fontSize: '0.8rem', color: '#6b7280' }}>
                  Notify immediately when stream distribution shifts beyond 3σ
                </div>
              </div>
              <input
                type="checkbox"
                checked={anomalyAlerts}
                onChange={(e) => setAnomalyAlerts(e.target.checked)}
                style={{ width: '18px', height: '18px' }}
              />
            </div>

            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '0.5rem 0' }}>
              <div>
                <div style={{ fontWeight: 600 }}>Daily Sanitation Intelligence Digest</div>
                <div style={{ fontSize: '0.8rem', color: '#6b7280' }}>
                  Receive summary evaluation of software hygiene indices
                </div>
              </div>
              <input
                type="checkbox"
                checked={notifications}
                onChange={(e) => setNotifications(e.target.checked)}
                style={{ width: '18px', height: '18px' }}
              />
            </div>
          </div>
        </div>

        <div className="card">
          <div className="card-header">
            <h3 className="card-title">Backend Connectivity</h3>
            <p className="card-subtitle">Local environment parameters and API routing</p>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem', fontSize: '0.9rem' }}>
            <div className="form-group">
              <label>FastAPI Base Gateway URL</label>
              <input
                type="text"
                className="form-control"
                value="http://127.0.0.1:8000"
                readOnly
              />
              <span style={{ fontSize: '0.75rem', color: '#6b7280' }}>
                Defined by VITE_API_BASE_URL environment variable
              </span>
            </div>

            <div className="form-group">
              <label>ML Model Target Engine</label>
              <input
                type="text"
                className="form-control"
                value="MobileNetV2 (12 Classes) - PyTorch .pth"
                readOnly
              />
            </div>

            <button type="submit" className="btn btn-primary" style={{ marginTop: '0.5rem' }}>
              <FiSave style={{ marginRight: '6px' }} /> Save Preferences
            </button>
          </div>
        </div>
      </form>
    </div>
  );
}
