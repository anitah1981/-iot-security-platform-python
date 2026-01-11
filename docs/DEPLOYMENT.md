# IoT Security Platform - Deployment Guide

## Overview
This guide covers deploying the IoT Security Platform to production environments.

## Pre-Deployment Checklist

### Security
- [ ] Change `JWT_SECRET` to a strong random value (32+ characters)
- [ ] Update CORS_ORIGINS to your production domain
- [ ] Set up MongoDB with authentication enabled
- [ ] Enable SSL/TLS for all connections
- [ ] Review and restrict API access as needed
- [ ] Set up firewall rules
- [ ] Enable MongoDB backup automation

### Configuration
- [ ] Set all environment variables in production
- [ ] Configure SendGrid for email notifications
- [ ] Configure Twilio for SMS/WhatsApp/Voice
- [ ] Test notification channels
- [ ] Set up monitoring and logging
- [ ] Configure auto-scaling if needed

### Testing
- [ ] Run full API test suite
- [ ] Test authentication flow
- [ ] Test device registration and heartbeat
- [ ] Test alert creation and notification delivery
- [ ] Load test critical endpoints
- [ ] Test failover scenarios

## Deployment Options

### Option 1: Railway (Easiest)

Railway provides automatic deployments from Git with minimal configuration.

#### Steps:
1. **Create Account**
   - Go to https://railway.app
   - Sign up with GitHub

2. **Create New Project**
   - Click "New Project"
   - Select "Deploy from GitHub repo"
   - Choose your repository

3. **Configure Environment**
   - Go to Variables tab
   - Add all environment variables from `.env`
   - Ensure `MONGO_URI` points to MongoDB Atlas

4. **Deploy**
   - Railway auto-deploys on push to main
   - Check logs for any errors
   - Visit the generated URL

5. **Custom Domain (Optional)**
   - Go to Settings
   - Add your custom domain
   - Configure DNS records as shown

#### Cost: ~$5-20/month depending on usage

---

### Option 2: Render

Render offers free tier for testing and simple paid tiers for production.

#### Steps:
1. **Create Account**
   - Go to https://render.com
   - Sign up with GitHub

2. **Create Web Service**
   - Click "New +" → "Web Service"
   - Connect your repository
   - Select branch (main)

3. **Configure Build**
   ```
   Build Command: pip install -r requirements.txt
   Start Command: uvicorn main:app --host 0.0.0.0 --port $PORT
   ```

4. **Environment Variables**
   - Add all variables from `.env`
   - Set `PORT=10000` (Render default)

5. **Deploy**
   - Click "Create Web Service"
   - Monitor build logs
   - Test the app URL

6. **Auto-Deploy**
   - Enabled by default on git push

#### Cost: Free tier available, $7+/month for production

---

### Option 3: Docker + Cloud Provider (AWS/GCP/Azure)

For maximum control and scalability.

#### Prerequisites:
- Docker installed
- Cloud provider account
- Domain name (optional)

#### Steps:

1. **Build Docker Image**
   ```bash
   docker build -t iot-security-platform:latest .
   ```

2. **Test Locally**
   ```bash
   docker run -p 8000:8000 --env-file .env iot-security-platform:latest
   ```

3. **Push to Container Registry**
   
   **For AWS ECR:**
   ```bash
   aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin YOUR_ACCOUNT.dkr.ecr.us-east-1.amazonaws.com
   docker tag iot-security-platform:latest YOUR_ACCOUNT.dkr.ecr.us-east-1.amazonaws.com/iot-security-platform:latest
   docker push YOUR_ACCOUNT.dkr.ecr.us-east-1.amazonaws.com/iot-security-platform:latest
   ```

   **For GCP:**
   ```bash
   gcloud auth configure-docker
   docker tag iot-security-platform:latest gcr.io/YOUR_PROJECT/iot-security-platform:latest
   docker push gcr.io/YOUR_PROJECT/iot-security-platform:latest
   ```

4. **Deploy to Cloud**
   
   **AWS ECS:**
   - Create ECS cluster
   - Create task definition
   - Create service
   - Configure load balancer
   
   **GCP Cloud Run:**
   ```bash
   gcloud run deploy iot-security-platform \
     --image gcr.io/YOUR_PROJECT/iot-security-platform:latest \
     --platform managed \
     --region us-central1 \
     --allow-unauthenticated
   ```

   **Azure Container Instances:**
   ```bash
   az container create \
     --resource-group myResourceGroup \
     --name iot-security-platform \
     --image YOUR_REGISTRY.azurecr.io/iot-security-platform:latest \
     --dns-name-label iot-security-unique \
     --ports 8000
   ```

