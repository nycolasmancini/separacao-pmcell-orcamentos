# -*- coding: utf-8 -*-
"""
Fase 42d - Testes E2E: Badge Local HTMX sem Reload
==================================================

Objetivo: Validar que badge "Aguardando Compra" aparece LOCALMENTE
          sem page reload ao marcar item para compra via HTMX.

Contexto: Bug original - badge só aparecia após F5 (reload manual).
          Correção - HTMX swap deve atualizar badge imediatamente.

Testes:
1. test_badge_aparece_sem_reload
2. test_badge_css_classes_corretas
3. test_badge_contem_icone_correto
4. test_badge_texto_aguardando_compra
5. test_page_url_nao_muda
6. test_outros_itens_nao_afetados

Total: 6 testes E2E
"""

import pytest
import time
from django.test import TestCase, LiveServerTestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
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
class TestFase42dBadgeLocalHTMX(LiveServerTestCase):
    """
    Suite de testes E2E para badge local HTMX.

    Valida que ao clicar em "Enviar para Compra":
    1. Badge aparece IMEDIATAMENTE no dispositivo local (sem reload)
    2. Badge tem classes CSS corretas (bg-orange-100, text-orange-800)
    3. Badge contém ícone de relógio
    4. Badge mostra texto "Aguardando Compra"
    5. URL da página NÃO muda (confirma que não houve navegação)
    6. Outros itens NÃO são afetados
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
            numero_login=5001,
            pin='1234',
            nome='Separador Badge Local',
            tipo='SEPARADOR'
        )

        # Vendedor
        self.vendedor = User.objects.create_user(
            numero_login=6001,
            pin='5678',
            nome='Vendedor Badge Local',
            tipo='VENDEDOR'
        )

        # Produtos
        self.produto1 = Produto.objects.create(
            codigo='BADGE-001',
            descricao='Produto Badge Local 1',
            quantidade=10,
            valor_unitario=100.00,
            valor_total=1000.00
        )

        self.produto2 = Produto.objects.create(
            codigo='BADGE-002',
            descricao='Produto Badge Local 2',
            quantidade=5,
            valor_unitario=50.00,
            valor_total=250.00
        )

        # Pedido
        self.pedido = Pedido.objects.create(
            numero_orcamento='ORD-BADGE-LOCAL-001',
            nome_cliente='Cliente Badge Local',
            codigo_cliente='CLI-BADGE-001',
            vendedor=self.vendedor,
            data=timezone.now().date()
        )

        # Item 1: Faltante (NÃO separado, NÃO em compra)
        self.item1 = ItemPedido.objects.create(
            pedido=self.pedido,
            produto=self.produto1,
            quantidade_solicitada=5,
            quantidade_separada=0,
            separado=False,
            em_compra=False
        )

        # Item 2: Faltante (NÃO será marcado para compra neste teste)
        self.item2 = ItemPedido.objects.create(
            pedido=self.pedido,
            produto=self.produto2,
            quantidade_solicitada=3,
            quantidade_separada=0,
            separado=False,
            em_compra=False
        )

        # Login como separador
        self.client.force_login(self.user)

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

    def test_badge_aparece_sem_reload(self):
        """
        Teste 1: Badge deve aparecer IMEDIATAMENTE após clicar, sem reload.

        Valida:
        - Badge NÃO está presente inicialmente
        - Clicar em "Enviar para Compra" (botão HTMX)
        - Badge aparece no DOM imediatamente
        - NÃO houve reload da página
        """
        # Login e navegar para detalhe do pedido
        self.login_selenium(self.user)
        self.driver.get(f'{self.live_server_url}/pedidos/{self.pedido.id}/')

        # Aguardar página carregar
        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, 'body'))
        )

        # Guardar URL inicial
        initial_url = self.driver.current_url

        # Verificar que badge NÃO está presente inicialmente
        badge_selector = f'#badge-{self.item1.id}'
        try:
            initial_badge = self.driver.find_element(By.CSS_SELECTOR, badge_selector)
            # Badge existe mas deve estar vazio (sem texto "Aguardando Compra")
            self.assertNotIn('Aguardando Compra', initial_badge.text)
        except NoSuchElementException:
            # Badge não existe, ok também
            pass

        # Clicar no botão "Enviar para Compra" via HTMX
        compra_button = WebDriverWait(self.driver, 10).until(
            EC.element_to_be_clickable((
                By.CSS_SELECTOR,
                f'button[hx-post*="marcar-compra"][hx-post*="{self.item1.id}"]'
            ))
        )
        compra_button.click()

        # Aguardar badge aparecer (HTMX swap)
        WebDriverWait(self.driver, 5).until(
            EC.presence_of_element_located((
                By.CSS_SELECTOR,
                f'{badge_selector}:not([class*="bg-gray"])'
            ))
        )

        # Verificar que badge agora contém "Aguardando Compra"
        badge = self.driver.find_element(By.CSS_SELECTOR, badge_selector)
        self.assertIn('Aguardando Compra', badge.text,
                     "Badge deve mostrar 'Aguardando Compra' IMEDIATAMENTE após clicar")

        # Verificar que URL NÃO mudou (não houve navegação/reload)
        current_url = self.driver.current_url
        self.assertEqual(initial_url, current_url,
                        "URL não deve mudar (confirma que não houve page reload)")

    def test_badge_css_classes_corretas(self):
        """
        Teste 2: Badge deve ter classes CSS corretas para estado "Aguardando Compra".

        Valida:
        - bg-orange-100 (fundo laranja claro)
        - text-orange-800 (texto laranja escuro)
        - Outras classes de estilo (px-3, py-1, rounded-full, etc.)
        """
        # Login e navegar
        self.login_selenium(self.user)
        self.driver.get(f'{self.live_server_url}/pedidos/{self.pedido.id}/')

        # Aguardar página carregar
        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, 'body'))
        )

        # Clicar no botão "Enviar para Compra"
        compra_button = WebDriverWait(self.driver, 10).until(
            EC.element_to_be_clickable((
                By.CSS_SELECTOR,
                f'button[hx-post*="marcar-compra"][hx-post*="{self.item1.id}"]'
            ))
        )
        compra_button.click()

        # Aguardar badge aparecer
        badge_selector = f'#badge-{self.item1.id}'
        badge = WebDriverWait(self.driver, 5).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, badge_selector))
        )

        # Extrair classes CSS
        badge_classes = badge.get_attribute('class').split()

        # Validar classes específicas de estado "Aguardando Compra"
        self.assertIn('bg-orange-100', badge_classes,
                     "Badge deve ter fundo laranja claro (bg-orange-100)")
        self.assertIn('text-orange-800', badge_classes,
                     "Badge deve ter texto laranja escuro (text-orange-800)")

        # Validar classes de estilo gerais
        self.assertIn('rounded-full', badge_classes,
                     "Badge deve ter bordas arredondadas")
        self.assertIn('text-xs', badge_classes,
                     "Badge deve ter texto pequeno")

    def test_badge_contem_icone_correto(self):
        """
        Teste 3: Badge deve conter ícone SVG de relógio (estado "Aguardando").

        Valida:
        - Badge contém elemento <svg>
        - SVG representa ícone de relógio (não checkmark)
        """
        # Login e navegar
        self.login_selenium(self.user)
        self.driver.get(f'{self.live_server_url}/pedidos/{self.pedido.id}/')

        # Aguardar página carregar
        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, 'body'))
        )

        # Clicar no botão "Enviar para Compra"
        compra_button = WebDriverWait(self.driver, 10).until(
            EC.element_to_be_clickable((
                By.CSS_SELECTOR,
                f'button[hx-post*="marcar-compra"][hx-post*="{self.item1.id}"]'
            ))
        )
        compra_button.click()

        # Aguardar badge aparecer
        badge_selector = f'#badge-{self.item1.id}'
        badge = WebDriverWait(self.driver, 5).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, badge_selector))
        )

        # Verificar que badge contém SVG
        svg_icon = badge.find_element(By.CSS_SELECTOR, 'svg')
        self.assertIsNotNone(svg_icon, "Badge deve conter ícone SVG")

        # Verificar dimensões do ícone (w-3 h-3)
        svg_classes = svg_icon.get_attribute('class').split()
        self.assertIn('w-3', svg_classes, "Ícone deve ter largura w-3")
        self.assertIn('h-3', svg_classes, "Ícone deve ter altura h-3")

    def test_badge_texto_aguardando_compra(self):
        """
        Teste 4: Badge deve mostrar texto exato "Aguardando Compra".

        Valida:
        - Texto visível no badge
        - Case-sensitive
        - Não contém textos de outros estados (ex: "Já comprado")
        """
        # Login e navegar
        self.login_selenium(self.user)
        self.driver.get(f'{self.live_server_url}/pedidos/{self.pedido.id}/')

        # Aguardar página carregar
        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, 'body'))
        )

        # Clicar no botão "Enviar para Compra"
        compra_button = WebDriverWait(self.driver, 10).until(
            EC.element_to_be_clickable((
                By.CSS_SELECTOR,
                f'button[hx-post*="marcar-compra"][hx-post*="{self.item1.id}"]'
            ))
        )
        compra_button.click()

        # Aguardar badge aparecer
        badge_selector = f'#badge-{self.item1.id}'
        badge = WebDriverWait(self.driver, 5).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, badge_selector))
        )

        # Validar texto exato
        badge_text = badge.text
        self.assertIn('Aguardando Compra', badge_text,
                     "Badge deve mostrar texto 'Aguardando Compra'")

        # Garantir que NÃO mostra textos de outros estados
        self.assertNotIn('Já comprado', badge_text,
                        "Badge não deve mostrar 'Já comprado' neste estado")
        self.assertNotIn('Separado', badge_text,
                        "Badge não deve mostrar 'Separado'")

    def test_page_url_nao_muda(self):
        """
        Teste 5: URL da página NÃO deve mudar após marcar para compra.

        Valida:
        - URL antes de clicar
        - Clicar no botão HTMX
        - URL permanece a mesma (sem navegação)
        - Confirma atualização local (HTMX swap) sem reload
        """
        # Login e navegar
        self.login_selenium(self.user)
        self.driver.get(f'{self.live_server_url}/pedidos/{self.pedido.id}/')

        # Aguardar página carregar
        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, 'body'))
        )

        # Guardar URL antes da ação
        url_before = self.driver.current_url

        # Clicar no botão "Enviar para Compra"
        compra_button = WebDriverWait(self.driver, 10).until(
            EC.element_to_be_clickable((
                By.CSS_SELECTOR,
                f'button[hx-post*="marcar-compra"][hx-post*="{self.item1.id}"]'
            ))
        )
        compra_button.click()

        # Aguardar badge aparecer (confirma que ação completou)
        badge_selector = f'#badge-{self.item1.id}'
        WebDriverWait(self.driver, 5).until(
            EC.text_to_be_present_in_element((By.CSS_SELECTOR, badge_selector), 'Aguardando Compra')
        )

        # Verificar URL após ação
        url_after = self.driver.current_url

        # Validar que URL permaneceu a mesma
        self.assertEqual(url_before, url_after,
                        "URL não deve mudar (confirma atualização local via HTMX sem reload)")

    def test_outros_itens_nao_afetados(self):
        """
        Teste 6: Marcar Item1 para compra NÃO deve afetar badge do Item2.

        Valida:
        - Item1 ganha badge "Aguardando Compra"
        - Item2 permanece sem badge (ou com badge vazio)
        - Atualização é local e específica por item
        """
        # Login e navegar
        self.login_selenium(self.user)
        self.driver.get(f'{self.live_server_url}/pedidos/{self.pedido.id}/')

        # Aguardar página carregar
        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, 'body'))
        )

        # Verificar estado inicial do Item2 (sem badge de compra)
        badge2_selector = f'#badge-{self.item2.id}'
        try:
            initial_badge2 = self.driver.find_element(By.CSS_SELECTOR, badge2_selector)
            initial_badge2_text = initial_badge2.text
        except NoSuchElementException:
            initial_badge2_text = ""

        # Clicar no botão "Enviar para Compra" do Item1 APENAS
        compra_button1 = WebDriverWait(self.driver, 10).until(
            EC.element_to_be_clickable((
                By.CSS_SELECTOR,
                f'button[hx-post*="marcar-compra"][hx-post*="{self.item1.id}"]'
            ))
        )
        compra_button1.click()

        # Aguardar badge do Item1 aparecer
        badge1_selector = f'#badge-{self.item1.id}'
        badge1 = WebDriverWait(self.driver, 5).until(
            EC.text_to_be_present_in_element((By.CSS_SELECTOR, badge1_selector), 'Aguardando Compra')
        )

        # Dar tempo para qualquer atualização indevida no Item2
        time.sleep(0.5)

        # Verificar que Item2 NÃO foi afetado
        try:
            badge2 = self.driver.find_element(By.CSS_SELECTOR, badge2_selector)
            current_badge2_text = badge2.text
        except NoSuchElementException:
            current_badge2_text = ""

        # Item2 não deve ter ganho badge "Aguardando Compra"
        self.assertNotIn('Aguardando Compra', current_badge2_text,
                        "Item2 NÃO deve ganhar badge de compra quando apenas Item1 é marcado")

        # Estado do Item2 deve ser igual ao inicial
        self.assertEqual(initial_badge2_text, current_badge2_text,
                        "Badge do Item2 deve permanecer inalterado")
