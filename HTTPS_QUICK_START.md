# 🔒 HTTPS Quick Start Guide

Get your app running on HTTPS quickly.

---

## Option 1: Cloud Provider (Easiest - Automatic HTTPS)

### **Railway / Render / Fly.io**
✅ **HTTPS included automatically**

1. Deploy your app
2. Add custom domain in dashboard
3. HTTPS works automatically with free SSL

**No configuration needed!**

---

## Option 2: Nginx Reverse Proxy (Self-Hosted)

### Prerequisites
- Server with public IP
- Domain name pointing to server
- Port 80 and 443 open in firewall

### Step 1: Install Nginx
```bash
# Ubuntu/Debian
sudo apt update && sudo apt install nginx

# CentOS/RHEL
sudo yum install nginx
```

### Step 2: Get SSL Certificate (Let's Encrypt)
```bash
# Install Certbot
sudo apt install certbot python3-certbot-nginx

# Get certificate (replace yourdomain.com)
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com
```

Certbot will:
- ✅ Get SSL certificate
- ✅ Configure Nginx automatically
- ✅ Set up auto-renewal

### Step 3: Configure Nginx Manually (if needed)

Create `/etc/nginx/sites-available/iot-security`:

```nginx
# HTTP → HTTPS redirect
server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;
    return 301 https://$server_name$request_uri;
}

# HTTPS server
server {
    listen 443 ssl http2;
    server_name yourdomain.com www.yourdomain.com;

    # SSL certificates
    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;
    
    # Modern SSL
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_prefer_server_ciphers off;

    # Security headers (add these!)
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains; preload" always;
    add_header X-Frame-Options "DENY" always;
    add_header X-Content-Type-Options "nosniff" always;

    # Proxy to FastAPI
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header X-Forwarded-Host $server_name;
    }
}
```

Enable and restart:
```bash
sudo ln -s /etc/nginx/sites-available/iot-security /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### Step 4: Test
```bash
# Should redirect to HTTPS
curl -I http://yourdomain.com

# Should return 200 with security headers
curl -I https://yourdomain.com
```

---

## Option 3: Caddy (Simplest Self-Hosted)

Caddy automatically handles HTTPS with Let's Encrypt.

### Install Caddy
```bash
# Debian/Ubuntu
sudo apt install -y debian-keyring debian-archive-keyring apt-transport-https
curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/gpg.key' | sudo gpg --dearmor -o /usr/share/keyrings/caddy-stable-archive-keyring.gpg
curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/debian.deb.txt' | sudo tee /etc/apt/sources.list.d/caddy-stable.list
sudo apt update && sudo apt install caddy
```

### Configure (`/etc/caddy/Caddyfile`)
```
yourdomain.com {
    reverse_proxy localhost:8000 {
        header_up X-Real-IP {remote_host}
        header_up X-Forwarded-For {remote_host}
        header_up X-Forwarded-Proto {scheme}
    }
}
```

### Start
```bash
sudo systemctl enable caddy
sudo systemctl start caddy
```

**That's it!** Caddy automatically:
- ✅ Gets SSL certificate
- ✅ Renews automatically
- ✅ Handles HTTP → HTTPS redirect

---

## Option 4: Cloudflare (Recommended for Production)

Cloudflare provides free SSL + DDoS protection + CDN.

### Setup:
1. Sign up at [cloudflare.com](https://cloudflare.com)
2. Add your domain
3. Change nameservers to Cloudflare's
4. Enable "SSL/TLS" → "Full (strict)"
5. Enable "Always Use HTTPS"
6. Enable "Automatic HTTPS Rewrites"

**Benefits:**
- ✅ Free SSL (automatic)
- ✅ DDoS protection
- ✅ CDN for faster loading
- ✅ Analytics
- ✅ Firewall rules
- ✅ Rate limiting

Your app runs behind Cloudflare, which handles HTTPS.

---

## Environment Variables for HTTPS

After HTTPS is working, set these in your `.env`:

```bash
APP_ENV=production
FORCE_HTTPS=true
ENABLE_HSTS=true
APP_BASE_URL=https://yourdomain.com
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
CORS_ORIGINS=https://yourdomain.com
```

---

## Verify HTTPS is Working

### Test 1: Redirect
```bash
curl -I http://yourdomain.com
# Should show: Location: https://yourdomain.com
```

### Test 2: HTTPS Works
```bash
curl -I https://yourdomain.com
# Should return: HTTP/2 200
```

### Test 3: Security Headers
```bash
curl -I https://yourdomain.com | grep -i "strict-transport"
# Should show: Strict-Transport-Security
```

### Test 4: SSL Certificate
Visit `https://yourdomain.com` in browser:
- ✅ No certificate warnings
- ✅ Padlock icon shows
- ✅ "Connection is secure"

---

## Troubleshooting

### "Certificate not trusted"
- Wait a few minutes (Let's Encrypt takes time)
- Check certificate: `sudo certbot certificates`
- Renew manually: `sudo certbot renew`

### "502 Bad Gateway"
- App not running: `ps aux | grep uvicorn`
- Wrong port: Check Nginx config points to 8000
- Firewall: Ensure port 8000 accessible internally

### "403 Forbidden"
- Check `ALLOWED_HOSTS` includes your domain
- Check Nginx `server_name` matches domain

### "Mixed Content" warnings
- Ensure `APP_BASE_URL` uses `https://`
- Check all external resources use HTTPS

---

## Auto-Renewal (Let's Encrypt)

Certbot sets this up automatically, but verify:

```bash
# Test renewal
sudo certbot renew --dry-run

# Check timer status
sudo systemctl status certbot.timer
```

Certificates auto-renew every 60 days.

---

**Quickest Path to HTTPS:**
1. Use Railway/Render/Fly.io (automatic)
2. OR use Cloudflare (free SSL + protection)
3. OR use Caddy (auto HTTPS for self-hosted)
