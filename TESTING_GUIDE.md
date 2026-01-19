# Testing Guide - v1.0.0

## Overview

This guide covers end-to-end testing of authentication flows, email verification, and password reset functionality for the IoT Security Platform.

## Test Environment Setup

### 1. Environment Configuration

Create or update your `.env` file with these settings:

```env
# MongoDB
MONGO_URI=mongodb://localhost:27017/iot_security

# JWT Configuration
JWT_SECRET=your-super-secret-key-change-in-production
JWT_EXPIRES_MINUTES=1440
REFRESH_EXPIRES_DAYS=30

# Email Verification
REQUIRE_EMAIL_VERIFICATION=false  # Set to true to test verification blocking
EMAIL_VERIFICATION_ENABLED=true   # Enable sending verification emails
VERIFICATION_EXPIRES_HOURS=24

# Password Reset
APP_BASE_URL=http://localhost:8000

# Email Configuration (for testing)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your_email@gmail.com
SMTP_PASSWORD=your_app_password
EMAIL_FROM=your_email@gmail.com

# Account Lockout
MAX_LOGIN_ATTEMPTS=5
LOCKOUT_MINUTES=15

# Application
APP_ENV=local
PORT=8000
```

### 2. Start the Server

```bash
cd c:\IoT-security-app-python
uvicorn main:app --reload --port 8000
```

The server should start at `http://localhost:8000`

## Automated Tests

### Run Authentication Flow Tests

```bash
python test_auth_flows.py
```

This script tests:
- ✅ User signup with strong password validation
- ✅ Duplicate account prevention
- ✅ Email verification flow
- ✅ Login with verified/unverified accounts
- ✅ Password reset request
- ✅ Token refresh and rotation
- ✅ Protected endpoint access
- ✅ Invalid token rejection
- ✅ Logout and token revocation

## Manual Testing Scenarios

### Scenario 1: Complete Signup Flow

1. **Navigate to Signup Page**
   - Open: `http://localhost:8000/signup`
   - Should see plan selection and signup form

2. **Create Account**
   - Fill in:
     - Name: Test User
     - Email: testuser@example.com
     - Password: TestPass123!@#Secure
   - Accept terms
   - Click "Start Free Trial"

3. **Check Response**
   - Should see success message
   - If `EMAIL_VERIFICATION_ENABLED=true`, should see verification notice
   - Should redirect to dashboard or verification page

4. **Check Email** (if email configured)
   - Should receive verification email
   - Email should contain verification link
   - Link format: `http://localhost:8000/verify-email?token=...`

### Scenario 2: Email Verification

1. **Without Verification**
   - Try to login with unverified account
   - If `REQUIRE_EMAIL_VERIFICATION=true`:
     - Should get error: "Email not verified"
   - If `REQUIRE_EMAIL_VERIFICATION=false`:
     - Login should succeed with warning

2. **Verify Email**
   - Click verification link from email OR
   - Navigate to: `http://localhost:8000/verify-email?token=YOUR_TOKEN`
   - Should see success message: "Email verified successfully"
   - Should have button to sign in

3. **Login After Verification**
   - Go to: `http://localhost:8000/login`
   - Enter credentials
   - Should login successfully
   - Should redirect to dashboard

### Scenario 3: Resend Verification Email

1. **Navigate to Verification Page**
   - Open: `http://localhost:8000/verify-email`
   - Without token parameter

2. **Request New Email**
   - Enter email address
   - Click "Resend verification email"
   - Should see: "Verification email sent"

3. **Check Email**
   - Should receive new verification email
   - Old token should be invalidated

### Scenario 4: Password Reset Flow

1. **Request Password Reset**
   - Go to: `http://localhost:8000/forgot-password`
   - Enter email address
   - Click "Send Reset Link"
   - Should see: "If an account exists..."

2. **Check Email**
   - Should receive password reset email
   - Email contains reset link
   - Link format: `http://localhost:8000/reset-password?token=...`
   - Token expires in 1 hour

3. **Reset Password**
   - Click reset link
   - Page should verify token (loading state)
   - If valid: Shows reset form with email
   - If invalid/expired: Shows error with "Request New Link" button

4. **Set New Password**
   - Enter new password: NewPass456!@#Secure
   - Confirm password
   - Click "Reset Password"
   - Should see success message
   - Should redirect to login page after 2 seconds

