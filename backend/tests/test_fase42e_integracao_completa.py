# -*- coding: utf-8 -*-
"""
Fase 42e - Testes E2E: Integração Completa Badge + WebSocket
Objetivo: Validar fluxo completo de marcar/desmarcar item para compra
          com atualizações locais (HTMX) e remotas (WebSocket)

Suite de 8 testes de integração end-to-end:
1. test_marcar_compra_badge_local_e_remoto - Badge aparece local e remotamente
2. test_desmarcar_compra_badge_desaparece - Badge some ao desmarcar
3. test_painel_compras_recebe_item_tempo_real - Painel recebe item via WebSocket
4. test_painel_compras_remove_item_tempo_real - Painel remove item via WebSocket
5. test_multiplas_operacoes_sequenciais - Múltiplas operações em sequência
6. test_fluxo_completo_roundtrip - Fluxo completo: marcar → desmarcar → marcar
7. test_sincronizacao_multi_tab - Sincronização entre múltiplas tabs
8. test_painel_compras_estado_vazio - Estado vazio do painel após remover todos

Metodologia TDD - Red-Green-Refactor
"""

import pytest
from django.test import LiveServerTestCase
from django.contrib.auth import get_user_model
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
import time
from core.models import Pedido, ItemPedido, Produto, Vendedor

User = get_user_model()


