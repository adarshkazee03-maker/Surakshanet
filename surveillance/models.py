from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class Province(models.Model):
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=10, unique=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['name']


class District(models.Model):
    name = models.CharField(max_length=100)
    province = models.ForeignKey(Province, on_delete=models.CASCADE, related_name='districts')
    latitude = models.DecimalField(max_digits=9, decimal_places=6)
    longitude = models.DecimalField(max_digits=9, decimal_places=6)
    population = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"{self.name} ({self.province.name})"

    class Meta:
        ordering = ['name']


class Disease(models.Model):
    SEVERITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    ]

    name = models.CharField(max_length=100)
    code = models.CharField(max_length=20, unique=True)
    description = models.TextField(blank=True)
    default_severity = models.CharField(max_length=10, choices=SEVERITY_CHOICES, default='low')
    is_notifiable = models.BooleanField(default=True)
    incubation_period_days = models.PositiveIntegerField(default=7)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['name']


class CaseReport(models.Model):
    STATUS_CHOICES = [
        ('suspected', 'Suspected'),
        ('confirmed', 'Confirmed'),
        ('negative', 'Negative'),
        ('recovered', 'Recovered'),
        ('deceased', 'Deceased'),
    ]
    SEVERITY_CHOICES = [
        ('mild', 'Mild'),
        ('moderate', 'Moderate'),
        ('severe', 'Severe'),
        ('critical', 'Critical'),
    ]

    disease = models.ForeignKey(Disease, on_delete=models.CASCADE, related_name='cases')
    district = models.ForeignKey(District, on_delete=models.CASCADE, related_name='cases')
    reported_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='reported_cases')

    case_count = models.PositiveIntegerField(default=1)
    onset_date = models.DateField()
    report_date = models.DateField(default=timezone.now)
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='suspected')
    severity = models.CharField(max_length=10, choices=SEVERITY_CHOICES, default='mild')

    ward = models.CharField(max_length=100, blank=True)
    symptoms = models.TextField(blank=True)
    lab_confirmed = models.BooleanField(default=False)
    hospitalized = models.BooleanField(default=False)
    deaths = models.PositiveIntegerField(default=0)

    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.disease.name} — {self.district.name} ({self.report_date})"

    class Meta:
        ordering = ['-report_date', '-created_at']


class AlertThreshold(models.Model):
    disease = models.ForeignKey(Disease, on_delete=models.CASCADE, related_name='thresholds')
    district = models.ForeignKey(District, on_delete=models.CASCADE, related_name='thresholds', null=True, blank=True,
                                  help_text='Leave blank for nationwide threshold')
    cases_per_week = models.PositiveIntegerField(default=10)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        scope = self.district.name if self.district else 'Nationwide'
        return f"{self.disease.name} — {scope} ({self.cases_per_week} cases/week)"

    class Meta:
        unique_together = ['disease', 'district']


class Alert(models.Model):
    LEVEL_CHOICES = [
        ('info', 'Info'),
        ('warning', 'Warning'),
        ('critical', 'Critical'),
    ]
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('acknowledged', 'Acknowledged'),
        ('resolved', 'Resolved'),
    ]

    disease = models.ForeignKey(Disease, on_delete=models.CASCADE, related_name='alerts')
    district = models.ForeignKey(District, on_delete=models.CASCADE, related_name='alerts')
    level = models.CharField(max_length=10, choices=LEVEL_CHOICES, default='warning')
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='active')

    title = models.CharField(max_length=255)
    message = models.TextField()
    case_count = models.PositiveIntegerField()
    threshold = models.PositiveIntegerField()

    triggered_at = models.DateTimeField(auto_now_add=True)
    acknowledged_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    acknowledged_at = models.DateTimeField(null=True, blank=True)
    resolved_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"[{self.level.upper()}] {self.title}"

    class Meta:
        ordering = ['-triggered_at']
