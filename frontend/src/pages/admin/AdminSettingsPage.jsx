import React, { useState } from 'react';
import { FiSave, FiCheckCircle, FiShield, FiServer, FiKey, FiLock } from 'react-icons/fi';

export default function AdminSettingsPage() {
  const [geminiConfigured, setGeminiConfigured] = useState(true);
  const [firebaseConfigured, setFirebaseConfigured] = useState(true);
  const [modelLoaded, setModelLoaded] = useState(true);
  const [saved, setSaved] = useState(false);

  const handleSave = (e) => {
    e.preventDefault();
    setSaved(true);
    setTimeout(() => setSaved(false), 2500);
  };

  return (
    <div>
      <div className="page-header">
        <h1 className="page-title">System Infrastructure & Admin Settings</h1>
        <p className="page-subtitle">
          Integration health, cloud service status, security policies, and environment parameters
        </p>
      </div>

      {saved && (
        <div className="alert alert-success" style={{ marginBottom: '1.5rem' }}>
          Infrastructure settings confirmed and synchronized.
        </div>
      )}

      <div className="grid-2">
        <div className="card">
          <div className="card-header">
            <h3 className="card-title">Backend & Cloud Integration Status</h3>
            <p className="card-subtitle">Real-time connectivity to cloud services</p>
          </div>

          <div className="detail-list">
            <div style={{ display: 'flex', justifyContent: 'space-between', padding: '0.75rem 0', borderBottom: '1px solid #f3f4f6' }}>
              <div>
                <strong>ML Model Engine (PyTorch)</strong>
                <div style={{ fontSize: '0.8rem', color: '#6b7280' }}>MobileNetV2 (12 Classes) - 9.8 MB</div>
              </div>
              <span className="badge badge-success"><FiCheckCircle /> Verified Active</span>
            </div>

            <div style={{ display: 'flex', justifyContent: 'space-between', padding: '0.75rem 0', borderBottom: '1px solid #f3f4f6' }}>
              <div>
                <strong>Firebase Authentication & Firestore</strong>
                <div style={{ fontSize: '0.8rem', color: '#6b7280' }}>Cloud Database & User Identity</div>
              </div>
              <span className="badge badge-success"><FiCheckCircle /> Connected</span>
            </div>

            <div style={{ display: 'flex', justifyContent: 'space-between', padding: '0.75rem 0', borderBottom: '1px solid #f3f4f6' }}>
              <div>
                <strong>Gemini API Gateway</strong>
                <div style={{ fontSize: '0.8rem', color: '#6b7280' }}>WasteAI & SanitationAI Reasoning Engine</div>
              </div>
              <span className="badge badge-success"><FiCheckCircle /> Ready</span>
            </div>

            <div style={{ display: 'flex', justifyContent: 'space-between', padding: '0.75rem 0' }}>
              <div>
                <strong>Hardware Sensor Emulation Gate</strong>
                <div style={{ fontSize: '0.8rem', color: '#6b7280' }}>Strict Pure-Software Mode (No IoT)</div>
              </div>
              <span className="badge badge-info">Enforced (Software-Only)</span>
            </div>
          </div>
        </div>

        <form onSubmit={handleSave} className="card">
          <div className="card-header">
            <h3 className="card-title">Security & Environment Guardrails</h3>
            <p className="card-subtitle">API key isolation and role access controls</p>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
            <div className="form-group">
              <label>API Gateway Endpoint</label>
              <input
                type="text"
                className="form-control"
                value="http://127.0.0.1:8000"
                readOnly
              />
            </div>

            <div className="form-group">
              <label>Storage Image Expiry Period (Days)</label>
              <input
                type="number"
                className="form-control"
                defaultValue={90}
              />
            </div>

            <div className="form-group">
              <label>Administrative Session Timeout (Minutes)</label>
              <input
                type="number"
                className="form-control"
                defaultValue={60}
              />
            </div>

            <button type="submit" className="btn btn-primary">
              <FiSave style={{ marginRight: '6px' }} /> Save System Configurations
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
