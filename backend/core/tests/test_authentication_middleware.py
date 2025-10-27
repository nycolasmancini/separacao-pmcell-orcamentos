# -*- coding: utf-8 -*-
"""
Testes para middleware de autenticação e gestão de sessões - Fase 8.

Testa:
- Redirecionamento de usuários não autenticados
- Acesso de usuários autenticados
- Expiração de sessão após 8 horas
- Atualização de timestamp de atividade
- Logout e limpeza de sessão
- Acessibilidade da página de login
"""

import pytest
from django.test import Client
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta
from core.models import Usuario


@pytest.fixture
def client():
    """Client de teste Django."""
    return Client()


@pytest.fixture
def usuario_teste():
    """Cria usuário de teste."""
    usuario = Usuario.objects.create_user(
        numero_login=1,
        pin='1234',
        nome='João Teste',
        tipo='SEPARADOR'
    )
    return usuario


@pytest.fixture
def logged_in_client(client, usuario_teste):
    """Client com usuário autenticado."""
    client.post(reverse('login'), {
        'numero_login': 1,
        'pin': '1234'
    })
    return client


@pytest.mark.django_db
class TestAuthenticationMiddleware:
    """Testes do middleware de autenticação."""

    def test_unauthenticated_user_redirected_to_login(self, client):
        """Testa que usuário não autenticado é redirecionado para login."""
        response = client.get(reverse('dashboard'))

        assert response.status_code == 302
        assert '/login/' in response.url

    def test_authenticated_user_can_access_dashboard(self, logged_in_client):
        """Testa que usuário autenticado pode acessar dashboard."""
        response = logged_in_client.get(reverse('dashboard'))

        assert response.status_code == 200

    def test_session_expires_after_8_hours(self, client, usuario_teste):
        """Testa que sessão expira após 8h de inatividade."""
        # Login inicial
        client.post(reverse('login'), {
            'numero_login': 1,
            'pin': '1234'
        })

        # Simular passagem de 8h + 1 minuto
        session = client.session
        session['last_activity'] = (timezone.now() - timedelta(hours=8, minutes=1)).isoformat()
        session.save()

        # Tentar acessar dashboard
        response = client.get(reverse('dashboard'))

        # Deve redirecionar para login (sessão expirada)
        assert response.status_code == 302
        assert '/login/' in response.url

    def test_session_not_expired_within_8_hours(self, client, usuario_teste):
        """Testa que sessão válida dentro de 8h permite acesso."""
        # Login inicial
        client.post(reverse('login'), {
            'numero_login': 1,
            'pin': '1234'
        })

        # Simular passagem de 7h59min (ainda válida)
        session = client.session
        session['last_activity'] = (timezone.now() - timedelta(hours=7, minutes=59)).isoformat()
        session.save()

        # Tentar acessar dashboard
        response = client.get(reverse('dashboard'))

        # Deve permitir acesso
        assert response.status_code == 200

    def test_session_updates_last_activity_on_request(self, client, usuario_teste):
        """Testa que cada request atualiza timestamp de última atividade."""
        # Login inicial
        client.post(reverse('login'), {
            'numero_login': 1,
            'pin': '1234'
        })

        # Pegar timestamp inicial
        initial_activity = client.session.get('last_activity')

        # Fazer uma requisição
        import time
        time.sleep(1)  # Garantir que timestamp será diferente
        client.get(reverse('dashboard'))

        # Verificar que timestamp foi atualizado
        updated_activity = client.session.get('last_activity')

        assert updated_activity is not None
        assert updated_activity != initial_activity

    def test_logout_clears_session(self, logged_in_client, usuario_teste):
        """Testa que logout limpa a sessão."""
        # Verificar que usuário está autenticado
        assert logged_in_client.session.get('_auth_user_id') is not None

        # Fazer logout
        logged_in_client.post(reverse('logout'))

        # Verificar que sessão foi limpa
        assert logged_in_client.session.get('_auth_user_id') is None

    def test_logout_redirects_to_login(self, logged_in_client):
        """Testa que logout redireciona para página de login."""
        response = logged_in_client.post(reverse('logout'))

        assert response.status_code == 302
        assert '/login/' in response.url

    def test_login_page_accessible_without_auth(self, client):
        """Testa que página de login é acessível sem autenticação."""
        response = client.get(reverse('login'))

        assert response.status_code == 200
        assert 'login.html' in [t.name for t in response.templates]
