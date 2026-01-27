/* Audit Logs - UI Logic */

// Helper function for escaping HTML
function esc(s) {
  return String(s ?? "").replace(/[&<>"']/g, (c) => ({
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    "\"": "&quot;",
    "'": "&#39;"
  }[c]));
}

let currentPage = 1;
let currentLimit = 50;
let currentFilters = {
  action: '',
  resource_type: '',
  days: 30
};

// Action labels for display
const actionLabels = {
  'login': 'Login',
  'logout': 'Logout',
  'password_change': 'Password Changed',
  'device_create': 'Device Created',
  'device_update': 'Device Updated',
  'device_delete': 'Device Deleted',
  'device_add_to_group': 'Device Added to Group',
  'device_remove_from_group': 'Device Removed from Group',
  'group_create': 'Group Created',
  'group_update': 'Group Updated',
  'group_delete': 'Group Deleted',
  'alert_resolve': 'Alert Resolved',
  'notification_preferences_update': 'Notification Settings Updated',
  'subscription_update': 'Subscription Updated'
};

// Action colors
const actionColors = {
  'login': 'var(--ok)',
  'logout': 'var(--muted)',
  'password_change': 'var(--warning)',
  'device_create': 'var(--ok)',
  'device_update': 'var(--primary)',
  'device_delete': 'var(--danger)',
  'device_add_to_group': 'var(--primary)',
  'device_remove_from_group': 'var(--warning)',
  'group_create': 'var(--ok)',
  'group_update': 'var(--primary)',
  'group_delete': 'var(--danger)',
  'alert_resolve': 'var(--ok)',
  'notification_preferences_update': 'var(--primary)',
  'subscription_update': 'var(--primary)'
};

// Check if user has Business plan access
async function checkAuditAccess() {
  const planCheckMsg = document.getElementById('planCheckMessage');
  const auditContent = document.getElementById('auditLogsContent');
  
  if (!planCheckMsg || !auditContent) return;
  
  try {
    // Try to load audit logs - will fail if not Business plan
    const response = await api('/api/audit/logs?limit=1');
    
    // If we get here, user has access
    planCheckMsg.style.display = 'none';
    auditContent.style.display = 'block';
    
    // Load audit logs
    await loadAuditLogs();
    await loadAuditStats();
  } catch (e) {
    // User doesn't have access
    planCheckMsg.innerHTML = `
      <div style="max-width: 500px; margin: 0 auto;">
        <div style="font-size: 48px; margin-bottom: 16px;">🔒</div>
        <h2 style="margin: 0 0 12px 0;">Business Plan Required</h2>
        <p style="color: var(--muted); margin-bottom: 24px;">
          Audit logs are available for Business plan subscribers only. 
          Upgrade your plan to access comprehensive activity history and compliance reporting.
        </p>
        <a href="/pricing" class="btn-sm" style="background: var(--primary); color: white; text-decoration: none; display: inline-block;">
          View Pricing Plans
        </a>
      </div>
    `;
    auditContent.style.display = 'none';
  }
}

