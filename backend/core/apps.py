# -*- coding: utf-8 -*-
"""
Django app configuration for core.
"""
from django.apps import AppConfig


class CoreConfig(AppConfig):
    """Configuração do app core."""

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'core'
    verbose_name = 'Separação de Pedidos PMCELL'
