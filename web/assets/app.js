/* Minimal frontend for the IoT Security Platform API */

const API_BASE = ""; // same-origin

function qs(sel){ return document.querySelector(sel); }
function esc(s){ return String(s ?? "").replace(/[&<>"']/g, (c)=>({ "&":"&amp;","<":"&lt;",">":"&gt;","\"":"&quot;","'":"&#39;" }[c])); }

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
    const [devices, alerts] = await Promise.all([
      api("/api/devices?limit=25&page=1"),
      api("/api/alerts?limit=25&page=1"),
    ]);

    renderDevices(devices.devices || []);
    renderAlerts(alerts.alerts || []);
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
      const [devices, alerts] = await Promise.all([
        api("/api/devices?limit=25&page=1"),
        api("/api/alerts?limit=25&page=1"),
      ]);
      renderDevices(devices.devices || []);
      renderAlerts(alerts.alerts || []);
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

function renderDevices(devs){
  const tbody = qs("#devices");
  if(!tbody) return;
  if(!devs.length){
    tbody.innerHTML = `<tr><td colspan="5" class="hint">No devices yet.</td></tr>`;
    return;
  }
  tbody.innerHTML = devs.map(d => `
    <tr data-device-id="${d.id || d._id}">
      <td>${esc(d.device_id)}</td>
      <td>${esc(d.name)}</td>
      <td>${esc(d.type)}</td>
      <td>${esc(d.ip_address)}</td>
      <td class="device-status">${badgeForStatus(d.status)}</td>
    </tr>
  `).join("");
}

function renderAlerts(alerts){
  const tbody = qs("#alerts");
  if(!tbody) return;
  if(!alerts.length){
    tbody.innerHTML = `<tr><td colspan="6" class="hint">No alerts yet.</td></tr>`;
    return;
  }
  tbody.innerHTML = alerts.map(a => `
    <tr class="${a.resolved ? 'resolved-alert' : ''}" data-alert-id="${a.id || a._id}">
      <td><span class="${badgeForSeverity(a.severity)}">${esc(a.severity)}</span></td>
      <td>${esc(a.type)}</td>
      <td>${esc(a.message)}</td>
      <td>${a.device?.name ? esc(a.device.name) : esc(a.device_id)}</td>
      <td>${esc((a.created_at || "").toString().slice(0,19).replace("T"," "))}</td>
      <td class="alert-action">
        ${!a.resolved ? `<button class="btn-sm" onclick="resolveAlert('${a.id}')">Resolve</button>` : '<span class="badge b-ok">Resolved</span>'}
      </td>
    </tr>
  `).join("");
}

async function resolveAlert(alertId){
  const msg = qs("#dashmsg");
  try{
    msg.textContent = "Resolving alert...";
    await api(`/api/alerts/${alertId}/resolve`, { method: "POST" });
    msg.className = "msg ok";
    msg.textContent = "Alert resolved!";
    setTimeout(() => { msg.textContent = ""; msg.className = "msg"; }, 2000);
    // Reload alerts
    const alerts = await api("/api/alerts?limit=25&page=1");
    renderAlerts(alerts.alerts || []);
  }catch(e){
    msg.className = "msg bad";
    msg.textContent = e.message;
  }
}

function logout(){
  setToken(null);
  window.location.href = "/";
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
    const [devices, alerts] = await Promise.all([
      api("/api/devices?limit=25&page=1"),
      api("/api/alerts?limit=25&page=1"),
    ]);
    
    renderDevices(devices.devices || []);
    renderAlerts(alerts.alerts || []);
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
