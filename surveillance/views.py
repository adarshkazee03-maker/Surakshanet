import json
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone
from django.db.models import Sum, Count
from datetime import timedelta

from .models import CaseReport, Alert, District, Disease, AlertThreshold
from .forms import CaseReportForm, AlertThresholdForm, CaseFilterForm
from .alerts import check_and_fire_alerts, get_dashboard_stats, get_weekly_trend, get_district_case_map


# ─── Dashboard ───────────────────────────────────────────────────────────────

@login_required
def dashboard(request):
    stats = get_dashboard_stats()
    recent_alerts = Alert.objects.filter(status='active').select_related('disease', 'district')[:5]
    recent_cases = CaseReport.objects.select_related('disease', 'district').order_by('-created_at')[:8]

    # Top districts by cases this week
    week_ago = timezone.now().date() - timedelta(days=7)
    top_districts = []
    for d in District.objects.all():
        count = sum(r.case_count for r in d.cases.filter(report_date__gte=week_ago))
        if count:
            top_districts.append({'name': d.name, 'count': count})
    top_districts = sorted(top_districts, key=lambda x: -x['count'])[:6]

    # Weekly trend per disease (last 8 weeks)
    diseases = Disease.objects.all()
    trend_labels = [f"W{i+1}" for i in range(8)]
    disease_trends = []
    COLORS = ['#E24B4A', '#EF9F27', '#378ADD', '#1D9E75', '#9B59B6', '#E67E22']
    for i, disease in enumerate(diseases[:6]):
        weekly = get_weekly_trend(disease=disease, weeks=8)
        disease_trends.append({
            'label': disease.name,
            'data': [w['count'] for w in weekly],
            'color': COLORS[i % len(COLORS)],
        })

    context = {
        'stats': stats,
        'recent_alerts': recent_alerts,
        'recent_cases': recent_cases,
        'top_districts': top_districts,
        'trend_labels_json': json.dumps(trend_labels),
        'disease_trends_json': json.dumps(disease_trends),
    }
    return render(request, 'surveillance/dashboard.html', context)


# ─── Case Reports ─────────────────────────────────────────────────────────────

@login_required
def case_list(request):
    form = CaseFilterForm(request.GET)
    qs = CaseReport.objects.select_related('disease', 'district', 'reported_by').order_by('-report_date')

    if form.is_valid():
        if form.cleaned_data.get('disease'):
            qs = qs.filter(disease=form.cleaned_data['disease'])
        if form.cleaned_data.get('district'):
            qs = qs.filter(district=form.cleaned_data['district'])
        if form.cleaned_data.get('date_from'):
            qs = qs.filter(report_date__gte=form.cleaned_data['date_from'])
        if form.cleaned_data.get('date_to'):
            qs = qs.filter(report_date__lte=form.cleaned_data['date_to'])
        if form.cleaned_data.get('status'):
            qs = qs.filter(status=form.cleaned_data['status'])

    return render(request, 'surveillance/case_list.html', {'cases': qs, 'filter_form': form})


@login_required
def case_create(request):
    if request.method == 'POST':
        form = CaseReportForm(request.POST)
        if form.is_valid():
            case = form.save(commit=False)
            case.reported_by = request.user
            case.save()
            # Auto-check alerts after new report
            new_alerts = check_and_fire_alerts()
            if new_alerts:
                messages.warning(request, f"⚠ {len(new_alerts)} new alert(s) triggered by this report.")
            messages.success(request, "Case report submitted successfully.")
            return redirect('case_list')
    else:
        form = CaseReportForm()
    return render(request, 'surveillance/case_form.html', {'form': form, 'title': 'Report New Case'})


@login_required
def case_edit(request, pk):
    case = get_object_or_404(CaseReport, pk=pk)
    if request.method == 'POST':
        form = CaseReportForm(request.POST, instance=case)
        if form.is_valid():
            form.save()
            messages.success(request, "Case report updated.")
            return redirect('case_list')
    else:
        form = CaseReportForm(instance=case)
    return render(request, 'surveillance/case_form.html', {'form': form, 'title': 'Edit Case Report', 'case': case})


