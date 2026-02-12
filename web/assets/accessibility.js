/**
 * Accessibility & UX Improvements
 * 
 * CIA Principles Applied:
 * - Confidentiality: Secure form handling, no data leakage
 * - Integrity: Input validation, error prevention
 * - Availability: Accessible to all users, graceful degradation
 */

// ============================================================================
// Accessibility Helpers
// ============================================================================

/**
 * Announce message to screen readers
 */
function announceToScreenReader(message, priority = 'polite') {
  const announcer = document.getElementById('sr-announcer') || createScreenReaderAnnouncer();
  announcer.setAttribute('aria-live', priority);
  announcer.textContent = message;
  
  // Clear after announcement
  setTimeout(() => {
    announcer.textContent = '';
  }, 1000);
}

/**
 * Create screen reader announcer element
 */
function createScreenReaderAnnouncer() {
  const announcer = document.createElement('div');
  announcer.id = 'sr-announcer';
  announcer.setAttribute('aria-live', 'polite');
  announcer.setAttribute('aria-atomic', 'true');
  announcer.className = 'sr-only';
  announcer.style.cssText = 'position: absolute; left: -10000px; width: 1px; height: 1px; overflow: hidden;';
  document.body.appendChild(announcer);
  return announcer;
}

/**
 * Trap focus within a modal/drawer
 */
function trapFocus(element) {
  const focusableElements = element.querySelectorAll(
    'a[href], button:not([disabled]), textarea:not([disabled]), input:not([disabled]), select:not([disabled]), [tabindex]:not([tabindex="-1"])'
  );
  
  const firstElement = focusableElements[0];
  const lastElement = focusableElements[focusableElements.length - 1];
  
  function handleTab(e) {
    if (e.key !== 'Tab') return;
    
    if (e.shiftKey) {
      if (document.activeElement === firstElement) {
        e.preventDefault();
        lastElement.focus();
      }
    } else {
      if (document.activeElement === lastElement) {
        e.preventDefault();
        firstElement.focus();
      }
    }
  }
  
  element.addEventListener('keydown', handleTab);
  
  // Focus first element
  if (firstElement) {
    firstElement.focus();
  }
  
  // Return cleanup function
  return () => {
    element.removeEventListener('keydown', handleTab);
  };
}

/**
 * Add skip navigation link
 */
function addSkipNavigation() {
  if (document.getElementById('skip-nav')) return;
  
  const skipLink = document.createElement('a');
  skipLink.id = 'skip-nav';
  skipLink.href = '#main-content';
  skipLink.textContent = 'Skip to main content';
  skipLink.className = 'skip-link';
  skipLink.style.cssText = `
    position: absolute;
    top: -40px;
    left: 0;
    background: var(--primary);
    color: white;
    padding: 8px 16px;
    text-decoration: none;
    z-index: 10000;
    border-radius: 0 0 4px 0;
  `;
  skipLink.addEventListener('focus', function() {
    this.style.top = '0';
  });
  skipLink.addEventListener('blur', function() {
    this.style.top = '-40px';
  });
  
  document.body.insertBefore(skipLink, document.body.firstChild);
}

// ============================================================================
// Form Validation & UX
// ============================================================================

/**
 * Show inline field error
 */
function showFieldError(field, message) {
  // Remove existing error
  const existingError = field.parentElement.querySelector('.field-error');
  if (existingError) {
    existingError.remove();
  }
  
  // Remove error class
  field.classList.remove('error');
  
  // Add error message
  if (message) {
    field.classList.add('error');
    const errorDiv = document.createElement('div');
    errorDiv.className = 'field-error';
    errorDiv.setAttribute('role', 'alert');
    errorDiv.setAttribute('aria-live', 'polite');
    errorDiv.textContent = message;
    errorDiv.style.cssText = 'color: var(--danger); font-size: 13px; margin-top: 4px;';
    field.parentElement.appendChild(errorDiv);
    
    // Announce to screen reader
    announceToScreenReader(`Error: ${message}`, 'assertive');
    
    // Focus field if not already focused
    if (document.activeElement !== field) {
      field.focus();
    }
  }
}

