# 🔒 Production Security Checklist

Use this checklist before deploying to production.

**See also:** [SECURITY_AND_AVAILABILITY.md](SECURITY_AND_AVAILABILITY.md) for offline detection thresholds, multi-port coverage for IoT devices, and CIA (Confidentiality, Integrity, Availability) alignment.

## Pre-Deployment

### Critical Security

- [ ] **JWT_SECRET Generated & Set**
  ```bash
  python scripts/generate_secrets.py
  # Copy JWT_SECRET to .env
  ```
  - [ ] Secret is 32+ characters
  - [ ] Secret is random (not a word/password)
  - [ ] Secret is stored securely (not in code/git)

- [ ] **Environment Variables Set**
  - [ ] `APP_ENV=production`
  - [ ] `JWT_SECRET=<generated-secret>`
  - [ ] `ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com`
  - [ ] `CORS_ORIGINS=https://yourdomain.com`
  - [ ] `FORCE_HTTPS=true`
  - [ ] `MONGO_URI` with authentication
  - [ ] All API keys configured (SMTP, Twilio, Stripe)

- [ ] **HTTPS Configured**
  - [ ] SSL certificate installed (Let's Encrypt or provider)
  - [ ] HTTP → HTTPS redirect working
  - [ ] Certificate auto-renewal configured
  - [ ] Tested: `curl -I http://yourdomain.com` returns 307

- [ ] **Database Security**
  - [ ] MongoDB requires authentication
  - [ ] Connection uses TLS (`mongodb+srv://` or `?ssl=true`)
  - [ ] Database user has minimal permissions
  - [ ] Automated backups enabled
  - [ ] Backup restoration tested

- [ ] **MFA Setup**
  - [ ] MFA working for test account
  - [ ] Backup codes stored securely
  - [ ] MFA required at login when enabled
  - [ ] MFA can be disabled with code

### Authentication & Authorization

- [ ] **Password Security**
  - [ ] Strong password requirements enforced (12+ chars, complexity)
  - [ ] Passwords hashed with bcrypt
  - [ ] Password reset flow tested
  - [ ] Old passwords rejected on change

- [ ] **Account Security**
  - [ ] Account lockout after 5 failed attempts
  - [ ] Lockout duration tested (15 minutes)
  - [ ] Email verification working
  - [ ] Admin unlock account feature tested

- [ ] **Session Management**
  - [ ] JWT tokens expire (check JWT_EXPIRES_MINUTES)
  - [ ] Refresh tokens rotate on use
  - [ ] Logout invalidates refresh tokens
  - [ ] "Sign out all devices" works

### Rate Limiting

- [ ] **Rate Limits Tested**
  - [ ] Signup: 3/minute (test by trying 4x rapidly)
  - [ ] Login: 5/minute
  - [ ] Password reset: 5/minute
  - [ ] MFA operations: 5/minute
  - [ ] General API: 100-120/minute

### API Security

- [ ] **Input Validation**
  - [ ] All endpoints validate input (Pydantic models)
  - [ ] SQL injection patterns blocked
  - [ ] XSS patterns blocked
  - [ ] Phone numbers validated (E.164)
  - [ ] Email format validated

- [ ] **Error Handling**
  - [ ] No stack traces in production responses
  - [ ] Generic error messages (no sensitive info leaked)
  - [ ] 500 errors return safe message

- [ ] **Security Headers**
  ```bash
  curl -I https://yourdomain.com
  ```
  - [ ] `X-Content-Type-Options: nosniff`
  - [ ] `X-Frame-Options: DENY`
  - [ ] `X-XSS-Protection: 1; mode=block`
  - [ ] `Strict-Transport-Security` present (HTTPS only)
  - [ ] `Content-Security-Policy` present
  - [ ] `Referrer-Policy` present

### Access Control

- [ ] **API Documentation**
  - [ ] `/docs` requires authentication
  - [ ] `/redoc` requires authentication
  - [ ] Public endpoints don't expose sensitive info

- [ ] **Admin Features**
  - [ ] Admin unlock account tested
  - [ ] Network monitoring only for admins
  - [ ] Audit logs accessible to admins

## Testing

### Security Testing

- [ ] **Authentication Flows**
  - [ ] Signup → Email verification → Login
  - [ ] Signup → MFA setup → Login with MFA
  - [ ] Password reset → Login with new password
  - [ ] Failed login → Account lockout → Wait → Login works

- [ ] **MFA Testing**
  - [ ] Enable MFA → QR code displays
  - [ ] Scan QR code → Code works
  - [ ] Login requires MFA code
  - [ ] Backup codes work for login
  - [ ] Backup codes are single-use
  - [ ] MFA can be disabled

- [ ] **Rate Limiting**
  - [ ] Rapid signup attempts blocked
  - [ ] Rapid login attempts blocked
  - [ ] Account locks after 5 failures

- [ ] **HTTPS**
  - [ ] HTTP redirects to HTTPS
  - [ ] HTTPS works on all pages
  - [ ] Mixed content warnings absent
  - [ ] SSL certificate valid

### Functional Testing

- [ ] All user flows work over HTTPS
- [ ] Notifications work (Email, WhatsApp, Voice)
- [ ] Device management works
- [ ] Alert creation/resolution works
- [ ] Dashboard loads correctly
- [ ] Settings page works

## Monitoring & Logging

- [ ] **Error Tracking**
  - [ ] Error logging configured
  - [ ] Error aggregation service (Sentry) set up
  - [ ] Alerts configured for critical errors

- [ ] **Uptime Monitoring**
  - [ ] Service monitors `/api/health`
  - [ ] Alerts on downtime
  - [ ] Response time monitoring

- [ ] **Security Monitoring**
  - [ ] Failed login attempts logged
  - [ ] Rate limit violations logged
  - [ ] Admin actions logged
  - [ ] Unusual patterns detected

## Documentation

- [ ] **Deployment Docs**
  - [ ] README updated with deployment steps
  - [ ] Environment variables documented
  - [ ] HTTPS setup documented
  - [ ] Security best practices documented

- [ ] **Runbooks**
  - [ ] Incident response plan documented
  - [ ] Backup/restore procedures documented
  - [ ] Secret rotation procedures documented

## Post-Deployment

### Immediate (Within 24 hours)

- [ ] Verify HTTPS working
- [ ] Test all authentication flows
- [ ] Check security headers
- [ ] Verify rate limiting works
- [ ] Test MFA end-to-end
- [ ] Review error logs
- [ ] Set up monitoring alerts

### First Week

- [ ] Monitor error rates
- [ ] Review access logs for suspicious activity
- [ ] Test backup restoration
- [ ] Verify all notifications working
- [ ] Check database performance
- [ ] Review security headers with security scanner

### First Month

- [ ] Security audit
- [ ] Dependency update check (`pip list --outdated`)
- [ ] Review and optimize rate limits
- [ ] Analyze usage patterns
- [ ] Update documentation

---

## Quick Security Test Script

```bash
#!/bin/bash
# Quick security check

DOMAIN="yourdomain.com"

echo "Testing HTTPS redirect..."
curl -I http://$DOMAIN | grep -i "location.*https"

echo "Testing security headers..."
curl -I https://$DOMAIN | grep -E "(X-Content-Type|X-Frame|X-XSS|Strict-Transport)"

echo "Testing rate limiting..."
for i in {1..6}; do
  curl -X POST https://$DOMAIN/api/auth/login \
    -H "Content-Type: application/json" \
    -d '{"email":"test@test.com","password":"wrong"}' \
    -w "\nHTTP Status: %{http_code}\n"
done

echo "Testing API docs protection..."
curl -I https://$DOMAIN/docs | grep -E "(401|403)"
```

---

**Last Updated:** January 2026  
**Review Frequency:** Before each production deployment
