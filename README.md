# Alert-Pro

A comprehensive IoT security monitoring platform with real-time device tracking, multi-channel alerting, and threat detection.

## 🚀 Deploy Now (Make It Live)

**Ready to go live?** Follow these steps:

1. **Get MongoDB Atlas connection string** (see `DEPLOY_NOW_STEPS.md` Step 1)
2. **Generate Railway env vars**: `python scripts\prepare_for_railway.py`
3. **Deploy to Railway**: https://railway.app → Deploy from GitHub → Add variables → Done!

**Full guide**: `DEPLOY_NOW_STEPS.md` | **Quick reference**: `GET_STARTED_DEPLOY.md`

---

## ✨ Features

### Core Functionality
- **🔐 Authentication**: JWT-based auth with bcrypt password hashing
- **📱 Device Management**: Register, monitor, and track IoT devices
- **📡 Connect real devices**: Run the **device agent** (in `agent/`) on your network so Alexa, Ring, cameras, etc. show as online/offline; get your API key in **Settings → Connect real devices**. See `agent/README.md` and `docs/HOW_DEVICES_CONNECT.md`.
- **🚨 Smart Alerts**: Multi-severity alerts with deduplication logic
- **💓 Heartbeat Monitoring**: Real-time device health tracking
- **📊 Web Dashboard**: Beautiful, responsive UI with auto-refresh
- **🔔 Multi-Channel Notifications**: Email, SMS, WhatsApp, Voice calls
- **⚙️ Notification Preferences**: Customizable per user with severity filtering
- **🛡️ Security Monitoring**: IP anomaly detection, connection pattern analysis

### Security Features
- Suspicious IP detection
- Rapid IP change alerts
- WiFi jamming detection (connection loss patterns)
- Mass disconnection alerts
- Device behavior anomaly detection

### Architecture
- **Backend**: FastAPI (Python)
- **Database**: MongoDB (with Motor async driver)
- **Frontend**: Modern vanilla JavaScript with real-time updates
- **Notifications**: Twilio (SMS/WhatsApp/Voice) + Gmail SMTP (Email)

## 🚀 Quick Start

### Local Development

#### 1) Clone and setup
```bash
git clone https://github.com/anitah1981/-iot-security-platform-python.git
cd -iot-security-platform-python
python -m venv venv
```

**Windows:**
```bash
.\venv\Scripts\activate
```

**Mac/Linux:**
```bash
source venv/bin/activate
```

#### 2) Install dependencies
```bash
pip install -r requirements.txt
```

#### 3) Configure environment
Copy `.env.example` to `.env` and update with your settings:

```env
# Core (Required)
MONGO_URI=mongodb+srv://user:pass@cluster.mongodb.net/iot_security
JWT_SECRET=your-super-secret-key-change-this
PORT=8000

# CORS (Set to your domain in production)
CORS_ORIGINS=http://localhost:8000,http://127.0.0.1:8000

# Heartbeat Monitoring
HEARTBEAT_SWEEP_ENABLED=true
SWEEP_INTERVAL_MS=30000
OFFLINE_THRESHOLD_MINUTES=5

# Notifications (Optional but recommended)
SENDGRID_API_KEY=your_sendgrid_api_key
FROM_EMAIL=alerts@yourdomain.com
TWILIO_ACCOUNT_SID=your_twilio_sid
TWILIO_AUTH_TOKEN=your_twilio_token
TWILIO_PHONE_NUMBER=+1234567890
TWILIO_WHATSAPP_NUMBER=whatsapp:+14155238886
```

#### 4) Start the server
```bash
uvicorn main:app --reload --port 8000
```

#### 5) Access the application
- **Web UI**: http://localhost:8000
- **Health Check**: http://localhost:8000/api/health
- **API Docs** (`/docs` and `/redoc`): **Require authentication.** Log in via the Web UI or `POST /api/auth/login`, then open http://localhost:8000/docs in the same browser (session/cookie) or send the `Authorization: Bearer <access_token>` header when requesting `/docs` or `/redoc`.

## 🚀 Make the web app live (production)

Run the deployment helper, then follow the printed steps (MongoDB Atlas → GitHub → Railway or Render):

```bash
python scripts/do_it_all_deploy.py
```

See **docs/MAKE_APP_LIVE.md** for full instructions. The project includes **Procfile** and **railway.json** for one-click deploy on Railway or Render.

## 🐳 Docker Deployment

```bash
cp .env.example .env
# Edit .env with your configuration
docker compose up --build
```

## 📡 API Endpoints

### Authentication
- `POST /api/auth/signup` - Register new user
- `POST /api/auth/login` - Login and get JWT token
- `GET /api/auth/me` - Get current user info

### Devices
- `GET /api/devices` - List all devices
- `POST /api/devices` - Register new device
- `GET /api/devices/{device_id}/status` - Get device status
- `PATCH /api/devices/{device_id}` - Update device
- `DELETE /api/devices/{device_id}` - Remove device

