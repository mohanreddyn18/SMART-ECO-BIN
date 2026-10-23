/**
 * Central API Client for SMART ECO BIN Public Service Platform
 * ============================================================
 * Provides unified, safe, and consistent HTTP communications with the
 * FastAPI backend gateway (/api). Handles network timeouts, JSON parsing,
 * transparent error messages, and request cancellation.
 */

// Base API configuration: In local dev, falls back to relative '/api' (handled by Vite proxy).
// In production or separate Cloud Run deployment, respects VITE_API_BASE_URL build arg / env.
const RAW_BASE = (import.meta.env?.VITE_API_BASE_URL || '').trim().replace(/\/+$/, '');
const API_BASE = RAW_BASE ? `${RAW_BASE}/api` : '/api';
const HEALTH_URL = RAW_BASE ? `${RAW_BASE}/health` : '/health';
const MISSING_PRODUCTION_API_MESSAGE =
  'The backend API is not configured for this deployment. Set VITE_API_BASE_URL to the backend HTTPS origin and redeploy.';

let currentAuthToken = null;
let onUnauthorizedCallback = null;

export const setAuthToken = (token) => {
  currentAuthToken = token;
};

export const getAuthToken = () => currentAuthToken;

export const setOnUnauthorized = (callback) => {
  onUnauthorizedCallback = callback;
};

class ApiError extends Error {
  constructor(message, status = 0, detail = null) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.detail = detail;
  }
}

/**
 * Universal request wrapper with error sanitization, token injection, and timeout guard.
 */
async function request(endpoint, options = {}) {
  if (import.meta.env.PROD && !RAW_BASE) {
    throw new ApiError(MISSING_PRODUCTION_API_MESSAGE, 503);
  }

  const url = `${API_BASE}${endpoint}`;
  const controller = new AbortController();
  const timeoutMs = options.timeout || 15000;
  const timeoutId = setTimeout(() => controller.abort(), timeoutMs);

  const defaultHeaders = {
    Accept: 'application/json'
  };

  // Automatically attach verified Bearer token if session is active
  if (currentAuthToken) {
    defaultHeaders['Authorization'] = `Bearer ${currentAuthToken}`;
  }

  // Do not set Content-Type for FormData (browser sets boundary automatically)
  if (!(options.body instanceof FormData)) {
    defaultHeaders['Content-Type'] = 'application/json';
  }

  const config = {
    ...options,
    signal: options.signal || controller.signal,
    headers: {
      ...defaultHeaders,
      ...options.headers
    }
  };

  try {
    const response = await fetch(url, config);
    clearTimeout(timeoutId);

    // Parse JSON safely
    let data = null;
    const contentType = response.headers.get('content-type') || '';
    if (contentType.includes('application/json')) {
      data = await response.json().catch(() => null);
    } else {
      const text = await response.text().catch(() => '');
      data = text ? { message: text } : null;
    }

    if (!response.ok) {
      if (response.status === 401 && typeof onUnauthorizedCallback === 'function') {
        onUnauthorizedCallback();
      }
      const detailMsg = data?.detail || data?.message || `Server communication error (HTTP ${response.status})`;
      throw new ApiError(detailMsg, response.status, data);
    }

    return data;
  } catch (err) {
    clearTimeout(timeoutId);

    if (err.name === 'AbortError') {
      throw new ApiError('Request timed out. Please verify backend service availability.', 408);
    }

    if (err instanceof ApiError) {
      throw err;
    }

    // Network disconnection or CORS failure
    throw new ApiError(
      'Unable to connect to the backend gateway. Please ensure the local FastAPI service is running.',
      0,
      { originalError: err.message }
    );
  }
}

