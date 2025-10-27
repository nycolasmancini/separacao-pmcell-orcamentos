# -*- coding: utf-8 -*-
"""
WSGI config for separacao_pmcell project.
"""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'separacao_pmcell.settings')

application = get_wsgi_application()