#### Cost: Varies, ~$20-100+/month depending on scale

---

## Post-Deployment

### 1. Verify Deployment
```bash
# Check health
curl https://your-domain.com/api/health

# Test login
curl -X POST https://your-domain.com/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"Test123!"}'
```

### 2. Set Up Monitoring

**Uptime Monitoring:**
- [UptimeRobot](https://uptimerobot.com) - Free tier available
- [Pingdom](https://pingdom.com)
- Monitor `/api/health` endpoint

**Application Monitoring:**
- Sentry for error tracking
- DataDog for performance monitoring
- CloudWatch (AWS) / Stackdriver (GCP)

### 3. Set Up Logging

Add logging configuration to `main.py`:
```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)
```

### 4. Database Backups

**MongoDB Atlas (Recommended):**
- Automatic backups enabled by default
- Configure retention period
- Test restore process

**Self-Hosted MongoDB:**
```bash
# Automated backup script
mongodump --uri="$MONGO_URI" --out=/backups/$(date +%Y%m%d)
```

### 5. SSL/TLS Certificate

**Let's Encrypt (Free):**
```bash
certbot --nginx -d your-domain.com
```

**Or use your hosting provider's SSL:**
- Railway/Render: Automatic HTTPS
- AWS: ACM certificates
- GCP: Managed SSL certificates

### 6. Set Up CI/CD

**GitHub Actions Example:**
```yaml
name: Deploy

on:
  push:
    branches: [ main ]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Deploy to Railway
        run: railway up
        env:
          RAILWAY_TOKEN: ${{ secrets.RAILWAY_TOKEN }}
```

---

## Scaling Considerations

### Vertical Scaling
- Increase CPU/RAM for single instance
- Good for: Up to ~1000 devices

### Horizontal Scaling
- Multiple FastAPI instances behind load balancer
- Shared MongoDB cluster
- Redis for session storage
- Message queue for notifications
- Good for: 1000+ devices

### Database Scaling
- MongoDB sharding for large datasets
- Read replicas for read-heavy workloads
- Indexes on frequently queried fields

---

## Troubleshooting

### App Won't Start
1. Check environment variables are set
2. Verify MongoDB connection
3. Check logs for Python errors
4. Ensure port is available

### Notifications Not Sending
1. Verify API credentials in environment
2. Check service quotas (SendGrid/Twilio)
3. Review logs for error messages
4. Test credentials manually

### High Memory Usage
1. Check for memory leaks in background tasks
2. Increase instance memory
3. Add connection pooling limits
4. Monitor with profiling tools

### Slow API Response
1. Add database indexes
2. Enable query caching
3. Optimize slow queries
4. Consider adding CDN for static files

---

## Security Recommendations

1. **Rate Limiting**: Add rate limiting to prevent abuse
   ```python
   from slowapi import Limiter
   limiter = Limiter(key_func=get_remote_address)
   ```

2. **Input Validation**: Already implemented with Pydantic

3. **SQL Injection**: Using MongoDB (NoSQL), but still sanitize inputs

4. **CORS**: Restrict to your domain in production

5. **Secrets Management**: Use environment variables, never commit secrets

6. **Regular Updates**: Keep dependencies updated
   ```bash
   pip list --outdated
   pip install --upgrade package-name
   ```

---

## Support & Maintenance

### Regular Tasks
- [ ] Weekly: Review error logs
- [ ] Weekly: Check disk space and memory
- [ ] Monthly: Review and update dependencies
- [ ] Monthly: Test backup restoration
- [ ] Quarterly: Security audit
- [ ] Quarterly: Performance optimization

### Monitoring Alerts
Set up alerts for:
- API endpoint failures
- High error rates
- Slow response times
- Database connection issues
- Disk space warnings
- Memory usage spikes

---

## Additional Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com)
- [MongoDB Atlas](https://www.mongodb.com/cloud/atlas)
- [Twilio Documentation](https://www.twilio.com/docs)
- [SendGrid Documentation](https://docs.sendgrid.com)
- [Railway Documentation](https://docs.railway.app)
- [Render Documentation](https://render.com/docs)

---

**Questions?** Check the main README.md or open an issue on GitHub.
