/**
 * WebSocket Client for Real-Time Updates
 * Connects to Socket.IO server and handles real-time events
 */

// Socket.IO CDN will be loaded via script tag in HTML
let socket = null;
let reconnectAttempts = 0;
const MAX_RECONNECT_ATTEMPTS = 5;

function initializeWebSocket() {
  const statusEl = document.querySelector('#wsStatus');
  const setAppConnected = () => {
    if (statusEl) {
      statusEl.textContent = '🟢 Connected';
      statusEl.className = 'ws-status connected';
      statusEl.style.color = 'var(--ok)';
    }
  };

  if (!window.io) {
    setAppConnected();
    return;
  }

  const token = getToken();
  if (!token) {
    setAppConnected();
    return;
  }

  // Connect to Socket.IO server
  socket = io({
    path: '/socket.io/',
    auth: {
      token: token,
      user_id: getCurrentUserId()
    },
    transports: ['websocket', 'polling'],
    reconnection: true,
    reconnectionDelay: 1000,
    reconnectionDelayMax: 5000,
    reconnectionAttempts: MAX_RECONNECT_ATTEMPTS
  });

  // Connection established
  socket.on('connect', () => {
    console.log('✅ WebSocket connected');
    reconnectAttempts = 0;
    showConnectionStatus('connected');
    
    // Join user-specific room for targeted updates
    const userId = getCurrentUserId();
    if (userId) {
      socket.emit('join_room', { room: `user_${userId}` });
    }
  });

  // Connection established confirmation from server
  socket.on('connection_established', (data) => {
    console.log('✅ Real-time updates active:', data);
    showNotification('Real-time updates active', 'success');
  });

  // Handle disconnection – show app as connected (API still works)
  socket.on('disconnect', (reason) => {
    if (reason === 'io server disconnect') {
      socket.connect();
    } else {
      showConnectionStatus('app_connected');
    }
  });

  // Handle reconnection attempts
  socket.on('reconnect_attempt', (attemptNumber) => {
    console.log(`🔄 Reconnection attempt ${attemptNumber}/${MAX_RECONNECT_ATTEMPTS}`);
    reconnectAttempts = attemptNumber;
    showConnectionStatus('reconnecting');
  });

  // Reconnection successful
  socket.on('reconnect', (attemptNumber) => {
    console.log(`✅ Reconnected after ${attemptNumber} attempts`);
    showConnectionStatus('connected');
    showNotification('Reconnected to server', 'success');
    
    // Reload data after reconnection
    if (typeof loadDashboard === 'function') {
      loadDashboard();
    }
  });

  // Reconnection failed (e.g. Socket.IO not enabled on server) – you're still connected to the app
  socket.on('reconnect_failed', () => {
    showConnectionStatus('app_connected');
  });

  // Device update event
  socket.on('device_update', (data) => {
    console.log('📱 Device update received:', data);
    handleDeviceUpdate(data);
  });

  // New alert event
  socket.on('new_alert', (data) => {
    console.log('🚨 New alert received:', data);
    handleNewAlert(data);
  });

  // Alert resolved event
  socket.on('alert_resolved', (data) => {
    console.log('✅ Alert resolved:', data);
    handleAlertResolved(data);
  });

  // System notification event
  socket.on('notification', (data) => {
    console.log('🔔 Notification:', data);
    showNotification(data.message, data.severity);
  });

  // Error handling
  socket.on('error', (error) => {
    console.error('❌ WebSocket error:', error);
  });
}

function showConnectionStatus(status) {
  const statusEl = document.querySelector('#wsStatus');
  if (!statusEl) return;

  const statusConfig = {
    connected: { text: '🟢 Live', class: 'connected', color: 'var(--ok)' },
    app_connected: { text: '🟢 Connected', class: 'connected', color: 'var(--ok)' },
    disconnected: { text: '🟢 Connected', class: 'connected', color: 'var(--ok)' },
    reconnecting: { text: '🟡 Reconnecting...', class: 'reconnecting', color: 'var(--warning)' },
    failed: { text: '🟢 Connected', class: 'connected', color: 'var(--ok)' }
  };

  const config = statusConfig[status] || statusConfig.disconnected;
  statusEl.textContent = config.text;
  statusEl.className = `ws-status ${config.class}`;
  statusEl.style.color = config.color;
}

