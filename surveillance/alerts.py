from django.utils import timezone
from datetime import timedelta
from .models import CaseReport, AlertThreshold, Alert, District, Disease


def check_and_fire_alerts():
    """
    Runs through all active thresholds, counts cases in the past 7 days,
    and creates Alert records when thresholds are exceeded.
    Returns list of newly created alerts.
    """
    new_alerts = []
    week_ago = timezone.now().date() - timedelta(days=7)
    thresholds = AlertThreshold.objects.filter(is_active=True).select_related('disease', 'district')

    for threshold in thresholds:
        qs = CaseReport.objects.filter(
            disease=threshold.disease,
            report_date__gte=week_ago,
        )
        if threshold.district:
            qs = qs.filter(district=threshold.district)

        total_cases = sum(r.case_count for r in qs)

        if total_cases >= threshold.cases_per_week:
            # Determine districts to alert
            if threshold.district:
                districts = [threshold.district]
            else:
                districts = District.objects.filter(
                    cases__disease=threshold.disease,
                    cases__report_date__gte=week_ago
                ).distinct()

            for district in districts:
                district_cases = sum(
                    r.case_count for r in CaseReport.objects.filter(
                        disease=threshold.disease,
                        district=district,
                        report_date__gte=week_ago,
                    )
                )
                if district_cases == 0:
                    continue

                # Avoid duplicate active alerts
                existing = Alert.objects.filter(
                    disease=threshold.disease,
                    district=district,
                    status='active',
                    triggered_at__date=timezone.now().date()
                ).exists()
                if existing:
                    continue

                ratio = district_cases / threshold.cases_per_week
                level = 'info' if ratio < 1.5 else ('warning' if ratio < 2.5 else 'critical')

                alert = Alert.objects.create(
                    disease=threshold.disease,
                    district=district,
                    level=level,
                    title=f"{threshold.disease.name} outbreak — {district.name}",
                    message=(
                        f"{district_cases} case(s) of {threshold.disease.name} reported in "
                        f"{district.name} in the past 7 days, exceeding the threshold of "
                        f"{threshold.cases_per_week} cases/week."
                    ),
                    case_count=district_cases,
                    threshold=threshold.cases_per_week,
                )
                new_alerts.append(alert)

    return new_alerts


def get_dashboard_stats():
    """Returns aggregate stats for the dashboard."""
    week_ago = timezone.now().date() - timedelta(days=7)
    month_ago = timezone.now().date() - timedelta(days=30)

    total_cases_week = sum(
        r.case_count for r in CaseReport.objects.filter(report_date__gte=week_ago)
    )
    total_cases_month = sum(
        r.case_count for r in CaseReport.objects.filter(report_date__gte=month_ago)
    )
    active_outbreaks = Alert.objects.filter(status='active', level__in=['warning', 'critical']).count()
    districts_affected = CaseReport.objects.filter(
        report_date__gte=week_ago
    ).values('district').distinct().count()
    recovered = sum(
        r.case_count for r in CaseReport.objects.filter(status='recovered', report_date__gte=month_ago)
    )

    return {
        'total_cases_week': total_cases_week,
        'total_cases_month': total_cases_month,
        'active_outbreaks': active_outbreaks,
        'districts_affected': districts_affected,
        'recovered_month': recovered,
    }


def get_weekly_trend(disease=None, weeks=8):
    """Returns weekly case counts for the past N weeks."""
    today = timezone.now().date()
    result = []
    for i in range(weeks - 1, -1, -1):
        start = today - timedelta(days=(i + 1) * 7)
        end = today - timedelta(days=i * 7)
        qs = CaseReport.objects.filter(report_date__gte=start, report_date__lt=end)
        if disease:
            qs = qs.filter(disease=disease)
        count = sum(r.case_count for r in qs)
        result.append({
            'week': f"W{weeks - i}",
            'start': start.strftime('%d %b'),
            'end': end.strftime('%d %b'),
            'count': count,
        })
    return result


def get_district_case_map():
    """Returns case counts + coords per district for the map."""
    week_ago = timezone.now().date() - timedelta(days=7)
    districts = District.objects.prefetch_related('cases', 'alerts').all()
    result = []
    for d in districts:
        week_cases = sum(
            r.case_count for r in d.cases.filter(report_date__gte=week_ago)
        )
        if week_cases == 0:
            continue
        active_alert = d.alerts.filter(status='active').order_by('-triggered_at').first()
        result.append({
            'id': d.id,
            'name': d.name,
            'province': d.province.name,
            'lat': float(d.latitude),
            'lng': float(d.longitude),
            'cases': week_cases,
            'level': active_alert.level if active_alert else 'info',
        })
    return result
