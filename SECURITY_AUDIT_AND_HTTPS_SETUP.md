# 🔒 Security Audit & HTTPS Setup Guide

**Last Updated:** January 2026  
**Status:** Pre-Production Security Hardening

---

## ✅ Current Security Measures (Already Implemented)

### 1. **Authentication & Authorization**
- ✅ Strong password requirements (12+ chars, complexity)
- ✅ Bcrypt password hashing with proper salt
- ✅ JWT tokens with expiration
- ✅ Refresh token rotation
- ✅ Email verification flow
- ✅ Account lockout after failed attempts (5 attempts, 15min lockout)
- ✅ Multi-Factor Authentication (TOTP + backup codes)
- ✅ MFA code required at login when enabled

### 2. **Rate Limiting**
- ✅ Global rate limiting (120/min default)
- ✅ Stricter limits on auth endpoints:
  - Signup: 3/min
  - Login: 5/min
  - Password reset: 5/min
  - MFA operations: 5/min
  - Network scans: 5/min

### 3. **Input Validation**
- ✅ Pydantic models for all API inputs
- ✅ SQL injection pattern detection
- ✅ XSS pattern detection
- ✅ URL/query parameter sanitization
- ✅ E.164 phone number validation
- ✅ Email format validation

### 4. **Security Headers**
- ✅ X-Content-Type-Options: nosniff
- ✅ X-Frame-Options: DENY
- ✅ X-XSS-Protection: 1; mode=block
- ✅ HSTS (when HTTPS enabled)
- ✅ Content-Security-Policy
- ✅ Referrer-Policy
- ✅ Permissions-Policy

### 5. **Production Safety**
- ✅ Exception handler hides stack traces in production
- ✅ Public API docs disabled
- ✅ JWT_SECRET validation on startup (fails if default in prod)
- ✅ TrustedHostMiddleware (production only)
- ✅ HTTPS redirect middleware (production only)

---

## ⚠️ Security Gaps & Recommendations

### 🔴 **CRITICAL - Must Fix Before Production**

#### 1. **JWT Storage (High Risk)**
**Current:** JWTs stored in `localStorage`  
**Risk:** XSS attacks can steal tokens  
**Fix:** Use httpOnly cookies for refresh tokens
```javascript
// Current: localStorage.setItem("iot_token", token)
// Should be: httpOnly cookie set by server
```

#### 2. **JWT_SECRET Strength**
**Action Required:**
```bash
# Generate a strong secret (32+ characters)
python -c "import secrets; print(secrets.token_urlsafe(32))"
# Add to .env: JWT_SECRET=<generated-secret>
```

#### 3. **MongoDB Connection Security**
**Check:**
- ✅ Connection string uses credentials? (`mongodb://user:pass@host/db`)
- ✅ MongoDB requires authentication?
- ✅ Connection over TLS? (Use `mongodb+srv://` for Atlas)

#### 4. **Environment Variables**
**Missing in production:**
- `ALLOWED_HOSTS` - must be set to your domain(s)
- `CORS_ORIGINS` - restrict to your frontend domain
- `FORCE_HTTPS=true` - already default, verify

---

### 🟡 **HIGH PRIORITY - Fix Soon**

#### 5. **Token Refresh Logic**
**Issue:** Refresh tokens don't expire on password change or MFA enable  
**Recommendation:** Add token revocation on security events

#### 6. **Session Management**
**Missing:**
- Device fingerprinting
- "Active sessions" list in UI
- Ability to revoke specific sessions
- Login notifications for new devices

#### 7. **CSRF Protection**
**Missing:** CSRF tokens for state-changing operations  
**Impact:** Medium (mitigated by SameSite cookies if using cookies)  
**Priority:** Add if moving to cookie-based auth

#### 8. **API Response Sanitization**
**Current:** Some errors may leak user info  
**Fix:** Ensure all error messages are generic in production

#### 9. **Audit Logging**
**Current:** Basic request logging  
**Missing:**
- Security event logging (login, password change, MFA enable)
- Failed authentication attempts
- Admin actions
- IP address tracking
- User agent tracking

#### 10. **Password Reset Security**
**Check:**
- ✅ Reset tokens expire (implemented)
- ✅ Tokens are single-use (check implementation)
- ✅ Tokens are hashed in database (check)

---

### 🟢 **MEDIUM PRIORITY - Enhancements**

#### 11. **Content Security Policy**
**Current:** Allows `unsafe-inline` for scripts/styles  
**Enhancement:** Use nonces or hash-based CSP for better XSS protection

#### 12. **Rate Limiting Enhancement**
**Current:** Global limits, some endpoint-specific  
**Enhancement:**
- Per-user rate limiting
- Adaptive rate limiting (stricter for suspicious IPs)
- CAPTCHA after repeated failures

