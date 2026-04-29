from django.urls import re_path
from .consumers import TriageEventsConsumer

websocket_urlpatterns = [
    re_path(r"ws/triage/events/$", TriageEventsConsumer.as_asgi()),
]
