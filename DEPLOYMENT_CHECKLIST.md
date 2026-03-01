# 🚀 Deployment Checklist

Use this checklist to track your deployment progress.

## 📋 Pre-Deployment

### Lock production env and secrets (before launch cutover)

Set and verify in production; do not launch with defaults or placeholders:

- [ ] `CORS_ORIGINS` = production domain(s) only (no `*`)
- [ ] `JWT_SECRET` = strong 32+ chars (e.g. `python scripts/generate_secrets.py`)
- [ ] `MONGO_URI` = production MongoDB (auth + TLS)
- [ ] `APP_BASE_URL` = production HTTPS URL (for email links)
- [ ] Live Stripe keys and webhook when accepting real payments
- [ ] See `docs/PRE_LAUNCH_48H_PLAN.md` for full checklist.

### Gmail SMTP Setup
- [ ] Enabled 2FA on Gmail account
- [ ] Created App Password
- [ ] Updated `.env` with SMTP credentials
- [ ] Tested email locally

### MongoDB
- [ ] MongoDB Atlas cluster created
- [ ] Connection string added to `.env`
- [ ] Database user created with proper permissions
- [ ] Network access configured (IP whitelist or 0.0.0.0/0)

### Environment Variables
- [ ] `MONGO_URI` - MongoDB connection string
- [ ] `JWT_SECRET` - Strong random secret (32+ chars)
- [ ] `SMTP_USER` - Your Gmail address
- [ ] `SMTP_PASSWORD` - Gmail app password
- [ ] `FROM_EMAIL` - Your Gmail address
- [ ] `PORT` - 8000 (or your preferred port)
- [ ] `CORS_ORIGINS` - Updated for production domain

### Local Testing
- [ ] Server starts without errors
- [ ] Can create user account
- [ ] Can login successfully
- [ ] Can create devices
- [ ] Can create alerts
- [ ] Email notifications arrive
- [ ] Dashboard loads and displays data
- [ ] All API endpoints working

## 🌐 Production Deployment

### Choose Platform
- [ ] **Railway** (Recommended - $5-20/month)
- [ ] **Render** (Free tier available, $7/month for production)
- [ ] **Docker + Cloud** (AWS/GCP/Azure - $20-100+/month)

### Railway Deployment
- [ ] Created Railway account
- [ ] Connected GitHub repository
- [ ] Created new project from repo
- [ ] Added all environment variables
- [ ] Updated `CORS_ORIGINS` with Railway domain
- [ ] Deployment successful
- [ ] Health check passes: `/api/health`
- [ ] Can login to production instance
- [ ] Notifications work in production

### Render Deployment
- [ ] Created Render account
- [ ] Created new Web Service
- [ ] Connected GitHub repository
- [ ] Configured build command: `pip install -r requirements.txt`
- [ ] Configured start command: `uvicorn main:app --host 0.0.0.0 --port $PORT`
- [ ] Added all environment variables
- [ ] Set `PORT=10000`
- [ ] Updated `CORS_ORIGINS` with Render domain
- [ ] Deployment successful
- [ ] Health check passes: `/api/health`
- [ ] Can login to production instance
- [ ] Notifications work in production

## 🔐 Security

- [ ] Changed `JWT_SECRET` from default
- [ ] `JWT_SECRET` is 32+ characters
- [ ] CORS restricted to actual domain (not `*` in production)
- [ ] MongoDB uses authentication
- [ ] No secrets in GitHub repository
- [ ] `.env` file in `.gitignore`
- [ ] HTTPS enabled (automatic on Railway/Render)

## 📊 Post-Deployment

### Monitoring
- [ ] Set up uptime monitoring (UptimeRobot/Pingdom)
- [ ] Monitor `/api/health` endpoint
- [ ] Set up error tracking (Sentry - optional)
- [ ] Set up log aggregation (optional)

### Testing Production
- [ ] Create test user account
- [ ] Add test device
- [ ] Create test alert
- [ ] Verify email notification received
- [ ] Test all major features
- [ ] Test on mobile device
- [ ] Test from different networks

### Database
- [ ] MongoDB backups enabled (automatic in Atlas)
- [ ] Backup retention configured
- [ ] Tested restore process
- [ ] Indexes created (automatic on first run)

### Performance
- [ ] API response times < 500ms
- [ ] Dashboard loads quickly
- [ ] No memory leaks
- [ ] CPU usage reasonable

## 🎯 Optional Enhancements

### Twilio (SMS/WhatsApp/Voice)
- [ ] Created Twilio account
- [ ] Got Account SID and Auth Token
- [ ] Purchased phone number
- [ ] Configured WhatsApp sandbox
- [ ] Added credentials to `.env`
- [ ] Tested SMS notifications
- [ ] Tested WhatsApp notifications
- [ ] Tested voice calls (critical alerts)

### Custom Domain
- [ ] Purchased domain name
- [ ] Configured DNS records
- [ ] SSL certificate configured
- [ ] Domain points to production
- [ ] Updated `CORS_ORIGINS`

### CI/CD
- [ ] GitHub Actions configured
- [ ] Auto-deploy on push to main
- [ ] Run tests before deploy
- [ ] Deployment notifications

## 📈 Maintenance

### Weekly
- [ ] Check server logs
- [ ] Review error rates
- [ ] Check disk space
- [ ] Review alerts

### Monthly
- [ ] Update dependencies
- [ ] Review security alerts
- [ ] Test backup restoration
- [ ] Review performance metrics

### Quarterly
- [ ] Security audit
- [ ] Performance optimization
- [ ] Update documentation
- [ ] Review costs and scaling needs

## 🎉 Success Criteria

You're ready for production when:

- ✅ All "Pre-Deployment" items checked
- ✅ All "Production Deployment" items checked (for your platform)
- ✅ All "Security" items checked
- ✅ All "Post-Deployment" testing items checked
- ✅ Email notifications arrive reliably
- ✅ Dashboard is accessible from public URL
- ✅ No errors in server logs
- ✅ Health check endpoint responds correctly

## 📞 Support

If you encounter issues:

1. Check `docs/DEPLOYMENT.md` for detailed troubleshooting
2. Check `docs/API_KEYS_SETUP.md` for notification setup
3. Review server logs for error messages
4. Check MongoDB Atlas for connection issues
5. Verify all environment variables are set correctly

## 🔗 Quick Links

- **Production URL**: `https://your-app.railway.app` or `https://your-app.onrender.com`
- **API Docs**: `https://your-app-url.com/docs`
- **Health Check**: `https://your-app-url.com/api/health`
- **Dashboard**: `https://your-app-url.com/dashboard`
- **MongoDB Atlas**: https://cloud.mongodb.com
- **Railway Dashboard**: https://railway.app/dashboard
- **Render Dashboard**: https://dashboard.render.com

---

**Last Updated**: {{ DATE }}
**Deployment Status**: {{ PENDING / IN PROGRESS / COMPLETE }}
**Production URL**: {{ YOUR_URL }}

---

Print this checklist and mark items as you complete them! 🎯
