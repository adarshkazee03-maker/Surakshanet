from django.urls import path
from . import views

urlpatterns = [
    # Dashboard
    path('', views.dashboard, name='dashboard'),

    # Cases
    path('cases/', views.case_list, name='case_list'),
    path('cases/new/', views.case_create, name='case_create'),
    path('cases/<int:pk>/edit/', views.case_edit, name='case_edit'),
    path('cases/<int:pk>/delete/', views.case_delete, name='case_delete'),

    # Map
    path('map/', views.map_view, name='map'),

    # Alerts
    path('alerts/', views.alert_list, name='alert_list'),
    path('alerts/<int:pk>/acknowledge/', views.alert_acknowledge, name='alert_acknowledge'),
    path('alerts/<int:pk>/resolve/', views.alert_resolve, name='alert_resolve'),
    path('alerts/check/', views.run_alert_check, name='run_alert_check'),

    # Thresholds
    path('thresholds/', views.threshold_list, name='threshold_list'),
    path('thresholds/new/', views.threshold_create, name='threshold_create'),
    path('thresholds/<int:pk>/edit/', views.threshold_edit, name='threshold_edit'),
    path('thresholds/<int:pk>/delete/', views.threshold_delete, name='threshold_delete'),

    # API
    path('api/map-data/', views.api_map_data, name='api_map_data'),
    path('api/trend/', views.api_trend, name='api_trend'),
    path('api/stats/', views.api_stats, name='api_stats'),
]
