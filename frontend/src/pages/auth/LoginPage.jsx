import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';

export default function LoginPage() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const { login } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');

    if (!email || !password) {
      setError('Please enter both email and password.');
      return;
    }

    try {
      setLoading(true);
      const user = await login(email, password);
      if (user.role === 'administrator' || user.role === 'admin' || user.isAdmin || user.is_admin) {
        navigate('/admin/dashboard');
      } else {
        navigate('/dashboard');
      }
    } catch (err) {
      setError(err.message || 'Unable to sign in. Check your connection and try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="auth-page">
      <div className="auth-card">
        <div className="auth-header">
          <div className="auth-logo">E</div>
          <h1 className="auth-title">Welcome Back</h1>
          <p className="auth-subtitle">Sign in to EcoSort AI</p>
        </div>

        <form className="auth-form" onSubmit={handleSubmit}>
          {error && (
            <div style={{
              background: '#fef2f2',
              color: '#dc2626',
              padding: '10px 14px',
              borderRadius: '8px',
              fontSize: '13px',
              marginBottom: '12px',
              border: '1px solid #fecaca'
            }}>
              {error}
            </div>
          )}

          <div className="form-group">
            <label className="form-label" htmlFor="login-email">Email Address</label>
            <input
              id="login-email"
              type="email"
              className="form-input"
              placeholder="you@example.com"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              autoComplete="email"
            />
          </div>

          <div className="form-group">
            <label className="form-label" htmlFor="login-password">Password</label>
            <input
              id="login-password"
              type="password"
              className="form-input"
              placeholder="Enter your password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              autoComplete="current-password"
            />
          </div>

          <div style={{ textAlign: 'right', marginBottom: '16px' }}>
            <Link to="/forgot-password" className="auth-link" style={{ fontSize: '13px' }}>
              Forgot Password?
            </Link>
          </div>

          <button
            type="submit"
            className="btn btn-primary btn-lg"
            disabled={loading}
            style={{ width: '100%' }}
          >
            {loading ? (
              <>
                <span className="loading-spinner" style={{ width: 18, height: 18 }} />
                Signing in...
              </>
            ) : (
              'Sign In'
            )}
          </button>
        </form>

        <div className="auth-divider">or</div>

        <div style={{
          background: '#f0fdf4',
          border: '1px solid #d1fae5',
          borderRadius: '8px',
          padding: '12px',
          fontSize: '12px',
          color: '#065f46',
          textAlign: 'center',
          marginBottom: '16px'
        }}>
          <strong>Local development access:</strong> Use any valid email and a non-empty password for a citizen session. For the configured local administrator, use <code>admin@ecosortai.com</code>. Passwords are not stored or verified in demo mode; cross-device accounts require a configured production identity provider.
        </div>

        <div className="auth-footer">
          Don't have an account?{' '}
          <Link to="/register" className="auth-link">Create Account</Link>
        </div>
      </div>
    </div>
  );
}
