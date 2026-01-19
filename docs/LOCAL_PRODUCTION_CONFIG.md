# Local Production Configuration

Use this guide to run a hardened local instance (staging-style) before cloud deployment.

## Recommended environment variables

```
APP_ENV=production
APP_BASE_URL=https://your-domain.example

JWT_SECRET=replace-with-strong-secret
JWT_ISSUER=iot-security-platform
JWT_EXPIRES_MINUTES=60
REFRESH_EXPIRES_DAYS=30

REQUIRE_EMAIL_VERIFICATION=true
EMAIL_VERIFICATION_ENABLED=true
VERIFICATION_EXPIRES_HOURS=24

CORS_ORIGINS=https://your-domain.example
ALLOWED_HOSTS=your-domain.example
ENABLE_HSTS=true
RATE_LIMIT_DEFAULT=120/minute

# Monitoring (admin-only)
ENABLE_NETWORK_MONITORING=true
NETWORK_MONITOR_INTERVAL=30
NETWORK_MONITOR_MAX_DEVICES=200
NETWORK_MONITOR_UNKNOWN_IP_LIMIT=50
NETWORK_MONITOR_UNKNOWN_IP_DEVICES_PER_CYCLE=2
NETWORK_MONITOR_UNKNOWN_IP_TIMEOUT=3
```

## Notes
- Use a reverse proxy for HTTPS (see `REVERSE_PROXY_SETUP.md`).
- Rotate `JWT_SECRET` before any public launch.
- Keep `CORS_ORIGINS` restricted to your real frontend domain.