#### 13. **Database Indexes**
**Current:** Basic indexes  
**Missing:**
- Index on `refresh_tokens.expires_at` for cleanup
- Index on `users.lock_until` for lockout queries
- Compound indexes for common queries

#### 14. **Error Logging**
**Current:** Print statements  
**Enhancement:** Structured logging with levels
```python
# Replace print() with:
import logging
logger = logging.getLogger(__name__)
logger.error("Failed login attempt", extra={"email": email, "ip": ip})
```

#### 15. **Dependency Security**
**Action:**
```bash
pip install safety
safety check
# Review and update any vulnerable packages
```

---

## 🔐 HTTPS Setup Guide

### Option 1: Reverse Proxy (Recommended for Production)

Your app already has HTTPS redirect middleware. Set up Nginx/Caddy/Traefik as reverse proxy.

#### **Nginx Configuration**

1. **Install Nginx:**
```bash
# Ubuntu/Debian
sudo apt update && sudo apt install nginx

# CentOS/RHEL
sudo yum install nginx
```

2. **Get SSL Certificate (Let's Encrypt):**
```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com
```

3. **Nginx Config (`/etc/nginx/sites-available/iot-security`):**
```nginx
# HTTP → HTTPS redirect
server {
    listen 80;
    listen [::]:80;
    server_name yourdomain.com www.yourdomain.com;
    return 301 https://$server_name$request_uri;
}

# HTTPS server
server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name yourdomain.com www.yourdomain.com;

    # SSL certificates (Certbot will add these)
    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;
    
    # Modern SSL configuration
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers 'ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384';
    ssl_prefer_server_ciphers off;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;

    # Security headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains; preload" always;
    add_header X-Frame-Options "DENY" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;

    # Proxy to FastAPI app
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header X-Forwarded-Host $server_name;
        
        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # Static files (optional - serve directly from Nginx)
    location /assets/ {
        alias /path/to/IoT-security-app-python/web/assets/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }
}
```

4. **Enable and restart:**
```bash
sudo ln -s /etc/nginx/sites-available/iot-security /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

#### **Caddy (Easier Alternative)**

Caddy automatically handles HTTPS with Let's Encrypt:

1. **Install Caddy:**
```bash
sudo apt install -y debian-keyring debian-archive-keyring apt-transport-https
curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/gpg.key' | sudo gpg --dearmor -o /usr/share/keyrings/caddy-stable-archive-keyring.gpg
curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/debian.deb.txt' | sudo tee /etc/apt/sources.list.d/caddy-stable.list
sudo apt update
sudo apt install caddy
```

2. **Caddyfile (`/etc/caddy/Caddyfile`):**
```
yourdomain.com {
    reverse_proxy localhost:8000 {
        header_up X-Real-IP {remote_host}
        header_up X-Forwarded-For {remote_host}
        header_up X-Forwarded-Proto {scheme}
    }
}
```

3. **Start Caddy:**
```bash
sudo systemctl enable caddy
sudo systemctl start caddy
```

---

### Option 2: Cloud Provider (Automatic HTTPS)

#### **Railway / Render / Vercel**
- ✅ Automatic HTTPS
- ✅ Free SSL certificates
- ✅ Auto-renewal
- Just set your domain in their dashboard

#### **AWS (API Gateway / ALB)**
- Use AWS Certificate Manager (free)
- Automatic HTTPS termination
- Set `FORCE_HTTPS=true` in your app

#### **Cloudflare (Recommended)**
1. Point DNS to Cloudflare
2. Enable "Always Use HTTPS"
3. Enable "Full (strict)" SSL mode
4. Free SSL + DDoS protection + CDN

---

## 📋 Pre-Production Security Checklist

### Environment Variables
```bash
# REQUIRED
APP_ENV=production
JWT_SECRET=<32+ character random string>
MONGO_URI=mongodb+srv://user:pass@cluster.mongodb.net/iot_security
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
CORS_ORIGINS=https://yourdomain.com,https://www.yourdomain.com

# RECOMMENDED
FORCE_HTTPS=true
ENABLE_HSTS=true
APP_BASE_URL=https://yourdomain.com

# Email/SMS
SMTP_HOST=smtp.gmail.com
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
FROM_EMAIL=noreply@yourdomain.com

# Twilio
TWILIO_ACCOUNT_SID=your-sid
TWILIO_AUTH_TOKEN=your-token
TWILIO_PHONE_NUMBER=+1234567890
SMS_ENABLED=false  # Keep false until UK regulatory bundle

# Optional
JWT_EXPIRES_MINUTES=60  # Shorter for production
REFRESH_EXPIRES_DAYS=7  # Shorter for production
MAX_LOGIN_ATTEMPTS=5
LOCKOUT_MINUTES=15
RATE_LIMIT_DEFAULT=100/minute  # Stricter for production
```

### Code Hardening

#### 1. **Generate Strong JWT_SECRET**
```bash
python -c "import secrets; print('JWT_SECRET=' + secrets.token_urlsafe(32))"
```

#### 2. **Review All Rate-Limited Routes**
All sensitive endpoints should have `request: Request` parameter.

#### 3. **Test MFA Flow**
- ✅ Signup → Enable MFA → Login requires code
- ✅ Backup codes work
- ✅ MFA can be disabled with code

#### 4. **Test Security Headers**
```bash
curl -I https://yourdomain.com
# Verify all security headers present
```

#### 5. **Database Security**
- ✅ MongoDB requires authentication
- ✅ Connection uses TLS (`mongodb+srv://` or `?ssl=true`)
- ✅ Database user has minimal required permissions
- ✅ Regular backups enabled

---

## 🚀 Immediate Action Items

### Before Going Live:

1. **Generate and set JWT_SECRET**
   ```bash
   python -c "import secrets; print(secrets.token_urlsafe(32))"
   ```

2. **Set environment variables:**
   - `APP_ENV=production`
   - `ALLOWED_HOSTS=yourdomain.com`
   - `CORS_ORIGINS=https://yourdomain.com`
   - All API keys configured

3. **Set up HTTPS:**
   - Use reverse proxy (Nginx/Caddy) OR
   - Deploy to cloud provider with automatic HTTPS

4. **Enable MFA for admin accounts:**
   - All admin users should have MFA enabled
   - Test the flow end-to-end

5. **Set up monitoring:**
   - Error tracking (Sentry)
   - Uptime monitoring (UptimeRobot)
   - Log aggregation

6. **Database:**
   - Enable MongoDB authentication
   - Enable TLS connections
   - Set up automated backups

7. **Test production deployment:**
   - Deploy to staging environment first
   - Run security scan: `safety check`
   - Test all authentication flows
   - Verify HTTPS redirect works

---

## 📊 Security Testing

### Manual Testing Checklist:
- [ ] Can't access `/docs` without authentication
- [ ] Rate limiting works (try 10 rapid logins)
- [ ] Account locks after 5 failed attempts
- [ ] MFA required when enabled
- [ ] Password reset tokens expire
- [ ] HTTPS redirect works
- [ ] Security headers present
- [ ] No stack traces in error responses (production)
- [ ] Invalid JWT tokens rejected
- [ ] Refresh tokens rotate on use

### Automated Testing:
```bash
# Security scan dependencies
pip install safety bandit
safety check
bandit -r . -f json -o bandit-report.json

# Test HTTPS redirect
curl -I http://yourdomain.com
# Should return 307 redirect to https://
```

---

## 🔧 Additional Hardening Recommendations

### 1. **Add Request ID Tracking**
Track requests through logs for debugging:
```python
import uuid
request_id = str(uuid.uuid4())
```

### 2. **IP Whitelisting (Optional)**
For admin endpoints, consider IP whitelisting

### 3. **WAF (Web Application Firewall)**
Consider Cloudflare WAF or AWS WAF for DDoS protection

### 4. **Database Encryption at Rest**
Ensure MongoDB Atlas encryption is enabled

### 5. **Secrets Management**
For production, consider:
- AWS Secrets Manager
- HashiCorp Vault
- Kubernetes Secrets
- Never commit `.env` files

### 6. **Regular Security Updates**
```bash
# Weekly:
pip list --outdated
pip install --upgrade package-name

# Monthly:
safety check
bandit -r .
```

---

## 📝 Post-Deployment Security Tasks

### Weekly:
- Review error logs
- Check for suspicious login patterns
- Monitor rate limit violations

### Monthly:
- Update dependencies
- Review audit logs
- Test backup restoration
- Review active sessions

### Quarterly:
- Full security audit
- Penetration testing (optional)
- Review and rotate secrets
- Update security policies

---

## 🆘 Incident Response Plan

### If Security Breach Detected:

1. **Immediate:**
   - Rotate JWT_SECRET (invalidates all sessions)
   - Force password reset for affected users
   - Review audit logs

2. **Investigation:**
   - Check access logs
   - Identify affected accounts
   - Review database for unauthorized changes

3. **Recovery:**
   - Revoke all refresh tokens
   - Require MFA for all users
   - Notify affected users

---

## 📚 References

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [FastAPI Security](https://fastapi.tiangolo.com/tutorial/security/)
- [MongoDB Security Checklist](https://www.mongodb.com/docs/manual/administration/security-checklist/)
- [Let's Encrypt Documentation](https://letsencrypt.org/docs/)

---

**Next Steps:**
1. Generate and set `JWT_SECRET`
2. Configure reverse proxy for HTTPS
3. Set all production environment variables
4. Test all security flows
5. Enable monitoring and alerting
