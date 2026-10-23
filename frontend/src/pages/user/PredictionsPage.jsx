import React, { useState, useEffect, useCallback } from 'react';
import { Link } from 'react-router-dom';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Tooltip,
  Legend
} from 'chart.js';
import { Line } from 'react-chartjs-2';
import { api } from '../../services/api';
import {
  FiTrendingUp,
  FiAlertCircle,
  FiInfo,
  FiCheckCircle,
  FiRefreshCw,
  FiCamera,
  FiShield
} from 'react-icons/fi';

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Tooltip,
  Legend
);

export default function PredictionsPage() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [isRestricted, setIsRestricted] = useState(false);

  const loadData = useCallback(async () => {
    setLoading(true);
    setError('');
    setIsRestricted(false);
    try {
      const result = await api.getPredictiveInsights();
      setData(result);
    } catch (err) {
      if (err.status === 403 || err.message?.toLowerCase().includes('administrator') || err.message?.toLowerCase().includes('forbidden')) {
        setIsRestricted(true);
      } else {
        setError(err.message || 'Failed to retrieve predictive insights telemetry.');
      }
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const sufficientData = data?.sufficientData || false;
  const currentEvents = data?.currentEvents || 0;
  const requiredEvents = data?.requiredEvents || 100;
  const observationDays = data?.observationDays || 0;
  const requiredDays = data?.requiredDays || 30;
  const readinessPct = data?.readinessPct || 0;
  const isSystemForecast = data?.scope === 'system';

  const forecastData = {
    labels: data?.forecast?.map((f) => f.label) || ['Day +1', 'Day +2', 'Day +3', 'Day +4', 'Day +5', 'Day +6', 'Day +7'],
    datasets: [
      {
        label: 'Exploratory Linear Trend',
        data: data?.forecast?.map((f) => f.value) || [],
        borderColor: '#0284c7',
        backgroundColor: 'rgba(2, 132, 199, 0.1)',
        tension: 0.3,
        fill: false
      }
    ]
  };

  return (
    <div>
      <div className="page-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem' }}>
        <div>
          <h1 className="page-title">Statistical Predictive Inflow Forecasting</h1>
          <p className="page-subtitle">
            Exploratory seven-day intake trends calculated from records you are authorized to view
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

      {/* Scientific Validation & Data Integrity Banner */}
      <div className="alert alert-info" style={{ marginBottom: '1.25rem', fontSize: '0.85rem' }}>
        <strong>Data Integrity Standard:</strong> The chart uses an ordinary least-squares trend over actual daily records
        after at least {requiredEvents} timestamped events across {requiredDays} distinct days. This exploratory trend is
        not independently validated and is not a substitute for a verified municipal forecast.
      </div>

      {/* Restricted Access Console Banner */}
      {isRestricted && (
        <div className="card" style={{ textAlign: 'center', padding: '3.5rem 1.5rem', marginBottom: '1.5rem' }}>
          <div style={{ fontSize: '3rem', marginBottom: '1rem' }}>🛡️</div>
          <h2 style={{ fontSize: '1.4rem', color: '#111827', marginBottom: '0.5rem' }}>
            Restricted Operational Console
          </h2>
          <p style={{ maxWidth: '600px', margin: '0 auto 1.5rem', color: '#4b5563', lineHeight: 1.6 }}>
            This forecast is unavailable to the current account. Sign in with an account authorized to view these records.
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
      {loading && !data && (
        <div className="card" style={{ textAlign: 'center', padding: '3.5rem 1rem' }}>
          <div className="spinner" style={{ width: '32px', height: '32px', margin: '0 auto 1rem auto' }}></div>
          <h3>Auditing Telemetry Baseline</h3>
          <p style={{ color: '#6b7280' }}>Verifying time-series statistical readiness and historical event counts...</p>
        </div>
      )}

      {/* Threshold Status Card */}
      {data && (
        <div className="card" style={{ marginBottom: '1.5rem' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem' }}>
            <div>
              <h3 className="card-title">Telemetry Baseline Sufficiency Audit</h3>
              <p className="card-subtitle">Actual-record coverage required before an exploratory trend is calculated</p>
            </div>
            <div>
              <span className={`badge ${sufficientData ? 'badge-success' : 'badge-warning'}`} style={{ fontSize: '0.9rem', padding: '0.35rem 0.75rem' }}>
                {sufficientData ? 'Minimum data reached (exploratory)' : `Insufficient data (${readinessPct}%)`}
              </span>
            </div>
          </div>

          <div style={{ marginTop: '1.25rem', display: 'flex', gap: '2.5rem', flexWrap: 'wrap' }}>
            <div>
              <span style={{ fontSize: '0.8rem', color: '#6b7280', display: 'block' }}>Timestamped Events</span>
              <strong style={{ fontSize: '1.2rem', color: '#111827' }}>
                {currentEvents} / {requiredEvents} required
              </strong>
            </div>
            <div>
              <span style={{ fontSize: '0.8rem', color: '#6b7280', display: 'block' }}>Observed Days</span>
              <strong style={{ fontSize: '1.2rem', color: sufficientData ? '#10b981' : '#f59e0b' }}>
                {observationDays} / {requiredDays}
              </strong>
            </div>
            <div>
              <span style={{ fontSize: '0.8rem', color: '#6b7280', display: 'block' }}>Model Specification</span>
              <strong style={{ fontSize: '1rem', color: '#4b5563' }}>
                Exploratory linear trend
              </strong>
            </div>
          </div>
        </div>
      )}

      {/* Insufficient Data State */}
      {data && !sufficientData && (
        <div className="card" style={{ textAlign: 'center', padding: '4rem 1.5rem', marginBottom: '1.5rem' }}>
          <FiAlertCircle style={{ fontSize: '3.5rem', color: '#f59e0b', marginBottom: '1rem' }} />
          <h2 style={{ fontSize: '1.4rem', color: '#111827', marginBottom: '0.5rem' }}>
            Insufficient historical data for reliable prediction.
          </h2>
          <p style={{ maxWidth: '600px', margin: '0 auto 1.5rem', color: '#4b5563', lineHeight: 1.6 }}>
            In accordance with sound public-service data science principles, time-series forecasting requires a baseline of
            at least {requiredEvents} timestamped events across {requiredDays} distinct days in the records available to this
            {isSystemForecast ? ' administrator' : ' account'}. The minimum is a data-volume gate, not a validation of forecasting accuracy.
          </p>
          <div style={{ display: 'inline-flex', alignItems: 'center', gap: '8px', padding: '0.6rem 1.25rem', background: '#f3f4f6', borderRadius: '6px', fontSize: '0.85rem', marginBottom: '1.5rem' }}>
            <FiInfo style={{ color: '#0284c7' }} />
            <span>Currently available: {currentEvents} timestamped events across {observationDays} days</span>
          </div>
          <div>
            <Link to="/detect" className="btn btn-primary" style={{ display: 'inline-flex', alignItems: 'center', gap: '8px' }}>
              <FiCamera /> Record Classification Events
            </Link>
          </div>
        </div>
      )}

      {/* Exploratory trend based on actual authorized records */}
      {data && sufficientData && (
        <div>
          <div className="card">
            <div className="card-header">
              <h3 className="card-title">{isSystemForecast ? 'Municipal' : 'Personal'} 7-Day Intake Trend</h3>
              <p className="card-subtitle">Exploratory ordinary least-squares trend from actual daily event counts</p>
            </div>
            <div style={{ height: '320px', position: 'relative' }}>
              <Line
                data={forecastData}
                options={{
                  responsive: true,
                  maintainAspectRatio: false,
                  plugins: { legend: { position: 'top' } },
                  scales: {
                    x: { title: { display: true, text: 'Forecast date (UTC)' } },
                    y: { beginAtZero: true, title: { display: true, text: 'Records per day' } }
                  }
                }}
              />
            </div>
            <p className="card-subtitle" style={{ marginTop: '1rem' }}>
              {data.projections?.validation} Generated {data.generatedAt ? new Date(data.generatedAt).toLocaleString() : 'time unavailable'}.
              {' '}Scope: {isSystemForecast ? 'system-wide administrator records' : 'your records only'}.
            </p>
          </div>
        </div>
      )}
    </div>
  );
}
