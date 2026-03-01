/* Minimal frontend for the Alert-Pro API */

const API_BASE = ""; // same-origin

function qs(sel){ return document.querySelector(sel); }
function esc(s){ return String(s ?? "").replace(/[&<>"']/g, (c)=>({ "&":"&amp;","<":"&lt;",">":"&gt;","\"":"&quot;","'":"&#39;" }[c])); }
function jsString(s){ return JSON.stringify(String(s ?? "")); }

function setToken(token){
  if(token) localStorage.setItem("iot_token", token);
  else localStorage.removeItem("iot_token");
}
function getToken(){ return localStorage.getItem("iot_token"); }
function setRefreshToken(token){
  if(token) localStorage.setItem("iot_refresh_token", token);
  else localStorage.removeItem("iot_refresh_token");
}
function getRefreshToken(){ return localStorage.getItem("iot_refresh_token"); }
function clearAuth(){
  setToken(null);
  setRefreshToken(null);
}

function ensureToastContainer(){
  let container = document.querySelector(".toast-container");
  if(!container){
    container = document.createElement("div");
    container.className = "toast-container";
    document.body.appendChild(container);
  }
  return container;
}

function showToast(message, type="info", timeout=3200){
  const container = ensureToastContainer();
  const toast = document.createElement("div");
  toast.className = `toast toast-${type}`;
  toast.textContent = message;
  container.appendChild(toast);
  requestAnimationFrame(() => {
    toast.classList.add("show");
  });
  setTimeout(() => {
    toast.classList.remove("show");
    setTimeout(() => toast.remove(), 300);
  }, timeout);
}

function normalizePhone(value){
  return String(value || "").replace(/\s+/g, "");
}

function isValidE164(value){
  const cleaned = normalizePhone(value);
  return /^\+[1-9]\d{7,14}$/.test(cleaned);
}

function setButtonLoading(btn, loading, text){
  if(!btn) return;
  if(loading){
    btn.dataset.originalText = btn.textContent;
    btn.disabled = true;
    btn.textContent = text || "Working...";
  } else {
    btn.disabled = false;
    if(btn.dataset.originalText){
      btn.textContent = btn.dataset.originalText;
      delete btn.dataset.originalText;
    }
  }
}

function showSmsComplianceBanner(message){
  const banner = document.getElementById("smsComplianceBanner");
  if(!banner) return;
  banner.textContent = message;
  banner.style.display = "block";
}

function hideSmsComplianceBanner(){
  const banner = document.getElementById("smsComplianceBanner");
  if(!banner) return;
  banner.style.display = "none";
}

async function api(path, { method="GET", body, auth=true, retry=true, timeout=30000 } = {}){
  const headers = { "Content-Type": "application/json" };
  if(auth){
    const t = getToken();
    if(t) headers["Authorization"] = `Bearer ${t}`;
  }
  
  // Add timeout using AbortController
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), timeout);
  
  try {
    const res = await fetch(`${API_BASE}${path}`, {
      method,
      headers,
      body: body ? JSON.stringify(body) : undefined,
      signal: controller.signal,
    });
    clearTimeout(timeoutId);
  let data = null;
  try{ data = await res.json(); } catch {}
  if(res.status === 401 && auth && retry){
    const refreshToken = getRefreshToken();
    if(refreshToken){
      try{
        const refreshed = await api("/api/auth/refresh", {
          method: "POST",
          auth: false,
          retry: false,
          body: { refresh_token: refreshToken }
        });
        setToken(refreshed.token);
        if(refreshed.refresh_token) setRefreshToken(refreshed.refresh_token);
        return api(path, { method, body, auth, retry: false });
      }catch(e){
        clearAuth();
      }
    }
  }
  if(!res.ok){
    if(res.status === 429){
      const msg = data?.detail || "Too many requests. Please wait a moment and try again.";
      const error = new Error(msg);
      error.rateLimited = true;
      throw error;
    }
    if(data?.mfa_required){
      const error = new Error(data?.detail || "MFA required");
      error.mfa_required = true;
      throw error;
    }
    // Handle both string and object error details
    if(data?.detail && typeof data.detail === 'object'){
      // If detail is an object (like password validation errors), throw the whole object
      const error = new Error(data.detail.message || `Request failed (${res.status})`);
      error.detail = data.detail.errors || data.detail;
      if(data.detail.mfa_required){
        error.mfa_required = true;
      }
      throw error;
    }
    const msg = data?.detail || data?.message || `Request failed (${res.status})`;
    const err = new Error(msg);
    // Treat 401 or 403 (e.g. "Not authenticated" when no Bearer token) as need-to-login
    if (auth && (res.status === 401 || res.status === 403)) {
      const authMsg = (typeof msg === 'string' ? msg : msg?.message || '').toLowerCase();
      if (res.status === 401 || authMsg.includes('not authenticated') || authMsg.includes('invalid authentication') || authMsg.includes('credentials')) {
        err.unauthorized = true;
      }
    }
    throw err;
  }
  return data;
  } catch (err) {
    clearTimeout(timeoutId);
    if (err.name === 'AbortError') {
      throw new Error(`Request timed out. The server may be slow—try again.`);
    }
    throw err;
  }
}

async function loginFlow(){
  const email = qs("#email")?.value?.trim();
  const password = qs("#password")?.value;
  const mfaCodeInput = qs("#mfaCode");
  const mfaCode = mfaCodeInput?.value?.trim();
  const msg = qs("#msg");
  msg.className = "msg";
  msg.textContent = "Signing in…";
  try{
    const body = { email, password };
    if(mfaCode) body.mfa_code = mfaCode;
    const data = await api("/api/auth/login", { method:"POST", auth:false, body });
    setToken(data.token);
    if(data.refresh_token) setRefreshToken(data.refresh_token);
    msg.className = "msg ok";
    msg.textContent = "Signed in. Redirecting…";
    // Check for redirect parameter, default to dashboard
    const urlParams = new URLSearchParams(window.location.search);
    const redirect = urlParams.get('redirect') || '/dashboard';
    setTimeout(()=>{ window.location.href = redirect; }, 450);
  }catch(e){
    msg.className = "msg bad";
    const lowerMsg = String(e.message || "").toLowerCase();
    if(lowerMsg.includes("email not verified")){
      const emailValue = encodeURIComponent(email || "");
      msg.innerHTML = `Email not verified. <a href="/verify-email?email=${emailValue}" style="color: var(--primary); text-decoration: none;">Resend verification</a>`;
      showToast("Check your inbox to verify your email.", "info");
    } else if(lowerMsg.includes("temporarily locked")){
      msg.textContent = e.message;
      showToast("Account temporarily locked. Try again later.", "warning");
    } else if(e.mfa_required){
      msg.className = "msg";
      msg.textContent = e.message || "MFA required. Enter the 6-digit code from your authenticator app.";
      if(mfaCodeInput){
        const mfaField = mfaCodeInput.parentElement;
        mfaField.style.display = "block";
        mfaCodeInput.required = true;
        mfaCodeInput.focus();
      }
      showToast("Enter your MFA code to continue.", "info");
    } else {
      msg.textContent = e.message;
    }
    if(e.rateLimited){
      showToast(e.message, "warning");
    }
  }
}

function timeoutPromise(ms, label) {
  return new Promise((_, reject) =>
    setTimeout(() => reject(new Error(label || "Request timed out")), ms)
  );
}

async function loadDashboard(){
  const msg = qs("#dashmsg");
  const who = qs("#who");
  if (who) who.textContent = "Loading profile…";

  try{
    const me = await Promise.race([
      api("/api/auth/me"),
      timeoutPromise(20000, "Profile load timed out")
    ]);
    if (who) who.textContent = `${me.name} (${me.email})`;
    const wsEl = qs("#wsStatus");
    if (wsEl) { wsEl.textContent = "🟢 Connected"; wsEl.style.color = "var(--ok)"; wsEl.className = "ws-status connected"; }
  }catch(e){
    if (e && e.unauthorized) {
      clearAuth();
      const currentPath = window.location.pathname;
      window.location.href = `/login?redirect=${encodeURIComponent(currentPath)}`;
      return;
    }
    const errMsg = (e?.message || "").toLowerCase();
    if (errMsg.includes("not authenticated") || errMsg.includes("invalid authentication") || errMsg.includes("credentials")) {
      clearAuth();
      window.location.href = `/login?redirect=${encodeURIComponent(window.location.pathname)}`;
      return;
    }
    if (msg) msg.textContent = e?.message || "Failed to load. Please try again.";
    if (who) who.textContent = "Could not load profile";
    return;
  }

  if (msg) msg.textContent = "Loading…";

  try{
    const loadTimeout = 25000;
    await Promise.race([
      Promise.all([loadDevices(), loadGroups()]),
      timeoutPromise(loadTimeout, "Dashboard load timed out. Check your connection and refresh.")
    ]);
    updateLastRefreshTime();

    if (msg) msg.textContent = "";
    
    // Load alerts after page is visible (non-blocking)
    loadAlerts().catch(err => console.error("Alerts load error:", err));
    
    // Auto-expand resolved alerts section if there are resolved alerts
    const resolvedContent = qs("#resolvedAlertsContent");
    const resolvedTable = qs("#resolvedAlerts");
    if(resolvedContent && resolvedTable && resolvedTable.children.length > 0) {
      // Check if first child is not the "No resolved alerts" message
      const firstChild = resolvedTable.firstElementChild;
      if(firstChild && !firstChild.textContent.includes("No resolved alerts")) {
        resolvedContent.style.display = 'block';
        const toggle = qs("#resolvedToggle");
        if(toggle) toggle.textContent = '▼';
      }
    }
    // Prefill router IP for network scan from settings
    const scanRouterIpEl = document.getElementById('scanRouterIp');
    if (scanRouterIpEl) {
      try {
        const net = await api('/api/network-settings');
        if (net && net.router_ip) scanRouterIpEl.placeholder = net.router_ip;
        if (net && net.router_ip && !scanRouterIpEl.value) scanRouterIpEl.value = net.router_ip;
      } catch (_) {}
    }
    // Check device status after page loads (non-blocking, delayed by 5 seconds)
    setTimeout(() => {
      checkDeviceStatus().catch(err => console.log("Device status check:", err.message));
    }, 5000);
  }catch(e){
    console.error("Dashboard load error:", e);
    if (msg) {
      msg.className = "msg bad";
      msg.textContent = "Error loading dashboard: " + (e.message || "Unknown error");
    }
  }

  startAutoRefreshDashboard();
}

