import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import { FiMail, FiArrowLeft, FiCheckCircle } from 'react-icons/fi';

export default function ForgotPasswordPage() {
  const [email, setEmail] = useState('');
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const { resetPassword } = useAuth();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setMessage('');
    setLoading(true);

    try {
      await resetPassword(email);
      setMessage('Password reset instructions sent to your email address (Mock service).');
    } catch (err) {
      setError(err.message || 'Failed to send reset link.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="auth-wrapper">
      <div className="auth-card">
        <div className="auth-header">
          <div className="auth-logo">
            <span className="logo-icon">♻️</span>
            <h2>EcoSort AI</h2>
          </div>
          <p className="auth-subtitle">Reset your account password</p>
        </div>

        {error && <div className="alert alert-error">{error}</div>}
        {message && (
          <div className="alert alert-success">
            <FiCheckCircle style={{ marginRight: '8px' }} />
            {message}
          </div>
        )}

        <form onSubmit={handleSubmit} className="auth-form">
          <div className="form-group">
            <label>Registered Email Address</label>
            <div className="input-with-icon">
              <FiMail className="input-icon" />
              <input
                type="email"
                className="form-control"
                placeholder="your.email@example.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
              />
            </div>
          </div>

          <button
            type="submit"
            className="btn btn-primary btn-block"
            disabled={loading}
          >
            {loading ? 'Sending Instructions...' : 'Send Reset Link'}
          </button>
        </form>

        <div className="auth-footer">
          <Link to="/login" className="auth-link" style={{ display: 'inline-flex', alignItems: 'center', gap: '6px' }}>
            <FiArrowLeft /> Back to Login
          </Link>
        </div>
      </div>
    </div>
  );
}
