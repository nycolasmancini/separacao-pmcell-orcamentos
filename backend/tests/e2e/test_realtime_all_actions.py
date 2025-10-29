# -*- coding: utf-8 -*-
"""
Testes E2E para validar atualizações em tempo real de TODAS as ações.

Fase 35: Validar que marcar para compra e substituir item também atualizam em tempo real,
não apenas marcar como separado.

Usando Playwright para simular 2 navegadores conectados simultaneamente.
"""

import pytest
from playwright.sync_api import sync_playwright, Page, Browser, BrowserContext, expect
import time


def ler_dados_teste():
    """Lê dados de teste do arquivo temporário criado pelo conftest.py."""
    dados = {}
    try:
        with open('/tmp/e2e_test_data.txt', 'r') as f:
            for line in f:
                key, value = line.strip().split('=')
                dados[key] = int(value)
    except FileNotFoundError:
        raise RuntimeError(
            "Arquivo de dados de teste não encontrado. "
            "Execute 'pytest tests/e2e/conftest.py' primeiro para gerar dados."
        )
    return dados


@pytest.fixture(scope="module")
def browser():
    """Inicializa Playwright e retorna browser."""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        yield browser
        browser.close()


@pytest.fixture
def contexts(browser):
    """Cria 2 contextos de browser (2 usuários simultâneos)."""
    context1 = browser.new_context()
    context2 = browser.new_context()
    yield context1, context2
    context1.close()
    context2.close()


@pytest.fixture(scope="module")
def dados_teste():
    """Retorna dados de teste (IDs de pedido, itens, etc)."""
    return ler_dados_teste()


def fazer_login(page: Page, numero_login: int, pin: str):
    """Helper para fazer login."""
    page.goto("http://192.168.15.110:8000/login/")
    page.wait_for_load_state("networkidle")

    page.fill('input[name="numero_login"]', str(numero_login))
    page.fill('input[name="pin"]', pin)
    page.click('button[type="submit"]')

    page.wait_for_url("**/dashboard/", timeout=10000)
    print(f"✓ Login realizado: usuário {numero_login}")


def abrir_pedido(page: Page, pedido_id: int):
    """Helper para abrir página de detalhe do pedido."""
    page.goto(f"http://192.168.15.110:8000/pedidos/{pedido_id}/")
    page.wait_for_load_state("networkidle")

    # Aguardar WebSocket conectar (verificar console logs)
    time.sleep(2)
    print(f"✓ Pedido {pedido_id} aberto e WebSocket conectado")


def marcar_item_para_compra(page: Page, item_id: int):
    """Helper para marcar item para compra."""
    # Clicar no menu dropdown do item
    menu_button = page.locator(f'#item-{item_id} button[data-dropdown-toggle]')
    menu_button.click()

    # Aguardar menu abrir
    time.sleep(0.5)

    # Clicar em "Marcar para Compra"
    page.locator(f'text="📦 Marcar para Compra"').click()

    # Aguardar requisição HTMX completar
    time.sleep(1)
    print(f"✓ Item {item_id} marcado para compra")


def substituir_item(page: Page, item_id: int, novo_codigo: str = "99999"):
    """Helper para substituir item."""
    # Clicar no menu dropdown do item
    menu_button = page.locator(f'#item-{item_id} button[data-dropdown-toggle]')
    menu_button.click()

    # Aguardar menu abrir
    time.sleep(0.5)

    # Clicar em "Marcar como Substituído"
    page.locator(f'text="🔄 Marcar como Substituído"').click()

    # Preencher modal com código substituto
    page.wait_for_selector('input[name="codigo_substituto"]', state="visible")
    page.fill('input[name="codigo_substituto"]', novo_codigo)

    # Confirmar substituição
    page.locator('button:has-text("Confirmar Substituição")').click()

    # Aguardar requisição HTMX completar
    time.sleep(1)
    print(f"✓ Item {item_id} substituído por {novo_codigo}")


def verificar_item_para_compra(page: Page, item_id: int):
    """Verifica se item está marcado para compra (badge azul/laranja)."""
    item = page.locator(f'#item-{item_id}')

    # Badge deve conter "Aguardando Compra" ou "Em Compra"
    badge = item.locator('.badge')
    badge_text = badge.text_content()

    assert "Aguardando" in badge_text or "Compra" in badge_text, \
        f"Item {item_id} deveria estar marcado para compra, mas badge é: {badge_text}"

    print(f"✓ Item {item_id} está marcado para compra: {badge_text}")


def verificar_item_substituido(page: Page, item_id: int):
    """Verifica se item está marcado como substituído (badge verde)."""
    item = page.locator(f'#item-{item_id}')

    # Badge deve conter "Substituído"
    badge = item.locator('.badge')
    badge_text = badge.text_content()

    assert "Substituído" in badge_text or "Substituido" in badge_text, \
        f"Item {item_id} deveria estar substituído, mas badge é: {badge_text}"

    print(f"✓ Item {item_id} está substituído: {badge_text}")


