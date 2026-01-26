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

// Handle MFA setup checkbox
document.getElementById('setupMfa')?.addEventListener('change', (e) => {
  const mfaSection = document.getElementById('mfaSetupSection');
  if(mfaSection){
    mfaSection.style.display = e.target.checked ? 'block' : 'none';
    if(!e.target.checked){
      // Reset MFA setup
      document.getElementById('mfaSecretValue').value = '';
      document.getElementById('mfaVerified').value = 'false';
      document.getElementById('mfaVerifyCodeSignup').value = '';
      document.getElementById('mfaQrCodeSignup').style.display = 'none';
      document.getElementById('mfaQrCodeLoadingSignup').style.display = 'block';
      document.getElementById('mfaQrCodeLoadingSignup').textContent = 'Click "Generate QR Code" to continue';
    }
  }
});

// Generate MFA QR code during signup
document.getElementById('generateMfaBtn')?.addEventListener('click', async () => {
  const btn = document.getElementById('generateMfaBtn');
  const qrContainer = document.getElementById('mfaQrCodeContainerSignup');
  const qrImg = document.getElementById('mfaQrCodeSignup');
  const qrLoading = document.getElementById('mfaQrCodeLoadingSignup');
  const secretInput = document.getElementById('mfaSecretSignup');
  const secretValueInput = document.getElementById('mfaSecretValue');
  
  if(!btn || !qrContainer || !qrImg || !qrLoading) return;
  
  btn.disabled = true;
  btn.textContent = 'Generating...';
  qrLoading.textContent = 'Loading QR code...';
  
  try {
    // We need to be logged in to generate MFA, so we'll do this after signup
    // For now, show a message that MFA will be set up after account creation
    qrLoading.innerHTML = '<div style="color: var(--primary);">MFA will be set up after your account is created. You can enable it in Settings or we\'ll prompt you on first login.</div>';
    btn.textContent = 'Will be set up after signup';
    btn.disabled = true;
  } catch(e) {
    qrLoading.textContent = 'Error: ' + (e.message || 'Failed to generate QR code');
    btn.disabled = false;
    btn.textContent = 'Generate QR Code';
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
    
    // Store plan selection for later use
    localStorage.setItem('selected_plan', plan);
    
    // Check if email verification is required
    const verificationRequired = response.verification_required === true;
    
    // Handle MFA setup if requested
    const setupMfa = document.getElementById('setupMfa')?.checked;
    if(setupMfa && response.token && !verificationRequired){
      // Save tokens for authenticated MFA setup
      setToken(response.token);
      if(response.refresh_token) setRefreshToken(response.refresh_token);
      
      // User wants to set up MFA - redirect to settings with auto-trigger
      msg.className = 'msg ok';
      msg.innerHTML = 'Account created! Redirecting to set up MFA...';
      showToast("Setting up MFA for your account...", "info");
      setTimeout(() => {
        window.location.href = '/settings?setupMfa=true';
      }, 1500);
      return;
    }
    
    // Save tokens (only if verification not required)
    if(!verificationRequired){
      setToken(response.token);
      if(response.refresh_token) setRefreshToken(response.refresh_token);
    } else {
      setToken(null);
      setRefreshToken(null);
    }
    
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