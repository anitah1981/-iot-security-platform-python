/* Signup Page Logic */

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
    
    // Visual feedback
    document.querySelectorAll('.plan-option').forEach(opt => {
      opt.classList.remove('selected');
    });
    e.target.closest('.plan-option').classList.add('selected');
  });
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
  
  // Validation
  if(password !== confirmPassword) {
    msg.className = 'msg bad';
    msg.textContent = 'Passwords do not match';
    return;
  }
  
  if(password.length < 8) {
    msg.className = 'msg bad';
    msg.textContent = 'Password must be at least 8 characters';
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
    
    // Save tokens (only if verification not required)
    const verificationRequired = response.verification_required === true;
    if(!verificationRequired){
      setToken(response.token);
      if(response.refresh_token) setRefreshToken(response.refresh_token);
    } else {
      setToken(null);
      setRefreshToken(null);
    }
    
    // Store plan selection for later use
    localStorage.setItem('selected_plan', plan);
    
    if(verificationRequired){
      msg.className = 'msg ok';
      msg.innerHTML = `Account created! Please verify your email to continue.<br/>
        <a href="/verify-email?email=${encodeURIComponent(email)}" style="color: var(--primary); text-decoration: none; font-weight: 600;">Verify email</a>`;
      showToast("Verification email sent.", "info");
    } else {
      msg.className = 'msg ok';
      msg.textContent = 'Account created! Redirecting to dashboard...';
      setTimeout(() => {
        window.location.href = '/dashboard';
      }, 1000);
    }
    
  } catch(error) {
    msg.className = 'msg bad';
    msg.textContent = error.message || 'Signup failed. Please try again.';
    if(error.rateLimited){
      showToast(error.message, "warning");
    }
  }
});