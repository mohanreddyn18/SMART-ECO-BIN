import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import {
  createUserWithEmailAndPassword,
  getIdToken,
  onIdTokenChanged,
  sendEmailVerification,
  sendPasswordResetEmail,
  signInWithEmailAndPassword,
  signOut,
  updateProfile
} from 'firebase/auth';
import { api, setAuthToken, setOnUnauthorized } from '../services/api';
import { firebaseAuth } from '../services/firebase';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(null);
  const [loading, setLoading] = useState(true);
  const [authMode, setAuthMode] = useState(firebaseAuth ? 'firebase' : 'development');

  const clearSession = useCallback(() => {
    setUser(null);
    setToken(null);
    setAuthToken(null);
    localStorage.removeItem('ecosort_auth_token');
    localStorage.removeItem('ecosort_user');
  }, []);

  const logout = useCallback(async () => {
    if (firebaseAuth) {
      try {
        await signOut(firebaseAuth);
      } catch (error) {
        console.error('Firebase sign-out failed:', error);
      }
    }
    clearSession();
  }, [clearSession]);

  const establishVerifiedSession = useCallback(async (verifiedToken, preferredName = '') => {
    setAuthToken(verifiedToken);
    const verification = await api.verifyAuthToken(verifiedToken);
    if (!verification?.valid || !verification.user) {
      throw new Error('The backend could not verify this sign-in.');
    }

    const verifiedUser = {
      ...verification.user,
      name: verification.user.name || preferredName || verification.user.email,
      role: verification.role || verification.user.role,
      isAdmin: verification.is_admin
    };
    setAuthToken(verifiedToken);
    setToken(verifiedToken);
    setUser(verifiedUser);
    setAuthMode(firebaseAuth ? 'firebase' : 'server_verified');
    localStorage.setItem('ecosort_auth_token', verifiedToken);
    localStorage.setItem('ecosort_user', JSON.stringify(verifiedUser));
    return verifiedUser;
  }, []);

  useEffect(() => {
    setOnUnauthorized(() => {
      void logout();
    });
  }, [logout]);

  useEffect(() => {
    let active = true;

    const restoreFirebaseSession = async (firebaseUser) => {
      if (!active) return;
      if (!firebaseUser) {
        clearSession();
        setLoading(false);
        return;
      }

      setLoading(true);
      try {
        const idToken = await getIdToken(firebaseUser);
        await establishVerifiedSession(idToken, firebaseUser.displayName || '');
      } catch (error) {
        console.warn('Firebase session could not be verified by the backend:', error.message);
        clearSession();
        try {
          await signOut(firebaseAuth);
        } catch (signOutError) {
          console.error('Could not clear the unverified Firebase session:', signOutError);
        }
      } finally {
        if (active) setLoading(false);
      }
    };

    if (firebaseAuth) {
      const unsubscribe = onIdTokenChanged(firebaseAuth, restoreFirebaseSession);
      return () => {
        active = false;
        unsubscribe();
      };
    }

    const savedToken = localStorage.getItem('ecosort_auth_token');
    if (!savedToken || !import.meta.env.DEV) {
      clearSession();
      setLoading(false);
      return () => {
        active = false;
      };
    }

    establishVerifiedSession(savedToken)
      .catch((error) => {
        console.warn('Persisted development session failed server verification:', error.message);
        clearSession();
      })
      .finally(() => {
        if (active) setLoading(false);
      });

    return () => {
      active = false;
    };
  }, [clearSession, establishVerifiedSession]);

  const login = async (email, password) => {
    setLoading(true);
    const emailClean = (email || '').trim().toLowerCase();

    try {
      if (firebaseAuth) {
        const credential = await signInWithEmailAndPassword(firebaseAuth, emailClean, password);
        return await establishVerifiedSession(
          await getIdToken(credential.user),
          credential.user.displayName || ''
        );
      }

      if (import.meta.env.DEV) {
        const isRequestedAdmin = emailClean === 'admin@ecosortai.com';
        const tokenResponse = await api.getDemoToken(
          emailClean,
          isRequestedAdmin ? 'administrator' : 'citizen',
          isRequestedAdmin ? 'Municipal Administrator' : 'Verified Citizen'
        );
        setAuthMode(tokenResponse.mode || 'development_signed_token');
        return await establishVerifiedSession(tokenResponse.token, tokenResponse.user?.name || '');
      }

      throw new Error('Production authentication is not configured. Set the VITE_FIREBASE_* project values and rebuild.');
    } finally {
      setLoading(false);
    }
  };

  const register = async (name, email, password) => {
    setLoading(true);
    const emailClean = (email || '').trim().toLowerCase();

    try {
      if (firebaseAuth) {
        const credential = await createUserWithEmailAndPassword(firebaseAuth, emailClean, password);
        if (name?.trim()) {
          await updateProfile(credential.user, { displayName: name.trim() });
        }
        await sendEmailVerification(credential.user);
        return await establishVerifiedSession(
          await getIdToken(credential.user),
          name?.trim() || 'Citizen User'
        );
      }

      if (import.meta.env.DEV) {
        const tokenResponse = await api.getDemoToken(emailClean, 'citizen', name || 'Citizen User');
        return await establishVerifiedSession(tokenResponse.token, name || 'Citizen User');
      }

      throw new Error('Production authentication is not configured. Set the VITE_FIREBASE_* project values and rebuild.');
    } finally {
      setLoading(false);
    }
  };

  const resetPassword = async (email) => {
    if (!firebaseAuth) {
      throw new Error('Password reset requires Firebase Authentication to be configured.');
    }
    await sendPasswordResetEmail(firebaseAuth, email.trim());
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