// Load audit logs
async function loadAuditLogs() {
  const table = document.getElementById('auditLogsTable');
  const pagination = document.getElementById('auditPagination');
  const countEl = document.getElementById('auditLogsCount');
  
  if (!table) return;
  
  // Get filters
  const actionFilter = document.getElementById('actionFilter');
  const resourceFilter = document.getElementById('resourceTypeFilter');
  const daysFilter = document.getElementById('daysFilter');
  
  currentFilters.action = actionFilter ? actionFilter.value : '';
  currentFilters.resource_type = resourceFilter ? resourceFilter.value : '';
  currentFilters.days = daysFilter ? parseInt(daysFilter.value) : 30;
  
  table.innerHTML = '<tr><td colspan="6" class="hint">Loading audit logs...</td></tr>';
  
  try {
    // Build query string
    const params = new URLSearchParams({
      page: currentPage.toString(),
      limit: currentLimit.toString(),
      days: currentFilters.days.toString()
    });
    if (currentFilters.action) params.append('action', currentFilters.action);
    if (currentFilters.resource_type) params.append('resource_type', currentFilters.resource_type);
    
    const response = await api(`/api/audit/logs?${params.toString()}`);
    
    if (!response.logs || response.logs.length === 0) {
      table.innerHTML = '<tr><td colspan="6" class="hint">No audit logs found for the selected filters.</td></tr>';
      if (pagination) pagination.style.display = 'none';
      if (countEl) countEl.textContent = '0 logs';
      return;
    }
    
    // Render logs
    table.innerHTML = response.logs.map(log => {
      const actionLabel = actionLabels[log.action] || log.action;
      const actionColor = actionColors[log.action] || 'var(--muted)';
      const timestamp = new Date(log.created_at);
      const timeStr = timestamp.toLocaleString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
      });
      
      // Format details
      let detailsHtml = '—';
      if (log.details && Object.keys(log.details).length > 0) {
        const detailsList = Object.entries(log.details)
          .filter(([k, v]) => k !== 'changes') // Exclude changes object for cleaner display
          .map(([k, v]) => {
            if (typeof v === 'object') {
              return `${k}: ${JSON.stringify(v)}`;
            }
            return `${k}: ${v}`;
          })
          .slice(0, 3); // Show first 3 details
        detailsHtml = detailsList.join('<br>') || '—';
      }
      
      return `
        <tr>
          <td style="font-size: 13px; color: var(--muted); white-space: nowrap;">${esc(timeStr)}</td>
          <td>
            <div style="font-size: 13px; font-weight: 500;">${esc(log.user_name || log.user_email)}</div>
            <div style="font-size: 12px; color: var(--muted);">${esc(log.user_email)}</div>
          </td>
          <td>
            <span class="badge" style="background: ${actionColor};">
              ${esc(actionLabel)}
            </span>
          </td>
          <td>
            <div style="font-size: 13px;">${esc(log.resource_type)}</div>
            ${log.resource_id ? `<div style="font-size: 12px; color: var(--muted); font-family: monospace;">${esc(log.resource_id.substring(0, 8))}...</div>` : ''}
          </td>
          <td style="font-size: 12px; color: var(--muted); max-width: 300px;">${detailsHtml}</td>
          <td style="font-size: 12px; color: var(--muted); font-family: monospace;">${log.ip_address ? esc(log.ip_address) : '—'}</td>
        </tr>
      `;
    }).join('');
    
    // Update pagination
    if (pagination) {
      const totalPages = response.pages || 1;
      const currentPageEl = document.getElementById('currentPage');
      const totalPagesEl = document.getElementById('totalPages');
      const prevBtn = document.getElementById('prevPageBtn');
      const nextBtn = document.getElementById('nextPageBtn');
      const infoEl = document.getElementById('auditLogsInfo');
      
      if (currentPageEl) currentPageEl.textContent = response.page || 1;
      if (totalPagesEl) totalPagesEl.textContent = totalPages;
      if (prevBtn) prevBtn.disabled = currentPage <= 1;
      if (nextBtn) nextBtn.disabled = currentPage >= totalPages;
      if (infoEl) {
        const start = ((response.page || 1) - 1) * currentLimit + 1;
        const end = Math.min(start + response.logs.length - 1, response.total || 0);
        infoEl.textContent = `Showing ${start}-${end} of ${response.total || 0} logs`;
      }
      pagination.style.display = 'flex';
    }
    
    if (countEl) {
      countEl.textContent = `${response.total || 0} total logs`;
    }
    
  } catch (e) {
    console.error('Failed to load audit logs:', e);
    table.innerHTML = `<tr><td colspan="6" class="hint" style="color: var(--danger);">Failed to load audit logs: ${e.message || 'Unknown error'}</td></tr>`;
    if (pagination) pagination.style.display = 'none';
  }
}

