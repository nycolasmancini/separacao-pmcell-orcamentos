# -*- coding: utf-8 -*-
"""
Testes E2E para validar o cálculo correto da porcentagem de separação.

A porcentagem deve ser calculada como:
(itens separados + itens substituídos) / (total de itens) * 100

Testes cobrem:
1. Porcentagem com apenas itens separados
2. Porcentagem com apenas itens substituídos
3. Porcentagem com mix de separados e substituídos
4. Porcentagem ao desmarcar item separado
5. Atualização em tempo real via WebSocket
"""

import pytest
from playwright.sync_api import Page, expect
from django.test import LiveServerTestCase
from core.models import Usuario, Pedido, ItemPedido, Produto
from core.domain.pedido.value_objects import Logistica, Embalagem, StatusPedido


class TestPorcentagemSeparacao(LiveServerTestCase):
    """Testes E2E para validar cálculo de porcentagem de separação."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Criar usuário para autenticação
        cls.usuario = Usuario.objects.create_user(
            numero_login=1234,
            pin='1234',
            nome='Testador',
            tipo='SEPARADOR'
        )

        # Criar vendedor
        cls.vendedor = Usuario.objects.create_user(
            numero_login=5678,
            pin='5678',
            nome='Vendedor Teste',
            tipo='VENDEDOR'
        )

    def setUp(self):
        """Setup executado antes de cada teste."""
        # Criar produtos de teste
        self.produto1 = Produto.objects.create(
            codigo='PROD001',
            descricao='Produto Teste 1',
            preco_venda=100.0
        )
        self.produto2 = Produto.objects.create(
            codigo='PROD002',
            descricao='Produto Teste 2',
            preco_venda=200.0
        )
        self.produto3 = Produto.objects.create(
            codigo='PROD003',
            descricao='Produto Teste 3',
            preco_venda=300.0
        )
        self.produto4 = Produto.objects.create(
            codigo='PROD004',
            descricao='Produto Teste 4',
            preco_venda=400.0
        )

        # Criar pedido de teste
        self.pedido = Pedido.objects.create(
            numero_orcamento='TEST001',
            codigo_cliente='CLI001',
            nome_cliente='Cliente Teste',
            vendedor=self.vendedor,
            data='01/01/2025',
            logistica=Logistica.RETIRA_LOJA.value,
            embalagem=Embalagem.CAIXA.value,
            status=StatusPedido.EM_SEPARACAO.value
        )

        # Criar 4 itens do pedido
        self.item1 = ItemPedido.objects.create(
            pedido=self.pedido,
            produto=self.produto1,
            quantidade_solicitada=10
        )
        self.item2 = ItemPedido.objects.create(
            pedido=self.pedido,
            produto=self.produto2,
            quantidade_solicitada=5
        )
        self.item3 = ItemPedido.objects.create(
            pedido=self.pedido,
            produto=self.produto3,
            quantidade_solicitada=8
        )
        self.item4 = ItemPedido.objects.create(
            pedido=self.pedido,
            produto=self.produto4,
            quantidade_solicitada=3
        )

    def fazer_login(self, page: Page):
        """Realiza login no sistema."""
        page.goto(f'{self.live_server_url}/login/')
        page.fill('input[name="numero_login"]', '1234')
        page.fill('input[name="pin"]', '1234')
        page.click('button[type="submit"]')
        # Aguardar redirecionamento para dashboard
        page.wait_for_url(f'{self.live_server_url}/dashboard/')

    def obter_porcentagem_dashboard(self, page: Page) -> int:
        """Obtém a porcentagem do card do pedido no dashboard."""
        card = page.locator(f'[data-pedido-id="{self.pedido.id}"]')
        progresso_text = card.locator('.progress-text').text_content()
        return int(progresso_text.replace('%', ''))

    def obter_porcentagem_detalhe(self, page: Page) -> int:
        """Obtém a porcentagem na página de detalhes do pedido."""
        progresso_text = page.locator('.progress-text').text_content()
        return int(progresso_text.replace('%', ''))

    def test_porcentagem_apenas_itens_separados(self):
        """
        Testa cálculo de porcentagem com apenas itens separados (sem substituídos).

        Cenário: 2 de 4 itens separados = 50%
        """
        self.fazer_login(page)

        # Ir para detalhes do pedido
        page.goto(f'{self.live_server_url}/pedidos/{self.pedido.id}/')

        # Marcar 2 itens como separados (50%)
        page.click(f'input[data-item-id="{self.item1.id}"]')
        page.wait_for_timeout(500)  # Aguardar atualização
        page.click(f'input[data-item-id="{self.item2.id}"]')
        page.wait_for_timeout(500)

        # Verificar porcentagem = 50%
        progresso = self.obter_porcentagem_detalhe(page)
        assert progresso == 50, f"Esperado 50%, obtido {progresso}%"

        # Voltar ao dashboard e verificar
        page.goto(f'{self.live_server_url}/dashboard/')
        progresso_dashboard = self.obter_porcentagem_dashboard(page)
        assert progresso_dashboard == 50, f"Dashboard: esperado 50%, obtido {progresso_dashboard}%"

    @pytest.mark.playwright
    def test_porcentagem_apenas_itens_substituidos(self, page: Page):
        """
        Testa cálculo de porcentagem com apenas itens substituídos.

        Cenário: 2 de 4 itens substituídos = 50%
        """
        self.fazer_login(page)
        page.goto(f'{self.live_server_url}/pedidos/{self.pedido.id}/')

        # Substituir 2 itens (50%)
        # Clicar no botão "Substituir" do item 1
        page.click(f'button[data-action="substituir"][data-item-id="{self.item1.id}"]')
        page.fill('input[name="produto_substituto"]', 'Produto Alternativo 1')
        page.click('button[type="submit"]')
        page.wait_for_timeout(500)

        # Substituir item 2
        page.click(f'button[data-action="substituir"][data-item-id="{self.item2.id}"]')
        page.fill('input[name="produto_substituto"]', 'Produto Alternativo 2')
        page.click('button[type="submit"]')
        page.wait_for_timeout(500)

        # Verificar porcentagem = 50%
        progresso = self.obter_porcentagem_detalhe(page)
        assert progresso == 50, f"Esperado 50%, obtido {progresso}%"

    @pytest.mark.playwright
    def test_porcentagem_mix_separados_e_substituidos(self, page: Page):
        """
        Testa cálculo com mix de itens separados e substituídos.

        Cenário: 2 separados + 1 substituído = 3 de 4 = 75%
        """
        self.fazer_login(page)
        page.goto(f'{self.live_server_url}/pedidos/{self.pedido.id}/')

        # Marcar 2 como separados
        page.click(f'input[data-item-id="{self.item1.id}"]')
        page.wait_for_timeout(500)
        page.click(f'input[data-item-id="{self.item2.id}"]')
        page.wait_for_timeout(500)

        # Substituir 1 item
        page.click(f'button[data-action="substituir"][data-item-id="{self.item3.id}"]')
        page.fill('input[name="produto_substituto"]', 'Produto Alternativo 3')
        page.click('button[type="submit"]')
        page.wait_for_timeout(500)

        # Verificar porcentagem = 75% (3 de 4)
        progresso = self.obter_porcentagem_detalhe(page)
        assert progresso == 75, f"Esperado 75%, obtido {progresso}%"

    @pytest.mark.playwright
    def test_porcentagem_ao_desmarcar_item(self, page: Page):
        """
        Testa se porcentagem diminui corretamente ao desmarcar item.

        Cenário:
        - Marcar 2 itens = 50%
        - Desmarcar 1 item = 25%
        """
        self.fazer_login(page)
        page.goto(f'{self.live_server_url}/pedidos/{self.pedido.id}/')

        # Marcar 2 itens (50%)
        page.click(f'input[data-item-id="{self.item1.id}"]')
        page.wait_for_timeout(500)
        page.click(f'input[data-item-id="{self.item2.id}"]')
        page.wait_for_timeout(500)

        # Verificar 50%
        progresso = self.obter_porcentagem_detalhe(page)
        assert progresso == 50, f"Esperado 50%, obtido {progresso}%"

        # Desmarcar 1 item
        page.click(f'input[data-item-id="{self.item1.id}"]')
        page.wait_for_timeout(500)

        # Verificar 25% (1 de 4)
        progresso = self.obter_porcentagem_detalhe(page)
        assert progresso == 25, f"Após desmarcar: esperado 25%, obtido {progresso}%"

    @pytest.mark.playwright
    def test_porcentagem_100_com_todos_separados(self, page: Page):
        """
        Testa se atinge 100% quando todos os itens são separados.
        """
        self.fazer_login(page)
        page.goto(f'{self.live_server_url}/pedidos/{self.pedido.id}/')

        # Marcar todos os 4 itens
        page.click(f'input[data-item-id="{self.item1.id}"]')
        page.wait_for_timeout(500)
        page.click(f'input[data-item-id="{self.item2.id}"]')
        page.wait_for_timeout(500)
        page.click(f'input[data-item-id="{self.item3.id}"]')
        page.wait_for_timeout(500)
        page.click(f'input[data-item-id="{self.item4.id}"]')
        page.wait_for_timeout(500)

        # Verificar 100%
        progresso = self.obter_porcentagem_detalhe(page)
        assert progresso == 100, f"Esperado 100%, obtido {progresso}%"

        # Botão de finalizar deve estar visível
        expect(page.locator('button:has-text("Finalizar Pedido")')).to_be_visible()

    @pytest.mark.playwright
    def test_porcentagem_100_com_mix_completo(self, page: Page):
        """
        Testa se atinge 100% com mix de separados e substituídos.

        Cenário: 3 separados + 1 substituído = 4 de 4 = 100%
        """
        self.fazer_login(page)
        page.goto(f'{self.live_server_url}/pedidos/{self.pedido.id}/')

        # Marcar 3 como separados
        page.click(f'input[data-item-id="{self.item1.id}"]')
        page.wait_for_timeout(500)
        page.click(f'input[data-item-id="{self.item2.id}"]')
        page.wait_for_timeout(500)
        page.click(f'input[data-item-id="{self.item3.id}"]')
        page.wait_for_timeout(500)

        # Substituir 1 item
        page.click(f'button[data-action="substituir"][data-item-id="{self.item4.id}"]')
        page.fill('input[name="produto_substituto"]', 'Produto Alternativo 4')
        page.click('button[type="submit"]')
        page.wait_for_timeout(500)

        # Verificar 100%
        progresso = self.obter_porcentagem_detalhe(page)
        assert progresso == 100, f"Esperado 100%, obtido {progresso}%"

        # Botão de finalizar deve estar visível
        expect(page.locator('button:has-text("Finalizar Pedido")')).to_be_visible()

    @pytest.mark.playwright
    def test_atualizacao_tempo_real_dashboard(self, page: Page):
        """
        Testa se a porcentagem é atualizada em tempo real no dashboard
        quando item é separado em outra aba/sessão.

        Usa WebSocket para atualização em tempo real.
        """
        self.fazer_login(page)

        # Abrir dashboard
        page.goto(f'{self.live_server_url}/dashboard/')

        # Verificar porcentagem inicial = 0%
        progresso_inicial = self.obter_porcentagem_dashboard(page)
        assert progresso_inicial == 0, f"Progresso inicial: esperado 0%, obtido {progresso_inicial}%"

        # Marcar item diretamente no banco (simula outra sessão)
        from django.utils import timezone
        self.item1.separado = True
        self.item1.quantidade_separada = self.item1.quantidade_solicitada
        self.item1.separado_por = self.usuario
        self.item1.separado_em = timezone.now()
        self.item1.save()

        # Enviar evento WebSocket manualmente para simular atualização
        from channels.layers import get_channel_layer
        from asgiref.sync import async_to_sync
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            'dashboard',
            {
                'type': 'item_separado',
                'pedido_id': self.pedido.id,
                'progresso': 25,  # 1 de 4 = 25%
                'itens_separados': 1,
                'total_itens': 4,
                'item_id': self.item1.id
            }
        )

        # Aguardar atualização via WebSocket (máx 3s)
        page.wait_for_timeout(3000)

        # Verificar se porcentagem foi atualizada para 25%
        progresso_atualizado = self.obter_porcentagem_dashboard(page)
        assert progresso_atualizado == 25, f"Após WebSocket: esperado 25%, obtido {progresso_atualizado}%"


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--headed'])