let dashboardAutoRefreshInterval = null;

function startAutoRefreshDashboard(){
  // Clear any existing interval
  if(dashboardAutoRefreshInterval){
    clearInterval(dashboardAutoRefreshInterval);
  }
  
  // Refresh devices and alerts every 30 seconds
  dashboardAutoRefreshInterval = setInterval(async () => {
    try {
      await Promise.all([loadDevices(), loadAlerts()]);
      updateLastRefreshTime();
    } catch(e) {
      console.error("Auto-refresh error:", e);
    }
  }, 30000); // 30 seconds
}

function stopAutoRefreshDashboard(){
  if(dashboardAutoRefreshInterval){
    clearInterval(dashboardAutoRefreshInterval);
    dashboardAutoRefreshInterval = null;
  }
}

function updateLastRefreshTime(){
  const elem = qs("#lastUpdate");
  if(elem){
    const now = new Date();
    elem.textContent = now.toLocaleTimeString();
    elem.style.color = "var(--ok)";
    setTimeout(() => { elem.style.color = "var(--text)"; }, 1000);
  }
}

// Auto-refresh dashboard every 10 seconds
let refreshInterval = null;
function startAutoRefresh(){
  if(refreshInterval) return;
  refreshInterval = setInterval(async () => {
    try{
      await Promise.all([loadDevices(), loadAlerts()]);
      updateLastRefreshTime();
    }catch(e){
      console.error("Auto-refresh error:", e);
    }
  }, 10000); // 10 seconds
}

function stopAutoRefresh(){
  if(refreshInterval){
    clearInterval(refreshInterval);
    refreshInterval = null;
  }
}

function badgeForStatus(status){
  const s = String(status || "").toLowerCase();
  if(s === "online") return `<span class="badge b-ok"><span class="dot" style="background:var(--ok);box-shadow:0 0 0 4px rgba(34,197,94,.12)"></span>online</span>`;
  if(s === "offline") return `<span class="badge b-bad"><span class="dot" style="background:var(--danger);box-shadow:0 0 0 4px rgba(239,68,68,.12)"></span>offline</span>`;
  return `<span class="badge b-warn"><span class="dot" style="background:var(--warning);box-shadow:0 0 0 4px rgba(245,158,11,.12)"></span>${esc(status)}</span>`;
}

function badgeForSeverity(sev){
  const s = String(sev || "").toLowerCase();
  if(s === "critical" || s === "high") return `badge b-bad`;
  if(s === "medium") return `badge b-warn`;
  return `badge b-ok`;
}

let deviceCache = new Map();
let editingDeviceId = null;
let devicesTableBound = false;
let deviceFilters = { search: "", type: "", status: "" };
let filterDebounce = null;
let editSnapshot = null;
let pendingDelete = null;

function formatDate(value){
  if(!value) return null;
  const d = new Date(value);
  return Number.isNaN(d.getTime()) ? null : d;
}

function formatRelativeTime(value){
  const d = formatDate(value);
  if(!d) return "Never";
  const diffMs = Date.now() - d.getTime();
  if(diffMs < 60000) return "Just now";
  const minutes = Math.floor(diffMs / 60000);
  if(minutes < 60) return `${minutes}m ago`;
  const hours = Math.floor(minutes / 60);
  if(hours < 24) return `${hours}h ago`;
  const days = Math.floor(hours / 24);
  if(days < 7) return `${days}d ago`;
  return d.toLocaleDateString();
}

function formatDateTime(value){
  const d = formatDate(value);
  return d ? d.toLocaleString() : "Never";
}

function buildDevicesQuery(){
  const params = new URLSearchParams();
  params.set("limit", "25");
  params.set("page", "1");
  if(deviceFilters.search) params.set("name", deviceFilters.search);
  if(deviceFilters.type) params.set("type", deviceFilters.type);
  if(deviceFilters.status) params.set("status", deviceFilters.status);
  return `/api/devices?${params.toString()}`;
}

async function loadDevices(){
  const data = await api(buildDevicesQuery());
  const devices = data.devices || [];
  const total = data.total != null ? data.total : devices.length;
  const countEl = document.getElementById("deviceCountSummary");
  if (countEl) countEl.textContent = total === 0 ? "Your devices: none yet" : `Your devices: ${total} registered`;
  renderDevices(devices);

  // Removed: Don't check device status on every load - it blocks page load (30+ seconds)
  // Device status will be checked after page loads via delayed call in loadDashboard()
  // checkDeviceStatus().catch(err => console.log("Device status check:", err.message));
  
  return data;
}

async function checkDeviceStatus(){
  try {
    const result = await api("/api/network/check-device-status", { method: "POST" });
    
    // If any devices were updated, reload to show new status
    if(result.updated > 0){
      console.log(`Updated ${result.updated} device(s) status`);
      // Wait a moment then reload devices
      setTimeout(() => {
        loadDevices().catch(e => console.error("Reload after status check:", e));
      }, 1000);
    }
  } catch(e) {
    // Silently fail - don't disrupt user experience
    console.log("Status check unavailable:", e.message);
  }
}

const ACTIVE_ALERTS_PAGE_SIZE = 10;
let activeAlertsPage = 1;
let activeAlertsTotal = 0;

async function loadAlerts(){
  // Load first page of active alerts (10 per page) and resolved alerts in parallel
  const results = await Promise.allSettled([
    api(`/api/alerts?limit=${ACTIVE_ALERTS_PAGE_SIZE}&page=1&resolved=false`).catch(e => {
      console.error("Failed to load unresolved alerts:", e);
      return { alerts: [], total: 0, page: 1 };
    }),
    api("/api/alerts?limit=100&page=1&resolved=true").catch(e => {
      console.error("Failed to load resolved alerts:", e);
      return { alerts: [] };
    })
  ]);
  
  const unresolvedData = results[0].status === 'fulfilled' ? results[0].value : { alerts: [], total: 0, page: 1 };
  const resolvedData = results[1].status === 'fulfilled' ? results[1].value : { alerts: [] };
  
  activeAlertsPage = unresolvedData.page || 1;
  activeAlertsTotal = unresolvedData.total != null ? unresolvedData.total : (unresolvedData.alerts || []).length;
  const unresolvedAlerts = unresolvedData.alerts || [];
  const resolvedAlerts = resolvedData.alerts || [];
  
  renderAlerts(unresolvedAlerts);
  renderResolvedAlerts(resolvedAlerts);
  renderActiveAlertsPagination(activeAlertsTotal, activeAlertsPage);
  
  return { alerts: unresolvedAlerts };
}

async function loadActiveAlertsPage(page){
  if (page < 1) page = 1;
  try {
    const data = await api(`/api/alerts?limit=${ACTIVE_ALERTS_PAGE_SIZE}&page=${page}&resolved=false`);
    const alerts = data.alerts || [];
    activeAlertsPage = data.page != null ? data.page : page;
    activeAlertsTotal = data.total != null ? data.total : alerts.length;
    renderAlerts(alerts);
    renderActiveAlertsPagination(activeAlertsTotal, activeAlertsPage);
  } catch (e) {
    console.error("Failed to load alerts page:", e);
  }
}

function renderActiveAlertsPagination(total, page){
  const totalPages = Math.max(1, Math.ceil(total / ACTIVE_ALERTS_PAGE_SIZE));
  const start = total === 0 ? 0 : (page - 1) * ACTIVE_ALERTS_PAGE_SIZE + 1;
  const end = total === 0 ? 0 : Math.min(page * ACTIVE_ALERTS_PAGE_SIZE, total);
  const html = total === 0
    ? ""
    : `<span><strong>Showing ${start}&ndash;${end} of ${total}</strong> active alert${total !== 1 ? "s" : ""} (10 per page)</span>
       <div class="pagination-buttons">
         <button class="btn-sm" ${page <= 1 ? "disabled" : ""} onclick="window.loadActiveAlertsPage(${page - 1})">← Previous</button>
         <span style="min-width: 100px; text-align: center;">Page ${page} of ${totalPages}</span>
         <button class="btn-sm" ${page >= totalPages ? "disabled" : ""} onclick="window.loadActiveAlertsPage(${page + 1})">Next →</button>
       </div>`;
  const el = qs("#activeAlertsPagination");
  const elTop = qs("#activeAlertsPaginationTop");
  if (el) el.innerHTML = html;
  if (elTop) elTop.innerHTML = html;
}
window.loadActiveAlertsPage = loadActiveAlertsPage;

function scheduleDeviceFilterUpdate(){
  if(filterDebounce) clearTimeout(filterDebounce);
  filterDebounce = setTimeout(() => {
    loadDevices().catch((e) => console.error("Device filter error:", e));
  }, 250);
}

function renderDevices(devs){
  const tbody = qs("#devices");
  const allOfflineBanner = qs("#allOfflineBanner");
  if(!tbody) return;
  if(!devs.length){
    tbody.innerHTML = `<tr><td colspan="8" class="hint">No devices yet.</td></tr>`;
    if(allOfflineBanner) allOfflineBanner.style.display = "none";
    return;
  }
  const allOffline = devs.every(d => (d.status || "").toLowerCase() === "offline");
  if(allOfflineBanner) allOfflineBanner.style.display = allOffline ? "block" : "none";
  deviceCache = new Map(devs.map(d => [d.device_id, d]));
  
  // Filter by group if selected
  let filteredDevs = devs;
  if (currentGroupFilter) {
    filteredDevs = devs.filter(d => {
      const deviceGroups = d.groups || [];
      return deviceGroups.some(g => String(g) === currentGroupFilter);
    });
  }
  
  if (!filteredDevs.length && currentGroupFilter) {
    tbody.innerHTML = `<tr><td colspan="8" class="hint">No devices in this group.</td></tr>`;
    return;
  }
  
  tbody.innerHTML = filteredDevs.map(d => {
    // Get group names for this device
    const deviceGroups = d.groups || [];
    const groupBadges = deviceGroups.map(gId => {
      const group = allGroups.find(g => g.id === String(gId));
      if (group) {
        return `<span class="badge" style="background: ${esc(group.color)}; margin-right: 4px;">${esc(group.name)}</span>`;
      }
      return '';
    }).filter(b => b).join('');
    
    return `
    <tr data-device-id="${d.id || d._id}" data-device-key="${esc(d.device_id)}">
      <td>${esc(d.device_id)}</td>
      <td>${esc(d.name)}</td>
      <td>${esc(d.type)}</td>
      <td>${groupBadges || '<span class="hint">No groups</span>'}</td>
      <td>${esc(d.router_ip || d.routerIp || 'Not set')}</td>
      <td class="device-status">${badgeForStatus(d.status)}</td>
      <td>${esc(formatRelativeTime(d.last_seen))}</td>
      <td>
        <div style="display:flex; gap:6px; flex-wrap:wrap;">
          <button class="btn-sm" data-action="edit" data-device-id="${esc(d.device_id)}">Edit</button>
          <button class="btn-sm danger" data-action="delete" data-device-id="${esc(d.device_id)}" data-device-name="${esc(d.name)}">Delete</button>
        </div>
      </td>
    </tr>
  `;
  }).join("");

  if(!devicesTableBound){
    devicesTableBound = true;
    tbody.addEventListener("click", (e) => {
      const btn = e.target.closest("button[data-action]");
      if(btn){
        const action = btn.dataset.action;
        const deviceId = btn.dataset.deviceId;
        const deviceName = btn.dataset.deviceName;
        if(action === "edit"){
          showEditDeviceForm(deviceId);
        } else if(action === "delete"){
          deleteDevice(deviceId, deviceName);
        }
        return;
      }

      const row = e.target.closest("tr[data-device-key]");
      if(!row) return;
      const deviceId = row.dataset.deviceKey;
      if(deviceId){
        const device = deviceCache.get(deviceId);
        if(device) openDevicePanel(device);
      }
    });
  }
}