5. **Login with New Password**
   - Go to login page
   - Use new password
   - Should login successfully

### Scenario 5: Invalid Token Handling

1. **Invalid Verification Token**
   - Navigate to: `http://localhost:8000/verify-email?token=invalid`
   - Should see error: "Invalid or expired verification link"
   - Should show resend form

2. **Invalid Reset Token**
   - Navigate to: `http://localhost:8000/reset-password?token=invalid`
   - Should see error: "Invalid or Expired Link"
   - Should show "Request New Link" button

3. **Expired Tokens**
   - Wait for token expiration (1 hour for reset, 24 hours for verification)
   - Try to use expired token
   - Should get same error as invalid token

### Scenario 6: Password Strength Validation

Test that weak passwords are rejected:

1. **Too Short**
   - Password: `Short1!`
   - Should reject: "Minimum 12 characters"

2. **No Uppercase**
   - Password: `alllowercase123!`
   - Should reject: "At least one uppercase letter"

3. **No Lowercase**
   - Password: `ALLUPPERCASE123!`
   - Should reject: "At least one lowercase letter"

4. **No Numbers**
   - Password: `NoNumbers!@#Abc`
   - Should reject: "At least one number"

5. **No Special Characters**
   - Password: `NoSpecialChars123`
   - Should reject: "At least one special character"

### Scenario 7: Account Lockout

1. **Failed Login Attempts**
   - Try to login with wrong password
   - Repeat 5 times (MAX_LOGIN_ATTEMPTS)
   - On 6th attempt: Should get "Account temporarily locked"

2. **Lockout Duration**
   - Wait 15 minutes (LOCKOUT_MINUTES)
   - Try to login again with correct password
   - Should succeed

### Scenario 8: Token Refresh

1. **Login and Get Tokens**
   - Login successfully
   - Save both `token` and `refresh_token` from response

2. **Use Refresh Token**
   - POST to `/api/auth/refresh`
   - Body: `{"refresh_token": "YOUR_REFRESH_TOKEN"}`
   - Should get new `token` and new `refresh_token`

3. **Old Refresh Token Revoked**
   - Try to use old refresh token again
   - Should get 401 Unauthorized

### Scenario 9: Logout and Revocation

1. **Login**
   - Get access and refresh tokens

2. **Logout**
   - POST to `/api/auth/logout`
   - Headers: `Authorization: Bearer YOUR_TOKEN`
   - Body: `{"refresh_token": "YOUR_REFRESH_TOKEN"}`

3. **Verify Revocation**
   - Try to refresh with old refresh token
   - Should fail with 401

## API Endpoint Testing

### Health Check
```bash
curl http://localhost:8000/health
```

### Signup
```bash
curl -X POST http://localhost:8000/api/auth/signup \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test User",
    "email": "test@example.com",
    "password": "TestPass123!@#Secure",
    "role": "consumer"
  }'
```

### Login
```bash
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "TestPass123!@#Secure"
  }'
```

### Verify Email
```bash
curl "http://localhost:8000/api/auth/verify-email?token=YOUR_TOKEN"
```

### Resend Verification
```bash
curl -X POST http://localhost:8000/api/auth/resend-verification \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com"}'
```

### Forgot Password
```bash
curl -X POST http://localhost:8000/api/auth/forgot-password \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com"}'
```

### Reset Password
```bash
curl -X POST http://localhost:8000/api/auth/reset-password \
  -H "Content-Type: application/json" \
  -d '{
    "token": "YOUR_RESET_TOKEN",
    "new_password": "NewPass456!@#Secure"
  }'
```

### Get Current User
```bash
curl http://localhost:8000/api/auth/me \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Refresh Token
```bash
curl -X POST http://localhost:8000/api/auth/refresh \
  -H "Content-Type: application/json" \
  -d '{"refresh_token": "YOUR_REFRESH_TOKEN"}'
