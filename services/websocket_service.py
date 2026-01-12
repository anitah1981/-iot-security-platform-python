"""
WebSocket Service for Real-Time Updates
Broadcasts device status changes, new alerts, and system events to connected clients
"""

import socketio
from typing import Dict, List, Any
import asyncio
from datetime import datetime

# Create Socket.IO server
sio = socketio.AsyncServer(
    async_mode='asgi',
    cors_allowed_origins='*',  # Configure for production
    logger=True,
    engineio_logger=False
)

# Track connected users and their rooms
connected_users: Dict[str, Dict[str, Any]] = {}


@sio.event
async def connect(sid, environ, auth):
    """Handle client connection"""
    print(f"✅ WebSocket client connected: {sid}")
    
    # Get user info from auth
    user_id = auth.get('user_id') if auth else None
    
    connected_users[sid] = {
        'user_id': user_id,
        'connected_at': datetime.utcnow().isoformat(),
        'rooms': []
    }
    
    await sio.emit('connection_established', {
        'status': 'connected',
        'timestamp': datetime.utcnow().isoformat(),
        'message': 'Real-time updates active'
    }, to=sid)


@sio.event
async def disconnect(sid):
    """Handle client disconnection"""
    if sid in connected_users:
        user_info = connected_users.pop(sid)
        print(f"❌ WebSocket client disconnected: {sid} (user: {user_info.get('user_id')})")


@sio.event
async def join_room(sid, data):
    """Join a room for targeted updates (e.g., specific user's devices)"""
    room = data.get('room')
    if room:
        sio.enter_room(sid, room)
        if sid in connected_users:
            connected_users[sid]['rooms'].append(room)
        print(f"🔗 Client {sid} joined room: {room}")
        await sio.emit('room_joined', {'room': room}, to=sid)


@sio.event
async def leave_room(sid, data):
    """Leave a room"""
    room = data.get('room')
    if room:
        sio.leave_room(sid, room)
        if sid in connected_users and room in connected_users[sid]['rooms']:
            connected_users[sid]['rooms'].remove(room)
        print(f"🔌 Client {sid} left room: {room}")


# Broadcast functions for different event types

async def broadcast_device_update(device_id: str, device_data: Dict[str, Any], user_id: str = None):
    """Broadcast device status update to relevant clients"""
    event_data = {
        'type': 'device_update',
        'device_id': device_id,
        'device': device_data,
        'timestamp': datetime.utcnow().isoformat()
    }
    
    if user_id:
        # Send to specific user's room
        await sio.emit('device_update', event_data, room=f'user_{user_id}')
    else:
        # Broadcast to all
        await sio.emit('device_update', event_data)
    
    print(f"📡 Broadcasted device update: {device_id}")


async def broadcast_new_alert(alert_data: Dict[str, Any], user_id: str = None):
    """Broadcast new alert to relevant clients"""
    event_data = {
        'type': 'new_alert',
        'alert': alert_data,
        'timestamp': datetime.utcnow().isoformat()
    }
    
    if user_id:
        await sio.emit('new_alert', event_data, room=f'user_{user_id}')
    else:
        await sio.emit('new_alert', event_data)
    
    print(f"🚨 Broadcasted new alert: {alert_data.get('severity')} - {alert_data.get('message')}")


async def broadcast_alert_resolved(alert_id: str, user_id: str = None):
    """Broadcast alert resolution"""
    event_data = {
        'type': 'alert_resolved',
        'alert_id': alert_id,
        'timestamp': datetime.utcnow().isoformat()
    }
    
    if user_id:
        await sio.emit('alert_resolved', event_data, room=f'user_{user_id}')
    else:
        await sio.emit('alert_resolved', event_data)
    
    print(f"✅ Broadcasted alert resolved: {alert_id}")


async def broadcast_notification(message: str, severity: str = 'info', user_id: str = None):
    """Broadcast system notification"""
    event_data = {
        'type': 'notification',
        'message': message,
        'severity': severity,
        'timestamp': datetime.utcnow().isoformat()
    }
    
    if user_id:
        await sio.emit('notification', event_data, room=f'user_{user_id}')
    else:
        await sio.emit('notification', event_data)


def get_connected_clients_count() -> int:
    """Get number of connected clients"""
    return len(connected_users)


def get_connected_users_info() -> List[Dict[str, Any]]:
    """Get info about all connected users"""
    return list(connected_users.values())


# Create ASGI app for Socket.IO
socket_app = socketio.ASGIApp(
    sio,
    other_asgi_app=None,
    socketio_path='socket.io'
)
