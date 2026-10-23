import React, { useState } from 'react';
import { MOCK_USERS_LIST } from '../../data/mockData';
import { FiUsers, FiSearch, FiShield, FiUserCheck, FiUserX, FiMail } from 'react-icons/fi';

export default function UsersPage() {
  const [users, setUsers] = useState(MOCK_USERS_LIST);
  const [search, setSearch] = useState('');

  const filteredUsers = users.filter(
    (u) =>
      u.name.toLowerCase().includes(search.toLowerCase()) ||
      u.email.toLowerCase().includes(search.toLowerCase()) ||
      u.role.toLowerCase().includes(search.toLowerCase())
  );

  const toggleRole = (userId) => {
    setUsers((prev) =>
      prev.map((u) => {
        if (u.id === userId) {
          const newRole = u.role === 'admin' ? 'user' : 'admin';
          return { ...u, role: newRole };
        }
        return u;
      })
    );
  };

  return (
    <div>
      <div className="page-header">
        <h1 className="page-title">User Directory & Roles</h1>
        <p className="page-subtitle">
          Manage researcher accounts, role permissions, and access privileges (Firebase Auth / Firestore)
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
                onChange={(e) => setSearch(e.target.value)}
              />
            </div>
          </div>
          <span className="badge badge-info">{filteredUsers.length} Users Listed</span>
        </div>

        <div className="table-responsive">
          <table className="table">
            <thead>
              <tr>
                <th>User Details</th>
                <th>Email Address</th>
                <th>Assigned Role</th>
                <th>Created Date</th>
                <th>Classifications</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {filteredUsers.map((u) => (
                <tr key={u.id}>
                  <td>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                      <div
                        style={{
                          width: '32px',
                          height: '32px',
                          borderRadius: '50%',
                          backgroundColor: u.role === 'admin' ? '#ef4444' : '#2563eb',
                          color: '#fff',
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'center',
                          fontWeight: 600,
                          fontSize: '0.85rem'
                        }}
                      >
                        {u.name.charAt(0)}
                      </div>
                      <div>
                        <strong>{u.name}</strong>
                        <div style={{ fontSize: '0.75rem', color: '#6b7280' }}>ID: {u.id}</div>
                      </div>
                    </div>
                  </td>
                  <td>{u.email}</td>
                  <td>
                    <span className={`badge ${u.role === 'admin' ? 'badge-danger' : 'badge-info'}`}>
                      {u.role.toUpperCase()}
                    </span>
                  </td>
                  <td style={{ color: '#6b7280', fontSize: '0.85rem' }}>{u.createdAt}</td>
                  <td><strong>{u.classificationsCount}</strong></td>
                  <td>
                    <button
                      type="button"
                      className="btn btn-outline"
                      style={{ fontSize: '0.75rem', padding: '0.25rem 0.5rem' }}
                      onClick={() => toggleRole(u.id)}
                    >
                      Toggle to {u.role === 'admin' ? 'User' : 'Admin'}
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
