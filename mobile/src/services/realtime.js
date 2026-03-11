import { io } from 'socket.io-client';
import * as SecureStore from 'expo-secure-store';
import { getEffectiveApiUrl } from '../config/api';

let socket = null;

function getUserIdFromUser(user) {
  if (!user) return null;
  return user.id || user._id || user.user_id || null;
}

export async function initializeRealtime(user, { onDeviceUpdate, onNewAlert, onAlertResolved, onNotification } = {}) {
  const userId = getUserIdFromUser(user);
  if (!userId) {
    return;
  }

  const token = await SecureStore.getItemAsync('auth_token');
  if (!token) {
    return;
  }

  const baseUrl = getEffectiveApiUrl();
  if (!baseUrl) {
    return;
  }

  // Clean up any existing connection
  if (socket) {
    try {
      socket.disconnect();
    } catch (e) {
      // ignore
    }
    socket = null;
  }

  socket = io(baseUrl, {
    path: '/socket.io/',
    auth: {
      token,
      user_id: userId,
    },
    transports: ['websocket', 'polling'],
    reconnection: true,
    reconnectionAttempts: 5,
    reconnectionDelay: 1000,
    reconnectionDelayMax: 5000,
  });

  socket.on('connect', () => {
    // Connection established; server will automatically put us in user_<id> room
    // We rely on backend JWT validation for security.
  });

  socket.on('device_update', (data) => {
    if (typeof onDeviceUpdate === 'function') {
      onDeviceUpdate(data);
    }
  });

  socket.on('new_alert', (data) => {
    if (typeof onNewAlert === 'function') {
      onNewAlert(data);
    }
  });

  socket.on('alert_resolved', (data) => {
    if (typeof onAlertResolved === 'function') {
      onAlertResolved(data);
    }
  });

  socket.on('notification', (data) => {
    if (typeof onNotification === 'function') {
      onNotification(data);
    }
  });
}

export function disconnectRealtime() {
  if (socket) {
    try {
      socket.disconnect();
    } catch (e) {
      // ignore
    }
    socket = null;
  }
}

