import requests
import json

BASE_URL = "http://127.0.0.1:8000"

# Test login with new password
print("TEST 1: Admin Login with New Password")
print("=" * 50)
try:
    login_resp = requests.post(f"{BASE_URL}/api/auth/login/", json={
        "username": "admin",
        "password": "admin@123"
    })
    print(f"Login Status: {login_resp.status_code}")
    
    if login_resp.status_code == 200:
        login_data = login_resp.json()
        token = login_data.get('access')
        user_info = login_data.get('user', {})
        print(f"✓ Login successful!")
        print(f"  - Username: {user_info.get('username')}")
        print(f"  - Full Name: {user_info.get('full_name')}")
        print(f"  - Is Admin: {user_info.get('is_admin')}")
        print(f"  - Token (first 20 chars): {token[:20] if token else 'None'}...")
        
        # Test admin stats with token
        print("\nTEST 2: Admin Stats Endpoint")
        print("=" * 50)
        headers = {"Authorization": f"Bearer {token}"}
        stats_resp = requests.get(f"{BASE_URL}/api/admin/stats/", headers=headers)
        print(f"Status: {stats_resp.status_code}")
        stats_data = stats_resp.json()
        print(f"Stats: {json.dumps(stats_data, indent=2)}")
        
        # Test admin schemes with token
        print("\nTEST 3: Admin Schemes Endpoint")
        print("=" * 50)
        schemes_resp = requests.get(f"{BASE_URL}/api/admin/schemes/", headers=headers)
        print(f"Status: {schemes_resp.status_code}")
        schemes_data = schemes_resp.json()
        print(f"Total schemes: {schemes_data.get('count')}")
        print(f"Schemes returned: {len(schemes_data.get('results', []))}")
        
        if schemes_data.get('results'):
            print(f"First scheme: {schemes_data['results'][0]}")
        
    else:
        print(f"✗ Login failed: {login_resp.text}")
        
except Exception as e:
    print(f"Error: {e}")