export const api = {
  /**
   * Health and System Status
   */
  async getHealth() {
    if (import.meta.env.PROD && !RAW_BASE) {
      return { status: 'unavailable', service: MISSING_PRODUCTION_API_MESSAGE };
    }

    try {
      const response = await fetch(HEALTH_URL);
      if (!response.ok) {
        throw new ApiError(`Backend health check failed (HTTP ${response.status}).`, response.status);
      }
      return await response.json();
    } catch (err) {
      if (err instanceof ApiError) throw err;
      throw new ApiError(
        'Unable to contact the backend health endpoint.',
        0,
        { originalError: err.message }
      );
    }
  },

  async getStorageStatus() {
    return request('/storage/status');
  },

  /**
   * Waste Image Classification (POST /api/predict)
   * Sends multipart form data with optional idempotency key.
   */
  async predictWaste(file, idempotencyKey = null) {
    if (!file) throw new ApiError('No image file provided for classification.');

    const formData = new FormData();
    formData.append('file', file);

    const headers = {};
    if (idempotencyKey) {
      headers['X-Idempotency-Key'] = idempotencyKey;
    }

    return request('/predict', {
      method: 'POST',
      body: formData,
      headers,
      timeout: 30000 // ML inference on CPU can take a few seconds
    });
  },

  /**
   * Multi-Object Mixed Waste Detection (POST /api/detect-waste)
   * Detects separate waste objects with bounding boxes and per-item disposal routing.
   */
  async detectWaste(file, includeAnnotation = true, idempotencyKey = null, confThreshold = null) {
    if (!file) throw new ApiError('No image file provided for waste detection.');

    const formData = new FormData();
    formData.append('file', file);

    const headers = {};
    if (idempotencyKey) {
      headers['X-Idempotency-Key'] = idempotencyKey;
    }

    const params = new URLSearchParams();
    params.set('include_annotation', includeAnnotation ? 'true' : 'false');
    if (confThreshold !== null && confThreshold !== undefined) {
      params.set('conf_threshold', confThreshold);
    }

    return request(`/detect-waste?${params.toString()}`, {
      method: 'POST',
      body: formData,
      headers,
      timeout: 35000
    });
  },

  /**
   * Classification History (GET /api/history)
   * Normalizes array responses and wrapper objects into a standard { records, total } structure.
   */
  async getHistory({ limit = 50, skip = 0, category = null, search = null } = {}) {
    const params = new URLSearchParams();
    if (limit) params.set('limit', limit);
    if (skip) params.set('skip', skip);
    if (category && category !== 'ALL') params.set('category', category);
    if (search && search.trim()) params.set('search', search.trim());

    const qs = params.toString() ? `?${params.toString()}` : '';
    const res = await request(`/history${qs}`);
    if (Array.isArray(res)) {
      return { records: res, total: res.length };
    }
    return res || { records: [], total: 0 };
  },

  /**
   * Single Record by ID (GET /api/history/:id)
   */
  async getRecordById(id) {
    if (!id) throw new ApiError('Record ID is required.');
    return request(`/history/${encodeURIComponent(id)}`);
  },

  /**
   * System-wide Analytics (GET /api/analytics)
   * Supports time period filtering: hourly, daily, weekly, monthly, yearly, custom
   */
  async getAnalytics({ period = 'all', startDate = null, endDate = null } = {}) {
    const params = new URLSearchParams();
    if (period && period !== 'all') params.set('period', period);
    if (startDate) params.set('start_date', startDate);
    if (endDate) params.set('end_date', endDate);
    const qs = params.toString() ? `?${params.toString()}` : '';
    return request(`/analytics${qs}`);
  },

  /**
   * Sanitation Intelligence (GET /api/sanitation)
   */
  async getSanitation() {
    return request('/sanitation');
  },

  /**
   * Statistical Anomalies (GET /api/anomalies)
   */
  async getAnomalies() {
    return request('/anomalies');
  },

  /**
   * Predictive Time-series Insights (GET /api/predictive-insights)
   */
  async getPredictiveInsights() {
    return request('/predictive-insights');
  },

  /**
   * WasteAI Assistant (POST /api/wasteai)
   */
  async queryWasteAI(prompt) {
    return request('/wasteai', {
      method: 'POST',
      body: JSON.stringify({ prompt })
    });
  },

  /**
   * SanitationAI Assistant (POST /api/sanitationai)
   */
  async querySanitationAI(prompt) {
    return request('/sanitationai', {
      method: 'POST',
      body: JSON.stringify({ prompt })
    });
  },

  /**
   * Token Verification (POST /api/auth/verify)
   */
  async verifyAuthToken(token) {
    return request('/auth/verify', {
      method: 'POST',
      headers: {
        Authorization: `Bearer ${token}`
      }
    });
  },

  /**
   * Controlled Development Token Issuance (POST /api/auth/demo-token)
   */
  async getDemoToken(email, role = 'citizen', name = 'Authorized User') {
    return request('/auth/demo-token', {
      method: 'POST',
      body: JSON.stringify({ email, role, name })
    });
  },

  /**
   * Administrative Record Deletion (DELETE /api/history/{id})
   */
  async deleteRecord(recordId) {
    return request(`/history/${recordId}`, {
      method: 'DELETE'
    });
  },

  /**
   * Public-service Security Posture (GET /api/security/posture)
   */
  async getSecurityPosture() {
    return request('/security/posture');
  }
};

export function isApiError(err) {
  return err instanceof ApiError;
}

export default api;
