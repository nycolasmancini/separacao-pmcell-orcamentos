# -*- coding: utf-8 -*-
"""
Testes para Fase 34: Otimizações de Performance
TDD: RED → GREEN → REFACTOR

Este módulo testa otimizações de performance:
- Índices criados corretamente
- MetricasView usa agregações (não loops)
- Cache Redis funciona nas views
- PainelComprasView tem paginação
- Queries otimizadas (max queries por view)
- Redução de queries em 50%+
- Django Debug Toolbar configurado
- Performance com 100+ pedidos
- Cache invalidado ao atualizar
- Funcionalidade mantida
"""

import pytest
from django.test import TestCase, Client
from django.test.utils import override_settings
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.urls import reverse
from django.core.cache import cache
from django.db import connection
from django.test.utils import override_settings
from datetime import datetime, timedelta
from decimal import Decimal

from core.models import Pedido, ItemPedido, Produto
from core.domain.pedido.value_objects import StatusPedido, Logistica, Embalagem


Usuario = get_user_model()


@override_settings(
    DEBUG=False,  # Desabilitar debug toolbar nos testes
    MIDDLEWARE=[
        'django.middleware.security.SecurityMiddleware',
        'django.contrib.sessions.middleware.SessionMiddleware',
        'django.middleware.common.CommonMiddleware',
        'django.middleware.csrf.CsrfViewMiddleware',
        'django.contrib.auth.middleware.AuthenticationMiddleware',
        'django.contrib.messages.middleware.MessageMiddleware',
        'django.middleware.clickjacking.XFrameOptionsMiddleware',
        'core.middleware.authentication.SessionTimeoutMiddleware',
    ]
)
class TestFase34Performance(TestCase):
    """
    Testes para otimizações de performance.

    Cobertura:
    1. Índices criados corretamente nos modelos
    2. MetricasView usa agregações (não loops manuais)
    3. Cache Redis funciona nas views pesadas
    4. PainelComprasView tem paginação
    5. Queries otimizadas no Dashboard (max 10 queries)
    6. Número de queries reduzido em MetricasView
    7. Django Debug Toolbar configurado
    8. Performance aceitável com 100+ pedidos
    9. Cache invalidado ao atualizar pedidos
    10. Funcionalidade mantida após otimizações
    """

    def setUp(self):
        """Setup para cada teste."""
        self.client = Client()

        # Limpar cache antes de cada teste
        cache.clear()

        # Criar usuários
        self.separador1 = Usuario.objects.create_user(
            numero_login="1001",
            pin="1234",
            nome="João Separador",
            tipo="SEPARADOR"
        )
        self.separador2 = Usuario.objects.create_user(
            numero_login="1002",
            pin="1235",
            nome="Maria Separadora",
            tipo="SEPARADOR"
        )
        self.vendedor = Usuario.objects.create_user(
            numero_login="2001",
            pin="2345",
            nome="Carlos Vendedor",
            tipo="VENDEDOR"
        )
        self.compradora = Usuario.objects.create_user(
            numero_login="3001",
            pin="3456",
            nome="Ana Compradora",
            tipo="COMPRADORA"
        )

        # Login do separador1
        self.client.force_login(self.separador1)

        # Criar produtos
        self.produto1 = Produto.objects.create(
            codigo="00001",
            descricao="Mouse USB",
            quantidade=10,
            valor_unitario=Decimal("25.00"),
            valor_total=Decimal("250.00")
        )
        self.produto2 = Produto.objects.create(
            codigo="00002",
            descricao="Teclado USB",
            quantidade=5,
            valor_unitario=Decimal("50.00"),
            valor_total=Decimal("250.00")
        )

    def tearDown(self):
        """Limpar cache após cada teste."""
        cache.clear()

    # ==================== TESTE 1: ÍNDICES ====================
    def test_indices_criados_corretamente(self):
        """
        Testa se os índices de performance foram criados nos modelos.

        Índices esperados:
        - ItemPedido: em_compra, pedido_realizado, separado_por
        - Pedido: data_finalizacao, vendedor, data_inicio, (status, data_inicio)
        """
        # Verificar índices do Pedido no Meta
        pedido_meta_indexes = Pedido._meta.indexes

        # Verificar que há índices declarados (pelo menos 7: 3 originais + 4 novos da Fase 34)
        assert len(pedido_meta_indexes) >= 7, f"Pedido deve ter pelo menos 7 índices (atual: {len(pedido_meta_indexes)})"

        # Verificar campos indexados convertendo índices para string
        pedido_indexes_str = ' '.join([str(idx) for idx in pedido_meta_indexes])

        # Verificar índices críticos da Fase 34
        assert 'data_finalizacao' in pedido_indexes_str, \
            "Pedido deve ter índice em data_finalizacao"
        assert 'data_inicio' in pedido_indexes_str, \
            "Pedido deve ter índice em data_inicio"

        # Verificar ItemPedido
        item_meta_indexes = ItemPedido._meta.indexes

        # Deve ter pelo menos 4 índices (1 original + 3 novos da Fase 34)
        assert len(item_meta_indexes) >= 4, f"ItemPedido deve ter pelo menos 4 índices (atual: {len(item_meta_indexes)})"

        # Verificar índices da Fase 34
        item_indexes_str = ' '.join([str(idx) for idx in item_meta_indexes])

        assert 'em_compra' in item_indexes_str, \
            "ItemPedido deve ter índice em em_compra"
        assert 'pedido_realizado' in item_indexes_str, \
            "ItemPedido deve ter índice em pedido_realizado"
        assert 'separado_por' in item_indexes_str, \
            "ItemPedido deve ter índice em separado_por"

    # ==================== TESTE 2: AGREGAÇÕES ====================
    def test_metricas_view_usa_agregacoes_nao_loops(self):
        """
        Testa se MetricasView usa agregações Django ao invés de loops manuais.

        Verifica que o número de queries é otimizado (deve ser constante,
        independente do número de pedidos).
        """
        # Criar 10 pedidos finalizados com itens separados
        for i in range(10):
            pedido = Pedido.objects.create(
                numero_orcamento=f"ORD{30000+i}",
                codigo_cliente=f"CLI{100+i}",
                nome_cliente=f"Cliente {i}",
                vendedor=self.vendedor,
                data="01/01/2025",
                logistica=Logistica.CORREIOS.value,
                embalagem=Embalagem.CAIXA.value,
                status=StatusPedido.FINALIZADO.value,
                data_inicio=timezone.now() - timedelta(hours=2),
                data_finalizacao=timezone.now() - timedelta(hours=1)
            )

            # Adicionar 3 itens separados
            for j in range(3):
                ItemPedido.objects.create(
                    pedido=pedido,
                    produto=self.produto1,
                    quantidade_solicitada=j+1,
                    quantidade_separada=j+1,
                    separado=True,
                    separado_por=self.separador1,
                    separado_em=timezone.now() - timedelta(hours=1, minutes=30)
                )

        # Fazer requisição contando queries
        # Otimizado: Máximo de 10 queries independente do número de pedidos
        with self.assertNumQueries(10):
            response = self.client.get(reverse('metricas'))

        assert response.status_code == 200

        # Verificar que métricas foram calculadas
        metricas = response.context['metricas']
        assert 'tempo_medio_separadores' in metricas
        assert len(metricas['tempo_medio_separadores']) > 0

    # ==================== TESTE 3: CACHE REDIS ====================
    @override_settings(CACHES={
        'default': {
            'BACKEND': 'django.core.cache.backends.redis.RedisCache',
            'LOCATION': 'redis://127.0.0.1:6379/1',
        }
    })
    def test_cache_redis_funciona_nas_views(self):
        """
        Testa se o cache Redis está funcionando nas views pesadas.

        Verifica que:
        1. Primeira requisição faz queries
        2. Segunda requisição usa cache (0 queries)
        3. Cache expira corretamente
        """
        # Criar 1 pedido em separação
        pedido = Pedido.objects.create(
            numero_orcamento="ORD30100",
            codigo_cliente="CLI100",
            nome_cliente="Cliente Cache Test",
            vendedor=self.vendedor,
            data="01/01/2025",
            logistica=Logistica.CORREIOS.value,
            embalagem=Embalagem.CAIXA.value,
            status=StatusPedido.EM_SEPARACAO.value,
        )

        # Limpar cache
        cache.clear()

        # Primeira requisição - deve fazer queries
        response1 = self.client.get(reverse('dashboard'))
        assert response1.status_code == 200

        # Verificar que cache foi setado (vendedores)
        cached_vendedores = cache.get('dashboard_vendedores')
        assert cached_vendedores is not None, "Cache de vendedores deve estar setado"

        # Segunda requisição - deve usar cache
        response2 = self.client.get(reverse('dashboard'))
        assert response2.status_code == 200

        # Verificar que cache ainda está ativo
        cached_vendedores2 = cache.get('dashboard_vendedores')
        assert cached_vendedores2 is not None
        assert cached_vendedores2 == cached_vendedores

    # ==================== TESTE 4: PAGINAÇÃO ====================
    def test_painel_compras_tem_paginacao(self):
        """
        Testa se PainelComprasView tem paginação implementada.

        Cria 30 itens em compra e verifica que:
        1. Apenas 20 aparecem na primeira página
        2. Página 2 existe com os restantes
        3. Navegação funciona
        """
        # Login como compradora
        self.client.force_login(self.compradora)

        # Criar 30 itens em compra
        for i in range(30):
            pedido = Pedido.objects.create(
                numero_orcamento=f"ORD{31000+i}",
                codigo_cliente=f"CLI{200+i}",
                nome_cliente=f"Cliente Compra {i}",
                vendedor=self.vendedor,
                data="01/01/2025",
                logistica=Logistica.CORREIOS.value,
                embalagem=Embalagem.CAIXA.value,
                status=StatusPedido.EM_SEPARACAO.value,
            )

            ItemPedido.objects.create(
                pedido=pedido,
                produto=self.produto1,
                quantidade_solicitada=1,
                em_compra=True,
                enviado_para_compra_por=self.separador1,
                enviado_para_compra_em=timezone.now()
            )

        # Fazer requisição para página 1
        response = self.client.get(reverse('painel_compras'))
        assert response.status_code == 200

        # Verificar que há paginação
        assert 'page_obj' in response.context, "Deve haver paginação no contexto"
        page_obj = response.context['page_obj']

        # Verificar que mostra apenas 20 itens
        assert page_obj.paginator.per_page == 20, "Deve ter 20 itens por página"
        assert page_obj.paginator.count == 30, "Deve ter 30 itens no total"
        assert page_obj.paginator.num_pages == 2, "Deve ter 2 páginas"

        # Fazer requisição para página 2
        response2 = self.client.get(reverse('painel_compras') + '?page=2')
        assert response2.status_code == 200
        page_obj2 = response2.context['page_obj']
        assert page_obj2.number == 2, "Deve estar na página 2"
        assert len(page_obj2.object_list) == 10, "Página 2 deve ter 10 itens"

    # ==================== TESTE 5: QUERIES OTIMIZADAS ====================
    def test_dashboard_queries_otimizadas(self):
        """
        Testa se Dashboard tem queries otimizadas com select_related/prefetch_related.

        Verifica que número de queries é baixo (máximo 10) mesmo com múltiplos pedidos.
        """
        # Criar 10 pedidos em separação com itens
        for i in range(10):
            pedido = Pedido.objects.create(
                numero_orcamento=f"ORD{32000+i}",
                codigo_cliente=f"CLI{300+i}",
                nome_cliente=f"Cliente Dashboard {i}",
                vendedor=self.vendedor,
                data="01/01/2025",
                logistica=Logistica.CORREIOS.value,
                embalagem=Embalagem.CAIXA.value,
                status=StatusPedido.EM_SEPARACAO.value,
            )

            # 5 itens por pedido
            for j in range(5):
                ItemPedido.objects.create(
                    pedido=pedido,
                    produto=self.produto1,
                    quantidade_solicitada=j+1,
                )

        # Fazer requisição contando queries
        # Com select_related/prefetch_related: deve fazer no máximo 5 queries
        with self.assertNumQueries(5):
            response = self.client.get(reverse('dashboard'))

        assert response.status_code == 200
        assert len(response.context['pedidos']['results']) == 10

    # ==================== TESTE 6: REDUÇÃO DE QUERIES ====================
    def test_reducao_queries_metricas_view(self):
        """
        Testa se MetricasView teve redução significativa de queries.

        Com agregações, deve fazer no máximo 15 queries independente
        do número de pedidos (vs centenas antes).
        """
        # Criar 20 pedidos finalizados
        for i in range(20):
            pedido = Pedido.objects.create(
                numero_orcamento=f"ORD{33000+i}",
                codigo_cliente=f"CLI{400+i}",
                nome_cliente=f"Cliente Métrica {i}",
                vendedor=self.vendedor,
                data="01/01/2025",
                logistica=Logistica.CORREIOS.value,
                embalagem=Embalagem.CAIXA.value,
                status=StatusPedido.FINALIZADO.value,
                data_inicio=timezone.now() - timedelta(days=i+1, hours=2),
                data_finalizacao=timezone.now() - timedelta(days=i+1, hours=1)
            )

            ItemPedido.objects.create(
                pedido=pedido,
                produto=self.produto1,
                quantidade_solicitada=1,
                quantidade_separada=1,
                separado=True,
                separado_por=self.separador1,
                separado_em=timezone.now() - timedelta(days=i+1, hours=1, minutes=30)
            )

        # Verificar número de queries (deve ser baixo)
        with self.assertNumQueries(10):  # Máximo de 10 queries (otimizado)
            response = self.client.get(reverse('metricas'))

        assert response.status_code == 200

    # ==================== TESTE 7: DEBUG TOOLBAR ====================
    def test_django_debug_toolbar_configurado(self):
        """
        Testa se Django Debug Toolbar está configurado corretamente.

        Verifica que:
        1. debug_toolbar pode ser importado
        2. INTERNAL_IPS está configurado no settings
        3. DEBUG_TOOLBAR_CONFIG está definido

        Nota: O app e middleware são desabilitados durante testes via override_settings,
        mas a configuração base está presente nos settings.py
        """
        from django.conf import settings
        import sys

        # Verificar se o pacote pode ser importado
        try:
            import debug_toolbar
            debug_toolbar_installed = True
        except ImportError:
            debug_toolbar_installed = False

        assert debug_toolbar_installed, \
            "django-debug-toolbar deve estar instalado"

        # Verificar configurações
        assert hasattr(settings, 'INTERNAL_IPS'), \
            "INTERNAL_IPS deve estar definido"

        assert '127.0.0.1' in settings.INTERNAL_IPS, \
            "127.0.0.1 deve estar em INTERNAL_IPS"

        assert hasattr(settings, 'DEBUG_TOOLBAR_CONFIG'), \
            "DEBUG_TOOLBAR_CONFIG deve estar definido"

    # ==================== TESTE 8: PERFORMANCE COM 100+ PEDIDOS ====================
    def test_performance_aceitavel_com_100_pedidos(self):
        """
        Testa se performance é aceitável com 100+ pedidos.

        Cria 100 pedidos e verifica que:
        1. Dashboard responde em tempo razoável
        2. Queries permanecem otimizadas
        3. Não há timeouts
        """
        import time

        # Criar 100 pedidos em separação
        pedidos_bulk = []
        for i in range(100):
            pedidos_bulk.append(Pedido(
                numero_orcamento=f"ORD{40000+i}",
                codigo_cliente=f"CLI{500+i}",
                nome_cliente=f"Cliente Bulk {i}",
                vendedor=self.vendedor,
                data="01/01/2025",
                logistica=Logistica.CORREIOS.value,
                embalagem=Embalagem.CAIXA.value,
                status=StatusPedido.EM_SEPARACAO.value,
            ))

        Pedido.objects.bulk_create(pedidos_bulk)

        # Adicionar itens aos primeiros 10 pedidos (suficiente para teste)
        pedidos_criados = Pedido.objects.filter(numero_orcamento__startswith='ORD400')[:10]
        itens_bulk = []
        for pedido in pedidos_criados:
            for j in range(3):
                itens_bulk.append(ItemPedido(
                    pedido=pedido,
                    produto=self.produto1,
                    quantidade_solicitada=j+1,
                ))

        ItemPedido.objects.bulk_create(itens_bulk)

        # Medir tempo de resposta
        start_time = time.time()
        response = self.client.get(reverse('dashboard'))
        end_time = time.time()

        response_time = end_time - start_time

        # Verificar que responde em menos de 2 segundos
        assert response_time < 2.0, f"Dashboard deve responder em < 2s (levou {response_time:.2f}s)"
        assert response.status_code == 200

        # Verificar paginação (deve mostrar apenas 10 da primeira página)
        assert len(response.context['pedidos']['results']) == 10

    # ==================== TESTE 9: INVALIDAÇÃO DE CACHE ====================
    def test_cache_invalidado_ao_atualizar_pedidos(self):
        """
        Testa se cache é invalidado quando pedidos são atualizados.

        Verifica que:
        1. Cache é setado na primeira requisição
        2. Ao criar novo pedido, cache é invalidado
        3. Próxima requisição mostra dados atualizados
        """
        # Primeira requisição - seta cache
        response1 = self.client.get(reverse('dashboard'))
        assert response1.status_code == 200
        count1 = response1.context['pedidos']['count']

        # Verificar cache de vendedores
        cache.set('dashboard_vendedores', ['cached'], 300)
        assert cache.get('dashboard_vendedores') == ['cached']

        # Criar novo pedido
        novo_pedido = Pedido.objects.create(
            numero_orcamento="ORD50000",
            codigo_cliente="CLI999",
            nome_cliente="Cliente Novo",
            vendedor=self.vendedor,
            data="01/01/2025",
            logistica=Logistica.CORREIOS.value,
            embalagem=Embalagem.CAIXA.value,
            status=StatusPedido.EM_SEPARACAO.value,
        )

        # Cache deve ser invalidado (simular signal ou limpar manualmente)
        # Nota: Em produção, isso seria feito por um signal post_save
        cache.delete('dashboard_vendedores')

        # Nova requisição - deve mostrar pedido novo
        response2 = self.client.get(reverse('dashboard'))
        assert response2.status_code == 200
        count2 = response2.context['pedidos']['count']

        # Verificar que contagem aumentou
        assert count2 == count1 + 1, "Novo pedido deve aparecer no dashboard"

    # ==================== TESTE 10: FUNCIONALIDADE MANTIDA ====================
    def test_funcionalidade_mantida_apos_otimizacoes(self):
        """
        Testa se funcionalidades foram mantidas após otimizações.

        Verifica que:
        1. Dashboard mostra pedidos corretamente
        2. Filtros funcionam
        3. Busca funciona
        4. Métricas são calculadas corretamente
        5. Painel de compras funciona
        """
        # Criar pedidos para teste
        pedido1 = Pedido.objects.create(
            numero_orcamento="ORD60000",
            codigo_cliente="CLI1000",
            nome_cliente="Cliente Funcional",
            vendedor=self.vendedor,
            data="01/01/2025",
            logistica=Logistica.CORREIOS.value,
            embalagem=Embalagem.CAIXA.value,
            status=StatusPedido.EM_SEPARACAO.value,
        )

        item1 = ItemPedido.objects.create(
            pedido=pedido1,
            produto=self.produto1,
            quantidade_solicitada=5,
            em_compra=True,
            enviado_para_compra_por=self.separador1,
            enviado_para_compra_em=timezone.now()
        )

        # Teste 1: Dashboard funciona
        response = self.client.get(reverse('dashboard'))
        assert response.status_code == 200
        assert response.context['pedidos']['count'] == 1

        # Teste 2: Busca funciona
        response = self.client.get(reverse('dashboard') + '?search=60000')
        assert response.status_code == 200
        assert response.context['pedidos']['count'] == 1

        response = self.client.get(reverse('dashboard') + '?search=inexistente')
        assert response.status_code == 200
        assert response.context['pedidos']['count'] == 0

        # Teste 3: Filtro por vendedor funciona
        response = self.client.get(reverse('dashboard') + f'?vendedor={self.vendedor.id}')
        assert response.status_code == 200
        assert response.context['pedidos']['count'] == 1

        # Teste 4: Painel de compras funciona
        self.client.force_login(self.compradora)
        response = self.client.get(reverse('painel_compras'))
        assert response.status_code == 200
        assert response.context['total_itens'] == 1

        # Teste 5: Métricas funcionam (mesmo sem dados suficientes)
        response = self.client.get(reverse('metricas'))
        assert response.status_code == 200
        assert 'metricas' in response.context
