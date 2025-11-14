"""
Quick script to send test notification to all users
Update BASE_URL if your server is on a different host/port
"""
import requests
import json
from datetime import datetime

# Configuration - UPDATE THIS IF YOUR SERVER IS ON DIFFERENT HOST/PORT
BASE_URL = "http://44.200.108.209:8000"  # Your EC2 server URL

# Your admin token
ADMIN_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNzYzMTM0NDkyLCJpYXQiOjE3NjMwNDgwOTIsImp0aSI6IjI5Nzg0OWEwODJhNTQ5ZmQ5MzIzMjU3MjZjNzljMGE3IiwidXNlcl9pZCI6IjE3In0.pvZpxtefii5xOW9DjxOYCCzz7-MUXWiGKKVF0-mVgkQ"

def send_test_notification():
    """Send test notification to all users"""
    
    url = f"{BASE_URL}/api/notifications/send/"
    
    headers = {
        "Authorization": f"Bearer {ADMIN_TOKEN}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "notification_type": "system_message",
        "title": "🧪 Test Notification - System Check",
        "body": "Hello! This is a test notification to verify the push notification system is working correctly. If you received this, everything is set up properly! ✅",
        "all_users": True,
        "data": {
            "test": True,
            "timestamp": datetime.now().isoformat(),
            "message": "Push notification system test"
        }
    }
    
    print("=" * 60)
    print("🚀 SENDING TEST NOTIFICATION TO ALL USERS")
    print("=" * 60)
    print(f"📡 Server URL: {BASE_URL}")
    print(f"🔗 Endpoint: {url}")
    print(f"📝 Notification Title: {payload['title']}")
    print(f"📝 Notification Body: {payload['body']}")
    print()
    
    try:
        print("⏳ Sending request...")
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        
        print(f"📊 Status Code: {response.status_code}")
        print()
        
        if response.status_code == 201:
            data = response.json()
            print("✅ SUCCESS!")
            print("=" * 60)
            print(f"📨 Message: {data.get('message', 'N/A')}")
            print(f"📨 Notifications Sent: {data.get('notifications_sent', 0)}")
            print("=" * 60)
            print()
            print("📱 Check your devices to see if you received the notification!")
            return True
            
        elif response.status_code == 401:
            print("❌ ERROR: Unauthorized")
            print("💡 Your token might be expired or invalid.")
            print("   Please login again to get a new token.")
            return False
            
        elif response.status_code == 403:
            print("❌ ERROR: Forbidden")
            print("💡 You need admin privileges to send notifications to all users.")
            return False
            
        elif response.status_code == 400:
            print("❌ ERROR: Bad Request")
            try:
                error_data = response.json()
                print(f"   Details: {error_data}")
            except:
                print(f"   Response: {response.text}")
            return False
            
        else:
            print(f"❌ ERROR: Status {response.status_code}")
            try:
                error_data = response.json()
                print(f"   Response: {json.dumps(error_data, indent=2)}")
            except:
                print(f"   Response: {response.text}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ ERROR: Could not connect to server")
        print(f"💡 Make sure the server is running at {BASE_URL}")
        print("   Check if:")
        print("   1. The Django server is running (python manage.py runserver)")
        print("   2. The URL and port are correct")
        print("   3. There's no firewall blocking the connection")
        return False
        
    except requests.exceptions.Timeout:
        print("❌ ERROR: Request timed out")
        print("💡 The server took too long to respond.")
        return False
        
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        return False

if __name__ == "__main__":
    print()
    success = send_test_notification()
    print()
    
    if not success:
        print("💡 TROUBLESHOOTING:")
        print("   1. Make sure your Django server is running")
        print("   2. Check if BASE_URL is correct in this script")
        print("   3. Verify your admin token is still valid")
        print("   4. Check server logs for any errors")
        print()

