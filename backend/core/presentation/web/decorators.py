# -*- coding: utf-8 -*-
"""
Decorators para views do sistema de separação de pedidos.
Fase 8: Decorator @login_required customizado.
"""

from functools import wraps
from django.shortcuts import redirect


def login_required(view_func):
    """
    Decorator que verifica se usuário está autenticado antes de executar view.

    Se usuário não estiver autenticado, redireciona para página de login.
    O middleware SessionTimeoutMiddleware já cuida da verificação de timeout.

    Args:
        view_func: Função da view a ser decorada

    Returns:
        Função decorada

    Example:
        @login_required
        def dashboard_view(request):
            return render(request, 'dashboard.html')
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('/login/')
        return view_func(request, *args, **kwargs)
    return wrapper
