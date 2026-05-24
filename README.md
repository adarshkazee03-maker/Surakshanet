# SurakshaNet
### A Web-Based Disease Surveillance and Outbreak Alert System with Geo-Visualization for Nepal

**Course:** Health Informatics Project I (HIMS 256)  
**Department:** Health Informatics  
**Group:** Adarsh Thapa · Bhupendra Neupane · Pranisha Shrestha · Jasmina Bhandari

---

## Quick Start

### 1. Prerequisites
- Python 3.10+
- pip

### 2. Create and activate a virtual environment
```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Run migrations
```bash
python manage.py migrate
```

### 5. Seed sample data (Nepal districts, diseases, cases)
```bash
python manage.py seed_data
```
This creates:
- Admin user: **admin / admin123**
- 7 provinces, 20 districts across Nepal
- 8 diseases (Dengue, Typhoid, Influenza, Cholera, TB, Malaria, Kala-azar, Diarrhoea)
- Alert thresholds
- 8 weeks of sample case data

### 6. Start the development server
```bash
python manage.py runserver
```

Open **http://127.0.0.1:8000** and log in with `admin / admin123`.

---

## Features

| Feature | Description |
|---|---|
| **Dashboard** | Real-time stats, weekly trend charts (Chart.js), hotspot districts |
| **Case Reports** | Submit, filter, edit and delete disease case reports |
| **GIS Map** | Leaflet.js + OpenStreetMap — colour-coded district outbreak circles |
| **Alert Engine** | Automatic threshold-based alerts; acknowledge & resolve workflow |
| **Thresholds** | Configurable cases/week trigger per disease and per district |
| **Admin panel** | Full Django admin at `/admin/` |

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python 3, Django 5 |
| REST API | Django REST Framework |
| Database | SQLite (dev) / PostgreSQL (production) |
| Maps | Leaflet.js + OpenStreetMap |
| Charts | Chart.js 4 |
| Frontend | Bootstrap 5, Bootstrap Icons |

## Switching to PostgreSQL (production)

In `surakshanet/settings.py`, replace the DATABASES block:

```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'surakshanet',
        'USER': 'your_db_user',
        'PASSWORD': 'your_password',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}
```

Then `pip install psycopg2-binary` and re-run migrations.

## Project Structure

```
surakshanet/
├── manage.py
├── requirements.txt
├── surakshanet/          # Django project config
│   ├── settings.py
│   └── urls.py
└── surveillance/         # Main app
    ├── models.py         # Province, District, Disease, CaseReport, Alert, Threshold
    ├── views.py          # Dashboard, cases, map, alerts, API
    ├── urls.py
    ├── forms.py
    ├── alerts.py         # Alert engine logic
    ├── context_processors.py
    ├── admin.py
    ├── management/
    │   └── commands/
    │       └── seed_data.py
    └── templates/
        └── surveillance/
            ├── base.html
            ├── login.html
            ├── dashboard.html
            ├── case_list.html
            ├── case_form.html
            ├── map.html
            ├── alert_list.html
            └── threshold_list.html
```
# Surakshanet
# Surakshanet
