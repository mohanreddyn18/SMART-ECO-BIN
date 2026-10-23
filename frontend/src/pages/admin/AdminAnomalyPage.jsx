import React from 'react';
import { FiActivity, FiInfo } from 'react-icons/fi';

export default function AdminAnomalyPage() {
  return (
    <div>
      <div className="page-header">
        <h1 className="page-title">Anomaly Detection Rules</h1>
        <p className="page-subtitle">
          Read-only description of the checks applied to stored classification records
        </p>
      </div>

      <div className="alert alert-info" style={{ marginBottom: '1.5rem' }}>
        <FiInfo style={{ marginRight: '0.5rem', verticalAlign: 'middle' }} />
        These thresholds are currently fixed in the backend. This page does not save settings or change runtime behavior.
      </div>

      <div className="grid-2">
        <section className="card">
          <div className="card-header">
            <h2 className="card-title">Active record checks</h2>
            <p className="card-subtitle">Only the latest 20 records are evaluated after a 10-event minimum.</p>
          </div>
          <ul style={{ color: '#4b5563', lineHeight: 1.9, paddingLeft: '1.25rem' }}>
            <li>Hazardous-stream review when at least 20% of the sample is classified as hazardous.</li>
            <li>Classification review when at least 3 sampled records have confidence below 60%.</li>
          </ul>
        </section>

        <section className="card">
          <div className="card-header">
            <h2 className="card-title">Method and limitations</h2>
            <p className="card-subtitle">Deterministic checks, not a trained anomaly model.</p>
          </div>
          <div style={{ fontSize: '0.9rem', color: '#4b5563', lineHeight: 1.8 }}>
            <p><FiActivity style={{ marginRight: '0.4rem', verticalAlign: 'middle' }} /><strong>Algorithm:</strong> Rule-based checks on recent classification records</p>
            <p><strong>Location or sensor data:</strong> Not collected by these checks</p>
            <p><strong>Configuration:</strong> Requires a code change and redeployment</p>
          </div>
        </section>
      </div>
    </div>
  );
}
