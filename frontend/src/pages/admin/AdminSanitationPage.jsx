import React, { useState } from 'react';
import { FiSliders, FiShield, FiSave, FiCheckCircle } from 'react-icons/fi';

export default function AdminSanitationPage() {
  const [skewThreshold, setSkewThreshold] = useState(40);
  const [criticalCap, setCriticalCap] = useState(500);
  const [saved, setSaved] = useState(false);

  const handleSave = (e) => {
    e.preventDefault();
    setSaved(true);
    setTimeout(() => setSaved(false), 2500);
  };

  return (
    <div>
      <div className="page-header">
        <h1 className="page-title">Sanitation Intelligence Rules Engine</h1>
        <p className="page-subtitle">
          Configure software heuristics, stream skew thresholds, and alert triggers for sanitation status scoring
        </p>
      </div>

      {saved && (
        <div className="alert alert-success" style={{ marginBottom: '1.5rem' }}>
          Sanitation evaluation rules updated and recompiled!
        </div>
      )}

      <div className="grid-2">
        <form onSubmit={handleSave} className="card">
          <div className="card-header">
            <h3 className="card-title">Threshold Tuning</h3>
            <p className="card-subtitle">Define boundaries for GOOD, ATTENTION, and CRITICAL states</p>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
            <div className="form-group">
              <label>Organic Stream Skew Tolerance (±{skewThreshold}%)</label>
              <input
                type="range"
                min="20"
                max="60"
                value={skewThreshold}
                onChange={(e) => setSkewThreshold(Number(e.target.value))}
                style={{ width: '100%', marginTop: '0.5rem' }}
              />
              <span style={{ fontSize: '0.8rem', color: '#6b7280' }}>
                If wet waste volume exceeds normal baseline by this percentage, flag ATTENTION REQUIRED.
              </span>
            </div>

            <div className="form-group">
              <label>Daily Single-Zone Event Cap: {criticalCap} events/day</label>
              <input
                type="number"
                className="form-control"
                value={criticalCap}
                onChange={(e) => setCriticalCap(Number(e.target.value))}
              />
              <span style={{ fontSize: '0.8rem', color: '#6b7280' }}>
                Exceeding this volume triggers CRITICAL sanitation surge notice.
              </span>
            </div>

            <button type="submit" className="btn btn-primary">
              <FiSave style={{ marginRight: '6px' }} /> Update Heuristic Rules
            </button>
          </div>
        </form>

        <div className="card">
          <div className="card-header">
            <h3 className="card-title">Current Active Indicators</h3>
            <p className="card-subtitle">Real-time status of software-driven sanitation metrics</p>
          </div>

          <div className="detail-list">
            {MOCK_SANITATION_INTEL.supportingIndicators.map((ind, idx) => (
              <div key={idx} style={{ padding: '0.75rem 0', borderBottom: '1px solid #f3f4f6' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <strong>{ind.indicator}</strong>
                  <span className={`badge ${ind.status === 'NORMAL' ? 'badge-success' : 'badge-warning'}`}>
                    {ind.status}
                  </span>
                </div>
                <div style={{ fontSize: '0.8rem', color: '#6b7280', marginTop: '2px' }}>
                  Current: {ind.value} | Guardrail: {ind.threshold}
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
