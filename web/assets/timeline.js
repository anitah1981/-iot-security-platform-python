/* Incident Timeline - UI Logic */

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

let currentIncidentPage = 1;
let currentIncidentLimit = 20;
let currentIncidentFilters = {
  status: '',
  severity: ''
};

// Severity colors
const severityColors = {
  'low': 'var(--ok)',
  'medium': 'var(--warning)',
  'high': 'var(--danger)',
  'critical': '#dc2626'
};

// Status colors
const statusColors = {
  'open': 'var(--primary)',
  'investigating': 'var(--warning)',
  'resolved': 'var(--ok)',
  'closed': 'var(--muted)'
};

// Check if user has Pro/Business plan access
async function checkIncidentAccess() {
  const planCheckMsg = document.getElementById('planCheckMessage');
  const incidentsContent = document.getElementById('incidentsContent');
  
  if (!planCheckMsg || !incidentsContent) return;
  
  try {
    // Try to load incidents - will fail if not Pro/Business plan
    const response = await api('/api/incidents?limit=1');
    
    // If we get here, user has access
    planCheckMsg.style.display = 'none';
    incidentsContent.style.display = 'block';
    
    // Load incidents
    await loadIncidents();
  } catch (e) {
    // User doesn't have access
    planCheckMsg.innerHTML = `
      <div style="max-width: 500px; margin: 0 auto;">
        <div style="font-size: 48px; margin-bottom: 16px;">🔒</div>
        <h2 style="margin: 0 0 12px 0;">Pro/Business Plan Required</h2>
        <p style="color: var(--muted); margin-bottom: 24px;">
          Incident Timeline is available for Pro and Business plan subscribers only. 
          Upgrade your plan to access advanced incident management and timeline visualization.
        </p>
        <a href="/pricing" class="btn-sm" style="background: var(--primary); color: white; text-decoration: none; display: inline-block;">
          View Pricing Plans
        </a>
      </div>
    `;
    incidentsContent.style.display = 'none';
  }
}

// Load incidents
async function loadIncidents() {
  const listEl = document.getElementById('incidentsList');
  const pagination = document.getElementById('incidentsPagination');
  const countEl = document.getElementById('incidentsCount');
  
  if (!listEl) return;
  
  // Get filters
  const statusFilter = document.getElementById('statusFilter');
  const severityFilter = document.getElementById('severityFilter');
  
  currentIncidentFilters.status = statusFilter ? statusFilter.value : '';
  currentIncidentFilters.severity = severityFilter ? severityFilter.value : '';
  
  listEl.innerHTML = '<div class="hint">Loading incidents...</div>';
  
  try {
    // Build query string
    const params = new URLSearchParams({
      page: currentIncidentPage.toString(),
      limit: currentIncidentLimit.toString()
    });
    if (currentIncidentFilters.status) params.append('status', currentIncidentFilters.status);
    if (currentIncidentFilters.severity) params.append('severity', currentIncidentFilters.severity);
    
    const response = await api(`/api/incidents?${params.toString()}`);
    
    if (!response.incidents || response.incidents.length === 0) {
      listEl.innerHTML = '<div class="hint">No incidents found for the selected filters.</div>';
      if (pagination) pagination.style.display = 'none';
      if (countEl) countEl.textContent = '0 incidents';
      return;
    }
    
    // Render incidents
    listEl.innerHTML = response.incidents.map(incident => {
      const severityColor = severityColors[incident.severity] || 'var(--muted)';
      const statusColor = statusColors[incident.status] || 'var(--muted)';
      const createdDate = new Date(incident.created_at);
      const timeStr = createdDate.toLocaleString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
      });
      
      let timeToResolution = '';
      if (incident.time_to_resolution_minutes) {
        const hours = Math.floor(incident.time_to_resolution_minutes / 60);
        const minutes = incident.time_to_resolution_minutes % 60;
        timeToResolution = hours > 0 
          ? `${hours}h ${minutes}m`
          : `${minutes}m`;
      }
      
      return `
        <div class="card" style="margin-bottom: 16px; cursor: pointer;" onclick="showIncidentDetail('${incident.id}')">
          <div style="display: flex; justify-content: space-between; align-items: start; margin-bottom: 12px;">
            <div style="flex: 1;">
              <h3 style="margin: 0 0 8px 0; font-size: 16px;">${esc(incident.title)}</h3>
              ${incident.description ? `<p style="margin: 0; color: var(--muted); font-size: 14px;">${esc(incident.description)}</p>` : ''}
            </div>
            <div style="display: flex; gap: 8px;">
              <span class="badge" style="background: ${severityColor};">
                ${esc(incident.severity.toUpperCase())}
              </span>
              <span class="badge" style="background: ${statusColor};">
                ${esc(incident.status.toUpperCase())}
              </span>
            </div>
          </div>
          <div style="display: flex; gap: 16px; font-size: 13px; color: var(--muted);">
            <span>📅 ${esc(timeStr)}</span>
            <span>🔔 ${incident.alert_ids.length} alerts</span>
            <span>💬 ${incident.notes.length} notes</span>
            ${timeToResolution ? `<span>⏱️ Resolved in ${timeToResolution}</span>` : ''}
          </div>
        </div>
      `;
    }).join('');
    
    // Update pagination
    if (pagination) {
      const totalPages = Math.ceil((response.total || 0) / currentIncidentLimit);
      const currentPageEl = document.getElementById('currentIncidentPage');
      const totalPagesEl = document.getElementById('totalIncidentPages');
      const prevBtn = document.getElementById('prevIncidentPageBtn');
      const nextBtn = document.getElementById('nextIncidentPageBtn');
      
      if (currentPageEl) currentPageEl.textContent = response.page || 1;
      if (totalPagesEl) totalPagesEl.textContent = totalPages || 1;
      if (prevBtn) prevBtn.disabled = currentIncidentPage <= 1;
      if (nextBtn) nextBtn.disabled = currentIncidentPage >= totalPages;
      pagination.style.display = 'flex';
    }
    
    if (countEl) {
      countEl.textContent = `${response.total || 0} total incidents`;
    }
    
  } catch (e) {
    console.error('Failed to load incidents:', e);
    listEl.innerHTML = `<div class="hint" style="color: var(--danger);">Failed to load incidents: ${e.message || 'Unknown error'}</div>`;
    if (pagination) pagination.style.display = 'none';
  }
}