@login_required
def case_delete(request, pk):
    case = get_object_or_404(CaseReport, pk=pk)
    if request.method == 'POST':
        case.delete()
        messages.success(request, "Case report deleted.")
        return redirect('case_list')
    return render(request, 'surveillance/case_confirm_delete.html', {'case': case})


# ─── Map ──────────────────────────────────────────────────────────────────────

@login_required
def map_view(request):
    return render(request, 'surveillance/map.html')


@login_required
def api_map_data(request):
    data = get_district_case_map()
    return JsonResponse({'districts': data})


# ─── Alerts ───────────────────────────────────────────────────────────────────

@login_required
def alert_list(request):
    alerts = Alert.objects.select_related('disease', 'district').order_by('-triggered_at')
    active = alerts.filter(status='active')
    resolved = alerts.filter(status__in=['acknowledged', 'resolved'])
    return render(request, 'surveillance/alert_list.html', {
        'active_alerts': active,
        'resolved_alerts': resolved,
    })


@login_required
def alert_acknowledge(request, pk):
    alert = get_object_or_404(Alert, pk=pk)
    if request.method == 'POST':
        alert.status = 'acknowledged'
        alert.acknowledged_by = request.user
        alert.acknowledged_at = timezone.now()
        alert.save()
        messages.success(request, f"Alert '{alert.title}' acknowledged.")
    return redirect('alert_list')


@login_required
def alert_resolve(request, pk):
    alert = get_object_or_404(Alert, pk=pk)
    if request.method == 'POST':
        alert.status = 'resolved'
        alert.resolved_at = timezone.now()
        alert.save()
        messages.success(request, f"Alert '{alert.title}' resolved.")
    return redirect('alert_list')


@login_required
def run_alert_check(request):
    """Manually trigger the alert engine."""
    if request.method == 'POST':
        new_alerts = check_and_fire_alerts()
        messages.success(request, f"Alert check complete. {len(new_alerts)} new alert(s) triggered.")
    return redirect('alert_list')


# ─── Thresholds ───────────────────────────────────────────────────────────────

@login_required
def threshold_list(request):
    thresholds = AlertThreshold.objects.select_related('disease', 'district').all()
    return render(request, 'surveillance/threshold_list.html', {'thresholds': thresholds})


@login_required
def threshold_create(request):
    if request.method == 'POST':
        form = AlertThresholdForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Threshold saved.")
            return redirect('threshold_list')
    else:
        form = AlertThresholdForm()
    return render(request, 'surveillance/threshold_form.html', {'form': form, 'title': 'Add Threshold'})


@login_required
def threshold_edit(request, pk):
    threshold = get_object_or_404(AlertThreshold, pk=pk)
    if request.method == 'POST':
        form = AlertThresholdForm(request.POST, instance=threshold)
        if form.is_valid():
            form.save()
            messages.success(request, "Threshold updated.")
            return redirect('threshold_list')
    else:
        form = AlertThresholdForm(instance=threshold)
    return render(request, 'surveillance/threshold_form.html', {'form': form, 'title': 'Edit Threshold'})


@login_required
def threshold_delete(request, pk):
    threshold = get_object_or_404(AlertThreshold, pk=pk)
    if request.method == 'POST':
        threshold.delete()
        messages.success(request, "Threshold deleted.")
        return redirect('threshold_list')
    return render(request, 'surveillance/threshold_confirm_delete.html', {'threshold': threshold})


# ─── API endpoints for charts ────────────────────────────────────────────────

@login_required
def api_trend(request):
    disease_id = request.GET.get('disease')
    disease = None
    if disease_id:
        disease = Disease.objects.filter(pk=disease_id).first()
    trend = get_weekly_trend(disease=disease, weeks=8)
    return JsonResponse({'trend': trend})


@login_required
def api_stats(request):
    return JsonResponse(get_dashboard_stats())
