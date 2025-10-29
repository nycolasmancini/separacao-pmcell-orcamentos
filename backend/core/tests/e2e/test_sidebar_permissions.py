# -*- coding: utf-8 -*-
"""
Testes E2E para Permissões do Menu Sidebar.

Fase 40: Implementar Menu Hamburguer Moderno
TDD: RED → GREEN → REFACTOR

Testa visibilidade de itens do menu baseado em permissões de usuário.
"""

import pytest
from django.test import Client
from django.urls import reverse
from core.domain.usuario.entities import Usuario, TipoUsuario


@pytest.fixture
def client():
    """Cliente Django para testes."""
    return Client()


@pytest.fixture
def usuario_separador(db):
    """Cria usuário SEPARADOR para testes."""
    usuario = Usuario(
        numero_login=1001,
        nome="João Separador",
        senha="senha123",
        tipo=TipoUsuario.SEPARADOR
    )
    usuario.save()
    return usuario


@pytest.fixture
def usuario_compradora(db):
    """Cria usuário COMPRADORA para testes."""
    usuario = Usuario(
        numero_login=2001,
        nome="Maria Compradora",
        senha="senha123",
        tipo=TipoUsuario.COMPRADORA
    )
    usuario.save()
    return usuario


@pytest.fixture
def usuario_admin(db):
    """Cria usuário ADMINISTRADOR para testes."""
    usuario = Usuario(
        numero_login=3001,
        nome="Admin Sistema",
        senha="senha123",
        tipo=TipoUsuario.ADMINISTRADOR
    )
    usuario.save()
    return usuario


@pytest.mark.django_db
class TestSidebarPermissoesSeparador:
    """Testes para permissões do SEPARADOR no menu."""

    def test_separador_ve_dashboard(self, client, usuario_separador):
        """SEPARADOR deve ver link Dashboard."""
        client.force_login(usuario_separador)
        response = client.get(reverse('dashboard'))
        content = response.content.decode('utf-8')

        assert 'Dashboard' in content, "SEPARADOR deve ver Dashboard"

    def test_separador_ve_novo_pedido(self, client, usuario_separador):
        """SEPARADOR deve ver link Novo Pedido."""
        client.force_login(usuario_separador)
        response = client.get(reverse('dashboard'))
        content = response.content.decode('utf-8')

        assert 'Novo Pedido' in content or 'Upload' in content, \
            "SEPARADOR deve ver Novo Pedido"

    def test_separador_ve_historico(self, client, usuario_separador):
        """SEPARADOR deve ver link Histórico."""
        client.force_login(usuario_separador)
        response = client.get(reverse('dashboard'))
        content = response.content.decode('utf-8')

        assert 'Histórico' in content or 'Historico' in content, \
            "SEPARADOR deve ver Histórico"

    def test_separador_ve_metricas(self, client, usuario_separador):
        """SEPARADOR deve ver link Métricas."""
        client.force_login(usuario_separador)
        response = client.get(reverse('dashboard'))
        content = response.content.decode('utf-8')

        assert 'Métricas' in content or 'Metricas' in content, \
            "SEPARADOR deve ver Métricas"

    def test_separador_nao_ve_painel_compras(self, client, usuario_separador):
        """SEPARADOR NÃO deve ver link Painel de Compras."""
        client.force_login(usuario_separador)
        response = client.get(reverse('dashboard'))
        content = response.content.decode('utf-8')

        # Não deve ter link explícito para compras no menu
        # (pode ter a palavra "compra" em outros contextos)
        compras_count = content.lower().count('painel de compras')
        assert compras_count == 0, \
            "SEPARADOR não deve ver 'Painel de Compras' no menu"

    def test_separador_nao_ve_admin_panel(self, client, usuario_separador):
        """SEPARADOR NÃO deve ver link Admin Panel."""
        client.force_login(usuario_separador)
        response = client.get(reverse('dashboard'))
        content = response.content.decode('utf-8')

        # Não deve ter acesso ao painel admin
        assert 'Admin Panel' not in content and 'Gerenciar Usuários' not in content, \
            "SEPARADOR não deve ver Admin Panel"