function renderAlerts(alerts){
  const tbody = qs("#alerts");
  if(!tbody) return;
  
  // Only show unresolved alerts in the main table
  const unresolvedAlerts = alerts.filter(a => !a.resolved);
  
  if(!unresolvedAlerts.length){
    tbody.innerHTML = `<tr><td colspan="6" class="hint">No active alerts. All clear! 🎉</td></tr>`;
    return;
  }
  
  // Action column first so Resolve is always visible without horizontal scroll
  const html = unresolvedAlerts.map(a => `
    <tr class="alert-row" data-alert-id="${a.id || a._id}">
      <td class="alert-action"><button class="btn-sm" onclick="resolveAlert('${a.id}')">Resolve</button></td>
      <td><span class="${badgeForSeverity(a.severity)}">${esc(a.severity)}</span></td>
      <td>${esc(a.type)}</td>
      <td>${esc(a.message)}</td>
      <td>${a.device?.name ? esc(a.device.name) : esc(a.device_id)}</td>
      <td>${esc((a.created_at || "").toString().slice(0,19).replace("T"," "))}</td>
    </tr>
  `).join("");
  
  tbody.innerHTML = html;
}

// Render resolved alerts in a separate section
function renderResolvedAlerts(alerts){
  const tbody = qs("#resolvedAlerts");
  if(!tbody) return;
  
  const resolvedAlerts = alerts.filter(a => a.resolved);
  
  if(!resolvedAlerts.length){
    tbody.innerHTML = `<tr><td colspan="6" class="hint">No resolved alerts yet.</td></tr>`;
    return;
  }
  
  // Show resolved alerts with resolved date
  const html = resolvedAlerts.map(a => `
    <tr class="resolved-alert" data-alert-id="${a.id || a._id}">
      <td><span class="${badgeForSeverity(a.severity)}" style="opacity: 0.7;">${esc(a.severity)}</span></td>
      <td>${esc(a.type)}</td>
      <td>${esc(a.message)}</td>
      <td>${a.device?.name ? esc(a.device.name) : esc(a.device_id)}</td>
      <td>${esc((a.created_at || "").toString().slice(0,19).replace("T"," "))}</td>
      <td class="alert-action">
        <span class="badge b-ok">Resolved</span>
        ${a.resolved_at ? `<div style="font-size: 11px; color: var(--muted); margin-top: 4px;">${esc((a.resolved_at || "").toString().slice(0,19).replace("T"," "))}</div>` : ''}
      </td>
    </tr>
  `).join("");
  
  tbody.innerHTML = html;
  
  // Update resolved count
  const countElement = qs("#resolvedAlertsCount");
  if(countElement) {
    countElement.textContent = `(${resolvedAlerts.length})`;
  }
}

async function resolveAlert(alertId){
  const msg = qs("#dashmsg");
  const alertRow = document.querySelector(`tr[data-alert-id="${alertId}"]`);
  
  try{
    msg.textContent = "Resolving alert...";
    await api(`/api/alerts/${alertId}/resolve`, { method: "POST" });
    
    // Remove the alert from the active alerts table immediately
    if(alertRow){
      alertRow.remove();
    }
    
    msg.className = "msg ok";
    msg.textContent = "Alert resolved!";
    setTimeout(() => { msg.textContent = ""; msg.className = "msg"; }, 2000);
    
    // Reload current page of active alerts and resolved section
    await loadActiveAlertsPage(activeAlertsPage);
    const resolvedData = await api("/api/alerts?limit=100&page=1&resolved=true").catch(() => ({ alerts: [] }));
    renderResolvedAlerts(resolvedData.alerts || []);
    
    // Show resolved alerts section if it was hidden
    const resolvedContent = qs("#resolvedAlertsContent");
    if(resolvedContent && !resolvedContent.style.display || resolvedContent.style.display === 'none') {
      resolvedContent.style.display = 'block';
      const toggle = qs("#resolvedToggle");
      if(toggle) toggle.textContent = '▼';
    }
  }catch(e){
    msg.className = "msg bad";
    msg.textContent = "Failed to resolve alert: " + e.message;
    console.error("Resolve alert error:", e);
  }
}

function logout(){
  const refreshToken = getRefreshToken();
  api("/api/auth/logout", {
    method: "POST",
    body: refreshToken ? { refresh_token: refreshToken } : {},
    auth: true,
    retry: false
  }).catch(() => {});
  clearAuth();
  window.location.href = "/";
}

// Resolved alerts section toggle
function toggleResolvedAlerts(){
  const content = document.getElementById('resolvedAlertsContent');
  const toggle = document.getElementById('resolvedToggle');
  if(!content || !toggle) return;
  
  if(content.style.display === 'none' || !content.style.display){
    content.style.display = 'block';
    toggle.textContent = '▼';
  } else {
    content.style.display = 'none';
    toggle.textContent = '▶';
  }
}

// Device form functions
function setDeviceFormMode(mode, device = null){
  const title = document.getElementById('deviceFormTitle');
  const submitBtn = document.getElementById('deviceSubmitBtn');
  const deviceIdInput = document.getElementById('device_id');
  const hint = document.getElementById('deviceFormHint');

  if(mode === "edit" && device){
    editingDeviceId = device.device_id;
    const deviceIpVal = (device.device_ip || device.deviceIp || device.ip_address || "").trim();
    const routerIpVal = (device.router_ip || device.routerIp || "").trim();
    editSnapshot = {
      name: device.name || "",
      type: device.type || "",
      device_ip: deviceIpVal,
      router_ip: routerIpVal,
      heartbeat_interval: device.heartbeat_interval || 30,
      alerts_enabled: device.alerts_enabled !== false,
      offline_only_when_missed_heartbeats: device.offline_only_when_missed_heartbeats === true,
      offline_after_seconds: device.offline_after_seconds != null ? device.offline_after_seconds : null
    };
    if(title) title.textContent = "Edit Device";
    if(submitBtn) submitBtn.textContent = "Save Changes";
    if(deviceIdInput){
      deviceIdInput.value = device.device_id || "";
      deviceIdInput.readOnly = true;
      deviceIdInput.style.background = "var(--surface)";
      deviceIdInput.style.color = "var(--muted)";
    }

    document.getElementById('device_name').value = device.name || "";
    document.getElementById('device_type').value = device.type || "";
    document.getElementById('device_heartbeat').value = device.heartbeat_interval || 30;
    document.getElementById('device_alerts').checked = device.alerts_enabled !== false;
    const heartbeatOnlyEl = document.getElementById('device_heartbeat_only_offline');
    if (heartbeatOnlyEl) heartbeatOnlyEl.checked = device.offline_only_when_missed_heartbeats === true;
    const offlineAfterEl = document.getElementById('device_offline_after_sec');
    if (offlineAfterEl) offlineAfterEl.value = device.offline_after_seconds != null ? String(device.offline_after_seconds) : '';
    document.getElementById('router_ip_display').value = device.router_ip || device.routerIp || "";
    const deviceIpEl = document.getElementById('device_ip');
    if(deviceIpEl) deviceIpEl.value = device.device_ip || device.deviceIp || "";
    if(hint) hint.textContent = "Make changes to enable Save.";
    setDeviceSubmitEnabled(false);
    return;
  }

  editingDeviceId = null;
  editSnapshot = null;
  if(title) title.textContent = "Add New Device";
  if(submitBtn) submitBtn.textContent = "Add Device";
  if(deviceIdInput){
    deviceIdInput.readOnly = false;
    deviceIdInput.style.background = "var(--bg)";
    deviceIdInput.style.color = "var(--text)";
  }
  if(hint) hint.textContent = "";
  setDeviceSubmitEnabled(true);
}

async function showAddDeviceForm(){
  const form = document.getElementById('addDeviceForm');
  if(form) {
    form.style.display = 'block';
    form.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    setDeviceFormMode("add");
    document.getElementById('device_id').value = '';
    document.getElementById('device_name').value = '';
    document.getElementById('device_type').value = '';
    const deviceIpEl = document.getElementById('device_ip');
    if(deviceIpEl) deviceIpEl.value = '';
    document.getElementById('device_heartbeat').value = '30';
    document.getElementById('device_alerts').checked = true;
    const heartbeatOnlyEl = document.getElementById('device_heartbeat_only_offline');
    if (heartbeatOnlyEl) heartbeatOnlyEl.checked = false;
    const offlineAfterEl = document.getElementById('device_offline_after_sec');
    if (offlineAfterEl) offlineAfterEl.value = '';
    
    // Load router IP and auto-fill
    try {
      const settings = await api("/api/network-settings");
      if(settings.router_ip) {
        document.getElementById('router_ip_display').value = settings.router_ip;
        document.getElementById('routerIpSetup').style.display = 'none';
      } else {
        document.getElementById('routerIpSetup').style.display = 'block';
      }
    } catch(e) {
      console.error("Failed to load network settings:", e);
      document.getElementById('routerIpSetup').style.display = 'block';
    }
  }
}

