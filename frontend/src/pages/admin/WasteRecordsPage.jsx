import React, { useState, useEffect, useCallback } from 'react';
import { api } from '../../services/api';
import { formatDateTime, getConfidenceBadgeClass } from '../../utils/helpers';
import { FiDatabase, FiTrash2, FiSearch, FiRefreshCw, FiCheckCircle, FiInbox } from 'react-icons/fi';

export default function WasteRecordsPage() {
  const [records, setRecords] = useState([]);
  const [search, setSearch] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [msg, setMsg] = useState('');

  const loadRecords = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      const data = await api.getHistory({ limit: 100 });
      setRecords(Array.isArray(data) ? data : (data?.records || []));
    } catch (err) {
      setError(err.message || 'Failed to retrieve master waste records from storage repository.');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadRecords();
  }, [loadRecords]);

  const filtered = records.filter(
    (r) =>
      (r.predicted_class || r.predictedClass || '').toLowerCase().includes(search.toLowerCase()) ||
      (r.waste_type || r.wasteType || '').toLowerCase().includes(search.toLowerCase()) ||
      (r.destination_compartment || r.destinationCompartment || '').toLowerCase().includes(search.toLowerCase()) ||
      (r.id || '').toLowerCase().includes(search.toLowerCase())
  );

  const handleDelete = async (id) => {
    try {
      await api.deleteRecord(id);
      setRecords((prev) => prev.filter((r) => r.id !== id));
      setMsg(`Record ${id} permanently deleted from authoritative storage.`);
      setTimeout(() => setMsg(''), 3000);
    } catch (err) {
      setError(`Failed to delete record: ${err.message}`);
      setTimeout(() => setError(''), 4000);
    }
  };

  return (
    <div>
      <div className="page-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem' }}>
        <div>
          <h1 className="page-title">Master Waste Records Audit</h1>
          <p className="page-subtitle">
            Administrative registry of all image classification transactions and metadata from the active storage provider
          </p>
        </div>
        <button
          type="button"
          className="btn btn-outline"
          onClick={loadRecords}
          disabled={loading}
          style={{ display: 'inline-flex', alignItems: 'center', gap: '6px' }}
        >
          <FiRefreshCw className={loading ? 'spin' : ''} /> Refresh
        </button>
      </div>

      {msg && <div className="alert alert-success">{msg}</div>}
      {error && <div className="alert alert-danger">{error}</div>}

      <div className="card">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.25rem', flexWrap: 'wrap', gap: '1rem' }}>
          <div style={{ flex: '1 1 300px' }}>
            <div className="input-with-icon">
              <FiSearch className="input-icon" />
              <input
                type="text"
                className="form-control"
                placeholder="Search by Record ID, category, or predicted class..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
              />
            </div>
          </div>
          <span className="badge badge-info">{filtered.length} Verified Master Records</span>
        </div>

        {loading ? (
          <div style={{ textAlign: 'center', padding: '3rem 1rem' }}>
            <div className="spinner" style={{ width: '28px', height: '28px', margin: '0 auto 0.75rem auto' }}></div>
            <p style={{ color: '#6b7280' }}>Loading master records from storage provider...</p>
          </div>
        ) : filtered.length === 0 ? (
          <div className="empty-state" style={{ padding: '3rem 1rem', textAlign: 'center' }}>
            <FiInbox style={{ fontSize: '3rem', color: '#9ca3af', marginBottom: '0.75rem' }} />
            <h3>No Records in Storage Repository</h3>
            <p style={{ color: '#6b7280' }}>
              {search ? 'No records matched your search query.' : 'No classification events have been logged yet.'}
            </p>
          </div>
        ) : (
          <div className="table-responsive">
            <table className="table">
              <thead>
                <tr>
                  <th>Record ID</th>
                  <th>Predicted Class</th>
                  <th>Category</th>
                  <th>Confidence</th>
                  <th>Target Compartment</th>
                  <th>Logged At</th>
                  <th>Admin Action</th>
                </tr>
              </thead>
              <tbody>
                {filtered.map((r) => (
                  <tr key={r.id}>
                    <td><code>{r.id}</code></td>
                    <td>
                      <code style={{ textTransform: 'capitalize' }}>
                        {r.predicted_class || r.predictedClass}
                      </code>
                    </td>
                    <td>
                      <span className="badge badge-info">{r.waste_type || r.wasteType}</span>
                    </td>
                    <td>
                      <span className={`badge ${getConfidenceBadgeClass(r.confidence)}`}>
                        {typeof r.confidence === 'number' ? r.confidence.toFixed(1) : r.confidence}%
                      </span>
                    </td>
                    <td>{r.destination_compartment || r.destinationCompartment || '—'}</td>
                    <td style={{ color: '#6b7280', fontSize: '0.85rem' }}>{formatDateTime(r.timestamp)}</td>
                    <td>
                      <button
                        type="button"
                        className="btn btn-outline"
                        style={{ color: '#ef4444', borderColor: '#fca5a5', padding: '0.25rem 0.5rem', fontSize: '0.75rem' }}
                        onClick={() => handleDelete(r.id)}
                      >
                        <FiTrash2 style={{ marginRight: '4px' }} /> Prune View
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