/**
 * Show inline field success
 */
function showFieldSuccess(field, message) {
  const existingSuccess = field.parentElement.querySelector('.field-success');
  if (existingSuccess) {
    existingSuccess.remove();
  }
  
  if (message) {
    field.classList.add('success');
    const successDiv = document.createElement('div');
    successDiv.className = 'field-success';
    successDiv.setAttribute('aria-live', 'polite');
    successDiv.textContent = message;
    successDiv.style.cssText = 'color: var(--ok); font-size: 13px; margin-top: 4px;';
    field.parentElement.appendChild(successDiv);
  }
}

/**
 * Clear field validation state
 */
function clearFieldValidation(field) {
  field.classList.remove('error', 'success');
  const error = field.parentElement.querySelector('.field-error');
  const success = field.parentElement.querySelector('.field-success');
  if (error) error.remove();
  if (success) success.remove();
}

/**
 * Validate email format
 */
function validateEmail(email) {
  const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  return re.test(email);
}

/**
 * Get password strength
 */
function getPasswordStrength(password) {
  if (!password) return { strength: 0, label: '', color: '' };
  
  let strength = 0;
  if (password.length >= 8) strength++;
  if (password.length >= 12) strength++;
  if (/[a-z]/.test(password)) strength++;
  if (/[A-Z]/.test(password)) strength++;
  if (/[0-9]/.test(password)) strength++;
  if (/[^a-zA-Z0-9]/.test(password)) strength++;
  
  const levels = [
    { label: 'Very Weak', color: 'var(--danger)' },
    { label: 'Weak', color: 'var(--warning)' },
    { label: 'Fair', color: 'var(--warning)' },
    { label: 'Good', color: 'var(--ok)' },
    { label: 'Strong', color: 'var(--ok)' },
    { label: 'Very Strong', color: 'var(--ok)' }
  ];
  
  return {
    strength,
    label: levels[Math.min(strength, levels.length - 1)].label,
    color: levels[Math.min(strength, levels.length - 1)].color
  };
}

// ============================================================================
// Loading States
// ============================================================================

/**
 * Show loading state on button
 */
function setButtonLoading(button, loading, text) {
  if (!button) return;
  
  if (loading) {
    button.dataset.originalText = button.textContent;
    button.disabled = true;
    button.setAttribute('aria-busy', 'true');
    button.textContent = text || 'Loading...';
    
    // Add spinner if not present
    if (!button.querySelector('.spinner')) {
      const spinner = document.createElement('span');
      spinner.className = 'spinner';
      spinner.setAttribute('aria-hidden', 'true');
      spinner.style.cssText = `
        display: inline-block;
        width: 14px;
        height: 14px;
        border: 2px solid currentColor;
        border-top-color: transparent;
        border-radius: 50%;
        animation: spin 0.6s linear infinite;
        margin-right: 8px;
        vertical-align: middle;
      `;
      button.insertBefore(spinner, button.firstChild);
    }
  } else {
    button.disabled = false;
    button.removeAttribute('aria-busy');
    if (button.dataset.originalText) {
      button.textContent = button.dataset.originalText;
      delete button.dataset.originalText;
    }
    const spinner = button.querySelector('.spinner');
    if (spinner) spinner.remove();
  }
}

/**
 * Show loading overlay
 */
function showLoadingOverlay(message = 'Loading...') {
  const overlay = document.getElementById('loading-overlay') || createLoadingOverlay();
  overlay.querySelector('.loading-message').textContent = message;
  overlay.setAttribute('aria-busy', 'true');
  overlay.setAttribute('aria-live', 'polite');
  overlay.style.display = 'flex';
  announceToScreenReader(message);
}

/**
 * Hide loading overlay
 */
function hideLoadingOverlay() {
  const overlay = document.getElementById('loading-overlay');
  if (overlay) {
    overlay.style.display = 'none';
    overlay.removeAttribute('aria-busy');
  }
}

/**
 * Create loading overlay element
 */
