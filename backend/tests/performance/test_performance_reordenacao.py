# -*- coding: utf-8 -*-
"""
Testes de Performance para Reordenação Animada (Fase 39i).

Valida que:
- Animações rodam a 60 FPS
- Múltiplas reordenações simultâneas não travam UI
- Memória não vaza após múltiplas operações
- Tempo de reordenação está dentro de limites aceitáveis
"""

import pytest
import time
from playwright.sync_api import Page, expect
from django.utils import timezone
from core.models import Pedido, ItemPedido, Produto, Usuario


@pytest.mark.django_db
@pytest.mark.performance
class TestPerformanceReordenacao:
    """Testes de performance para reordenação."""

    @pytest.fixture(autouse=True)
    def setup(self, db):
        """Setup que roda antes de cada teste."""
        self.vendedor = Usuario.objects.create(
            numero_login="001",
            nome="Vendedor Teste",
            tipo="VENDEDOR",
            ativo=True
        )
        self.vendedor.set_password("1234")
        self.vendedor.save()

        self.separador = Usuario.objects.create(
            numero_login="002",
            nome="Separador Teste",
            tipo="SEPARADOR",
            ativo=True
        )
        self.separador.set_password("1234")
        self.separador.save()

        self.pedido = Pedido.objects.create(
            numero_orcamento="ORD-001",
            codigo_cliente="CLI-001",
            nome_cliente="Cliente Teste",
            vendedor=self.vendedor,
            logistica="MOTOBOY",
            embalagem="CAIXA",
            status="EM_SEPARACAO"
        )

        # Criar 20 produtos para teste de performance
        self.produtos = []
        for i in range(20):
            produto = Produto.objects.create(
                codigo=f'PROD-{i:03d}',
                descricao=f'Produto {i:03d}',
                quantidade=10,
                valor_unitario=100.00,
                valor_total=1000.00
            )
            self.produtos.append(produto)

    def _login(self, page: Page):
        """Helper para fazer login."""
        page.goto("http://localhost:8000/login/")
        page.fill('input[name="numero_login"]', "002")
        page.fill('input[name="password"]', "1234")
        page.click('button[type="submit"]')
        page.wait_for_url("http://localhost:8000/painel/", timeout=5000)

    def test_tempo_reordenacao_single_item(self, page: Page):
        """
        Tempo de reordenação de 1 item deve ser < 500ms.
        """
        # Criar 10 itens
        for i in range(10):
            ItemPedido.objects.create(
                pedido=self.pedido,
                produto=self.produtos[i],
                quantidade_solicitada=1,
                separado=False
            )

        self._login(page)
        page.goto(f"http://localhost:8000/pedido/{self.pedido.id}/")

        # Medir tempo de reordenação
        items = page.locator('.item-pedido')
        checkbox = items.nth(0).locator('input[type="checkbox"]')

        start_time = time.time()
        checkbox.check()

        # Aguardar animação completar (visual validation)
        time.sleep(0.5)

        end_time = time.time()
        elapsed = (end_time - start_time) * 1000  # ms

        # Validação: deve completar em < 500ms (250ms animação + overhead)
        assert elapsed < 500, f"Reordenação levou {elapsed:.2f}ms (esperado < 500ms)"

    def test_multiplas_reordenacoes_sequenciais_performance(self, page: Page):
        """
        10 reordenações sequenciais devem completar em < 5s.
        """
        # Criar 10 itens
        for i in range(10):
            ItemPedido.objects.create(
                pedido=self.pedido,
                produto=self.produtos[i],
                quantidade_solicitada=1,
                separado=False
            )

        self._login(page)
        page.goto(f"http://localhost:8000/pedido/{self.pedido.id}/")

        # Medir tempo para marcar todos como separados
        start_time = time.time()

        for i in range(10):
            items = page.locator('.item-pedido')
            checkbox = items.nth(0).locator('input[type="checkbox"]')
            checkbox.check()
            time.sleep(0.3)  # Espera mínima entre operações

        end_time = time.time()
        elapsed = (end_time - start_time)

        # Validação: 10 operações em < 5s (média 500ms/operação)
        assert elapsed < 5.0, f"10 reordenações levaram {elapsed:.2f}s (esperado < 5s)"

    def test_reordenacao_lista_grande_20_itens(self, page: Page):
        """
        Reordenação em lista grande (20 itens) deve ser < 700ms.
        """
        # Criar 20 itens
        for i in range(20):
            ItemPedido.objects.create(
                pedido=self.pedido,
                produto=self.produtos[i],
                quantidade_solicitada=1,
                separado=False
            )

        self._login(page)
        page.goto(f"http://localhost:8000/pedido/{self.pedido.id}/")

        # Marcar item do meio (item 10)
        items = page.locator('.item-pedido')
        checkbox = items.nth(10).locator('input[type="checkbox"]')

        start_time = time.time()
        checkbox.check()
        time.sleep(0.5)  # Aguardar animação
        end_time = time.time()

        elapsed = (end_time - start_time) * 1000

        # Validação: mesmo com 20 itens, deve completar em < 700ms
        assert elapsed < 700, f"Reordenação em lista grande levou {elapsed:.2f}ms (esperado < 700ms)"

    def test_calcular_posicao_destino_performance(self, page: Page):
        """
        Função calcularPosicaoDestino() deve executar em < 50ms mesmo com 20 itens.
        """
        # Criar 20 itens
        for i in range(20):
            ItemPedido.objects.create(
                pedido=self.pedido,
                produto=self.produtos[i],
                quantidade_solicitada=1,
                separado=False
            )

        self._login(page)
        page.goto(f"http://localhost:8000/pedido/{self.pedido.id}/}")

        # Executar benchmark JavaScript
        resultado = page.evaluate("""
            () => {
                const container = document.getElementById('lista-itens');
                const item = container.children[10]; // Item do meio

                // Benchmark: 100 execuções
                const start = performance.now();
                for (let i = 0; i < 100; i++) {
                    const descricao = item.querySelector('.text-gray-800').textContent;
                    window.ItemAnimations.calcularPosicaoDestino('separado', descricao, container);
                }
                const end = performance.now();

                return {
                    totalTime: end - start,
                    avgTime: (end - start) / 100
                };
            }
        """)

        # Validação: média < 5ms por execução
        assert resultado['avgTime'] < 5.0, \
            f"calcularPosicaoDestino() média: {resultado['avgTime']:.2f}ms (esperado < 5ms)"

    def test_detectar_estado_item_performance(self, page: Page):
        """
        Função detectarEstadoItem() deve executar em < 1ms.
        """
        # Criar 1 item para teste
        ItemPedido.objects.create(
            pedido=self.pedido,
            produto=self.produtos[0],
            quantidade_solicitada=1,
            separado=False
        )

        self._login(page)
        page.goto(f"http://localhost:8000/pedido/{self.pedido.id}/")

        # Benchmark
        resultado = page.evaluate("""
            () => {
                const item = document.querySelector('.item-pedido');

                // 1000 execuções
                const start = performance.now();
                for (let i = 0; i < 1000; i++) {
                    window.ItemAnimations.detectarEstadoItem(item);
                }
                const end = performance.now();

                return {
                    totalTime: end - start,
                    avgTime: (end - start) / 1000
                };
            }
        """)

        # Validação: média < 1ms
        assert resultado['avgTime'] < 1.0, \
            f"detectarEstadoItem() média: {resultado['avgTime']:.2f}ms (esperado < 1ms)"

    def test_animacao_nao_bloqueia_ui(self, page: Page):
        """
        Durante animação, UI deve permanecer responsiva (outros elementos clicáveis).
        """
        # Criar 3 itens
        for i in range(3):
            ItemPedido.objects.create(
                pedido=self.pedido,
                produto=self.produtos[i],
                quantidade_solicitada=1,
                separado=False
            )

        self._login(page)
        page.goto(f"http://localhost:8000/pedido/{self.pedido.id}/")

        # Iniciar animação do item 1
        items = page.locator('.item-pedido')
        checkbox_1 = items.nth(0).locator('input[type="checkbox"]')
        checkbox_1.check()

        # Durante animação (50ms após início), tentar interagir com item 2
        time.sleep(0.05)

        checkbox_2 = items.nth(1).locator('input[type="checkbox"]')

        # Validação: segundo checkbox deve ser clicável
        start_time = time.time()
        checkbox_2.check()
        click_time = (time.time() - start_time) * 1000

        # Click deve ser instantâneo (< 100ms)
        assert click_time < 100, \
            f"Click durante animação levou {click_time:.2f}ms (UI bloqueada?)"

    def test_memoria_nao_vaza_apos_multiplas_reordenacoes(self, page: Page):
        """
        Heap size não deve crescer descontroladamente após múltiplas operações.
        """
        # Criar 5 itens
        for i in range(5):
            ItemPedido.objects.create(
                pedido=self.pedido,
                produto=self.produtos[i],
                quantidade_solicitada=1,
                separado=False
            )

        self._login(page)
        page.goto(f"http://localhost:8000/pedido/{self.pedido.id}/")

        # Medir heap inicial
        heap_inicial = page.evaluate("() => performance.memory.usedJSHeapSize")

        # Executar 20 reordenações
        for i in range(20):
            items = page.locator('.item-pedido')
            checkbox = items.nth(0).locator('input[type="checkbox"]')
            checkbox.check()
            time.sleep(0.3)

            # Desmarcar para refazer ciclo
            checkbox.uncheck()
            time.sleep(0.3)

        # Forçar garbage collection (se disponível)
        page.evaluate("() => { if (window.gc) window.gc(); }")
        time.sleep(1)

        # Medir heap final
        heap_final = page.evaluate("() => performance.memory.usedJSHeapSize")

        # Crescimento de heap
        crescimento = (heap_final - heap_inicial) / 1024 / 1024  # MB

        # Validação: crescimento < 5MB após 20 operações
        assert crescimento < 5.0, \
            f"Memória cresceu {crescimento:.2f}MB (vazamento detectado?)"

    def test_fps_durante_animacao(self, page: Page):
        """
        FPS durante animação deve ser >= 50 (idealmente 60).
        """
        # Criar 10 itens
        for i in range(10):
            ItemPedido.objects.create(
                pedido=self.pedido,
                produto=self.produtos[i],
                quantidade_solicitada=1,
                separado=False
            )

        self._login(page)
        page.goto(f"http://localhost:8000/pedido/{self.pedido.id}/")

        # Monitorar FPS durante animação
        resultado = page.evaluate("""
            async () => {
                const item = document.querySelector('.item-pedido');
                const checkbox = item.querySelector('input[type="checkbox"]');

                let frames = 0;
                let startTime = performance.now();

                // Contador de frames via requestAnimationFrame
                function countFrames() {
                    frames++;
                    if (performance.now() - startTime < 500) {
                        requestAnimationFrame(countFrames);
                    }
                }

                // Iniciar contagem e trigger animação
                requestAnimationFrame(countFrames);
                checkbox.click();

                // Aguardar animação completar
                await new Promise(resolve => setTimeout(resolve, 500));

                const elapsed = performance.now() - startTime;
                const fps = (frames / elapsed) * 1000;

                return { fps, frames, elapsed };
            }
        """)

        # Validação: FPS >= 50
        assert resultado['fps'] >= 50, \
            f"FPS durante animação: {resultado['fps']:.2f} (esperado >= 50)"
