# -*- coding: utf-8 -*-
"""
Testes E2E para Menu Hamburguer (Sidebar).

Fase 40: Implementar Menu Hamburguer Moderno
TDD: RED → GREEN → REFACTOR

Testa estrutura, responsividade e comportamento do menu lateral.
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
class TestSidebarMenuEstrutura:
    """Testes para estrutura do menu sidebar."""

    def test_sidebar_existe_no_dashboard(self, client, usuario_separador):
        """Testa se sidebar é renderizada no dashboard."""
        # Login
        client.force_login(usuario_separador)

        # Acessa dashboard
        response = client.get(reverse('dashboard'))

        # Verifica status
        assert response.status_code == 200

        # Verifica se sidebar existe
        content = response.content.decode('utf-8')
        assert 'data-sidebar' in content or 'id="sidebar"' in content, \
            "Sidebar deve existir no dashboard"

    def test_botao_hamburguer_existe(self, client, usuario_separador):
        """Testa se botão hamburguer é renderizado."""
        client.force_login(usuario_separador)
        response = client.get(reverse('dashboard'))
        content = response.content.decode('utf-8')

        # Verifica botão hamburguer (ícone de 3 barras)
        assert 'hamburger-button' in content or 'menu-toggle' in content, \
            "Botão hamburguer deve existir"

    def test_sidebar_contem_logo_ou_titulo(self, client, usuario_separador):
        """Testa se sidebar contém logo ou título do sistema."""
        client.force_login(usuario_separador)
        response = client.get(reverse('dashboard'))
        content = response.content.decode('utf-8')

        # Deve conter nome do sistema
        assert 'PMCELL' in content or 'Separação' in content, \
            "Sidebar deve conter identificação do sistema"

    def test_sidebar_tem_navegacao_principal(self, client, usuario_separador):
        """Testa se sidebar contém elementos de navegação."""
        client.force_login(usuario_separador)
        response = client.get(reverse('dashboard'))
        content = response.content.decode('utf-8')

        # Verifica links de navegação básicos
        assert 'Dashboard' in content, "Deve ter link Dashboard"
        assert 'Histórico' in content or 'Historico' in content, "Deve ter link Histórico"
        assert 'Métricas' in content or 'Metricas' in content, "Deve ter link Métricas"

    def test_sidebar_tem_classes_responsivas(self, client, usuario_separador):
        """Testa se sidebar tem classes CSS responsivas."""
        client.force_login(usuario_separador)
        response = client.get(reverse('dashboard'))
        content = response.content.decode('utf-8')

        # Verifica classes Tailwind para responsividade
        # Desktop: lg:block, lg:w-64, etc
        # Mobile: hidden, -translate-x-full, etc
        assert 'lg:' in content or 'md:' in content, \
            "Sidebar deve ter classes responsivas (Tailwind)"


@pytest.mark.django_db
class TestSidebarMenuAnimacoes:
    """Testes para animações do menu sidebar."""

    def test_sidebar_tem_transicoes_css(self, client, usuario_separador):
        """Testa se sidebar possui classes de transição CSS."""
        client.force_login(usuario_separador)
        response = client.get(reverse('dashboard'))
        content = response.content.decode('utf-8')

        # Verifica classes de transição
        assert 'transition' in content, "Sidebar deve ter transições CSS"

    def test_sidebar_tem_estado_aberto_fechado(self, client, usuario_separador):
        """Testa se sidebar tem indicadores de estado (aberto/fechado)."""
        client.force_login(usuario_separador)
        response = client.get(reverse('dashboard'))
        content = response.content.decode('utf-8')

        # Alpine.js data para controle de estado
        assert 'x-data' in content or 'sidebarOpen' in content, \
            "Sidebar deve ter controle de estado (Alpine.js)"

    def test_overlay_backdrop_existe(self, client, usuario_separador):
        """Testa se existe backdrop/overlay para mobile."""
        client.force_login(usuario_separador)
        response = client.get(reverse('dashboard'))
        content = response.content.decode('utf-8')

        # Verifica backdrop para fechar menu em mobile
        assert 'backdrop' in content or 'overlay' in content or 'bg-black' in content, \
            "Deve existir backdrop/overlay para mobile"


@pytest.mark.django_db
class TestSidebarMenuIcones:
    """Testes para ícones do menu sidebar."""

    def test_menu_items_tem_icones_svg(self, client, usuario_separador):
        """Testa se items do menu possuem ícones SVG."""
        client.force_login(usuario_separador)
        response = client.get(reverse('dashboard'))
        content = response.content.decode('utf-8')

        # Verifica presença de SVG icons (Heroicons)
        svg_count = content.count('<svg')
        assert svg_count >= 5, \
            f"Deve ter pelo menos 5 ícones SVG no menu (encontrou {svg_count})"

    def test_icones_tem_viewbox_correto(self, client, usuario_separador):
        """Testa se ícones SVG têm viewBox configurado."""
        client.force_login(usuario_separador)
        response = client.get(reverse('dashboard'))
        content = response.content.decode('utf-8')

        # Verifica viewBox padrão do Heroicons
        assert 'viewBox="0 0 24 24"' in content, \
            "Ícones devem ter viewBox correto (Heroicons)"


@pytest.mark.django_db
class TestSidebarMenuAcessibilidade:
    """Testes para acessibilidade do menu sidebar."""

    def test_botao_hamburguer_tem_aria_label(self, client, usuario_separador):
        """Testa se botão hamburguer tem aria-label."""
        client.force_login(usuario_separador)
        response = client.get(reverse('dashboard'))
        content = response.content.decode('utf-8')

        # Verifica aria-label ou aria-labelledby
        assert 'aria-label' in content or 'aria-labelledby' in content, \
            "Botão hamburguer deve ter aria-label para acessibilidade"

    def test_links_navegacao_tem_texto(self, client, usuario_separador):
        """Testa se links de navegação têm texto descritivo."""
        client.force_login(usuario_separador)
        response = client.get(reverse('dashboard'))
        content = response.content.decode('utf-8')

        # Links devem ter texto, não apenas ícones
        assert 'Dashboard' in content
        assert 'Novo Pedido' in content or 'Upload' in content
        assert 'Histórico' in content or 'Historico' in content
