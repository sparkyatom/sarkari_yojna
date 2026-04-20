import requests
import json

BASE_URL = "http://127.0.0.1:8000"

# Test login
print("TEST 1: User Login")
print("=" * 50)
try:
    # Try to login with test credentials
    login_resp = requests.post(f"{BASE_URL}/api/auth/login/", json={
        "username": "admin",
        "password": "admin123"
    })
    print(f"Login Status: {login_resp.status_code}")
    print(f"Login Response: {login_resp.text[:500]}")
    
    if login_resp.status_code == 200:
        login_data = login_resp.json()
        token = login_data.get('access')
        print(f"Got Access Token: {token[:20] if token else 'None'}...")
        
        # Test admin stats with token
        print("\nTEST 2: Admin Stats with Auth")
        print("=" * 50)
        headers = {"Authorization": f"Bearer {token}"}
        stats_resp = requests.get(f"{BASE_URL}/api/admin/stats/", headers=headers)
        print(f"Stats Status: {stats_resp.status_code}")
        print(f"Stats Response: {stats_resp.text}")
        
        # Test admin schemes with token
        print("\nTEST 3: Admin Schemes with Auth")
        print("=" * 50)
        schemes_resp = requests.get(f"{BASE_URL}/api/admin/schemes/", headers=headers)
        print(f"Admin Schemes Status: {schemes_resp.status_code}")
        data = schemes_resp.json()
        print(f"Admin Schemes Response: {json.dumps(data, indent=2)[:500]}")
        
except Exception as e:
    print(f"Error: {e}")

print("\n")

# Check available users
print("TEST 4: Check Available Users in Database")
print("=" * 50)
try:
    import sys
    sys.path.insert(0, 'c:\\Users\\sreya\\OneDrive\\Desktop\\sarkari_yojna\\backend')
    import os
    import django
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sarkari_yojana.settings')
    django.setup()
    
    from django.contrib.auth import get_user_model
    User = get_user_model()
    
    users = User.objects.all().values('username', 'is_admin', 'is_staff')
    print(f"Total users: {User.objects.count()}")
    for u in users:
        print(f"  - {u['username']}: is_admin={u['is_admin']}, is_staff={u['is_staff']}")
        
except Exception as e:
    print(f"Error: {e}")
