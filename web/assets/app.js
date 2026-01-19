/* Minimal frontend for the IoT Security Platform API */

const API_BASE = ""; // same-origin

function qs(sel){ return document.querySelector(sel); }
function esc(s){ return String(s ?? "").replace(/[&<>"']/g, (c)=>({ "&":"&amp;","<":"&lt;",">":"&gt;","\"":"&quot;","'":"&#39;" }[c])); }
function jsString(s){ return JSON.stringify(String(s ?? "")); }

function setToken(token){
  if(token) localStorage.setItem("iot_token", token);
  else localStorage.removeItem("iot_token");
}
function getToken(){ return localStorage.getItem("iot_token"); }

async function api(path, { method="GET", body, auth=true } = {}){
  const headers = { "Content-Type": "application/json" };
  if(auth){
    const t = getToken();
    if(t) headers["Authorization"] = `Bearer ${t}`;
  }
  const res = await fetch(`${API_BASE}${path}`, {
    method,
    headers,
    body: body ? JSON.stringify(body) : undefined,
  });
  let data = null;
  try{ data = await res.json(); } catch {}
  if(!res.ok){
    // Handle both string and object error details
    if(data?.detail && typeof data.detail === 'object'){
      // If detail is an object (like password validation errors), throw the whole object
      const error = new Error(data.detail.message || `Request failed (${res.status})`);
      error.detail = data.detail.errors || data.detail;
      throw error;
    }
    const msg = data?.detail || data?.message || `Request failed (${res.status})`;
    throw new Error(msg);
  }
  return data;
}

async function loginFlow(){
  const email = qs("#email")?.value?.trim();
  const password = qs("#password")?.value;
  const msg = qs("#msg");
  msg.className = "msg";
  msg.textContent = "Signing in…";
  try{
    const data = await api("/api/auth/login", { method:"POST", auth:false, body:{ email, password } });
    setToken(data.token);
    msg.className = "msg ok";
    msg.textContent = "Signed in. Redirecting…";
    setTimeout(()=>{ window.location.href = "/dashboard"; }, 450);
  }catch(e){
    msg.className = "msg bad";
    msg.textContent = e.message;
  }
}