@pytest.mark.django_db
class TestSidebarPermissoesCompradora:
    """Testes para permissões da COMPRADORA no menu."""

    def test_compradora_ve_dashboard(self, client, usuario_compradora):
        """COMPRADORA deve ver link Dashboard."""
        client.force_login(usuario_compradora)
        response = client.get(reverse('dashboard'))
        content = response.content.decode('utf-8')

        assert 'Dashboard' in content, "COMPRADORA deve ver Dashboard"

    def test_compradora_ve_novo_pedido(self, client, usuario_compradora):
        """COMPRADORA deve ver link Novo Pedido."""
        client.force_login(usuario_compradora)
        response = client.get(reverse('dashboard'))
        content = response.content.decode('utf-8')

        assert 'Novo Pedido' in content or 'Upload' in content, \
            "COMPRADORA deve ver Novo Pedido"

    def test_compradora_ve_historico(self, client, usuario_compradora):
        """COMPRADORA deve ver link Histórico."""
        client.force_login(usuario_compradora)
        response = client.get(reverse('dashboard'))
        content = response.content.decode('utf-8')

        assert 'Histórico' in content or 'Historico' in content, \
            "COMPRADORA deve ver Histórico"

    def test_compradora_ve_metricas(self, client, usuario_compradora):
        """COMPRADORA deve ver link Métricas."""
        client.force_login(usuario_compradora)
        response = client.get(reverse('dashboard'))
        content = response.content.decode('utf-8')

        assert 'Métricas' in content or 'Metricas' in content, \
            "COMPRADORA deve ver Métricas"

    def test_compradora_ve_painel_compras(self, client, usuario_compradora):
        """COMPRADORA deve ver link Painel de Compras."""
        client.force_login(usuario_compradora)
        response = client.get(reverse('dashboard'))
        content = response.content.decode('utf-8')

        assert 'Painel de Compras' in content or 'Compras' in content, \
            "COMPRADORA deve ver Painel de Compras"

    def test_compradora_nao_ve_admin_panel(self, client, usuario_compradora):
        """COMPRADORA NÃO deve ver link Admin Panel."""
        client.force_login(usuario_compradora)
        response = client.get(reverse('dashboard'))
        content = response.content.decode('utf-8')

        # Não deve ter acesso ao painel admin
        assert 'Admin Panel' not in content and 'Gerenciar Usuários' not in content, \
            "COMPRADORA não deve ver Admin Panel"


