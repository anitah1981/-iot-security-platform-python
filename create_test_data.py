#!/usr/bin/env python3
"""
Create test data for IoT Security Platform
Adds devices and alerts to populate the dashboard charts
"""

import requests
import json
from datetime import datetime, timedelta
import random

API_BASE = 'http://localhost:8000'

def create_test_data():
    print("\n" + "="*60)
    print("  Creating Test Data for Dashboard Charts")
    print("="*60 + "\n")
    
    # Login to get token
    print('[1/5] Logging in as anitah1981@gmail.com...')
    try:
        login_response = requests.post(f'{API_BASE}/api/auth/login', json={
            'email': 'anitah1981@gmail.com',
            'password': 'Test123!!Test'
        })
        login_response.raise_for_status()
        token = login_response.json()['token']
        headers = {'Authorization': f'Bearer {token}'}
        print('      [OK] Logged in successfully!\n')
    except Exception as e:
        print(f'      [ERROR] Login failed: {e}')
        return

    # Create test devices
    print('[2/5] Creating test devices...')
    devices = [
        {'device_id': 'dev-001', 'name': 'Living Room Camera', 'type': 'Camera', 'ip_address': '192.168.1.101'},
        {'device_id': 'dev-002', 'name': 'Front Door Sensor', 'type': 'Sensor', 'ip_address': '192.168.1.102'},
        {'device_id': 'dev-003', 'name': 'WiFi Router', 'type': 'Router', 'ip_address': '192.168.1.1'},
        {'device_id': 'dev-004', 'name': 'Bedroom Camera', 'type': 'Camera', 'ip_address': '192.168.1.103'},
        {'device_id': 'dev-005', 'name': 'Smart Thermostat', 'type': 'Thermostat', 'ip_address': '192.168.1.104'},
    ]

    device_ids = []
    for device in devices:
        try:
            response = requests.post(f'{API_BASE}/api/devices', json=device, headers=headers)
            if response.status_code == 201:
                device_data = response.json()
                device_ids.append(device_data['id'])
                print(f'      [OK] Created: {device["name"]}')
            elif response.status_code == 409:
                print(f'      [SKIP] {device["name"]} (already exists)')
        except Exception as e:
            print(f'      [ERROR] Failed to create {device["name"]}: {e}')

    print(f'\n[3/5] Successfully created/found {len(device_ids)} devices\n')

    # Update some devices to be online
    if device_ids:
        print('[4/5] Updating device statuses...')
        for i, device_id in enumerate(device_ids[:3]):  # Make first 3 online
            try:
                response = requests.patch(
                    f'{API_BASE}/api/devices/{device_id}',
                    json={'status': 'online'},
                    headers=headers
                )
                if response.status_code == 200:
                    print(f'      [OK] Set device {i+1} to ONLINE')
            except:
                pass
        print()

    # Create test alerts
    print('[5/5] Creating test alerts...')
    severities = ['low', 'medium', 'high', 'critical']
    alert_types = ['connectivity', 'security', 'system']
    alert_messages = [
        'Connection lost - device offline',
        'Suspicious login attempt detected',
        'System warning - high CPU usage',
        'Device disconnected unexpectedly',
        'Security scan completed',
        'Network anomaly detected',
        'Firmware update required',
        'Low battery warning',
        'Motion detected',
        'Temperature threshold exceeded'
    ]

    alerts_created = 0
    for i in range(12):
        if device_ids:
            alert = {
                'device_id': random.choice(device_ids),
                'severity': random.choice(severities),
                'type': random.choice(alert_types),
                'message': random.choice(alert_messages),
                'context': {'test_data': True, 'alert_number': i+1}
            }
            try:
                response = requests.post(f'{API_BASE}/api/alerts', json=alert, headers=headers)
                if response.status_code == 201:
                    alerts_created += 1
                    severity_emoji = {
                        'low': '[INFO]',
                        'medium': '[WARN]',
                        'high': '[HIGH]',
                        'critical': '[CRIT]'
                    }
                    print(f'      {severity_emoji[alert["severity"]]} {alert["message"][:50]}')
            except Exception as e:
                print(f'      [ERROR] Failed to create alert: {e}')

    print(f'\n{"="*60}')
    print(f'  Test Data Creation Complete!')
    print(f'{"="*60}\n')
    print(f'  [OK] Devices Created: {len(device_ids)}')
    print(f'  [OK] Alerts Created: {alerts_created}')
    print(f'  [OK] Online Devices: 3')
    print(f'  [OK] Offline Devices: {max(0, len(device_ids) - 3)}')
    print(f'\n{"="*60}')
    print(f'  Next Steps:')
    print(f'{"="*60}')
    print(f'  1. Refresh your dashboard: http://localhost:8000/dashboard')
    print(f'  2. You should now see:')
    print(f'     - Device status pie chart (3 online, 2 offline)')
    print(f'     - Device type distribution chart')
    print(f'     - Alert trends over time')
    print(f'     - Alert severity breakdown')
    print(f'     - Updated health metrics')
    print(f'\n  Enjoy your beautiful charts! [CHARTS_ICON]\n')

if __name__ == '__main__':
    create_test_data()