function createLoadingOverlay() {
  const overlay = document.createElement('div');
  overlay.id = 'loading-overlay';
  overlay.setAttribute('role', 'status');
  overlay.setAttribute('aria-live', 'polite');
  overlay.style.cssText = `
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: rgba(11, 18, 32, 0.9);
    display: none;
    align-items: center;
    justify-content: center;
    z-index: 10000;
    flex-direction: column;
    gap: 16px;
  `;
  
  const spinner = document.createElement('div');
  spinner.className = 'loading-spinner';
  spinner.style.cssText = `
    width: 40px;
    height: 40px;
    border: 4px solid var(--border);
    border-top-color: var(--primary);
    border-radius: 50%;
    animation: spin 0.8s linear infinite;
  `;
  
  const message = document.createElement('div');
  message.className = 'loading-message';
  message.style.cssText = 'color: var(--text); font-size: 16px;';
  message.textContent = 'Loading...';
  
  overlay.appendChild(spinner);
  overlay.appendChild(message);
  document.body.appendChild(overlay);
  
  return overlay;
}

// ============================================================================
// Error Handling
// ============================================================================

/**
 * Format API error for display
 */
function formatError(error) {
  if (typeof error === 'string') {
    return error;
  }
  
  if (error.detail) {
    if (typeof error.detail === 'object' && error.detail.errors) {
      // Validation errors
      const errors = Object.entries(error.detail.errors)
        .map(([field, messages]) => `${field}: ${Array.isArray(messages) ? messages.join(', ') : messages}`)
        .join('. ');
      return errors || 'Validation error';
    }
    return error.detail;
  }
  
  if (error.message) {
    return error.message;
  }
  
  return 'An error occurred. Please try again.';
}

/**
 * Show user-friendly error message
 */
function showError(message, options = {}) {
  const {
    title = 'Error',
    duration = 5000,
    persistent = false
  } = options;
  
  // Use existing toast if available
  if (typeof showToast === 'function') {
    showToast(message, 'error', duration);
    return;
  }
  
  // Fallback to alert
  alert(`${title}: ${message}`);
}

// ============================================================================
// Keyboard Navigation
// ============================================================================

/**
 * Handle Escape key to close modals
 */
function setupEscapeKeyHandler() {
  document.addEventListener('keydown', function(e) {
    if (e.key === 'Escape') {
      // Close any open modals/drawers
      const modals = document.querySelectorAll('[role="dialog"][aria-hidden="false"]');
      modals.forEach(modal => {
        const closeButton = modal.querySelector('[aria-label*="close" i], [aria-label*="Close"]');
        if (closeButton) {
          closeButton.click();
        }
      });
      
      // Close drawers
      const drawers = document.querySelectorAll('.drawer:not([aria-hidden="true"])');
      drawers.forEach(drawer => {
        const hideFunction = drawer.dataset.hideFunction;
        if (hideFunction && typeof window[hideFunction] === 'function') {
          window[hideFunction]();
        }
      });
    }
  });
}

// ============================================================================
// Initialize on DOM ready
// ============================================================================

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', function() {
    addSkipNavigation();
    setupEscapeKeyHandler();
    createScreenReaderAnnouncer();
  });
} else {
  addSkipNavigation();
  setupEscapeKeyHandler();
  createScreenReaderAnnouncer();
}

// Add CSS animation for spinner
if (!document.getElementById('accessibility-styles')) {
  const style = document.createElement('style');
  style.id = 'accessibility-styles';
  style.textContent = `
    @keyframes spin {
      to { transform: rotate(360deg); }
    }
    
    .skip-link:focus {
      top: 0 !important;
    }
    
    input.error, textarea.error, select.error {
      border-color: var(--danger) !important;
      box-shadow: 0 0 0 3px rgba(239, 68, 68, 0.1) !important;
    }
    
    input.success, textarea.success, select.success {
      border-color: var(--ok) !important;
    }
    
    input:focus, textarea:focus, select:focus, button:focus {
      outline: 2px solid var(--primary);
      outline-offset: 2px;
    }
    
    .sr-only {
      position: absolute;
      left: -10000px;
      width: 1px;
      height: 1px;
      overflow: hidden;
    }
  `;
  document.head.appendChild(style);
}
