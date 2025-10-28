#!/usr/bin/env python3
"""
Script para capturar screenshots das páginas do site usando Playwright.
Útil para que o Claude possa visualizar o site.
"""
import asyncio
from playwright.async_api import async_playwright
import sys
from pathlib import Path

# URLs para capturar
URLS = {
    'login': 'http://localhost:8000/',
    'dashboard': 'http://localhost:8000/dashboard/',
    'historico': 'http://localhost:8000/historico/',
    'metricas': 'http://localhost:8000/metricas/',
    'painel_compras': 'http://localhost:8000/compras/',
    'admin_panel': 'http://localhost:8000/usuarios/',
    'criar_usuario': 'http://localhost:8000/usuarios/criar/',
}

# Diretório para salvar screenshots
SCREENSHOTS_DIR = Path(__file__).parent / 'screenshots'
SCREENSHOTS_DIR.mkdir(exist_ok=True)


async def capture_screenshot(page, name, url, width=1920, height=1080):
    """Captura screenshot de uma página específica."""
    print(f"📸 Capturando {name}...")

    try:
        # Navegar para a URL
        await page.goto(url, wait_until='networkidle', timeout=30000)

        # Aguardar um pouco para garantir que tudo carregou
        await page.wait_for_timeout(2000)

        # Capturar screenshot
        screenshot_path = SCREENSHOTS_DIR / f"{name}.png"
        await page.screenshot(path=str(screenshot_path), full_page=True)

        print(f"✅ {name} salvo em: {screenshot_path}")
        return True

    except Exception as e:
        print(f"❌ Erro ao capturar {name}: {str(e)}")
        return False


async def capture_authenticated_pages(page, numero_login='9999', pin='1234'):
    """Captura screenshots das páginas autenticadas."""
    print(f"\n🔐 Fazendo login com número {numero_login}...")

    try:
        # Ir para a página de login
        await page.goto('http://localhost:8000/', wait_until='networkidle')

        # Preencher formulário de login (o sistema usa numero_login e pin)
        await page.fill('input[name="numero_login"]', numero_login)
        await page.fill('input[name="pin"]', pin)

        # Clicar no botão de login
        await page.click('button[type="submit"]')

        # Aguardar redirecionamento
        await page.wait_for_url('**/dashboard/', timeout=10000)
        print("✅ Login realizado com sucesso!")

        # Capturar todas as páginas autenticadas
        results = {}
        for name, url in URLS.items():
            if name != 'login':  # Pular a página de login
                results[name] = await capture_screenshot(page, name, url)

        return results

    except Exception as e:
        print(f"❌ Erro durante autenticação: {str(e)}")
        return {}


async def main():
    """Função principal."""
    print("🎭 Iniciando Playwright...")

    async with async_playwright() as p:
        # Lançar navegador
        browser = await p.chromium.launch(headless=True)

        # Criar contexto com viewport grande
        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        )

        page = await context.new_page()

        # Capturar página de login
        await capture_screenshot(page, 'login', URLS['login'])

        # Capturar páginas autenticadas
        results = await capture_authenticated_pages(page)

        # Fechar navegador
        await browser.close()

        # Resumo
        print("\n" + "="*50)
        print("📊 RESUMO")
        print("="*50)
        print(f"Screenshots salvos em: {SCREENSHOTS_DIR}")

        successful = sum(1 for v in results.values() if v)
        total = len(results) + 1  # +1 para a página de login
        print(f"✅ {successful + 1}/{total} páginas capturadas com sucesso")

        return 0 if successful == len(results) else 1


if __name__ == '__main__':
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n⚠️  Operação cancelada pelo usuário")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Erro fatal: {str(e)}")
        sys.exit(1)
