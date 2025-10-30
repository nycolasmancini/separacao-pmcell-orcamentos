"""
Testes E2E para sidebar mobile - Botão X de fechar
Fase 40b: Corrigir problema de z-index que impede o botão X de funcionar
"""

import re
import pytest
from playwright.sync_api import Page, expect


@pytest.fixture
def logged_in_page(page: Page):
    """Fixture que faz login antes de cada teste"""
    page.goto("http://localhost:8000/accounts/login/")
    page.fill('input[name="username"]', 'separador')
    page.fill('input[name="password"]', 'senha123')
    page.click('button[type="submit"]')
    page.wait_for_url("**/dashboard/")
    return page


class TestMobileSidebarClose:
    """Testes para verificar que o botão X fecha a sidebar no mobile"""

    def test_sidebar_fechada_por_padrao_mobile(self, logged_in_page: Page):
        """
        Teste 1: Verifica que sidebar inicia escondida em viewports mobile
        """
        # Configura viewport mobile (iPhone 12)
        logged_in_page.set_viewport_size({"width": 390, "height": 844})

        # Recarrega para aplicar viewport
        logged_in_page.reload()
        logged_in_page.wait_for_load_state("networkidle")

        # Verifica que sidebar está escondida (fora da tela)
        sidebar = logged_in_page.locator('#sidebar[data-sidebar]')
        expect(sidebar).to_have_class(re.compile(r'-translate-x-full'))

    def test_botao_hamburguer_abre_sidebar_mobile(self, logged_in_page: Page):
        """
        Teste 2: Clica no botão hamburguer e verifica que sidebar aparece
        """
        # Configura viewport mobile
        logged_in_page.set_viewport_size({"width": 390, "height": 844})
        logged_in_page.reload()
        logged_in_page.wait_for_load_state("networkidle")

        # Clica no botão hamburguer
        hamburger_btn = logged_in_page.locator('#hamburger-button')
        expect(hamburger_btn).to_be_visible()
        hamburger_btn.click()

        # Aguarda animação
        logged_in_page.wait_for_timeout(500)

        # Verifica que sidebar NÃO tem mais a classe -translate-x-full
        sidebar = logged_in_page.locator('#sidebar[data-sidebar]')
        expect(sidebar).not_to_have_class(re.compile(r'-translate-x-full'))

        # Verifica que backdrop está visível
        backdrop = logged_in_page.locator('.backdrop')
        expect(backdrop).to_be_visible()

    def test_botao_x_fecha_sidebar_mobile(self, logged_in_page: Page):
        """
        Teste 3: Clica no X e verifica que sidebar fecha
        ESTE TESTE VAI FALHAR ANTES DA CORREÇÃO!
        """
        # Configura viewport mobile
        logged_in_page.set_viewport_size({"width": 390, "height": 844})
        logged_in_page.reload()
        logged_in_page.wait_for_load_state("networkidle")

        # Abre sidebar com botão hamburguer
        hamburger_btn = logged_in_page.locator('#hamburger-button')
        hamburger_btn.click()
        logged_in_page.wait_for_timeout(500)

        # Verifica que sidebar está aberta
        sidebar = logged_in_page.locator('#sidebar[data-sidebar]')
        expect(sidebar).not_to_have_class(re.compile(r'-translate-x-full'))

        # Clica no botão X (dentro do header da sidebar)
        close_btn = logged_in_page.locator('.lg\\:hidden button[aria-label="Fechar menu"]')
        expect(close_btn).to_be_visible()
        close_btn.click()

        # Aguarda animação
        logged_in_page.wait_for_timeout(500)

        # Verifica que sidebar voltou a ter -translate-x-full (fechada)
        expect(sidebar).to_have_class(re.compile(r'-translate-x-full'))

        # Verifica que backdrop desapareceu
        backdrop = logged_in_page.locator('.backdrop')
        expect(backdrop).not_to_be_visible()

    def test_backdrop_fecha_sidebar_mobile(self, logged_in_page: Page):
        """
        Teste 4: Clica no backdrop e verifica que sidebar fecha
        """
        # Configura viewport mobile
        logged_in_page.set_viewport_size({"width": 390, "height": 844})
        logged_in_page.reload()
        logged_in_page.wait_for_load_state("networkidle")

        # Abre sidebar
        hamburger_btn = logged_in_page.locator('#hamburger-button')
        hamburger_btn.click()
        logged_in_page.wait_for_timeout(500)

        # Clica no backdrop
        backdrop = logged_in_page.locator('.backdrop')
        expect(backdrop).to_be_visible()
        backdrop.click()

        # Aguarda animação
        logged_in_page.wait_for_timeout(500)

        # Verifica que sidebar fechou
        sidebar = logged_in_page.locator('#sidebar[data-sidebar]')
        expect(sidebar).to_have_class(re.compile(r'-translate-x-full'))

    def test_z_index_sidebar_acima_backdrop(self, logged_in_page: Page):
        """
        Teste 5: Verifica que sidebar tem z-index maior que backdrop
        """
        # Configura viewport mobile
        logged_in_page.set_viewport_size({"width": 390, "height": 844})
        logged_in_page.reload()
        logged_in_page.wait_for_load_state("networkidle")

        # Abre sidebar
        hamburger_btn = logged_in_page.locator('#hamburger-button')
        hamburger_btn.click()
        logged_in_page.wait_for_timeout(500)

        # Pega z-index computed de ambos
        sidebar = logged_in_page.locator('#sidebar[data-sidebar]')
        backdrop = logged_in_page.locator('.backdrop')

        sidebar_z = logged_in_page.evaluate("""
            () => window.getComputedStyle(document.querySelector('#sidebar[data-sidebar]')).zIndex
        """)

        backdrop_z = logged_in_page.evaluate("""
            () => window.getComputedStyle(document.querySelector('.backdrop')).zIndex
        """)

        # Sidebar deve ter z-index maior que backdrop
        assert int(sidebar_z) > int(backdrop_z), \
            f"Sidebar z-index ({sidebar_z}) deve ser maior que backdrop ({backdrop_z})"

    def test_sidebar_permanece_aberta_desktop(self, logged_in_page: Page):
        """
        Teste 6: Em desktop, sidebar fica visível sempre
        """
        # Configura viewport desktop
        logged_in_page.set_viewport_size({"width": 1920, "height": 1080})
        logged_in_page.reload()
        logged_in_page.wait_for_load_state("networkidle")

        # Verifica que sidebar NÃO tem -translate-x-full em desktop
        sidebar = logged_in_page.locator('#sidebar[data-sidebar]')
        expect(sidebar).not_to_have_class(re.compile(r'-translate-x-full'))

        # Verifica que botão hamburguer NÃO está visível em desktop
        hamburger_btn = logged_in_page.locator('#hamburger-button')
        expect(hamburger_btn).not_to_be_visible()

        # Verifica que backdrop NÃO está visível em desktop
        backdrop = logged_in_page.locator('.backdrop')
        expect(backdrop).not_to_be_visible()

    def test_botao_seta_colapsa_sidebar_desktop(self, logged_in_page: Page):
        """
        Teste 7: Seta << colapsa sidebar em desktop (já funciona)
        """
        # Configura viewport desktop
        logged_in_page.set_viewport_size({"width": 1920, "height": 1080})
        logged_in_page.reload()
        logged_in_page.wait_for_load_state("networkidle")

        # Verifica que sidebar está expandida (lg:w-64)
        sidebar = logged_in_page.locator('#sidebar[data-sidebar]')

        # Clica no botão de colapsar (seta dupla <<)
        collapse_btn = logged_in_page.locator('button[aria-label="Expandir/recolher menu"]').first
        expect(collapse_btn).to_be_visible()
        collapse_btn.click()

        # Aguarda animação
        logged_in_page.wait_for_timeout(500)

        # Verifica que sidebar ficou estreita (lg:w-20)
        # Podemos verificar pela classe aplicada via Alpine.js
        sidebar_width = logged_in_page.evaluate("""
            () => window.getComputedStyle(document.querySelector('#sidebar[data-sidebar]')).width
        """)

        # Em desktop colapsado, largura deve ser próxima de 80px (w-20 = 5rem = 80px)
        assert "80px" in sidebar_width or "5rem" in sidebar_width, \
            f"Sidebar colapsada deve ter largura ~80px, mas tem {sidebar_width}"
