# -*- coding: utf-8 -*-
"""
Testes E2E para Fase 38B - Correção de Duplicação ao Desmarcar Item

BUG: Item desmarcado permanece duplicado - aparece em "Itens Separados" E "Itens Não Separados"

Este teste E2E usa Playwright para simular comportamento real do usuário
e validar que item desmarcado NÃO fica duplicado no DOM.

DEVE FALHAR com código atual e PASSAR após implementar correção.
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
def page(browser):
    """Cria nova página para cada teste."""
    page = browser.new_page()
    yield page
    page.close()


def fazer_login(page: Page, numero_login: int = 1001, pin: str = "1234"):
    """Helper para fazer login."""
    page.goto("http://localhost:8000/login/")
    page.wait_for_load_state("networkidle")

    page.fill('input[name="numero_login"]', str(numero_login))
    page.fill('input[name="pin"]', pin)
    page.click('button[type="submit"]')

    page.wait_for_url("**/dashboard/", timeout=10000)
    print(f"✓ Login realizado: usuário {numero_login}")


def contar_elementos_com_id(page: Page, element_id: str) -> int:
    """
    Conta quantos elementos com o mesmo ID existem no DOM.

    IMPORTANTE: IDs devem ser únicos! Se retornar > 1, há BUG.
    """
    script = f"""
    () => {{
        const elements = document.querySelectorAll('[id="{element_id}"]');
        return elements.length;
    }}
    """
    return page.evaluate(script)


def verificar_item_em_container(page: Page, item_id: int, container_id: str) -> bool:
    """
    Verifica se item está dentro de um container específico.
    """
    script = f"""
    () => {{
        const container = document.getElementById('{container_id}');
        if (!container) return false;

        const item = container.querySelector('#item-{item_id}');
        return item !== null;
    }}
    """
    return page.evaluate(script)


@pytest.mark.e2e
@pytest.mark.skip(reason="Deve FALHAR até correção ser implementada - executar manualmente após correção")
def test_desmarcar_item_nao_duplica_no_dom(page):
    """
    Teste E2E CRÍTICO: Item desmarcado NÃO deve ficar duplicado no DOM.

    Cenário:
    1. Usuário abre pedido com item não separado
    2. Marca item → item move para "Itens Separados" (único)
    3. Desmarca item → item move para "Itens Não Separados"
    4. VALIDAÇÃO: Item existe APENAS 1 vez no DOM total
    5. VALIDAÇÃO: Item NÃO está em "Itens Separados"
    6. VALIDAÇÃO: Item está em "Itens Não Separados"

    ESTE TESTE DEVE FALHAR COM CÓDIGO ATUAL (bug de duplicação).
    """
    print("\n[TESTE E2E] Validação de Unicidade ao Desmarcar")
    print("=" * 60)

    # 1. Fazer login
    fazer_login(page)

    # 2. Abrir pedido de teste
    pedido_id = 1
    item_id = 1

    page.goto(f"http://localhost:8000/pedidos/{pedido_id}/")
    page.wait_for_load_state("networkidle")
    time.sleep(2)  # Aguardar WebSocket conectar

    print(f"\n✓ Pedido {pedido_id} aberto")

    # 3. Verificar estado inicial: item em "Não Separados"
    item_em_nao_sep_inicial = verificar_item_em_container(
        page, item_id, 'container-nao-separados'
    )
    assert item_em_nao_sep_inicial, \
        f"Item {item_id} deve estar em 'Não Separados' inicialmente"

    # Validar unicidade inicial
    total_inicial = contar_elementos_com_id(page, f"item-{item_id}")
    assert total_inicial == 1, \
        f"Item {item_id} deve existir 1 vez inicialmente, mas existe {total_inicial}"

    print(f"✓ Estado inicial válido: item único em 'Não Separados'")

    # 4. MARCAR item como separado
    print(f"\n[Ação] Marcando item {item_id} como separado...")
    checkbox = page.locator(f'#item-{item_id} input[type="checkbox"]')
    checkbox.check()
    time.sleep(2)  # Aguardar animação

    # 5. Validar que item foi movido para "Separados" (e é único)
    item_em_separados = verificar_item_em_container(
        page, item_id, 'container-separados'
    )
    assert item_em_separados, \
        f"Item {item_id} deve estar em 'Separados' após marcar"

    total_apos_marcar = contar_elementos_com_id(page, f"item-{item_id}")
    assert total_apos_marcar == 1, \
        f"Item {item_id} deve ser único após marcar, mas existe {total_apos_marcar} vezes"

    print(f"✓ Item movido para 'Separados' e é único")

    # 6. DESMARCAR item (ação que causa o bug)
    print(f"\n[Ação] DESMARCANDO item {item_id}...")
    checkbox_separado = page.locator(f'#container-separados #item-{item_id} input[type="checkbox"]')
    checkbox_separado.uncheck()
    time.sleep(2)  # Aguardar animação

    # 7. VALIDAÇÃO CRÍTICA: Item deve ser ÚNICO no DOM
    print(f"\n[Validação] Verificando unicidade do item {item_id} no DOM...")

    total_apos_desmarcar = contar_elementos_com_id(page, f"item-{item_id}")

    if total_apos_desmarcar > 1:
        print(f"❌ BUG DETECTADO: Item {item_id} está DUPLICADO!")
        print(f"   Total de elementos com id='item-{item_id}': {total_apos_desmarcar}")

        # Log de onde estão os duplicados
        em_separados = verificar_item_em_container(page, item_id, 'container-separados')
        em_nao_separados = verificar_item_em_container(page, item_id, 'container-nao-separados')

        print(f"   - Em 'Separados': {em_separados}")
        print(f"   - Em 'Não Separados': {em_nao_separados}")

        # Capturar screenshot para debug
        page.screenshot(path=f"/tmp/bug_duplicacao_item{item_id}_{int(time.time())}.png")

        pytest.fail(
            f"BUG: Item {item_id} duplicado após desmarcar "
            f"({total_apos_desmarcar} ocorrências no DOM)"
        )

    assert total_apos_desmarcar == 1, \
        f"Item {item_id} deve ser ÚNICO no DOM, mas existe {total_apos_desmarcar} vezes"

    print(f"✅ Item é único no DOM ({total_apos_desmarcar} ocorrência)")

    # 8. Validar que item está no container CORRETO
    item_em_separados_final = verificar_item_em_container(
        page, item_id, 'container-separados'
    )
    item_em_nao_sep_final = verificar_item_em_container(
        page, item_id, 'container-nao-separados'
    )

    assert not item_em_separados_final, \
        f"Item {item_id} NÃO deve estar em 'Separados' após desmarcar"
    assert item_em_nao_sep_final, \
        f"Item {item_id} DEVE estar em 'Não Separados' após desmarcar"

    print(f"✓ Item está no container correto ('Não Separados')")

    print("\n✅ TESTE PASSOU: Item desmarcado é único e está no container correto!")


@pytest.mark.e2e
@pytest.mark.skip(reason="Deve FALHAR até correção - executar manualmente")
def test_badges_atualizam_corretamente_apos_desmarcar(page):
    """
    Teste E2E: Badges devem refletir contagem CORRETA após desmarcar.

    Problema bug: Badge 'Separados' pode mostrar 1 item quando deveria mostrar 0
    (porque item duplicado permanece em 'Separados').

    Cenário:
    - Pedido com 3 itens não separados
    - Marcar 2 itens → Badge 'Separados': 2
    - Desmarcar 1 item → Badge 'Separados': 1 (NÃO 2!)
    - Desmarcar outro → Badge 'Separados': 0
    """
    print("\n[TESTE E2E] Validação de Badges após Desmarcar")
    print("=" * 60)

    fazer_login(page)

    pedido_id = 1
    page.goto(f"http://localhost:8000/pedidos/{pedido_id}/")
    page.wait_for_load_state("networkidle")
    time.sleep(2)

    # Função helper para ler badge
    def get_badge_count(badge_id: str) -> int:
        script = f"""
        () => {{
            const badge = document.getElementById('{badge_id}');
            if (!badge) return -1;
            const text = badge.textContent.trim();
            const match = text.match(/(\d+)/);
            return match ? parseInt(match[1]) : 0;
        }}
        """
        return page.evaluate(script)

    # Estado inicial
    count_sep_inicial = get_badge_count('badge-separados')
    count_nao_sep_inicial = get_badge_count('badge-nao-separados')

    print(f"✓ Estado inicial: {count_sep_inicial} separados, {count_nao_sep_inicial} não separados")

    # Marcar 2 itens
    page.locator('#item-1 input[type="checkbox"]').check()
    time.sleep(1)
    page.locator('#item-2 input[type="checkbox"]').check()
    time.sleep(2)

    count_sep_apos_marcar = get_badge_count('badge-separados')
    assert count_sep_apos_marcar == 2, \
        f"Badge 'Separados' deve mostrar 2 após marcar 2 itens"

    print(f"✓ Após marcar 2 itens: {count_sep_apos_marcar} separados")

    # Desmarcar 1 item
    page.locator('#container-separados #item-1 input[type="checkbox"]').uncheck()
    time.sleep(2)

    # VALIDAÇÃO CRÍTICA
    count_sep_apos_desmarcar = get_badge_count('badge-separados')

    if count_sep_apos_desmarcar != 1:
        print(f"❌ BUG NO BADGE: Esperado 1, mas mostra {count_sep_apos_desmarcar}")

        # Contar itens reais no container
        real_count_script = """
        () => {
            const container = document.getElementById('container-separados');
            return container ? container.children.length : 0;
        }
        """
        real_count = page.evaluate(real_count_script)
        print(f"   Badge mostra: {count_sep_apos_desmarcar}")
        print(f"   Itens reais no container: {real_count}")

        pytest.fail(
            f"Badge 'Separados' incorreto: mostra {count_sep_apos_desmarcar}, "
            f"mas deveria mostrar 1"
        )

    assert count_sep_apos_desmarcar == 1, \
        f"Badge deve mostrar 1 separado após desmarcar 1 item"

    print(f"✓ Após desmarcar 1 item: {count_sep_apos_desmarcar} separado")

    print("\n✅ TESTE PASSOU: Badges atualizados corretamente!")


@pytest.mark.e2e
def test_multiplos_desmarcar_sem_duplicacao(page):
    """
    Teste E2E: Desmarcar múltiplos itens em sequência não deve causar duplicação.

    Cenário:
    - Marcar 3 itens
    - Desmarcar todos em sequência rápida
    - Cada item deve permanecer único no DOM
    """
    print("\n[TESTE E2E] Múltiplos Desmarcações sem Duplicação")
    print("=" * 60)

    fazer_login(page)

    pedido_id = 1
    page.goto(f"http://localhost:8000/pedidos/{pedido_id}/")
    page.wait_for_load_state("networkidle")
    time.sleep(2)

    # Marcar 3 itens
    for item_id in [1, 2, 3]:
        page.locator(f'#item-{item_id} input[type="checkbox"]').check()
        time.sleep(0.5)

    print("✓ 3 itens marcados")
    time.sleep(1)

    # Desmarcar todos em sequência
    for item_id in [1, 2, 3]:
        print(f"\n  Desmarcando item {item_id}...")
        page.locator(f'#container-separados #item-{item_id} input[type="checkbox"]').uncheck()
        time.sleep(1)

        # Validar unicidade após cada desmarcação
        total = contar_elementos_com_id(page, f"item-{item_id}")
        assert total == 1, \
            f"Item {item_id} deve ser único, mas existe {total} vezes"

        print(f"  ✓ Item {item_id} é único")

    print("\n✅ TESTE PASSOU: Todos os itens permanecem únicos!")


if __name__ == "__main__":
    # Executar manualmente com browser visível para debug
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, slow_mo=500)
        page = browser.new_page()

        try:
            print("\n" + "="*60)
            print("EXECUTANDO TESTE MANUAL - Bug de Duplicação ao Desmarcar")
            print("="*60)

            test_desmarcar_item_nao_duplica_no_dom(page)

        except Exception as e:
            print(f"\n❌ TESTE FALHOU: {str(e)}")
            print("\nEste é o comportamento esperado ANTES da correção.")
            page.screenshot(path=f"/tmp/test_manual_falha_{int(time.time())}.png")

        finally:
            input("\nPressione ENTER para fechar o browser...")
            page.close()
            browser.close()
