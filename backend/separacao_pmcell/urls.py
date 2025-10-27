# -*- coding: utf-8 -*-
"""
URL configuration for separacao_pmcell project.
"""
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('core.urls')),  # URLs do core app
]
