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
  FiUsers,
  FiDatabase,
  FiAlertTriangle,
  FiCheckCircle,
  FiCpu,
  FiTrendingUp,
  FiActivity,
  FiArrowRight,
  FiRefreshCw
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

export default function AdminDashboardPage() {
  const [analytics, setAnalytics] = useState(null);
  const [recentRecords, setRecentRecords] = useState([]);
  const [anomalies, setAnomalies] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const loadData = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      const [analyticsData, historyData, anomalyData] = await Promise.all([
        api.getAnalytics(),
        api.getHistory({ limit: 5 }),
        api.getAnomalies()
      ]);
      setAnalytics(analyticsData);
      setRecentRecords(Array.isArray(historyData) ? historyData : (historyData?.records || []));
      setAnomalies(anomalyData?.anomalies || []);
    } catch (err) {
      setError(err.message || 'Failed to retrieve administrative overview telemetry.');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const categoryLabels = ['Recyclable / Dry', 'Organic / Wet', 'Hazardous / E-Waste', 'Residual Trash'];
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

  const trendLabels = analytics?.volumeTrends?.map((d) => d.date?.split('-').slice(1).join('/')) || [];
  const trendValues = analytics?.volumeTrends?.map((d) => d.count) || [];

  const trendData = {
    labels: trendLabels.length ? trendLabels : ['Today'],
    datasets: [
      {
        label: 'System Classification Throughput',
        data: trendValues.length ? trendValues : [analytics?.todayActivity || 0],
        borderColor: '#0284c7',
        backgroundColor: 'rgba(2, 132, 199, 0.12)',
        tension: 0.35,
        fill: true
      }
    ]
  };

  const totalClassifications = analytics?.totalClassifications || 0;

  return (
    <div>
      <div className="page-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem' }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <h1 className="page-title">Administrator Central Command</h1>
            <span className="badge badge-info" style={{ fontWeight: 600 }}>ADMIN CONSOLE</span>
          </div>
          <p className="page-subtitle">
            System health, verified event registry, algorithm performance, and sanitation governance
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
          <Link to="/admin/sanitationai" className="btn btn-primary" style={{ display: 'inline-flex', alignItems: 'center', gap: '8px' }}>
            <FiCpu /> Launch SanitationAI
          </Link>
        </div>
      </div>

      {error && <div className="alert alert-danger">{error}</div>}

      {/* Admin Stats Grid */}
      <div className="stats-grid">
        <StatCard
          title="Active Storage Provider"
          value={analytics?.storageProvider || 'Local Registry'}
          subtitle="Emulated Dev Mode"
          icon={<FiDatabase />}
          color="primary"
        />
        <StatCard
          title="Total Master Records"
          value={totalClassifications.toLocaleString()}
          subtitle="Stored event logs"
          icon={<FiActivity />}
          color="info"
        />
        <StatCard
          title="Active Anomalies"
          value={anomalies.length}
          subtitle="Isolation Forest outliers"
          icon={<FiAlertTriangle />}
          color={anomalies.length > 0 ? 'warning' : 'success'}
        />
        <StatCard
          title="System Sanitation"
          value={analytics?.sanitationStatus || 'UNAVAILABLE'}
          subtitle="Software evaluated"
          icon={<FiCheckCircle />}
          color={analytics?.sanitationStatus === 'GOOD' ? 'success' : 'warning'}
        />
      </div>

      {/* Charts Row */}
      <div className="grid-2" style={{ marginTop: '1.5rem' }}>
        <div className="card">
          <div className="card-header">
            <h3 className="card-title">Macro Waste Distribution</h3>
            <p className="card-subtitle">Aggregated system-wide stream proportions</p>
          </div>
          <div style={{ height: '260px', position: 'relative' }}>
            <Doughnut data={doughnutData} options={{ responsive: true, maintainAspectRatio: false, cutout: '65%' }} />
          </div>
        </div>

        <div className="card">
          <div className="card-header">
            <h3 className="card-title">Intake Volume Trend</h3>
            <p className="card-subtitle">Classification throughput across recorded timeline</p>
          </div>
          <div style={{ height: '260px', position: 'relative' }}>
            <Line data={trendData} options={{ responsive: true, maintainAspectRatio: false }} />
          </div>
        </div>
      </div>

      {/* Recent Activity & Anomalies Section */}
      <div className="grid-2" style={{ marginTop: '1.5rem' }}>
        {/* Recent Classifications */}
        <div className="card">
          <div className="card-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <h3 className="card-title">Recent Inflow Events</h3>
            <Link to="/admin/records" className="btn btn-outline" style={{ fontSize: '0.8rem', padding: '0.3rem 0.6rem' }}>
              All Records <FiArrowRight />
            </Link>
          </div>
          {recentRecords.length === 0 ? (
            <p style={{ color: '#6b7280', fontSize: '0.9rem', padding: '1rem 0' }}>No records logged in storage repository yet.</p>
          ) : (
            <div className="table-responsive">
              <table className="table" style={{ fontSize: '0.85rem' }}>
                <thead>
                  <tr>
                    <th>Record ID</th>
                    <th>Class</th>
                    <th>Category</th>
                    <th>Confidence</th>
                    <th>Time</th>
                  </tr>
                </thead>
                <tbody>
                  {recentRecords.map((r) => (
                    <tr key={r.id}>
                      <td><code>{r.id}</code></td>
                      <td><code>{r.predicted_class || r.predictedClass}</code></td>
                      <td>{r.waste_type || r.wasteType}</td>
                      <td>
                        <span className={`badge ${getConfidenceBadgeClass(r.confidence)}`}>
                          {typeof r.confidence === 'number' ? r.confidence.toFixed(1) : r.confidence}%
                        </span>
                      </td>
                      <td style={{ color: '#6b7280' }}>{formatDateTime(r.timestamp)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>

        {/* Flagged Anomalies */}
        <div className="card">
          <div className="card-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <h3 className="card-title">Unresolved Telemetry Anomalies</h3>
            <Link to="/admin/anomalies" className="btn btn-outline" style={{ fontSize: '0.8rem', padding: '0.3rem 0.6rem' }}>
              Anomaly Manager <FiArrowRight />
            </Link>
          </div>
          {anomalies.length === 0 ? (
            <div style={{ padding: '1.5rem', textAlign: 'center', color: '#10b981' }}>
              <FiCheckCircle style={{ fontSize: '2rem', marginBottom: '0.5rem' }} />
              <div style={{ fontWeight: 600 }}>Nominal Bounds Maintained</div>
              <div style={{ fontSize: '0.85rem', color: '#6b7280' }}>Zero anomalous variance flagged by Isolation Forest.</div>
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
              {anomalies.map((a) => (
                <div key={a.id} style={{ padding: '0.75rem', border: '1px solid #e5e7eb', borderRadius: '6px' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <strong>{a.type}</strong>
                    <span className={`badge ${a.severity?.toLowerCase() === 'high' ? 'badge-danger' : 'badge-warning'}`}>
                      {a.severity}
                    </span>
                  </div>
                  <div style={{ fontSize: '0.8rem', color: '#6b7280', marginTop: '4px' }}>
                    {a.reason}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
