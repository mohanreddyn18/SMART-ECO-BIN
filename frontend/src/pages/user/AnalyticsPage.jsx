import React, { useState, useEffect, useCallback } from 'react';
import { Link } from 'react-router-dom';
import {
  Chart as ChartJS,
  ArcElement,
  Tooltip,
  Legend,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement
} from 'chart.js';
import { Doughnut, Line, Bar } from 'react-chartjs-2';
import { api } from '../../services/api';
import {
  FiTrendingUp,
  FiPieChart,
  FiBarChart2,
  FiCheckCircle,
  FiRefreshCw,
  FiInbox,
  FiCamera,
  FiInfo,
  FiShield
} from 'react-icons/fi';

ChartJS.register(
  ArcElement,
  Tooltip,
  Legend,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement
);

const ALL_12_CLASSES = [
  'plastic', 'paper', 'cardboard', 'metal', 'biological',
  'brown-glass', 'white-glass', 'green-glass', 'clothes', 'shoes', 'battery', 'trash'
];

export default function AnalyticsPage() {
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
      setError(err.message || 'Failed to retrieve analytics metrics from backend service.');
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

  // Doughnut: Category Distribution
  const categoryLabels = ['Recyclable / Dry', 'Organic / Wet', 'Hazardous / E-Waste', 'Residual Trash'];
  const categoryCounts = analytics ? [
    analytics.categoryBreakdown?.recyclable || 0,
    analytics.categoryBreakdown?.organic || 0,
    analytics.categoryBreakdown?.hazardous || 0,
    analytics.categoryBreakdown?.trash || 0
  ] : [0, 0, 0, 0];

  const doughnutData = {
    labels: categoryLabels,
    datasets: [
      {
        data: categoryCounts,
        backgroundColor: ['#2563eb', '#10b981', '#f59e0b', '#6b7280'],
        borderWidth: 2,
        borderColor: '#ffffff'
      }
    ]
  };

  // Line: Trends over telemetry window
  const trendLabels = analytics?.volumeTrends?.map((d) => d.date?.split('-').slice(1).join('/') || d.date) || [];
  const trendUploads = analytics?.volumeTrends?.map((d) => d.count ?? 0) || [];
  const trendObjects = analytics?.volumeTrends?.map((d) => d.objects ?? 0) || [];

  const trendData = {
    labels: trendLabels,
    datasets: [
      {
        label: 'Upload Sessions',
        data: trendUploads,
        borderColor: '#0284c7',
        backgroundColor: 'rgba(2, 132, 199, 0.12)',
        tension: 0.3,
        fill: true
      },
      {
        label: 'Objects Detected',
        data: trendObjects,
        borderColor: '#10b981',
        backgroundColor: 'rgba(16, 185, 129, 0.08)',
        tension: 0.3,
        fill: false,
        borderDash: [4, 4]
      }
    ]
  };

  // Bar: Specific Class Volume Breakdown (All 12 Supported Classes)
  const classBreakdown = analytics?.classBreakdown || {};
  const barData = {
    labels: ALL_12_CLASSES.map((c) => c.charAt(0).toUpperCase() + c.slice(1)),
    datasets: [
      {
        label: 'Verified Event Records',
        data: ALL_12_CLASSES.map((c) => classBreakdown[c] || 0),
        backgroundColor: '#3b82f6',
        borderRadius: 4
      }
    ]
  };

  const chartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: { position: 'top' }
    }
  };

  const comp = analytics?.comparison;

  return (
    <div>
      <div className="page-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem' }}>
        <div>
          <h1 className="page-title">Waste Analytics & Audit Metrics</h1>
          <p className="page-subtitle">
            Longitudinal telemetry of classification volume, stream distribution, and inference metrics
          </p>
        </div>
        <div style={{ display: 'flex', gap: '0.75rem' }}>
          <button
            type="button"
            className="btn btn-outline"
            onClick={() => loadData()}
            disabled={loading}
            style={{ display: 'inline-flex', alignItems: 'center', gap: '6px' }}
          >
            <FiRefreshCw className={loading ? 'spin' : ''} /> Refresh
          </button>
          <Link to="/detect" className="btn btn-primary" style={{ display: 'inline-flex', alignItems: 'center', gap: '8px' }}>
            <FiCamera /> Classify Waste
          </Link>
        </div>
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

      {/* Public Service Methodology & Provenance Notice */}
      <div className="alert alert-info" style={{ marginBottom: '1.25rem', fontSize: '0.85rem' }}>
        <strong>Data Integrity & Methodology:</strong> All statistics are derived dynamically from verified classification
        records in the active storage provider. Multiple detected objects from one image are individually registered and
        tallied to prevent undercounting. Baseline comparisons show changes versus the previous equivalent time window.
      </div>

      {/* Error State */}
      {error && (
        <div className="alert alert-danger" style={{ marginBottom: '1.25rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div>
            <strong>Service Communication Error:</strong> {error}
          </div>
          <button type="button" className="btn btn-outline" onClick={() => loadData()} style={{ fontSize: '0.8rem', padding: '0.3rem 0.6rem' }}>
            Retry
          </button>
        </div>
      )}

      {/* Loading State */}
      {loading && !analytics && (
        <div className="card" style={{ textAlign: 'center', padding: '3.5rem 1rem' }}>
          <div className="spinner" style={{ width: '32px', height: '32px', margin: '0 auto 1rem auto' }}></div>
          <h3>Computing System Analytics</h3>
          <p style={{ color: '#6b7280' }}>Aggregating telemetry logs and stream proportions across all stored records...</p>
        </div>
      )}

      {/* Empty State */}
      {!loading && analytics && analytics.totalClassifications === 0 && (
        <div className="card" style={{ textAlign: 'center', padding: '4rem 1.5rem', marginBottom: '1.5rem' }}>
          <FiInbox style={{ fontSize: '3.5rem', color: '#9ca3af', marginBottom: '1rem' }} />
          <h2 style={{ fontSize: '1.4rem', color: '#111827', marginBottom: '0.5rem' }}>
            Insufficient Telemetry for Aggregate Analytics
          </h2>
          <p style={{ maxWidth: '580px', margin: '0 auto 1.5rem', color: '#4b5563', lineHeight: 1.6 }}>
            There are currently zero classification records in the active storage repository. In accordance with government
            data integrity standards, charts and statistical summaries require at least one authenticated classification event.
          </p>
          <Link to="/detect" className="btn btn-primary" style={{ display: 'inline-flex', alignItems: 'center', gap: '8px' }}>
            <FiCamera /> Record First Classification
          </Link>
        </div>
      )}

      {/* Analytics Visualizations (Rendered when records exist) */}
      {analytics && analytics.totalClassifications > 0 && (
        <>
          {/* Top Summary Cards */}
          <div className="stats-grid" style={{ marginBottom: '1.5rem' }}>
            <div className="card">
              <div style={{ fontSize: '0.85rem', color: '#6b7280', fontWeight: 600 }}>Total Upload Sessions</div>
              <div style={{ fontSize: '1.75rem', fontWeight: 700, color: '#111827', marginTop: '4px' }}>
                {(analytics.totalUploads ?? 0).toLocaleString()}
              </div>
              <div style={{ fontSize: '0.8rem', marginTop: '4px' }}>
                {comp && comp.pct_change_uploads !== undefined ? (
                  <span className={`comparison-badge ${comp.pct_change_uploads >= 0 ? 'pos' : 'neg'}`}>
                    {comp.pct_change_uploads >= 0 ? '↑' : '↓'} {Math.abs(comp.pct_change_uploads)}% ({comp.diff_uploads >= 0 ? `+${comp.diff_uploads}` : comp.diff_uploads} vs prev)
                  </span>
                ) : (
                  <span style={{ color: '#10b981' }}>Verified intake sessions</span>
                )}
              </div>
            </div>

            <div className="card">
              <div style={{ fontSize: '0.85rem', color: '#6b7280', fontWeight: 600 }}>Total Objects Detected</div>
              <div style={{ fontSize: '1.75rem', fontWeight: 700, color: '#059669', marginTop: '4px' }}>
                {(analytics.totalObjectsDetected ?? 0).toLocaleString()}
              </div>
              <div style={{ fontSize: '0.8rem', marginTop: '4px' }}>
                {comp && comp.pct_change_objects !== undefined ? (
                  <span className={`comparison-badge ${comp.pct_change_objects >= 0 ? 'pos' : 'neg'}`}>
                    {comp.pct_change_objects >= 0 ? '↑' : '↓'} {Math.abs(comp.pct_change_objects)}% ({comp.diff_objects >= 0 ? `+${comp.diff_objects}` : comp.diff_objects} vs prev)
                  </span>
                ) : (
                  <span style={{ color: '#6b7280' }}>Discrete waste items</span>
                )}
              </div>
            </div>

            <div className="card">
              <div style={{ fontSize: '0.85rem', color: '#6b7280', fontWeight: 600 }}>Average Model Confidence</div>
              <div style={{ fontSize: '1.75rem', fontWeight: 700, color: '#2563eb', marginTop: '4px' }}>
                {(analytics.averageConfidence || 0).toFixed(1)}%
              </div>
              <div style={{ fontSize: '0.8rem', color: '#6b7280', marginTop: '4px' }}>AI inference certainty</div>
            </div>

            <div className="card">
              <div style={{ fontSize: '0.85rem', color: '#6b7280', fontWeight: 600 }}>Active Storage Mode</div>
              <div style={{ fontSize: '1.25rem', fontWeight: 700, color: '#16a34a', marginTop: '8px' }}>
                {analytics.storageProvider || 'Local Registry'}
              </div>
              <div style={{ fontSize: '0.8rem', color: '#6b7280', marginTop: '4px' }}>Emulated Development</div>
            </div>
          </div>

          {/* 2 Charts Grid */}
          <div className="grid-2">
            <div className="card">
              <div className="card-header">
                <h3 className="card-title">Waste Stream Distribution</h3>
                <p className="card-subtitle">Aggregate proportion of classified items by waste stream</p>
              </div>
              {categoryCounts.some((value) => value > 0) ? (
                <div style={{ height: '320px', position: 'relative' }}>
                  <Doughnut data={doughnutData} options={chartOptions} />
                </div>
              ) : (
                <p className="empty-state" style={{ padding: '2rem 1rem', textAlign: 'center' }}>
                  Category breakdown is unavailable for these records.
                </p>
              )}
            </div>

            <div className="card">
              <div className="card-header">
                <h3 className="card-title">Telemetry Inflow Trend</h3>
                <p className="card-subtitle">Classification frequency and localized object count</p>
              </div>
              {trendLabels.length > 0 ? (
                <div style={{ height: '320px', position: 'relative' }}>
                  <Line data={trendData} options={chartOptions} />
                </div>
              ) : (
                <p className="empty-state" style={{ padding: '2rem 1rem', textAlign: 'center' }}>
                  Insufficient dated history to display an inflow trend.
                </p>
              )}
            </div>
          </div>

          {/* Bar Chart: Detailed 12-Class Breakdown */}
          <div className="card" style={{ marginTop: '1.5rem' }}>
            <div className="card-header">
              <h3 className="card-title">12-Class Distribution Breakdown</h3>
              <p className="card-subtitle">
                Exact count of items classified into each of the 12 trained MobileNetV2 classes
              </p>
            </div>
            <div style={{ height: '320px', position: 'relative' }}>
              <Bar
                data={barData}
                options={{
                  ...chartOptions,
                  scales: {
                    y: { beginAtZero: true, ticks: { precision: 0 } },
                    x: { ticks: { autoSkip: false, maxRotation: 45, minRotation: 45 } }
                  }
                }}
              />
            </div>
          </div>

          {/* Data Quality & Governance Overview */}
          <div className="card" style={{ marginTop: '1.5rem' }}>
            <div className="card-header">
              <h3 className="card-title">Data Provenance & Record Handling</h3>
              <p className="card-subtitle">Transparent public disclosure regarding data storage and handling</p>
            </div>
            <div className="grid-3" style={{ fontSize: '0.9rem', lineHeight: 1.6 }}>
              <div style={{ padding: '0.75rem', background: '#f9fafb', borderRadius: '6px' }}>
                <strong>Storage Architecture:</strong>
                <p style={{ margin: '4px 0 0', color: '#4b5563', fontSize: '0.85rem' }}>
                  Operates under a cloud-ready storage abstraction (`BaseStorageProvider`). Development emulation uses a thread-safe local JSON provider with idempotency protection.
                </p>
              </div>
              <div style={{ padding: '0.75rem', background: '#f9fafb', borderRadius: '6px' }}>
                <strong>Incomplete Records:</strong>
                <p style={{ margin: '4px 0 0', color: '#4b5563', fontSize: '0.85rem' }}>
                  Requests lacking valid image binaries or failing neural confidence thresholds (&lt; 60%) are flagged for manual review and not fabricated into automated segregation totals.
                </p>
              </div>
              <div style={{ padding: '0.75rem', background: '#f9fafb', borderRadius: '6px' }}>
                <strong>Environmental Claims:</strong>
                <p style={{ margin: '4px 0 0', color: '#4b5563', fontSize: '0.85rem' }}>
                  To avoid greenwashing, environmental savings metrics are omitted until physical waste weights and local landfill diversion factors are verified by accredited authorities.
                </p>
              </div>
            </div>
          </div>
        </>
      )}
    </div>
  );
}
