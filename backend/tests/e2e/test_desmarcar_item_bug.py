# -*- coding: utf-8 -*-
"""
Testes E2E para reproduzir e validar correção do bug de desmarcação de itens.

FASE 38 - Bug Fix: Item desmarcado aparece na seção errada até refresh

BUG REPRODUZIDO:
1. Usuário marca item como separado → item vai para "Itens Separados" ✅
2. Usuário desmarca item → item faz fade out mas reaparece em "Itens Separados" ❌
3. Usuário atualiza página → item aparece corretamente em "Itens Não Separados" ✅

COMPORTAMENTO ESPERADO:
- Ao desmarcar, item deve aparecer imediatamente em "Itens Não Separados"
- WebSocket deve sincronizar estado para outros usuários em tempo real

Este teste usa Playwright para simular interação real do usuário.
"""

import pytest
from playwright.sync_api import sync_playwright, Page, expect
import time


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


def fazer_login(page: Page, numero_login: int = 1001, pin: str = "1234"):
    """Helper para fazer login."""
    page.goto("http://localhost:8000/login/")
    page.wait_for_load_state("networkidle")

    page.fill('input[name="numero_login"]', str(numero_login))
    page.fill('input[name="pin"]', pin)
    page.click('button[type="submit"]')

    page.wait_for_url("**/dashboard/", timeout=10000)
    print(f"✓ Login realizado: usuário {numero_login}")


def criar_pedido_teste_via_api(page: Page) -> dict:
    """
    Cria pedido de teste via API interna do Django.
    Retorna dict com pedido_id e item_ids.
    """
    # Navegar para página admin/criar pedido (se existir) ou usar fixture
    # Por simplicidade, assumimos que existe fixture no conftest.py
    # que cria pedido com itens não separados

    # TODO: Implementar criação via API ou fixture
    # Por ora, retorna IDs fictícios (deve ser substituído por fixture real)
    return {
        'pedido_id': 1,  # Placeholder
        'item_ids': [1, 2, 3]  # Placeholder
    }


@pytest.mark.e2e
@pytest.mark.skip(reason="Teste deve FALHAR até bug ser corrigido - executar manualmente")
def test_desmarcar_item_aparece_secao_correta_sem_refresh(browser):
    """
    Teste E2E: Ao desmarcar item separado, ele deve aparecer
    imediatamente em "Itens Não Separados" SEM REFRESH.

    Cenário:
    1. Usuário abre pedido com item não separado
    2. Marca item como separado → item vai para seção "Itens Separados"
    3. Desmarca item → item faz fade out
    4. BUG: Item reaparece em "Itens Separados" (errado)
    5. ESPERADO: Item deveria aparecer em "Itens Não Separados"

    ESTE TESTE DEVE FALHAR ANTES DA CORREÇÃO!
    """
    page = browser.new_page()

    try:
        print("\n[TESTE] Desmarcar Item - Bug de Agrupamento")
        print("=" * 60)

        # 1. Fazer login
        fazer_login(page)

        # 2. Abrir pedido de teste (usar fixture ou criar via API)
        # Por ora, assumimos pedido_id = 1
        pedido_id = 1
        item_id = 1

        page.goto(f"http://localhost:8000/pedidos/{pedido_id}/")
        page.wait_for_load_state("networkidle")
        time.sleep(2)  # Aguardar WebSocket conectar

        print(f"\n✓ Pedido {pedido_id} aberto")

        # 3. Verificar que item está na seção "Itens Não Separados"
        container_nao_separados = page.locator('#container-nao-separados')
        item_inicial = container_nao_separados.locator(f'#item-{item_id}')

        expect(item_inicial).to_be_visible(timeout=5000)
        print(f"✓ Item {item_id} está em 'Itens Não Separados' (estado inicial)")

        # 4. Marcar item como separado
        print(f"\n[Ação] Marcando item {item_id} como separado...")
        checkbox = item_inicial.locator('input[type="checkbox"]')
        checkbox.check()

        # Aguardar animação e atualização
        time.sleep(2)

        # 5. Verificar que item foi movido para "Itens Separados"
        container_separados = page.locator('#container-separados')
        item_separado = container_separados.locator(f'#item-{item_id}')

        expect(item_separado).to_be_visible(timeout=5000)
        print(f"✓ Item {item_id} movido para 'Itens Separados'")

        # 6. DESMARCAR item (ação que causa o bug)
        print(f"\n[Ação] DESMARCANDO item {item_id}...")
        checkbox_separado = item_separado.locator('input[type="checkbox"]')
        checkbox_separado.uncheck()

        # Aguardar animação de fade out
        time.sleep(1.5)

        # 7. VERIFICAR BUG: Item deve aparecer em "Itens Não Separados"
        print(f"\n[Verificação] Onde o item {item_id} reapareceu?")

        # Verificar se item está em "Itens Não Separados"
        item_desmarcado_nao_sep = container_nao_separados.locator(f'#item-{item_id}')

        # Verificar se item ainda está em "Itens Separados" (BUG)
        item_desmarcado_sep = container_separados.locator(f'#item-{item_id}')

        # ASSERÇÃO CRÍTICA: Item DEVE estar em não-separados
        try:
            expect(item_desmarcado_nao_sep).to_be_visible(timeout=3000)
            print(f"✅ CORRETO: Item {item_id} apareceu em 'Itens Não Separados'")
        except AssertionError:
            # Bug detectado
            print(f"❌ BUG DETECTADO: Item {item_id} NÃO apareceu em 'Itens Não Separados'")

            # Verificar se está na seção errada
            if item_desmarcado_sep.is_visible():
                print(f"❌ Item {item_id} permaneceu em 'Itens Separados' (ERRADO)")
                pytest.fail(
                    f"BUG CONFIRMADO: Item {item_id} desmarcado reapareceu "
                    f"em 'Itens Separados' em vez de 'Itens Não Separados'"
                )
            else:
                print(f"❌ Item {item_id} desapareceu completamente (ERRO CRÍTICO)")
                pytest.fail(f"Item {item_id} não está em nenhuma seção após desmarcar")

        # 8. Verificar que item NÃO está mais em "Itens Separados"
        expect(item_desmarcado_sep).not_to_be_visible(timeout=1000)
        print(f"✓ Item {item_id} removido de 'Itens Separados'")

        print("\n✅ TESTE PASSOU: Item desmarcado apareceu na seção correta!")

    except Exception as e:
        # Capturar screenshot para debug
        page.screenshot(path=f"/tmp/test_desmarcar_bug_{int(time.time())}.png")
        print(f"\n❌ TESTE FALHOU: {str(e)}")
        raise

    finally:
        page.close()


