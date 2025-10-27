# -*- coding: utf-8 -*-
"""
ASGI config for separacao_pmcell project.
Fase 29: Configuração com Django Channels para WebSockets
"""

import os

from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.security.websocket import AllowedHostsOriginValidator
from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'separacao_pmcell.settings')

# Initialize Django ASGI application early to ensure the AppRegistry
# is populated before importing code that may import ORM models.
django_asgi_app = get_asgi_application()

# Import routing após inicializar Django
from core.routing import websocket_urlpatterns

application = ProtocolTypeRouter({
    # Django's ASGI application para HTTP
    "http": django_asgi_app,

    # WebSocket chat handler
    "websocket": AllowedHostsOriginValidator(
        AuthMiddlewareStack(
            URLRouter(
                websocket_urlpatterns
            )
        )
    ),
})