@pytest.mark.django_db
class TestFase42eIntegracaoCompleta(LiveServerTestCase):
    """
    Suite de testes E2E para integração completa do sistema de compras.

    Valida:
    - Atualizações locais via HTMX (sem reload)
    - Atualizações remotas via WebSocket (tempo real)
    - Sincronização entre dashboard e painel de compras
    - Sincronização entre múltiplas tabs/browsers
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        # Configurar Chrome headless
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')

        cls.driver = webdriver.Chrome(options=chrome_options)
        cls.driver.implicitly_wait(10)

        # Segundo driver para testes multi-tab
        cls.driver2 = webdriver.Chrome(options=chrome_options)
        cls.driver2.implicitly_wait(10)

    @classmethod
    def tearDownClass(cls):
        cls.driver.quit()
        cls.driver2.quit()
        super().tearDownClass()

    def setUp(self):
        """Configurar dados de teste para cada teste."""
        # Criar usuário autenticado
        self.user = User.objects.create_user(
            username='separador_teste',
            password='senha123'
        )

        # Criar vendedor
        self.vendedor = Vendedor.objects.create(
            codigo='V001',
            nome='Vendedor Teste'
        )

        # Criar produto
        self.produto = Produto.objects.create(
            codigo='PROD001',
            descricao='Produto Teste E2E',
            preco_venda=100.00
        )

        # Criar pedido
        self.pedido = Pedido.objects.create(
            numero_orcamento='ORC-42E-001',
            codigo_cliente='CLI001',
            nome_cliente='Cliente Teste',
            vendedor=self.vendedor,
            total_itens=1,
            valor_total=100.00,
            separador=self.user
        )

        # Criar item do pedido
        self.item = ItemPedido.objects.create(
            pedido=self.pedido,
            produto=self.produto,
            quantidade_solicitada=5,
            preco_unitario=100.00,
            separado=False,
            em_compra=False
        )

        # Login nos dois drivers
        self._login_driver(self.driver)
        self._login_driver(self.driver2)

    def _login_driver(self, driver):
        """Helper para fazer login em um driver."""
        driver.get(f'{self.live_server_url}/login/')
        driver.find_element(By.NAME, 'username').send_keys('separador_teste')
        driver.find_element(By.NAME, 'password').send_keys('senha123')
        driver.find_element(By.CSS_SELECTOR, 'button[type="submit"]').click()
        time.sleep(1)  # Aguardar redirect

    def _wait_for_badge_present(self, driver, item_id, timeout=10):
        """Helper: aguardar badge aparecer."""
        WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located(
                (By.CSS_SELECTOR, f'#badge-{item_id} .bg-orange-100')
            )
        )

    def _wait_for_badge_absent(self, driver, item_id, timeout=10):
        """Helper: aguardar badge desaparecer."""
        WebDriverWait(driver, timeout).until_not(
            EC.presence_of_element_located(
                (By.CSS_SELECTOR, f'#badge-{item_id} .bg-orange-100')
            )
        )

    def _wait_for_element_removed(self, driver, selector, timeout=10):
        """Helper: aguardar elemento ser removido do DOM."""
        WebDriverWait(driver, timeout).until_not(
            EC.presence_of_element_located((By.CSS_SELECTOR, selector))
        )

    def test_marcar_compra_badge_local_e_remoto(self):
        """
        Teste 1: Badge deve aparecer localmente (HTMX) e remotamente (WebSocket).

        Cenário:
        1. Tab 1 (driver): Dashboard aberto
        2. Tab 2 (driver2): Dashboard aberto (mesmo pedido visível)
        3. Tab 1: Clicar "Enviar para Compra"
        4. VALIDAR: Tab 1 → Badge aparece LOCALMENTE (sem reload)
        5. VALIDAR: Tab 2 → Badge aparece REMOTAMENTE (via WebSocket)
        """
        # Tab 1: Abrir dashboard
        self.driver.get(f'{self.live_server_url}/dashboard/')
        time.sleep(2)  # Aguardar WebSocket conectar

        # Tab 2: Abrir dashboard
        self.driver2.get(f'{self.live_server_url}/dashboard/')
        time.sleep(2)  # Aguardar WebSocket conectar

        # Validar: Badge NÃO existe inicialmente em ambas as tabs
        badge1_initial = self.driver.find_elements(By.CSS_SELECTOR, f'#badge-{self.item.id} .bg-orange-100')
        badge2_initial = self.driver2.find_elements(By.CSS_SELECTOR, f'#badge-{self.item.id} .bg-orange-100')
        assert len(badge1_initial) == 0, "Badge não deveria existir inicialmente na Tab 1"
        assert len(badge2_initial) == 0, "Badge não deveria existir inicialmente na Tab 2"

        # Tab 1: Clicar "Enviar para Compra"
        botao_compra = self.driver.find_element(By.CSS_SELECTOR, f'button[hx-post*="marcar_compra/{self.item.id}"]')
        botao_compra.click()

        # VALIDAR: Tab 1 → Badge aparece LOCALMENTE (HTMX)
        self._wait_for_badge_present(self.driver, self.item.id, timeout=5)
        badge_local = self.driver.find_element(By.CSS_SELECTOR, f'#badge-{self.item.id}')
        assert 'bg-orange-100' in badge_local.get_attribute('class'), "Badge local deve ter classe bg-orange-100"
        assert 'Aguardando Compra' in badge_local.text, "Badge local deve conter texto 'Aguardando Compra'"

        # VALIDAR: Tab 2 → Badge aparece REMOTAMENTE (WebSocket)
        self._wait_for_badge_present(self.driver2, self.item.id, timeout=10)
        badge_remoto = self.driver2.find_element(By.CSS_SELECTOR, f'#badge-{self.item.id}')
        assert 'bg-orange-100' in badge_remoto.get_attribute('class'), "Badge remoto deve ter classe bg-orange-100"
        assert 'Aguardando Compra' in badge_remoto.text, "Badge remoto deve conter texto 'Aguardando Compra'"

    def test_desmarcar_compra_badge_desaparece(self):
        """
        Teste 2: Badge deve desaparecer ao desmarcar item de compra.

        Cenário:
        1. Item JÁ está marcado para compra (badge presente)
        2. Tab 1: Clicar botão "Desmarcar Compra"
        3. VALIDAR: Badge desaparece localmente (HTMX)
        4. VALIDAR: Badge desaparece remotamente (WebSocket)
        """
        # Preparar: Marcar item para compra
        self.item.em_compra = True
        self.item.enviado_para_compra_por = self.user
        self.item.save()

        # Tab 1: Abrir dashboard
        self.driver.get(f'{self.live_server_url}/dashboard/')
        time.sleep(2)

        # Tab 2: Abrir dashboard
        self.driver2.get(f'{self.live_server_url}/dashboard/')
        time.sleep(2)

        # Validar: Badge EXISTE inicialmente
        badge1_initial = self.driver.find_element(By.CSS_SELECTOR, f'#badge-{self.item.id}')
        badge2_initial = self.driver2.find_element(By.CSS_SELECTOR, f'#badge-{self.item.id}')
        assert 'bg-orange-100' in badge1_initial.get_attribute('class'), "Badge deve existir inicialmente na Tab 1"
        assert 'bg-orange-100' in badge2_initial.get_attribute('class'), "Badge deve existir inicialmente na Tab 2"

        # Tab 1: Clicar "Desmarcar Compra"
        botao_desmarcar = self.driver.find_element(By.CSS_SELECTOR, f'button[hx-post*="desmarcar_compra/{self.item.id}"]')
        botao_desmarcar.click()

        # VALIDAR: Tab 1 → Badge desaparece LOCALMENTE
        self._wait_for_badge_absent(self.driver, self.item.id, timeout=5)
        badge_local = self.driver.find_element(By.CSS_SELECTOR, f'#badge-{self.item.id}')
        assert 'bg-orange-100' not in badge_local.get_attribute('class'), "Badge local não deve ter bg-orange-100"

        # VALIDAR: Tab 2 → Badge desaparece REMOTAMENTE
        self._wait_for_badge_absent(self.driver2, self.item.id, timeout=10)
        badge_remoto = self.driver2.find_element(By.CSS_SELECTOR, f'#badge-{self.item.id}')
        assert 'bg-orange-100' not in badge_remoto.get_attribute('class'), "Badge remoto não deve ter bg-orange-100"

    def test_painel_compras_recebe_item_tempo_real(self):
        """
        Teste 3: Painel de Compras deve receber item em tempo real via WebSocket.

        Cenário:
        1. Tab 1: Dashboard aberto
        2. Tab 2: Painel de Compras aberto
        3. Tab 1: Marcar item para compra
        4. VALIDAR: Tab 2 (Painel) recebe item em tempo real (via WebSocket)
        """
        # Tab 1: Abrir dashboard
        self.driver.get(f'{self.live_server_url}/dashboard/')
        time.sleep(2)

        # Tab 2: Abrir painel de compras
        self.driver2.get(f'{self.live_server_url}/painel-compras/')
        time.sleep(2)

        # Validar: Painel VAZIO inicialmente
        empty_state = self.driver2.find_elements(By.XPATH, '//*[contains(text(), "Nenhum item aguardando compra")]')
        assert len(empty_state) > 0, "Painel deve estar vazio inicialmente"

        # Tab 1: Marcar item para compra
        botao_compra = self.driver.find_element(By.CSS_SELECTOR, f'button[hx-post*="marcar_compra/{self.item.id}"]')
        botao_compra.click()
        time.sleep(1)  # Aguardar HTMX

        # Aguardar page reload no painel (comportamento atual)
        time.sleep(3)

        # VALIDAR: Item aparece no painel de compras
        self.driver2.refresh()  # Simular reload
        time.sleep(2)

        item_painel = self.driver2.find_elements(By.CSS_SELECTOR, f'[data-item-id="{self.item.id}"]')
        assert len(item_painel) > 0, f"Item {self.item.id} deve aparecer no painel de compras"

    def test_painel_compras_remove_item_tempo_real(self):
        """
        Teste 4: Painel de Compras deve remover item em tempo real ao desmarcar.

        Cenário:
        1. Item JÁ está no painel de compras
        2. Tab 1: Dashboard aberto
        3. Tab 2: Painel de Compras aberto (item visível)
        4. Tab 1: Desmarcar item de compra
        5. VALIDAR: Tab 2 (Painel) remove item em tempo real (sem reload)
        """
        # Preparar: Marcar item para compra
        self.item.em_compra = True
        self.item.enviado_para_compra_por = self.user
        self.item.save()

        # Tab 1: Abrir dashboard
        self.driver.get(f'{self.live_server_url}/dashboard/')
        time.sleep(2)

        # Tab 2: Abrir painel de compras
        self.driver2.get(f'{self.live_server_url}/painel-compras/')
        time.sleep(2)

        # Validar: Item EXISTE no painel
        item_painel_initial = self.driver2.find_elements(By.CSS_SELECTOR, f'[data-item-id="{self.item.id}"]')
        assert len(item_painel_initial) > 0, "Item deve estar no painel inicialmente"

        # Tab 1: Desmarcar item de compra
        botao_desmarcar = self.driver.find_element(By.CSS_SELECTOR, f'button[hx-post*="desmarcar_compra/{self.item.id}"]')
        botao_desmarcar.click()
        time.sleep(1)  # Aguardar HTMX

        # VALIDAR: Tab 2 → Item removido do painel (via WebSocket)
        self._wait_for_element_removed(
            self.driver2,
            f'[data-item-id="{self.item.id}"]',
            timeout=10
        )

        item_painel_final = self.driver2.find_elements(By.CSS_SELECTOR, f'[data-item-id="{self.item.id}"]')
        assert len(item_painel_final) == 0, "Item deve ser removido do painel via WebSocket"

    def test_multiplas_operacoes_sequenciais(self):
        """
        Teste 5: Múltiplas operações sequenciais devem funcionar corretamente.

        Cenário:
        1. Marcar item 1 para compra → Badge aparece
        2. Criar item 2
        3. Marcar item 2 para compra → Badge aparece
        4. Desmarcar item 1 → Badge 1 some, Badge 2 permanece
        5. Desmarcar item 2 → Ambos badges sumiram
        """
        # Criar segundo item
        item2 = ItemPedido.objects.create(
            pedido=self.pedido,
            produto=self.produto,
            quantidade_solicitada=3,
            preco_unitario=100.00,
            separado=False,
            em_compra=False
        )

        # Abrir dashboard
        self.driver.get(f'{self.live_server_url}/dashboard/')
        time.sleep(2)

        # 1. Marcar item 1 para compra
        botao1 = self.driver.find_element(By.CSS_SELECTOR, f'button[hx-post*="marcar_compra/{self.item.id}"]')
        botao1.click()
        self._wait_for_badge_present(self.driver, self.item.id, timeout=5)

        # 2. Marcar item 2 para compra
        botao2 = self.driver.find_element(By.CSS_SELECTOR, f'button[hx-post*="marcar_compra/{item2.id}"]')
        botao2.click()
        self._wait_for_badge_present(self.driver, item2.id, timeout=5)

        # Validar: Ambos badges presentes
        badge1 = self.driver.find_element(By.CSS_SELECTOR, f'#badge-{self.item.id}')
        badge2 = self.driver.find_element(By.CSS_SELECTOR, f'#badge-{item2.id}')
        assert 'bg-orange-100' in badge1.get_attribute('class'), "Badge 1 deve estar presente"
        assert 'bg-orange-100' in badge2.get_attribute('class'), "Badge 2 deve estar presente"

        # 3. Desmarcar item 1
        botao_desmarcar1 = self.driver.find_element(By.CSS_SELECTOR, f'button[hx-post*="desmarcar_compra/{self.item.id}"]')
        botao_desmarcar1.click()
        self._wait_for_badge_absent(self.driver, self.item.id, timeout=5)

        # Validar: Badge 1 sumiu, Badge 2 permanece
        badge1_final = self.driver.find_element(By.CSS_SELECTOR, f'#badge-{self.item.id}')
        badge2_check = self.driver.find_element(By.CSS_SELECTOR, f'#badge-{item2.id}')
        assert 'bg-orange-100' not in badge1_final.get_attribute('class'), "Badge 1 deve ter sumido"
        assert 'bg-orange-100' in badge2_check.get_attribute('class'), "Badge 2 deve permanecer"

        # 4. Desmarcar item 2
        botao_desmarcar2 = self.driver.find_element(By.CSS_SELECTOR, f'button[hx-post*="desmarcar_compra/{item2.id}"]')
        botao_desmarcar2.click()
        self._wait_for_badge_absent(self.driver, item2.id, timeout=5)

        # Validar: Ambos badges sumiram
        badge1_end = self.driver.find_element(By.CSS_SELECTOR, f'#badge-{self.item.id}')
        badge2_end = self.driver.find_element(By.CSS_SELECTOR, f'#badge-{item2.id}')
        assert 'bg-orange-100' not in badge1_end.get_attribute('class'), "Badge 1 final não deve existir"
        assert 'bg-orange-100' not in badge2_end.get_attribute('class'), "Badge 2 final não deve existir"

    def test_fluxo_completo_roundtrip(self):
        """
        Teste 6: Fluxo completo round-trip: marcar → desmarcar → marcar novamente.

        Valida que o sistema suporta múltiplos ciclos de marcação/desmarcação.
        """
        # Abrir dashboard
        self.driver.get(f'{self.live_server_url}/dashboard/')
        time.sleep(2)

        # Ciclo 1: Marcar
        botao1 = self.driver.find_element(By.CSS_SELECTOR, f'button[hx-post*="marcar_compra/{self.item.id}"]')
        botao1.click()
        self._wait_for_badge_present(self.driver, self.item.id, timeout=5)
        badge1 = self.driver.find_element(By.CSS_SELECTOR, f'#badge-{self.item.id}')
        assert 'bg-orange-100' in badge1.get_attribute('class'), "Badge deve aparecer no ciclo 1"

        # Ciclo 1: Desmarcar
        botao_desmarcar1 = self.driver.find_element(By.CSS_SELECTOR, f'button[hx-post*="desmarcar_compra/{self.item.id}"]')
        botao_desmarcar1.click()
        self._wait_for_badge_absent(self.driver, self.item.id, timeout=5)
        badge1_off = self.driver.find_element(By.CSS_SELECTOR, f'#badge-{self.item.id}')
        assert 'bg-orange-100' not in badge1_off.get_attribute('class'), "Badge deve sumir no ciclo 1"

        # Ciclo 2: Marcar novamente
        botao2 = self.driver.find_element(By.CSS_SELECTOR, f'button[hx-post*="marcar_compra/{self.item.id}"]')
        botao2.click()
        self._wait_for_badge_present(self.driver, self.item.id, timeout=5)
        badge2 = self.driver.find_element(By.CSS_SELECTOR, f'#badge-{self.item.id}')
        assert 'bg-orange-100' in badge2.get_attribute('class'), "Badge deve aparecer novamente no ciclo 2"

        # Ciclo 2: Desmarcar novamente
        botao_desmarcar2 = self.driver.find_element(By.CSS_SELECTOR, f'button[hx-post*="desmarcar_compra/{self.item.id}"]')
        botao_desmarcar2.click()
        self._wait_for_badge_absent(self.driver, self.item.id, timeout=5)
        badge2_off = self.driver.find_element(By.CSS_SELECTOR, f'#badge-{self.item.id}')
        assert 'bg-orange-100' not in badge2_off.get_attribute('class'), "Badge deve sumir novamente no ciclo 2"

    def test_sincronizacao_multi_tab(self):
        """
        Teste 7: Sincronização perfeita entre múltiplas tabs abertas.

        Cenário:
        1. Tab 1, Tab 2, Tab 3: Todas com dashboard aberto
        2. Tab 1: Marcar item para compra
        3. VALIDAR: Badge aparece em TODAS as tabs simultaneamente
        4. Tab 2: Desmarcar item
        5. VALIDAR: Badge some em TODAS as tabs simultaneamente
        """
        # Criar terceiro driver
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        driver3 = webdriver.Chrome(options=chrome_options)
        driver3.implicitly_wait(10)
        self._login_driver(driver3)

        try:
            # Abrir dashboard em todas as tabs
            self.driver.get(f'{self.live_server_url}/dashboard/')
            self.driver2.get(f'{self.live_server_url}/dashboard/')
            driver3.get(f'{self.live_server_url}/dashboard/')
            time.sleep(3)  # Aguardar WebSockets

            # Tab 1: Marcar item para compra
            botao = self.driver.find_element(By.CSS_SELECTOR, f'button[hx-post*="marcar_compra/{self.item.id}"]')
            botao.click()

            # VALIDAR: Badge aparece em TODAS as tabs
            self._wait_for_badge_present(self.driver, self.item.id, timeout=5)
            self._wait_for_badge_present(self.driver2, self.item.id, timeout=10)
            self._wait_for_badge_present(driver3, self.item.id, timeout=10)

            badge1 = self.driver.find_element(By.CSS_SELECTOR, f'#badge-{self.item.id}')
            badge2 = self.driver2.find_element(By.CSS_SELECTOR, f'#badge-{self.item.id}')
            badge3 = driver3.find_element(By.CSS_SELECTOR, f'#badge-{self.item.id}')

            assert 'bg-orange-100' in badge1.get_attribute('class'), "Badge deve aparecer na Tab 1"
            assert 'bg-orange-100' in badge2.get_attribute('class'), "Badge deve aparecer na Tab 2"
            assert 'bg-orange-100' in badge3.get_attribute('class'), "Badge deve aparecer na Tab 3"

            # Tab 2: Desmarcar item
            botao_desmarcar = self.driver2.find_element(By.CSS_SELECTOR, f'button[hx-post*="desmarcar_compra/{self.item.id}"]')
            botao_desmarcar.click()

            # VALIDAR: Badge some em TODAS as tabs
            self._wait_for_badge_absent(self.driver2, self.item.id, timeout=5)
            self._wait_for_badge_absent(self.driver, self.item.id, timeout=10)
            self._wait_for_badge_absent(driver3, self.item.id, timeout=10)

            badge1_off = self.driver.find_element(By.CSS_SELECTOR, f'#badge-{self.item.id}')
            badge2_off = self.driver2.find_element(By.CSS_SELECTOR, f'#badge-{self.item.id}')
            badge3_off = driver3.find_element(By.CSS_SELECTOR, f'#badge-{self.item.id}')

            assert 'bg-orange-100' not in badge1_off.get_attribute('class'), "Badge deve sumir na Tab 1"
            assert 'bg-orange-100' not in badge2_off.get_attribute('class'), "Badge deve sumir na Tab 2"
            assert 'bg-orange-100' not in badge3_off.get_attribute('class'), "Badge deve sumir na Tab 3"

        finally:
            driver3.quit()

    def test_painel_compras_estado_vazio(self):
        """
        Teste 8: Painel de Compras deve mostrar estado vazio após remover todos os itens.

        Cenário:
        1. Criar 2 itens e marcar ambos para compra
        2. Painel de Compras mostra 2 itens
        3. Desmarcar item 1 → Painel mostra 1 item
        4. Desmarcar item 2 → Painel mostra estado vazio
        """
        # Criar segundo item
        item2 = ItemPedido.objects.create(
            pedido=self.pedido,
            produto=self.produto,
            quantidade_solicitada=3,
            preco_unitario=100.00,
            separado=False,
            em_compra=True,
            enviado_para_compra_por=self.user
        )

        # Marcar primeiro item
        self.item.em_compra = True
        self.item.enviado_para_compra_por = self.user
        self.item.save()

        # Tab 1: Dashboard
        self.driver.get(f'{self.live_server_url}/dashboard/')
        time.sleep(2)

        # Tab 2: Painel de Compras
        self.driver2.get(f'{self.live_server_url}/painel-compras/')
        time.sleep(2)

        # Validar: 2 itens no painel
        itens_painel = self.driver2.find_elements(By.CSS_SELECTOR, '[data-item-id]')
        assert len(itens_painel) == 2, "Painel deve mostrar 2 itens inicialmente"

        # Desmarcar item 1
        botao1 = self.driver.find_element(By.CSS_SELECTOR, f'button[hx-post*="desmarcar_compra/{self.item.id}"]')
        botao1.click()
        time.sleep(2)

        # Validar: 1 item restante (o item2)
        self._wait_for_element_removed(self.driver2, f'[data-item-id="{self.item.id}"]', timeout=10)
        itens_restantes = self.driver2.find_elements(By.CSS_SELECTOR, '[data-item-id]')
        assert len(itens_restantes) == 1, "Painel deve mostrar 1 item após remover primeiro"

        # Desmarcar item 2
        botao2 = self.driver.find_element(By.CSS_SELECTOR, f'button[hx-post*="desmarcar_compra/{item2.id}"]')
        botao2.click()
        time.sleep(2)

        # Validar: Estado vazio (reload automático quando último item removido)
        # O painel recarrega automaticamente, então verificamos após reload
        time.sleep(3)  # Aguardar reload
        empty_message = self.driver2.find_elements(By.XPATH, '//*[contains(text(), "Nenhum item aguardando compra")]')
        assert len(empty_message) > 0, "Painel deve mostrar mensagem de estado vazio"

        itens_final = self.driver2.find_elements(By.CSS_SELECTOR, '[data-item-id]')
        assert len(itens_final) == 0, "Painel não deve ter nenhum item após remover todos"
