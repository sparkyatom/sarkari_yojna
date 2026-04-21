"""
core/excel_importer.py
Parses uploaded Excel / CSV files and bulk-creates Scheme records.

Expected columns (case-insensitive):
  scheme_name, category, ministry, description, eligible_category,
  eligible_occupation, eligible_gender, eligible_state,
  min_income, max_income, benefit_amount, benefit_period,
  last_date, official_url, required_documents, status, icon
"""
import openpyxl
import csv
import io
from datetime import datetime
from schemes.models import Scheme


COLUMN_MAP = {
    'scheme_name':          'name',
    'name':                 'name',
    'category':             'category',
    'ministry':             'ministry',
    'description':          'description',
    'eligible_category':    'eligible_category',
    'caste':                'eligible_category',
    'eligible_occupation':  'eligible_occupation',
    'occupation':           'eligible_occupation',
    'eligible_gender':      'eligible_gender',
    'gender':               'eligible_gender',
    'eligible_state':       'eligible_state',
    'state':                'eligible_state',
    'min_income':           'min_income',
    'max_income':           'max_income',
    'min_age':              'min_age',
    'max_age':              'max_age',
    'benefit_amount':       'benefit_amount',
    'benefit':              'benefit_amount',
    'benefit_period':       'benefit_period',
    'period':               'benefit_period',
    'last_date':            'last_date',
    'deadline':             'last_date',
    'official_url':         'official_url',
    'url':                  'official_url',
    'required_documents':   'required_documents',
    'documents':            'required_documents',
    'status':               'status',
    'icon':                 'icon',
}

VALID_CHOICES = {
    'category': [c[0] for c in Scheme.CATEGORY_CHOICES],
    'status': [c[0] for c in Scheme.STATUS_CHOICES],
    'benefit_period': [c[0] for c in Scheme.PERIOD_CHOICES],
    'eligible_gender': [c[0] for c in Scheme.GENDER_CHOICES],
    'eligible_category': [c[0] for c in Scheme.ELIGIBLE_CAT_CHOICES],
    'eligible_occupation': [c[0] for c in Scheme.OCCUPATION_CHOICES],
}


def parse_date(val):
    if not val:
        return None
    if isinstance(val, datetime):
        return val.date()
    for fmt in ('%Y-%m-%d', '%d/%m/%Y', '%d-%m-%Y', '%d %b %Y'):
        try:
            return datetime.strptime(str(val).strip(), fmt).date()
        except ValueError:
            continue
    return None


def parse_int(val, default=0):
    try:
        if default is None and (val is None or str(val).strip() == ''):
            return None
        return int(str(val).replace(',', '').strip())
    except (ValueError, TypeError):
        return default


def normalize_text(val):
    if not val:
        return ''
    text = str(val).strip().lower()
    text = text.replace('&', ' and ')
    text = text.replace('-', ' ')
    text = text.replace('_', ' ')
    text = text.replace(',', ' ')
    return ' '.join(text.split())


def normalize_category(val):
    raw = normalize_text(val)
    if raw in VALID_CHOICES['category']:
        return raw
    mapping = {
        'women and child': 'women',
        'women child': 'women',
        'social security': 'social',
        'finance and loans': 'finance',
        'finance loans': 'finance',
    }
    return mapping.get(raw, '')


def normalize_eligible_category(val):
    raw = normalize_text(val)
    if not raw:
        return ''
    if raw == 'all' or ' all ' in f' {raw} ':
        return 'all'
    if 'sc' in raw and 'st' in raw and 'obc' in raw:
        return 'sc_st_obc'
    if 'sc' in raw and 'st' in raw:
        return 'sc_st'
    if 'sc' in raw:
        return 'sc'
    if 'st' in raw:
        return 'st'
    if 'obc' in raw:
        return 'obc'
    if 'general' in raw:
        return 'general'
    return ''


def normalize_eligible_occupation(val):
    raw = normalize_text(val)
    if raw in VALID_CHOICES['eligible_occupation']:
        return raw
    if 'student' in raw:
        return 'student'
    if 'farmer' in raw:
        return 'farmer'
    if 'self' in raw:
        return 'self_employed'
    if 'daily' in raw or 'wage' in raw or 'labor' in raw or 'labour' in raw:
        return 'labour'
    if 'teacher' in raw:
        return 'teacher'
    if 'business' in raw:
        return 'business'
    if 'unemployed' in raw or 'artisan' in raw:
        return 'other'
    return ''


def normalize_benefit_period(val):
    raw = normalize_text(val)
    if raw in VALID_CHOICES['benefit_period']:
        return raw
    if 'season' in raw:
        return 'per_year'
    if 'month' in raw:
        return 'per_month'
    if 'year' in raw:
        return 'per_year'
    if 'one' in raw:
        return 'one_time'
    if 'install' in raw:
        return 'per_installment'
    return ''


def normalize_eligible_state(val):
    raw = normalize_text(val)
    if not raw:
        return 'all'
    if raw in {'all', 'all states', 'all state', 'all_states'}:
        return 'all'
    return raw


def import_from_excel(file_obj):
    """
    file_obj: InMemoryUploadedFile (.xlsx or .xls)
    Returns: { 'created': int, 'skipped': int, 'errors': [str] }
    """
    wb = openpyxl.load_workbook(file_obj, data_only=True)
    ws = wb.active

    rows       = list(ws.iter_rows(values_only=True))
    headers    = [str(h).replace(' ', '_').replace('-', '_').strip().lower() if h else '' for h in rows[0]]
    data_rows  = rows[1:]

    return _process_rows(headers, data_rows)


