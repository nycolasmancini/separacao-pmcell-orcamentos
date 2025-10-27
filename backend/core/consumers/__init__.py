# -*- coding: utf-8 -*-
"""
Consumers package - Django Channels
Fase 29: WebSocket consumers para atualização em tempo real
"""

from .dashboard_consumer import DashboardConsumer

__all__ = ['DashboardConsumer']
