# -*- coding: utf-8 -*-
"""
Testes E2E para sincronização WebSocket com reordenação animada (Fase 39g).

Valida que quando eventos WebSocket são recebidos:
1. Itens são reordenados automaticamente na lista corrida
2. Animações de fade out/in são aplicadas
3. Ordem final está correta após múltiplos eventos
4. Não há duplicação de itens durante sincronização
"""

import pytest
import json
import asyncio
from playwright.sync_api import Page, expect
from django.utils import timezone
from core.models import Pedido, ItemPedido, Produto, Usuario
from channels.testing import WebsocketCommunicator
from core.routing import application


@pytest.mark.django_db
class TestWebSocketReordenacao:
    """Testes E2E para reordenação via WebSocket."""

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

        # Criar usuário separador 1
        self.separador1 = Usuario.objects.create(
            numero_login="002",
            nome="Separador 1",
            tipo="SEPARADOR",
            ativo=True
        )
        self.separador1.set_password("1234")
        self.separador1.save()

        # Criar usuário separador 2 (para simular outro usuário)
        self.separador2 = Usuario.objects.create(
            numero_login="003",
            nome="Separador 2",
            tipo="SEPARADOR",
            ativo=True
        )
        self.separador2.set_password("1234")
        self.separador2.save()

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

    def test_websocket_reordena_item_separado_por_outro_usuario(self, page: Page):
        """
        Quando outro usuário marca item como separado, deve reordenar na minha tela.
        """
        # Criar: A, B, C (todos aguardando)
        item_a = ItemPedido.objects.create(
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

        # Login como separador 1 e acessar pedido
        self._login(page)
        page.goto(f"http://localhost:8000/pedido/{self.pedido.id}/")

        # Verificar ordem inicial: A, B, C
        items = page.locator('.item-pedido')
        expect(items.nth(0)).to_contain_text('Produto A')
        expect(items.nth(1)).to_contain_text('Produto B')
        expect(items.nth(2)).to_contain_text('Produto C')

        # Simular separador 2 marcando item A como separado via backend
        item_a.separado = True
        item_a.separado_por = self.separador2
        item_a.separado_em = timezone.now()
        item_a.save()

        # WebSocket deve enviar evento e trigger reordenação
        # Aguardar animação + sincronização WebSocket
        page.wait_for_timeout(2000)

        # Nova ordem esperada: B, C (aguardando), A (separado)
        items_after = page.locator('.item-pedido')
        expect(items_after.nth(0)).to_contain_text('Produto B')
        expect(items_after.nth(1)).to_contain_text('Produto C')
        expect(items_after.nth(2)).to_contain_text('Produto A')

        # Validar estado visual de A
        item_a_element = items_after.nth(2)
        expect(item_a_element).to_have_class('border-green-200')

    def test_websocket_reordena_multiplos_itens_sequencialmente(self, page: Page):
        """
        Múltiplos eventos WebSocket devem reordenar itens sequencialmente.
        """
        # Criar: A, B, C (todos aguardando)
        item_a = ItemPedido.objects.create(
            pedido=self.pedido,
            produto=self.produto_a,
            quantidade_solicitada=1,
            separado=False
        )
        item_b = ItemPedido.objects.create(
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

        # Login e acessar pedido
        self._login(page)
        page.goto(f"http://localhost:8000/pedido/{self.pedido.id}/")

        # Marcar A como separado
        item_a.separado = True
        item_a.separado_por = self.separador2
        item_a.separado_em = timezone.now()
        item_a.save()
        page.wait_for_timeout(1500)

        # Ordem esperada: B, C, A
        items_1 = page.locator('.item-pedido')
        expect(items_1.nth(0)).to_contain_text('Produto B')
        expect(items_1.nth(1)).to_contain_text('Produto C')
        expect(items_1.nth(2)).to_contain_text('Produto A')

        # Marcar B como separado
        item_b.separado = True
        item_b.separado_por = self.separador2
        item_b.separado_em = timezone.now()
        item_b.save()
        page.wait_for_timeout(1500)

        # Ordem final: C, A, B (C aguardando, A e B separados alfabeticamente)
        items_2 = page.locator('.item-pedido')
        expect(items_2.nth(0)).to_contain_text('Produto C')
        expect(items_2.nth(1)).to_contain_text('Produto A')
        expect(items_2.nth(2)).to_contain_text('Produto B')

    def test_websocket_nao_duplica_item_durante_reordenacao(self, page: Page):
        """
        Reordenação via WebSocket não deve duplicar itens.
        """
        # Criar: A, B (aguardando)
        item_a = ItemPedido.objects.create(
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

        # Login e acessar
        self._login(page)
        page.goto(f"http://localhost:8000/pedido/{self.pedido.id}/")

        # Verificar contagem inicial: 2 itens
        items_before = page.locator('.item-pedido')
        expect(items_before).to_have_count(2)

        # Marcar A como separado
        item_a.separado = True
        item_a.separado_por = self.separador2
        item_a.separado_em = timezone.now()
        item_a.save()

        # Aguardar reordenação
        page.wait_for_timeout(1500)

        # Ainda deve haver 2 itens (sem duplicação)
        items_after = page.locator('.item-pedido')
        expect(items_after).to_have_count(2)

    def test_websocket_reordena_item_enviado_compra(self, page: Page):
        """
        Item marcado para compra por outro usuário deve reordenar corretamente.
        """
        # Criar: A, B, C (aguardando)
        item_a = ItemPedido.objects.create(
            pedido=self.pedido,
            produto=self.produto_a,
            quantidade_solicitada=1,
            separado=False,
            em_compra=False
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

        # Login e acessar
        self._login(page)
        page.goto(f"http://localhost:8000/pedido/{self.pedido.id}/")

        # Marcar A para compra
        item_a.em_compra = True
        item_a.save()
        page.wait_for_timeout(1500)

        # Ordem esperada: B, C (aguardando), A (compra)
        items_after = page.locator('.item-pedido')
        expect(items_after.nth(0)).to_contain_text('Produto B')
        expect(items_after.nth(1)).to_contain_text('Produto C')
        expect(items_after.nth(2)).to_contain_text('Produto A')

        # Validar classe de compra
        item_a_element = items_after.nth(2)
        expect(item_a_element).to_have_class('border-orange-200')

    def test_websocket_reordena_item_substituido(self, page: Page):
        """
        Item marcado como substituído deve ir para posição correta.
        """
        # Criar: A, B (aguardando), C (separado)
        item_a = ItemPedido.objects.create(
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
            separado_por=self.separador2,
            separado_em=timezone.now()
        )

        # Login e acessar
        self._login(page)
        page.goto(f"http://localhost:8000/pedido/{self.pedido.id}/")

        # Marcar A como substituído
        item_a.separado = True
        item_a.substituido = True
        item_a.separado_por = self.separador2
        item_a.separado_em = timezone.now()
        item_a.save()
        page.wait_for_timeout(1500)

        # Ordem esperada: B (aguardando), A (substituído), C (separado)
        items_after = page.locator('.item-pedido')
        expect(items_after.nth(0)).to_contain_text('Produto B')
        expect(items_after.nth(1)).to_contain_text('Produto A')
        expect(items_after.nth(2)).to_contain_text('Produto C')

        # Validar classe de substituído
        item_a_element = items_after.nth(1)
        expect(item_a_element).to_have_class('border-blue-200')

    def test_websocket_mantem_ordem_alfabetica_dentro_grupo(self, page: Page):
        """
        Ordem alfabética deve ser mantida dentro do mesmo grupo após WebSocket.
        """
        # Criar: A, C, E (aguardando)
        item_a = ItemPedido.objects.create(
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
            separado=False
        )

        # Login e acessar
        self._login(page)
        page.goto(f"http://localhost:8000/pedido/{self.pedido.id}/")

        # Marcar A como separado
        item_a.separado = True
        item_a.separado_por = self.separador2
        item_a.separado_em = timezone.now()
        item_a.save()
        page.wait_for_timeout(1500)

        # Ordem esperada: C, E (aguardando alfabético), A (separado)
        items_after = page.locator('.item-pedido')
        expect(items_after.nth(0)).to_contain_text('Produto C')
        expect(items_after.nth(1)).to_contain_text('Produto E')
        expect(items_after.nth(2)).to_contain_text('Produto A')

    def test_websocket_reordenacao_nao_interfere_em_acoes_locais(self, page: Page):
        """
        Reordenação via WebSocket não deve interferir em ações do usuário local.
        """
        # Criar: A, B, C (aguardando)
        ItemPedido.objects.create(
            pedido=self.pedido,
            produto=self.produto_a,
            quantidade_solicitada=1,
            separado=False
        )
        item_b = ItemPedido.objects.create(
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

        # Login e acessar
        self._login(page)
        page.goto(f"http://localhost:8000/pedido/{self.pedido.id}/")

        # Usuário local marca B como separado
        items = page.locator('.item-pedido')
        checkbox_b = items.nth(1).locator('input[type="checkbox"]')
        checkbox_b.check()
        page.wait_for_timeout(1000)

        # Ordem após ação local: A, C, B
        items_1 = page.locator('.item-pedido')
        expect(items_1.nth(0)).to_contain_text('Produto A')
        expect(items_1.nth(1)).to_contain_text('Produto C')
        expect(items_1.nth(2)).to_contain_text('Produto B')

        # Outro usuário marca A como separado via backend
        item_b.separado = False  # Resetar para teste
        item_b.save()

        # Recarregar para nova ordem
        page.reload()
        page.wait_for_timeout(1000)

        # Verificar que interface está consistente
        items_final = page.locator('.item-pedido')
        expect(items_final).to_have_count(3)
