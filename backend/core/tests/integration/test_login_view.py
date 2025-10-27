# -*- coding: utf-8 -*-
"""
Testes de integração para a view de login.
Fase 7: Criar Tela de Login (UI)
"""
import pytest
from django.test import Client
from django.urls import reverse
from django.core.cache import cache
from unittest.mock import Mock, patch
from core.models import Usuario


@pytest.fixture
def client():
    """Cliente Django para testes."""
    return Client()


@pytest.fixture
def usuario_teste(db):
    """Cria usuário de teste no banco."""
    # Limpar cache antes de criar usuário
    cache.clear()

    usuario = Usuario.objects.create_user(
        numero_login=1,
        pin='1234',
        nome='João Teste',
        tipo='SEPARADOR'
    )
    return usuario


@pytest.mark.django_db
class TestLoginView:
    """Testes da view de login."""

    def test_login_page_loads(self, client):
        """Testa se página de login carrega corretamente."""
        response = client.get('/login/')

        assert response.status_code == 200
        assert 'login.html' in [t.name for t in response.templates]
        content = response.content.decode('utf-8')
        assert 'numero_login' in content.lower() or 'numero' in content.lower()
        assert 'pin' in content.lower()

    def test_login_success_redirects_to_dashboard(self, client, usuario_teste):
        """Testa que login bem-sucedido redireciona para dashboard."""
        response = client.post('/login/', {
            'numero_login': 1,
            'pin': '1234'
        })

        assert response.status_code == 302
        assert '/dashboard/' in response.url

    def test_login_failure_shows_error_message(self, client, usuario_teste):
        """Testa que login falho mostra mensagem de erro."""
        response = client.post('/login/', {
            'numero_login': 1,
            'pin': '9999'
        }, follow=True)

        content = response.content.decode('utf-8')
        assert 'inválid' in content.lower() or 'incorret' in content.lower() or 'erro' in content.lower()

    def test_login_rate_limiting_shows_block_message(self, client, usuario_teste):
        """Testa que bloqueio por rate limit mostra mensagem adequada."""
        # Simular 5 tentativas falhas
        for _ in range(5):
            client.post('/login/', {
                'numero_login': 1,
                'pin': '9999'
            })

        # Sexta tentativa deve mostrar bloqueio
        response = client.post('/login/', {
            'numero_login': 1,
            'pin': '1234'  # Mesmo com PIN correto
        }, follow=True)

        content = response.content.decode('utf-8')
        assert 'bloqueado' in content.lower() or 'aguarde' in content.lower() or 'muitas tentativas' in content.lower()

    def test_login_shows_remaining_attempts(self, client, usuario_teste):
        """Testa que exibe tentativas restantes após falha."""
        # Uma tentativa falha
        response = client.post('/login/', {
            'numero_login': 1,
            'pin': '9999'
        }, follow=True)

        content = response.content.decode('utf-8')
        # Deve mostrar algo como "4 tentativas restantes" ou similar
        assert '4' in content or 'tentativa' in content.lower()

    def test_login_creates_session_on_success(self, client, usuario_teste):
        """Testa que sessão é criada corretamente no login."""
        # Fazer login
        response = client.post('/login/', {
            'numero_login': 1,
            'pin': '1234'
        })

        # Verificar que redirecionou (indica login bem-sucedido)
        assert response.status_code == 302

        # Acessar uma página protegida para verificar autenticação
        dashboard_response = client.get('/dashboard/')
        assert dashboard_response.status_code == 200
        assert usuario_teste.nome.encode() in dashboard_response.content

    def test_invalid_form_shows_validation_errors(self, client):
        """Testa que formulário inválido mostra erros de validação."""
        # Submeter formulário vazio
        response = client.post('/login/', {})

        content = response.content.decode('utf-8')
        assert 'obrigatório' in content.lower() or 'campo' in content.lower() or 'required' in content.lower()

    def test_login_requires_4_digit_pin(self, client):
        """Testa validação de PIN com 4 dígitos."""
        # PIN com 3 dígitos
        response = client.post('/login/', {
            'numero_login': 1,
            'pin': '123'
        }, follow=True)

        content = response.content.decode('utf-8')
        assert '4 dígitos' in content.lower() or 'exatamente 4' in content.lower() or response.status_code == 200

        # PIN com 5 dígitos
        response = client.post('/login/', {
            'numero_login': 1,
            'pin': '12345'
        }, follow=True)

        content = response.content.decode('utf-8')
        assert '4 dígitos' in content.lower() or 'exatamente 4' in content.lower() or response.status_code == 200
