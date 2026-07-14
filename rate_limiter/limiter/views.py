from django.shortcuts import render
from django.http import JsonResponse
from limiter.services.stats import rate_limit_stats
from limiter.services.events import event_manager
from limiter.config import RATE_LIMITER

# Create your views here.
def stats_view(request):
    return JsonResponse(rate_limit_stats.to_dict())

def health_view(request):
    if rate_limit_stats.redis_available:
        status = "healthy"
    else:
        status = "degraded"

    return JsonResponse({
        "status" : status,
        "redis_available" : rate_limit_stats.redis_available,
        "fallback_active" : rate_limit_stats.fallback_active,
        "active_limiter" : rate_limit_stats.active_limiter,
        "algorithm" : RATE_LIMITER.upper(),
    })

def event_view(request):
    return JsonResponse({
        "events" : event_manager.get_events()
    })

def dashboard_view(request):
    return render(request, "limiter/dashboard.html")