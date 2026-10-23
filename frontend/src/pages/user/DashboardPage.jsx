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
import { Doughnut, Line } from 'react-chartjs-2';
import StatCard from '../../components/common/StatCard';
import { api } from '../../services/api';
import { formatDateTime, getConfidenceBadgeClass } from '../../utils/helpers';
import {
  FiCamera,
  FiActivity,
  FiTrendingUp,
  FiCheckCircle,
  FiAlertTriangle,
  FiTrash2,
  FiClock,
  FiArrowRight,
  FiRefreshCw,
  FiInfo,
  FiInbox
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

export default function DashboardPage() {
  const [timePeriod, setTimePeriod] = useState('all');
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');
  const [analytics, setAnalytics] = useState(null);
  const [storageStatus, setStorageStatus] = useState(null);
  const [recentRecords, setRecentRecords] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const loadData = useCallback(async (periodOverride, sDate, eDate) => {
    const activePeriod = periodOverride !== undefined ? periodOverride : timePeriod;
    const activeStart = sDate !== undefined ? sDate : startDate;
    const activeEnd = eDate !== undefined ? eDate : endDate;

    setLoading(true);
    setError('');
    try {
      const [analyticsData, historyData, storageData] = await Promise.all([
        api.getAnalytics({
          period: activePeriod,
          startDate: activeStart,
          endDate: activeEnd
        }),
        api.getHistory({ limit: 8 }),
        api.getStorageStatus()
      ]);
      setAnalytics(analyticsData);
      setRecentRecords(Array.isArray(historyData) ? historyData : (historyData?.records || []));
      setStorageStatus(storageData);
    } catch (err) {
      setError(err.message || 'Failed to retrieve telemetry and classification records.');
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

  // Chart configuration for Category Distribution
  const categoryLabels = ['Recyclable / Dry', 'Organic / Wet', 'Hazardous / E-Waste', 'Residual / Review'];
  const categoryValues = analytics ? [
    analytics.categoryBreakdown?.recyclable || 0,
    analytics.categoryBreakdown?.organic || 0,
    analytics.categoryBreakdown?.hazardous || 0,
    analytics.categoryBreakdown?.trash || 0
  ] : [0, 0, 0, 0];

  const doughnutData = {
    labels: categoryLabels,
    datasets: [
      {
        data: categoryValues,
        backgroundColor: ['#2563eb', '#10b981', '#f59e0b', '#6b7280'],
        borderWidth: 2,
        borderColor: '#ffffff'
      }
    ]
  };

  const doughnutOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'bottom',
        labels: { boxWidth: 14, padding: 14, font: { size: 12 } }
      }
    },
    cutout: '65%'
  };

  // Chart configuration for Intake Trends
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
        label: 'Total Objects Localized',
        data: trendObjects,
        borderColor: '#10b981',
        backgroundColor: 'rgba(16, 185, 129, 0.08)',
        tension: 0.3,
        fill: false,
        borderDash: [4, 4]
      }
    ]
  };

  const trendOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: { position: 'top', labels: { boxWidth: 14, font: { size: 12 } } }
    },
    scales: {
      y: { beginAtZero: true, ticks: { precision: 0 } },
      x: { grid: { display: false } }
    }
  };

  return (
    <div>
      {/* Page Header */}
      <div className="page-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem' }}>
        <div>
          <h1 className="page-title">Operations & Sanitation Telemetry</h1>
          <p className="page-subtitle">
            Verified waste classification telemetry, multi-object intake tracking & software segregation analytics
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

      {/* Time-Based Filter Bar (Requirement 4) */}
      <div className="filter-bar">
        <div className="filter-group">
          <span style={{ fontSize: '13px', fontWeight: 600, color: '#4b5563', marginRight: '4px' }}>Time Period:</span>
          {['all', 'hourly', 'daily', 'weekly', 'monthly', 'yearly', 'custom'].map((p) => (
            <button
              key={p}
              type="button"
              className={`filter-btn ${timePeriod === p ? 'active' : ''}`}
              onClick={() => handlePeriodChange(p)}
            >
              {p === 'all' ? 'All Time' :
               p === 'hourly' ? 'Hourly (24h)' :
               p === 'daily' ? 'Daily (7d)' :
               p === 'weekly' ? 'Weekly (4w)' :
               p === 'monthly' ? 'Monthly (3m)' :
               p === 'yearly' ? 'Yearly (1y)' : 'Custom Range'}
            </button>
          ))}
        </div>

        {timePeriod === 'custom' && (
          <form onSubmit={handleCustomDateApply} className="date-range-inputs">
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

        <div style={{ fontSize: '12px', color: '#6b7280', display: 'flex', alignItems: 'center', gap: '6px' }}>
          <span className="badge badge-info">
            {storageStatus?.cloud_provider || analytics?.storageProvider || 'Active Registry'}
          </span>
          {storageStatus && (
            <span className={`badge ${storageStatus.persistent_cloud_enabled ? 'badge-success' : 'badge-warning'}`}>
              {storageStatus.persistent_cloud_enabled ? 'Cloud record storage enabled' : 'Cloud record storage not configured'}
            </span>
          )}
        </div>
      </div>

      {/* Public Data Transparency Notice */}
      <div className="alert alert-info" style={{ marginBottom: '1.25rem', fontSize: '0.85rem' }}>
        <strong>Data Provenance Notice:</strong> Statistics displayed are calculated dynamically from verified
        records in the active storage provider. Software segregation is simulated in digital logic; no physical actuators or
        live municipal IoT hardware are claimed.
      </div>

      {/* Error State */}
      {error && (
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
      {loading && !analytics && (
        <div className="card" style={{ textAlign: 'center', padding: '3.5rem 1rem' }}>
          <div className="spinner" style={{ width: '32px', height: '32px', margin: '0 auto 1rem auto' }}></div>
          <h3>Retrieving Telemetry Records</h3>
          <p style={{ color: '#6b7280' }}>Connecting to local storage abstraction and computing derived statistics...</p>
        </div>
      )}

      {/* First-Use Empty State */}
      {!loading && analytics && analytics.totalClassifications === 0 && (
        <div className="card" style={{ textAlign: 'center', padding: '4rem 1.5rem', marginBottom: '1.5rem' }}>
          <FiInbox style={{ fontSize: '3.5rem', color: '#9ca3af', marginBottom: '1rem' }} />
          <h2 style={{ fontSize: '1.4rem', color: '#111827', marginBottom: '0.5rem' }}>
            No Classification Records in Storage Registry
          </h2>
          <p style={{ maxWidth: '580px', margin: '0 auto 1.5rem', color: '#4b5563', lineHeight: 1.6 }}>
            The storage registry is currently empty in local development emulation mode. In accordance with public data
            integrity principles, no fabricated metrics or estimated volumes are presented. Upload or capture your
            first waste image to initiate verifiable telemetry.
          </p>
          <div style={{ display: 'inline-flex', gap: '1rem', flexWrap: 'wrap', justifyContent: 'center' }}>
            <Link to="/detect" className="btn btn-primary" style={{ display: 'inline-flex', alignItems: 'center', gap: '8px' }}>
              <FiCamera /> Classify First Waste Item
            </Link>
            <button type="button" className="btn btn-outline" onClick={loadData}>
              Check for Inflow Updates
            </button>
          </div>
        </div>
      )}

      {/* Operational Stats Grid (Always visible when analytics loaded, showing true zeros or actual counts) */}
      {analytics && (
        <>
          <div className="stats-grid">
            <StatCard
              title="Total Classifications"
              value={analytics.totalClassifications.toLocaleString()}
              subtitle="Verified event records"
              icon={<FiActivity />}
              color="primary"
            />
            <StatCard
              title="Recyclable / Dry Waste"
              value={(analytics.categoryBreakdown?.recyclable || 0).toLocaleString()}
              subtitle="Paper, Plastic, Metal, Glass"
              icon={<FiCheckCircle />}
              color="info"
            />
            <StatCard
              title="Organic / Wet Waste"
              value={(analytics.categoryBreakdown?.organic || 0).toLocaleString()}
              subtitle="Food & biological matter"
              icon={<FiTrash2 />}
              color="success"
            />
            <StatCard
              title="Hazardous & Other"
              value={((analytics.categoryBreakdown?.hazardous || 0) + (analytics.categoryBreakdown?.trash || 0) + (analytics.categoryBreakdown?.other || 0)).toLocaleString()}
              subtitle="Batteries, E-Waste, Residual"
              icon={<FiAlertTriangle />}
              color="warning"
            />
            <StatCard
              title="Today's Intake"
              value={analytics.todayActivity || 0}
              subtitle="Events processed today"
              icon={<FiClock />}
              color="primary"
            />
            <StatCard
              title="Average Confidence"
              value={`${(analytics.averageConfidence || 0).toFixed(1)}%`}
              subtitle="MobileNetV2 neural certainty"
              icon={<FiTrendingUp />}
              color="success"
            />
            <StatCard
              title="Sanitation Status"
              value={analytics.sanitationStatus || 'UNAVAILABLE'}
              subtitle="Derived from stream skew"
              icon={<FiCheckCircle />}
              color={analytics.sanitationStatus === 'GOOD' ? 'success' : analytics.sanitationStatus === 'ATTENTION REQUIRED' ? 'warning' : 'info'}
            />
            <StatCard
              title="Active Anomalies"
              value={analytics.activeAnomalies || 0}
              subtitle="Isolation Forest outliers"
              icon={<FiAlertTriangle />}
              color={analytics.activeAnomalies > 0 ? 'warning' : 'success'}
            />
          </div>

          {/* Analytics Visualizations Row */}
          {analytics.totalClassifications > 0 && (
            <div className="grid-2" style={{ marginTop: '1.5rem' }}>
              <div className="card">
                <div className="card-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <div>
                    <h3 className="card-title">Waste Stream Distribution</h3>
                    <p className="card-subtitle">Actual proportion of classified items by waste stream</p>
                  </div>
                  <Link to="/analytics" className="btn btn-outline" style={{ fontSize: '0.8rem', padding: '0.35rem 0.75rem' }}>
                    Full Analytics
                  </Link>
                </div>
                {categoryValues.some((value) => value > 0) ? (
                  <div style={{ height: '280px', position: 'relative' }}>
                    <Doughnut data={doughnutData} options={doughnutOptions} />
                  </div>
                ) : (
                  <p className="empty-state" style={{ padding: '2rem 1rem', textAlign: 'center' }}>
                    Category breakdown is unavailable for these records.
                  </p>
                )}
              </div>

              <div className="card">
                <div className="card-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <div>
                    <h3 className="card-title">Intake Volume Trend</h3>
                    <p className="card-subtitle">Historical classification events over telemetry window</p>
                  </div>
                  <span className="badge badge-info">{analytics.storageProvider || 'Local Registry'}</span>
                </div>
                {trendLabels.length > 0 ? (
                  <div style={{ height: '280px', position: 'relative' }}>
                    <Line data={trendData} options={trendOptions} />
                  </div>
                ) : (
                  <p className="empty-state" style={{ padding: '2rem 1rem', textAlign: 'center' }}>
                    Insufficient dated history to display an intake trend.
                  </p>
                )}
              </div>
            </div>
          )}

          {/* Recent Records Table */}
          {recentRecords.length > 0 && (
            <div className="card" style={{ marginTop: '1.5rem' }}>
              <div className="card-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <div>
                  <h3 className="card-title">Recent Classification Events</h3>
                  <p className="card-subtitle">Latest software predictions logged to the storage registry</p>
                </div>
                <Link to="/history" className="btn btn-outline" style={{ display: 'inline-flex', alignItems: 'center', gap: '6px' }}>
                  View Full History <FiArrowRight />
                </Link>
              </div>

              <div className="table-responsive">
                <table className="table">
                  <thead>
                    <tr>
                      <th>Record ID</th>
                      <th>Predicted Class</th>
                      <th>Category</th>
                      <th>Confidence</th>
                      <th>Target Compartment</th>
                      <th>Routing Status</th>
                      <th>Timestamp</th>
                    </tr>
                  </thead>
                  <tbody>
                    {recentRecords.map((item) => (
                      <tr key={item.id}>
                        <td><code>{item.id}</code></td>
                        <td>
                          <code style={{ textTransform: 'capitalize' }}>
                            {item.predicted_class || item.predictedClass}
                          </code>
                        </td>
                        <td>
                          <span className={`badge ${
                            (item.waste_type || item.wasteType || '').includes('Recyclable') ? 'badge-info' :
                            (item.waste_type || item.wasteType || '').includes('Organic') ? 'badge-success' : 'badge-warning'
                          }`}>
                            {item.waste_type || item.wasteType}
                          </span>
                        </td>
                        <td>
                          <span className={`badge ${getConfidenceBadgeClass(item.confidence)}`}>
                            {typeof item.confidence === 'number' ? item.confidence.toFixed(1) : item.confidence}%
                          </span>
                        </td>
                        <td>
                          <span style={{ fontSize: '0.85rem', color: '#1f2937' }}>
                            {item.destination_compartment || item.destinationCompartment || '—'}
                          </span>
                        </td>
                        <td>
                          <span className={`badge ${item.manual_review_required ? 'badge-warning' : 'badge-success'}`}>
                            {item.routing_status || item.routingStatus || 'ROUTED'}
                          </span>
                        </td>
                        <td style={{ fontSize: '0.85rem', color: '#6b7280', whiteSpace: 'nowrap' }}>
                          {formatDateTime(item.timestamp)}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
}
