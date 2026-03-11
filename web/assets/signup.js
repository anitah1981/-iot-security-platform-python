/* Signup Page Logic – after signup, user must verify email then log in (no dashboard until login) */
/* v7: force 12-char messaging even if cached HTML still shows 8 */
(function () {
  var p = document.getElementById("password");
  var h = document.getElementById("passwordHintSignup");
  if (p) {
    p.placeholder = "Min. 12 characters";
    p.setAttribute("placeholder", "Min. 12 characters");
  }
  if (h) {
    h.textContent = "Use at least 12 characters with uppercase, lowercase, a number, and a special character";
  }
})();

// Get plan from URL parameter
const urlParams = new URLSearchParams(window.location.search);
const planParam = urlParams.get('plan');

if(planParam) {
  const planRadio = document.querySelector(`input[value="${planParam}"]`);
  if(planRadio) {
    planRadio.checked = true;
    document.getElementById('selected-plan').value = planParam;
  }
}

// Handle plan selection
document.querySelectorAll('input[name="plan"]').forEach(radio => {
  radio.addEventListener('change', (e) => {
    document.getElementById('selected-plan').value = e.target.value;
    document.querySelectorAll('.plan-option').forEach(opt => {
      opt.classList.remove('selected');
    });
    e.target.closest('.plan-option').classList.add('selected');
  });
});

// MFA during signup removed from flow – enable MFA after first login in Settings
document.getElementById('setupMfa')?.addEventListener('change', (e) => {
  if(e.target.checked) {
    e.target.checked = false;
    const msg = document.getElementById('signupMsg');
    if(msg) {
      msg.className = 'msg';
      msg.textContent = 'MFA can be enabled after you verify your email and sign in (Settings).';
    }
  }
});

document.getElementById('generateMfaBtn')?.addEventListener('click', (e) => {
  e.preventDefault();
  const msg = document.getElementById('signupMsg');
  if(msg) {
    msg.className = 'msg';
    msg.textContent = 'MFA is set up after sign in under Settings.';
  }
});

// Handle signup form
document.getElementById('signupForm')?.addEventListener('submit', async (e) => {
  e.preventDefault();

  const name = document.getElementById('name').value.trim();
  const email = document.getElementById('email').value.trim();
  const password = document.getElementById('password').value;
  const confirmPassword = document.getElementById('confirm-password').value;
  const plan = document.getElementById('selected-plan').value;
  const msg = document.getElementById('signupMsg');

  if(password !== confirmPassword) {
    msg.className = 'msg bad';
    msg.textContent = 'Passwords do not match';
    return;
  }

  if(password.length < 12) {
    msg.className = 'msg bad';
    msg.textContent = 'Password must be at least 12 characters, with uppercase, lowercase, a number, and a special character';
    return;
  }

  msg.className = 'msg';
  msg.textContent = 'Creating your account...';

  try {
    const response = await api('/api/auth/signup', {
      method: 'POST',
      auth: false,
      body: {
        name,
        email,
        password,
        role: plan === 'business' ? 'business' : 'consumer'
      }
    });

    localStorage.setItem('selected_plan', plan);
    // Never store tokens from signup – backend does not issue session until after verify + login
    if(typeof setToken === 'function') setToken(null);
    if(typeof setRefreshToken === 'function') setRefreshToken(null);

    msg.className = 'msg ok';
    msg.innerHTML = `Account created. <strong>Verify your email</strong> using the link we sent, then <a href="/login" style="color: var(--primary); font-weight: 600;">sign in</a> to open the dashboard.<br/><br/>
      <a href="/verify-email?email=${encodeURIComponent(email)}" style="color: var(--primary); text-decoration: none; font-weight: 600;">Resend or open verify page</a>`;
    showToast('Check your inbox to verify, then sign in.', 'info');
  } catch(error) {
    msg.className = 'msg bad';
    msg.textContent = error.message || 'Signup failed. Please try again.';
    if(error.rateLimited){
      showToast(error.message, 'warning');
    }
  }
});
