import React, { useState, useEffect, useCallback } from 'react';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend
} from 'chart.js';
import { Bar, Line } from 'react-chartjs-2';
import { api } from '../../services/api';
import { FiRefreshCw, FiInbox, FiShield, FiDatabase, FiActivity, FiAlertCircle } from 'react-icons/fi';

ChartJS.register(
  CategoryScale,
  LinearScale,
  BarElement,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend
);

export default function AdminAnalyticsPage() {
  const [timePeriod, setTimePeriod] = useState('all');
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');
  const [analytics, setAnalytics] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const loadData = useCallback(async (periodOverride, sDate, eDate) => {
    const activePeriod = periodOverride !== undefined ? periodOverride : timePeriod;
    const activeStart = sDate !== undefined ? sDate : startDate;
    const activeEnd = eDate !== undefined ? eDate : endDate;

    setLoading(true);
    setError('');
    try {
      const data = await api.getAnalytics({
        period: activePeriod,
        startDate: activeStart,
        endDate: activeEnd
      });
      setAnalytics(data);
    } catch (err) {
      setError(err.message || 'Failed to retrieve administrative analytics telemetry.');
    } finally {
      setLoading(false);
    }
  }, [timePeriod, startDate, endDate]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const handlePeriodChange = (newPeriod) => {
    setTimePeriod(newPeriod);
    loadData(newPeriod, startDate, endDate);
  };

  const handleCustomDateApply = (e) => {
    e.preventDefault();
    if (startDate && endDate) {
      loadData('custom', startDate, endDate);
    }
  };

  const trendLabels = analytics?.volumeTrends?.map((d) => d.date?.split('-').slice(1).join('/') || d.date) || [];
  const trendCounts = analytics?.volumeTrends?.map((d) => d.count) || [];
  const trendObjects = analytics?.volumeTrends?.map((d) => d.objects || d.count) || [];

  const throughputData = {
    labels: trendLabels.length ? trendLabels : ['Today'],
    datasets: [
      {
        label: 'Upload Sessions',
        data: trendCounts.length ? trendCounts : [analytics?.todayActivity || 0],
        backgroundColor: '#0284c7',
        borderRadius: 4
      },
      {
        label: 'Discrete Objects Localized',
        data: trendObjects.length ? trendObjects : [analytics?.todayActivity || 0],
        backgroundColor: '#10b981',
        borderRadius: 4
      }
    ]
  };

  const avgConfidence = analytics?.averageConfidence || 0;
  const accuracyTrend = {
    labels: trendLabels.length ? trendLabels : ['Current Session'],
    datasets: [
      {
        label: 'Average Neural Confidence (%)',
        data: trendLabels.length ? trendLabels.map(() => avgConfidence) : [avgConfidence],
        borderColor: '#10b981',
        backgroundColor: 'rgba(16, 185, 129, 0.1)',
        tension: 0.25,
        fill: true
      }
    ]
  };

  const comp = analytics?.comparison;

  return (
    <div>
      <div className="page-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem' }}>
        <div>
          <h1 className="page-title">Administrative Analytics & Capacity Metrics</h1>
          <p className="page-subtitle">
            System intake load monitoring, storage registry health, and neural confidence tracking
          </p>
        </div>
        <button
          type="button"
          className="btn btn-outline"
          onClick={() => loadData()}
          disabled={loading}
          style={{ display: 'inline-flex', alignItems: 'center', gap: '6px' }}
        >
          <FiRefreshCw className={loading ? 'spin' : ''} /> Refresh
        </button>
      </div>

      {/* Time-Based Filter Bar */}
      <div className="filter-bar">
        <span style={{ fontSize: '13px', fontWeight: 600, color: '#475569' }}>Time Window:</span>
        {[
          { key: 'all', label: 'All Time' },
          { key: 'hourly', label: '24 Hours' },
          { key: 'daily', label: '7 Days' },
          { key: 'weekly', label: '4 Weeks' },
          { key: 'monthly', label: '90 Days' },
          { key: 'yearly', label: '1 Year' },
          { key: 'custom', label: 'Custom' }
        ].map((item) => (
          <button
            key={item.key}
            type="button"
            className={`filter-btn ${timePeriod === item.key ? 'active' : ''}`}
            onClick={() => handlePeriodChange(item.key)}
          >
            {item.label}
          </button>
        ))}

        {timePeriod === 'custom' && (
          <form onSubmit={handleCustomDateApply} style={{ display: 'inline-flex', alignItems: 'center', gap: '6px', marginLeft: 'auto' }}>
            <input
              type="date"
              value={startDate}
              onChange={(e) => setStartDate(e.target.value)}
              required
            />
            <span>to</span>
            <input
              type="date"
              value={endDate}
              onChange={(e) => setEndDate(e.target.value)}
              required
            />
            <button type="submit" className="btn btn-primary btn-sm">Apply</button>
          </form>
        )}

        <div style={{ fontSize: '12px', color: '#6b7280', display: 'flex', alignItems: 'center', gap: '6px', marginLeft: timePeriod === 'custom' ? '0' : 'auto' }}>
          <span className="badge badge-info">{analytics?.storageProvider || 'Active Registry'}</span>
        </div>
      </div>

      <div className="alert alert-info" style={{ marginBottom: '1.25rem', fontSize: '0.85rem' }}>
        <strong>Administrative Telemetry:</strong> Metrics are gathered in real time across single-item and multi-object
        detection pipelines. Cloud/local storage status indicates whether events are written to Google Firestore or local filesystem fallback.
      </div>

      {error && <div className="alert alert-danger" style={{ marginBottom: '1.25rem' }}>{error}</div>}

      {/* Top Admin Stats Cards */}
      {analytics && (
        <div className="stats-grid" style={{ marginBottom: '1.5rem' }}>
          <div className="card">
            <div style={{ fontSize: '0.85rem', color: '#6b7280', fontWeight: 600 }}>Total Intake Sessions</div>
            <div style={{ fontSize: '1.75rem', fontWeight: 700, color: '#111827', marginTop: '4px' }}>
              {(analytics.totalUploads || analytics.totalClassifications || 0).toLocaleString()}
            </div>
            <div style={{ fontSize: '0.8rem', marginTop: '4px' }}>
              {comp && comp.pct_change_uploads !== undefined ? (
                <span className={`comparison-badge ${comp.pct_change_uploads >= 0 ? 'pos' : 'neg'}`}>
                  {comp.pct_change_uploads >= 0 ? '↑' : '↓'} {Math.abs(comp.pct_change_uploads)}% vs prev
                </span>
              ) : (
                <span style={{ color: '#10b981' }}>Intake uploads</span>
              )}
            </div>
          </div>

          <div className="card">
            <div style={{ fontSize: '0.85rem', color: '#6b7280', fontWeight: 600 }}>Total Objects Localized</div>
            <div style={{ fontSize: '1.75rem', fontWeight: 700, color: '#059669', marginTop: '4px' }}>
              {(analytics.totalObjectsDetected || analytics.totalClassifications || 0).toLocaleString()}
            </div>
            <div style={{ fontSize: '0.8rem', marginTop: '4px' }}>
              {comp && comp.pct_change_objects !== undefined ? (
                <span className={`comparison-badge ${comp.pct_change_objects >= 0 ? 'pos' : 'neg'}`}>
                  {comp.pct_change_objects >= 0 ? '↑' : '↓'} {Math.abs(comp.pct_change_objects)}% vs prev
                </span>
              ) : (
                <span style={{ color: '#6b7280' }}>Detected waste items</span>
              )}
            </div>
          </div>

          <div className="card">
            <div style={{ fontSize: '0.85rem', color: '#6b7280', fontWeight: 600 }}>Storage Backend Provider</div>
            <div style={{ fontSize: '1.35rem', fontWeight: 700, color: '#2563eb', marginTop: '6px' }}>
              {analytics.storageProvider || 'Local Storage'}
            </div>
            <div style={{ fontSize: '0.8rem', color: '#6b7280', marginTop: '2px' }}>
              {analytics.storageProvider?.includes('Firestore') ? 'Live Cloud Datastore' : 'Thread-safe local storage'}
            </div>
          </div>

          <div className="card">
            <div style={{ fontSize: '0.85rem', color: '#6b7280', fontWeight: 600 }}>System Sanitation Status</div>
            <div style={{ fontSize: '1.35rem', fontWeight: 700, color: analytics.sanitationStatus === 'GOOD' ? '#16a34a' : '#d97706', marginTop: '6px' }}>
              {analytics.sanitationStatus || 'OPERATIONAL'}
            </div>
            <div style={{ fontSize: '0.8rem', color: '#6b7280', marginTop: '2px' }}>
              {analytics.activeAnomalies || 0} active anomaly flags
            </div>
          </div>
        </div>
      )}

      {loading && !analytics ? (
        <div className="card" style={{ textAlign: 'center', padding: '3rem 1rem' }}>
          <div className="spinner" style={{ width: '28px', height: '28px', margin: '0 auto 0.75rem auto' }}></div>
          <p style={{ color: '#6b7280' }}>Loading administrative telemetry...</p>
        </div>
      ) : analytics?.totalClassifications === 0 ? (
        <div className="card" style={{ textAlign: 'center', padding: '3.5rem 1rem' }}>
          <FiInbox style={{ fontSize: '3rem', color: '#9ca3af', marginBottom: '0.75rem' }} />
          <h3>No Operational Records Logged</h3>
          <p style={{ color: '#6b7280' }}>The storage registry currently contains zero classification events.</p>
        </div>
      ) : (
        <div className="grid-2">
          <div className="card">
            <div className="card-header">
              <h3 className="card-title">Inflow Volume Throughput</h3>
              <p className="card-subtitle">Classification upload events vs discrete objects detected</p>
            </div>
            <div style={{ height: '320px', position: 'relative' }}>
              <Bar
                data={throughputData}
                options={{
                  responsive: true,
                  maintainAspectRatio: false,
                  plugins: { legend: { position: 'top' } },
                  scales: { y: { beginAtZero: true, ticks: { precision: 0 } } }
                }}
              />
            </div>
          </div>

          <div className="card">
            <div className="card-header">
              <h3 className="card-title">Production Model Confidence Trend</h3>
              <p className="card-subtitle">Tracking against reference benchmarks</p>
            </div>
            <div style={{ height: '320px', position: 'relative' }}>
              <Line
                data={accuracyTrend}
                options={{
                  responsive: true,
                  maintainAspectRatio: false,
                  plugins: { legend: { position: 'top' } },
                  scales: { y: { min: 0, max: 100 } }
                }}
              />
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
