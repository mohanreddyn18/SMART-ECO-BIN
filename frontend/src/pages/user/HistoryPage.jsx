import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { Link } from 'react-router-dom';
import { api } from '../../services/api';
import { formatDateTime, getConfidenceBadgeClass } from '../../utils/helpers';
import {
  FiSearch,
  FiFilter,
  FiEye,
  FiX,
  FiChevronLeft,
  FiChevronRight,
  FiRefreshCw,
  FiCamera,
  FiInbox,
  FiShield,
  FiInfo,
  FiCheckCircle
} from 'react-icons/fi';

export default function HistoryPage() {
  const [records, setRecords] = useState([]);
  const [totalCount, setTotalCount] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [searchTerm, setSearchTerm] = useState('');
  const [categoryFilter, setCategoryFilter] = useState('ALL');
  const [sortBy, setSortBy] = useState('date-desc');
  const [currentPage, setCurrentPage] = useState(1);
  const [selectedRecord, setSelectedRecord] = useState(null);

  const pageSize = 10;

  const loadHistory = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      const data = await api.getHistory({
        limit: 100,
        category: categoryFilter,
        search: searchTerm
      });
      const list = Array.isArray(data) ? data : (data?.records || []);
      setRecords(list);
      setTotalCount(Array.isArray(data) ? data.length : (data?.total !== undefined ? data.total : list.length));
    } catch (err) {
      setError(err.message || 'Failed to retrieve classification history from storage provider.');
    } finally {
      setLoading(false);
    }
  }, [categoryFilter, searchTerm]);

  useEffect(() => {
    loadHistory();
  }, [loadHistory]);

  const sortedRecords = useMemo(() => {
    const list = [...records];
    return list.sort((a, b) => {
      const timeA = new Date(a.timestamp || 0).getTime();
      const timeB = new Date(b.timestamp || 0).getTime();
      const confA = typeof a.confidence === 'number' ? a.confidence : 0;
      const confB = typeof b.confidence === 'number' ? b.confidence : 0;

      if (sortBy === 'date-desc') return timeB - timeA;
      if (sortBy === 'date-asc') return timeA - timeB;
      if (sortBy === 'confidence-desc') return confB - confA;
      if (sortBy === 'confidence-asc') return confA - confB;
      return 0;
    });
  }, [records, sortBy]);

  const totalPages = Math.ceil(sortedRecords.length / pageSize) || 1;
  const paginatedRecords = sortedRecords.slice(
    (currentPage - 1) * pageSize,
    currentPage * pageSize
  );

  return (
    <div>
      <div className="page-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem' }}>
        <div>
          <h1 className="page-title">Classification Audit Registry</h1>
          <p className="page-subtitle">
            Immutable, auditable registry of all image classification events, neural confidence, and routing directives
          </p>
        </div>
        <div style={{ display: 'flex', gap: '0.75rem' }}>
          <button
            type="button"
            className="btn btn-outline"
            onClick={loadHistory}
            disabled={loading}
            style={{ display: 'inline-flex', alignItems: 'center', gap: '6px' }}
          >
            <FiRefreshCw className={loading ? 'spin' : ''} /> Refresh
          </button>
          <Link to="/detect" className="btn btn-primary" style={{ display: 'inline-flex', alignItems: 'center', gap: '8px' }}>
            <FiCamera /> New Classification
          </Link>
        </div>
      </div>

      {/* Public Service Notice */}
      <div className="alert alert-info" style={{ marginBottom: '1.25rem', fontSize: '0.85rem' }}>
        <strong>Audit Trail Integrity:</strong> Event records represent discrete classification transactions logged by the
        backend storage abstraction. Each entry records the predicted neural class, model confidence, software target compartment,
        and human-audit flags. Records are never fabricated to populate tables.
      </div>

      {/* Error Alert */}
      {error && (
        <div className="alert alert-danger" style={{ marginBottom: '1.25rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div>
            <strong>Storage Error:</strong> {error}
          </div>
          <button type="button" className="btn btn-outline" onClick={loadHistory} style={{ fontSize: '0.8rem', padding: '0.3rem 0.6rem' }}>
            Retry
          </button>
        </div>
      )}

      <div className="card">
        {/* Controls: Search, Filter, Sort */}
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '1rem', marginBottom: '1.25rem' }}>
          <div style={{ flex: '1 1 250px' }}>
            <div className="input-with-icon">
              <FiSearch className="input-icon" />
              <input
                type="text"
                className="form-control"
                placeholder="Search by Record ID, class name, compartment..."
                value={searchTerm}
                onChange={(e) => {
                  setSearchTerm(e.target.value);
                  setCurrentPage(1);
                }}
              />
            </div>
          </div>

          <div style={{ minWidth: '180px' }}>
            <select
              className="form-control"
              value={categoryFilter}
              onChange={(e) => {
                setCategoryFilter(e.target.value);
                setCurrentPage(1);
              }}
            >
              <option value="ALL">All Categories</option>
              <option value="Recyclable">Recyclable / Dry</option>
              <option value="Organic">Organic / Wet</option>
              <option value="Hazardous">Hazardous / E-Waste</option>
              <option value="Residual">Residual / Trash</option>
            </select>
          </div>

          <div style={{ minWidth: '180px' }}>
            <select
              className="form-control"
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value)}
            >
              <option value="date-desc">Newest First</option>
              <option value="date-asc">Oldest First</option>
              <option value="confidence-desc">Highest Confidence</option>
              <option value="confidence-asc">Lowest Confidence</option>
            </select>
          </div>
        </div>

        {/* Loading State */}
        {loading && (
          <div style={{ textAlign: 'center', padding: '3rem 1rem' }}>
            <div className="spinner" style={{ width: '28px', height: '28px', margin: '0 auto 0.75rem auto' }}></div>
            <p style={{ color: '#6b7280', fontSize: '0.9rem' }}>Loading registry records from storage provider...</p>
          </div>
        )}

        {/* Empty State */}
        {!loading && paginatedRecords.length === 0 && (
          <div className="empty-state" style={{ padding: '3.5rem 1rem', textAlign: 'center' }}>
            <FiInbox className="empty-icon" style={{ fontSize: '3rem', color: '#9ca3af', marginBottom: '0.75rem' }} />
            <h3>No Audit Records Found</h3>
            <p style={{ maxWidth: '450px', margin: '0.5rem auto 1rem auto', color: '#6b7280' }}>
              {searchTerm || categoryFilter !== 'ALL'
                ? 'No classification records matched your search or category filter criteria.'
                : 'No waste classification events have been logged in the active storage repository yet.'}
            </p>
            {!searchTerm && categoryFilter === 'ALL' && (
              <Link to="/detect" className="btn btn-primary" style={{ display: 'inline-flex', alignItems: 'center', gap: '6px' }}>
                <FiCamera /> Record First Classification
              </Link>
            )}
          </div>
        )}

        {/* Table */}
        {!loading && paginatedRecords.length > 0 && (
          <div className="table-responsive">
            <table className="table">
              <thead>
                <tr>
                  <th>Record ID</th>
                  <th>Predicted Class</th>
                  <th>Waste Category</th>
                  <th>Confidence</th>
                  <th>Target Compartment</th>
                  <th>Routing Status</th>
                  <th>Logged At</th>
                  <th>Audit Action</th>
                </tr>
              </thead>
              <tbody>
                {paginatedRecords.map((item) => (
                  <tr key={item.id}>
                    <td>
                      <code style={{ fontSize: '0.8rem' }}>{item.id}</code>
                    </td>
                    <td>
                      <code style={{ textTransform: 'capitalize', fontWeight: 600 }}>
                        {item.predicted_class || item.predictedClass}
                      </code>
                    </td>
                    <td>
                      <span
                        className={`badge ${
                          (item.waste_type || item.wasteType || '').includes('Recyclable')
                            ? 'badge-info'
                            : (item.waste_type || item.wasteType || '').includes('Organic')
                            ? 'badge-success'
                            : 'badge-warning'
                        }`}
                      >
                        {item.waste_type || item.wasteType}
                      </span>
                    </td>
                    <td>
                      <span className={`badge ${getConfidenceBadgeClass(item.confidence)}`}>
                        {typeof item.confidence === 'number' ? item.confidence.toFixed(1) : item.confidence}%
                      </span>
                    </td>
                    <td style={{ fontSize: '0.85rem', color: '#374151' }}>
                      {item.destination_compartment || item.destinationCompartment || '—'}
                    </td>
                    <td>
                      <span className={`badge ${item.manual_review_required ? 'badge-warning' : 'badge-success'}`}>
                        {item.routing_status || item.routingStatus || 'ROUTED'}
                      </span>
                    </td>
                    <td style={{ fontSize: '0.85rem', color: '#6b7280', whiteSpace: 'nowrap' }}>
                      {formatDateTime(item.timestamp)}
                    </td>
                    <td>
                      <button
                        type="button"
                        className="btn btn-outline"
                        style={{ padding: '0.3rem 0.6rem', fontSize: '0.8rem' }}
                        onClick={() => setSelectedRecord(item)}
                      >
                        <FiEye style={{ marginRight: '4px' }} /> Inspect
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {/* Pagination */}
        {!loading && totalPages > 1 && (
          <div
            style={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              marginTop: '1.25rem',
              paddingTop: '1rem',
              borderTop: '1px solid #e5e7eb'
            }}
          >
            <span style={{ fontSize: '0.85rem', color: '#6b7280' }}>
              Showing {((currentPage - 1) * pageSize) + 1} to{' '}
              {Math.min(currentPage * pageSize, sortedRecords.length)} of{' '}
              {sortedRecords.length} records
            </span>
            <div style={{ display: 'flex', gap: '6px' }}>
              <button
                type="button"
                className="btn btn-outline"
                disabled={currentPage === 1}
                onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
                style={{ padding: '0.35rem 0.75rem' }}
              >
                <FiChevronLeft /> Prev
              </button>
              <button
                type="button"
                className="btn btn-outline"
                disabled={currentPage === totalPages}
                onClick={() => setCurrentPage((p) => Math.min(totalPages, p + 1))}
                style={{ padding: '0.35rem 0.75rem' }}
              >
                Next <FiChevronRight />
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Record Audit Inspection Modal */}
      {selectedRecord && (
        <div
          style={{
            position: 'fixed',
            inset: 0,
            backgroundColor: 'rgba(0,0,0,0.5)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            zIndex: 1000,
            padding: '1rem'
          }}
          onClick={() => setSelectedRecord(null)}
        >
          <div
            className="card"
            style={{ maxWidth: '580px', width: '100%', margin: 0, maxHeight: '90vh', overflowY: 'auto' }}
            onClick={(e) => e.stopPropagation()}
          >
            <div
              style={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                marginBottom: '1rem',
                borderBottom: '1px solid #e5e7eb',
                paddingBottom: '0.75rem'
              }}
            >
              <div>
                <h3 style={{ margin: 0, fontSize: '1.15rem' }}>Classification Event Audit Dossier</h3>
                <span style={{ fontSize: '0.8rem', color: '#6b7280' }}>Storage Provider: Local JSON Emulation</span>
              </div>
              <button
                type="button"
                style={{ border: 'none', background: 'none', cursor: 'pointer', fontSize: '1.25rem', color: '#6b7280' }}
                onClick={() => setSelectedRecord(null)}
              >
                <FiX />
              </button>
            </div>

            <div style={{ textAlign: 'center', margin: '1rem 0' }}>
              <div style={{ fontSize: '0.8rem', textTransform: 'uppercase', color: '#6b7280', fontWeight: 600 }}>
                Verified Classification Output
              </div>
              <h2 style={{ margin: '0.25rem 0', textTransform: 'capitalize', color: '#111827' }}>
                {selectedRecord.predicted_class || selectedRecord.predictedClass}
              </h2>
              <span className={`badge ${getConfidenceBadgeClass(selectedRecord.confidence)}`} style={{ fontSize: '0.95rem', padding: '0.25rem 0.6rem' }}>
                {typeof selectedRecord.confidence === 'number' ? selectedRecord.confidence.toFixed(1) : selectedRecord.confidence}% Confidence
              </span>
            </div>

            <div style={{ fontSize: '0.875rem', lineHeight: 1.8, display: 'flex', flexDirection: 'column', gap: '0.4rem' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', borderBottom: '1px solid #f3f4f6', paddingBottom: '0.25rem' }}>
                <span style={{ color: '#6b7280' }}>Record ID:</span>
                <code>{selectedRecord.id}</code>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', borderBottom: '1px solid #f3f4f6', paddingBottom: '0.25rem' }}>
                <span style={{ color: '#6b7280' }}>Operational Category:</span>
                <strong>{selectedRecord.waste_type || selectedRecord.wasteType}</strong>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', borderBottom: '1px solid #f3f4f6', paddingBottom: '0.25rem' }}>
                <span style={{ color: '#6b7280' }}>Target Compartment:</span>
                <span className="badge badge-success">{selectedRecord.destination_compartment || selectedRecord.destinationCompartment || '—'}</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', borderBottom: '1px solid #f3f4f6', paddingBottom: '0.25rem' }}>
                <span style={{ color: '#6b7280' }}>Compartment Identifier:</span>
                <code>{selectedRecord.compartment_id || selectedRecord.compartmentId || 'compartment-default'}</code>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', borderBottom: '1px solid #f3f4f6', paddingBottom: '0.25rem' }}>
                <span style={{ color: '#6b7280' }}>Routing Disposition:</span>
                <span className={`badge ${selectedRecord.manual_review_required ? 'badge-warning' : 'badge-info'}`}>
                  {selectedRecord.routing_status || selectedRecord.routingStatus || 'ROUTED'}
                </span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', borderBottom: '1px solid #f3f4f6', paddingBottom: '0.25rem' }}>
                <span style={{ color: '#6b7280' }}>Manual Review Required:</span>
                <span>{selectedRecord.manual_review_required ? 'YES (Confidence / Hazard flag)' : 'NO (Automated Routing)'}</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', borderBottom: '1px solid #f3f4f6', paddingBottom: '0.25rem' }}>
                <span style={{ color: '#6b7280' }}>Execution Posture:</span>
                <span>Software Digital Simulation Only</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', borderBottom: '1px solid #f3f4f6', paddingBottom: '0.25rem' }}>
                <span style={{ color: '#6b7280' }}>Timestamp:</span>
                <span>{formatDateTime(selectedRecord.timestamp)}</span>
              </div>
              {selectedRecord.idempotency_key && (
                <div style={{ display: 'flex', justifyContent: 'space-between', borderBottom: '1px solid #f3f4f6', paddingBottom: '0.25rem' }}>
                  <span style={{ color: '#6b7280' }}>Idempotency Key:</span>
                  <code>{selectedRecord.idempotency_key}</code>
                </div>
              )}
              <div style={{ marginTop: '0.5rem', background: '#f9fafb', padding: '0.75rem', borderRadius: '6px' }}>
                <div style={{ fontWeight: 600, color: '#374151', marginBottom: '2px' }}>Routing Rationale:</div>
                <div style={{ color: '#4b5563', fontSize: '0.85rem' }}>
                  {selectedRecord.routing_explanation || selectedRecord.recommendation || 'Automated stream assignment based on trained MobileNetV2 neural classification.'}
                </div>
              </div>
            </div>

            <div style={{ marginTop: '1.25rem', textAlign: 'right' }}>
              <button
                type="button"
                className="btn btn-primary"
                onClick={() => setSelectedRecord(null)}
              >
                Close Audit Dossier
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