def import_from_csv(file_obj):
    """
    file_obj: InMemoryUploadedFile (.csv)
    Returns: { 'created': int, 'skipped': int, 'errors': [str] }
    """
    content = file_obj.read().decode('utf-8-sig')
    reader  = csv.reader(io.StringIO(content))
    rows    = list(reader)
    headers    = [h.replace(' ', '_').replace('-', '_').strip().lower() for h in rows[0]]
    data_rows  = [tuple(r) for r in rows[1:]]

    return _process_rows(headers, data_rows)


def _process_rows(headers, data_rows):
    created = 0
    skipped = 0
    errors  = []

    # Map header index → model field name
    field_idx = {}
    for i, h in enumerate(headers):
        if h in COLUMN_MAP:
            field_idx[COLUMN_MAP[h]] = i

    required = {'name', 'category', 'benefit_amount', 'last_date'}
    missing  = required - set(field_idx.keys())
    if missing:
        return {
            'created': 0,
            'skipped': 0,
            'errors': [f"Missing required columns: {', '.join(missing)}"]
        }

    schemes_to_create = []

    for row_num, row in enumerate(data_rows, start=2):
        def get(field, default=''):
            idx = field_idx.get(field)
            return row[idx] if idx is not None and idx < len(row) else default

        name = str(get('name', '')).strip()
        if not name:
            errors.append(f"Row {row_num}: Missing scheme name")
            skipped += 1
            continue

        # Skip if already exists
        if Scheme.objects.filter(name=name).exists():
            errors.append(f"Row {row_num}: Scheme '{name}' already exists")
            skipped += 1
            continue

        last_date = parse_date(get('last_date'))
        if not last_date:
            errors.append(f"Row {row_num}: Invalid date '{get('last_date')}' for '{name}'")
            skipped += 1
            continue

        benefit_amount = parse_int(get('benefit_amount'))
        if not benefit_amount:
            errors.append(f"Row {row_num}: Invalid benefit_amount '{get('benefit_amount')}' for '{name}'")
            skipped += 1
            continue

        # Validate category
        category = normalize_category(get('category'))
        if not category:
            errors.append(f"Row {row_num}: Invalid category '{get('category')}' for '{name}'")
            skipped += 1
            continue

        # Validate status
        status = normalize_text(get('status', 'active')) or 'active'
        if status not in VALID_CHOICES['status']:
            errors.append(f"Row {row_num}: Invalid status '{get('status')}' for '{name}'")
            skipped += 1
            continue

        # Validate benefit_period
        benefit_period = normalize_benefit_period(get('benefit_period', 'per_year')) or 'per_year'
        if benefit_period not in VALID_CHOICES['benefit_period']:
            errors.append(f"Row {row_num}: Invalid benefit_period '{get('benefit_period')}' for '{name}'")
            skipped += 1
            continue

        # Validate eligible_gender
        eligible_gender = normalize_text(get('eligible_gender', 'all')) or 'all'
        if eligible_gender not in VALID_CHOICES['eligible_gender']:
            errors.append(f"Row {row_num}: Invalid eligible_gender '{get('eligible_gender')}' for '{name}'")
            skipped += 1
            continue

        # Validate eligible_category
        eligible_category = normalize_eligible_category(get('eligible_category', 'all')) or 'all'
        if eligible_category not in VALID_CHOICES['eligible_category']:
            errors.append(f"Row {row_num}: Invalid eligible_category '{get('eligible_category')}' for '{name}'")
            skipped += 1
            continue

        # Validate eligible_occupation
        eligible_occupation = normalize_eligible_occupation(get('eligible_occupation', 'all')) or 'all'
        if eligible_occupation not in VALID_CHOICES['eligible_occupation']:
            errors.append(f"Row {row_num}: Invalid eligible_occupation '{get('eligible_occupation')}' for '{name}'")
            skipped += 1
            continue

        # Build documents list
        docs_raw = str(get('required_documents', ''))
        docs = [d.strip() for d in docs_raw.replace(',', '\n').split('\n') if d.strip()]

        scheme = Scheme(
            name               = name,
            ministry           = str(get('ministry', 'Government of India')).strip(),
            category           = category,
            description        = str(get('description', '')).strip(),
            eligible_category  = eligible_category,
            eligible_occupation= eligible_occupation,
            eligible_gender    = eligible_gender,
            eligible_state     = normalize_eligible_state(get('eligible_state', 'all')), 
            min_income         = parse_int(get('min_income'), 0),
            max_income         = parse_int(get('max_income')) or None,
            min_age            = parse_int(get('min_age'), None),
            max_age            = parse_int(get('max_age'), None),
            benefit_amount     = benefit_amount,
            benefit_period     = benefit_period,
            last_date          = last_date,
            official_url       = str(get('official_url', '')).strip() or None,
            status             = status,
            icon               = str(get('icon', '📋')).strip() or '📋',
            required_documents = '\n'.join(docs),
        )
        schemes_to_create.append(scheme)

    if schemes_to_create:
        Scheme.objects.bulk_create(schemes_to_create)
        created = len(schemes_to_create)

    return {'created': created, 'skipped': skipped, 'errors': errors}
