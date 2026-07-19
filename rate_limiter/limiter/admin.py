from django.contrib import admin
from limiter.models import RouteLimit
# Register your models here.

@admin.register(RouteLimit)
class RouteLimitAdmin(admin.ModelAdmin):
    list_display = (
        "route",
        "capacity",
        "refill_rate",
        "algorithm",
        "enabled",
    )