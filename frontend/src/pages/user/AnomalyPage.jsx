import React, { useState, useEffect, useCallback } from 'react';
import { Link } from 'react-router-dom';
import { api } from '../../services/api';
import { formatDateTime } from '../../utils/helpers';
import {
  FiAlertTriangle,
  FiCheckCircle,
  FiAlertOctagon,
  FiActivity,
  FiFilter,
  FiInfo,
  FiRefreshCw,
  FiCamera,
  FiInbox,
  FiShield
} from 'react-icons/fi';

export default function AnomalyPage() {
  const [anomalyData, setAnomalyData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [isRestricted, setIsRestricted] = useState(false);
  const [severityFilter, setSeverityFilter] = useState('ALL');

  const loadData = useCallback(async () => {
    setLoading(true);
    setError('');
    setIsRestricted(false);
    try {
      const data = await api.getAnomalies();
      setAnomalyData(data);
    } catch (err) {
      if (err.status === 403 || err.message?.toLowerCase().includes('administrator') || err.message?.toLowerCase().includes('forbidden')) {
        setIsRestricted(true);
      } else {
        setError(err.message || 'Failed to retrieve statistical anomaly detection telemetry.');
      }
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const anomaliesList = anomalyData?.anomalies || [];
  const filteredAnomalies = anomaliesList.filter((a) => {
    if (severityFilter === 'ALL') return true;
    return a.severity?.toUpperCase() === severityFilter;
  });

  const getSeverityBadge = (severity) => {
    switch (severity?.toLowerCase()) {
      case 'high':
        return <span className="badge badge-danger">High Severity</span>;
      case 'medium':
        return <span className="badge badge-warning">Medium Severity</span>;
      case 'low':
        return <span className="badge badge-info">Low Severity</span>;
      default:
        return <span className="badge badge-info">{severity}</span>;
    }
  };

  const recordsSampled = anomalyData?.recordsSampled || 0;
  const isBaselineBuilding = recordsSampled < 10;

  return (
    <div>
      <div className="page-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem' }}>
        <div>
          <h1 className="page-title">Statistical Anomaly & Outlier Detection</h1>
          <p className="page-subtitle">
            Record-based checks for unusually high hazardous-stream shares and repeated low-confidence classifications
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

      {/* Algorithmic Public Service Notice */}
      <div className="alert alert-info" style={{ marginBottom: '1.25rem', fontSize: '0.85rem' }}>
        <strong>Data Integrity Disclosure:</strong> Checks use the most recent classification records and explicit thresholds.
        They do not use connected sensors, location data, or an Isolation Forest model. Alerts are only shown when the
        stored records meet a stated rule.
      </div>

      {/* Restricted Access Console Banner */}
      {isRestricted && (
        <div className="card" style={{ textAlign: 'center', padding: '3.5rem 1.5rem', marginBottom: '1.5rem' }}>
          <div style={{ fontSize: '3rem', marginBottom: '1rem' }}>🛡️</div>
          <h2 style={{ fontSize: '1.4rem', color: '#111827', marginBottom: '0.5rem' }}>
            Restricted Operational Console
          </h2>
          <p style={{ maxWidth: '600px', margin: '0 auto 1.5rem', color: '#4b5563', lineHeight: 1.6 }}>
            Anomaly Detection is an administrative supervisory console reserved for verified municipal officials and system operators. Citizen accounts are restricted from accessing system-wide outlier diagnostics in accordance with municipal data governance policies.
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
      {loading && !anomalyData && (
        <div className="card" style={{ textAlign: 'center', padding: '3.5rem 1rem' }}>
          <div className="spinner" style={{ width: '32px', height: '32px', margin: '0 auto 1rem auto' }}></div>
          <h3>Checking Recent Classification Records</h3>
          <p style={{ color: '#6b7280' }}>Applying the documented record thresholds...</p>
        </div>
      )}

      {/* Baseline Building State (< 10 records) */}
      {!loading && anomalyData && isBaselineBuilding && (
        <div className="card" style={{ textAlign: 'center', padding: '4rem 1.5rem', marginBottom: '1.5rem' }}>
          <FiActivity style={{ fontSize: '3.5rem', color: '#0284c7', marginBottom: '1rem' }} />
          <h2 style={{ fontSize: '1.4rem', color: '#111827', marginBottom: '0.5rem' }}>
            Baseline Telemetry Inflow in Progress ({recordsSampled} / 10 Events)
          </h2>
          <p style={{ maxWidth: '580px', margin: '0 auto 1.5rem', color: '#4b5563', lineHeight: 1.6 }}>
            At least 10 stored classification events are required before these threshold checks run. No connected sensor
            data or location information is available to this analysis.
          </p>
          <div style={{ display: 'inline-flex', alignItems: 'center', gap: '8px', padding: '0.6rem 1.25rem', background: '#f3f4f6', borderRadius: '6px', fontSize: '0.85rem', marginBottom: '1.5rem' }}>
            <FiShield style={{ color: '#0284c7' }} />
            <span>Method: {anomalyData.algorithm}</span>
          </div>
          <div>
            <Link to="/detect" className="btn btn-primary" style={{ display: 'inline-flex', alignItems: 'center', gap: '8px' }}>
              <FiCamera /> Record More Classifications
            </Link>
          </div>
        </div>
      )}

      {/* Active Anomaly Dashboard (>= 10 records) */}
      {anomalyData && !isBaselineBuilding && (
        <>
          {/* Summary Cards */}
          <div className="stats-grid" style={{ marginBottom: '1.5rem' }}>
            <div className="stat-card card-warning">
              <div className="stat-header">
                <span className="stat-title">Detected Outliers</span>
                <FiAlertTriangle className="stat-icon" />
              </div>
              <div className="stat-value">{anomaliesList.length}</div>
              <div className="stat-footer">
                <span className="stat-subtitle">From {recordsSampled} verified events</span>
              </div>
            </div>

            <div className="stat-card card-danger">
              <div className="stat-header">
                <span className="stat-title">High Severity Alerts</span>
                <FiAlertOctagon className="stat-icon" />
              </div>
              <div className="stat-value">
                {anomaliesList.filter((a) => a.severity?.toLowerCase() === 'high').length}
              </div>
              <div className="stat-footer">
                <span className="stat-subtitle">Requires supervisory audit</span>
              </div>
            </div>

            <div className="stat-card card-success">
              <div className="stat-header">
                <span className="stat-title">Detector Architecture</span>
                <FiActivity className="stat-icon" />
              </div>
              <div className="stat-value" style={{ fontSize: '1.2rem' }}>Record Rules</div>
              <div className="stat-footer">
                <span className="stat-subtitle">Sample: latest {Math.min(recordsSampled, 20)} events</span>
              </div>
            </div>
          </div>

          {/* Filter and List */}
          <div className="card">
            <div className="card-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem' }}>
              <div>
                <h3 className="card-title">Outlier Telemetry Log</h3>
                <p className="card-subtitle">Detailed records of detected distribution skews and confidence anomalies</p>
              </div>
              <div style={{ minWidth: '160px' }}>
                <select
                  className="form-control"
                  value={severityFilter}
                  onChange={(e) => setSeverityFilter(e.target.value)}
                >
                  <option value="ALL">All Severities</option>
                  <option value="HIGH">High Severity</option>
                  <option value="MEDIUM">Medium Severity</option>
                  <option value="LOW">Low Severity</option>
                </select>
              </div>
            </div>

            {filteredAnomalies.length === 0 ? (
              <div className="empty-state" style={{ padding: '3.5rem 1rem', textAlign: 'center' }}>
                <FiCheckCircle className="empty-icon" style={{ color: '#10b981', fontSize: '3rem', marginBottom: '0.75rem' }} />
                <h3>No Statistical Anomalies Detected</h3>
                <p style={{ maxWidth: '480px', margin: '0.5rem auto 0 auto', color: '#6b7280' }}>
                  No configured record-based anomaly threshold was reached in the {recordsSampled} analyzed events.
                </p>
              </div>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                {filteredAnomalies.map((item) => (
                  <div
                    key={item.id}
                    style={{
                      padding: '1.25rem',
                      borderRadius: '8px',
                      border: '1px solid #e5e7eb',
                      backgroundColor: '#ffffff',
                      boxShadow: '0 1px 2px rgba(0,0,0,0.03)'
                    }}
                  >
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '0.5rem', marginBottom: '0.5rem' }}>
                      <div>
                        <span style={{ fontSize: '0.8rem', color: '#6b7280', textTransform: 'uppercase', fontWeight: 600 }}>
                          Event Ref: <code>{item.id}</code> • {item.category || 'General'}
                        </span>
                        <h4 style={{ margin: '4px 0', fontSize: '1.1rem', color: '#111827' }}>
                          {item.type}
                        </h4>
                      </div>
                      <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
                        {getSeverityBadge(item.severity)}
                      </div>
                    </div>

                    <p style={{ margin: '0.5rem 0', color: '#374151', fontSize: '0.9rem', lineHeight: 1.5 }}>
                      <strong>Trigger Rationale:</strong> {item.reason}
                    </p>

                    <div style={{ backgroundColor: '#f9fafb', padding: '0.75rem', borderRadius: '6px', margin: '0.75rem 0', fontSize: '0.85rem' }}>
                      <span style={{ fontWeight: 600, color: '#1f2937' }}>Recommended Operational Action: </span>
                      <span style={{ color: '#4b5563' }}>{item.recommendation}</span>
                    </div>

                    <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.8rem', color: '#9ca3af', paddingTop: '0.5rem', borderTop: '1px solid #f3f4f6' }}>
                      <span>Location: {item.location || 'Not recorded'}</span>
                      <span>Detected: {formatDateTime(item.timestamp)}</span>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </>
      )}
    </div>
  );
}
