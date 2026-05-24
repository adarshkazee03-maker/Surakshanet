from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
import random

from surveillance.models import Province, District, Disease, CaseReport, AlertThreshold


PROVINCES = [
    ('Koshi', 'P1'),
    ('Madhesh', 'P2'),
    ('Bagmati', 'P3'),
    ('Gandaki', 'P4'),
    ('Lumbini', 'P5'),
    ('Karnali', 'P6'),
    ('Sudurpashchim', 'P7'),
]

DISTRICTS = [
    # (name, province_code, lat, lng, population)
    ('Kathmandu',   'P3', 27.7172, 85.3240, 1744240),
    ('Lalitpur',    'P3', 27.6588, 85.3247, 468132),
    ('Bhaktapur',   'P3', 27.6710, 85.4298, 304651),
    ('Kaski',       'P4', 28.2096, 83.9856, 492098),
    ('Chitwan',     'P3', 27.5291, 84.3542, 579984),
    ('Jhapa',       'P1', 26.5217, 87.8979, 812650),
    ('Morang',      'P1', 26.6670, 87.4330, 965370),
    ('Sunsari',     'P1', 26.6500, 87.1670, 763487),
    ('Rupandehi',   'P5', 27.5000, 83.4500, 880196),
    ('Bardiya',     'P5', 28.2833, 81.5167, 426576),
    ('Banke',       'P5', 28.0500, 81.6000, 491313),
    ('Dang',        'P5', 28.0667, 82.3000, 552583),
    ('Makwanpur',   'P3', 27.3167, 85.0000, 420477),
    ('Parsa',       'P2', 27.0000, 84.9000, 601017),
    ('Sarlahi',     'P2', 26.9667, 85.5833, 769729),
    ('Mahottari',   'P2', 26.7833, 85.9167, 627580),
    ('Dhanusha',    'P2', 26.8167, 86.0500, 754777),
    ('Dolakha',     'P3', 27.8000, 86.0000, 186557),
    ('Sindhupalchok','P3', 27.8833, 85.7500, 287798),
    ('Kailali',     'P7', 28.6500, 80.6000, 775709),
]

DISEASES = [
    ('Dengue Fever',       'DENGUE',   'high',   14),
    ('Typhoid Fever',      'TYPHOID',  'medium', 10),
    ('Influenza',          'FLU',      'low',    3),
    ('Cholera',            'CHOLERA',  'critical',2),
    ('Tuberculosis',       'TB',       'medium', 90),
    ('Malaria',            'MALARIA',  'high',   14),
    ('Kala-azar',          'KALAAZAR', 'high',   60),
    ('Acute Diarrhoea',    'DIARR',    'low',    2),
]

THRESHOLDS = [
    ('DENGUE',  None, 20),
    ('TYPHOID', None, 10),
    ('FLU',     None, 30),
    ('CHOLERA', None, 3),
    ('DENGUE',  'Kathmandu', 15),
    ('DENGUE',  'Lalitpur', 10),
]


class Command(BaseCommand):
    help = 'Seed the database with Nepal provinces, districts, diseases and sample data'

    def handle(self, *args, **options):
        self.stdout.write('🌱 Seeding SurakshaNet...')

        # Superuser
        if not User.objects.filter(username='admin').exists():
            User.objects.create_superuser('admin', 'admin@surakshanet.np', 'admin123')
            self.stdout.write('  ✓ Superuser: admin / admin123')

        # Provinces
        province_map = {}
        for name, code in PROVINCES:
            p, _ = Province.objects.get_or_create(code=code, defaults={'name': name})
            province_map[code] = p
        self.stdout.write(f'  ✓ {len(PROVINCES)} provinces')

        # Districts
        district_map = {}
        for name, pcode, lat, lng, pop in DISTRICTS:
            d, _ = District.objects.get_or_create(
                name=name,
                defaults={'province': province_map[pcode], 'latitude': lat, 'longitude': lng, 'population': pop}
            )
            district_map[name] = d
        self.stdout.write(f'  ✓ {len(DISTRICTS)} districts')

        # Diseases
        disease_map = {}
        for name, code, sev, incub in DISEASES:
            dis, _ = Disease.objects.get_or_create(
                code=code,
                defaults={'name': name, 'default_severity': sev, 'incubation_period_days': incub}
            )
            disease_map[code] = dis
        self.stdout.write(f'  ✓ {len(DISEASES)} diseases')

        # Thresholds
        for dcode, dname, per_week in THRESHOLDS:
            district = district_map.get(dname) if dname else None
            AlertThreshold.objects.get_or_create(
                disease=disease_map[dcode],
                district=district,
                defaults={'cases_per_week': per_week}
            )
        self.stdout.write(f'  ✓ {len(THRESHOLDS)} alert thresholds')

        # Sample case reports — past 8 weeks
        admin = User.objects.get(username='admin')
        today = timezone.now().date()

        # Disease-district hotspot weights
        hotspots = [
            ('DENGUE',  'Kathmandu',  [3,5,4,8,12,10,18,22]),
            ('DENGUE',  'Lalitpur',   [2,3,2,5,7,6,11,14]),
            ('DENGUE',  'Kaski',      [0,1,2,3,4,3,7,9]),
            ('TYPHOID', 'Lalitpur',   [1,2,1,2,3,4,5,6]),
            ('TYPHOID', 'Bhaktapur',  [0,1,1,2,2,3,4,5]),
            ('FLU',     'Kathmandu',  [8,10,9,12,14,11,8,6]),
            ('FLU',     'Chitwan',    [3,4,5,6,7,6,5,4]),
            ('MALARIA', 'Kailali',    [2,3,4,3,5,4,6,5]),
            ('CHOLERA', 'Sarlahi',    [0,0,1,0,2,1,3,2]),
            ('DIARR',   'Morang',     [5,6,7,8,9,8,7,6]),
        ]

        if CaseReport.objects.count() == 0:
            for dcode, dname, weekly_counts in hotspots:
                disease = disease_map.get(dcode)
                district = district_map.get(dname)
                if not disease or not district:
                    continue
                for week_idx, count in enumerate(weekly_counts):
                    if count == 0:
                        continue
                    weeks_back = 7 - week_idx
                    report_date = today - timedelta(weeks=weeks_back)
                    CaseReport.objects.create(
                        disease=disease,
                        district=district,
                        reported_by=admin,
                        case_count=count,
                        onset_date=report_date - timedelta(days=random.randint(1, 5)),
                        report_date=report_date,
                        status=random.choice(['suspected', 'suspected', 'confirmed']),
                        severity=random.choice(['mild', 'mild', 'moderate', 'severe']),
                        ward=f"Ward {random.randint(1,32)}",
                        lab_confirmed=random.choice([True, False]),
                    )
            self.stdout.write(f'  ✓ Sample case reports created')
        else:
            self.stdout.write('  ℹ Case reports already exist, skipping')

        self.stdout.write(self.style.SUCCESS('\n✅ Seeding complete! Visit http://127.0.0.1:8000 and login with admin / admin123'))