### Alerts
- `GET /api/alerts` - List alerts (with filters)
- `POST /api/alerts` - Create alert
- `POST /api/alerts/{alert_id}/resolve` - Resolve alert

### Heartbeat
- `POST /api/heartbeat` - Submit device heartbeat

### Notification Preferences
- `GET /api/notification-preferences` - Get user preferences
- `PUT /api/notification-preferences` - Update preferences
- `POST /api/notification-preferences/test/{channel}` - Send a test notification (email|sms|whatsapp|voice)

## 🔧 Configuration

### MongoDB Setup

#### Option 1: MongoDB Atlas (Recommended for Production)
1. Create account at [mongodb.com/cloud/atlas](https://mongodb.com/cloud/atlas)
2. Create a cluster
3. Get connection string and add to `.env`

#### Option 2: Local MongoDB
```bash
# Install MongoDB locally
brew install mongodb-community  # Mac
# or use Docker
docker run -d -p 27017:27017 --name mongodb mongo

# Update .env
MONGO_URI=mongodb://localhost:27017/iot_security
```

### Notification Services

#### Gmail SMTP (Email) - Recommended!
1. Enable 2-Factor Authentication on your Gmail
2. Create App Password: https://myaccount.google.com/apppasswords
3. Add to `.env`:
```env
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your@gmail.com
SMTP_PASSWORD=your-16-char-app-password
FROM_EMAIL=your@gmail.com
```

#### Twilio (SMS/WhatsApp/Voice)
1. Sign up at [twilio.com](https://twilio.com)
2. Get Account SID and Auth Token
3. Get a phone number
4. Add to `.env`:
```env
TWILIO_ACCOUNT_SID=ACxxxxx
TWILIO_AUTH_TOKEN=xxxxx
TWILIO_PHONE_NUMBER=+1234567890
TWILIO_WHATSAPP_NUMBER=whatsapp:+14155238886
```
**Trial & UK regulatory notes:**
- Trial accounts can only send SMS to verified recipient numbers.
- UK SMS may require a UK Regulatory Bundle before you can buy/use a UK number.
- Error code **21612** means UK SMS geo permissions are disabled.

## 🎨 Frontend Features

The web dashboard includes:
- Real-time device status monitoring (auto-refresh every 10s)
- Interactive alert management with resolve buttons
- Responsive design for mobile and desktop
- Dark mode with modern UI
- Status badges with visual indicators

## 🛡️ Security Best Practices

1. **Change JWT Secret**: Generate a strong random secret for production
2. **Use HTTPS**: Always use SSL/TLS in production
3. **Set CORS Origins**: Restrict to your actual domain
4. **Rotate Credentials**: Regularly update API keys and secrets
5. **Monitor Logs**: Check for suspicious activity
6. **Database Backups**: Regular automated backups of MongoDB

## 📊 Monitoring & Alerting

### Alert Types
- **connectivity**: Device online/offline status
- **power**: Power-related issues
- **security**: Security threats and anomalies
- **system**: System errors and issues

### Severity Levels
- **low**: Informational
- **medium**: Warning, attention needed
- **high**: Urgent, requires action
- **critical**: Emergency, immediate action required

### Notification Escalation
Automatic escalation based on severity:
1. **Email**: All severities (configurable)
2. **SMS**: High and Critical (configurable)
3. **WhatsApp**: Medium, High, Critical (configurable)
4. **Voice Call**: Critical only (configurable)

## 📈 Scaling Considerations

For production at scale:
1. **Database**: Use MongoDB Atlas with auto-scaling
2. **Caching**: Add Redis for session management
3. **Load Balancing**: Use multiple FastAPI instances
4. **Message Queue**: Add RabbitMQ/Redis for async tasks
5. **Monitoring**: Integrate Prometheus + Grafana
6. **Logging**: Centralized logging with ELK stack

## 🚀 Production Deployment

### Option 1: Railway
1. Create account at [railway.app](https://railway.app)
2. Connect GitHub repository
3. Add environment variables
4. Deploy automatically on git push

### Option 2: Render
1. Create account at [render.com](https://render.com)
2. Create new Web Service
3. Connect repository
4. Add environment variables
5. Deploy

### Option 3: AWS/GCP/Azure
Deploy using Docker containers:
```bash
docker build -t iot-security-platform .
docker push your-registry/iot-security-platform
# Deploy to your cloud provider
```

## 🤝 Contributing

This project follows standard contribution guidelines. Feel free to submit issues and pull requests.

## 📝 License

[Your License Here]

## 🔗 Links

- **Documentation**: See `docs/` folder
- **API Docs**: `https://your-domain.com/docs` (**requires authentication**, same as local `/docs` / `/redoc`)
- **Branding Guide**: `docs/branding.md`

---

Built with ❤️ for IoT security

