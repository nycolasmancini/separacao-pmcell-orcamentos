# -*- coding: utf-8 -*-
"""
Testes de Integração E2E Completos para Lista Corrida (Fase 39h).

Valida cenários complexos envolvendo:
- Múltiplos usuários operando simultaneamente
- Transições de estado completas (aguardando → compra → separado → substituído)
- Sincronização WebSocket com múltiplos eventos
- Consistência da UI após sequências complexas de ações
"""

import pytest
import time
from playwright.sync_api import Page, expect, BrowserContext
from django.utils import timezone
from core.models import Pedido, ItemPedido, Produto, Usuario


@pytest.mark.django_db
class TestIntegracaoCompletaListaCorrida:
    """Testes E2E de integração completa."""

    @pytest.fixture(autouse=True)
    def setup(self, db):
        """Setup que roda antes de cada teste."""
        # Criar usuários
        self.vendedor = Usuario.objects.create(
            numero_login="001",
            nome="Vendedor Teste",
            tipo="VENDEDOR",
            ativo=True
        )
        self.vendedor.set_password("1234")
        self.vendedor.save()

        self.separador1 = Usuario.objects.create(
            numero_login="002",
            nome="Separador 1",
            tipo="SEPARADOR",
            ativo=True
        )
        self.separador1.set_password("1234")
        self.separador1.save()

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

        # Criar 6 produtos
        self.produtos = []
        for letra in ['A', 'B', 'C', 'D', 'E', 'F']:
            produto = Produto.objects.create(
                codigo=f'PROD-{letra}',
                descricao=f'Produto {letra}',
                quantidade=10,
                valor_unitario=100.00,
                valor_total=1000.00
            )
            self.produtos.append(produto)

    def _login(self, page: Page, numero_login: str):
        """Helper para fazer login."""
        page.goto("http://localhost:8000/login/")
        page.fill('input[name="numero_login"]', numero_login)
        page.fill('input[name="password"]', "1234")
        page.click('button[type="submit"]')
        page.wait_for_url("http://localhost:8000/painel/", timeout=5000)

    def test_cenario_completo_dois_separadores_simultaneos(self, browser_context: BrowserContext):
        """
        Cenário complexo com 2 separadores trabalhando simultaneamente.

        Fluxo:
        1. Criar 6 itens (A, B, C, D, E, F) todos aguardando
        2. Separador 1 marca A e B como separados
        3. Separador 2 marca C para compra e D como separado
        4. Separador 1 marca E como substituído
        5. Validar ordem final: F (aguardando), C (compra), E (substituído), A, B, D (separados)
        """
        # Criar todos os itens aguardando
        itens = []
        for produto in self.produtos:
            item = ItemPedido.objects.create(
                pedido=self.pedido,
                produto=produto,
                quantidade_solicitada=1,
                separado=False,
                em_compra=False
            )
            itens.append(item)

        # Abrir 2 páginas (2 separadores)
        page1 = browser_context.new_page()
        page2 = browser_context.new_page()

        # Login como separador 1 (página 1)
        self._login(page1, "002")
        page1.goto(f"http://localhost:8000/pedido/{self.pedido.id}/")

        # Login como separador 2 (página 2)
        self._login(page2, "003")
        page2.goto(f"http://localhost:8000/pedido/{self.pedido.id}/")

        # Validar ordem inicial em ambas as páginas: A, B, C, D, E, F
        for page in [page1, page2]:
            items = page.locator('.item-pedido')
            expect(items.nth(0)).to_contain_text('Produto A')
            expect(items.nth(5)).to_contain_text('Produto F')

        # Separador 1: Marcar A como separado
        items_p1 = page1.locator('.item-pedido')
        checkbox_a = items_p1.nth(0).locator('input[type="checkbox"]')
        checkbox_a.check()
        time.sleep(1.5)

        # Separador 2: Marcar C para compra
        items_p2 = page2.locator('.item-pedido')
        btn_compra_c = items_p2.nth(2).locator('button:has-text("Enviar p/ Compra")')
        btn_compra_c.click()
        time.sleep(1.5)

        # Separador 1: Marcar B como separado
        items_p1_2 = page1.locator('.item-pedido')
        checkbox_b = items_p1_2.nth(0).locator('input[type="checkbox"]')  # B agora é o primeiro
        checkbox_b.check()
        time.sleep(1.5)

        # Separador 2: Marcar D como separado
        items_p2_2 = page2.locator('.item-pedido')
        checkbox_d = items_p2_2.nth(1).locator('input[type="checkbox"]')  # D agora é segundo aguardando
        checkbox_d.check()
        time.sleep(1.5)

        # Separador 1: Marcar E como substituído (separado + substituído flag)
        # Simular via backend para garantir ambos os flags
        itens[4].separado = True
        itens[4].substituido = True
        itens[4].separado_por = self.separador1
        itens[4].separado_em = timezone.now()
        itens[4].save()
        time.sleep(2)

        # Ordem final esperada:
        # Aguardando: F (alfabético)
        # Compra: C
        # Substituído: E
        # Separados: A, B, D (alfabético)

        # Validar em página 1 (separador 1)
        items_final_p1 = page1.locator('.item-pedido')
        expect(items_final_p1.nth(0)).to_contain_text('Produto F')  # Aguardando
        expect(items_final_p1.nth(1)).to_contain_text('Produto C')  # Compra
        expect(items_final_p1.nth(2)).to_contain_text('Produto E')  # Substituído
        expect(items_final_p1.nth(3)).to_contain_text('Produto A')  # Separado
        expect(items_final_p1.nth(4)).to_contain_text('Produto B')  # Separado
        expect(items_final_p1.nth(5)).to_contain_text('Produto D')  # Separado

        # Validar em página 2 (separador 2)
        items_final_p2 = page2.locator('.item-pedido')
        expect(items_final_p2.nth(0)).to_contain_text('Produto F')
        expect(items_final_p2.nth(1)).to_contain_text('Produto C')
        expect(items_final_p2.nth(2)).to_contain_text('Produto E')
        expect(items_final_p2.nth(3)).to_contain_text('Produto A')
        expect(items_final_p2.nth(4)).to_contain_text('Produto B')
        expect(items_final_p2.nth(5)).to_contain_text('Produto D')

        page1.close()
        page2.close()

    def test_fluxo_completo_single_item_todos_estados(self, page: Page):
        """
        Fluxo completo de um item passando por todos os estados.

        Fluxo:
        1. Item A criado (aguardando)
        2. Marcado para compra
        3. Desmarcado de compra (volta para aguardando)
        4. Marcado como separado
        5. Marcado como substituído
        6. Validar transições e posições corretas
        """
        # Criar 3 itens: A (testar), B, C (referência)
        item_a = ItemPedido.objects.create(
            pedido=self.pedido,
            produto=self.produtos[0],
            quantidade_solicitada=1,
            separado=False,
            em_compra=False
        )
        ItemPedido.objects.create(
            pedido=self.pedido,
            produto=self.produtos[1],
            quantidade_solicitada=1,
            separado=False
        )
        ItemPedido.objects.create(
            pedido=self.pedido,
            produto=self.produtos[2],
            quantidade_solicitada=1,
            separado=True,
            separado_por=self.separador1,
            separado_em=timezone.now()
        )

        # Login e acessar
        self._login(page, "002")
        page.goto(f"http://localhost:8000/pedido/{self.pedido.id}/")

        # Estado 1: A aguardando (ordem: A, B, C)
        items_1 = page.locator('.item-pedido')
        expect(items_1.nth(0)).to_contain_text('Produto A')
        expect(items_1.nth(0)).to_have_class('border-gray-200')

        # Estado 2: A → compra (ordem: B, A, C)
        btn_compra = items_1.nth(0).locator('button:has-text("Enviar p/ Compra")')
        btn_compra.click()
        time.sleep(1.5)

        items_2 = page.locator('.item-pedido')
        expect(items_2.nth(0)).to_contain_text('Produto B')
        expect(items_2.nth(1)).to_contain_text('Produto A')
        expect(items_2.nth(1)).to_have_class('border-orange-200')

        # Estado 3: A → aguardando (desmarcar compra via backend)
        item_a.em_compra = False
        item_a.save()
        time.sleep(1.5)

        items_3 = page.locator('.item-pedido')
        expect(items_3.nth(0)).to_contain_text('Produto A')
        expect(items_3.nth(0)).to_have_class('border-gray-200')

        # Estado 4: A → separado (ordem: B, A, C)
        checkbox_a = items_3.nth(0).locator('input[type="checkbox"]')
        checkbox_a.check()
        time.sleep(1.5)

        items_4 = page.locator('.item-pedido')
        expect(items_4.nth(0)).to_contain_text('Produto B')
        expect(items_4.nth(1)).to_contain_text('Produto A')
        expect(items_4.nth(1)).to_have_class('border-green-200')

        # Estado 5: A → substituído
        item_a.substituido = True
        item_a.save()
        time.sleep(1.5)

        items_5 = page.locator('.item-pedido')
        # Ordem: B (aguardando), A (substituído), C (separado)
        expect(items_5.nth(0)).to_contain_text('Produto B')
        expect(items_5.nth(1)).to_contain_text('Produto A')
        expect(items_5.nth(1)).to_have_class('border-blue-200')
        expect(items_5.nth(2)).to_contain_text('Produto C')

    def test_ordem_alfabetica_mantida_em_todos_grupos(self, page: Page):
        """
        Validar que ordem alfabética é mantida dentro de cada grupo após múltiplas operações.
        """
        # Criar itens fora de ordem: F, D, B, E, C, A
        produtos_ordem = [5, 3, 1, 4, 2, 0]  # Índices embaralhados
        for idx in produtos_ordem:
            ItemPedido.objects.create(
                pedido=self.pedido,
                produto=self.produtos[idx],
                quantidade_solicitada=1,
                separado=False
            )

        # Login e acessar
        self._login(page, "002")
        page.goto(f"http://localhost:8000/pedido/{self.pedido.id}/")

        # Validar ordem alfabética inicial: A, B, C, D, E, F
        items_inicial = page.locator('.item-pedido')
        for i, letra in enumerate(['A', 'B', 'C', 'D', 'E', 'F']):
            expect(items_inicial.nth(i)).to_contain_text(f'Produto {letra}')

        # Marcar B, D, F como separados (ordem inversa para complexidade)
        for idx in [5, 3, 1]:  # F, D, B
            items = page.locator('.item-pedido')
            # Encontrar item por texto
            item = items.filter(has_text=f"Produto {chr(65 + idx)}")
            checkbox = item.locator('input[type="checkbox"]').first
            checkbox.check()
            time.sleep(1.2)

        # Ordem final esperada:
        # Aguardando: A, C, E
        # Separados: B, D, F (alfabético)
        items_final = page.locator('.item-pedido')
        expect(items_final.nth(0)).to_contain_text('Produto A')
        expect(items_final.nth(1)).to_contain_text('Produto C')
        expect(items_final.nth(2)).to_contain_text('Produto E')
        expect(items_final.nth(3)).to_contain_text('Produto B')
        expect(items_final.nth(4)).to_contain_text('Produto D')
        expect(items_final.nth(5)).to_contain_text('Produto F')

    def test_progresso_atualizado_corretamente_apos_reordenacoes(self, page: Page):
        """
        Validar que progresso (X/Y) é atualizado corretamente após reordenações.
        """
        # Criar 4 itens
        for i in range(4):
            ItemPedido.objects.create(
                pedido=self.pedido,
                produto=self.produtos[i],
                quantidade_solicitada=1,
                separado=False
            )

        # Login e acessar
        self._login(page, "002")
        page.goto(f"http://localhost:8000/pedido/{self.pedido.id}/")

        # Validar progresso inicial: 0/4 (0%)
        contador = page.locator('#contador-itens')
        expect(contador).to_contain_text('(0/4)')

        # Marcar A como separado
        items = page.locator('.item-pedido')
        checkbox_a = items.nth(0).locator('input[type="checkbox"]')
        checkbox_a.check()
        time.sleep(1.5)

        # Validar progresso: 1/4 (25%)
        expect(contador).to_contain_text('(1/4)')
        progresso = page.locator('#progresso-percentual')
        expect(progresso).to_contain_text('25%')

        # Marcar B como separado
        items_2 = page.locator('.item-pedido')
        checkbox_b = items_2.nth(0).locator('input[type="checkbox"]')
        checkbox_b.check()
        time.sleep(1.5)

        # Validar progresso: 2/4 (50%)
        expect(contador).to_contain_text('(2/4)')
        expect(progresso).to_contain_text('50%')

        # Marcar C e D como separados
        for _ in range(2):
            items_n = page.locator('.item-pedido')
            checkbox = items_n.nth(0).locator('input[type="checkbox"]')
            checkbox.check()
            time.sleep(1.5)

        # Validar progresso: 4/4 (100%)
        expect(contador).to_contain_text('(4/4)')
        expect(progresso).to_contain_text('100%')

        # Botão finalizar deve aparecer
        botao_finalizar = page.locator('#container-botao-finalizar')
        expect(botao_finalizar).to_be_visible()

    def test_consistencia_apos_refresh_durante_operacoes(self, page: Page):
        """
        Validar que após refresh da página, a ordem e estados estão corretos.
        """
        # Criar 3 itens
        for i in range(3):
            ItemPedido.objects.create(
                pedido=self.pedido,
                produto=self.produtos[i],
                quantidade_solicitada=1,
                separado=False
            )

        # Login e acessar
        self._login(page, "002")
        page.goto(f"http://localhost:8000/pedido/{self.pedido.id}/")

        # Marcar A como separado
        items = page.locator('.item-pedido')
        checkbox_a = items.nth(0).locator('input[type="checkbox"]')
        checkbox_a.check()
        time.sleep(1.5)

        # Ordem esperada: B, C, A
        items_before = page.locator('.item-pedido')
        expect(items_before.nth(0)).to_contain_text('Produto B')
        expect(items_before.nth(2)).to_contain_text('Produto A')

        # Refresh da página
        page.reload()
        page.wait_for_selector('.item-pedido')

        # Validar que ordem persiste após refresh
        items_after = page.locator('.item-pedido')
        expect(items_after.nth(0)).to_contain_text('Produto B')
        expect(items_after.nth(1)).to_contain_text('Produto C')
        expect(items_after.nth(2)).to_contain_text('Produto A')

        # Validar estado visual de A
        item_a = items_after.nth(2)
        expect(item_a).to_have_class('border-green-200')

    def test_sem_duplicacao_em_cenario_de_stress(self, page: Page):
        """
        Stress test: marcar múltiplos itens rapidamente e validar sem duplicação.
        """
        # Criar 5 itens
        for i in range(5):
            ItemPedido.objects.create(
                pedido=self.pedido,
                produto=self.produtos[i],
                quantidade_solicitada=1,
                separado=False
            )

        # Login e acessar
        self._login(page, "002")
        page.goto(f"http://localhost:8000/pedido/{self.pedido.id}/")

        # Marcar todos rapidamente (sem esperar animações completarem)
        for i in range(5):
            items = page.locator('.item-pedido')
            checkbox = items.nth(0).locator('input[type="checkbox"]')
            checkbox.check()
            time.sleep(0.3)  # Tempo muito curto para stress

        # Aguardar todas as animações
        time.sleep(3)

        # Validar que ainda há exatamente 5 itens
        items_final = page.locator('.item-pedido')
        expect(items_final).to_have_count(5)

        # Validar que todos estão separados
        for i in range(5):
            expect(items_final.nth(i)).to_have_class('border-green-200')
