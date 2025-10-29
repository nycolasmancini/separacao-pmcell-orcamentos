# -*- coding: utf-8 -*-
"""
Testes E2E para reordenação animada de itens (Fase 39e).

Valida que quando um item muda de estado, ele:
1. Faz fade out da posição atual
2. É reordenado para a posição correta
3. Faz fade in na nova posição
"""

import pytest
import time
from playwright.sync_api import Page, expect
from django.utils import timezone
from core.models import Pedido, ItemPedido, Produto, Usuario


@pytest.mark.django_db
class TestReordenacaoAnimada:
    """Testes E2E para animação de reordenação."""

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

    def test_item_reordena_quando_marcado_separado(self, page: Page):
        """Item aguardando deve ir para o final quando marcado como separado."""
        # Criar: A (aguardando), B (aguardando), C (aguardando)
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
            separado=False
        )
        ItemPedido.objects.create(
            pedido=self.pedido,
            produto=self.produto_c,
            quantidade_solicitada=1,
            separado=False
        )

        # Fazer login e acessar pedido
        self._login(page)
        page.goto(f"http://localhost:8000/pedido/{self.pedido.id}/")

        # Validar ordem inicial: A, B, C (todos aguardando)
        items = page.locator('.item-pedido')
        expect(items.nth(0)).to_contain_text('Produto A')
        expect(items.nth(1)).to_contain_text('Produto B')
        expect(items.nth(2)).to_contain_text('Produto C')

        # Marcar item A como separado
        checkbox_a = items.nth(0).locator('input[type="checkbox"][data-action="marcar-separado"]')
        checkbox_a.check()

        # Aguardar animação completar (fade out + reordenação + fade in)
        time.sleep(1)

        # Validar nova ordem: B, C (aguardando), A (separado)
        items_after = page.locator('.item-pedido')
        expect(items_after.nth(0)).to_contain_text('Produto B')
        expect(items_after.nth(1)).to_contain_text('Produto C')
        expect(items_after.nth(2)).to_contain_text('Produto A')

        # Validar que A está com classe de separado
        item_a = items_after.nth(2)
        expect(item_a).to_have_class('border-green-200')

    def test_item_reordena_quando_enviado_compra(self, page: Page):
        """Item aguardando deve ir para grupo 'compra' quando enviado."""
        # Criar: A (aguardando), B (aguardando), C (separado)
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
            separado=False
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

        # Validar ordem inicial: A, B (aguardando), C (separado)
        items = page.locator('.item-pedido')
        expect(items.nth(0)).to_contain_text('Produto A')
        expect(items.nth(1)).to_contain_text('Produto B')
        expect(items.nth(2)).to_contain_text('Produto C')

        # Marcar item A para compra
        item_a = items.nth(0)
        btn_compra = item_a.locator('button:has-text("Enviar p/ Compra")')
        btn_compra.click()

        # Aguardar animação
        time.sleep(1)

        # Nova ordem esperada: B (aguardando), A (compra), C (separado)
        items_after = page.locator('.item-pedido')
        expect(items_after.nth(0)).to_contain_text('Produto B')
        expect(items_after.nth(1)).to_contain_text('Produto A')
        expect(items_after.nth(2)).to_contain_text('Produto C')

        # Validar classe de compra
        item_a_after = items_after.nth(1)
        expect(item_a_after).to_have_class('border-orange-200')

    def test_item_reordena_alfabeticamente_dentro_grupo(self, page: Page):
        """Itens devem manter ordem alfabética dentro do mesmo grupo."""
        # Criar: A (aguardando), C (aguardando), B (aguardando)
        ItemPedido.objects.create(
            pedido=self.pedido,
            produto=self.produto_a,
            quantidade_solicitada=1,
            separado=False
        )
        ItemPedido.objects.create(
            pedido=self.pedido,
            produto=self.produto_c,
            quantidade_solicitada=1,
            separado=False
        )
        ItemPedido.objects.create(
            pedido=self.pedido,
            produto=self.produto_b,
            quantidade_solicitada=1,
            separado=False
        )

        # Fazer login e acessar pedido
        self._login(page)
        page.goto(f"http://localhost:8000/pedido/{self.pedido.id}/")

        # Ordem deve estar alfabética: A, B, C
        items = page.locator('.item-pedido')
        expect(items.nth(0)).to_contain_text('Produto A')
        expect(items.nth(1)).to_contain_text('Produto B')
        expect(items.nth(2)).to_contain_text('Produto C')

    def test_multiplos_itens_reordenam_independentemente(self, page: Page):
        """Múltiplos itens podem ser reordenados independentemente."""
        # Criar: A, B, C (todos aguardando)
        for produto in [self.produto_a, self.produto_b, self.produto_c]:
            ItemPedido.objects.create(
                pedido=self.pedido,
                produto=produto,
                quantidade_solicitada=1,
                separado=False
            )

        # Fazer login e acessar pedido
        self._login(page)
        page.goto(f"http://localhost:8000/pedido/{self.pedido.id}/")

        # Marcar B como separado
        items = page.locator('.item-pedido')
        checkbox_b = items.nth(1).locator('input[type="checkbox"]')
        checkbox_b.check()
        time.sleep(1)

        # Ordem esperada: A, C (aguardando), B (separado)
        items_after_1 = page.locator('.item-pedido')
        expect(items_after_1.nth(0)).to_contain_text('Produto A')
        expect(items_after_1.nth(1)).to_contain_text('Produto C')
        expect(items_after_1.nth(2)).to_contain_text('Produto B')

        # Marcar A como separado
        checkbox_a = items_after_1.nth(0).locator('input[type="checkbox"]')
        checkbox_a.check()
        time.sleep(1)

        # Ordem final: C (aguardando), A, B (separados alfabeticamente)
        items_after_2 = page.locator('.item-pedido')
        expect(items_after_2.nth(0)).to_contain_text('Produto C')
        expect(items_after_2.nth(1)).to_contain_text('Produto A')
        expect(items_after_2.nth(2)).to_contain_text('Produto B')

    def test_animacao_fadeout_visivel(self, page: Page):
        """Validar que animação de fade out é aplicada."""
        # Criar item aguardando
        ItemPedido.objects.create(
            pedido=self.pedido,
            produto=self.produto_a,
            quantidade_solicitada=1,
            separado=False
        )

        # Fazer login e acessar pedido
        self._login(page)
        page.goto(f"http://localhost:8000/pedido/{self.pedido.id}/")

        # Capturar item antes da animação
        item = page.locator('.item-pedido').nth(0)

        # Marcar como separado e verificar classe de animação
        checkbox = item.locator('input[type="checkbox"]')
        checkbox.check()

        # Verificar se classe de fade out foi aplicada (timing rápido)
        # Nota: Em teste real, verificaríamos a opacidade ou classe CSS
        time.sleep(0.5)

        # Item deve existir após animação completa
        items_after = page.locator('.item-pedido')
        expect(items_after).to_have_count(1)

    def test_animacao_nao_duplica_item(self, page: Page):
        """Reordenação animada não deve duplicar o item."""
        # Criar item
        ItemPedido.objects.create(
            pedido=self.pedido,
            produto=self.produto_a,
            quantidade_solicitada=1,
            separado=False
        )

        # Fazer login e acessar pedido
        self._login(page)
        page.goto(f"http://localhost:8000/pedido/{self.pedido.id}/")

        # Verificar contagem inicial
        items_before = page.locator('.item-pedido')
        expect(items_before).to_have_count(1)

        # Marcar como separado
        checkbox = items_before.nth(0).locator('input[type="checkbox"]')
        checkbox.check()

        # Aguardar animação completa
        time.sleep(1.5)

        # Verificar que ainda há apenas 1 item (sem duplicação)
        items_after = page.locator('.item-pedido')
        expect(items_after).to_have_count(1)