// Change incident page
function changeIncidentPage(delta) {
  currentIncidentPage += delta;
  if (currentIncidentPage < 1) currentIncidentPage = 1;
  loadIncidents();
}

// Show create incident modal
function showCreateIncidentModal() {
  const modal = document.getElementById('createIncidentModal');
  if (modal) {
    modal.style.display = 'flex';
    document.body.style.overflow = 'hidden';
  }
}

// Hide create incident modal
function hideCreateIncidentModal() {
  const modal = document.getElementById('createIncidentModal');
  if (modal) {
    modal.style.display = 'none';
    document.body.style.overflow = '';
    document.getElementById('createIncidentForm').reset();
  }
}

// Create incident
async function createIncident(event) {
  event.preventDefault();
  
  const title = document.getElementById('incidentTitle').value;
  const description = document.getElementById('incidentDescription').value;
  const severity = document.getElementById('incidentSeverity').value;
  const status = document.getElementById('incidentStatus').value;
  
  try {
    await api('/api/incidents', {
      method: 'POST',
      body: JSON.stringify({
        title,
        description: description || null,
        severity,
        status,
        alert_ids: []
      })
    });
    
    hideCreateIncidentModal();
    await loadIncidents();
  } catch (e) {
    alert('Failed to create incident: ' + (e.message || 'Unknown error'));
  }
}

