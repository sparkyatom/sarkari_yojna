import os, sys
from pathlib import Path
BASE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sarkari_yojana.settings')
import django
django.setup()
from django.utils import timezone
from schemes.models import Scheme

today = timezone.now().date()
base_qs = Scheme.objects.filter(status='active', last_date__gte=today)
print('Active schemes (not expired):', base_qs.count())
for s in base_qs.order_by('last_date')[:20]:
    print('-', s.id, s.name, s.category, s.eligible_category, s.eligible_state, s.eligible_occupation, s.eligible_gender, s.min_income, s.max_income, s.last_date)
