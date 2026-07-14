from django.urls import path
from .views import stats_view, health_view, event_view

urlpatterns = [
    path("stats/", stats_view),
    path("health/", health_view),
    path("events/", event_view),
]