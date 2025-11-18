#!/usr/bin/env python
"""
Test script for the unified billboard approval/rejection endpoint
"""
import requests
import json
import sys

# Configuration
BASE_URL = "http://localhost:8000"
ADMIN_EMAIL = "admin@gmail.com"  # Update with your admin email
ADMIN_PASSWORD = "zeshanopn1613m"  # Update with your admin password

def get_admin_token():
    """Get admin authentication token"""
    print("🔐 Getting admin token...")
    try:
        response = requests.post(
            f"{BASE_URL}/api/users/admin/auth/login/",
            json={
                "email": ADMIN_EMAIL,
                "password": ADMIN_PASSWORD
            },
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            data = response.json()
            token = data.get('access')
            print(f"✅ Login successful!")
            return token
        else:
            print(f"❌ Login failed: {response.status_code}")
            print(response.json())
            return None
    except Exception as e:
        print(f"❌ Error during login: {str(e)}")
        return None

def get_pending_billboards(token):
    """Get list of pending billboards"""
    print("\n📋 Fetching pending billboards...")
    try:
        response = requests.get(
            f"{BASE_URL}/api/billboards/pending/",
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            billboards = data.get('results', [])
            print(f"✅ Found {len(billboards)} pending billboard(s)")
            return billboards
        else:
            print(f"❌ Failed to fetch pending billboards: {response.status_code}")
            print(response.json())
            return []
    except Exception as e:
        print(f"❌ Error fetching pending billboards: {str(e)}")
        return []

def test_approve_billboard(token, billboard_id):
    """Test approve action"""
    print(f"\n✅ Testing APPROVE action for billboard ID: {billboard_id}")
    try:
        response = requests.post(
            f"{BASE_URL}/api/billboards/{billboard_id}/approval-status/",
            json={
                "action": "approve"
            },
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }
        )
        
        print(f"Status Code: {response.status_code}")
        result = response.json()
        print(f"Response: {json.dumps(result, indent=2)}")
        
        if response.status_code == 200:
            print("✅ APPROVE test PASSED!")
            return True
        else:
            print("❌ APPROVE test FAILED!")
            return False
    except Exception as e:
        print(f"❌ Error during approve test: {str(e)}")
        return False

def test_reject_billboard(token, billboard_id, reason="Test rejection from API"):
    """Test reject action"""
    print(f"\n❌ Testing REJECT action for billboard ID: {billboard_id}")
    try:
        response = requests.post(
            f"{BASE_URL}/api/billboards/{billboard_id}/approval-status/",
            json={
                "action": "reject",
                "rejection_reason": reason
            },
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }
        )
        
        print(f"Status Code: {response.status_code}")
        result = response.json()
        print(f"Response: {json.dumps(result, indent=2)}")
        
        if response.status_code == 200:
            print("✅ REJECT test PASSED!")
            return True
        else:
            print("❌ REJECT test FAILED!")
            return False
    except Exception as e:
        print(f"❌ Error during reject test: {str(e)}")
        return False

def test_invalid_action(token, billboard_id):
    """Test invalid action"""
    print(f"\n⚠️  Testing INVALID action for billboard ID: {billboard_id}")
    try:
        response = requests.post(
            f"{BASE_URL}/api/billboards/{billboard_id}/approval-status/",
            json={
                "action": "invalid_action"
            },
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }
        )
        
        print(f"Status Code: {response.status_code}")
        result = response.json()
        print(f"Response: {json.dumps(result, indent=2)}")
        
        if response.status_code == 400:
            print("✅ Invalid action test PASSED (correctly rejected invalid action)!")
            return True
        else:
            print("❌ Invalid action test FAILED (should return 400)!")
            return False
    except Exception as e:
        print(f"❌ Error during invalid action test: {str(e)}")
        return False

def main():
    print("=" * 60)
    print("🧪 Testing Unified Billboard Approval/Rejection Endpoint")
    print("=" * 60)
    
    # Step 1: Get admin token
    token = get_admin_token()
    if not token:
        print("\n❌ Cannot proceed without admin token. Exiting...")
        sys.exit(1)
    
    # Step 2: Get pending billboards
    pending_billboards = get_pending_billboards(token)
    
    if not pending_billboards:
        print("\n⚠️  No pending billboards found. Cannot test approval/rejection.")
        print("   Please create a pending billboard first, or test with an existing billboard ID.")
        return
    
    # Use the first pending billboard
    test_billboard = pending_billboards[0]
    billboard_id = test_billboard.get('id')
    
    print(f"\n📌 Using billboard ID: {billboard_id}")
    print(f"   City: {test_billboard.get('city', 'N/A')}")
    print(f"   Status: {test_billboard.get('approval_status', 'N/A')}")
    
    # Step 3: Test approve action
    approve_success = test_approve_billboard(token, billboard_id)
    
    # Step 4: Test invalid action (won't work since billboard is now approved)
    # We'll test this with a different billboard if available
    if len(pending_billboards) > 1:
        test_invalid_action(token, pending_billboards[1].get('id'))
    
    # Step 5: Get pending billboards again to find one to reject
    # (Note: The approved one is no longer pending)
    pending_after_approve = get_pending_billboards(token)
    
    if pending_after_approve:
        reject_billboard_id = pending_after_approve[0].get('id')
        reject_success = test_reject_billboard(token, reject_billboard_id, "Test rejection reason")
    else:
        print("\n⚠️  No pending billboards available for reject test.")
        reject_success = None
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)
    print(f"Approve Test: {'✅ PASSED' if approve_success else '❌ FAILED'}")
    if reject_success is not None:
        print(f"Reject Test:  {'✅ PASSED' if reject_success else '❌ FAILED'}")
    else:
        print(f"Reject Test:  ⚠️  SKIPPED (no pending billboards)")
    print("=" * 60)

if __name__ == "__main__":
    main()

