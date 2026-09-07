/**
 * Ancestra Frontend API Client Layer
 * 
 * Provides centralized, authenticated HTTP request methods to the FastAPI backend.
 * Automatically manages JWT access tokens and transparent token refreshing.
 */

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000/api/v1";
const BACKEND_ROOT_URL = API_BASE_URL.replace(/\/api\/v1\/?$/, "");

const ACCESS_TOKEN_KEY = "ancestra_access_token";
const REFRESH_TOKEN_KEY = "ancestra_refresh_token";

// Storage Helpers
export function getAccessToken() {
  return localStorage.getItem(ACCESS_TOKEN_KEY);
}

export function getRefreshToken() {
  return localStorage.getItem(REFRESH_TOKEN_KEY);
}

export function setTokens(accessToken, refreshToken) {
  if (accessToken) {
    localStorage.setItem(ACCESS_TOKEN_KEY, accessToken);
  }
  if (refreshToken) {
    localStorage.setItem(REFRESH_TOKEN_KEY, refreshToken);
  }
}

export function clearTokens() {
  localStorage.removeItem(ACCESS_TOKEN_KEY);
  localStorage.removeItem(REFRESH_TOKEN_KEY);
}

/**
 * Base HTTP request wrapper with automatic Bearer token injection and 401 refresh handling.
 */
async function apiRequest(endpoint, options = {}, isRetry = false) {
  const url = endpoint.startsWith("http")
    ? endpoint
    : `${API_BASE_URL}${endpoint.startsWith("/") ? endpoint : `/${endpoint}`}`;

  const headers = { ...options.headers };

  // Attach Bearer token if present and not already provided
  const token = getAccessToken();
  if (token && !headers["Authorization"]) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  // Set default JSON Content-Type if body is plain object
  if (options.body && !(options.body instanceof FormData) && !headers["Content-Type"]) {
    headers["Content-Type"] = "application/json";
  }

  try {
    const response = await fetch(url, {
      ...options,
      headers,
    });

    // If Unauthorized (401) and we haven't retried yet, attempt refresh token exchange
    if (response.status === 401 && !isRetry) {
      const refreshTokenValue = getRefreshToken();
      if (refreshTokenValue) {
        try {
          const refreshRes = await fetch(`${BACKEND_ROOT_URL}/auth/refresh`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ refresh_token: refreshTokenValue }),
          });

          if (refreshRes.ok) {
            const refreshData = await refreshRes.json();
            setTokens(refreshData.access_token, refreshData.refresh_token);
            // Retry the original request with new token
            headers["Authorization"] = `Bearer ${refreshData.access_token}`;
            return apiRequest(endpoint, { ...options, headers }, true);
          } else {
            // Refresh token expired or revoked
            clearTokens();
          }
        } catch (refreshErr) {
          console.error("Failed to refresh auth token:", refreshErr);
          clearTokens();
        }
      }
    }

    if (!response.ok) {
      let errorData;
      try {
        errorData = await response.json();
      } catch {
        errorData = { detail: response.statusText || `HTTP Error ${response.status}` };
      }
      const error = new Error(errorData.detail || errorData.message || `Request failed with status ${response.status}`);
      error.status = response.status;
      error.data = errorData;
      throw error;
    }

    // Return JSON if available, otherwise raw response
    const contentType = response.headers.get("content-type");
    if (contentType && contentType.includes("application/json")) {
      return await response.json();
    }
    return response;
  } catch (error) {
    throw error;
  }
}

/**
 * Ancestra API Methods
 */
export const api = {
  // Base URLs
  API_BASE_URL,
  BACKEND_ROOT_URL,

  // Token Management
  getAccessToken,
  getRefreshToken,
  setTokens,
  clearTokens,

  // ==========================================
  // Authentication & User Endpoints
  // ==========================================
  getGoogleLoginUrl() {
    return `${BACKEND_ROOT_URL}/auth/login`;
  },

  async getMe() {
    return apiRequest(`${BACKEND_ROOT_URL}/auth/me`);
  },

  async refreshToken(token) {
    const refreshTokenValue = token || getRefreshToken();
    if (!refreshTokenValue) throw new Error("No refresh token available");
    const res = await apiRequest(`${BACKEND_ROOT_URL}/auth/refresh`, {
      method: "POST",
      body: JSON.stringify({ refresh_token: refreshTokenValue }),
    });
    if (res.access_token) {
      setTokens(res.access_token, res.refresh_token);
    }
    return res;
  },

  async logout() {
    try {
      await apiRequest(`${BACKEND_ROOT_URL}/auth/logout`, { method: "POST" });
    } catch (e) {
      console.warn("Backend logout request notice:", e);
    } finally {
      clearTokens();
    }
    return { success: true };
  },

  // ==========================================
  // Health & System Status
  // ==========================================
  async checkHealth() {
    const res = await fetch(`${BACKEND_ROOT_URL}/`);
    return await res.json();
  },

  // ==========================================
  // Module 1: Ingestion & Observations
  // ==========================================
  async uploadObservation({ monumentId, imageFile, metadata = {} }) {
    const formData = new FormData();
    formData.append("monument_id", monumentId);
    formData.append("file", imageFile);

    if (metadata && Object.keys(metadata).length > 0) {
      formData.append("metadata", JSON.stringify(metadata));
    }

    return apiRequest("/observations/upload", {
      method: "POST",
      body: formData,
    });
  },

  async listObservations(monumentId) {
    return apiRequest(`/observations/${monumentId}`);
  },

  // ==========================================
  // Module 2: Consensus & Memory
  // ==========================================
  async getConsensus(regionId) {
    return apiRequest(`/consensus/${regionId}`);
  },

  // ==========================================
  // Module 3: Anomaly Validation
  // ==========================================
  async validateAnomaly({ anomalyId, validationStatus, validatorNotes = "", expertId = null }) {
    return apiRequest("/validation/validate", {
      method: "POST",
      body: JSON.stringify({
        anomaly_id: anomalyId,
        validation_status: validationStatus,
        validator_notes: validatorNotes,
        expert_id: expertId,
      }),
    });
  },

  // ==========================================
  // Module 4: Temporal Evolution
  // ==========================================
  async getDeteriorationTrend(regionId) {
    return apiRequest(`/temporal/trend/${regionId}`);
  },

  // ==========================================
  // Module 5: Orchestrator & Work Orders
  // ==========================================
  async createWorkOrder({ monumentId, regionId, anomalyId = null, priority = "MEDIUM", description = "", assignedTo = null }) {
    return apiRequest("/orchestrator/work-orders", {
      method: "POST",
      body: JSON.stringify({
        monument_id: monumentId,
        region_id: regionId,
        anomaly_id: anomalyId,
        priority,
        description,
        assigned_to: assignedTo,
      }),
    });
  },
};

export default api;
