# -*- coding: utf-8 -*-
"""
Testes E2E para interface de lista corrida (Fase 39c).

Valida que a interface renderiza uma lista única contínua
de itens, sem separação visual entre separados e não separados.
"""

import pytest
from playwright.sync_api import Page, expect
from django.utils import timezone
from core.models import Pedido, ItemPedido, Produto, Usuario


@pytest.mark.django_db
class TestListaCorridaInterface:
    """Testes E2E da interface de lista corrida."""

    @pytest.fixture(autouse=True)
    def setup(self, db):
        """Setup que roda antes de cada teste."""
        # Criar usuário vendedor
        self.vendedor = Usuario.objects.create(
            numero_login="001",
            nome="Vendedor Teste",
            tipo="VENDEDOR",
            ativo=True
        )
        self.vendedor.set_password("1234")
        self.vendedor.save()

        # Criar usuário separador
        self.separador = Usuario.objects.create(
            numero_login="002",
            nome="Separador Teste",
            tipo="SEPARADOR",
            ativo=True
        )
        self.separador.set_password("1234")
        self.separador.save()

        # Criar pedido
        self.pedido = Pedido.objects.create(
            numero_orcamento="ORD-001",
            codigo_cliente="CLI-001",
            nome_cliente="Cliente Teste",
            vendedor=self.vendedor,
            logistica="MOTOBOY",
            embalagem="CAIXA",
            status="EM_SEPARACAO"
        )

        # Criar produtos
        self.produto_a = Produto.objects.create(
            codigo='PROD-A',
            descricao='Produto A',
            quantidade=10,
            valor_unitario=100.00,
            valor_total=1000.00
        )
        self.produto_b = Produto.objects.create(
            codigo='PROD-B',
            descricao='Produto B',
            quantidade=10,
            valor_unitario=100.00,
            valor_total=1000.00
        )
        self.produto_c = Produto.objects.create(
            codigo='PROD-C',
            descricao='Produto C',
            quantidade=10,
            valor_unitario=100.00,
            valor_total=1000.00
        )

    def _login(self, page: Page):
        """Helper para fazer login."""
        page.goto("http://localhost:8000/login/")
        page.fill('input[name="numero_login"]', "002")
        page.fill('input[name="password"]', "1234")
        page.click('button[type="submit"]')
        page.wait_for_url("http://localhost:8000/painel/", timeout=5000)

    def test_interface_renderiza_lista_unica(self, page: Page):
        """Interface deve renderizar uma lista única de itens."""
        # Criar itens
        ItemPedido.objects.create(
            pedido=self.pedido,
            produto=self.produto_a,
            quantidade_solicitada=1,
            separado=False
        )
        ItemPedido.objects.create(
            pedido=self.pedido,
            produto=self.produto_b,
            quantidade_solicitada=1,
            separado=True,
            separado_por=self.separador,
            separado_em=timezone.now()
        )

        # Fazer login e acessar pedido
        self._login(page)
        page.goto(f"http://localhost:8000/pedido/{self.pedido.id}/")

        # Validar que existe uma lista de itens
        items_list = page.locator('#lista-itens')
        expect(items_list).to_be_visible()

        # Validar que todos os itens estão na mesma lista
        items = page.locator('.item-pedido')
        expect(items).to_have_count(2)

    def test_interface_nao_tem_secoes_separadas(self, page: Page):
        """Interface NÃO deve ter seções separadas para itens separados/não separados."""
        # Criar itens
        ItemPedido.objects.create(
            pedido=self.pedido,
            produto=self.produto_a,
            quantidade_solicitada=1,
            separado=False
        )
        ItemPedido.objects.create(
            pedido=self.pedido,
            produto=self.produto_b,
            quantidade_solicitada=1,
            separado=True,
            separado_por=self.separador,
            separado_em=timezone.now()
        )

        # Fazer login e acessar pedido
        self._login(page)
        page.goto(f"http://localhost:8000/pedido/{self.pedido.id}/")

        # Validar que NÃO existem seções separadas
        # (assumindo que as antigas seções tinham IDs específicos)
        separados_section = page.locator('#itens-separados')
        nao_separados_section = page.locator('#itens-nao-separados')

        expect(separados_section).not_to_be_visible()
        expect(nao_separados_section).not_to_be_visible()

    def test_itens_aparecem_na_ordem_correta(self, page: Page):
        """Itens devem aparecer na ordem: aguardando, compra, substituído, separado."""
        # Criar itens em ordem aleatória
        # C - Separado
        ItemPedido.objects.create(
            pedido=self.pedido,
            produto=self.produto_c,
            quantidade_solicitada=1,
            separado=True,
            separado_por=self.separador,
            separado_em=timezone.now()
        )
        # A - Aguardando
        ItemPedido.objects.create(
            pedido=self.pedido,
            produto=self.produto_a,
            quantidade_solicitada=1,
            separado=False
        )
        # B - Compra
        ItemPedido.objects.create(
            pedido=self.pedido,
            produto=self.produto_b,
            quantidade_solicitada=1,
            separado=False,
            em_compra=True,
            enviado_para_compra_por=self.separador,
            enviado_para_compra_em=timezone.now()
        )

        # Fazer login e acessar pedido
        self._login(page)
        page.goto(f"http://localhost:8000/pedido/{self.pedido.id}/")

        # Validar ordem visual dos itens
        items = page.locator('.item-pedido')

        # Primeiro item deve ser A (aguardando)
        first_item = items.nth(0)
        expect(first_item).to_contain_text('Produto A')

        # Segundo item deve ser B (compra)
        second_item = items.nth(1)
        expect(second_item).to_contain_text('Produto B')

        # Terceiro item deve ser C (separado)
        third_item = items.nth(2)
        expect(third_item).to_contain_text('Produto C')

    def test_lista_corrida_contem_todos_estados(self, page: Page):
        """Lista corrida deve conter itens de todos os estados."""
        # Criar 1 item de cada estado
        ItemPedido.objects.create(
            pedido=self.pedido,
            produto=self.produto_a,
            quantidade_solicitada=1,
            separado=False
        )

        produto_d = Produto.objects.create(
            codigo='PROD-D',
            descricao='Produto D',
            quantidade=10,
            valor_unitario=100.00,
            valor_total=1000.00
        )
        ItemPedido.objects.create(
            pedido=self.pedido,
            produto=produto_d,
            quantidade_solicitada=1,
            separado=False,
            em_compra=True,
            enviado_para_compra_por=self.separador,
            enviado_para_compra_em=timezone.now()
        )

        produto_e = Produto.objects.create(
            codigo='PROD-E',
            descricao='Produto E',
            quantidade=10,
            valor_unitario=100.00,
            valor_total=1000.00
        )
        ItemPedido.objects.create(
            pedido=self.pedido,
            produto=produto_e,
            quantidade_solicitada=1,
            separado=True,
            substituido=True,
            produto_substituto="Substituto E",
            separado_por=self.separador,
            separado_em=timezone.now()
        )

        ItemPedido.objects.create(
            pedido=self.pedido,
            produto=self.produto_c,
            quantidade_solicitada=1,
            separado=True,
            separado_por=self.separador,
            separado_em=timezone.now()
        )

        # Fazer login e acessar pedido
        self._login(page)
        page.goto(f"http://localhost:8000/pedido/{self.pedido.id}/")

        # Validar que todos os itens estão presentes
        items = page.locator('.item-pedido')
        expect(items).to_have_count(4)

        # Validar ordem específica
        expect(items.nth(0)).to_contain_text('Produto A')  # Aguardando
        expect(items.nth(1)).to_contain_text('Produto D')  # Compra
        expect(items.nth(2)).to_contain_text('Produto E')  # Substituído
        expect(items.nth(3)).to_contain_text('Produto C')  # Separado

    def test_lista_vazia_renderiza_mensagem(self, page: Page):
        """Pedido sem itens deve renderizar mensagem apropriada."""
        # Não criar nenhum item

        # Fazer login e acessar pedido
        self._login(page)
        page.goto(f"http://localhost:8000/pedido/{self.pedido.id}/")

        # Validar mensagem de lista vazia ou ausência de itens
        items = page.locator('.item-pedido')
        expect(items).to_have_count(0)

    def test_estrutura_html_lista_corrida(self, page: Page):
        """Estrutura HTML deve ter uma lista contínua sem divisões."""
        # Criar itens
        ItemPedido.objects.create(
            pedido=self.pedido,
            produto=self.produto_a,
            quantidade_solicitada=1,
            separado=False
        )
        ItemPedido.objects.create(
            pedido=self.pedido,
            produto=self.produto_b,
            quantidade_solicitada=1,
            separado=True,
            separado_por=self.separador,
            separado_em=timezone.now()
        )

        # Fazer login e acessar pedido
        self._login(page)
        page.goto(f"http://localhost:8000/pedido/{self.pedido.id}/")

        # Validar que existe container único
        lista_container = page.locator('#lista-itens')
        expect(lista_container).to_be_visible()

        # Validar que itens são filhos diretos (ou próximos)
        items = lista_container.locator('.item-pedido')
        expect(items).to_have_count(2)