// Show incident detail modal
async function showIncidentDetail(incidentId) {
  const modal = document.getElementById('incidentDetailModal');
  const titleEl = document.getElementById('incidentDetailTitle');
  const contentEl = document.getElementById('incidentDetailContent');
  
  if (!modal || !titleEl || !contentEl) return;
  
  modal.style.display = 'flex';
  document.body.style.overflow = 'hidden';
  contentEl.innerHTML = '<div class="hint">Loading incident details...</div>';
  
  try {
    // Get incident details
    const incident = await api(`/api/incidents/${incidentId}`);
    
    // Get timeline
    const timeline = await api(`/api/incidents/${incidentId}/timeline`);
    
    titleEl.textContent = incident.title;
    
    const severityColor = severityColors[incident.severity] || 'var(--muted)';
    const statusColor = statusColors[incident.status] || 'var(--muted)';
    
    // Render timeline
    const timelineHtml = timeline.map(event => {
      const eventDate = new Date(event.timestamp);
      const timeStr = eventDate.toLocaleString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit'
      });
      
      let eventIcon = '📌';
      let eventColor = 'var(--muted)';
      if (event.type === 'alert') {
        eventIcon = '🔔';
        eventColor = severityColors[event.severity] || 'var(--muted)';
      } else if (event.type === 'note') {
        eventIcon = '💬';
        eventColor = 'var(--primary)';
      } else if (event.type === 'status_change') {
        eventIcon = '✅';
        eventColor = 'var(--ok)';
      } else if (event.type === 'incident_created') {
        eventIcon = '🚨';
        eventColor = 'var(--danger)';
      }
      
      return `
        <div style="display: flex; gap: 16px; margin-bottom: 24px; position: relative;">
          <div style="flex-shrink: 0; width: 40px; height: 40px; border-radius: 50%; background: ${eventColor}; display: flex; align-items: center; justify-content: center; font-size: 20px;">
            ${eventIcon}
          </div>
          <div style="flex: 1; padding-bottom: 16px; border-left: 2px solid var(--border); padding-left: 16px; margin-left: -21px;">
            <div style="font-size: 12px; color: var(--muted); margin-bottom: 4px;">${esc(timeStr)}</div>
            <div style="font-weight: 500; margin-bottom: 4px;">${esc(event.title)}</div>
            ${event.description ? `<div style="color: var(--muted); font-size: 14px; margin-bottom: 4px;">${esc(event.description)}</div>` : ''}
            ${event.user_name ? `<div style="font-size: 12px; color: var(--muted);">by ${esc(event.user_name)}</div>` : ''}
          </div>
        </div>
      `;
    }).join('');
    
    contentEl.innerHTML = `
      <div style="margin-bottom: 24px;">
        <div style="display: flex; gap: 8px; margin-bottom: 16px;">
          <span class="badge" style="background: ${severityColor};">
            ${incident.severity.toUpperCase()}
          </span>
          <span class="badge" style="background: ${statusColor};">
            ${incident.status.toUpperCase()}
          </span>
        </div>
        ${incident.description ? `<p style="color: var(--muted); margin-bottom: 16px;">${esc(incident.description)}</p>` : ''}
        <div style="display: flex; gap: 16px; font-size: 14px; color: var(--muted); margin-bottom: 16px;">
          <span>🔔 ${incident.alert_ids.length} alerts</span>
          <span>💬 ${incident.notes.length} notes</span>
          ${incident.time_to_resolution_minutes ? `<span>⏱️ Resolved in ${Math.floor(incident.time_to_resolution_minutes / 60)}h ${incident.time_to_resolution_minutes % 60}m</span>` : ''}
        </div>
        ${incident.status !== 'resolved' && incident.status !== 'closed' ? `
          <div style="display: flex; gap: 8px;">
            <button class="btn-sm" onclick="resolveIncident('${incident.id}')" style="background: var(--ok); color: white;">
              Mark as Resolved
            </button>
          </div>
        ` : ''}
      </div>
      
      <div style="margin-bottom: 24px;">
        <h3 style="margin: 0 0 16px 0; font-size: 16px;">Timeline</h3>
        <div>
          ${timelineHtml}
        </div>
      </div>
      
      <div style="margin-bottom: 24px;">
        <h3 style="margin: 0 0 16px 0; font-size: 16px;">Notes</h3>
        <div id="incidentNotesList" style="margin-bottom: 16px;">
          ${incident.notes.map(note => {
            const noteDate = new Date(note.created_at);
            const noteTimeStr = noteDate.toLocaleString('en-US', {
              year: 'numeric',
              month: 'short',
              day: 'numeric',
              hour: '2-digit',
              minute: '2-digit'
            });
            return `
              <div class="card" style="margin-bottom: 12px;">
                <div style="font-size: 12px; color: var(--muted); margin-bottom: 8px;">
                  ${esc(note.user_name)} • ${esc(noteTimeStr)}
                </div>
                <div style="color: var(--text);">${esc(note.content)}</div>
              </div>
            `;
          }).join('')}
        </div>
        <form id="addNoteForm" onsubmit="addIncidentNote(event, '${incident.id}')">
          <textarea id="noteContent" rows="3" placeholder="Add a note..." required style="width: 100%; padding: 10px; background: var(--surface); border: 1px solid var(--border); border-radius: 6px; color: var(--text); resize: vertical; margin-bottom: 8px;"></textarea>
          <button type="submit" class="btn-sm" style="background: var(--primary); color: white;">Add Note</button>
        </form>
      </div>
    `;
  } catch (e) {
    console.error('Failed to load incident details:', e);
    contentEl.innerHTML = `<div class="hint" style="color: var(--danger);">Failed to load incident details: ${e.message || 'Unknown error'}</div>`;
  }
}

// Hide incident detail modal
function hideIncidentDetailModal() {
  const modal = document.getElementById('incidentDetailModal');
  if (modal) {
    modal.style.display = 'none';
    document.body.style.overflow = '';
  }
}

// Add note to incident
async function addIncidentNote(event, incidentId) {
  event.preventDefault();
  
  const content = document.getElementById('noteContent').value;
  
  try {
    await api(`/api/incidents/${incidentId}/notes`, {
      method: 'POST',
      body: JSON.stringify({ content })
    });
    
    document.getElementById('noteContent').value = '';
    await showIncidentDetail(incidentId); // Reload
  } catch (e) {
    alert('Failed to add note: ' + (e.message || 'Unknown error'));
  }
}