```

### Logout
```bash
curl -X POST http://localhost:8000/api/auth/logout \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"refresh_token": "YOUR_REFRESH_TOKEN"}'
```

## Email Testing

### Option 1: Gmail SMTP (Development)

1. **Create App Password**
   - Go to Google Account settings
   - Security → 2-Step Verification → App passwords
   - Generate password for "Mail"

2. **Configure .env**
   ```env
   SMTP_HOST=smtp.gmail.com
   SMTP_PORT=587
   SMTP_USERNAME=your_email@gmail.com
   SMTP_PASSWORD=your_app_password
   EMAIL_FROM=your_email@gmail.com
   ```

### Option 2: MailHog (Local Testing)

1. **Install MailHog**
   ```bash
   # Windows (via Chocolatey)
   choco install mailhog
   
   # Or download from: https://github.com/mailhog/MailHog/releases
   ```

2. **Start MailHog**
   ```bash
   mailhog
   ```

3. **Configure .env**
   ```env
   SMTP_HOST=localhost
   SMTP_PORT=1025
   SMTP_USERNAME=
   SMTP_PASSWORD=
   EMAIL_FROM=noreply@iot-security.local
   ```

4. **View Emails**
   - Open: `http://localhost:8025`
   - All emails appear here

### Option 3: Console Logging (No Email)

If no SMTP configured, emails are logged to console:

```bash
# Check server logs for email content
# Look for lines containing verification links and reset tokens
```

## Database Verification

### Check User Record

```javascript
// MongoDB shell
use iot_security

// Find user
db.users.findOne({email: "test@example.com"})

// Check fields:
// - email_verified: should be true after verification
// - email_verification_token: should be cleared after verification
// - reset_token: should be set after forgot password
// - reset_token_expires: should be 1 hour in future
```

### Check Refresh Tokens

```javascript
// Find refresh tokens for user
db.refresh_tokens.find({user_id: ObjectId("USER_ID")})

// Check fields:
// - revoked: false for active tokens
// - expires_at: should be 30 days in future
```

## Common Issues and Solutions

### Issue: "SMTP connection failed"
**Solution:** Verify SMTP credentials and app password in .env

### Issue: "Email not verified" but can't find email
**Solution:** 
- Check server logs for email content
- Or use resend verification
- Or set `REQUIRE_EMAIL_VERIFICATION=false` for testing

### Issue: "Invalid or expired verification link"
**Solution:**
- Token may have expired (24 hours)
- Request new verification email

### Issue: "Account temporarily locked"
**Solution:**
- Wait 15 minutes, or
- Admin can unlock via `/api/auth/unlock/{user_id}`

### Issue: Password reset not working
**Solution:**
- Check token hasn't expired (1 hour)
- Verify password meets strength requirements
- Check server logs for errors

## Security Testing Checklist

- [ ] Weak passwords are rejected
- [ ] Duplicate accounts prevented
- [ ] Email verification blocking works (if enabled)
- [ ] Invalid tokens rejected (401)
- [ ] Expired tokens rejected
- [ ] Account lockout after 5 failed attempts
- [ ] Lockout expires after 15 minutes
- [ ] Refresh token rotation works
- [ ] Old refresh tokens revoked on logout
- [ ] Protected endpoints require valid JWT
- [ ] Password reset tokens expire after 1 hour
- [ ] Verification tokens expire after 24 hours
- [ ] No sensitive data in error messages
- [ ] Rate limiting works on auth endpoints

## Test Coverage

### Current Features (v1.0.0)

✅ **Implemented and Tested:**
- User signup with strong password validation
- Email verification flow (send, verify, resend)
- Password reset flow (request, verify token, reset)
- Login with email/password
- JWT access tokens (24 hour expiry)
- Refresh tokens with rotation (30 day expiry)
- Account lockout after failed attempts
- Protected endpoint access
- Logout and token revocation
- Duplicate account prevention
- Invalid/expired token handling

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `REQUIRE_EMAIL_VERIFICATION` | false | Block login until email verified |
| `EMAIL_VERIFICATION_ENABLED` | false | Send verification emails |
| `VERIFICATION_EXPIRES_HOURS` | 24 | Verification token expiry |
| `JWT_EXPIRES_MINUTES` | 1440 | Access token expiry (24h) |
| `REFRESH_EXPIRES_DAYS` | 30 | Refresh token expiry |
| `MAX_LOGIN_ATTEMPTS` | 5 | Failed attempts before lockout |
| `LOCKOUT_MINUTES` | 15 | Account lockout duration |

## Next Steps

1. Run automated tests: `python test_auth_flows.py`
2. Test each manual scenario above
3. Verify email delivery (if configured)
4. Check database records after each operation
5. Test security measures (lockout, token expiry)
6. Review server logs for any errors

## Support

For issues or questions:
- Check server logs in terminal
- Review MongoDB records
- Verify environment variables
- Check this guide's Common Issues section
