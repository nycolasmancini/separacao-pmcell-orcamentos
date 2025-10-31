# -*- coding: utf-8 -*-
"""
Fase 42c - Testes E2E: Handler Remoção Item do Painel
======================================================

Objetivo: Validar que painel_compras.html remove item em tempo real
          quando recebe evento WebSocket 'item_desmarcado_compra'.

Contexto: Fase 42b emite evento backend. Fase 42c consome no frontend.

Testes:
1. test_websocket_handler_existe
2. test_handler_remove_item_do_painel
3. test_handler_nao_remove_outros_itens
4. test_multiplos_eventos_sequenciais
5. test_evento_item_inexistente_nao_causa_erro
6. test_console_log_confirmacao
7. test_reload_nao_e_chamado

Total: 7 testes E2E
"""

import pytest
import time
from django.test import TestCase, LiveServerTestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException

from core.models import Pedido, ItemPedido, Produto


User = get_user_model()


@pytest.mark.django_db
class TestFase42cHandlerRemocao(LiveServerTestCase):
    """
    Suite de testes E2E para handler de remoção do Painel de Compras.

    Valida que:
    1. Handler handleItemDesmarcadoCompra existe no JavaScript
    2. Remove item da lista quando recebe evento WebSocket
    3. Não remove outros itens (apenas o especificado)
    4. Lida com múltiplos eventos sequenciais
    5. Não causa erros se item não existe no DOM
    6. Loga confirmação no console
    7. NÃO chama location.reload() (remoção é local)
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        # Configurar ChromeDriver headless
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')

        cls.driver = webdriver.Chrome(options=chrome_options)
        cls.driver.set_window_size(1920, 1080)

    @classmethod
    def tearDownClass(cls):
        cls.driver.quit()
        super().tearDownClass()

    def setUp(self):
        """Configurar dados de teste."""
        # Usuário autenticado (separador)
        self.user = User.objects.create_user(
            numero_login=3001,
            pin='1234',
            nome='Separador Teste Remocao',
            tipo='SEPARADOR'
        )

        # Compradora (para acessar painel de compras)
        self.compradora = User.objects.create_user(
            numero_login=4001,
            pin='5678',
            nome='Compradora Teste',
            tipo='COMPRADORA'
        )

        # Vendedor
        self.vendedor = User.objects.create_user(
            numero_login=2002,
            pin='9999',
            nome='Vendedor Teste Remocao',
            tipo='VENDEDOR'
        )

        # Produtos
        self.produto1 = Produto.objects.create(
            codigo='PROD-REM-001',
            descricao='Produto Remocao 1',
            quantidade=10,
            valor_unitario=100.00,
            valor_total=1000.00
        )

        self.produto2 = Produto.objects.create(
            codigo='PROD-REM-002',
            descricao='Produto Remocao 2',
            quantidade=5,
            valor_unitario=50.00,
            valor_total=250.00
        )

        # Pedido
        self.pedido = Pedido.objects.create(
            numero_orcamento='ORD-REM-001',
            nome_cliente='Cliente Remocao Teste',
            codigo_cliente='CLI-REM-001',
            vendedor=self.vendedor,
            data=timezone.now().date()
        )

        # Item 1: Em compra
        self.item1 = ItemPedido.objects.create(
            pedido=self.pedido,
            produto=self.produto1,
            quantidade_solicitada=5,
            quantidade_separada=0,
            separado=False,
            em_compra=True,
            enviado_para_compra_por=self.user,
            enviado_para_compra_em=timezone.now()
        )

        # Item 2: Em compra (NÃO será desmarcado nos testes)
        self.item2 = ItemPedido.objects.create(
            pedido=self.pedido,
            produto=self.produto2,
            quantidade_solicitada=3,
            quantidade_separada=0,
            separado=False,
            em_compra=True,
            enviado_para_compra_por=self.user,
            enviado_para_compra_em=timezone.now()
        )

        # Login como compradora
        self.client.force_login(self.compradora)

    def login_selenium(self, user):
        """Helper para fazer login via Selenium."""
        self.driver.get(f'{self.live_server_url}/login/')

        # Preencher formulário
        numero_login_input = self.driver.find_element(By.NAME, 'numero_login')
        pin_input = self.driver.find_element(By.NAME, 'pin')

        numero_login_input.send_keys(str(user.numero_login))
        pin_input.send_keys(user.pin)

        # Submit
        submit_button = self.driver.find_element(By.CSS_SELECTOR, 'button[type="submit"]')
        submit_button.click()

        # Aguardar redirecionamento
        WebDriverWait(self.driver, 10).until(
            EC.url_changes(f'{self.live_server_url}/login/')
        )

    def test_websocket_handler_existe(self):
        """
        Teste 1: Verificar que função handleItemDesmarcadoCompra existe no JavaScript.

        Valida:
        - Script painel_compras.html define a função
        - Função está disponível no escopo global
        """
        # Login e navegar para painel de compras
        self.login_selenium(self.compradora)
        self.driver.get(f'{self.live_server_url}/compras/')

        # Aguardar página carregar
        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, 'body'))
        )

        # Verificar se função existe no window
        handler_exists = self.driver.execute_script(
            "return typeof window.handleItemDesmarcadoCompra === 'function';"
        )

        self.assertTrue(handler_exists,
                       "Função handleItemDesmarcadoCompra deve existir no JavaScript")

    def test_handler_remove_item_do_painel(self):
        """
        Teste 2: Handler deve remover item do DOM quando recebe evento WebSocket.

        Valida:
        - Item1 está no painel inicialmente
        - Simula evento WebSocket de item_desmarcado_compra
        - Item1 é removido do DOM
        - Painel atualiza visualmente
        """
        # Login e navegar para painel de compras
        self.login_selenium(self.compradora)
        self.driver.get(f'{self.live_server_url}/compras/')

        # Aguardar lista de itens carregar
        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, '[data-item-id]'))
        )

        # Verificar que Item1 está presente
        item1_element = self.driver.find_element(
            By.CSS_SELECTOR, f'[data-item-id="{self.item1.id}"]'
        )
        self.assertIsNotNone(item1_element, "Item1 deve estar no painel inicialmente")

        # Simular evento WebSocket
        event_data = {
            'item_id': self.item1.id,
            'pedido_id': self.pedido.id,
            'numero_orcamento': self.pedido.numero_orcamento,
            'produto_codigo': self.produto1.codigo,
            'produto_descricao': self.produto1.descricao,
            'desmarcado_por': self.user.nome
        }

        self.driver.execute_script("""
            window.handleItemDesmarcadoCompra(arguments[0]);
        """, event_data)

        # Aguardar remoção do DOM
        time.sleep(0.5)

        # Verificar que Item1 foi removido
        with self.assertRaises(NoSuchElementException):
            self.driver.find_element(
                By.CSS_SELECTOR, f'[data-item-id="{self.item1.id}"]'
            )

    def test_handler_nao_remove_outros_itens(self):
        """
        Teste 3: Handler NÃO deve remover outros itens (apenas o especificado).

        Valida:
        - Item1 e Item2 estão no painel inicialmente
        - Simula evento para remover Item1
        - Item1 é removido
        - Item2 permanece no DOM
        """
        # Login e navegar para painel de compras
        self.login_selenium(self.compradora)
        self.driver.get(f'{self.live_server_url}/compras/')

        # Aguardar lista de itens carregar
        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, '[data-item-id]'))
        )

        # Verificar que ambos estão presentes
        item1_element = self.driver.find_element(
            By.CSS_SELECTOR, f'[data-item-id="{self.item1.id}"]'
        )
        item2_element = self.driver.find_element(
            By.CSS_SELECTOR, f'[data-item-id="{self.item2.id}"]'
        )
        self.assertIsNotNone(item1_element)
        self.assertIsNotNone(item2_element)

        # Simular evento para remover APENAS Item1
        event_data = {
            'item_id': self.item1.id,
            'pedido_id': self.pedido.id,
            'numero_orcamento': self.pedido.numero_orcamento,
            'produto_codigo': self.produto1.codigo,
            'produto_descricao': self.produto1.descricao,
            'desmarcado_por': self.user.nome
        }

        self.driver.execute_script("""
            window.handleItemDesmarcadoCompra(arguments[0]);
        """, event_data)

        # Aguardar remoção
        time.sleep(0.5)

        # Verificar que Item1 foi removido
        with self.assertRaises(NoSuchElementException):
            self.driver.find_element(
                By.CSS_SELECTOR, f'[data-item-id="{self.item1.id}"]'
            )

        # Verificar que Item2 ainda está presente
        item2_still_present = self.driver.find_element(
            By.CSS_SELECTOR, f'[data-item-id="{self.item2.id}"]'
        )
        self.assertIsNotNone(item2_still_present,
                           "Item2 NÃO deve ser removido quando Item1 é desmarcado")

    def test_multiplos_eventos_sequenciais(self):
        """
        Teste 4: Handler deve lidar com múltiplos eventos sequenciais corretamente.

        Valida:
        - Item1 e Item2 estão no painel
        - Envia evento para remover Item1
        - Item1 é removido
        - Envia evento para remover Item2
        - Item2 também é removido
        - Painel fica vazio
        """
        # Login e navegar para painel de compras
        self.login_selenium(self.compradora)
        self.driver.get(f'{self.live_server_url}/compras/')

        # Aguardar lista carregar
        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, '[data-item-id]'))
        )

        # Remover Item1
        event_data_1 = {
            'item_id': self.item1.id,
            'pedido_id': self.pedido.id,
            'numero_orcamento': self.pedido.numero_orcamento,
            'produto_codigo': self.produto1.codigo,
            'produto_descricao': self.produto1.descricao,
            'desmarcado_por': self.user.nome
        }

        self.driver.execute_script("""
            window.handleItemDesmarcadoCompra(arguments[0]);
        """, event_data_1)
        time.sleep(0.3)

        # Verificar Item1 removido
        with self.assertRaises(NoSuchElementException):
            self.driver.find_element(
                By.CSS_SELECTOR, f'[data-item-id="{self.item1.id}"]'
            )

        # Remover Item2
        event_data_2 = {
            'item_id': self.item2.id,
            'pedido_id': self.pedido.id,
            'numero_orcamento': self.pedido.numero_orcamento,
            'produto_codigo': self.produto2.codigo,
            'produto_descricao': self.produto2.descricao,
            'desmarcado_por': self.user.nome
        }

        self.driver.execute_script("""
            window.handleItemDesmarcadoCompra(arguments[0]);
        """, event_data_2)
        time.sleep(0.3)

        # Verificar Item2 também removido
        with self.assertRaises(NoSuchElementException):
            self.driver.find_element(
                By.CSS_SELECTOR, f'[data-item-id="{self.item2.id}"]'
            )

        # Verificar mensagem de lista vazia
        empty_message = self.driver.find_element(By.CSS_SELECTOR, '.text-gray-500')
        self.assertIn('Nenhum item aguardando compra', empty_message.text)

    def test_evento_item_inexistente_nao_causa_erro(self):
        """
        Teste 5: Evento para item inexistente NÃO deve causar erro JavaScript.

        Valida:
        - Simula evento para item_id que NÃO existe no DOM
        - JavaScript lida gracefully (não quebra)
        - Console não mostra erros JavaScript
        """
        # Login e navegar para painel de compras
        self.login_selenium(self.compradora)
        self.driver.get(f'{self.live_server_url}/compras/')

        # Aguardar lista carregar
        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, '[data-item-id]'))
        )

        # Simular evento para item inexistente (ID muito alto)
        event_data = {
            'item_id': 999999,  # ID que não existe
            'pedido_id': self.pedido.id,
            'numero_orcamento': self.pedido.numero_orcamento,
            'produto_codigo': 'FAKE',
            'produto_descricao': 'Item Inexistente',
            'desmarcado_por': self.user.nome
        }

        # Executar handler
        result = self.driver.execute_script("""
            try {
                window.handleItemDesmarcadoCompra(arguments[0]);
                return { success: true, error: null };
            } catch (error) {
                return { success: false, error: error.message };
            }
        """, event_data)

        # Validar que não houve erro
        self.assertTrue(result['success'],
                       f"Handler deve lidar com item inexistente sem erro: {result.get('error')}")

        # Verificar que itens existentes ainda estão presentes
        item1_still_present = self.driver.find_element(
            By.CSS_SELECTOR, f'[data-item-id="{self.item1.id}"]'
        )
        self.assertIsNotNone(item1_still_present)

    def test_console_log_confirmacao(self):
        """
        Teste 6: Handler deve logar confirmação de remoção no console.

        Valida:
        - Captura console.log do navegador
        - Handler loga mensagem confirmando remoção
        - Mensagem contém item_id removido
        """
        # Login e navegar para painel de compras
        self.login_selenium(self.compradora)
        self.driver.get(f'{self.live_server_url}/compras/')

        # Aguardar lista carregar
        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, '[data-item-id]'))
        )

        # Capturar logs do console antes da ação
        # (Selenium não tem API direta, então vamos mockar console.log)
        self.driver.execute_script("""
            window.consoleCapture = [];
            const originalLog = console.log;
            console.log = function(...args) {
                window.consoleCapture.push(args.join(' '));
                originalLog.apply(console, args);
            };
        """)

        # Simular evento
        event_data = {
            'item_id': self.item1.id,
            'pedido_id': self.pedido.id,
            'numero_orcamento': self.pedido.numero_orcamento,
            'produto_codigo': self.produto1.codigo,
            'produto_descricao': self.produto1.descricao,
            'desmarcado_por': self.user.nome
        }

        self.driver.execute_script("""
            window.handleItemDesmarcadoCompra(arguments[0]);
        """, event_data)

        time.sleep(0.3)

        # Capturar logs
        logs = self.driver.execute_script("return window.consoleCapture;")

        # Validar que há log de remoção
        removal_log_found = any(
            'Item removido' in log and str(self.item1.id) in log
            for log in logs
        )

        self.assertTrue(removal_log_found,
                       "Console deve logar confirmação de remoção com item_id")

    def test_reload_nao_e_chamado(self):
        """
        Teste 7: Handler NÃO deve chamar location.reload() (remoção é local).

        Valida:
        - Handler remove item do DOM localmente
        - NÃO recarrega a página inteira
        - Performance melhor que reload
        """
        # Login e navegar para painel de compras
        self.login_selenium(self.compradora)
        self.driver.get(f'{self.live_server_url}/compras/')

        # Aguardar lista carregar
        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, '[data-item-id]'))
        )

        # Mockar location.reload para detectar se foi chamado
        self.driver.execute_script("""
            window.reloadCalled = false;
            const originalReload = location.reload;
            location.reload = function() {
                window.reloadCalled = true;
                // Não chamar reload de verdade para não quebrar o teste
            };
        """)

        # Simular evento
        event_data = {
            'item_id': self.item1.id,
            'pedido_id': self.pedido.id,
            'numero_orcamento': self.pedido.numero_orcamento,
            'produto_codigo': self.produto1.codigo,
            'produto_descricao': self.produto1.descricao,
            'desmarcado_por': self.user.nome
        }

        self.driver.execute_script("""
            window.handleItemDesmarcadoCompra(arguments[0]);
        """, event_data)

        time.sleep(0.5)

        # Verificar que reload NÃO foi chamado
        reload_called = self.driver.execute_script("return window.reloadCalled;")
        self.assertFalse(reload_called,
                        "Handler NÃO deve chamar location.reload() (remoção é local)")

        # Verificar que item foi removido do DOM
        with self.assertRaises(NoSuchElementException):
            self.driver.find_element(
                By.CSS_SELECTOR, f'[data-item-id="{self.item1.id}"]'
            )
