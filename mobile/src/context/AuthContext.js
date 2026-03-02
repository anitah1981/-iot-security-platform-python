import React, { createContext, useState, useContext, useEffect } from 'react';
import * as SecureStore from 'expo-secure-store';
import api, { getEffectiveApiUrl, setBaseUrlOverride, loadBaseUrlOverride } from '../config/api';

const AuthContext = createContext({});

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider');
  }
  return context;
};

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [effectiveApiUrl, setEffectiveApiUrl] = useState('...');

  useEffect(() => {
    let mounted = true;
    (async () => {
      await loadBaseUrlOverride();
      if (mounted) {
        setEffectiveApiUrl(getEffectiveApiUrl());
        loadUser();
      }
    })();
    return () => { mounted = false; };
  }, []);

  const loadUser = async () => {
    try {
      const token = await SecureStore.getItemAsync('auth_token');
      const userData = await SecureStore.getItemAsync('user_data');
      
      if (token && userData) {
        // Verify token is still valid
        try {
          const response = await api.get('/api/auth/me');
          setUser(response.data);
          await SecureStore.setItemAsync('user_data', JSON.stringify(response.data));
        } catch (error) {
          // Token invalid, clear storage
          await SecureStore.deleteItemAsync('auth_token');
          await SecureStore.deleteItemAsync('refresh_token');
          await SecureStore.deleteItemAsync('user_data');
          setUser(null);
        }
      } else {
        setUser(null);
      }
    } catch (error) {
      console.error('Error loading user:', error);
      setUser(null);
    } finally {
      setLoading(false);
    }
  };

  const login = async (email, password, mfaCode = null) => {
    try {
      const body = { email, password };
      if (mfaCode) body.mfa_code = mfaCode;
      const response = await api.post('/api/auth/login', body);

      const { token, refresh_token, user: userData } = response.data;

      // Store tokens securely
      await SecureStore.setItemAsync('auth_token', token);
      if (refresh_token) {
        await SecureStore.setItemAsync('refresh_token', refresh_token);
      }
      await SecureStore.setItemAsync('user_data', JSON.stringify(userData));

      setUser(userData);
      return { success: true };
    } catch (error) {
      const detail = error.response?.data?.detail;
      const mfaRequired = detail && typeof detail === 'object' && detail.mfa_required;
      let message = 'Login failed';
      if (!error.response) {
        message = "Can't reach server. Check your internet and that the app is using the correct server URL (e.g. https://pro-alert.co.uk).";
      } else if (typeof detail === 'string') {
        message = detail;
      } else if (detail && typeof detail === 'object' && detail.message) {
        message = detail.message;
      } else if (detail && typeof detail === 'object') {
        message = JSON.stringify(detail);
      } else if (error.message) {
        message = error.message;
      }
      return { success: false, error: message, mfaRequired };
    }
  };

  const signup = async (name, email, password, role = 'consumer') => {
    try {
      const response = await api.post('/api/auth/signup', {
        name,
        email,
        password,
        role,
      });

      const { token, refresh_token, user: userData } = response.data;

      // Store tokens securely
      await SecureStore.setItemAsync('auth_token', token);
      if (refresh_token) {
        await SecureStore.setItemAsync('refresh_token', refresh_token);
      }
      await SecureStore.setItemAsync('user_data', JSON.stringify(userData));

      setUser(userData);
      return { success: true };
    } catch (error) {
      const detail = error.response?.data?.detail;
      let message = 'Signup failed';
      if (!error.response) {
        message = "Can't reach server. Check your internet and server URL.";
      } else if (typeof detail === 'string') message = detail;
      else if (detail?.message) message = detail.message;
      return { success: false, error: message };
    }
  };

  const logout = async () => {
    try {
      // Call logout endpoint if available
      try {
        await api.post('/api/auth/logout');
      } catch (e) {
        // Ignore logout errors
      }

      // Clear storage
      await SecureStore.deleteItemAsync('auth_token');
      await SecureStore.deleteItemAsync('refresh_token');
      await SecureStore.deleteItemAsync('user_data');

      setUser(null);
    } catch (error) {
      console.error('Error logging out:', error);
    }
  };

  const updateUser = (userData) => {
    setUser(userData);
    SecureStore.setItemAsync('user_data', JSON.stringify(userData));
  };

  /** Ping /api/health to see if the backend is reachable. Returns { ok: true } or { ok: false, error } */
  const checkConnection = async () => {
    try {
      const res = await api.get('/api/health', { timeout: 8000 });
      return res?.data?.ok ? { ok: true } : { ok: false, error: 'Server returned unexpected response' };
    } catch (e) {
      return {
        ok: false,
        error: e.response ? `Server error: ${e.response.status}` : "Can't reach server. Check internet and server URL.",
        apiUrl: getEffectiveApiUrl(),
      };
    }
  };

  const setApiUrlOverride = async (url) => {
    const newUrl = await setBaseUrlOverride(url);
    setEffectiveApiUrl(newUrl);
    return newUrl;
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        loading,
        login,
        signup,
        logout,
        updateUser,
        loadUser,
        checkConnection,
        setApiUrlOverride,
        apiUrl: effectiveApiUrl,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};
