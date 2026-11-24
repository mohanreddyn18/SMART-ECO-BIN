import React, { useCallback, useEffect, useState } from 'react';
import { api } from '../../services/api';
import { FiRefreshCw, FiSearch, FiShield } from 'react-icons/fi';

export default function UsersPage() {
  const [users, setUsers] = useState([]);
  const [search, setSearch] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [nextPageToken, setNextPageToken] = useState(null);

  const loadUsers = useCallback(async (pageToken = null, append = false) => {
    setLoading(true);
    setError('');
    try {
      const result = await api.getUsers(pageToken);
      setUsers((previous) => append ? [...previous, ...result.users] : result.users);
      setNextPageToken(result.nextPageToken || null);
    } catch (requestError) {
      setError(requestError.message || 'Could not load the Firebase user directory.');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadUsers();
  }, [loadUsers]);

  const filteredUsers = users.filter((user) =>
    `${user.name} ${user.email} ${user.role}`.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div>
      <div className="page-header">
        <h1 className="page-title">User Directory & Roles</h1>
        <p className="page-subtitle">
          Registered Firebase Authentication accounts. Roles are resolved by backend policy and verified identity claims.
        </p>
      </div>

      <div className="card">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.25rem', flexWrap: 'wrap', gap: '1rem' }}>
          <div style={{ flex: '1 1 300px' }}>
            <div className="input-with-icon">
              <FiSearch className="input-icon" />
              <input
                type="text"
                className="form-control"
                placeholder="Search user by name, email, or role..."
                value={search}
                onChange={(event) => setSearch(event.target.value)}
              />
            </div>
          </div>
          <button type="button" className="btn btn-outline" onClick={() => loadUsers()} disabled={loading}>
            <FiRefreshCw className={loading ? 'spin' : ''} /> Refresh
          </button>
          <span className="badge badge-info">{filteredUsers.length} Users Listed</span>
        </div>

        {error && <div className="alert alert-error" role="alert">{error}</div>}
        {!loading && !error && users.length === 0 && (
          <div className="alert alert-info" role="status">No Firebase accounts were returned.</div>
        )}

        {users.length > 0 && (
          <div className="table-responsive">
            <table className="table">
              <thead>
                <tr>
                  <th>User Details</th>
                  <th>Email Address</th>
                  <th>Assigned Role</th>
                  <th>Email Verification</th>
                  <th>Created</th>
                </tr>
              </thead>
              <tbody>
                {filteredUsers.map((user) => (
                  <tr key={user.id}>
                    <td>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                        <div style={{
                          width: '32px',
                          height: '32px',
                          borderRadius: '50%',
                          backgroundColor: user.role === 'administrator' ? '#ef4444' : '#2563eb',
                          color: '#fff',
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'center',
                          fontWeight: 600,
                          fontSize: '0.85rem'
                        }}>
                          {user.name.charAt(0).toUpperCase()}
                        </div>
                        <div>
                          <strong>{user.name}</strong>
                          <div style={{ fontSize: '0.75rem', color: '#6b7280' }}>ID: {user.id}</div>
                        </div>
                      </div>
                    </td>
                    <td>{user.email || 'No email'}</td>
                    <td>
                      <span className={`badge ${user.role === 'administrator' ? 'badge-danger' : 'badge-info'}`}>
                        {user.role.toUpperCase()}
                      </span>
                    </td>
                    <td>{user.emailVerified ? 'Verified' : 'Not verified'}</td>
                    <td style={{ color: '#6b7280', fontSize: '0.85rem' }}>
                      {user.createdAt ? new Date(user.createdAt).toLocaleDateString() : 'Unavailable'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {nextPageToken && (
          <button
            type="button"
            className="btn btn-outline"
            onClick={() => loadUsers(nextPageToken, true)}
            disabled={loading}
          >
            Load More
          </button>
        )}

        <p style={{ display: 'flex', alignItems: 'center', gap: '6px', marginTop: '1rem', color: '#6b7280', fontSize: '0.85rem' }}>
          <FiShield /> Role changes must be made through Firebase Admin or the backend administrator allowlist; this directory is read-only.
        </p>
      </div>
    </div>
  );
}
