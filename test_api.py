import requests
import json

BASE_URL = "http://127.0.0.1:8000"

# Test 1: Check if admin stats endpoint exists and works
print("TEST 1: Admin Stats Endpoint")
print("=" * 50)
try:
    resp = requests.get(f"{BASE_URL}/api/admin/stats/", timeout=5)
    print(f"Status Code: {resp.status_code}")
    print(f"Response: {resp.text[:500]}")
except Exception as e:
    print(f"Error: {e}")

print("\n")

# Test 2: Check if schemes endpoint works
print("TEST 2: Schemes Endpoint")
print("=" * 50)
try:
    resp = requests.get(f"{BASE_URL}/api/schemes/", timeout=5)
    print(f"Status Code: {resp.status_code}")
    data = resp.json()
    print(f"Response Keys: {list(data.keys())}")
    if 'results' in data:
        print(f"Number of schemes: {len(data['results'])}")
    elif isinstance(data, list):
        print(f"Number of schemes: {len(data)}")
    else:
        print(f"Response: {json.dumps(data, indent=2)[:500]}")
except Exception as e:
    print(f"Error: {e}")

print("\n")

# Test 3: Check database status
print("TEST 3: Database Status")
print("=" * 50)
try:
    import os
    import django
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sarkari_yojana.settings')
    django.setup()
    from schemes.models import Scheme
    from django.contrib.auth import get_user_model
    
    scheme_count = Scheme.objects.count()
    user_count = get_user_model().objects.count()
    
    print(f"Total Schemes in DB: {scheme_count}")
    print(f"Total Users in DB: {user_count}")
except Exception as e:
    print(f"Error: {e}")