@pytest.mark.e2e
def test_marcar_para_compra_atualiza_em_tempo_real(contexts, dados_teste):
    """
    Teste E2E: Marcar item para compra deve atualizar em tempo real nos 2 browsers.

    Cenário:
    1. Browser 1 (Separador) e Browser 2 (Separador) abrem o mesmo pedido
    2. Browser 1 marca item para compra
    3. Browser 2 deve ver o item atualizado automaticamente via WebSocket
    """
    context1, context2 = contexts
    page1 = context1.new_page()
    page2 = context2.new_page()

    try:
        print("\n[TESTE] Marcar para compra - Tempo Real")
        print("=" * 60)

        # 1. Login nos 2 browsers (ambos como separador)
        fazer_login(page1, numero_login=dados_teste['SEPARADOR1_LOGIN'], pin="1234")
        fazer_login(page2, numero_login=dados_teste['SEPARADOR2_LOGIN'], pin="1234")

        # 2. Abrir mesmo pedido nos 2 browsers
        pedido_id = dados_teste['PEDIDO_ID']
        item_id = dados_teste['ITEM1_ID']

        abrir_pedido(page1, pedido_id)
        abrir_pedido(page2, pedido_id)

        # 3. No browser 1, marcar item para compra
        print("\n[Browser 1] Marcando item para compra...")
        marcar_item_para_compra(page1, item_id)

        # 4. Aguardar WebSocket propagar evento (1-2 segundos)
        print("[WebSocket] Aguardando propagação do evento...")
        time.sleep(3)

        # 5. No browser 2, verificar se item foi atualizado
        print("\n[Browser 2] Verificando se item foi atualizado...")
        verificar_item_para_compra(page2, item_id)

        print("\n✅ TESTE PASSOU: Item atualizado em tempo real!")

    finally:
        page1.close()
        page2.close()


@pytest.mark.e2e
def test_substituir_item_atualiza_em_tempo_real(contexts, dados_teste):
    """
    Teste E2E: Substituir item deve atualizar em tempo real nos 2 browsers.

    Cenário:
    1. Browser 1 (Separador) e Browser 2 (Separador) abrem o mesmo pedido
    2. Browser 1 substitui item
    3. Browser 2 deve ver o item atualizado automaticamente via WebSocket
    """
    context1, context2 = contexts
    page1 = context1.new_page()
    page2 = context2.new_page()

    try:
        print("\n[TESTE] Substituir item - Tempo Real")
        print("=" * 60)

        # 1. Login nos 2 browsers
        fazer_login(page1, numero_login=dados_teste['SEPARADOR1_LOGIN'], pin="1234")
        fazer_login(page2, numero_login=dados_teste['SEPARADOR2_LOGIN'], pin="1234")

        # 2. Abrir mesmo pedido nos 2 browsers
        pedido_id = dados_teste['PEDIDO_ID']
        item_id = dados_teste['ITEM2_ID']

        abrir_pedido(page1, pedido_id)
        abrir_pedido(page2, pedido_id)

        # 3. No browser 1, substituir item
        print("\n[Browser 1] Substituindo item...")
        substituir_item(page1, item_id, novo_codigo="99999")

        # 4. Aguardar WebSocket propagar evento
        print("[WebSocket] Aguardando propagação do evento...")
        time.sleep(3)

        # 5. No browser 2, verificar se item foi atualizado
        print("\n[Browser 2] Verificando se item foi atualizado...")
        verificar_item_substituido(page2, item_id)

        print("\n✅ TESTE PASSOU: Item atualizado em tempo real!")

    finally:
        page1.close()
        page2.close()


@pytest.mark.e2e
def test_todas_acoes_atualizam_em_tempo_real(contexts, dados_teste):
    """
    Teste E2E completo: Todas as ações (separar, marcar compra, substituir)
    devem atualizar em tempo real.

    Cenário:
    1. Browser 1 e Browser 2 abrem o mesmo pedido
    2. Browser 1 executa 3 ações em itens diferentes
    3. Browser 2 verifica que todos os itens foram atualizados
    """
    context1, context2 = contexts
    page1 = context1.new_page()
    page2 = context2.new_page()

    try:
        print("\n[TESTE] Todas as ações - Tempo Real")
        print("=" * 60)

        # Login e abrir pedido
        fazer_login(page1, numero_login=dados_teste['SEPARADOR1_LOGIN'], pin="1234")
        fazer_login(page2, numero_login=dados_teste['SEPARADOR2_LOGIN'], pin="1234")

        pedido_id = dados_teste['PEDIDO_ID']
        item1_id = dados_teste['ITEM1_ID']
        item2_id = dados_teste['ITEM2_ID']
        item3_id = dados_teste['ITEM3_ID']

        abrir_pedido(page1, pedido_id)
        abrir_pedido(page2, pedido_id)

        # Ação 1: Marcar item 1 como separado
        print(f"\n[Browser 1] Marcando item {item1_id} como separado...")
        page1.locator(f'#item-{item1_id} input[type="checkbox"]').check()
        time.sleep(3)

        # Verificar no browser 2
        expect(page2.locator(f'#item-{item1_id} input[type="checkbox"]')).to_be_checked()
        print(f"✓ Item {item1_id} separado atualizado no Browser 2")

        # Ação 2: Marcar item 2 para compra
        print(f"\n[Browser 1] Marcando item {item2_id} para compra...")
        marcar_item_para_compra(page1, item_id=item2_id)
        time.sleep(3)

        # Verificar no browser 2
        verificar_item_para_compra(page2, item_id=item2_id)

        # Ação 3: Substituir item 3
        print(f"\n[Browser 1] Substituindo item {item3_id}...")
        substituir_item(page1, item_id=item3_id, novo_codigo="88888")
        time.sleep(3)

        # Verificar no browser 2
        verificar_item_substituido(page2, item_id=item3_id)

        print("\n✅ TESTE COMPLETO PASSOU: Todas as ações atualizam em tempo real!")

    finally:
        page1.close()
        page2.close()


if __name__ == "__main__":
    # Executar testes diretamente (sem pytest)
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)  # headless=False para visualizar

        context1 = browser.new_context()
        context2 = browser.new_context()

        try:
            test_marcar_para_compra_atualiza_em_tempo_real((context1, context2))
            test_substituir_item_atualiza_em_tempo_real((context1, context2))
        finally:
            context1.close()
            context2.close()
            browser.close()
