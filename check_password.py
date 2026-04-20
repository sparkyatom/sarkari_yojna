import sys
sys.path.insert(0, 'c:\\Users\\sreya\\OneDrive\\Desktop\\sarkari_yojna\\backend')
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sarkari_yojana.settings')
django.setup()

from django.contrib.auth import get_user_model, authenticate

User = get_user_model()

print("CHECK 1: Admin User Details")
print("=" * 50)
try:
    user = User.objects.get(username='admin')
    print(f"Username: {user.username}")
    print(f"Is active: {user.is_active}")
    print(f"Is admin: {user.is_admin}")
    print(f"Is staff: {user.is_staff}")
    print(f"Password hash (first 50 chars): {user.password[:50]}")
except Exception as e:
    print(f"Error: {e}")

print("\nCHECK 2: Test Password Authentication")
print("=" * 50)
try:
    # Try authenticating with various passwords
    passwords = ['admin123', 'admin', 'password', 'admin@123']
    
    for pwd in passwords:
        result = authenticate(username='admin', password=pwd)
        if result:
            print(f"✓ Password '{pwd}' works!")
        else:
            print(f"✗ Password '{pwd}' does NOT work")
            
except Exception as e:
    print(f"Error: {e}")

print("\nCHECK 3: Reset Admin Password")
print("=" * 50)
try:
    user = User.objects.get(username='admin')
    new_password = 'admin@123'
    user.set_password(new_password)
    user.save()
    print(f"✓ Password reset to '{new_password}'")
    
    # Test new password
    result = authenticate(username='admin', password=new_password)
    if result:
        print(f"✓ New password verified!")
    else:
        print(f"✗ Password verification FAILED")
        
except Exception as e:
    print(f"Error: {e}")
