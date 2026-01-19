# Next Testing Steps - v1.0.0

## Quick Reference

**Current Status:** ✅ 90.9% test pass rate (10/11 tests)  
**Server Running:** http://localhost:8000  
**Last Verified:** January 19, 2026

## Immediate Testing Tasks

### 1. Test Email Verification End-to-End

**Without Email Server (Console Logging)**

```bash
# In terminal 1: Start server and watch logs
cd c:\IoT-security-app-python
python -m uvicorn main:app --reload --port 8000

# In terminal 2: Create a test user
curl -X POST http://localhost:8000/api/auth/signup \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test User",
    "email": "verify-test@example.com",
    "password": "VerifyPass4#8@Test9",
    "role": "consumer"
  }'

# Check server logs for verification link like:
# http://localhost:8000/verify-email?token=...
```

**Manual Browser Test:**

1. Open: http://localhost:8000/signup
2. Fill in form and submit
3. Check server terminal for verification link
4. Copy token from link
5. Navigate to: http://localhost:8000/verify-email?token=YOUR_TOKEN
6. Should see success message
7. Click "Sign in"
8. Login with credentials
9. Should redirect to dashboard

### 2. Test Password Reset End-to-End

**Using Browser:**

1. Navigate to: http://localhost:8000/forgot-password
2. Enter: `verify-test@example.com`
3. Click "Send Reset Link"
4. Check server terminal for reset link
5. Copy token from link
6. Navigate to: http://localhost:8000/reset-password?token=YOUR_TOKEN
7. Should see reset form
8. Enter new password: `NewPass4#8@Reset9`
9. Confirm password
10. Click "Reset Password"
11. Should redirect to login
12. Login with new password
13. Should succeed

**Using cURL:**

```bash
# 1. Request password reset
curl -X POST http://localhost:8000/api/auth/forgot-password \
  -H "Content-Type: application/json" \
  -d '{"email": "verify-test@example.com"}'

# 2. Check server logs for reset token

# 3. Verify token
curl http://localhost:8000/api/auth/verify-reset-token/YOUR_TOKEN

# 4. Reset password
curl -X POST http://localhost:8000/api/auth/reset-password \
  -H "Content-Type: application/json" \
  -d '{
    "token": "YOUR_TOKEN",
    "new_password": "NewPass4#8@Reset9"
  }'

# 5. Login with new password
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "verify-test@example.com",
    "password": "NewPass4#8@Reset9"
  }'
```

### 3. Test Login After Verification

**Scenario A: Verification NOT Required**

Current default (`REQUIRE_EMAIL_VERIFICATION=false`):

1. Create account
2. Login immediately (should work)
3. Access dashboard (should work)
4. Check user data shows `email_verified: false`

**Scenario B: Verification Required**

Update `.env`:
```env
REQUIRE_EMAIL_VERIFICATION=true
```

Restart server, then:

1. Create new account
2. Try to login → Should get 403 "Email not verified"
3. Verify email using token
4. Login again → Should succeed
5. Check user data shows `email_verified: true`

## Setup Email Testing (Optional)

### Option 1: MailHog (Recommended for Local Testing)

```bash
# Download MailHog for Windows
# From: https://github.com/mailhog/MailHog/releases

# Run MailHog
mailhog.exe

# MailHog SMTP: localhost:1025
# MailHog Web UI: http://localhost:8025
```

Update `.env`:
```env
SMTP_HOST=localhost
SMTP_PORT=1025
SMTP_USERNAME=
SMTP_PASSWORD=
EMAIL_FROM=noreply@iot-security.local
EMAIL_VERIFICATION_ENABLED=true
```

### Option 2: Gmail SMTP

1. Generate App Password in Google Account
2. Update `.env`:

```env
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your_email@gmail.com
SMTP_PASSWORD=your_app_password
EMAIL_FROM=your_email@gmail.com
EMAIL_VERIFICATION_ENABLED=true
```

### Option 3: Mailtrap (Testing Service)

```env
SMTP_HOST=sandbox.smtp.mailtrap.io
SMTP_PORT=2525
SMTP_USERNAME=your_mailtrap_username
SMTP_PASSWORD=your_mailtrap_password
EMAIL_FROM=noreply@iot-security.local
EMAIL_VERIFICATION_ENABLED=true
```

## Test Checklist

### Email Verification Flow

- [ ] Signup sends verification email
- [ ] Email contains correct link format
- [ ] Link opens verification page
- [ ] Valid token shows success message
- [ ] Invalid token shows error with resend form
- [ ] Expired token (24h+) shows error
- [ ] Resend verification works
- [ ] User can login after verification
- [ ] Database shows `email_verified: true`
- [ ] Verification token cleared from DB

### Password Reset Flow

- [ ] Forgot password page works
- [ ] Reset email sent successfully
- [ ] Email contains correct reset link
- [ ] Reset page verifies token on load
- [ ] Valid token shows reset form
- [ ] Invalid token shows error
- [ ] Expired token (1h+) shows error
- [ ] Password requirements displayed
- [ ] Weak password rejected
- [ ] Strong password accepted
- [ ] Success message shown
- [ ] Redirect to login works
- [ ] Login with new password succeeds
- [ ] Reset token cleared from DB