@pytest.mark.e2e
@pytest.mark.skip(reason="Teste deve FALHAR até bug ser corrigido - executar manualmente")
def test_desmarcar_item_realtime_multiplos_usuarios(contexts):
    """
    Teste E2E: Desmarcar item deve sincronizar em tempo real para outros usuários.

    Cenário:
    1. Browser 1 e Browser 2 abrem o mesmo pedido
    2. Browser 1 marca item como separado → Browser 2 vê atualização
    3. Browser 1 desmarca item → Browser 2 deve ver item em "Não Separados"
    4. BUG: Browser 2 vê item na seção errada

    ESTE TESTE DEVE FALHAR ANTES DA CORREÇÃO!
    """
    context1, context2 = contexts
    page1 = context1.new_page()
    page2 = context2.new_page()

    try:
        print("\n[TESTE] Desmarcar Item - Tempo Real (2 Usuários)")
        print("=" * 60)

        # 1. Login nos 2 browsers
        fazer_login(page1, numero_login=1001, pin="1234")
        fazer_login(page2, numero_login=1002, pin="1234")

        # 2. Abrir mesmo pedido
        pedido_id = 1  # TODO: Usar fixture
        item_id = 1

        page1.goto(f"http://localhost:8000/pedidos/{pedido_id}/")
        page2.goto(f"http://localhost:8000/pedidos/{pedido_id}/")

        page1.wait_for_load_state("networkidle")
        page2.wait_for_load_state("networkidle")
        time.sleep(3)  # Aguardar WebSocket conectar em ambos

        print(f"✓ Ambos os browsers abriram pedido {pedido_id}")

        # 3. Browser 1: Marcar item como separado
        print(f"\n[Browser 1] Marcando item {item_id}...")
        checkbox1 = page1.locator(f'#item-{item_id} input[type="checkbox"]')
        checkbox1.check()
        time.sleep(3)  # Aguardar WebSocket propagar

        # 4. Browser 2: Verificar que item foi atualizado
        container_sep_2 = page2.locator('#container-separados')
        item_sep_2 = container_sep_2.locator(f'#item-{item_id}')

        expect(item_sep_2).to_be_visible(timeout=5000)
        print(f"✓ [Browser 2] Item {item_id} apareceu em 'Itens Separados'")

        # 5. Browser 1: DESMARCAR item (causa o bug)
        print(f"\n[Browser 1] DESMARCANDO item {item_id}...")
        checkbox1_sep = page1.locator(f'#container-separados #item-{item_id} input[type="checkbox"]')
        checkbox1_sep.uncheck()
        time.sleep(3)  # Aguardar WebSocket propagar

        # 6. Browser 2: VERIFICAR BUG
        print(f"\n[Browser 2] Verificando onde item {item_id} apareceu...")

        container_nao_sep_2 = page2.locator('#container-nao-separados')
        item_nao_sep_2 = container_nao_sep_2.locator(f'#item-{item_id}')

        # ASSERÇÃO: Item DEVE estar em não-separados no Browser 2
        try:
            expect(item_nao_sep_2).to_be_visible(timeout=5000)
            print(f"✅ [Browser 2] Item {item_id} apareceu corretamente em 'Não Separados'")
        except AssertionError:
            print(f"❌ BUG DETECTADO: [Browser 2] Item não apareceu em 'Não Separados'")

            # Verificar se está na seção errada
            if item_sep_2.is_visible():
                pytest.fail(
                    f"BUG CONFIRMADO: Browser 2 vê item {item_id} em 'Itens Separados' "
                    f"após desmarcar (deveria estar em 'Não Separados')"
                )
            else:
                pytest.fail(f"Item {item_id} desapareceu no Browser 2")

        print("\n✅ TESTE PASSOU: Desmarcação sincronizada corretamente!")

    except Exception as e:
        page1.screenshot(path=f"/tmp/test_desmarcar_realtime_p1_{int(time.time())}.png")
        page2.screenshot(path=f"/tmp/test_desmarcar_realtime_p2_{int(time.time())}.png")
        print(f"\n❌ TESTE FALHOU: {str(e)}")
        raise

    finally:
        page1.close()
        page2.close()


