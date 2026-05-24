from django.contrib import admin
from .models import Province, District, Disease, CaseReport, AlertThreshold, Alert


@admin.register(Province)
class ProvinceAdmin(admin.ModelAdmin):
    list_display = ['name', 'code']
    search_fields = ['name', 'code']


@admin.register(District)
class DistrictAdmin(admin.ModelAdmin):
    list_display = ['name', 'province', 'population', 'latitude', 'longitude']
    list_filter = ['province']
    search_fields = ['name']


@admin.register(Disease)
class DiseaseAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'default_severity', 'is_notifiable', 'incubation_period_days']
    list_filter = ['default_severity', 'is_notifiable']
    search_fields = ['name', 'code']


@admin.register(CaseReport)
class CaseReportAdmin(admin.ModelAdmin):
    list_display = ['disease', 'district', 'case_count', 'onset_date', 'report_date', 'status', 'severity', 'lab_confirmed']
    list_filter = ['disease', 'district__province', 'status', 'severity', 'lab_confirmed']
    search_fields = ['disease__name', 'district__name', 'ward']
    date_hierarchy = 'report_date'
    readonly_fields = ['created_at', 'updated_at']


@admin.register(AlertThreshold)
class AlertThresholdAdmin(admin.ModelAdmin):
    list_display = ['disease', 'district', 'cases_per_week', 'is_active']
    list_filter = ['disease', 'is_active']


@admin.register(Alert)
class AlertAdmin(admin.ModelAdmin):
    list_display = ['title', 'disease', 'district', 'level', 'status', 'case_count', 'triggered_at']
    list_filter = ['level', 'status', 'disease']
    search_fields = ['title', 'message']
    readonly_fields = ['triggered_at']
