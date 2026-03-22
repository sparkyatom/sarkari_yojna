# SarkariYojana — Complete Full-Stack Project
## Government Schemes Eligibility Portal

---

## What's Inside
```
sarkari_yojana/
├── frontend/
│   ├── index.html          ← Homepage with stats + categories
│   ├── login.html          ← Login page (JWT auth)
│   ├── signup.html         ← Multi-step signup form (3 steps)
│   ├── schemes.html        ← Schemes listing + filters + detail modal
│   ├── admin-panel.html    ← Full admin dashboard
│   ├── css/
│   │   └── styles.css      ← Complete design system
│   └── js/
│       └── api.js          ← All API calls + auth helpers + utilities
│
├── backend/
│   ├── manage.py
│   ├── requirements.txt
│   ├── sarkari_yojana/
│   │   ├── settings.py     ← Django settings (MySQL, JWT, CORS)
│   │   ├── urls.py         ← Root URL config
│   │   └── wsgi.py
│   ├── users/              ← Custom user model + auth APIs
│   │   ├── models.py       ← UserProfile (all eligibility fields)
│   │   ├── serializers.py
│   │   ├── views.py        ← Register, Login, Logout, Profile
│   │   └── urls.py
│   ├── schemes/            ← Scheme model + public APIs
│   │   ├── models.py       ← Scheme (all eligibility + benefit fields)
│   │   ├── serializers.py
│   │   ├── views.py        ← List, Detail, EligibleSchemes
│   │   └── urls.py
│   └── core/               ← Admin APIs + matching engine
│       ├── models.py       ← UploadHistory
│       ├── views.py        ← Admin CRUD, Excel upload, Stats, Users
│       ├── urls.py
│       ├── matcher.py      ← Eligibility matching algorithm
│       └── excel_importer.py ← Parse .xlsx/.csv bulk uploads
│
└── docs/
    └── database_schema.sql ← Full MySQL schema + 10 seed schemes
```

---

## STEP 1 — MySQL Setup

Open MySQL Workbench or MySQL command line and run:

```sql
-- Option A: Run the full SQL file
SOURCE C:/path/to/sarkari_yojana/docs/database_schema.sql;

-- Option B: Manual setup
CREATE DATABASE sarkari_yojana_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'syuser'@'localhost' IDENTIFIED BY 'SY@pass2024';
GRANT ALL PRIVILEGES ON sarkari_yojana_db.* TO 'syuser'@'localhost';
FLUSH PRIVILEGES;
```

The SQL file also inserts 10 real government schemes as seed data.

---

## STEP 2 — Django Backend Setup

Open a terminal in the `backend/` folder:

```bash
# 1. Create virtual environment
python -m venv venv

# 2. Activate it
venv\Scripts\activate          # Windows
# source venv/bin/activate    # Mac/Linux

# 3. Install packages
pip install -r requirements.txt

# 4. Run migrations (creates all tables in MySQL)
python manage.py migrate

# 5. Create an admin superuser
python manage.py createsuperuser
# Enter username, then set is_admin=True manually in MySQL:
# UPDATE user_profiles SET is_admin=1, is_staff=1 WHERE username='your_admin_username';

# 6. Start the server
python manage.py runserver
```

Backend runs at: **http://localhost:8000**

---

## STEP 3 — Frontend

1. Open the `frontend/` folder in VS Code
2. Right-click `index.html` → **Open with Live Server**
3. Frontend runs at: **http://localhost:5500**

The frontend works immediately with mock data even without the backend.
When Django is running, it automatically connects via the API calls in `api.js`.

---

## API Reference

### Auth
| Method | URL | Body | Description |
|--------|-----|------|-------------|
| POST | `/api/auth/register/` | user fields | Create account |
| POST | `/api/auth/login/` | username, password | Returns JWT tokens |
| POST | `/api/auth/logout/` | refresh token | Blacklists token |
| GET  | `/api/auth/profile/` | — | Get logged-in user profile |
| PATCH| `/api/auth/profile/` | fields to update | Update profile |
| POST | `/api/auth/token/refresh/` | refresh | Get new access token |

### Schemes (Public)
| Method | URL | Description |
|--------|-----|-------------|
| GET | `/api/schemes/` | All active schemes |
| GET | `/api/schemes/?category=education` | Filter by category |
| GET | `/api/schemes/?search=kisan` | Full-text search |
| GET | `/api/schemes/eligible/` | Schemes matching logged-in user's profile |
| GET | `/api/schemes/1/` | Single scheme detail |

### Admin (requires is_admin=True)
| Method | URL | Description |
|--------|-----|-------------|
| GET | `/api/admin/stats/` | Dashboard KPIs |
| GET | `/api/admin/schemes/` | All schemes (admin view) |
| POST | `/api/admin/schemes/` | Create new scheme |
| PUT | `/api/admin/schemes/1/` | Update scheme |
| DELETE | `/api/admin/schemes/1/` | Delete scheme |
| POST | `/api/admin/upload/excel/` | Bulk upload Excel/CSV |
| GET | `/api/admin/users/` | All registered users |
| GET | `/api/admin/uploads/` | Upload history |

---

## Excel Upload Format

Your `.xlsx` or `.csv` file must have these column headers:

| Column | Required | Example |
|--------|----------|---------|
| scheme_name | ✅ | PM Kisan Samman Nidhi |
| category | ✅ | agriculture |
| ministry | ✅ | Ministry of Agriculture |
| description | ✅ | Direct income support... |
| benefit_amount | ✅ | 6000 |
| last_date | ✅ | 2026-05-31 |
| eligible_category | | all / sc / st / obc / sc_st / sc_st_obc |
| eligible_occupation | | all / farmer / student / labour / ... |
| eligible_gender | | all / male / female |
| eligible_state | | all / andhra_pradesh / telangana / ... |
| min_income | | 0 |
| max_income | | 250000 |
| benefit_period | | per_year / per_month / one_time |
| required_documents | | Aadhaar Card, Income Certificate |
| official_url | | https://scheme.gov.in |
| status | | active / draft |
| icon | | 🌾 |

---

## Troubleshooting

**"ModuleNotFoundError: No module named 'MySQLdb'"**
```bash
pip install mysqlclient
# If that fails on Windows:
pip install PyMySQL
# Then add to backend/sarkari_yojana/__init__.py:
# import pymysql; pymysql.install_as_MySQLdb()
```

**"Access denied for user 'syuser'"**
- Check MySQL is running
- Re-run the GRANT commands in database_schema.sql

**CORS error in browser console**
- Make sure Django is running on port 8000
- Check that CORS_ALLOWED_ORIGINS in settings.py includes your frontend URL

**Frontend shows mock data only**
- That's expected when Django is not running
- Start Django server with `python manage.py runserver` to use real data

---

## Making Yourself Admin

After registering via the signup page, run this in MySQL:
```sql
USE sarkari_yojana_db;
UPDATE user_profiles SET is_admin=1, is_staff=1, is_superuser=1
WHERE username='your_username';
```
Then log out and log back in. The Admin Panel will now work fully.
