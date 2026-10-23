import React, { useState, useEffect, useCallback } from 'react';
import { Link } from 'react-router-dom';
import { api } from '../../services/api';
import { formatDateTime } from '../../utils/helpers';
import {
  FiShield,
  FiCheckCircle,
  FiAlertTriangle,
  FiAlertOctagon,
  FiTrendingUp,
  FiLayers,
  FiActivity,
  FiRefreshCw,
  FiCamera,
  FiInbox,
  FiInfo
} from 'react-icons/fi';

export default function SanitationPage() {
  const [intel, setIntel] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [isRestricted, setIsRestricted] = useState(false);

  const loadData = useCallback(async () => {
    setLoading(true);
    setError('');
    setIsRestricted(false);
    try {
      const data = await api.getSanitation();
      setIntel(data);
    } catch (err) {
      if (err.status === 403 || err.message?.toLowerCase().includes('administrator') || err.message?.toLowerCase().includes('forbidden')) {
        setIsRestricted(true);
      } else {
        setError(err.message || 'Failed to retrieve sanitation intelligence assessment.');
      }
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const getStatusBadge = (status) => {
    switch (status?.toUpperCase()) {
      case 'GOOD':
        return (
          <span className="badge badge-success" style={{ fontSize: '1rem', padding: '0.4rem 0.8rem' }}>
            <FiCheckCircle style={{ marginRight: '6px' }} /> GOOD
          </span>
        );
      case 'ATTENTION REQUIRED':
        return (
          <span className="badge badge-warning" style={{ fontSize: '1rem', padding: '0.4rem 0.8rem' }}>
            <FiAlertTriangle style={{ marginRight: '6px' }} /> ATTENTION REQUIRED
          </span>
        );
      case 'CRITICAL':
        return (
          <span className="badge badge-danger" style={{ fontSize: '1rem', padding: '0.4rem 0.8rem' }}>
            <FiAlertOctagon style={{ marginRight: '6px' }} /> CRITICAL
          </span>
        );
      default:
        return (
          <span className="badge badge-info" style={{ fontSize: '1rem', padding: '0.4rem 0.8rem' }}>
            <FiInfo style={{ marginRight: '6px' }} /> {status || 'UNAVAILABLE'}
          </span>
        );
    }
  };

  const isUnavailable = !intel || intel.currentStatus === 'UNAVAILABLE' || (intel.supportingIndicators?.length === 0);

  return (
    <div>
      <div className="page-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem' }}>
        <div>
          <h1 className="page-title">Software Sanitation Posture & Stream Health</h1>
          <p className="page-subtitle">
            Rule-based evaluation of waste stream balance, intake throughput, and classification certainty
          </p>
        </div>
        <div style={{ display: 'flex', gap: '0.75rem' }}>
          <button
            type="button"
            className="btn btn-outline"
            onClick={loadData}
            disabled={loading}
            style={{ display: 'inline-flex', alignItems: 'center', gap: '6px' }}
          >
            <FiRefreshCw className={loading ? 'spin' : ''} /> Refresh
          </button>
          <Link to="/detect" className="btn btn-primary" style={{ display: 'inline-flex', alignItems: 'center', gap: '8px' }}>
            <FiCamera /> Record Inflow
          </Link>
        </div>
      </div>

      {/* Zero Hardware Public Service Declaration */}
      <div className="alert alert-info" style={{ marginBottom: '1.25rem', fontSize: '0.85rem' }}>
        <strong>Zero-Hardware Operational Posture:</strong> Sanitation scores are calculated solely through software-derived
        heuristics (event intake volume, stream imbalance ratio, and model confidence thresholds).
        No physical IoT bin sensors, optical fullness monitors, or municipal telemetry devices are deployed.
      </div>

      {/* Restricted Access Console Banner */}
      {isRestricted && (
        <div className="card" style={{ textAlign: 'center', padding: '3.5rem 1.5rem', marginBottom: '1.5rem' }}>
          <div style={{ fontSize: '3rem', marginBottom: '1rem' }}>🛡️</div>
          <h2 style={{ fontSize: '1.4rem', color: '#111827', marginBottom: '0.5rem' }}>
            Restricted Operational Console
          </h2>
          <p style={{ maxWidth: '600px', margin: '0 auto 1.5rem', color: '#4b5563', lineHeight: 1.6 }}>
            Sanitation Intelligence is an administrative supervisory console reserved for verified municipal officials and system operators. Citizen accounts are restricted from accessing system-wide disposal telemetry in accordance with municipal data governance policies.
          </p>
          <div style={{ display: 'flex', gap: '10px', justifyContent: 'center', flexWrap: 'wrap' }}>
            <Link to="/login" className="btn btn-primary" style={{ display: 'inline-flex', alignItems: 'center', gap: '8px' }}>
              Sign In with Administrator Privileges
            </Link>
            <Link to="/dashboard" className="btn btn-outline">
              Return to Citizen Dashboard
            </Link>
            <Link to="/detect" className="btn btn-outline" style={{ display: 'inline-flex', alignItems: 'center', gap: '6px' }}>
              <FiCamera /> Record Waste Inflow
            </Link>
          </div>
        </div>
      )}

      {/* Error Alert */}
      {!isRestricted && error && (
        <div className="alert alert-danger" style={{ marginBottom: '1.25rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div>
            <strong>Service Communication Error:</strong> {error}
          </div>
          <button type="button" className="btn btn-outline" onClick={loadData} style={{ fontSize: '0.8rem', padding: '0.3rem 0.6rem' }}>
            Retry
          </button>
        </div>
      )}

      {/* Loading Skeleton */}
      {loading && !intel && (
        <div className="card" style={{ textAlign: 'center', padding: '3.5rem 1rem' }}>
          <div className="spinner" style={{ width: '32px', height: '32px', margin: '0 auto 1rem auto' }}></div>
          <h3>Evaluating Sanitation Heuristics</h3>
          <p style={{ color: '#6b7280' }}>Analyzing stream balance and confidence logs from storage repository...</p>
        </div>
      )}

      {/* Empty / Awaiting Telemetry State */}
      {!loading && intel && isUnavailable && (
        <div className="card" style={{ textAlign: 'center', padding: '4rem 1.5rem', marginBottom: '1.5rem' }}>
          <FiInbox style={{ fontSize: '3.5rem', color: '#9ca3af', marginBottom: '1rem' }} />
          <h2 style={{ fontSize: '1.4rem', color: '#111827', marginBottom: '0.5rem' }}>
            Sanitation Telemetry Unavailable
          </h2>
          <p style={{ maxWidth: '580px', margin: '0 auto 1.5rem', color: '#4b5563', lineHeight: 1.6 }}>
            {intel.reason || 'No classification events have been logged in the active storage repository. In accordance with public integrity guidelines, sanitation status is not fabricated.'}
          </p>
          <Link to="/detect" className="btn btn-primary" style={{ display: 'inline-flex', alignItems: 'center', gap: '8px' }}>
            <FiCamera /> Classify Items to Initiate Monitoring
          </Link>
        </div>
      )}

      {/* Active Sanitation Intelligence Display */}
      {intel && !isUnavailable && (
        <>
          {/* Assessment Banner */}
          <div
            className="card"
            style={{
              borderLeft: `4px solid ${
                intel.currentStatus === 'GOOD' ? '#10b981' :
                intel.currentStatus === 'ATTENTION REQUIRED' ? '#f59e0b' : '#0284c7'
              }`,
              marginBottom: '1.5rem'
            }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem' }}>
              <div>
                <div style={{ fontSize: '0.85rem', color: '#6b7280', textTransform: 'uppercase', fontWeight: 600 }}>
                  Algorithmic Stream Health
                </div>
                <h2 style={{ margin: '6px 0', fontSize: '1.6rem', color: '#111827' }}>
                  Overall Posture: {intel.currentStatus}
                </h2>
                <p style={{ margin: 0, color: '#4b5563', maxWidth: '650px' }}>
                  {intel.reason}
                </p>
              </div>
              <div>
                {getStatusBadge(intel.currentStatus)}
              </div>
            </div>

            <div style={{ marginTop: '1rem', fontSize: '0.8rem', color: '#9ca3af' }}>
              Last evaluated: {formatDateTime(intel.lastUpdated)} • Algorithmic rule-based evaluation engine
            </div>
          </div>

          {/* Indicators & Location Signals */}
          <div className="grid-2">
            <div className="card">
              <div className="card-header">
                <h3 className="card-title">Supporting Software Indicators</h3>
                <p className="card-subtitle">Algorithmic metrics driving current evaluation</p>
              </div>
              <div className="detail-list">
                {intel.supportingIndicators?.map((ind, idx) => (
                  <div
                    key={idx}
                    style={{
                      display: 'flex',
                      justifyContent: 'space-between',
                      alignItems: 'center',
                      padding: '0.75rem 0',
                      borderBottom: idx < intel.supportingIndicators.length - 1 ? '1px solid #f3f4f6' : 'none'
                    }}
                  >
                    <div>
                      <div style={{ fontWeight: 600, color: '#1f2937' }}>{ind.indicator}</div>
                      <div style={{ fontSize: '0.8rem', color: '#6b7280' }}>Threshold: {ind.threshold}</div>
                    </div>
                    <div style={{ textAlign: 'right' }}>
                      <div style={{ fontWeight: 700, color: '#111827' }}>{ind.value}</div>
                      <span
                        className={`badge ${
                          ind.status === 'NORMAL' || ind.status === 'GOOD' ? 'badge-success' : 'badge-warning'
                        }`}
                        style={{ fontSize: '0.75rem' }}
                      >
                        {ind.status}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Departmental Stream Tracking */}
            <div className="card">
              <div className="card-header">
                <h3 className="card-title">Departmental Stream Monitoring</h3>
                <p className="card-subtitle">Facility stream allocation based on classification metadata</p>
              </div>
              <div className="detail-list">
                {intel.locationSignals?.map((loc, idx) => (
                  <div
                    key={idx}
                    style={{
                      display: 'flex',
                      justifyContent: 'space-between',
                      alignItems: 'center',
                      padding: '0.75rem 0',
                      borderBottom: idx < intel.locationSignals.length - 1 ? '1px solid #f3f4f6' : 'none'
                    }}
                  >
                    <div>
                      <div style={{ fontWeight: 600, color: '#1f2937' }}>{loc.department}</div>
                      <div style={{ fontSize: '0.8rem', color: '#6b7280' }}>
                        Activity: {loc.activityLevel} • Dominant: {loc.dominantCategory}
                      </div>
                    </div>
                    <div>
                      <span
                        className={`badge ${
                          loc.status === 'OPTIMAL' || loc.status === 'NORMAL' ? 'badge-success' : 'badge-warning'
                        }`}
                      >
                        {loc.status}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Actionable Recommendations */}
          <div className="card" style={{ marginTop: '1.5rem' }}>
            <div className="card-header">
              <h3 className="card-title">Actionable Directives & Recommendations</h3>
              <p className="card-subtitle">Operational actions suggested by stream balance algorithms</p>
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
              {intel.recommendations?.map((rec, idx) => (
                <div
                  key={idx}
                  style={{
                    display: 'flex',
                    alignItems: 'flex-start',
                    gap: '12px',
                    padding: '0.75rem',
                    backgroundColor: '#f9fafb',
                    borderRadius: '6px',
                    border: '1px solid #e5e7eb'
                  }}
                >
                  <FiCheckCircle style={{ color: '#10b981', marginTop: '3px', flexShrink: 0 }} />
                  <span style={{ fontSize: '0.9rem', color: '#374151' }}>{rec}</span>
                </div>
              ))}
            </div>
          </div>
        </>
      )}
    </div>
  );
}
