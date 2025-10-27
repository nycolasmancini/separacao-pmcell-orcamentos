# -*- coding: utf-8 -*-
"""
Middleware de autenticação customizado para o sistema de separação de pedidos.
Fase 8: Gestão de sessões com timeout de 8 horas.
"""

import logging
from django.shortcuts import redirect
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta

logger = logging.getLogger(__name__)


class SessionTimeoutMiddleware:
    """
    Middleware que gerencia timeout de sessão (8 horas) e atualiza timestamp de atividade.

    Funcionalidades:
    - Verifica se sessão expirou (8h de inatividade)
    - Atualiza timestamp de última atividade em cada request
    - Redireciona para login se sessão expirada
    - Permite acesso à página de login sem autenticação
    """

    # Constantes
    TIMEOUT_HOURS = 8
    LOGIN_URL = '/login/'
    PUBLIC_URLS = ['/login/', '/admin/']  # URLs acessíveis sem autenticação

    def __init__(self, get_response):
        """
        Inicializa o middleware.

        Args:
            get_response: Callable que retorna a response
        """
        self.get_response = get_response

    def __call__(self, request):
        """
        Processa cada request.

        Args:
            request: HttpRequest do Django

        Returns:
            HttpResponse
        """
        # Permitir acesso a URLs públicas
        if self._is_public_url(request.path):
            return self.get_response(request)

        # Verificar se usuário está autenticado
        if not request.user.is_authenticated:
            logger.info(f"Usuário não autenticado tentou acessar: {request.path}")
            return redirect(self.LOGIN_URL)

        # Verificar timeout de sessão
        if self._session_expired(request):
            # Limpar sessão
            logger.warning(
                f"Sessão expirada para usuário {request.user.numero_login}. "
                f"Última atividade: {request.session.get('last_activity')}"
            )
            request.session.flush()
            return redirect(self.LOGIN_URL)

        # Atualizar timestamp de última atividade
        self._update_last_activity(request)

        return self.get_response(request)

    def _is_public_url(self, path):
        """
        Verifica se URL é pública (não requer autenticação).

        Args:
            path: Caminho da URL

        Returns:
            bool: True se URL é pública
        """
        return any(path.startswith(public_url) for public_url in self.PUBLIC_URLS)

    def _session_expired(self, request):
        """
        Verifica se sessão expirou (8h de inatividade).

        Args:
            request: HttpRequest do Django

        Returns:
            bool: True se sessão expirou
        """
        last_activity_str = request.session.get('last_activity')

        if not last_activity_str:
            # Primeira atividade, definir timestamp
            self._update_last_activity(request)
            return False

        # Converter string ISO para datetime
        last_activity = timezone.datetime.fromisoformat(last_activity_str)

        # Calcular tempo decorrido
        time_elapsed = timezone.now() - last_activity
        timeout = timedelta(hours=self.TIMEOUT_HOURS)

        return time_elapsed > timeout

    def _update_last_activity(self, request):
        """
        Atualiza timestamp de última atividade na sessão.

        Args:
            request: HttpRequest do Django
        """
        request.session['last_activity'] = timezone.now().isoformat()
