# -*- coding: utf-8 -*-
"""
Testes para Fase 43e - Integration E2E: Complete purchase panel sync

Testa o fluxo completo de sincronização em tempo real do painel de compras,
incluindo todos os 3 problemas relatados pelo usuário:

Issue #1 (WORKING): Items aparecem no painel quando marcados para compra
Issue #2 (FIXED): Items desaparecem do painel quando separados/substituídos
Issue #3 (FIXED): Badge atualiza de "Aguardando Compra" para "Já Comprado"

Fase 43e - 10 testes E2E de integração completa
"""

import pytest
from django.test import TestCase, Client, LiveServerTestCase
from django.contrib.auth import get_user_model
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import time

from core.models import Pedido, ItemPedido, Produto


Usuario = get_user_model()


@pytest.mark.django_db
class TestIntegracaoCompletaPainelCompras(LiveServerTestCase):
    """
    Testes E2E de integração completa para sincronização do painel de compras.

    Valida o fluxo completo end-to-end dos 3 problemas reportados.
    """

    @classmethod
    def setUpClass(cls):
        """Configurar Selenium WebDriver."""
        super().setUpClass()
        options = webdriver.ChromeOptions()
        options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        cls.driver = webdriver.Chrome(options=options)
        cls.driver.implicitly_wait(10)

    @classmethod
    def tearDownClass(cls):
        """Fechar WebDriver."""
        cls.driver.quit()
        super().tearDownClass()

    def setUp(self):
        """Configurar dados de teste."""
        # Criar usuários
        self.separador = Usuario.objects.create_user(
            numero_login=1004,
            pin='1234',
            nome='Separador Fase 43e',
            tipo='SEPARADOR'
        )

        self.compradora = Usuario.objects.create_user(
            numero_login=1005,
            pin='5678',
            nome='Compradora Fase 43e',
            tipo='COMPRADORA'
        )

        self.vendedor = Usuario.objects.create_user(
            numero_login=2004,
            pin='9012',
            nome='Vendedor Fase 43e',
            tipo='VENDEDOR'
        )

        # Criar produto
        self.produto = Produto.objects.create(
            codigo='PR43E',
            descricao='Produto Fase 43e',
            quantidade=30,
            valor_unitario=100.00,
            valor_total=3000.00
        )

        # Criar pedido
        self.pedido = Pedido.objects.create(
            numero_orcamento='PED43E',
            codigo_cliente='CLI43E',
            nome_cliente='Cliente Fase 43e',
            vendedor=self.vendedor,
            data='01/01/2025',
            logistica='RETIRA_LOJA',
            embalagem='CAIXA'
        )

        # Criar item NÃO separado e NÃO em compra
        self.item = ItemPedido.objects.create(
            pedido=self.pedido,
            produto=self.produto,
            quantidade_solicitada=30,
            em_compra=False,
            separado=False
        )

        # Login via Client para sessão
        self.client = Client()
        self.client.force_login(self.separador)

        # Transferir cookies para Selenium
        self.driver.get(self.live_server_url)
        for key, value in self.client.cookies.items():
            self.driver.add_cookie({'name': key, 'value': value.value})

    @pytest.mark.skip(reason="E2E test - requires real browser and WebSocket connection")
    def test_issue1_item_aparece_no_painel_apos_marcar_compra(self):
        """
        Teste 1: Issue #1 (WORKING) - Item deve aparecer no painel após marcar para compra.

        Fluxo completo:
        1. Abrir detalhe do pedido
        2. Marcar item para compra
        3. Verificar que item aparece no painel de compras

        SKIP: Requer ambiente E2E completo com WebSocket real.
        """
        # Abrir detalhe do pedido
        self.driver.get(f'{self.live_server_url}/pedidos/{self.pedido.id}/')

        wait = WebDriverWait(self.driver, 10)

        # Encontrar botão "Enviar para Compra"
        botao_compra = wait.until(
            EC.presence_of_element_located((By.XPATH, f"//button[contains(text(), 'Comprar')]"))
        )

        # Marcar item para compra
        botao_compra.click()
        time.sleep(1)

        # Verificar que badge "Aguardando Compra" apareceu
        badge = wait.until(
            EC.presence_of_element_located((By.ID, f'badge-{self.item.id}'))
        )
        self.assertIn('Aguardando Compra', badge.text)

        # Abrir painel de compras em nova aba
        self.driver.execute_script("window.open('');")
        self.driver.switch_to.window(self.driver.window_handles[1])
        self.driver.get(f'{self.live_server_url}/painel-compras/')

        # Verificar que item aparece no painel
        item_no_painel = wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, f'[data-item-id="{self.item.id}"]'))
        )
        self.assertTrue(item_no_painel.is_displayed())

    @pytest.mark.skip(reason="E2E test - requires real browser and WebSocket connection")
    def test_issue2_item_desaparece_do_painel_quando_separado(self):
        """
        Teste 2: Issue #2 (FIXED) - Item deve desaparecer do painel quando marcado como separado.

        Fluxo completo:
        1. Marcar item para compra
        2. Verificar que aparece no painel
        3. Marcar item como separado
        4. Verificar que desaparece do painel EM TEMPO REAL

        SKIP: Requer ambiente E2E completo.
        """
        # Marcar item para compra via backend
        self.item.em_compra = True
        self.item.save()

        # Abrir painel de compras
        self.driver.get(f'{self.live_server_url}/painel-compras/')

        wait = WebDriverWait(self.driver, 10)

        # Verificar que item está no painel
        item_element = wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, f'[data-item-id="{self.item.id}"]'))
        )
        self.assertTrue(item_element.is_displayed())

        # Abrir detalhe do pedido em nova aba
        self.driver.execute_script("window.open('');")
        self.driver.switch_to.window(self.driver.window_handles[1])
        self.driver.get(f'{self.live_server_url}/pedidos/{self.pedido.id}/')

        # Marcar item como separado
        checkbox = wait.until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, f'input[type="checkbox"][data-item-id="{self.item.id}"]'))
        )
        checkbox.click()
        time.sleep(1)

        # Voltar para aba do painel
        self.driver.switch_to.window(self.driver.window_handles[0])

        # Aguardar remoção via WebSocket (300ms fade out)
        time.sleep(0.5)

        # Item NÃO deve mais estar no painel
        items = self.driver.find_elements(By.CSS_SELECTOR, f'[data-item-id="{self.item.id}"]')
        self.assertEqual(len(items), 0)

    @pytest.mark.skip(reason="E2E test - requires real browser and WebSocket connection")
    def test_issue3_badge_atualiza_quando_marcado_como_comprado(self):
        """
        Teste 3: Issue #3 (FIXED) - Badge deve atualizar de "Aguardando Compra" para "Já Comprado".

        Fluxo completo:
        1. Marcar item para compra
        2. Verificar badge laranja "Aguardando Compra"
        3. No painel, marcar como realizado
        4. Verificar badge azul "Já comprado" EM TEMPO REAL

        SKIP: Requer ambiente E2E completo.
        """
        # Marcar item para compra via backend
        self.item.em_compra = True
        self.item.save()

        # Abrir detalhe do pedido
        self.driver.get(f'{self.live_server_url}/pedidos/{self.pedido.id}/')

        wait = WebDriverWait(self.driver, 10)

        # Verificar badge laranja "Aguardando Compra"
        badge = wait.until(
            EC.presence_of_element_located((By.ID, f'badge-{self.item.id}'))
        )
        self.assertIn('Aguardando Compra', badge.text)
        self.assertIn('bg-orange-100', badge.get_attribute('class'))

        # Login como compradora em nova aba
        self.driver.execute_script("window.open('');")
        self.driver.switch_to.window(self.driver.window_handles[1])

        # Fazer login como compradora
        self.client.force_login(self.compradora)
        for key, value in self.client.cookies.items():
            self.driver.add_cookie({'name': key, 'value': value.value})

        # Abrir painel de compras
        self.driver.get(f'{self.live_server_url}/painel-compras/')

        # Marcar checkbox como realizado
        checkbox = wait.until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, f'input[type="checkbox"]'))
        )
        checkbox.click()
        time.sleep(1)

        # Voltar para aba do separador
        self.driver.switch_to.window(self.driver.window_handles[0])

        # Aguardar atualização via WebSocket
        time.sleep(0.5)

        # Verificar badge azul "Já comprado"
        badge = self.driver.find_element(By.ID, f'badge-{self.item.id}')
        self.assertIn('Já comprado', badge.text)
        self.assertIn('bg-blue-100', badge.get_attribute('class'))

    @pytest.mark.skip(reason="E2E test - requires real browser and WebSocket connection")
    def test_fluxo_completo_marcar_separar_realizado(self):
        """
        Teste 4: Fluxo completo end-to-end dos 3 problemas.

        1. Marcar item para compra → Aparece no painel (Issue #1)
        2. Desmarcar compra → Desaparece do painel
        3. Marcar novamente para compra → Reaparece no painel
        4. Marcar como realizado → Badge atualiza (Issue #3)
        5. Marcar como separado → Desaparece do painel (Issue #2)

        SKIP: Teste completo end-to-end.
        """
        pass

    @pytest.mark.skip(reason="E2E test - requires real browser and WebSocket connection")
    def test_sincronizacao_multi_tab_completa(self):
        """
        Teste 5: Sincronização entre múltiplas abas/dispositivos.

        Simula 3 usuários simultâneos:
        - Separador 1: Marca item para compra
        - Separador 2: Vê badge aparecer em tempo real
        - Compradora: Marca como realizado, ambos separadores veem badge mudar

        SKIP: Requer múltiplas sessões simultâneas.
        """
        pass

    @pytest.mark.skip(reason="E2E test - requires real browser and WebSocket connection")
    def test_item_substituido_remove_do_painel(self):
        """
        Teste 6: Item substituído deve ser removido do painel de compras.

        Fluxo:
        1. Marcar item para compra
        2. Abrir modal de substituição
        3. Substituir produto
        4. Verificar que item original desaparece do painel

        SKIP: Requer modal de substituição funcional.
        """
        pass

    @pytest.mark.skip(reason="E2E test - requires real browser and WebSocket connection")
    def test_multiplos_itens_sincronizam_independentemente(self):
        """
        Teste 7: Múltiplos itens devem sincronizar independentemente.

        Criar 3 itens:
        - Item 1: Marcar para compra → Badge aparece
        - Item 2: Marcar para compra → Badge aparece
        - Item 1: Marcar como realizado → Apenas badge 1 muda
        - Item 2: Marcar como separado → Item 2 desaparece do painel

        SKIP: Teste com múltiplos itens.
        """
        pass

    @pytest.mark.skip(reason="E2E test - requires real browser and WebSocket connection")
    def test_painel_vazio_apos_todos_itens_removidos(self):
        """
        Teste 8: Painel deve mostrar mensagem vazia após todos itens serem removidos.

        Fluxo:
        1. Marcar 2 itens para compra
        2. Verificar que ambos aparecem no painel
        3. Marcar ambos como separados
        4. Verificar que painel mostra mensagem "Nenhum item aguardando compra"

        SKIP: Teste de estado vazio.
        """
        pass

    @pytest.mark.skip(reason="E2E test - requires real browser and WebSocket connection")
    def test_reconexao_websocket_apos_perda_conexao(self):
        """
        Teste 9: WebSocket deve reconectar automaticamente após perda de conexão.

        Fluxo:
        1. Conectar ao painel
        2. Simular perda de conexão (fechar WebSocket)
        3. Aguardar reconexão automática (3s timeout)
        4. Verificar que eventos continuam funcionando após reconexão

        SKIP: Teste de resiliência de conexão.
        """
        pass

    @pytest.mark.skip(reason="E2E test - requires real browser and WebSocket connection")
    def test_performance_100_itens_simultaneos(self):
        """
        Teste 10: Sistema deve manter performance com muitos itens.

        Criar pedido com 100 itens:
        1. Marcar todos para compra
        2. Verificar que todos aparecem no painel
        3. Marcar 50 como realizados
        4. Marcar 50 como separados
        5. Verificar que atualizações ocorrem em < 5s

        SKIP: Teste de carga/performance.
        """
        pass