### Login After Verification

- [ ] Login page loads correctly
- [ ] Valid credentials accepted
- [ ] Invalid credentials rejected
- [ ] Unverified email blocked (if REQUIRE_EMAIL_VERIFICATION=true)
- [ ] JWT token received
- [ ] Refresh token received
- [ ] Dashboard accessible
- [ ] User data correct
- [ ] Account lockout after 5 failures
- [ ] Lockout message shown

## Database Verification Queries

### Check User Record

```javascript
// MongoDB shell or Compass
use iot_security

// Find user
db.users.findOne({email: "verify-test@example.com"})

// Should see:
// - email_verified: true (after verification)
// - email_verification_token: null (after verification)
// - reset_token: null (after password reset)
```

### Check Refresh Tokens

```javascript
// Find all tokens for user
db.refresh_tokens.find({user_id: "USER_ID_HERE"})

// Check:
// - revoked: false for active tokens
// - revoked: true for old tokens
// - expires_at: 30 days in future
```

### Check Token Rotation

```javascript
// Count active tokens per user
db.refresh_tokens.aggregate([
  {$match: {revoked: false}},
  {$group: {_id: "$user_id", count: {$sum: 1}}}
])

// Each user should have only 1-2 active tokens
```

## Performance Testing

### Load Test Login

```bash
# Install Apache Bench (if needed)
# Windows: Download from https://www.apachelounge.com/

# Test 100 concurrent login requests
ab -n 100 -c 10 -p login.json -T application/json \
  http://localhost:8000/api/auth/login

# login.json:
# {"email":"test@example.com","password":"TestPass4#8@Secure9"}
```

### Monitor Server

```bash
# Watch MongoDB connections
mongosh --eval "db.serverStatus().connections"

# Watch Python memory
# Task Manager > python.exe > Memory
```

## Security Testing

### Test Account Lockout

```bash
# Try 6 failed logins
for i in {1..6}; do
  curl -X POST http://localhost:8000/api/auth/login \
    -H "Content-Type: application/json" \
    -d '{"email":"test@example.com","password":"WrongPassword"}'
  echo "Attempt $i"
done

# 6th attempt should return 429 "Account temporarily locked"
```

### Test Rate Limiting

```bash
# Try 10 rapid signups (should hit rate limit)
for i in {1..10}; do
  curl -X POST http://localhost:8000/api/auth/signup \
    -H "Content-Type: application/json" \
    -d "{\"name\":\"Test$i\",\"email\":\"test$i@example.com\",\"password\":\"TestPass4#8@Secure9\",\"role\":\"consumer\"}"
  echo "Request $i"
done

# Should see rate limit error after 3 requests
```

### Test Token Expiration

```bash
# 1. Login and save token
TOKEN=$(curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"TestPass4#8@Secure9"}' \
  | jq -r '.token')

# 2. Use token immediately (should work)
curl http://localhost:8000/api/auth/me \
  -H "Authorization: Bearer $TOKEN"

# 3. Wait 24 hours + 1 minute
# 4. Try again (should get 401)
```

## Common Issues & Solutions

### Issue: Server Not Starting

```bash
# Check if port 8000 is already in use
netstat -ano | findstr :8000

# Kill process if needed
taskkill /PID <PID> /F

# Restart server
python -m uvicorn main:app --reload --port 8000
```

### Issue: MongoDB Connection Failed

```bash
# Check MongoDB is running
mongosh

# If not running, start MongoDB service
net start MongoDB

# Or start manually
mongod --dbpath C:\data\db
```

### Issue: Emails Not Sending

1. Check SMTP settings in `.env`
2. Verify credentials
3. Check server logs for email errors
4. Try MailHog for local testing
5. Emails appear in console if SMTP not configured

### Issue: Token Not Working

1. Check token hasn't expired
2. Verify token copied correctly (no spaces)
3. Check database for token hash
4. Try requesting new token

## Next Steps After Testing

1. **If all tests pass:**
   - Review VERIFICATION_RESULTS.md
   - Prepare for deployment
   - Configure production environment
   - Set up real email service

2. **If issues found:**
   - Document in GitHub issues
   - Check server logs
   - Review relevant code
   - Update tests as needed

3. **Future Enhancements:**
   - Multi-factor authentication (2FA)
   - OAuth/Social login
   - Password strength meter UI
   - Session management UI
   - Email notification preferences

## Quick Commands Reference

```bash
# Start server
python -m uvicorn main:app --reload --port 8000

# Run automated tests
python test_auth_flows.py

# Create test data
python create_test_data.py

# Test email directly
python test_email_direct.py

# MongoDB shell
mongosh

# View specific terminal output
cat C:\Users\anita\.cursor\projects\c-IoT-security-app-python\terminals\220245.txt
```

## Contact & Support

- GitHub: https://github.com/anitah1981/-iot-security-platform-python.git
- Docs: See `TESTING_GUIDE.md` for detailed instructions
- Results: See `VERIFICATION_RESULTS.md` for test summary

---

**Status:** Ready for manual verification testing  
**Next:** Complete email verification and password reset end-to-end tests
