/* Family Sharing - Frontend Logic */

let currentFamily = null;
let currentUser = null;

async function loadFamilyPage() {
  const who = document.getElementById('who');
  
  try {
    // Get current user
    currentUser = await api('/api/auth/me');
    who.textContent = `${currentUser.name} (${currentUser.email})`;
    
    // Try to load family
    try {
      currentFamily = await api('/api/family/my-family');
      showHasFamily();
      await loadFamilyDetails();
    } catch (error) {
      if (error.message.includes('not part of any family')) {
        showNoFamily();
      } else {
        throw error;
      }
    }
  } catch (error) {
    console.error('Failed to load family page:', error);
    if (error && error.unauthorized) {
      clearAuth();
      const currentPath = window.location.pathname;
      window.location.href = `/login?redirect=${encodeURIComponent(currentPath)}`;
      return;
    }
    const msgEl = document.getElementById('familyMsg');
    if (msgEl) { msgEl.textContent = error?.message || 'Failed to load. Please try again.'; msgEl.className = 'msg bad'; }
  }
}

function showNoFamily() {
  document.getElementById('noFamily').style.display = 'block';
  document.getElementById('hasFamily').style.display = 'none';
}

function showHasFamily() {
  document.getElementById('noFamily').style.display = 'none';
  document.getElementById('hasFamily').style.display = 'block';
}

async function createFamily(event) {
  event.preventDefault();
  
  const name = document.getElementById('familyName').value.trim();
  const description = document.getElementById('familyDescription').value.trim();
  const msg = document.getElementById('createMsg');
  
  msg.className = 'msg';
  msg.textContent = 'Creating family...';
  
  try {
    const family = await api('/api/family/', {
      method: 'POST',
      body: {
        name,
        description: description || undefined
      }
    });
    
    msg.className = 'msg ok';
    msg.textContent = '✅ Family created successfully!';
    
    currentFamily = family;
    
    setTimeout(() => {
      showHasFamily();
      loadFamilyDetails();
    }, 1000);
  } catch (error) {
    msg.className = 'msg bad';
    msg.textContent = '❌ ' + error.message;
  }
}

async function loadFamilyDetails() {
  if (!currentFamily) return;
  
  // Update family info
  document.getElementById('familyName').textContent = currentFamily.name;
  document.getElementById('familyDescription').textContent = currentFamily.description || 'No description';
  
  // Update stats
  document.getElementById('memberCount').textContent = currentFamily.members.length;
  document.getElementById('deviceCount').textContent = currentFamily.total_devices;
  
  // Load invitations
  await loadInvitations();
  
  // Render members table
  renderMembers(currentFamily.members);
}

function renderMembers(members) {
  const tbody = document.getElementById('membersTable');
  
  if (!members || members.length === 0) {
    tbody.innerHTML = '<tr><td colspan="6" class="hint">No family members yet</td></tr>';
    return;
  }
  
  const isAdmin = currentUser && currentFamily && currentUser.id === currentFamily.owner_id;
  
  tbody.innerHTML = members.map(member => {
    const isOwner = member.user_id === currentFamily.owner_id;
    const permissions = [];
    if (member.can_manage_devices) permissions.push('Manage Devices');
    if (member.can_resolve_alerts) permissions.push('Resolve Alerts');
    if (member.can_invite_members) permissions.push('Invite Members');
    
    return `
      <tr>
        <td>
          ${esc(member.name)}
          ${isOwner ? '<span class="badge b-ok" style="margin-left: 8px;">Owner</span>' : ''}
        </td>
        <td>${esc(member.email)}</td>
        <td><span class="badge ${member.role === 'admin' ? 'b-primary' : 'b-muted'}">${esc(member.role)}</span></td>
        <td>${new Date(member.joined_at).toLocaleDateString()}</td>
        <td style="font-size: 12px;">${permissions.join(', ') || 'View Only'}</td>
        <td>
          ${isAdmin && !isOwner ? 
            `<button class="btn-sm danger" onclick="removeMember('${member.user_id}')">Remove</button>` : 
            '-'
          }
        </td>
      </tr>
    `;
  }).join('');
}