@pytest.mark.e2e
def test_progresso_atualiza_corretamente_ao_desmarcar(browser):
    """
    Teste E2E: Barra de progresso deve atualizar corretamente ao desmarcar item.

    Cenário:
    1. Pedido com 3 itens, todos não separados (0%)
    2. Marcar 2 itens → progresso 66%
    3. Desmarcar 1 item → progresso 33%
    4. Verificar que contador e barra estão corretos
    """
    page = browser.new_page()

    try:
        print("\n[TESTE] Progresso ao Desmarcar")
        print("=" * 60)

        fazer_login(page)

        pedido_id = 1  # TODO: Usar fixture com 3 itens
        page.goto(f"http://localhost:8000/pedidos/{pedido_id}/")
        page.wait_for_load_state("networkidle")
        time.sleep(2)

        # Verificar progresso inicial (0%)
        progresso = page.locator('#progresso-percentual')
        expect(progresso).to_have_text('0%')
        print("✓ Progresso inicial: 0%")

        # Marcar 2 itens
        page.locator('#item-1 input[type="checkbox"]').check()
        time.sleep(1)
        page.locator('#item-2 input[type="checkbox"]').check()
        time.sleep(2)

        # Verificar progresso 66%
        expect(progresso).to_have_text('66%', timeout=3000)
        print("✓ Após marcar 2/3 itens: 66%")

        # Desmarcar 1 item
        page.locator('#container-separados #item-1 input[type="checkbox"]').uncheck()
        time.sleep(2)

        # Verificar progresso 33%
        expect(progresso).to_have_text('33%', timeout=3000)
        print("✓ Após desmarcar 1 item: 33%")

        # Verificar contador de itens
        contador = page.locator('#contador-itens')
        expect(contador).to_have_text('(1/3)')
        print("✓ Contador atualizado: 1/3")

        print("\n✅ TESTE PASSOU: Progresso atualiza corretamente!")

    finally:
        page.close()


if __name__ == "__main__":
    # Executar teste manualmente para ver bug
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, slow_mo=1000)  # slow_mo para visualizar

        try:
            print("\n" + "="*60)
            print("EXECUTANDO TESTE MANUAL - Bug de Desmarcação")
            print("="*60)

            # Executar teste principal
            test_desmarcar_item_aparece_secao_correta_sem_refresh(browser)

        except Exception as e:
            print(f"\n❌ BUG CONFIRMADO: {str(e)}")
            print("\nEste é o comportamento esperado ANTES da correção.")

        finally:
            browser.close()
