import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { api, setAuthToken, setOnUnauthorized } from '../services/api';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(null);
  const [loading, setLoading] = useState(true);
  const [authMode, setAuthMode] = useState('server_verified');

  const logout = useCallback(() => {
    setUser(null);
    setToken(null);
    setAuthToken(null);
    localStorage.removeItem('ecosort_auth_token');
    localStorage.removeItem('ecosort_user');
  }, []);

  // Register automatic session expiration callback on HTTP 401
  useEffect(() => {
    setOnUnauthorized(() => {
      console.warn('Authentication token expired or rejected by backend. Terminating active session.');
      logout();
    });
  }, [logout]);

  // Restore and cryptographically verify persisted session on mount
  useEffect(() => {
    const restoreSession = async () => {
      const savedToken = localStorage.getItem('ecosort_auth_token');
      const savedUserStr = localStorage.getItem('ecosort_user');

      if (savedToken) {
        setAuthToken(savedToken);
        setToken(savedToken);
        try {
          // Cryptographically verify token with server
          const verification = await api.verifyAuthToken(savedToken);
          if (verification && verification.valid && verification.user) {
            setUser({
              ...verification.user,
              role: verification.role || verification.user.role,
              isAdmin: verification.is_admin
            });
            setLoading(false);
            return;
          }
        } catch (err) {
          console.warn('Persisted session failed server verification:', err.message);
          logout();
        }
      } else if (savedUserStr) {
        // Clear stale unauthenticated legacy storage
        localStorage.removeItem('ecosort_user');
      }

      setLoading(false);
    };

    restoreSession();
  }, [logout]);

  const login = async (email, password) => {
    setLoading(true);
    const emailClean = (email || '').trim().toLowerCase();
    const isRequestedAdmin = emailClean === 'admin@ecosortai.com';
    const requestedRole = isRequestedAdmin ? 'administrator' : 'citizen';

    try {
      // 1. Request cryptographically signed token from backend
      const tokenResponse = await api.getDemoToken(
        emailClean,
        requestedRole,
        isRequestedAdmin ? 'Municipal Administrator' : 'Verified Citizen'
      );

      const verifiedToken = tokenResponse.token;
      const verifiedUser = {
        ...tokenResponse.user,
        role: tokenResponse.user.role,
        isAdmin: tokenResponse.user.is_admin
      };

      // 2. Persist token in API client and secure storage
      setAuthToken(verifiedToken);
      setToken(verifiedToken);
      setUser(verifiedUser);
      setAuthMode(tokenResponse.mode || 'server_verified');

      localStorage.setItem('ecosort_auth_token', verifiedToken);
      localStorage.setItem('ecosort_user', JSON.stringify(verifiedUser));

      setLoading(false);
      return verifiedUser;
    } catch (err) {
      setLoading(false);
      throw new Error(err.message || 'Authentication failed. Please verify credentials.');
    }
  };

  const register = async (name, email, password) => {
    setLoading(true);
    const emailClean = (email || '').trim().toLowerCase();

    try {
      const tokenResponse = await api.getDemoToken(emailClean, 'citizen', name || 'Citizen User');
      const verifiedToken = tokenResponse.token;
      const verifiedUser = {
        ...tokenResponse.user,
        name: name || 'Citizen User',
        role: 'citizen',
        isAdmin: false
      };

      setAuthToken(verifiedToken);
      setToken(verifiedToken);
      setUser(verifiedUser);

      localStorage.setItem('ecosort_auth_token', verifiedToken);
      localStorage.setItem('ecosort_user', JSON.stringify(verifiedUser));

      setLoading(false);
      return verifiedUser;
    } catch (err) {
      setLoading(false);
      throw new Error(err.message || 'Registration failed. Please try again.');
    }
  };

  const resetPassword = async (email) => {
    await new Promise(resolve => setTimeout(resolve, 600));
    return true;
  };

  const value = {
    user,
    token,
    loading,
    authMode,
    login,
    register,
    logout,
    resetPassword,
    isAdmin: Boolean(user?.is_admin || user?.isAdmin || user?.role === 'administrator'),
    isAuthenticated: Boolean(user && token)
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