// Resolve incident
async function resolveIncident(incidentId) {
  if (!confirm('Mark this incident as resolved?')) return;
  
  try {
    await api(`/api/incidents/${incidentId}/resolve`, {
      method: 'POST'
    });
    
    await showIncidentDetail(incidentId); // Reload
    await loadIncidents(); // Refresh list
  } catch (e) {
    alert('Failed to resolve incident: ' + (e.message || 'Unknown error'));
  }
}

// Load correlation suggestions
async function loadCorrelationSuggestions() {
  const container = document.getElementById('correlationSuggestions');
  const listEl = document.getElementById('correlationSuggestionsList');
  
  if (!container || !listEl) return;
  
  listEl.innerHTML = '<div class="hint">Analyzing alerts...</div>';
  container.style.display = 'block';
  
  try {
    const suggestions = await api('/api/incidents/suggestions/correlate?time_window_minutes=30');
    
    if (!suggestions || suggestions.length === 0) {
      listEl.innerHTML = '<div class="hint">No correlation suggestions found. All alerts are already associated with incidents or there are no unresolved alerts.</div>';
      return;
    }
    
    listEl.innerHTML = suggestions.map((suggestion, index) => {
      const severityColor = severityColors[suggestion.severity] || 'var(--muted)';
      const firstTime = new Date(suggestion.first_alert_time);
      const timeStr = firstTime.toLocaleString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
      });
      
      // Store suggestion in data attribute
      const suggestionId = `suggestion_${index}`;
      window[`suggestion_${index}`] = suggestion;
      
      return `
        <div class="card" style="margin-bottom: 12px;">
          <div style="display: flex; justify-content: space-between; align-items: start; margin-bottom: 8px;">
            <div>
              <div style="font-weight: 500; margin-bottom: 4px;">${esc(suggestion.suggested_title)}</div>
              <div style="font-size: 13px; color: var(--muted);">${esc(suggestion.suggested_description)}</div>
            </div>
            <span class="badge" style="background: ${severityColor};">
              ${esc(suggestion.severity.toUpperCase())}
            </span>
          </div>
          <div style="display: flex; gap: 16px; font-size: 13px; color: var(--muted); margin-bottom: 12px;">
            <span>🔔 ${suggestion.alert_count} alerts</span>
            <span>📅 ${esc(timeStr)}</span>
            ${suggestion.device_name ? `<span>📱 ${esc(suggestion.device_name)}</span>` : ''}
          </div>
          <button class="btn-sm" onclick="createIncidentFromSuggestion(${index})" style="background: var(--primary); color: white;">
            Create Incident
          </button>
        </div>
      `;
    }).join('');
  } catch (e) {
    console.error('Failed to load correlation suggestions:', e);
    listEl.innerHTML = `<div class="hint" style="color: var(--danger);">Failed to load suggestions: ${e.message || 'Unknown error'}</div>`;
  }
}

// Create incident from suggestion
async function createIncidentFromSuggestion(index) {
  try {
    const suggestion = window[`suggestion_${index}`];
    if (!suggestion) {
      throw new Error('Suggestion not found');
    }
    
    await api('/api/incidents', {
      method: 'POST',
      body: JSON.stringify({
        title: suggestion.suggested_title,
        description: suggestion.suggested_description,
        severity: suggestion.severity,
        status: 'open',
        alert_ids: suggestion.alert_ids
      })
    });
    
    await loadIncidents();
    document.getElementById('correlationSuggestions').style.display = 'none';
    
    // Clean up
    delete window[`suggestion_${index}`];
  } catch (e) {
    alert('Failed to create incident: ' + (e.message || 'Unknown error'));
  }
}

// Make functions globally accessible
window.loadIncidents = loadIncidents;
window.changeIncidentPage = changeIncidentPage;
window.showCreateIncidentModal = showCreateIncidentModal;
window.hideCreateIncidentModal = hideCreateIncidentModal;
window.createIncident = createIncident;
window.showIncidentDetail = showIncidentDetail;
window.hideIncidentDetailModal = hideIncidentDetailModal;
window.addIncidentNote = addIncidentNote;
window.resolveIncident = resolveIncident;
window.loadCorrelationSuggestions = loadCorrelationSuggestions;
window.createIncidentFromSuggestion = createIncidentFromSuggestion;
window.checkIncidentAccess = checkIncidentAccess;

// Initialize on page load
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', checkIncidentAccess);
} else {
  checkIncidentAccess();
}