function handleDeviceUpdate(data) {
  // Update device in the UI without full refresh
  const device = data.device;
  const deviceRow = document.querySelector(`tr[data-device-id="${device.id}"]`);
  
  if (deviceRow) {
    // Update existing row
    const statusCell = deviceRow.querySelector('.device-status');
    if (statusCell) {
      statusCell.innerHTML = badgeForStatus(device.status);
    }
  } else {
    // Device doesn't exist, reload full list
    reloadDevices();
  }

  // Show notification for status changes
  if (device.status === 'offline') {
    showNotification(`${device.name} went offline`, 'warning');
  } else if (device.status === 'online') {
    showNotification(`${device.name} is back online`, 'success');
  }
}

function handleNewAlert(data) {
  const alert = data.alert;
  
  // Show browser notification if permitted
  if (Notification.permission === 'granted') {
    new Notification('New Alert-Pro Alert', {
      body: `${alert.severity.toUpperCase()}: ${alert.message}`,
      icon: '/assets/logo.png',
      tag: alert.id
    });
  }

  // Show in-app notification
  showNotification(
    `New ${alert.severity} alert: ${alert.message}`,
    alert.severity === 'critical' || alert.severity === 'high' ? 'error' : 'warning'
  );

  // Reload alerts list
  reloadAlerts();
  
  // Play alert sound if critical
  if (alert.severity === 'critical') {
    playAlertSound();
  }
}

function handleAlertResolved(data) {
  // Update alert in UI
  const alertRow = document.querySelector(`tr[data-alert-id="${data.alert_id}"]`);
  if (alertRow) {
    alertRow.classList.add('resolved-alert');
    const actionCell = alertRow.querySelector('.alert-action');
    if (actionCell) {
      actionCell.innerHTML = '<span class="badge b-ok">Resolved</span>';
    }
  }
}

async function reloadDevices() {
  try {
    const devices = await api("/api/devices?limit=25&page=1");
    renderDevices(devices.devices || []);
  } catch (e) {
    console.error('Error reloading devices:', e);
  }
}

async function reloadAlerts() {
  try {
    const alerts = await api("/api/alerts?limit=25&page=1");
    renderAlerts(alerts.alerts || []);
  } catch (e) {
    console.error('Error reloading alerts:', e);
  }
}

function showNotification(message, severity = 'info') {
  // Create toast notification
  const toast = document.createElement('div');
  toast.className = `toast toast-${severity}`;
  toast.textContent = message;
  
  const container = document.querySelector('#toastContainer') || createToastContainer();
  container.appendChild(toast);
  
  // Animate in
  setTimeout(() => toast.classList.add('show'), 10);
  
  // Remove after 5 seconds
  setTimeout(() => {
    toast.classList.remove('show');
    setTimeout(() => toast.remove(), 300);
  }, 5000);
}

function createToastContainer() {
  const container = document.createElement('div');
  container.id = 'toastContainer';
  container.style.cssText = 'position: fixed; top: 20px; right: 20px; z-index: 9999;';
  document.body.appendChild(container);
  return container;
}

function playAlertSound() {
  // Play alert sound for critical alerts
  try {
    const audio = new Audio('/assets/alert-sound.mp3');
    audio.volume = 0.5;
    audio.play().catch(e => console.log('Could not play alert sound:', e));
  } catch (e) {
    console.log('Alert sound not available');
  }
}

function getCurrentUserId() {
  // Extract user ID from token or local storage
  const token = getToken();
  if (!token) return null;
  
  try {
    const payload = JSON.parse(atob(token.split('.')[1]));
    return payload.sub;
  } catch (e) {
    return null;
  }
}

function requestNotificationPermission() {
  if ('Notification' in window && Notification.permission === 'default') {
    Notification.requestPermission().then(permission => {
      if (permission === 'granted') {
        console.log('✅ Browser notifications enabled');
      }
    });
  }
}

// Cleanup on page unload
function disconnectWebSocket() {
  if (socket) {
    socket.disconnect();
    socket = null;
  }
}

// Export functions
window.initializeWebSocket = initializeWebSocket;
window.disconnectWebSocket = disconnectWebSocket;
window.requestNotificationPermission = requestNotificationPermission;
