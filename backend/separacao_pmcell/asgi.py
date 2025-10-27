# -*- coding: utf-8 -*-
"""
ASGI config for separacao_pmcell project.
"""

import os

from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'separacao_pmcell.settings')

application = get_asgi_application()