window.refreshDiscoveredDevices = async function(){
  const listEl = document.getElementById('discoveredDevicesList');
  const updatedEl = document.getElementById('discoveryUpdated');
  const btn = document.getElementById('refreshDiscoveredBtn');
  if(!listEl) return;
  if(btn) { btn.disabled = true; btn.textContent = 'Loading...'; }
  try {
    const res = await api("/api/discovery");
    if(updatedEl && res.updated_at) {
      const d = new Date(res.updated_at);
      updatedEl.textContent = 'Last discovery: ' + d.toLocaleString();
    } else if(updatedEl) updatedEl.textContent = '';
    if(!res.devices || res.devices.length === 0) {
      listEl.innerHTML = '<span class="hint">No devices found yet. Run the device agent in discovery mode on a computer on your network (see agent README), then click Refresh again.</span>';
    } else {
      listEl.innerHTML = res.devices.map(d => {
        const host = (d.hostname || '').replace(/"/g, '&quot;');
        return `<div style="display: flex; align-items: center; justify-content: space-between; padding: 10px 12px; margin-bottom: 6px; background: var(--bg); border-radius: 6px; border: 1px solid var(--border);">
          <div><strong>${esc(d.ip)}</strong>${d.hostname ? ' <span class="hint">(' + esc(d.hostname) + ')</span>' : ''}</div>
          <button type="button" class="btn-sm discover-add-btn" data-ip="${esc(d.ip)}" data-hostname="${host}" style="background: var(--ok); color: white;">Add to my devices</button>
        </div>`;
      }).join('');
      listEl.querySelectorAll('.discover-add-btn').forEach(btn => {
        btn.addEventListener('click', () => addDeviceFromDiscovery(btn.dataset.ip, btn.dataset.hostname || btn.dataset.ip));
      });
    }
  } catch(e) {
    listEl.innerHTML = '<span class="msg bad">Could not load discovery: ' + (e.message || 'Unknown error') + '</span>';
    if(updatedEl) updatedEl.textContent = '';
  }
  if(btn) { btn.disabled = false; btn.textContent = 'Refresh discovered devices'; }
};

window.addDeviceFromDiscovery = async function(ip, hostname){
  const name = (hostname && hostname !== ip) ? hostname : ('Device ' + ip.replace(/\./g, '-'));
  const deviceId = 'device-' + ip.replace(/\./g, '-');
  const form = document.getElementById('addDeviceForm');
  const hintEl = document.getElementById('deviceFormHint');
  if(form) {
    form.style.display = 'block';
    form.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
  }
  setDeviceFormMode("add");
  document.getElementById('device_id').value = deviceId;
  document.getElementById('device_name').value = name;
  document.getElementById('device_type').value = 'Other';
  const deviceIpEl = document.getElementById('device_ip');
  if(deviceIpEl) deviceIpEl.value = ip;
  if(hintEl) {
    hintEl.textContent = 'You can rename the device above before adding.';
    hintEl.className = 'hint';
    hintEl.style.marginTop = '8px';
  }
  setTimeout(function(){ document.getElementById('device_name').focus(); }, 300);
  try {
    const settings = await api("/api/network-settings");
    if(settings.router_ip) document.getElementById('router_ip_display').value = settings.router_ip;
  } catch(_) {}
};

window.showChangeRouterIp = function() {
  const setup = document.getElementById('routerIpSetup');
  const display = document.getElementById('router_ip_display');
  const input = document.getElementById('router_ip');
  if (setup && input) {
    if (display && display.value) input.value = display.value;
    setup.style.display = 'block';
    input.focus();
  }
};

async function saveRouterIp(){
  const routerIp = document.getElementById('router_ip').value.trim();
  if(!routerIp) {
    showToast("Please enter your router IP address", "error");
    return;
  }
  
  // Validate IP format
  const ipPattern = /^(?:[0-9]{1,3}\.){3}[0-9]{1,3}$/;
  if(!ipPattern.test(routerIp)) {
    showToast("Please enter a valid IP address (e.g., 192.168.1.1)", "error");
    return;
  }
  
  try {
    await api("/api/network-settings", {
      method: "PUT",
      body: { router_ip: routerIp }
    });
    
    document.getElementById('routerIpSetup').style.display = 'none';
    
    // Update router IP display
    const routerIpDisplay = document.getElementById('router_ip_display');
    if(routerIpDisplay) {
      routerIpDisplay.value = routerIp;
    }
    
    showToast("Router IP saved! You can now scan for devices.", "success");
    
    // Optionally trigger scan automatically
    setTimeout(() => {
      if(typeof scanNetworkForDevices === 'function') {
        scanNetworkForDevices();
      }
    }, 1000);
  } catch(e) {
    showToast("Failed to save router IP: " + (e.message || "Unknown error"), "error");
  }
}

// New improved network scan function for the enhanced UI (exposed on window for onclick)
window.scanNetworkForDevices = async function scanNetworkForDevices(){
  const scanBtn = document.getElementById('scanNetworkBtn');
  const resultsDiv = document.getElementById('networkScanResults');
  const statusDiv = document.getElementById('networkScanStatus');
  const devicesList = document.getElementById('networkScanDevicesList');

  function setStatus(html) {
    if (statusDiv) statusDiv.innerHTML = html;
    else if (typeof showToast === 'function') showToast(html.replace(/<[^>]+>/g, '').trim(), 'info');
  }
  function setList(html) {
    if (devicesList) devicesList.innerHTML = html;
  }
  function showResults() {
    if (resultsDiv) resultsDiv.style.display = 'block';
  }

  const routerIpInput = document.getElementById('scanRouterIp');
  const routerIp = routerIpInput ? routerIpInput.value.trim() : '';
  const url = routerIp ? `/api/network/scan-devices?router_ip=${encodeURIComponent(routerIp)}` : '/api/network/scan-devices';

  showResults();
  setStatus('<span style="color: var(--primary);">Scanning network thoroughly... This will take 1-2 minutes to ensure all devices are found.</span>');
  setList('');
  if(scanBtn) {
    scanBtn.disabled = true;
    scanBtn.textContent = 'Scanning...';
  }

  try {
    // Scan can take 1–2 minutes (253 IPs); use a long timeout so the request doesn't abort
    const result = await api(url, { timeout: 150000 });

    if(result.error === 'no_router_ip') {
      setStatus('<span style="color: var(--danger);">Enter your router IP above (e.g. 192.168.1.1) and click Scan.</span>');
      setList('<p style="color: var(--muted); font-size: 14px;">Or set a default in <a href="/settings">Settings</a>.</p>');
      return;
    }
    if(result.error === 'invalid_router_ip') {
      setStatus('<span style="color: var(--danger);">Invalid router IP. Use format like 192.168.1.1</span>');
      setList('');
      return;
    }
    if(result.error === 'scan_failed') {
      setStatus(`<span style="color: var(--danger);">${esc(result.message || 'Scan failed')}</span>`);
      setList('<p style="color: var(--muted); font-size: 14px; margin-top: 8px;">Check that your router IP is correct and this PC can reach the network (e.g. open Command Prompt and run: <code>ping ' + esc(result.router_ip || '192.168.1.1') + '</code>).</p>');
      return;
    }

    if(result.devices && result.devices.length > 0) {
      setStatus(`<span style="color: var(--ok); font-weight: 500;">Found ${result.devices.length} device(s)</span>`);
      setList(result.devices.map(device => {
        const name = device.hostname || '—';
        const mac = device.mac || '—';
        const deviceType = device.device_type || 'Other';
        const typeIcon = {
          'Doorbell': '🔔',
          'Camera': '📷',
          'Router': '📡',
          'Smart Speaker': '🔊',
          'Thermostat': '🌡️',
          'Smart TV': '📺',
          'Sensor': '📡',
          'Smart Home Hub': '🏠',
          'Smart Plug': '🔌',
          'Other': '📱'
        }[deviceType] || '📱';
        return `
          <div style="display: flex; align-items: center; justify-content: space-between; padding: 12px; margin-bottom: 8px; background: var(--bg); border-radius: 6px; border: 1px solid var(--border);">
            <div style="flex: 1; min-width: 0;">
              <div style="font-weight: 500; margin-bottom: 4px;">${esc(device.ip)}${deviceType !== 'Other' ? ' <span style="background: var(--primary); color: white; padding: 2px 6px; border-radius: 4px; font-size: 11px; margin-left: 6px;">' + typeIcon + ' ' + esc(deviceType) + '</span>' : ''}</div>
              <div style="font-size: 12px; color: var(--muted);">
                Name: ${esc(name)}${mac !== '—' ? ' • MAC: ' + esc(mac) : ''}
              </div>
            </div>
            <button type="button" class="btn-sm" onclick="addDeviceFromScan('${esc(device.ip)}', '${esc(name === '—' ? '' : name)}', '${esc(deviceType)}')" style="background: var(--ok); color: white; border: none; cursor: pointer; padding: 8px 16px; border-radius: 6px; font-weight: 500; flex-shrink: 0;">
              Add
            </button>
          </div>
        `;
      }).join(''));
    } else {
      const scanned = result.ips_scanned ? ` Scanned ${result.ips_scanned} IPs.` : '';
      setStatus('<span style="color: var(--warning);">No devices found.' + scanned + '</span>');
      setList('<p style="color: var(--muted); font-size: 14px; margin-top: 8px;"><strong>Tips:</strong><br>1) Confirm router IP (run <code>ipconfig</code> → Default Gateway).<br>2) Some devices sleep/don\'t respond—run scan again or check your router\'s device list.<br>3) If devices don\'t appear, add them manually with their IP.</p>');
    }
  } catch(e) {
    const errMsg = e.message || 'Unknown error';
    setStatus(`<span style="color: var(--danger);">Scan failed: ${esc(errMsg)}</span>`);
    setList('');
    if (typeof showToast === 'function') showToast('Scan failed: ' + errMsg, 'error');
  }

  if(scanBtn) {
    scanBtn.disabled = false;
    scanBtn.textContent = 'Scan network';
  }
};

// Bulk add devices by IP list (one IP per line)
window.bulkAddDevicesByIp = async function() {
  const textarea = document.getElementById('bulkAddIps');
  const statusEl = document.getElementById('bulkAddStatus');
  const btn = document.getElementById('bulkAddBtn');
  if(!textarea || !statusEl) return;
  const raw = textarea.value.trim();
  const lines = raw.split(/\r?\n/).map(l => l.trim()).filter(Boolean);
  const ipPattern = /^(?:[0-9]{1,3}\.){3}[0-9]{1,3}$/;
  const ips = lines.filter(l => ipPattern.test(l));
  if(ips.length === 0) {
    statusEl.textContent = 'Enter at least one valid IP address (one per line).';
    statusEl.style.color = 'var(--danger)';
    return;
  }
  
  // Try to get router IP from multiple sources
  let routerIp = null;
  const scanRouterIpEl = document.getElementById('scanRouterIp');
  if(scanRouterIpEl && scanRouterIpEl.value) routerIp = scanRouterIpEl.value.trim();
  if(!routerIp) {
    const routerIpDisplay = document.getElementById('router_ip_display');
    if(routerIpDisplay && routerIpDisplay.value) routerIp = routerIpDisplay.value.trim();
  }
  if(!routerIp) {
    try {
      const settings = await api("/api/network-settings");
      routerIp = settings.router_ip;
    } catch(e) {}
  }
  if(!routerIp) {
    statusEl.textContent = 'Enter Router IP in the scan box above first, or set it in Settings.';
    statusEl.style.color = 'var(--danger)';
    return;
  }
  
  if(btn) { btn.disabled = true; btn.textContent = 'Adding...'; }
  statusEl.textContent = `Adding ${ips.length} device(s)...`;
  statusEl.style.color = 'var(--primary)';
  let added = 0, failed = 0;
  const errors = [];
  for(const ip of ips) {
    const name = 'Device ' + ip.replace(/\./g, '-');
    try {
      await api("/api/devices", {
        method: "POST",
        body: { name, type: "Other", device_ip: ip, router_ip: routerIp, alerts_enabled: true }
      });
      added++;
    } catch(e) {
      failed++;
      errors.push(`${ip}: ${e.message || 'failed'}`);
    }
  }
  if(btn) { btn.disabled = false; btn.textContent = 'Add all'; }
  
  if(added > 0 && failed === 0) {
    statusEl.textContent = `✓ Added ${added} device(s).`;
    statusEl.style.color = 'var(--ok)';
    textarea.value = '';
    loadDashboard();
  } else if(added > 0 && failed > 0) {
    statusEl.textContent = `Added ${added}, ${failed} failed (may already exist or invalid). Check console for details.`;
    statusEl.style.color = 'var(--warning)';
    console.log('Bulk add errors:', errors);
    loadDashboard();
  } else {
    statusEl.textContent = `All ${failed} failed. ${errors[0] || 'May already exist or router IP issue.'}`;
    statusEl.style.color = 'var(--danger)';
    console.log('Bulk add errors:', errors);
  }
};

// Add device from network scan results
window.addDeviceFromScan = function(ip, hostname, deviceType) {
  deviceType = deviceType || 'Other';
  const name = (hostname && hostname !== 'Unknown' && hostname !== ip) ? hostname : ('Device ' + ip.replace(/\./g, '-'));
  const deviceId = 'device-' + ip.replace(/\./g, '-');
  
  // Show add device form
  showAddDeviceForm();
  
  // Pre-fill form
  setDeviceFormMode("add");
  document.getElementById('device_id').value = deviceId;
  document.getElementById('device_name').value = name;
  document.getElementById('device_type').value = deviceType;
  const deviceIpEl = document.getElementById('device_ip');
  if(deviceIpEl) deviceIpEl.value = ip;
  
  const hintEl = document.getElementById('deviceFormHint');
  if(hintEl) {
    hintEl.textContent = `Device details pre-filled from scan${deviceType !== 'Other' ? ' (detected as ' + deviceType + ')' : ''}. You can rename or change the type before adding.`;
    hintEl.className = 'hint';
    hintEl.style.marginTop = '8px';
  }
  
  // Focus name field for easy editing
  setTimeout(() => {
    const nameField = document.getElementById('device_name');
    if(nameField) {
      nameField.focus();
      nameField.select();
    }
  }, 300);
  
  // Scroll to form
  const form = document.getElementById('addDeviceForm');
  if(form) {
    form.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
  }
};

// Show/hide discovery script info section
window.showDiscoveryScriptInfo = function() {
  const infoDiv = document.getElementById('discoveryScriptInfo');
  if(infoDiv) {
    if(infoDiv.style.display === 'none' || !infoDiv.style.display) {
      infoDiv.style.display = 'block';
      refreshDiscoveredDevices(); // Load discovered devices when showing
    } else {
      infoDiv.style.display = 'none';
    }
  }
};

// Legacy function for backward compatibility
async function scanForDevices(){
  // Redirect to new function
  await scanNetworkForDevices();
}

function selectDetectedDevice(ip, hostname){
  document.getElementById('device_ip').value = ip;
  if(hostname && hostname !== 'Unknown' && !document.getElementById('device_name').value) {
    document.getElementById('device_name').value = hostname;
  }
  document.getElementById('detectedDevices').style.display = 'none';
  verifyDeviceConnection();
}

async function verifyDeviceConnection(){
  const ip = document.getElementById('device_ip').value.trim();
  const statusDiv = document.getElementById('deviceIpStatus');
  
  if(!ip) {
    statusDiv.innerHTML = '<span style="color: var(--warning);">Please enter an IP address first</span>';
    return;
  }
  
  // Validate IP format
  const ipPattern = /^(?:[0-9]{1,3}\.){3}[0-9]{1,3}$/;
  if(!ipPattern.test(ip)) {
    statusDiv.innerHTML = '<span style="color: var(--danger);">Invalid IP address format</span>';
    return;
  }
  
  statusDiv.innerHTML = '<span style="color: var(--primary);">Testing connection...</span>';
  
  try {
    const result = await api(`/api/network/verify-device?ip_address=${encodeURIComponent(ip)}`);
    
    if(result.verified && result.reachable) {
      statusDiv.innerHTML = `<span style="color: var(--ok);">✓ Device is reachable and on your network${result.hostname ? ` (${result.hostname})` : ''}</span>`;
    } else if(result.same_network && !result.reachable) {
      statusDiv.innerHTML = `<span style="color: var(--warning);">⚠️ Device is on your network but not currently reachable. Make sure it's powered on.</span>`;
    } else if(!result.same_network) {
      statusDiv.innerHTML = `<span style="color: var(--danger);">⚠️ WARNING: Device is NOT on your network! This may be a security risk.</span>`;
    } else {
      statusDiv.innerHTML = '<span style="color: var(--danger);">✗ Connection test failed</span>';
    }
  } catch(e) {
    statusDiv.innerHTML = `<span style="color: var(--danger);">✗ Test failed: ${e.message}</span>`;
  }
}

function hideAddDeviceForm(){
  const form = document.getElementById('addDeviceForm');
  if(form) {
    form.style.display = 'none';
    // Clear form
    document.getElementById('device_id').value = '';
    document.getElementById('device_name').value = '';
    document.getElementById('device_type').value = '';
    const deviceIpEl = document.getElementById('device_ip');
    if(deviceIpEl) deviceIpEl.value = '';
    document.getElementById('device_heartbeat').value = '30';
    document.getElementById('device_alerts').checked = true;
    // Router IP stays filled (readonly)
    setDeviceFormMode("add");
  }
}

function showEditDeviceForm(deviceId){
  const device = deviceCache.get(deviceId);
  if(!device){
    alert("Device not found in the current list. Please refresh.");
    return;
  }

  const form = document.getElementById('addDeviceForm');
  if(form) {
    form.style.display = 'block';
    form.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    setDeviceFormMode("edit", device);
  }
}

async function submitDeviceForm(event){
  event.preventDefault();
  const msg = qs("#dashmsg");
  const submitBtn = event.target.querySelector('button[type="submit"]');
  
  const deviceIdEl = document.getElementById('device_id');
  const deviceId = deviceIdEl ? deviceIdEl.value.trim() : '';
  const name = document.getElementById('device_name').value.trim();
  const type = document.getElementById('device_type').value;
  const routerIp = document.getElementById('router_ip_display').value;
  const deviceIpEl = document.getElementById('device_ip');
  const deviceIp = deviceIpEl ? deviceIpEl.value.trim() : null;
  const heartbeatInterval = parseInt(document.getElementById('device_heartbeat').value) || 30;
  const alertsEnabled = document.getElementById('device_alerts').checked;
  const heartbeatOnlyOffline = document.getElementById('device_heartbeat_only_offline') && document.getElementById('device_heartbeat_only_offline').checked;
  const offlineAfterSecEl = document.getElementById('device_offline_after_sec');
  const offlineAfterSec = offlineAfterSecEl && offlineAfterSecEl.value.trim() !== '' ? parseInt(offlineAfterSecEl.value, 10) : null;
  const offlineAfterSeconds = (offlineAfterSec != null && !isNaN(offlineAfterSec) && offlineAfterSec >= 30 && offlineAfterSec <= 300) ? offlineAfterSec : null;

  // Validation: name, type, and router IP (from settings) required; device_id is optional
  if(!name || !type || !routerIp) {
    if(msg) {
      msg.className = "msg bad";
      msg.textContent = "Please enter name, type, and set Router IP in Settings if you haven't.";
    }
    return;
  }
  
  try{
    if(msg) {
      msg.textContent = editingDeviceId ? "Saving changes..." : "Adding device...";
      msg.className = "msg";
    }
    
    if(submitBtn) {
      submitBtn.disabled = true;
      submitBtn.textContent = editingDeviceId ? "Saving..." : "Adding...";
    }

    if(editingDeviceId){
      await api(`/api/devices/${encodeURIComponent(editingDeviceId)}`, {
        method: "PATCH",
        body: {
          name,
          type,
          device_ip: (deviceIp && deviceIp.trim()) ? deviceIp.trim() : null,
          router_ip: (routerIp && routerIp.trim()) ? routerIp.trim() : null,
          heartbeat_interval: heartbeatInterval,
          alerts_enabled: alertsEnabled,
          offline_only_when_missed_heartbeats: heartbeatOnlyOffline,
          offline_after_seconds: offlineAfterSeconds
        }
      });

      if(msg) {
        msg.className = "msg ok";
        msg.textContent = `Device "${name}" updated successfully!`;
      }
      editSnapshot = null;
    } else {
      const deviceData = {
        name,
        type,
        router_ip: routerIp,
        device_ip: deviceIp || null,
        heartbeat_interval: heartbeatInterval,
        alerts_enabled: alertsEnabled,
        offline_only_when_missed_heartbeats: heartbeatOnlyOffline,
        offline_after_seconds: offlineAfterSeconds
      };
      if(deviceId) deviceData.device_id = deviceId;

      await api("/api/devices", {
        method: "POST",
        body: deviceData
      });

      if(msg) {
        msg.className = "msg ok";
        msg.textContent = `Device "${name}" added successfully!`;
      }
    }

    // Hide form and reload devices
    hideAddDeviceForm();
    
    // Reload dashboard
    setTimeout(() => {
      loadDashboard();
      if(msg) msg.textContent = "";
    }, 1000);
    
  }catch(e){
    if(msg) {
      msg.className = "msg bad";
      msg.textContent = (editingDeviceId ? "Failed to update device: " : "Failed to add device: ") + (e.message || e.detail || "Unknown error");
    }
    console.error("Device submit error:", e);
    
    // Re-enable button
    if(submitBtn) {
      submitBtn.disabled = false;
      submitBtn.textContent = editingDeviceId ? "Save Changes" : "Add Device";
    }
  }
}

function deleteDevice(deviceId, deviceName){
  openDeleteModal(deviceId, deviceName);
}

function setDeviceSubmitEnabled(enabled){
  const btn = document.getElementById('deviceSubmitBtn');
  if(btn) btn.disabled = !enabled;
}

function getDeviceFormState(){
  const deviceIpEl = document.getElementById('device_ip');
  const routerIpEl = document.getElementById('router_ip_display');
  const heartbeatOnlyEl = document.getElementById('device_heartbeat_only_offline');
  return {
    name: document.getElementById('device_name').value.trim(),
    type: document.getElementById('device_type').value,
    device_ip: (deviceIpEl && deviceIpEl.value) ? deviceIpEl.value.trim() : "",
    router_ip: (routerIpEl && routerIpEl.value) ? routerIpEl.value.trim() : "",
    heartbeat_interval: parseInt(document.getElementById('device_heartbeat').value) || 30,
    alerts_enabled: document.getElementById('device_alerts').checked,
    offline_only_when_missed_heartbeats: heartbeatOnlyEl ? heartbeatOnlyEl.checked : false,
    offline_after_seconds: (() => {
      const el = document.getElementById('device_offline_after_sec');
      if (!el || el.value.trim() === '') return null;
      const n = parseInt(el.value, 10);
      return (!isNaN(n) && n >= 30 && n <= 300) ? n : null;
    })()
  };
}

function refreshDeviceFormState(){
  if(!editingDeviceId || !editSnapshot){
    setDeviceSubmitEnabled(true);
    return;
  }
  const current = getDeviceFormState();
  const isDirty = Object.keys(editSnapshot).some((key) => editSnapshot[key] !== current[key]);
  const hint = document.getElementById('deviceFormHint');
  if(hint) hint.textContent = isDirty ? "" : "No changes to save.";
  setDeviceSubmitEnabled(isDirty);
}

function openDevicePanel(device){
  const overlay = document.getElementById('deviceDrawerOverlay');
  const panel = document.getElementById('deviceDetailPanel');
  if(!overlay || !panel) return;

  document.getElementById('deviceDetailName').textContent = device.name || "Device";
  document.getElementById('deviceDetailId').textContent = `ID: ${device.device_id || ""}`;
  document.getElementById('deviceDetailStatus').innerHTML = badgeForStatus(device.status);
  document.getElementById('deviceDetailLastSeen').textContent = `${formatRelativeTime(device.last_seen)} • ${formatDateTime(device.last_seen)}`;
  document.getElementById('deviceDetailType').textContent = device.type || "—";
  document.getElementById('deviceDetailRouterIp').textContent = device.router_ip || device.routerIp || "—";
  document.getElementById('deviceDetailDeviceIp').textContent = device.device_ip || device.ip_address || "—";
  document.getElementById('deviceDetailHeartbeat').textContent = `${device.heartbeat_interval || 30}s`;
  document.getElementById('deviceDetailAlerts').textContent = device.alerts_enabled === false ? "Disabled" : "Enabled";
  document.getElementById('deviceDetailSignal').textContent = device.signal_strength != null ? `${device.signal_strength} dBm` : "—";

  const editBtn = document.getElementById('deviceDetailEdit');
  const deleteBtn = document.getElementById('deviceDetailDelete');
  if(editBtn) editBtn.dataset.deviceId = device.device_id;
  if(deleteBtn){
    deleteBtn.dataset.deviceId = device.device_id;
    deleteBtn.dataset.deviceName = device.name || device.device_id;
  }

  // Update device groups section
  updateDeviceGroupsDisplay(device);

  overlay.classList.add('show');
  panel.classList.add('show');
  overlay.setAttribute('aria-hidden', 'false');
  panel.setAttribute('aria-hidden', 'false');
}

// Update device groups display in detail panel
function updateDeviceGroupsDisplay(device) {
  const groupsContainer = document.getElementById('deviceDetailGroups');
  const addGroupSelect = document.getElementById('deviceDetailAddGroup');
  if (!groupsContainer || !addGroupSelect) return;
  
  const deviceGroups = device.groups || [];
  const deviceId = device.id || device._id;
  
  // Show current groups
  if (deviceGroups.length > 0) {
    const groupBadges = deviceGroups.map(gId => {
      const group = allGroups.find(g => g.id === String(gId));
      if (group) {
        return `
          <span class="badge" style="background: ${esc(group.color)}; display: inline-flex; align-items: center; gap: 6px; margin-right: 6px; margin-bottom: 6px;">
            ${esc(group.name)}
            <button onclick="removeDeviceFromGroup('${group.id}', '${deviceId}', '${esc(device.name || device.device_id)}')" 
                    style="background: transparent; border: none; color: inherit; cursor: pointer; padding: 0 4px; font-size: 14px; line-height: 1;">×</button>
          </span>
        `;
      }
      return '';
    }).filter(b => b).join('');
    
    groupsContainer.innerHTML = `<div style="display: flex; flex-wrap: wrap; gap: 6px;">${groupBadges}</div>`;
  } else {
    groupsContainer.innerHTML = '<div class="hint" style="font-size: 13px;">No groups assigned</div>';
  }
  
  // Update dropdown with groups not already assigned
  const groupsNotAssigned = allGroups.filter(g => !deviceGroups.some(dg => String(dg) === g.id));
  addGroupSelect.innerHTML = '<option value="">Add to group...</option>' +
    groupsNotAssigned.map(g => `<option value="${g.id}">${esc(g.name)}</option>`).join('');
  
  // Add event listener for adding device to group
  addGroupSelect.onchange = async function() {
    const groupId = this.value;
    if (groupId) {
      await addDeviceToGroup(groupId, deviceId);
      this.value = ''; // Reset dropdown
      // Reload device data to refresh groups
      await loadDevices();
      const updatedDevice = Array.from(deviceCache.values()).find(d => (d.id || d._id) === deviceId || d.device_id === deviceId);
      if (updatedDevice && typeof updateDeviceGroupsDisplay === 'function') {
        updateDeviceGroupsDisplay(updatedDevice);
      }
    }
  };
}

function closeDevicePanel(){
  const overlay = document.getElementById('deviceDrawerOverlay');
  const panel = document.getElementById('deviceDetailPanel');
  if(!overlay || !panel) return;
  overlay.classList.remove('show');
  panel.classList.remove('show');
  overlay.setAttribute('aria-hidden', 'true');
  panel.setAttribute('aria-hidden', 'true');
}

function openDeleteModal(deviceId, deviceName){
  const overlay = document.getElementById('deleteModalOverlay');
  const input = document.getElementById('deleteConfirmInput');
  const confirmBtn = document.getElementById('deleteModalConfirm');
  const deviceLabel = document.getElementById('deleteModalDevice');
  if(!overlay || !input || !confirmBtn || !deviceLabel) return;

  pendingDelete = { deviceId, deviceName: deviceName || deviceId };
  deviceLabel.textContent = pendingDelete.deviceName;
  input.value = "";
  confirmBtn.disabled = true;
  overlay.classList.add('show');
  overlay.setAttribute('aria-hidden', 'false');
  input.focus();
}

function closeDeleteModal(){
  const overlay = document.getElementById('deleteModalOverlay');
  if(!overlay) return;
  overlay.classList.remove('show');
  overlay.setAttribute('aria-hidden', 'true');
  pendingDelete = null;
}

async function confirmDeleteDevice(){
  if(!pendingDelete) return;
  const msg = qs("#dashmsg");
  const { deviceId, deviceName } = pendingDelete;

  try{
    if(msg){
      msg.className = "msg";
      msg.textContent = `Deleting "${deviceName}"...`;
    }

    await api(`/api/devices/${encodeURIComponent(deviceId)}`, { method: "DELETE" });

    if(msg){
      msg.className = "msg ok";
      msg.textContent = `Device "${deviceName}" deleted successfully!`;
    }

    if(editingDeviceId === deviceId){
      hideAddDeviceForm();
    }

    closeDeleteModal();
    closeDevicePanel();

    setTimeout(() => {
      loadDashboard();
      if(msg) msg.textContent = "";
    }, 1000);
  }catch(e){
    if(msg){
      msg.className = "msg bad";
      msg.textContent = "Failed to delete device: " + (e.message || "Unknown error");
    }
  }
}

async function manualRefresh(){
  const msg = qs("#dashmsg");
  const btn = event.target.closest('button');
  
  // Disable button and show loading
  if(btn){
    btn.disabled = true;
    btn.innerHTML = '<span style="display: inline-block; margin-right: 6px;">⏳</span>Refreshing...';
  }
  
  try{
    msg.textContent = "Refreshing...";
    // Use allSettled so one failing request (e.g. timeout) doesn't break the whole refresh
    const [devicesResult, alertsResult] = await Promise.allSettled([
      loadDevices(),
      loadAlerts()
    ]);
    const devicesOk = devicesResult.status === 'fulfilled';
    const alertsOk = alertsResult.status === 'fulfilled';
    if (devicesOk || alertsOk) {
      updateLastRefreshTime();
    }
    if (devicesOk && alertsOk) {
      msg.textContent = "✅ Refreshed successfully!";
      setTimeout(() => { msg.textContent = ""; }, 2000);
    } else if (devicesOk || alertsOk) {
      msg.className = "msg";
      msg.textContent = "⚠️ Partially refreshed. " + (devicesOk ? "Devices loaded." : "Alerts loaded.") + " One request timed out.";
      setTimeout(() => { msg.textContent = ""; msg.className = "msg"; }, 4000);
    } else {
      const err = devicesResult.reason || alertsResult.reason;
      msg.className = "msg bad";
      msg.textContent = "❌ Refresh failed: " + (err && err.message ? err.message : "Request failed or timed out.");
    }
  }catch(e){
    msg.className = "msg bad";
    msg.textContent = "❌ Refresh failed: " + e.message;
  }finally{
    // Re-enable button
    if(btn){
      btn.disabled = false;
      btn.innerHTML = '<span style="display: inline-block; margin-right: 6px;">🔄</span>Refresh';
    }
  }
}

// Page wiring
window.addEventListener("DOMContentLoaded", () => {
  if(qs("#loginForm")){
    qs("#loginForm").addEventListener("submit", (e)=>{ e.preventDefault(); loginFlow(); });
    const msg = qs("#msg");
    const params = new URLSearchParams(window.location.search);
    if(msg && params.get("reset") === "success"){
      msg.className = "msg ok";
      msg.textContent = "Password reset successful. Please sign in.";
    }
  }
  if(qs("#logoutBtn")){
    qs("#logoutBtn").addEventListener("click", logout);
  }
  if(qs("#dashboardRoot")){
    loadDashboard();
    // Ensure Scan Network button works (fallback if inline onclick doesn't run)
    const scanNetworkBtn = document.getElementById('scanNetworkBtn');
    if(scanNetworkBtn && typeof window.scanNetworkForDevices === 'function'){
      scanNetworkBtn.addEventListener('click', window.scanNetworkForDevices);
    }
    // Always start auto-refresh as backup
    startAutoRefresh();
    // Initialize WebSocket for real-time updates (if available)
    if(typeof initializeWebSocket === 'function'){
      initializeWebSocket();
      // Request browser notification permission
      if(typeof requestNotificationPermission === 'function'){
        requestNotificationPermission();
      }
    }

    const searchInput = document.getElementById('deviceSearch');
    const typeFilter = document.getElementById('deviceTypeFilter');
    const statusFilter = document.getElementById('deviceStatusFilter');
    const clearFilters = document.getElementById('clearDeviceFilters');

    if(searchInput){
      searchInput.addEventListener('input', () => {
        deviceFilters.search = searchInput.value.trim();
        scheduleDeviceFilterUpdate();
      });
    }
    if(typeFilter){
      typeFilter.addEventListener('change', () => {
        deviceFilters.type = typeFilter.value;
        scheduleDeviceFilterUpdate();
      });
    }
    if(statusFilter){
      statusFilter.addEventListener('change', () => {
        deviceFilters.status = statusFilter.value;
        scheduleDeviceFilterUpdate();
      });
    }
    if(clearFilters){
      clearFilters.addEventListener('click', () => {
        deviceFilters = { search: "", type: "", status: "" };
        if(searchInput) searchInput.value = "";
        if(typeFilter) typeFilter.value = "";
        if(statusFilter) statusFilter.value = "";
        loadDevices().catch((e) => console.error("Device filter error:", e));
      });
    }

    ['device_name', 'device_type', 'device_ip', 'router_ip_display', 'device_heartbeat', 'device_alerts', 'device_offline_after_sec', 'device_heartbeat_only_offline'].forEach((id) => {
      const el = document.getElementById(id);
      if(el){
        el.addEventListener('input', refreshDeviceFormState);
        el.addEventListener('change', refreshDeviceFormState);
      }
    });

    const drawerOverlay = document.getElementById('deviceDrawerOverlay');
    const closeDrawerBtn = document.getElementById('closeDevicePanel');
    const detailEdit = document.getElementById('deviceDetailEdit');
    const detailDelete = document.getElementById('deviceDetailDelete');
    if(drawerOverlay){
      drawerOverlay.addEventListener('click', closeDevicePanel);
    }
    if(closeDrawerBtn){
      closeDrawerBtn.addEventListener('click', closeDevicePanel);
    }
    if(detailEdit){
      detailEdit.addEventListener('click', () => {
        const deviceId = detailEdit.dataset.deviceId;
        if(deviceId){
          closeDevicePanel();
          showEditDeviceForm(deviceId);
        }
      });
    }
    if(detailDelete){
      detailDelete.addEventListener('click', () => {
        const deviceId = detailDelete.dataset.deviceId;
        const deviceName = detailDelete.dataset.deviceName;
        if(deviceId){
          openDeleteModal(deviceId, deviceName);
        }
      });
    }

    const deleteOverlay = document.getElementById('deleteModalOverlay');
    const deleteCancel = document.getElementById('deleteModalCancel');
    const deleteConfirm = document.getElementById('deleteModalConfirm');
    const deleteInput = document.getElementById('deleteConfirmInput');
    if(deleteOverlay){
      deleteOverlay.addEventListener('click', (e) => {
        if(e.target === deleteOverlay) closeDeleteModal();
      });
    }
    if(deleteCancel){
      deleteCancel.addEventListener('click', closeDeleteModal);
    }
    if(deleteInput && deleteConfirm){
      deleteInput.addEventListener('input', () => {
        deleteConfirm.disabled = deleteInput.value.trim().toUpperCase() !== "DELETE";
      });
    }
    if(deleteConfirm){
      deleteConfirm.addEventListener('click', confirmDeleteDevice);
    }

    document.addEventListener('keydown', (e) => {
      if(e.key === "Escape"){
        closeDeleteModal();
        closeDevicePanel();
      }
    });
  }
});

// Export functions
async function exportAlertsPDF() {
  const btn = event.target;
  btn.disabled = true;
  btn.textContent = '⏳ Generating PDF...';
  
  try {
    const response = await fetch('/api/alerts/export/pdf?days=30', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${getToken()}`
      }
    });
    
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Export failed');
    }
    
    // Download the file
    const blob = await response.blob();
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `alerts_report_${new Date().toISOString().slice(0,10)}.pdf`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    window.URL.revokeObjectURL(url);
    
    btn.textContent = '✅ Downloaded!';
    setTimeout(() => {
      btn.disabled = false;
      btn.textContent = '📄 Export PDF';
    }, 2000);
  } catch (error) {
    alert('Export failed: ' + error.message);
    btn.disabled = false;
    btn.textContent = '📄 Export PDF';
  }
}

async function exportAlertsCSV() {
  const btn = event.target;
  btn.disabled = true;
  btn.textContent = '⏳ Generating CSV...';
  
  try {
    const response = await fetch('/api/alerts/export/csv?days=30', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${getToken()}`
      }
    });
    
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Export failed');
    }
    
    // Download the file
    const blob = await response.blob();
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `alerts_export_${new Date().toISOString().slice(0,10)}.csv`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    window.URL.revokeObjectURL(url);
    
    btn.textContent = '✅ Downloaded!';
    setTimeout(() => {
      btn.disabled = false;
      btn.textContent = '📊 Export CSV';
    }, 2000);
  } catch (error) {
    alert('Export failed: ' + error.message);
    btn.disabled = false;
    btn.textContent = '📊 Export CSV';
  }
}

