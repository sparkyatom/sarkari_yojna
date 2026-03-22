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
        return int(str(val).replace(',', '').strip())
    except (ValueError, TypeError):
        return default


def import_from_excel(file_obj):
    """
    file_obj: InMemoryUploadedFile (.xlsx or .xls)
    Returns: { 'created': int, 'skipped': int, 'errors': [str] }
    """
    wb = openpyxl.load_workbook(file_obj, data_only=True)
    ws = wb.active

    rows       = list(ws.iter_rows(values_only=True))
    headers    = [str(h).strip().lower() if h else '' for h in rows[0]]
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
    headers    = [h.strip().lower() for h in rows[0]]
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
            skipped += 1
            continue

        # Skip if already exists
        if Scheme.objects.filter(name=name).exists():
            skipped += 1
            continue

        last_date = parse_date(get('last_date'))
        if not last_date:
            errors.append(f"Row {row_num}: Invalid date '{get('last_date')}' for '{name}'")
            skipped += 1
            continue

        benefit_amount = parse_int(get('benefit_amount'))
        if not benefit_amount:
            errors.append(f"Row {row_num}: Invalid benefit_amount for '{name}'")
            skipped += 1
            continue

        # Validate category
        category = str(get('category', 'agriculture')).strip().lower()
        valid_cats = [c[0] for c in Scheme.CATEGORY_CHOICES]
        if category not in valid_cats:
            category = 'agriculture'

        # Build documents list
        docs_raw = str(get('required_documents', ''))
        docs = [d.strip() for d in docs_raw.replace(',', '\n').split('\n') if d.strip()]

        scheme = Scheme(
            name               = name,
            ministry           = str(get('ministry', 'Government of India')).strip(),
            category           = category,
            description        = str(get('description', '')).strip(),
            eligible_category  = str(get('eligible_category', 'all')).strip().lower() or 'all',
            eligible_occupation= str(get('eligible_occupation', 'all')).strip().lower() or 'all',
            eligible_gender    = str(get('eligible_gender', 'all')).strip().lower() or 'all',
            eligible_state     = str(get('eligible_state', 'all')).strip().lower() or 'all',
            min_income         = parse_int(get('min_income'), 0),
            max_income         = parse_int(get('max_income')) or None,
            benefit_amount     = benefit_amount,
            benefit_period     = str(get('benefit_period', 'per_year')).strip().lower() or 'per_year',
            last_date          = last_date,
            official_url       = str(get('official_url', '')).strip() or None,
            status             = str(get('status', 'active')).strip().lower() or 'active',
            icon               = str(get('icon', '📋')).strip() or '📋',
            required_documents = '\n'.join(docs),
        )
        schemes_to_create.append(scheme)

    if schemes_to_create:
        Scheme.objects.bulk_create(schemes_to_create)
        created = len(schemes_to_create)

    return {'created': created, 'skipped': skipped, 'errors': errors}
