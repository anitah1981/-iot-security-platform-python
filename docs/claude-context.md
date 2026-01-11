# Claude Context / Product & Tech Summary

This file captures the project plan and decisions discussed outside the codebase so they stay “attached” to the repo.

## Project Vision
A comprehensive IoT security platform for homeowners and small-to-medium businesses to monitor smart devices, detect security threats, and receive multi-channel alerts.

## Core Features
### Device Monitoring
- Real-time heartbeat monitoring
- Online/offline status tracking
- Auto-enrollment of new devices
- Device grouping and organization

### Security Features (Planned)
- WiFi jammer detection
- Unauthorized access attempts
- Network change monitoring
- Suspicious traffic analysis
- Port scanning and vulnerability detection
- Malicious IP connection blocking
- Abnormal behavior detection
- Man-in-the-middle attack detection

### Multi-Channel Notifications
- In-app alerts
- Email (SendGrid)
- SMS (Twilio)
- WhatsApp (Twilio)
- Automated voice calls (Twilio)
- Smart escalation (Email → SMS → WhatsApp → Call)

### Alert System
- Severity-based routing (low, medium, high, critical)
- Deduplication logic
- Acknowledgment tracking
- Alert history and resolution

## Technical Stack
### Backend
- FastAPI (Python)
- MongoDB (Motor async driver)
- Authentication: JWT + bcrypt
- Notifications: Twilio + SendGrid
- Security scanning: python-nmap

### Frontend (Planned)
- Web dashboard (HTML/CSS/JavaScript)
- iOS app (future)
- Android app (future)

## Current Progress (as of 2026-01-11)
### Completed / Present in repo
- Backend API structure (FastAPI)
- User authentication (signup/login/me)
- Device CRUD + status endpoint
- Alert creation/listing/resolution + dedupe rules (route-level)
- Heartbeat receiver endpoint (added in this repo)
- Heartbeat sweep + notification service scaffolding (added in this repo)

### In Progress
- Testing notification system
- Getting API credentials (Twilio, SendGrid)

### Next To Do
- User notification preferences endpoints + storage
- Wire alert creation → notification delivery + escalation logic
- Security monitoring features (nmap scanning, behavior detection)
- Web dashboard frontend
- Deployment

