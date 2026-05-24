from .models import Alert


def alert_count(request):
    """Injects active alert count into every template context."""
    if request.user.is_authenticated:
        count = Alert.objects.filter(status='active').count()
        return {'active_alert_count': count}
    return {'active_alert_count': 0}