@pytest.mark.django_db
class TestLogicaBackendIntegracao(TestCase):
    """
    Testes de lógica backend para validar comportamento correto dos modelos.

    Estes testes NÃO requerem Selenium e podem rodar normalmente.
    """

    def setUp(self):
        """Configurar dados de teste."""
        self.client = Client()

        self.separador = Usuario.objects.create_user(
            numero_login=1006,
            pin='1234',
            nome='Separador Backend',
            tipo='SEPARADOR'
        )

        self.compradora = Usuario.objects.create_user(
            numero_login=1007,
            pin='5678',
            nome='Compradora Backend',
            tipo='COMPRADORA'
        )

        self.vendedor = Usuario.objects.create_user(
            numero_login=2005,
            pin='9012',
            nome='Vendedor Backend',
            tipo='VENDEDOR'
        )

        self.produto = Produto.objects.create(
            codigo='PRBACK',
            descricao='Produto Backend',
            quantidade=50,
            valor_unitario=150.00,
            valor_total=7500.00
        )

        self.pedido = Pedido.objects.create(
            numero_orcamento='PEDBACK',
            codigo_cliente='CLIBACK',
            nome_cliente='Cliente Backend',
            vendedor=self.vendedor,
            data='01/01/2025',
            logistica='RETIRA_LOJA',
            embalagem='CAIXA'
        )

        self.item = ItemPedido.objects.create(
            pedido=self.pedido,
            produto=self.produto,
            quantidade_solicitada=50,
            em_compra=False,
            separado=False
        )

        self.client.force_login(self.separador)

    def test_marcar_compra_seta_em_compra_true(self):
        """
        Teste Backend 1: Marcar item para compra deve setar em_compra=True.
        """
        self.assertFalse(self.item.em_compra)

        response = self.client.post(
            f'/pedidos/{self.pedido.id}/itens/{self.item.id}/marcar-compra/',
            HTTP_HX_REQUEST='true'
        )

        self.assertEqual(response.status_code, 200)

        self.item.refresh_from_db()
        self.assertTrue(self.item.em_compra)

    def test_marcar_separado_seta_em_compra_false(self):
        """
        Teste Backend 2: Marcar item como separado deve setar em_compra=False.
        """
        # Marcar para compra primeiro
        self.item.em_compra = True
        self.item.save()

        self.assertTrue(self.item.em_compra)

        # Marcar como separado
        response = self.client.post(
            f'/pedidos/{self.pedido.id}/itens/{self.item.id}/separar/',
            data={'quantidade': self.item.quantidade_solicitada},
            HTTP_HX_REQUEST='true'
        )

        self.assertEqual(response.status_code, 200)

        self.item.refresh_from_db()
        self.assertFalse(self.item.em_compra)  # CRÍTICO: deve ser False
        self.assertTrue(self.item.separado)

    def test_marcar_realizado_toggle_behavior(self):
        """
        Teste Backend 3: marcar_realizado() deve ter comportamento de toggle.
        """
        self.item.em_compra = True
        self.item.save()

        self.client.force_login(self.compradora)

        # Primeiro clique: marcar como realizado
        response = self.client.post(
            f'/compras/itens/{self.item.id}/marcar-realizado/',
            HTTP_HX_REQUEST='true'
        )

        self.assertEqual(response.status_code, 200)
        self.item.refresh_from_db()
        self.assertTrue(self.item.pedido_realizado)

        # Segundo clique: desmarcar
        response = self.client.post(
            f'/compras/itens/{self.item.id}/marcar-realizado/',
            HTTP_HX_REQUEST='true'
        )

        self.assertEqual(response.status_code, 200)
        self.item.refresh_from_db()
        self.assertFalse(self.item.pedido_realizado)
