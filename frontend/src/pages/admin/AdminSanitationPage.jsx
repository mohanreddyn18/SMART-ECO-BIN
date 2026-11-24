import React, { useEffect, useState } from 'react';
import { api } from '../../services/api';

export default function AdminSanitationPage() {
  const [sanitation, setSanitation] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    let active = true;
    api.getSanitation()
      .then((data) => {
        if (active) setSanitation(data);
      })
      .catch((requestError) => {
        if (active) setError(requestError.message || 'Could not load sanitation telemetry.');
      })
      .finally(() => {
        if (active) setLoading(false);
      });

    return () => {
      active = false;
    };
  }, []);

  return (
    <div>
      <div className="page-header">
        <h1 className="page-title">Sanitation Intelligence Rules Engine</h1>
        <p className="page-subtitle">
          Review software-computed sanitation status and indicators from stored classification events
        </p>
      </div>

      <div className="grid-2">
        <section className="card">
          <div className="card-header">
            <h3 className="card-title">Evaluation Policy</h3>
            <p className="card-subtitle">Rules are evaluated by the backend and are not edited from this screen.</p>
          </div>
          <p>
            {sanitation?.reason || (loading
              ? 'Loading the current backend assessment...'
              : 'No sanitation assessment is available.')}
          </p>
          <p style={{ fontSize: '0.85rem', color: '#6b7280' }}>
            Data source: {sanitation?.telemetrySource || 'Unavailable'}.
            {' '}Physical sensors: {sanitation?.hardwareSensors ? 'connected' : 'not connected'}.
          </p>
        </section>

        <section className="card">
          <div className="card-header">
            <h3 className="card-title">Current Active Indicators</h3>
            <p className="card-subtitle">Values returned by the sanitation API</p>
          </div>

          {error && <div className="alert alert-error" role="alert">{error}</div>}
          {!loading && !error && sanitation?.currentStatus === 'UNAVAILABLE' && (
            <div className="alert alert-info" role="status">{sanitation.reason}</div>
          )}
          {!loading && !error && sanitation?.supportingIndicators?.length === 0 && (
            <p>No indicators are available from the current telemetry.</p>
          )}
          <div className="detail-list">
            {(sanitation?.supportingIndicators || []).map((indicator) => (
              <div key={indicator.indicator} style={{ padding: '0.75rem 0', borderBottom: '1px solid #f3f4f6' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <strong>{indicator.indicator}</strong>
                  <span className={`badge ${indicator.status === 'NORMAL' ? 'badge-success' : 'badge-warning'}`}>
                    {indicator.status}
                  </span>
                </div>
                <div style={{ fontSize: '0.8rem', color: '#6b7280', marginTop: '2px' }}>
                  Current: {indicator.value} | Guardrail: {indicator.threshold}
                </div>
              </div>
            ))}
          </div>
        </section>
      </div>
    </div>
  );
}
