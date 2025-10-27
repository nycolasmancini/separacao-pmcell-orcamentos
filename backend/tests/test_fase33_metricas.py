# -*- coding: utf-8 -*-
"""
Testes para Fase 33: Criar Tela de Métricas Avançadas
TDD: RED → GREEN → REFACTOR

Este módulo testa a funcionalidade de métricas avançadas:
- View renderiza template correto
- Cálculo de tempo médio por separador
- Ranking de separadores (ordenado por velocidade)
- Top 10 produtos mais separados
- Top 10 produtos mais enviados para compra
- Gráfico de pedidos por dia (últimos 30 dias)
- Proteção de autenticação
- Estado vazio quando não há dados
"""

import pytest
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.urls import reverse
from datetime import datetime, timedelta
from decimal import Decimal

from core.models import Pedido, ItemPedido, Produto
from core.domain.pedido.value_objects import StatusPedido, Logistica, Embalagem


Usuario = get_user_model()


class TestFase33Metricas(TestCase):
    """
    Testes para a tela de métricas avançadas.

    Cobertura:
    1. View renderiza template correto
    2. Cálculo de tempo médio por separador está correto
    3. Ranking de separadores ordenado por velocidade
    4. Top 10 produtos mais separados
    5. Top 10 produtos mais enviados para compra
    6. Gráfico de pedidos por dia (últimos 30 dias)
    7. View protegida com autenticação
    8. Métricas zeradas quando não há dados
    """

    def setUp(self):
        """Setup para cada teste."""
        self.client = Client()

        # Criar usuários separadores
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
        self.separador3 = Usuario.objects.create_user(
            numero_login="1003",
            pin="1236",
            nome="Pedro Separador",
            tipo="SEPARADOR"
        )

        # Criar vendedor
        self.vendedor = Usuario.objects.create_user(
            numero_login="2001",
            pin="2345",
            nome="Carlos Vendedor",
            tipo="VENDEDOR"
        )

        # Login do separador1
        self.client.force_login(self.separador1)

        # Criar produtos para testes
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
        self.produto3 = Produto.objects.create(
            codigo="00003",
            descricao="Webcam HD",
            quantidade=3,
            valor_unitario=Decimal("100.00"),
            valor_total=Decimal("300.00")
        )

    def test_01_view_renderiza_template_correto(self):
        """Testa que a view renderiza o template metricas.html."""
        response = self.client.get(reverse('metricas'))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'metricas.html')
        self.assertIn('metricas', response.context)

    def test_02_calcula_tempo_medio_por_separador(self):
        """Testa cálculo correto do tempo médio por separador."""
        # Criar pedidos finalizados com tempos conhecidos

        # Separador 1: 2 pedidos (1h e 2h) = média 1.5h = 90min
        pedido1 = self._criar_pedido_finalizado(
            numero_orcamento="30001",
            vendedor=self.vendedor,
            data_inicio=timezone.now() - timedelta(hours=3),
            data_finalizacao=timezone.now() - timedelta(hours=2)  # 1h
        )
        self._criar_item_separado(pedido1, self.produto1, self.separador1)

        pedido2 = self._criar_pedido_finalizado(
            numero_orcamento="30002",
            vendedor=self.vendedor,
            data_inicio=timezone.now() - timedelta(hours=4),
            data_finalizacao=timezone.now() - timedelta(hours=2)  # 2h
        )
        self._criar_item_separado(pedido2, self.produto2, self.separador1)

        # Separador 2: 1 pedido (30min)
        pedido3 = self._criar_pedido_finalizado(
            numero_orcamento="30003",
            vendedor=self.vendedor,
            data_inicio=timezone.now() - timedelta(minutes=60),
            data_finalizacao=timezone.now() - timedelta(minutes=30)  # 30min
        )
        self._criar_item_separado(pedido3, self.produto3, self.separador2)

        response = self.client.get(reverse('metricas'))

        tempo_medio_separadores = response.context['metricas']['tempo_medio_separadores']

        # Verificar que temos 2 separadores com métricas
        self.assertEqual(len(tempo_medio_separadores), 2)

        # Verificar separador1 (média ~90min)
        sep1_data = next(s for s in tempo_medio_separadores if s['separador'] == self.separador1.nome)
        self.assertAlmostEqual(sep1_data['tempo_medio_minutos'], 90, delta=5)
        self.assertEqual(sep1_data['total_pedidos'], 2)

    def test_03_ranking_separadores_ordenado_por_velocidade(self):
        """Testa que ranking está ordenado do mais rápido para o mais lento."""
        # Criar pedidos com tempos diferentes

        # Separador 3: mais rápido (20min)
        pedido1 = self._criar_pedido_finalizado(
            numero_orcamento="30101",
            vendedor=self.vendedor,
            data_inicio=timezone.now() - timedelta(minutes=40),
            data_finalizacao=timezone.now() - timedelta(minutes=20)
        )
        self._criar_item_separado(pedido1, self.produto1, self.separador3)

        # Separador 1: médio (60min)
        pedido2 = self._criar_pedido_finalizado(
            numero_orcamento="30102",
            vendedor=self.vendedor,
            data_inicio=timezone.now() - timedelta(minutes=90),
            data_finalizacao=timezone.now() - timedelta(minutes=30)
        )
        self._criar_item_separado(pedido2, self.produto2, self.separador1)

        # Separador 2: mais lento (120min)
        pedido3 = self._criar_pedido_finalizado(
            numero_orcamento="30103",
            vendedor=self.vendedor,
            data_inicio=timezone.now() - timedelta(minutes=150),
            data_finalizacao=timezone.now() - timedelta(minutes=30)
        )
        self._criar_item_separado(pedido3, self.produto3, self.separador2)

        response = self.client.get(reverse('metricas'))

        ranking = response.context['metricas']['ranking_separadores']

        # Verificar ordenação: separador3 (20min) < separador1 (60min) < separador2 (120min)
        self.assertEqual(len(ranking), 3)
        self.assertEqual(ranking[0]['separador'], self.separador3.nome)
        self.assertEqual(ranking[1]['separador'], self.separador1.nome)
        self.assertEqual(ranking[2]['separador'], self.separador2.nome)

    def test_04_produtos_mais_separados(self):
        """Testa listagem dos produtos mais separados."""
        # Criar pedidos com produtos diferentes

        # Produto 1: separado 5 vezes
        for i in range(5):
            pedido = self._criar_pedido_finalizado(
                numero_orcamento=f"30201{i}",
                vendedor=self.vendedor
            )
            self._criar_item_separado(pedido, self.produto1, self.separador1, quantidade=2)

        # Produto 2: separado 3 vezes
        for i in range(3):
            pedido = self._criar_pedido_finalizado(
                numero_orcamento=f"30202{i}",
                vendedor=self.vendedor
            )
            self._criar_item_separado(pedido, self.produto2, self.separador1, quantidade=1)

        # Produto 3: separado 1 vez
        pedido = self._criar_pedido_finalizado(
            numero_orcamento="302030",
            vendedor=self.vendedor
        )
        self._criar_item_separado(pedido, self.produto3, self.separador1, quantidade=3)

        response = self.client.get(reverse('metricas'))

        produtos_separados = response.context['metricas']['produtos_mais_separados']

        # Verificar top 3 produtos ordenados por quantidade
        self.assertGreaterEqual(len(produtos_separados), 3)
        self.assertEqual(produtos_separados[0]['produto'], self.produto1.descricao)
        self.assertEqual(produtos_separados[0]['total_separado'], 10)  # 5 pedidos x 2 unidades

        # Produtos 2 e 3 têm empate (3 unidades cada), podem estar em qualquer ordem
        produtos_com_3_unidades = {produtos_separados[1]['produto'], produtos_separados[2]['produto']}
        self.assertIn(self.produto2.descricao, produtos_com_3_unidades)
        self.assertIn(self.produto3.descricao, produtos_com_3_unidades)
        self.assertEqual(produtos_separados[1]['total_separado'], 3)
        self.assertEqual(produtos_separados[2]['total_separado'], 3)

    def test_05_produtos_mais_enviados_para_compra(self):
        """Testa listagem dos produtos mais enviados para compra."""
        # Criar pedidos com itens enviados para compra

        # Produto 1: enviado 4 vezes
        for i in range(4):
            pedido = self._criar_pedido_em_separacao(f"30301{i}", self.vendedor)
            self._criar_item_em_compra(pedido, self.produto1, self.separador1, quantidade=2)

        # Produto 2: enviado 2 vezes
        for i in range(2):
            pedido = self._criar_pedido_em_separacao(f"30302{i}", self.vendedor)
            self._criar_item_em_compra(pedido, self.produto2, self.separador1, quantidade=1)

        response = self.client.get(reverse('metricas'))

        produtos_compra = response.context['metricas']['produtos_mais_enviados_compra']

        # Verificar top 2 produtos ordenados por quantidade
        self.assertGreaterEqual(len(produtos_compra), 2)
        self.assertEqual(produtos_compra[0]['produto'], self.produto1.descricao)
        self.assertEqual(produtos_compra[0]['total_enviado'], 8)  # 4 pedidos x 2 unidades
        self.assertEqual(produtos_compra[1]['produto'], self.produto2.descricao)
        self.assertEqual(produtos_compra[1]['total_enviado'], 2)  # 2 pedidos x 1 unidade

    def test_06_grafico_pedidos_ultimos_30_dias(self):
        """Testa dados do gráfico de pedidos por dia (últimos 30 dias)."""
        hoje = timezone.now()

        # Criar pedidos em dias diferentes
        # Dia 0 (hoje): 2 pedidos
        for i in range(2):
            self._criar_pedido_finalizado(
                numero_orcamento=f"3040{i}",
                vendedor=self.vendedor,
                data_finalizacao=hoje
            )

        # Dia -5 (5 dias atrás): 3 pedidos
        for i in range(3):
            self._criar_pedido_finalizado(
                numero_orcamento=f"3041{i}",
                vendedor=self.vendedor,
                data_finalizacao=hoje - timedelta(days=5)
            )

        # Dia -10 (10 dias atrás): 1 pedido
        self._criar_pedido_finalizado(
            numero_orcamento="30420",
            vendedor=self.vendedor,
            data_finalizacao=hoje - timedelta(days=10)
        )

        response = self.client.get(reverse('metricas'))

        grafico_dados = response.context['metricas']['grafico_pedidos_30_dias']

        # Verificar estrutura do gráfico
        self.assertIn('labels', grafico_dados)  # Datas
        self.assertIn('data', grafico_dados)     # Quantidades

        # Verificar que temos 30 dias
        self.assertEqual(len(grafico_dados['labels']), 30)
        self.assertEqual(len(grafico_dados['data']), 30)

        # Verificar total de pedidos (6 criados)
        total_pedidos = sum(grafico_dados['data'])
        self.assertEqual(total_pedidos, 6)

    def test_07_view_protegida_com_autenticacao(self):
        """Testa que view redireciona usuário não autenticado."""
        # Fazer logout
        self.client.logout()

        response = self.client.get(reverse('metricas'))

        # Deve redirecionar para login
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login/', response.url)

    def test_08_metricas_zeradas_quando_sem_dados(self):
        """Testa que métricas retornam valores vazios/zero quando não há dados."""
        # Não criar nenhum pedido

        response = self.client.get(reverse('metricas'))

        metricas = response.context['metricas']

        # Verificar que todas as métricas estão vazias ou zero
        self.assertEqual(len(metricas['tempo_medio_separadores']), 0)
        self.assertEqual(len(metricas['ranking_separadores']), 0)
        self.assertEqual(len(metricas['produtos_mais_separados']), 0)
        self.assertEqual(len(metricas['produtos_mais_enviados_compra']), 0)

        # Gráfico deve ter 30 dias com zeros
        self.assertEqual(len(metricas['grafico_pedidos_30_dias']['labels']), 30)
        self.assertEqual(sum(metricas['grafico_pedidos_30_dias']['data']), 0)

    # ==================== HELPERS ====================

    def _criar_pedido_finalizado(
        self,
        numero_orcamento,
        vendedor,
        data_inicio=None,
        data_finalizacao=None
    ):
        """Helper para criar pedido finalizado."""
        if data_inicio is None:
            data_inicio = timezone.now() - timedelta(hours=2)
        if data_finalizacao is None:
            data_finalizacao = timezone.now()

        # Criar pedido e atualizar datas manualmente (auto_now_add=True bloqueia valores customizados)
        pedido = Pedido.objects.create(
            numero_orcamento=numero_orcamento,
            codigo_cliente="12345",
            nome_cliente="Cliente Teste",
            vendedor=vendedor,
            data="01/01/2025",
            logistica=Logistica.CORREIOS.value,
            embalagem=Embalagem.CAIXA.value,
            status=StatusPedido.FINALIZADO.value
        )

        # Atualizar datas manualmente usando update (bypass auto_now_add)
        Pedido.objects.filter(id=pedido.id).update(
            data_inicio=data_inicio,
            data_finalizacao=data_finalizacao
        )

        pedido.refresh_from_db()
        return pedido

    def _criar_pedido_em_separacao(self, numero_orcamento, vendedor):
        """Helper para criar pedido em separação."""
        return Pedido.objects.create(
            numero_orcamento=numero_orcamento,
            codigo_cliente="12345",
            nome_cliente="Cliente Teste",
            vendedor=vendedor,
            data="01/01/2025",
            logistica=Logistica.CORREIOS.value,
            embalagem=Embalagem.CAIXA.value,
            status=StatusPedido.EM_SEPARACAO.value,
            data_inicio=timezone.now()
        )

    def _criar_item_separado(self, pedido, produto, separador, quantidade=1):
        """Helper para criar item separado."""
        return ItemPedido.objects.create(
            pedido=pedido,
            produto=produto,
            quantidade_solicitada=quantidade,
            quantidade_separada=quantidade,
            separado=True,
            separado_por=separador,
            separado_em=timezone.now()
        )

    def _criar_item_em_compra(self, pedido, produto, usuario, quantidade=1):
        """Helper para criar item enviado para compra."""
        return ItemPedido.objects.create(
            pedido=pedido,
            produto=produto,
            quantidade_solicitada=quantidade,
            quantidade_separada=0,
            separado=False,
            em_compra=True,
            enviado_para_compra_por=usuario,
            enviado_para_compra_em=timezone.now()
        )
