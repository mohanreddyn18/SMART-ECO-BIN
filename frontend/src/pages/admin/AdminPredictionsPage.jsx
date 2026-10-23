import React, { useCallback, useEffect, useState } from 'react';
import { FiAlertCircle, FiCheckCircle, FiDatabase, FiRefreshCw, FiTrendingUp } from 'react-icons/fi';
import { api } from '../../services/api';

export default function AdminPredictionsPage() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const loadData = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      setData(await api.getPredictiveInsights());
    } catch (err) {
      setError(err.message || 'Unable to load current forecasting data.');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadData();
  }, [loadData]);

  return (
    <div>
      <div className="page-header" style={{ display: 'flex', justifyContent: 'space-between', gap: '1rem', flexWrap: 'wrap' }}>
        <div>
          <h1 className="page-title">Predictive Intelligence</h1>
          <p className="page-subtitle">Municipal trend readiness calculated from actual stored records</p>
        </div>
        <button type="button" className="btn btn-outline" onClick={loadData} disabled={loading}>
          <FiRefreshCw className={loading ? 'spin' : ''} /> Refresh
        </button>
      </div>

      {error && <div className="alert alert-danger" role="alert">{error}</div>}

      {loading && !data && (
        <div className="card" role="status">Loading municipal record coverage…</div>
      )}

      {data && (
        <>
          <div className="alert alert-info" role="note">
            <strong>Exploratory only:</strong> Forecasts use an ordinary least-squares trend from recorded daily counts.
            They are not independently validated; no projections are shown until the data minimum is met.
          </div>
          <div className="grid-2">
            <section className="card">
              <div className="card-header">
                <h3 className="card-title"><FiDatabase /> Observed Data</h3>
                <p className="card-subtitle">System-wide records available in the configured storage provider</p>
              </div>
              <p><strong>Timestamped events:</strong> {data.currentEvents} / {data.requiredEvents}</p>
              <p><strong>Distinct observation days:</strong> {data.observationDays} / {data.requiredDays}</p>
              <p><strong>Data readiness:</strong> {data.readinessPct}%</p>
              <p><strong>Storage scope:</strong> {data.scope === 'system' ? 'Municipal records' : 'Authenticated account records'}</p>
              <p><strong>Generated:</strong> {data.generatedAt ? new Date(data.generatedAt).toLocaleString() : 'Unavailable'}</p>
            </section>

            <section className="card">
              <div className="card-header">
                <h3 className="card-title"><FiTrendingUp /> Forecast Readiness</h3>
              </div>
              <p>
                <strong>Status:</strong>{' '}
                {data.sufficientData
                  ? <span className="badge badge-warning">Exploratory trend available</span>
                  : <span className="badge badge-warning">Insufficient observations</span>}
              </p>
              <p>{data.message}</p>
              {data.sufficientData && (
                <p><FiCheckCircle /> Seven-day trend available; it is not a validated operational forecast.</p>
              )}
              {!data.sufficientData && (
                <p><FiAlertCircle /> More timestamped observations across distinct days are required.</p>
              )}
            </section>
          </div>
        </>
      )}
    </div>
  );
}