async function loadDashboard(){
  const msg = qs("#dashmsg");
  const who = qs("#who");

  try{
    const me = await api("/api/auth/me");
    if (who) who.textContent = `${me.name} (${me.email})`;
  }catch(e){
    // Not logged in
    setToken(null);
    window.location.href = "/login";
    return;
  }

  if (msg) msg.textContent = "Loading…";

  try{
    await Promise.all([loadDevices(), loadAlerts()]);
    updateLastRefreshTime();

    if (msg) msg.textContent = "";
  }catch(e){
    console.error("Dashboard load error:", e);
    if (msg) {
      msg.className = "msg bad";
      msg.textContent = "Error loading dashboard: " + (e.message || "Unknown error");
    }
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
  renderDevices(data.devices || []);
  return data;
}

async function loadAlerts(){
  const data = await api("/api/alerts?limit=25&page=1");
  renderAlerts(data.alerts || []);
  return data;
}

function scheduleDeviceFilterUpdate(){
  if(filterDebounce) clearTimeout(filterDebounce);
  filterDebounce = setTimeout(() => {
    loadDevices().catch((e) => console.error("Device filter error:", e));
  }, 250);
}

function renderDevices(devs){
  const tbody = qs("#devices");
  if(!tbody) return;
  if(!devs.length){
    tbody.innerHTML = `<tr><td colspan="7" class="hint">No devices yet.</td></tr>`;
    return;
  }
  deviceCache = new Map(devs.map(d => [d.device_id, d]));
  tbody.innerHTML = devs.map(d => `
    <tr data-device-id="${d.id || d._id}" data-device-key="${esc(d.device_id)}">
      <td>${esc(d.device_id)}</td>
      <td>${esc(d.name)}</td>
      <td>${esc(d.type)}</td>
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
  `).join("");

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
  
  // Filter out resolved alerts or show them dimmed
  const unresolvedAlerts = alerts.filter(a => !a.resolved);
  const resolvedAlerts = alerts.filter(a => a.resolved);
  
  if(!alerts.length){
    tbody.innerHTML = `<tr><td colspan="6" class="hint">No alerts yet.</td></tr>`;
    return;
  }
  
  // Render unresolved alerts first
  let html = unresolvedAlerts.map(a => `
    <tr class="alert-row" data-alert-id="${a.id || a._id}">
      <td><span class="${badgeForSeverity(a.severity)}">${esc(a.severity)}</span></td>
      <td>${esc(a.type)}</td>
      <td>${esc(a.message)}</td>
      <td>${a.device?.name ? esc(a.device.name) : esc(a.device_id)}</td>
      <td>${esc((a.created_at || "").toString().slice(0,19).replace("T"," "))}</td>
      <td class="alert-action">
        <button class="btn-sm" onclick="resolveAlert('${a.id}')">Resolve</button>
      </td>
    </tr>
  `).join("");
  
  // Optionally show resolved alerts (dimmed)
  if(resolvedAlerts.length > 0){
    html += `<tr class="resolved-alerts-header"><td colspan="6" style="padding: 8px; font-weight: 600; color: var(--muted); font-size: 12px; border-top: 1px solid var(--border);">Resolved (${resolvedAlerts.length})</td></tr>`;
    html += resolvedAlerts.slice(0, 5).map(a => `
      <tr class="resolved-alert" data-alert-id="${a.id || a._id}" style="opacity: 0.6;">
        <td><span class="${badgeForSeverity(a.severity)}">${esc(a.severity)}</span></td>
        <td>${esc(a.type)}</td>
        <td>${esc(a.message)}</td>
        <td>${a.device?.name ? esc(a.device.name) : esc(a.device_id)}</td>
        <td>${esc((a.created_at || "").toString().slice(0,19).replace("T"," "))}</td>
        <td class="alert-action">
          <span class="badge b-ok">Resolved</span>
        </td>
      </tr>
    `).join("");
  }
  
  tbody.innerHTML = html;
}

async function resolveAlert(alertId){
  const msg = qs("#dashmsg");
  const alertRow = document.querySelector(`tr[data-alert-id="${alertId}"]`);
  
  try{
    msg.textContent = "Resolving alert...";
    await api(`/api/alerts/${alertId}/resolve`, { method: "POST" });
    
    // Immediately hide/update the alert in UI
    if(alertRow){
      alertRow.classList.add('resolved-alert');
      const actionCell = alertRow.querySelector('.alert-action');
      if(actionCell){
        actionCell.innerHTML = '<span class="badge b-ok">Resolved</span>';
      }
      // Optionally fade out and remove after a delay
      setTimeout(() => {
        alertRow.style.opacity = '0.5';
        alertRow.style.transition = 'opacity 0.3s';
      }, 500);
    }
    
    msg.className = "msg ok";
    msg.textContent = "Alert resolved!";
    setTimeout(() => { msg.textContent = ""; msg.className = "msg"; }, 2000);
    
    // Reload alerts to refresh the list
    const alerts = await api("/api/alerts?limit=25&page=1");
    renderAlerts(alerts.alerts || []);
  }catch(e){
    msg.className = "msg bad";
    msg.textContent = "Failed to resolve alert: " + e.message;
    console.error("Resolve alert error:", e);
  }
}

function logout(){
  setToken(null);
  window.location.href = "/";
}

// Alerts section toggle
function toggleAlertsSection(){
  const content = document.getElementById('alertsContent');
  const toggle = document.getElementById('alertsToggle');
  if(content.style.display === 'none'){
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
    editSnapshot = {
      name: device.name || "",
      type: device.type || "",
      heartbeat_interval: device.heartbeat_interval || 30,
      alerts_enabled: device.alerts_enabled !== false
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
    document.getElementById('router_ip_display').value = device.router_ip || device.routerIp || "";
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
    document.getElementById('device_heartbeat').value = '30';
    document.getElementById('device_alerts').checked = true;
    
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

async function saveRouterIp(){
  const routerIp = document.getElementById('router_ip').value.trim();
  if(!routerIp) {
    alert("Please enter your router IP address");
    return;
  }
  
  // Validate IP format
  const ipPattern = /^(?:[0-9]{1,3}\.){3}[0-9]{1,3}$/;
  if(!ipPattern.test(routerIp)) {
    alert("Please enter a valid IP address (e.g., 192.168.1.1)");
    return;
  }
  
  try {
    await api("/api/network-settings", {
      method: "PUT",
      body: { router_ip: routerIp }
    });
    
    document.getElementById('routerIpSetup').style.display = 'none';
    alert("Router IP saved! You can now scan for devices.");
  } catch(e) {
    alert("Failed to save router IP: " + e.message);
  }
}

async function scanForDevices(){
  const statusDiv = document.getElementById('deviceIpStatus');
  const detectedDiv = document.getElementById('detectedDevices');
  const detectedList = document.getElementById('detectedDevicesList');
  
  statusDiv.innerHTML = '<span style="color: var(--primary);">Scanning network...</span>';
  detectedDiv.style.display = 'none';
  
  try {
    const result = await api("/api/network/scan-devices");
    
    if(result.error === 'no_router_ip') {
      statusDiv.innerHTML = '<span style="color: var(--danger);">⚠️ Please configure your router IP first</span>';
      document.getElementById('routerIpSetup').style.display = 'block';
      return;
    }
    
    if(result.devices && result.devices.length > 0) {
      statusDiv.innerHTML = `<span style="color: var(--ok);">✓ Found ${result.total_detected} device(s) on your network</span>`;
      
      // Show detected devices
      detectedList.innerHTML = result.devices.map(device => `
        <div style="padding: 8px; margin-bottom: 4px; background: var(--bg); border-radius: 4px; cursor: pointer; border: 1px solid var(--border);" 
             onclick="selectDetectedDevice('${device.ip}', '${device.hostname || 'Unknown'}')"
             onmouseover="this.style.borderColor='var(--primary)'"
             onmouseout="this.style.borderColor='var(--border)'">
          <div style="font-weight: 500;">${device.ip}</div>
          <div style="font-size: 12px; color: var(--muted);">
            ${device.hostname ? `Hostname: ${device.hostname} | ` : ''}
            Ports: ${device.ports_open.join(', ')}
          </div>
        </div>
      `).join('');
      
      detectedDiv.style.display = 'block';
    } else {
      statusDiv.innerHTML = '<span style="color: var(--warning);">No new devices detected. Make sure devices are powered on and connected.</span>';
      detectedDiv.style.display = 'none';
    }
  } catch(e) {
    statusDiv.innerHTML = `<span style="color: var(--danger);">✗ Scan failed: ${e.message}</span>`;
    detectedDiv.style.display = 'none';
  }
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
  
  const deviceId = document.getElementById('device_id').value.trim();
  const name = document.getElementById('device_name').value.trim();
  const type = document.getElementById('device_type').value;
  const routerIp = document.getElementById('router_ip_display').value;
  const heartbeatInterval = parseInt(document.getElementById('device_heartbeat').value) || 30;
  const alertsEnabled = document.getElementById('device_alerts').checked;

  // Validation
  if(!deviceId || !name || !type || !routerIp) {
    if(msg) {
      msg.className = "msg bad";
      msg.textContent = "Please fill in all required fields";
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
          heartbeat_interval: heartbeatInterval,
          alerts_enabled: alertsEnabled
        }
      });

      if(msg) {
        msg.className = "msg ok";
        msg.textContent = `Device "${name}" updated successfully!`;
      }
      editSnapshot = null;
    } else {
      const deviceData = {
        device_id: deviceId,
        name,
        type,
        router_ip: routerIp,
        device_ip: null, // Not required
        heartbeat_interval: heartbeatInterval,
        alerts_enabled: alertsEnabled
      };

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
  return {
    name: document.getElementById('device_name').value.trim(),
    type: document.getElementById('device_type').value,
    heartbeat_interval: parseInt(document.getElementById('device_heartbeat').value) || 30,
    alerts_enabled: document.getElementById('device_alerts').checked
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

  overlay.classList.add('show');
  panel.classList.add('show');
  overlay.setAttribute('aria-hidden', 'false');
  panel.setAttribute('aria-hidden', 'false');
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
    await Promise.all([loadDevices(), loadAlerts()]);
    updateLastRefreshTime();
    
    msg.textContent = "✅ Refreshed successfully!";
    setTimeout(() => { msg.textContent = ""; }, 2000);
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
  }
  if(qs("#logoutBtn")){
    qs("#logoutBtn").addEventListener("click", logout);
  }
  if(qs("#dashboardRoot")){
    loadDashboard();
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

    ['device_name', 'device_type', 'device_heartbeat', 'device_alerts'].forEach((id) => {
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

// Clean up on page unload
window.addEventListener("beforeunload", () => {
  stopAutoRefresh();
  if(typeof disconnectWebSocket === 'function'){
    disconnectWebSocket();
  }
});
