import os, sys, json
from pathlib import Path
BASE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sarkari_yojana.settings')
import django
django.setup()

from django.contrib.auth import get_user_model
from users.serializers import ProfileSerializer, UserSummarySerializer
from rest_framework.test import APIRequestFactory
from schemes.views import SchemeCategoriesView

User = get_user_model()
USERNAME = 'riya'

try:
    user = User.objects.get(username=USERNAME)
except User.DoesNotExist:
    print(f"User '{USERNAME}' not found")
    sys.exit(1)

print('--- PROFILE SERIALIZER ---')
print(json.dumps(ProfileSerializer(user).data, default=str, indent=2))
print('\n--- USER SUMMARY (login payload) ---')
print(json.dumps(UserSummarySerializer(user).data, default=str, indent=2))

# Call categorized view
factory = APIRequestFactory()
request = factory.get('/api/schemes/categorized/')
request.user = user
view = SchemeCategoriesView()
resp = view.get(request)
print('\n--- /api/schemes/categorized/ RESPONSE ---')
print(json.dumps(resp.data, default=str, indent=2))
