import { getApp, getApps, initializeApp } from 'firebase/app';
import { getAuth } from 'firebase/auth';

const config = {
  apiKey: import.meta.env.VITE_FIREBASE_API_KEY,
  authDomain: import.meta.env.VITE_FIREBASE_AUTH_DOMAIN,
  projectId: import.meta.env.VITE_FIREBASE_PROJECT_ID,
  appId: import.meta.env.VITE_FIREBASE_APP_ID
};

export const isFirebaseConfigured = Object.values(config).every(
  (value) => typeof value === 'string' && value.trim().length > 0
);

export const firebaseAuth = isFirebaseConfigured
  ? getAuth(getApps().length ? getApp() : initializeApp(config))
  : null;