async function loadInvitations() {
  try {
    const invitations = await api('/api/family/invitations');
    document.getElementById('inviteCount').textContent = invitations.length;
    renderInvitations(invitations);
  } catch (error) {
    console.error('Failed to load invitations:', error);
  }
}

function renderInvitations(invitations) {
  const tbody = document.getElementById('invitationsTable');
  
  if (!invitations || invitations.length === 0) {
    tbody.innerHTML = '<tr><td colspan="6" class="hint">No pending invitations</td></tr>';
    return;
  }
  
  tbody.innerHTML = invitations.map(inv => `
    <tr>
      <td>${esc(inv.invitee_email)}</td>
      <td>${esc(inv.invitee_name)}</td>
      <td><span class="badge b-muted">${esc(inv.role)}</span></td>
      <td>${new Date(inv.created_at).toLocaleDateString()}</td>
      <td>${new Date(inv.expires_at).toLocaleDateString()}</td>
      <td><span class="badge b-warn">${esc(inv.status)}</span></td>
    </tr>
  `).join('');
}

async function inviteMember(event) {
  event.preventDefault();
  
  const email = document.getElementById('inviteEmail').value.trim();
  const name = document.getElementById('inviteName').value.trim();
  const role = document.getElementById('inviteRole').value;
  const canManageDevices = document.getElementById('canManageDevices').checked;
  const canResolveAlerts = document.getElementById('canResolveAlerts').checked;
  const canInviteMembers = document.getElementById('canInviteMembers').checked;
  
  const msg = document.getElementById('inviteMsg');
  msg.className = 'msg';
  msg.textContent = 'Sending invitation...';
  
  try {
    await api('/api/family/invite', {
      method: 'POST',
      body: {
        email,
        name,
        role,
        can_manage_devices: canManageDevices,
        can_resolve_alerts: canResolveAlerts,
        can_invite_members: canInviteMembers
      }
    });
    
    msg.className = 'msg ok';
    msg.textContent = `✅ Invitation sent to ${email}!`;
    
    // Reset form
    document.getElementById('inviteForm').reset();
    
    // Reload invitations
    await loadInvitations();
    
    setTimeout(() => {
      msg.textContent = '';
      msg.className = 'msg';
    }, 3000);
  } catch (error) {
    msg.className = 'msg bad';
    msg.textContent = '❌ ' + error.message;
  }
}

async function removeMember(userId) {
  if (!confirm('Are you sure you want to remove this member from your family?')) {
    return;
  }
  
  try {
    await api(`/api/family/members/${userId}`, {
      method: 'DELETE'
    });
    
    // Reload family
    currentFamily = await api('/api/family/my-family');
    await loadFamilyDetails();
  } catch (error) {
    alert('Failed to remove member: ' + error.message);
  }
}

async function leaveFamily() {
  if (!confirm('Are you sure you want to leave this family? You will no longer have access to shared devices.')) {
    return;
  }
  
  try {
    await api('/api/family/my-family', {
      method: 'DELETE'
    });
    
    // Reload page
    window.location.reload();
  } catch (error) {
    alert('Failed to leave family: ' + error.message);
  }
}

function editFamily() {
  const name = prompt('Enter new family name:', currentFamily.name);
  if (!name) return;
  
  const description = prompt('Enter new description (optional):', currentFamily.description || '');
  
  updateFamily(name, description);
}

async function updateFamily(name, description) {
  try {
    const updated = await api('/api/family/my-family', {
      method: 'PUT',
      body: {
        name,
        description: description || undefined
      }
    });
    
    currentFamily = updated;
    await loadFamilyDetails();
  } catch (error) {
    alert('Failed to update family: ' + error.message);
  }
}

// Page initialization
window.addEventListener('DOMContentLoaded', () => {
  if (document.getElementById('familyRoot')) {
    loadFamilyPage();
    
    // Set up event listeners
    const createForm = document.getElementById('createFamilyForm');
    if (createForm) {
      createForm.addEventListener('submit', createFamily);
    }
    
    const inviteForm = document.getElementById('inviteForm');
    if (inviteForm) {
      inviteForm.addEventListener('submit', inviteMember);
    }
    
    const logoutBtn = document.getElementById('logoutBtn');
    if (logoutBtn) {
      logoutBtn.addEventListener('click', logout);
    }
  }
});