// ============================================================
// DEVICE GROUP MANAGEMENT
// ============================================================

let allGroups = [];
let currentGroupFilter = null;

// Load groups and populate filter dropdown
async function loadGroups() {
  try {
    allGroups = await api('/api/groups');
    const filterSelect = qs('#groupFilter');
    if (filterSelect) {
      filterSelect.innerHTML = '<option value="">All Devices</option>' +
        allGroups.map(g => `<option value="${g.id}">${esc(g.name)} (${g.device_count})</option>`).join('');
      if (currentGroupFilter) {
        filterSelect.value = currentGroupFilter;
      }
    }
    renderGroupsList();
  } catch (e) {
    console.error('Failed to load groups:', e);
  }
}

// Render groups list in management panel
function renderGroupsList() {
  const container = qs('#groupsList');
  if (!container) return;
  
  if (allGroups.length === 0) {
    container.innerHTML = '<div class="hint">No groups yet. Create one to get started!</div>';
    return;
  }
  
  // Get all devices for the dropdown
  const allDevices = Array.from(deviceCache.values());
  
  container.innerHTML = allGroups.map(group => {
    // Get devices in this group
    const devicesInGroup = allDevices.filter(d => {
      const deviceGroups = d.groups || [];
      return deviceGroups.some(g => String(g) === group.id);
    });
    
    // Get devices NOT in this group
    const devicesNotInGroup = allDevices.filter(d => {
      const deviceGroups = d.groups || [];
      return !deviceGroups.some(g => String(g) === group.id);
    });
    
    return `
    <div class="card" style="margin-bottom: 16px; padding: 16px;">
      <div style="display: flex; justify-content: space-between; align-items: start; margin-bottom: 12px;">
        <div style="flex: 1;">
          <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 4px;">
            <span style="display: inline-block; width: 16px; height: 16px; border-radius: 4px; background: ${esc(group.color)};"></span>
            <strong>${esc(group.name)}</strong>
            <span class="badge" style="background: var(--muted);">${devicesInGroup.length} device${devicesInGroup.length !== 1 ? 's' : ''}</span>
          </div>
          ${group.description ? `<div style="color: var(--muted); font-size: 14px; margin-top: 4px;">${esc(group.description)}</div>` : ''}
        </div>
        <div style="display: flex; gap: 4px;">
          <button class="btn-sm" onclick="deleteGroup('${group.id}')" style="background: var(--danger); color: white;">Delete</button>
        </div>
      </div>
      
      <!-- Devices in Group -->
      <div style="margin-top: 12px; padding-top: 12px; border-top: 1px solid var(--border);">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
          <strong style="font-size: 14px;">Devices in Group</strong>
          ${devicesNotInGroup.length > 0 ? `
            <select id="addDeviceToGroup_${group.id}" style="padding: 6px 10px; border-radius: 4px; border: 1px solid var(--border); background: var(--bg); color: var(--text); font-size: 13px; min-width: 150px;">
              <option value="">Add device...</option>
              ${devicesNotInGroup.map(d => `<option value="${d.id || d._id}" data-device-name="${esc(d.name || d.device_id)}">${esc(d.name || d.device_id)}</option>`).join('')}
            </select>
          ` : ''}
        </div>
        ${devicesInGroup.length > 0 ? `
          <div style="display: flex; flex-wrap: wrap; gap: 6px; margin-bottom: 8px;">
            ${devicesInGroup.map(d => `
              <span class="badge" style="background: ${esc(group.color)}; display: inline-flex; align-items: center; gap: 4px;">
                ${esc(d.name || d.device_id)}
                <button onclick="removeDeviceFromGroup('${group.id}', '${d.id || d._id}', '${esc(d.name || d.device_id)}')" 
                        style="background: transparent; border: none; color: inherit; cursor: pointer; padding: 0 4px; font-size: 14px; line-height: 1;">×</button>
              </span>
            `).join('')}
          </div>
        ` : '<div class="hint" style="font-size: 13px;">No devices in this group</div>'}
      </div>
    </div>
  `;
  }).join('');
  
  // Add event listeners for device selection dropdowns
  allGroups.forEach(group => {
    const select = document.getElementById(`addDeviceToGroup_${group.id}`);
    if (select) {
      // Remove existing listener if any
      select.onchange = null;
      select.addEventListener('change', async (e) => {
        const deviceId = e.target.value;
        if (deviceId) {
          const selectedOption = e.target.options[e.target.selectedIndex];
          const deviceName = selectedOption ? selectedOption.text : 'device';
          await addDeviceToGroup(group.id, deviceId);
          e.target.value = ''; // Reset dropdown
        }
      });
    }
  });
}

