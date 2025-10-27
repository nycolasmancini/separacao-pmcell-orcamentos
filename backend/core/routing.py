# -*- coding: utf-8 -*-
"""
WebSocket URL routing
Fase 29: Configurar Django Channels e WebSockets

Define os padrões de URL para conexões WebSocket.
Similar ao urls.py, mas para WebSockets.
"""

from django.urls import re_path
from core.consumers import DashboardConsumer

# WebSocket URL patterns
websocket_urlpatterns = [
    re_path(r'ws/dashboard/$', DashboardConsumer.as_asgi()),
]
