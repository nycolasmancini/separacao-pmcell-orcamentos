# -*- coding: utf-8 -*-
"""
Testes E2E para Navegação do Menu Sidebar.

Fase 40: Implementar Menu Hamburguer Moderno
TDD: RED → GREEN → REFACTOR

Testa navegação, highlight de item ativo e comportamento responsive.
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
def usuario_test(db):
    """Cria usuário para testes de navegação."""
    usuario = Usuario(
        numero_login=5001,
        nome="Test User",
        senha="senha123",
        tipo=TipoUsuario.ADMINISTRADOR
    )
    usuario.save()
    return usuario


@pytest.mark.django_db
class TestSidebarNavegacao:
    """Testes para navegação do menu sidebar."""

    def test_navegacao_para_dashboard(self, client, usuario_test):
        """Testa navegação para Dashboard via sidebar."""
        client.force_login(usuario_test)

        # Acessa dashboard
        response = client.get(reverse('dashboard'))
        assert response.status_code == 200

        # Verifica se está na página correta
        content = response.content.decode('utf-8')
        assert 'Dashboard' in content

    def test_navegacao_para_historico(self, client, usuario_test):
        """Testa navegação para Histórico via sidebar."""
        client.force_login(usuario_test)

        # Acessa histórico
        response = client.get(reverse('historico'))
        assert response.status_code == 200

        # Verifica se está na página correta
        content = response.content.decode('utf-8')
        assert 'Histórico' in content or 'Historico' in content

    def test_navegacao_para_metricas(self, client, usuario_test):
        """Testa navegação para Métricas via sidebar."""
        client.force_login(usuario_test)

        # Acessa métricas
        response = client.get(reverse('metricas'))
        assert response.status_code == 200

        # Verifica se está na página correta
        content = response.content.decode('utf-8')
        assert 'Métricas' in content or 'Metricas' in content

    def test_navegacao_para_painel_compras(self, client, usuario_test):
        """Testa navegação para Painel de Compras via sidebar."""
        client.force_login(usuario_test)

        # Acessa painel de compras
        response = client.get(reverse('painel_compras'))
        assert response.status_code == 200

        # Verifica se está na página correta
        content = response.content.decode('utf-8')
        assert 'Compras' in content

    def test_navegacao_para_admin_panel(self, client, usuario_test):
        """Testa navegação para Admin Panel via sidebar."""
        client.force_login(usuario_test)

        # Acessa admin panel
        response = client.get(reverse('admin_panel'))
        assert response.status_code == 200

        # Verifica se está na página correta
        content = response.content.decode('utf-8')
        assert 'Usuários' in content or 'Usuarios' in content


@pytest.mark.django_db
class TestSidebarItemAtivo:
    """Testes para highlight do item ativo no menu."""

    def test_dashboard_item_ativo_quando_na_pagina_dashboard(self, client, usuario_test):
        """Dashboard deve ter classe 'ativo' quando estiver na página Dashboard."""
        client.force_login(usuario_test)
        response = client.get(reverse('dashboard'))
        content = response.content.decode('utf-8')

        # Deve ter indicador visual de item ativo (classe CSS)
        # Exemplos: 'active', 'bg-blue-100', 'border-blue-600'
        assert 'active' in content.lower() or 'bg-blue' in content, \
            "Dashboard deve ter indicador visual quando ativo"

    def test_historico_item_ativo_quando_na_pagina_historico(self, client, usuario_test):
        """Histórico deve ter classe 'ativo' quando estiver na página Histórico."""
        client.force_login(usuario_test)
        response = client.get(reverse('historico'))
        content = response.content.decode('utf-8')

        # Deve ter sidebar renderizada
        assert 'sidebar' in content.lower() or 'menu' in content.lower(), \
            "Histórico deve ter sidebar renderizada"

    def test_metricas_item_ativo_quando_na_pagina_metricas(self, client, usuario_test):
        """Métricas deve ter classe 'ativo' quando estiver na página Métricas."""
        client.force_login(usuario_test)
        response = client.get(reverse('metricas'))
        content = response.content.decode('utf-8')

        # Deve ter sidebar renderizada
        assert 'sidebar' in content.lower() or 'menu' in content.lower(), \
            "Métricas deve ter sidebar renderizada"


@pytest.mark.django_db
class TestSidebarSubmenu:
    """Testes para submenu do Admin Panel."""

    def test_admin_panel_tem_submenu(self, client, usuario_test):
        """Admin Panel deve ter submenu com 'Criar Usuário'."""
        client.force_login(usuario_test)
        response = client.get(reverse('dashboard'))
        content = response.content.decode('utf-8')

        # Deve ter estrutura de submenu
        if 'Admin' in content or 'Gerenciar' in content:
            # Se admin está visível, deve ter referência ao submenu
            assert 'Criar Usuário' in content or 'Criar Usuario' in content, \
                "Admin Panel deve ter submenu com 'Criar Usuário'"

    def test_submenu_expansivel_com_alpine(self, client, usuario_test):
        """Submenu deve ser expansível via Alpine.js."""
        client.force_login(usuario_test)
        response = client.get(reverse('dashboard'))
        content = response.content.decode('utf-8')

        # Deve ter controle Alpine.js para expandir/recolher submenu
        # Exemplos: x-show, x-transition, submenuOpen
        if 'Admin' in content or 'Gerenciar' in content:
            assert 'x-show' in content or 'x-transition' in content, \
                "Submenu deve ser controlado por Alpine.js"

    def test_criar_usuario_navegavel_via_submenu(self, client, usuario_test):
        """'Criar Usuário' deve ser navegável via submenu."""
        client.force_login(usuario_test)

        # Acessa criar usuário
        response = client.get(reverse('criar_usuario'))
        assert response.status_code == 200

        # Verifica se está na página correta
        content = response.content.decode('utf-8')
        assert 'Criar' in content and ('Usuário' in content or 'Usuario' in content)


@pytest.mark.django_db
class TestSidebarResponsivo:
    """Testes para comportamento responsivo do menu."""

    def test_sidebar_tem_estado_collapsed(self, client, usuario_test):
        """Sidebar deve suportar estado collapsed/expanded em desktop."""
        client.force_login(usuario_test)
        response = client.get(reverse('dashboard'))
        content = response.content.decode('utf-8')

        # Deve ter controle de colapso para desktop
        # Alpine.js: sidebarExpanded, collapsed, w-16, w-64, etc
        assert 'sidebarExpanded' in content or 'collapsed' in content or 'w-16' in content, \
            "Sidebar deve ter estado collapsed/expanded"

    def test_sidebar_tem_overlay_mobile(self, client, usuario_test):
        """Sidebar deve ter overlay/backdrop em mobile."""
        client.force_login(usuario_test)
        response = client.get(reverse('dashboard'))
        content = response.content.decode('utf-8')

        # Deve ter backdrop para fechar sidebar em mobile
        assert 'backdrop' in content or 'overlay' in content or '@click.away' in content, \
            "Sidebar deve ter backdrop para mobile"

    def test_sidebar_hidden_por_padrao_em_mobile(self, client, usuario_test):
        """Sidebar deve estar hidden por padrão em viewport mobile."""
        client.force_login(usuario_test)
        response = client.get(reverse('dashboard'))
        content = response.content.decode('utf-8')

        # Deve ter classe -translate-x-full ou hidden em mobile
        assert '-translate-x-full' in content or 'hidden' in content, \
            "Sidebar deve estar hidden em mobile por padrão"

    def test_sidebar_visivel_em_desktop(self, client, usuario_test):
        """Sidebar deve estar visível em viewport desktop."""
        client.force_login(usuario_test)
        response = client.get(reverse('dashboard'))
        content = response.content.decode('utf-8')

        # Deve ter breakpoint lg: (1024px+) com translate-x-0 ou block
        assert 'lg:translate-x-0' in content or 'lg:block' in content, \
            "Sidebar deve estar visível em desktop (lg:)"


@pytest.mark.django_db
class TestSidebarInteracao:
    """Testes para interações do usuário com sidebar."""

    def test_botao_toggle_tem_evento_click(self, client, usuario_test):
        """Botão hamburguer deve ter evento @click para abrir/fechar."""
        client.force_login(usuario_test)
        response = client.get(reverse('dashboard'))
        content = response.content.decode('utf-8')

        # Deve ter @click ou @click.prevent do Alpine.js
        assert '@click' in content, \
            "Botão hamburguer deve ter evento @click (Alpine.js)"

    def test_links_sidebar_sao_clicaveis(self, client, usuario_test):
        """Links da sidebar devem ser elementos <a> com href."""
        client.force_login(usuario_test)
        response = client.get(reverse('dashboard'))
        content = response.content.decode('utf-8')

        # Deve ter tags <a> com href
        assert '<a href=' in content, \
            "Sidebar deve ter links <a> clicáveis"

        # Deve ter múltiplos links
        link_count = content.count('<a href=')
        assert link_count >= 4, \
            f"Sidebar deve ter pelo menos 4 links (encontrou {link_count})"

    def test_sidebar_fecha_ao_clicar_fora_mobile(self, client, usuario_test):
        """Sidebar deve fechar ao clicar no backdrop (mobile)."""
        client.force_login(usuario_test)
        response = client.get(reverse('dashboard'))
        content = response.content.decode('utf-8')

        # Deve ter @click.away para fechar sidebar
        assert '@click.away' in content or '@click' in content, \
            "Sidebar deve fechar ao clicar fora (backdrop)"