// Show group management panel (make it globally accessible)
window.showGroupManagement = function() {
  const overlay = document.getElementById('groupModalOverlay');
  const panel = document.getElementById('groupManagementPanel');
  if (!overlay || !panel) {
    console.error('Group management modal elements not found', { overlay, panel });
    if (typeof showToast === 'function') {
      showToast('Group management panel not found. Please refresh the page.', 'error');
    } else {
      alert('Group management panel not found. Please refresh the page.');
    }
    return;
  }
  
  // Show overlay and panel
  overlay.style.display = 'block';
  panel.style.display = 'flex';
  
  // Use requestAnimationFrame to ensure display is applied before animation
  requestAnimationFrame(() => {
    // Add show class for animation
    overlay.classList.add('show');
    panel.classList.add('show');
  });
  
  // Prevent body scroll when modal is open
  document.body.style.overflow = 'hidden';
  
  // Load groups if function exists
  if (typeof loadGroups === 'function') {
    loadGroups();
  }
}

// Hide group management panel (make it globally accessible)
window.hideGroupManagement = function() {
  const overlay = document.getElementById('groupModalOverlay');
  const panel = document.getElementById('groupManagementPanel');
  if (!overlay || !panel) return;
  
  // Remove show class to trigger animation
  overlay.classList.remove('show');
  panel.classList.remove('show');
  
  // Hide after animation completes (CSS transition is 0.25s = 250ms)
  setTimeout(() => {
    overlay.style.display = 'none';
    panel.style.display = 'none';
  }, 300);
  
  // Restore body scroll
  document.body.style.overflow = '';
  
  if (typeof hideCreateGroupForm === 'function') {
    hideCreateGroupForm();
  }
}

