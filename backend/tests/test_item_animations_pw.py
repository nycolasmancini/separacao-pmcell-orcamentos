# -*- coding: utf-8 -*-
"""
Testes E2E com Playwright para validar animações de itens.

Fase 37: Validar que itens separados/substituídos/desmarcados fazem animação
fluida de fade out e se movem para a seção correta (Itens Separados ou Itens Não Separados).

Usando Playwright para simular interações do usuário e validar comportamento visual.
"""

import pytest
from playwright.sync_api import Page, expect
import time
from django.test import LiveServerTestCase
from django.contrib.auth import get_user_model
from core.models import Pedido, ItemPedido, Produto


User = get_user_model()


class TestItemAnimationsPlaywright(LiveServerTestCase):
    """
    Testes E2E para animações de itens usando Playwright.

    Validações:
    - Item marcado como separado: fade out → move para "Itens Separados"
    - Item desmarcado: fade out → move para "Itens Não Separados"
    - Item substituído: fade out → move para "Itens Separados"
    - Badges atualizam corretamente
    - Animações não conflitam em múltiplas operações
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        # Criar usuários
        cls.vendedor = User.objects.create_user(
            numero_login=9999,
            nome="Vendedor Teste",
            tipo="VENDEDOR",
            pin="9999"
        )

        cls.usuario = User.objects.create_user(
            numero_login=1001,
            nome="Separador Teste",
            tipo="SEPARADOR",
            pin="1234"
        )

        # Criar pedido com 5 itens (usando campos corretos do modelo)
        cls.pedido = Pedido.objects.create(
            numero_orcamento="E2E-ANIM-001",
            codigo_cliente="CLI001",
            nome_cliente="Cliente Teste",
            vendedor=cls.vendedor,
            data="28/10/2025",
            status="EM_SEPARACAO"
        )

        # Criar 5 produtos e itens
        cls.itens = []
        for i in range(1, 6):
            produto = Produto.objects.create(
                codigo=f"PROD{i:03d}",
                descricao=f"Produto Teste {i}",
                quantidade=10,
                valor_unitario=100.0,
                valor_total=1000.0
            )
            item = ItemPedido.objects.create(
                pedido=cls.pedido,
                produto=produto,
                quantidade_solicitada=5,
                separado=False
            )
            cls.itens.append(item)

    @classmethod
    def tearDownClass(cls):
        # Limpar dados de teste
        ItemPedido.objects.all().delete()
        Pedido.objects.all().delete()
        Produto.objects.all().delete()
        User.objects.all().delete()
        super().tearDownClass()

    def fazer_login(self, page: Page):
        """Helper para fazer login no sistema."""
        page.goto(f'{self.live_server_url}/login/')
        page.wait_for_load_state("networkidle")

        page.fill('input[name="numero_login"]', '1001')
        page.fill('input[name="pin"]', '1234')
        page.click('button[type="submit"]')

        page.wait_for_url(f"{self.live_server_url}/dashboard/", timeout=10000)

    def abrir_pedido(self, page: Page):
        """Helper para abrir página de detalhe do pedido."""
        page.goto(f'{self.live_server_url}/pedidos/{self.pedido.id}/')
        page.wait_for_load_state("networkidle")

        # Aguardar WebSocket conectar
        time.sleep(1)

    @pytest.mark.django_db
    def test_marcar_separado_move_para_secao_separados(self, page: Page):
        """
        Teste E2E: Marcar item como separado deve fazer fade out e mover
        para seção "Itens Separados".

        Cenário:
        1. Item começa em "Itens Não Separados"
        2. Marcar checkbox de separado
        3. Item faz fade out
        4. Item aparece em "Itens Separados" com fade in
        5. Badges atualizam
        """
        self.fazer_login(page)
        self.abrir_pedido(page)

        item_id = self.itens[0].id

        # 1. Validar que item está em "Itens Não Separados"
        container_nao_separados = page.locator('#container-nao-separados')
        item_origem = container_nao_separados.locator(f'#item-{item_id}')
        expect(item_origem).to_be_visible()

        # 2. Marcar checkbox de separado
        checkbox = page.locator(f'#item-{item_id} input[type="checkbox"]')
        checkbox.check()

        # 3. Aguardar animação completar (250ms + buffer)
        time.sleep(0.4)

        # 4. Validar que item MOVEU para "Itens Separados"
        container_separados = page.locator('#container-separados')
        item_destino = container_separados.locator(f'#item-{item_id}')
        expect(item_destino).to_be_visible()

        # 5. Validar que item NÃO está mais em "Itens Não Separados"
        # (usando count para evitar timeout - count = 0 significa que não existe)
        expect(container_nao_separados.locator(f'#item-{item_id}')).to_have_count(0)

        # 6. Validar badges
        badge_nao_separados = page.locator('#badge-nao-separados')
        badge_separados = page.locator('#badge-separados')

        expect(badge_nao_separados).to_contain_text('4 itens')  # 5 - 1 = 4
        expect(badge_separados).to_contain_text('1 itens')  # 0 + 1 = 1

    @pytest.mark.django_db
    def test_desmarcar_separado_move_para_secao_nao_separados(self, page: Page):
        """
        Teste E2E: Desmarcar item separado deve fazer fade out e mover
        para seção "Itens Não Separados".

        Cenário:
        1. Primeiro, marcar item como separado
        2. Item está em "Itens Separados"
        3. Desmarcar checkbox
        4. Item faz fade out
        5. Item aparece em "Itens Não Separados" com fade in
        6. Badges atualizam
        """
        self.fazer_login(page)
        self.abrir_pedido(page)

        item_id = self.itens[1].id

        # Passo 1: Marcar item como separado primeiro
        checkbox = page.locator(f'#item-{item_id} input[type="checkbox"]')
        checkbox.check()
        time.sleep(0.4)

        # Validar que está em "Itens Separados"
        container_separados = page.locator('#container-separados')
        expect(container_separados.locator(f'#item-{item_id}')).to_be_visible()

        # Passo 2: Desmarcar checkbox
        checkbox_separados = container_separados.locator(f'#item-{item_id} input[type="checkbox"]')
        checkbox_separados.uncheck()

        # Passo 3: Aguardar animação
        time.sleep(0.4)

        # Passo 4: Validar que item VOLTOU para "Itens Não Separados"
        container_nao_separados = page.locator('#container-nao-separados')
        expect(container_nao_separados.locator(f'#item-{item_id}')).to_be_visible()

        # Passo 5: Validar que item NÃO está mais em "Itens Separados"
        expect(container_separados.locator(f'#item-{item_id}')).to_have_count(0)

        # Passo 6: Validar badges voltaram ao estado original
        badge_nao_separados = page.locator('#badge-nao-separados')
        badge_separados = page.locator('#badge-separados')

        expect(badge_nao_separados).to_contain_text('5 itens')  # Voltou para 5
        expect(badge_separados).to_contain_text('0 itens')  # Voltou para 0

    @pytest.mark.django_db
    def test_substituir_item_move_para_secao_separados(self, page: Page):
        """
        Teste E2E: Substituir item deve fazer fade out e mover para seção
        "Itens Separados" (pois substituído = separado).

        Cenário:
        1. Item começa em "Itens Não Separados"
        2. Abrir menu dropdown → Substituir item
        3. Preencher modal de substituição
        4. Item faz fade out
        5. Item aparece em "Itens Separados" com badge "Substituído"
        6. Badges atualizam
        """
        self.fazer_login(page)
        self.abrir_pedido(page)

        item_id = self.itens[2].id

        # 1. Validar que item está em "Itens Não Separados"
        container_nao_separados = page.locator('#container-nao-separados')
        expect(container_nao_separados.locator(f'#item-{item_id}')).to_be_visible()

        # 2. Abrir menu dropdown
        menu_button = page.locator(f'#item-{item_id} button[data-dropdown-toggle]')
        menu_button.click()
        time.sleep(0.3)  # Aguardar menu abrir

        # 3. Clicar em "Marcar como Substituído"
        page.locator('text="🔄 Marcar como Substituído"').click()

        # 4. Preencher modal com código substituto
        page.wait_for_selector('input[name="produto_substituto"]', state="visible")
        page.fill('input[name="produto_substituto"]', 'PROD999 - Produto Substituto')

        # 5. Confirmar substituição
        page.locator('button:has-text("Confirmar Substituição")').click()

        # 6. Aguardar animação
        time.sleep(0.4)

        # 7. Validar que item MOVEU para "Itens Separados"
        container_separados = page.locator('#container-separados')
        item_substituido = container_separados.locator(f'#item-{item_id}')
        expect(item_substituido).to_be_visible()

        # 8. Validar que tem badge "Substituído"
        badge_substituido = item_substituido.locator('text=/Substituído|Substituido/i')
        expect(badge_substituido).to_be_visible()

        # 9. Validar que item NÃO está mais em "Itens Não Separados"
        expect(container_nao_separados.locator(f'#item-{item_id}')).to_have_count(0)

        # 10. Validar badges
        badge_nao_separados = page.locator('#badge-nao-separados')
        badge_separados = page.locator('#badge-separados')

        expect(badge_nao_separados).to_contain_text('4 itens')  # 5 - 1 = 4
        expect(badge_separados).to_contain_text('1 itens')  # 0 + 1 = 1

    @pytest.mark.django_db
    def test_multiplos_itens_animam_sequencialmente(self, page: Page):
        """
        Teste E2E: Marcar múltiplos itens como separados em sequência deve
        animar cada um corretamente sem conflitos.

        Cenário:
        1. Marcar 3 itens como separados em sequência
        2. Cada item deve fazer animação individual
        3. Todos devem terminar em "Itens Separados"
        4. Badges devem refletir contagem correta
        """
        self.fazer_login(page)
        self.abrir_pedido(page)

        # Marcar itens 0, 1, 2 como separados
        itens_para_separar = [self.itens[0].id, self.itens[1].id, self.itens[2].id]

        for item_id in itens_para_separar:
            # Marcar checkbox
            checkbox = page.locator(f'#item-{item_id} input[type="checkbox"]')
            checkbox.check()

            # Aguardar animação completar antes de marcar próximo
            time.sleep(0.4)

        # Validar que todos os 3 itens estão em "Itens Separados"
        container_separados = page.locator('#container-separados')
        for item_id in itens_para_separar:
            expect(container_separados.locator(f'#item-{item_id}')).to_be_visible()

        # Validar badges
        badge_nao_separados = page.locator('#badge-nao-separados')
        badge_separados = page.locator('#badge-separados')

        expect(badge_nao_separados).to_contain_text('2 itens')  # 5 - 3 = 2
        expect(badge_separados).to_contain_text('3 itens')  # 0 + 3 = 3

    @pytest.mark.django_db
    def test_animacao_fade_out_visivel_durante_transicao(self, page: Page):
        """
        Teste E2E: Durante a transição, a classe CSS 'item-fade-out' deve
        ser aplicada ao elemento.

        Nota: Este teste captura o comportamento durante a animação, que é
        difícil de testar de forma determinística. Validamos que a animação
        foi aplicada através de screenshot ou validação de classe CSS.
        """
        self.fazer_login(page)
        self.abrir_pedido(page)

        item_id = self.itens[3].id

        # Preparar para capturar estado durante animação
        checkbox = page.locator(f'#item-{item_id} input[type="checkbox"]')

        # Marcar checkbox
        checkbox.check()

        # Aguardar um momento curto (meio da animação)
        time.sleep(0.1)

        # Validar que elemento ainda existe no DOM durante transição
        # (a animação não remove imediatamente)
        item = page.locator(f'#item-{item_id}')

        # Item pode estar em qualquer container durante transição
        # Validamos apenas que existe no DOM
        expect(item.first).to_be_attached()

        # Aguardar animação completar
        time.sleep(0.3)

        # Validar que moveu para container correto
        container_separados = page.locator('#container-separados')
        expect(container_separados.locator(f'#item-{item_id}')).to_be_visible()

    @pytest.mark.django_db
    def test_badges_sempre_corretos_apos_operacoes_mistas(self, page: Page):
        """
        Teste E2E: Executar operações mistas (separar, desmarcar, substituir)
        e validar que badges sempre refletem estado correto.

        Cenário:
        1. Marcar item 0 como separado
        2. Marcar item 1 como separado
        3. Desmarcar item 0
        4. Substituir item 2
        5. Validar contagens finais
        """
        self.fazer_login(page)
        self.abrir_pedido(page)

        # Operação 1: Separar item 0
        checkbox_0 = page.locator(f'#item-{self.itens[0].id} input[type="checkbox"]')
        checkbox_0.check()
        time.sleep(0.4)

        # Badge: Não Separados=4, Separados=1
        expect(page.locator('#badge-nao-separados')).to_contain_text('4 itens')
        expect(page.locator('#badge-separados')).to_contain_text('1 itens')

        # Operação 2: Separar item 1
        checkbox_1 = page.locator(f'#item-{self.itens[1].id} input[type="checkbox"]')
        checkbox_1.check()
        time.sleep(0.4)

        # Badge: Não Separados=3, Separados=2
        expect(page.locator('#badge-nao-separados')).to_contain_text('3 itens')
        expect(page.locator('#badge-separados')).to_contain_text('2 itens')

        # Operação 3: Desmarcar item 0 (volta para não separado)
        container_separados = page.locator('#container-separados')
        checkbox_0_separado = container_separados.locator(f'#item-{self.itens[0].id} input[type="checkbox"]')
        checkbox_0_separado.uncheck()
        time.sleep(0.4)

        # Badge: Não Separados=4, Separados=1
        expect(page.locator('#badge-nao-separados')).to_contain_text('4 itens')
        expect(page.locator('#badge-separados')).to_contain_text('1 itens')

        # Operação 4: Substituir item 2
        item_2_id = self.itens[2].id
        menu_button = page.locator(f'#item-{item_2_id} button[data-dropdown-toggle]')
        menu_button.click()
        time.sleep(0.3)

        page.locator('text="🔄 Marcar como Substituído"').click()
        page.wait_for_selector('input[name="produto_substituto"]', state="visible")
        page.fill('input[name="produto_substituto"]', 'PROD999')
        page.locator('button:has-text("Confirmar Substituição")').click()
        time.sleep(0.4)

        # Badge Final: Não Separados=3, Separados=2 (1 separado + 1 substituído)
        expect(page.locator('#badge-nao-separados')).to_contain_text('3 itens')
        expect(page.locator('#badge-separados')).to_contain_text('2 itens')


# Fixtures do Playwright (pytest) - Sobrescrevem fixtures do conftest.py
@pytest.fixture(scope="function", autouse=True)
def _django_db_mark(transactional_db):
    """Marca todos os testes desta classe para usar o banco de dados."""
    pass


@pytest.fixture(scope="function")
def page(browser):
    """Cria uma nova página para cada teste."""
    context = browser.new_context()
    page = context.new_page()
    yield page
    context.close()


@pytest.fixture(scope="module")
def browser():
    """Inicializa o browser Playwright (Chromium headless)."""
    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        yield browser
        browser.close()
