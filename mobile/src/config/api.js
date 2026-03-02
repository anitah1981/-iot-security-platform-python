import Constants from 'expo-constants';
// Use the browser build of axios to avoid Node-only dependencies (like 'crypto')
import axios from 'axios/dist/axios.js';
import * as SecureStore from 'expo-secure-store';

const BUILTIN_URL = Constants.expoConfig?.extra?.apiUrl || 'http://localhost:8000';
const OVERRIDE_KEY = 'api_url_override';

/** Get the effective API base URL (override if set, else built-in). Exported for display. */
let effectiveBaseUrl = BUILTIN_URL;

/** Set base URL override (call with url or null to clear). Updates axios and persists. */
async function setBaseUrlOverride(url) {
  const trimmed = (url || '').trim();
  if (trimmed) {
    effectiveBaseUrl = trimmed.replace(/\/+$/, ''); // no trailing slash
    api.defaults.baseURL = effectiveBaseUrl;
    await SecureStore.setItemAsync(OVERRIDE_KEY, effectiveBaseUrl);
  } else {
    effectiveBaseUrl = BUILTIN_URL;
    api.defaults.baseURL = BUILTIN_URL;
    await SecureStore.deleteItemAsync(OVERRIDE_KEY);
  }
  return effectiveBaseUrl;
}

/** Load saved override on startup. Call once when app starts. */
async function loadBaseUrlOverride() {
  try {
    const saved = await SecureStore.getItemAsync(OVERRIDE_KEY);
    if (saved) {
      effectiveBaseUrl = saved.replace(/\/+$/, '');
      api.defaults.baseURL = effectiveBaseUrl;
    }
  } catch (e) {
    console.warn('Could not load API URL override:', e);
  }
  return effectiveBaseUrl;
}

function getEffectiveApiUrl() {
  return effectiveBaseUrl;
}

// Create axios instance (baseURL can be changed via setBaseUrlOverride)
const api = axios.create({
  baseURL: BUILTIN_URL,
  timeout: 15000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor to add auth token
api.interceptors.request.use(
  async (config) => {
    try {
      const token = await SecureStore.getItemAsync('auth_token');
      if (token) {
        config.headers.Authorization = `Bearer ${token}`;
      }
    } catch (error) {
      console.error('Error getting token:', error);
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor to handle errors
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    if (error.response?.status === 401) {
      // Token expired or invalid - clear storage and redirect to login
      try {
        await SecureStore.deleteItemAsync('auth_token');
        await SecureStore.deleteItemAsync('refresh_token');
        await SecureStore.deleteItemAsync('user_data');
      } catch (e) {
        console.error('Error clearing storage:', e);
      }
    }
    return Promise.reject(error);
  }
);

export default api;
export { BUILTIN_URL as API_URL, getEffectiveApiUrl, setBaseUrlOverride, loadBaseUrlOverride };