// Load audit statistics
async function loadAuditStats() {
  const statsContainer = document.getElementById('auditStats');
  const statsContent = document.getElementById('statsContent');
  
  if (!statsContainer || !statsContent) return;
  
  try {
    const daysFilter = document.getElementById('daysFilter');
    const days = daysFilter ? parseInt(daysFilter.value) : 30;
    
    const stats = await api(`/api/audit/logs/stats?days=${days}`);
    
    if (!stats || stats.total_logs === 0) {
      statsContainer.style.display = 'none';
      return;
    }
    
    statsContainer.style.display = 'block';
    
    // Render action breakdown
    const actionBreakdown = Object.entries(stats.action_breakdown || {})
      .sort((a, b) => b[1] - a[1])
      .slice(0, 5);
    
    const resourceBreakdown = Object.entries(stats.resource_breakdown || {})
      .sort((a, b) => b[1] - a[1])
      .slice(0, 5);
    
    statsContent.innerHTML = `
      <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px;">
        <div>
          <div style="font-size: 32px; font-weight: bold; color: var(--primary); margin-bottom: 4px;">
            ${stats.total_logs}
          </div>
          <div style="font-size: 14px; color: var(--muted);">Total Actions (${stats.period_days} days)</div>
        </div>
        <div>
          <div style="font-size: 14px; font-weight: 500; margin-bottom: 8px;">Top Actions</div>
          <div style="display: flex; flex-direction: column; gap: 6px;">
            ${actionBreakdown.map(([action, count]) => `
              <div style="display: flex; justify-content: space-between; align-items: center; font-size: 13px;">
                <span>${esc(actionLabels[action] || action)}</span>
                <span class="badge" style="background: ${actionColors[action] || 'var(--muted)'};">${count}</span>
              </div>
            `).join('')}
          </div>
        </div>
        <div>
          <div style="font-size: 14px; font-weight: 500; margin-bottom: 8px;">By Resource Type</div>
          <div style="display: flex; flex-direction: column; gap: 6px;">
            ${resourceBreakdown.map(([type, count]) => `
              <div style="display: flex; justify-content: space-between; align-items: center; font-size: 13px;">
                <span style="text-transform: capitalize;">${esc(type)}</span>
                <span class="badge" style="background: var(--primary);">${count}</span>
              </div>
            `).join('')}
          </div>
        </div>
      </div>
    `;
  } catch (e) {
    console.error('Failed to load audit stats:', e);
    statsContainer.style.display = 'none';
  }
}

// Change page
function changePage(delta) {
  currentPage += delta;
  if (currentPage < 1) currentPage = 1;
  loadAuditLogs();
}

// Export audit logs
async function exportAuditLogs() {
  const btn = event?.target || document.querySelector('button[onclick="exportAuditLogs()"]');
  if (!btn) return;
  
  const originalText = btn.textContent;
  btn.disabled = true;
  btn.textContent = '⏳ Exporting...';
  
  try {
    // Build query string
    const params = new URLSearchParams({
      format: 'csv',
      days: currentFilters.days.toString()
    });
    if (currentFilters.action) params.append('action', currentFilters.action);
    if (currentFilters.resource_type) params.append('resource_type', currentFilters.resource_type);
    
    const token = getToken();
    const response = await fetch(`/api/audit/logs/export?${params.toString()}`, {
      headers: {
        'Authorization': `Bearer ${token}`
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
    a.download = `audit_logs_${new Date().toISOString().slice(0,10)}.csv`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    window.URL.revokeObjectURL(url);
    
    btn.textContent = '✅ Downloaded!';
    setTimeout(() => {
      btn.disabled = false;
      btn.textContent = '📥 Export';
    }, 2000);
  } catch (e) {
    alert('Export failed: ' + (e.message || 'Unknown error'));
    btn.disabled = false;
    btn.textContent = originalText;
  }
}

// Make functions globally accessible
window.loadAuditLogs = loadAuditLogs;
window.loadAuditStats = loadAuditStats;
window.changePage = changePage;
window.exportAuditLogs = exportAuditLogs;
window.checkAuditAccess = checkAuditAccess;

// Initialize on page load
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', checkAuditAccess);
} else {
  checkAuditAccess();
}
