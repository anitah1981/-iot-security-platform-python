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
    who.textContent = `${me.name} (${me.email})`;
  }catch(e){
    // Not logged in
    setToken(null);
    window.location.href = "/login";
    return;
  }

  msg.textContent = "Loading…";

  try{
    const [devices, alerts] = await Promise.all([
      api("/api/devices?limit=25&page=1", { auth:false }), // current API has no auth on devices yet
      api("/api/alerts?limit=25&page=1", { auth:false }),
    ]);

    renderDevices(devices.devices || []);
    renderAlerts(alerts.alerts || []);

    msg.textContent = "";
  }catch(e){
    msg.textContent = e.message;
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
    <tr>
      <td>${esc(d.device_id)}</td>
      <td>${esc(d.name)}</td>
      <td>${esc(d.type)}</td>
      <td>${esc(d.ip_address)}</td>
      <td>${badgeForStatus(d.status)}</td>
    </tr>
  `).join("");
}

function renderAlerts(alerts){
  const tbody = qs("#alerts");
  if(!tbody) return;
  if(!alerts.length){
    tbody.innerHTML = `<tr><td colspan="5" class="hint">No alerts yet.</td></tr>`;
    return;
  }
  tbody.innerHTML = alerts.map(a => `
    <tr>
      <td><span class="${badgeForSeverity(a.severity)}">${esc(a.severity)}</span></td>
      <td>${esc(a.type)}</td>
      <td>${esc(a.message)}</td>
      <td>${a.device?.name ? esc(a.device.name) : esc(a.device_id)}</td>
      <td>${esc((a.created_at || "").toString().slice(0,19).replace("T"," "))}</td>
    </tr>
  `).join("");
}

function logout(){
  setToken(null);
  window.location.href = "/";
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
  }
});

