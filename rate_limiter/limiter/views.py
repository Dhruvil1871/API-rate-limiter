import json
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from limiter.services.stats import rate_limit_stats
from limiter.services.events import event_manager
from limiter.config import RATE_LIMITER, RATE_LIMITS
from .models import RouteLimit

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

def config_view(request):
    routes = {}

    for limit in RouteLimit.objects.all():
        routes[limit.route] = {
            "capacity" : limit.capacity,
            "refill_rate" : limit.refill_rate,
            "algorithm" : limit.algorithm,
            "enabled" : limit.enabled,
        }
    
    return JsonResponse({"routes" : routes})

@require_POST
def update_config_view(request):
    try:
        data = json.loads(request.body)

        route = data["route"]

        config = RouteLimit.objects.get(route = route)

        config.capacity = int(data["capacity"])
        config.refill_rate = float(data["refill_rate"])
        config.save()

        return JsonResponse({"success" : True})
    
    except RouteLimit.DoesNotExist:
        return JsonResponse({
            "success" : False,
            "error" : "Route not found"
        },status = 404)
    
    except Exception as e:
        return JsonResponse({
            "success" : False,
            "error" : str(e)
        },status = 400)