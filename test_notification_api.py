"""
Simple script to send test notification to all users via API
This doesn't require Django setup - just uses HTTP requests

Usage:
1. Get your admin token (login as admin)
2. Update ADMIN_TOKEN below
3. Update BASE_URL if needed
4. Run: python test_notification_api.py
"""

import requests
import json

# Configuration
BASE_URL = "http://localhost:8000"  # Change if your server is on different host/port
ADMIN_TOKEN = "YOUR_ADMIN_TOKEN_HERE"  # Get this by logging in as admin

def send_notification_to_all_users():
    """Send test notification to all users using the API"""
    
    url = f"{BASE_URL}/api/notifications/send/"
    
    headers = {
        "Authorization": f"Bearer {ADMIN_TOKEN}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "notification_type": "system_message",
        "title": "🧪 Test Notification - System Check",
        "body": "Hello! This is a test notification to verify the push notification system is working correctly. If you received this, everything is set up properly! ✅",
        "all_users": True,  # Send to all users
        "data": {
            "test": True,
            "timestamp": "2025-01-26T12:00:00Z",
            "message": "Push notification system test"
        }
    }
    
    print("🚀 Sending test notification to all users...")
    print(f"📡 URL: {url}")
    print(f"📝 Payload: {json.dumps(payload, indent=2)}")
    print()
    
    try:
        response = requests.post(url, headers=headers, json=payload)
        
        print(f"📊 Status Code: {response.status_code}")
        print(f"📄 Response: {json.dumps(response.json(), indent=2)}")
        print()
        
        if response.status_code == 201:
            data = response.json()
            print("✅ SUCCESS!")
            print(f"📨 Notifications sent: {data.get('notifications_sent', 0)}")
            print("📱 Check your devices to see if you received the notification!")
        elif response.status_code == 401:
            print("❌ ERROR: Unauthorized")
            print("💡 Make sure:")
            print("   1. You're logged in as an admin user")
            print("   2. Your admin token is correct")
            print("   3. The token hasn't expired")
        elif response.status_code == 403:
            print("❌ ERROR: Forbidden")
            print("💡 You need admin privileges to send notifications to all users")
        else:
            print(f"❌ ERROR: {response.status_code}")
            print(f"Response: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("❌ ERROR: Could not connect to server")
        print(f"💡 Make sure the server is running at {BASE_URL}")
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")

if __name__ == "__main__":
    if ADMIN_TOKEN == "YOUR_ADMIN_TOKEN_HERE":
        print("⚠️  Please update ADMIN_TOKEN in the script first!")
        print()
        print("To get your admin token:")
        print("1. Login as admin using: POST /api/users/admin/auth/login/")
        print("2. Copy the 'access' token from the response")
        print("3. Update ADMIN_TOKEN in this script")
        print()
    else:
        send_notification_to_all_users()

