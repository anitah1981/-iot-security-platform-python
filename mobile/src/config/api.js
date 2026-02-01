import Constants from 'expo-constants';
// Use the browser build of axios to avoid Node-only dependencies (like 'crypto')
import axios from 'axios/dist/axios.js';
import * as SecureStore from 'expo-secure-store';

// Get API URL from config or use default
const API_URL = Constants.expoConfig?.extra?.apiUrl || 'http://localhost:8000';

// Create axios instance
const api = axios.create({
  baseURL: API_URL,
  timeout: 10000,
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
export { API_URL };