// Show create group form (make globally accessible)
window.showCreateGroupForm = function() {
  const form = document.querySelector('#createGroupForm');
  if (form) form.style.display = 'block';
}

// Hide create group form (make globally accessible)
window.hideCreateGroupForm = function() {
  const form = document.querySelector('#createGroupForm');
  if (form) {
    form.style.display = 'none';
    const nameInput = document.querySelector('#groupName');
    const descInput = document.querySelector('#groupDescription');
    const colorInput = document.querySelector('#groupColor');
    if (nameInput) nameInput.value = '';
    if (descInput) descInput.value = '';
    if (colorInput) colorInput.value = '#3b82f6';
  }
}

// Create new group (make globally accessible)
window.createGroup = async function(event) {
  event.preventDefault();
  const nameInput = document.querySelector('#groupName');
  const descInput = document.querySelector('#groupDescription');
  const colorInput = document.querySelector('#groupColor');
  
  if (!nameInput) return;
  
  const name = nameInput.value.trim();
  const description = descInput ? descInput.value.trim() : '';
  const color = colorInput ? colorInput.value : '#3b82f6';
  
  if (!name) {
    if (typeof showToast === 'function') {
      showToast('Group name is required', 'error');
    } else {
      alert('Group name is required');
    }
    return;
  }
  
  try {
    await api('/api/groups', {
      method: 'POST',
      body: {
        name,
        description: description || undefined,
        color
      }
    });
    if (typeof showToast === 'function') {
      showToast('Group created successfully', 'success');
    }
    hideCreateGroupForm();
    if (typeof loadGroups === 'function') {
      await loadGroups();
    }
  } catch (e) {
    if (typeof showToast === 'function') {
      showToast('Failed to create group: ' + (e.message || 'Unknown error'), 'error');
    } else {
      alert('Failed to create group: ' + (e.message || 'Unknown error'));
    }
  }
}

