# Reverse Proxy Setup (HTTPS)

This app should run behind HTTPS in production. Below is a minimal Nginx example.

## Nginx example

```
server {
    listen 443 ssl;
    server_name your-domain.example;

    ssl_certificate     /etc/letsencrypt/live/your-domain.example/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your-domain.example/privkey.pem;

    location / {
        proxy_pass         http://127.0.0.1:8000;
        proxy_set_header   Host $host;
        proxy_set_header   X-Real-IP $remote_addr;
        proxy_set_header   X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header   X-Forwarded-Proto $scheme;
    }
}
```

## HTTP → HTTPS redirect

```
server {
    listen 80;
    server_name your-domain.example;
    return 301 https://$host$request_uri;
}
```

## Notes
- Use Certbot or your provider to manage TLS certificates.
- Set `APP_BASE_URL` to the HTTPS URL.
