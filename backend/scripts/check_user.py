import os
import sys
from pathlib import Path
# Ensure backend is on sys.path
BASE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sarkari_yojana.settings')
import django
django.setup()

from django.contrib.auth import get_user_model
User = get_user_model()

USERNAME = 'riya'  # change if needed

try:
    user = User.objects.get(username=USERNAME)
except User.DoesNotExist:
    print(f"User '{USERNAME}' not found")
    sys.exit(1)

print('User:', user.username)
print('Full name:', getattr(user, 'full_name', None))
print('Date of birth:', getattr(user, 'date_of_birth', None))
print('Category:', getattr(user, 'category', None))
print('Income range:', getattr(user, 'income_range', None))
print('State:', getattr(user, 'state', None))
print('Occupation:', getattr(user, 'occupation', None))
print('Gender:', getattr(user, 'gender', None))
print('Family size:', getattr(user, 'family_size', None))

# Run matcher
from core.matcher import get_eligible_schemes
qs = get_eligible_schemes(user)
print('Eligible schemes count:', qs.count())
for s in qs[:20]:
    print('-', s.id, s.name, s.last_date)