// Delete group (make globally accessible)
window.deleteGroup = async function(groupId) {
  if (!confirm('Are you sure you want to delete this group? Devices will be removed from the group.')) {
    return;
  }
  
  try {
    await api(`/api/groups/${groupId}`, { method: 'DELETE' });
    if (typeof showToast === 'function') {
      showToast('Group deleted successfully', 'success');
    }
    if (typeof loadGroups === 'function') {
      await loadGroups();
    }
    if (currentGroupFilter === groupId) {
      currentGroupFilter = null;
      if (typeof filterDevicesByGroup === 'function') {
        filterDevicesByGroup();
      }
    }
    if (typeof loadDevices === 'function') {
      await loadDevices();
    }
  } catch (e) {
    if (typeof showToast === 'function') {
      showToast('Failed to delete group: ' + (e.message || 'Unknown error'), 'error');
    } else {
      alert('Failed to delete group: ' + (e.message || 'Unknown error'));
    }
  }
}

// Add device to group (make globally accessible)
window.addDeviceToGroup = async function(groupId, deviceId) {
  try {
    // deviceId should be MongoDB _id (from device.id or device._id)
    // If it's device_id, we need to find the device first
    let actualDeviceId = deviceId;
    let device = null;
    
    // Check if it's already a MongoDB _id by checking deviceCache
    device = Array.from(deviceCache.values()).find(d => (d.id || d._id) === deviceId);
    if (device) {
      actualDeviceId = device.id || device._id;
    } else {
      // Try to find by device_id
      device = Array.from(deviceCache.values()).find(d => d.device_id === deviceId);
      if (device) {
        actualDeviceId = device.id || device._id;
      } else {
        // deviceId might already be the MongoDB _id
        actualDeviceId = deviceId;
      }
    }
    
    await api(`/api/groups/${groupId}/devices/${actualDeviceId}`, { method: 'POST' });
    if (typeof showToast === 'function') {
      showToast('Device added to group', 'success');
    }
    // Reload devices and groups to refresh the UI
    await Promise.all([loadDevices(), loadGroups()]);
    
    // Update device detail panel if open
    const panel = document.getElementById('deviceDetailPanel');
    if (panel && panel.classList.contains('show')) {
      const currentDevice = device || Array.from(deviceCache.values()).find(d => (d.id || d._id) === actualDeviceId);
      if (currentDevice && typeof updateDeviceGroupsDisplay === 'function') {
        updateDeviceGroupsDisplay(currentDevice);
      }
    }
  } catch (e) {
    console.error('Failed to add device to group:', e);
    if (typeof showToast === 'function') {
      showToast('Failed to add device to group: ' + (e.message || 'Unknown error'), 'error');
    } else {
      alert('Failed to add device to group: ' + (e.message || 'Unknown error'));
    }
  }
}

// Remove device from group (make globally accessible)
window.removeDeviceFromGroup = async function(groupId, deviceId, deviceName) {
  if (!confirm(`Remove "${deviceName}" from this group?`)) {
    return;
  }
  try {
    // deviceId should be MongoDB _id (from device.id or device._id)
    // If it's device_id, we need to find the device first
    let actualDeviceId = deviceId;
    let device = null;
    
    // Check if it's already a MongoDB _id by checking deviceCache
    device = Array.from(deviceCache.values()).find(d => (d.id || d._id) === deviceId);
    if (device) {
      actualDeviceId = device.id || device._id;
    } else {
      // Try to find by device_id
      device = Array.from(deviceCache.values()).find(d => d.device_id === deviceId);
      if (device) {
        actualDeviceId = device.id || device._id;
      } else {
        // deviceId might already be the MongoDB _id
        actualDeviceId = deviceId;
      }
    }
    
    await api(`/api/groups/${groupId}/devices/${actualDeviceId}`, { method: 'DELETE' });
    if (typeof showToast === 'function') {
      showToast('Device removed from group', 'success');
    }
    // Reload devices and groups to refresh the UI
    await Promise.all([loadDevices(), loadGroups()]);
    
    // Update device detail panel if open
    const panel = document.getElementById('deviceDetailPanel');
    if (panel && panel.classList.contains('show')) {
      const currentDevice = device || Array.from(deviceCache.values()).find(d => (d.id || d._id) === actualDeviceId);
      if (currentDevice && typeof updateDeviceGroupsDisplay === 'function') {
        updateDeviceGroupsDisplay(currentDevice);
      }
    }
  } catch (e) {
    console.error('Failed to remove device from group:', e);
    if (typeof showToast === 'function') {
      showToast('Failed to remove device from group: ' + (e.message || 'Unknown error'), 'error');
    } else {
      alert('Failed to remove device from group: ' + (e.message || 'Unknown error'));
    }
  }
}

// Filter devices by group (make globally accessible)
window.filterDevicesByGroup = function() {
  const filterSelect = document.querySelector('#groupFilter');
  if (filterSelect) {
    currentGroupFilter = filterSelect.value || null;
    if (typeof loadDevices === 'function') {
      loadDevices(); // Reload devices with filter
    }
  }
}

async function manualRefreshStatus(){
  const btn = event?.target;
  if(btn) {
    btn.disabled = true;
    btn.textContent = "🔄 Checking...";
  }
  
  try {
    const result = await api("/api/network/check-device-status", { method: "POST" });
    
    if(result.updated > 0){
      showToast(`Updated ${result.updated} device(s) - reloading...`, "success");
      await loadDevices();
    } else {
      showToast("All devices up to date", "info");
    }
  } catch(e) {
    showToast("Status check failed: " + e.message, "error");
  } finally {
    if(btn) {
      btn.disabled = false;
      btn.textContent = "🔄 Refresh Status";
    }
  }
}

// Clean up on page unload
window.addEventListener("beforeunload", () => {
  stopAutoRefresh();
  stopAutoRefreshDashboard();
  if(typeof disconnectWebSocket === 'function'){
    disconnectWebSocket();
  }
});