@pytest.mark.django_db
class TestSidebarPermissoesAdmin:
    """Testes para permissões do ADMINISTRADOR no menu."""

    def test_admin_ve_dashboard(self, client, usuario_admin):
        """ADMINISTRADOR deve ver link Dashboard."""
        client.force_login(usuario_admin)
        response = client.get(reverse('dashboard'))
        content = response.content.decode('utf-8')

        assert 'Dashboard' in content, "ADMIN deve ver Dashboard"

    def test_admin_ve_novo_pedido(self, client, usuario_admin):
        """ADMINISTRADOR deve ver link Novo Pedido."""
        client.force_login(usuario_admin)
        response = client.get(reverse('dashboard'))
        content = response.content.decode('utf-8')

        assert 'Novo Pedido' in content or 'Upload' in content, \
            "ADMIN deve ver Novo Pedido"

    def test_admin_ve_historico(self, client, usuario_admin):
        """ADMINISTRADOR deve ver link Histórico."""
        client.force_login(usuario_admin)
        response = client.get(reverse('dashboard'))
        content = response.content.decode('utf-8')

        assert 'Histórico' in content or 'Historico' in content, \
            "ADMIN deve ver Histórico"

    def test_admin_ve_metricas(self, client, usuario_admin):
        """ADMINISTRADOR deve ver link Métricas."""
        client.force_login(usuario_admin)
        response = client.get(reverse('dashboard'))
        content = response.content.decode('utf-8')

        assert 'Métricas' in content or 'Metricas' in content, \
            "ADMIN deve ver Métricas"

    def test_admin_ve_painel_compras(self, client, usuario_admin):
        """ADMINISTRADOR deve ver link Painel de Compras."""
        client.force_login(usuario_admin)
        response = client.get(reverse('dashboard'))
        content = response.content.decode('utf-8')

        assert 'Painel de Compras' in content or 'Compras' in content, \
            "ADMIN deve ver Painel de Compras"

    def test_admin_ve_admin_panel(self, client, usuario_admin):
        """ADMINISTRADOR deve ver link Admin Panel."""
        client.force_login(usuario_admin)
        response = client.get(reverse('dashboard'))
        content = response.content.decode('utf-8')

        assert 'Admin Panel' in content or 'Gerenciar Usuários' in content or 'Usuários' in content, \
            "ADMIN deve ver Admin Panel"

    def test_admin_ve_criar_usuario_no_submenu(self, client, usuario_admin):
        """ADMINISTRADOR deve ver 'Criar Usuário' como submenu de Admin."""
        client.force_login(usuario_admin)
        response = client.get(reverse('dashboard'))
        content = response.content.decode('utf-8')

        # Deve ter link ou referência a criar usuário
        assert 'Criar Usuário' in content or 'Criar Usuario' in content or 'criar_usuario' in content, \
            "ADMIN deve ter acesso a Criar Usuário"


@pytest.mark.django_db
class TestSidebarPermissoesLinks:
    """Testes para URLs corretas dos links do menu."""

    def test_link_dashboard_correto(self, client, usuario_separador):
        """Link Dashboard deve apontar para URL correta."""
        client.force_login(usuario_separador)
        response = client.get(reverse('dashboard'))
        content = response.content.decode('utf-8')

        dashboard_url = reverse('dashboard')
        assert f'href="{dashboard_url}"' in content or f"href='{dashboard_url}'" in content, \
            "Link Dashboard deve ter URL correta"

    def test_link_historico_correto(self, client, usuario_separador):
        """Link Histórico deve apontar para URL correta."""
        client.force_login(usuario_separador)
        response = client.get(reverse('dashboard'))
        content = response.content.decode('utf-8')

        historico_url = reverse('historico')
        assert f'href="{historico_url}"' in content or f"href='{historico_url}'" in content, \
            "Link Histórico deve ter URL correta"

    def test_link_metricas_correto(self, client, usuario_separador):
        """Link Métricas deve apontar para URL correta."""
        client.force_login(usuario_separador)
        response = client.get(reverse('dashboard'))
        content = response.content.decode('utf-8')

        metricas_url = reverse('metricas')
        assert f'href="{metricas_url}"' in content or f"href='{metricas_url}'" in content, \
            "Link Métricas deve ter URL correta"

    def test_link_compras_correto_para_compradora(self, client, usuario_compradora):
        """Link Painel de Compras deve apontar para URL correta."""
        client.force_login(usuario_compradora)
        response = client.get(reverse('dashboard'))
        content = response.content.decode('utf-8')

        compras_url = reverse('painel_compras')
        assert f'href="{compras_url}"' in content or f"href='{compras_url}'" in content, \
            "Link Painel de Compras deve ter URL correta"

    def test_link_admin_correto_para_admin(self, client, usuario_admin):
        """Link Admin Panel deve apontar para URL correta."""
        client.force_login(usuario_admin)
        response = client.get(reverse('dashboard'))
        content = response.content.decode('utf-8')

        admin_url = reverse('admin_panel')
        assert f'href="{admin_url}"' in content or f"href='{admin_url}'" in content, \
            "Link Admin Panel deve ter URL correta"
