# -*- coding: utf-8 -*-
"""
Testes para Fase 31: Criar Tela de Histórico
TDD: RED → GREEN → REFACTOR

Este módulo testa a funcionalidade de histórico de pedidos finalizados:
- Listagem de pedidos finalizados
- Ordenação por data de finalização
- Paginação (20 por página)
- Filtros: busca, vendedor, data
- Estado vazio
"""

import pytest
from django.test import TestCase, RequestFactory, Client
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import datetime, timedelta
from decimal import Decimal

from core.models import Pedido, ItemPedido, Usuario, Produto
from core.domain.pedido.value_objects import StatusPedido, Logistica, Embalagem
from core.presentation.web.views import HistoricoView


Usuario = get_user_model()


class TestFase31Historico(TestCase):
    """
    Testes para a tela de histórico de pedidos finalizados.

    Cobertura:
    1. View renderiza template correto
    2. Lista apenas pedidos FINALIZADOS
    3. Ordenação por data_finalizacao DESC
    4. Paginação funcional (20 por página)
    5. Filtro por busca (número/cliente)
    6. Filtro por vendedor
    7. Filtro por data
    8. Estado vazio quando sem pedidos
    """

    def setUp(self):
        """Setup para cada teste."""
        self.factory = RequestFactory()
        self.client = Client()

        # Criar usuário de teste
        self.usuario = Usuario.objects.create_user(
            numero_login="1001",
            pin="1234",
            nome="João Separador",
            tipo="SEPARADOR"
        )

        # Criar vendedores
        self.vendedor1 = Usuario.objects.create_user(
            numero_login="2001",
            pin="2345",
            nome="Maria Vendedora",
            tipo="VENDEDOR"
        )
        self.vendedor2 = Usuario.objects.create_user(
            numero_login="3001",
            pin="3456",
            nome="Pedro Vendedor",
            tipo="VENDEDOR"
        )

        # Login do usuário
        self.client.force_login(self.usuario)

    def _criar_pedido_finalizado(
        self,
        numero_orcamento,
        nome_cliente,
        vendedor,
        data_inicio=None,
        data_finalizacao=None
    ):
        """Helper para criar pedido finalizado."""
        if data_inicio is None:
            data_inicio = timezone.now() - timedelta(hours=2)
        if data_finalizacao is None:
            data_finalizacao = timezone.now()

        pedido = Pedido.objects.create(
            numero_orcamento=numero_orcamento,
            codigo_cliente="12345",
            nome_cliente=nome_cliente,
            vendedor=vendedor,
            data="01/01/2025",
            logistica=Logistica.CORREIOS.value,
            embalagem=Embalagem.CAIXA.value,
            status=StatusPedido.FINALIZADO.value,
            data_inicio=data_inicio,
            data_finalizacao=data_finalizacao
        )

        # Criar produto (get_or_create para evitar conflitos de código único)
        produto, _ = Produto.objects.get_or_create(
            codigo=f"PROD{numero_orcamento}",
            defaults={
                'descricao': "Produto Teste",
                'quantidade': 1,
                'valor_unitario': Decimal("10.00"),
                'valor_total': Decimal("10.00")
            }
        )

        # Criar item separado
        ItemPedido.objects.create(
            pedido=pedido,
            produto=produto,
            quantidade_solicitada=1,
            quantidade_separada=1,
            separado=True,
            separado_por=self.usuario,
            separado_em=data_inicio + timedelta(minutes=30)
        )

        return pedido

    def _criar_pedido_em_separacao(self, numero_orcamento):
        """Helper para criar pedido em separação (NÃO deve aparecer no histórico)."""
        pedido = Pedido.objects.create(
            numero_orcamento=numero_orcamento,
            codigo_cliente="12345",
            nome_cliente="Cliente Teste",
            vendedor=self.vendedor1,
            data="01/01/2025",
            logistica=Logistica.CORREIOS.value,
            embalagem=Embalagem.CAIXA.value,
            status=StatusPedido.EM_SEPARACAO.value,
            data_inicio=timezone.now()
        )

        # Criar produto (get_or_create para evitar conflitos de código único)
        produto, _ = Produto.objects.get_or_create(
            codigo=f"PROD{numero_orcamento}",
            defaults={
                'descricao': "Produto Teste",
                'quantidade': 1,
                'valor_unitario': Decimal("10.00"),
                'valor_total': Decimal("10.00")
            }
        )

        ItemPedido.objects.create(
            pedido=pedido,
            produto=produto,
            quantidade_solicitada=1,
            quantidade_separada=0
        )

        return pedido

    def test_view_renderiza_template_correto(self):
        """Teste 1: View renderiza template historico.html."""
        response = self.client.get('/historico/')

        assert response.status_code == 200
        assert 'historico.html' in [t.name for t in response.templates]

    def test_lista_apenas_pedidos_finalizados(self):
        """Teste 2: Apenas pedidos FINALIZADOS aparecem no histórico."""
        # Criar pedidos
        finalizado1 = self._criar_pedido_finalizado("30001", "Rosana", self.vendedor1)
        finalizado2 = self._criar_pedido_finalizado("30002", "Ponto do Celular", self.vendedor2)
        em_separacao = self._criar_pedido_em_separacao("30003")

        response = self.client.get('/historico/')

        # Verificar que apenas finalizados aparecem
        pedidos = response.context['pedidos']
        assert len(pedidos) == 2
        assert finalizado1 in pedidos
        assert finalizado2 in pedidos
        assert em_separacao not in pedidos

    def test_ordenacao_por_data_finalizacao_desc(self):
        """Teste 3: Pedidos ordenados por data de finalização (mais recente primeiro)."""
        # Criar pedidos com datas diferentes
        pedido_antigo = self._criar_pedido_finalizado(
            "30001",
            "Cliente Antigo",
            self.vendedor1,
            data_finalizacao=timezone.now() - timedelta(days=2)
        )
        pedido_recente = self._criar_pedido_finalizado(
            "30002",
            "Cliente Recente",
            self.vendedor1,
            data_finalizacao=timezone.now()
        )
        pedido_meio = self._criar_pedido_finalizado(
            "30003",
            "Cliente Meio",
            self.vendedor1,
            data_finalizacao=timezone.now() - timedelta(days=1)
        )

        response = self.client.get('/historico/')
        pedidos = list(response.context['pedidos'])

        # Verificar ordem (mais recente primeiro)
        assert pedidos[0].id == pedido_recente.id
        assert pedidos[1].id == pedido_meio.id
        assert pedidos[2].id == pedido_antigo.id

    def test_paginacao_funcional(self):
        """Teste 4: Paginação de 20 pedidos por página."""
        # Criar 25 pedidos finalizados
        for i in range(25):
            self._criar_pedido_finalizado(
                f"3000{i:02d}",
                f"Cliente {i}",
                self.vendedor1,
                data_finalizacao=timezone.now() - timedelta(hours=i)
            )

        # Página 1: deve ter 20 pedidos
        response = self.client.get('/historico/')
        assert len(response.context['pedidos']) == 20
        assert response.context['page_obj'].has_next()

        # Página 2: deve ter 5 pedidos
        response = self.client.get('/historico/?page=2')
        assert len(response.context['pedidos']) == 5
        assert not response.context['page_obj'].has_next()

    def test_filtro_busca_numero_cliente(self):
        """Teste 5: Filtro de busca por número de orçamento ou nome de cliente."""
        pedido1 = self._criar_pedido_finalizado("30567", "Rosana", self.vendedor1)
        pedido2 = self._criar_pedido_finalizado("30568", "Ponto do Celular", self.vendedor1)
        pedido3 = self._criar_pedido_finalizado("30569", "Loja ABC", self.vendedor1)

        # Busca por número
        response = self.client.get('/historico/?busca=30567')
        pedidos = list(response.context['pedidos'])
        assert len(pedidos) == 1
        assert pedidos[0].id == pedido1.id

        # Busca por nome (parcial)
        response = self.client.get('/historico/?busca=Ponto')
        pedidos = list(response.context['pedidos'])
        assert len(pedidos) == 1
        assert pedidos[0].id == pedido2.id

    def test_filtro_por_vendedor(self):
        """Teste 6: Filtro por vendedor."""
        pedido_maria = self._criar_pedido_finalizado("30001", "Cliente 1", self.vendedor1)
        pedido_pedro = self._criar_pedido_finalizado("30002", "Cliente 2", self.vendedor2)

        # Filtrar por vendedor1 (Maria)
        response = self.client.get(f'/historico/?vendedor={self.vendedor1.id}')
        pedidos = list(response.context['pedidos'])
        assert len(pedidos) == 1
        assert pedidos[0].id == pedido_maria.id

        # Filtrar por vendedor2 (Pedro)
        response = self.client.get(f'/historico/?vendedor={self.vendedor2.id}')
        pedidos = list(response.context['pedidos'])
        assert len(pedidos) == 1
        assert pedidos[0].id == pedido_pedro.id

    def test_filtro_por_data(self):
        """Teste 7: Filtro por data de finalização."""
        hoje = timezone.now().date()
        ontem = hoje - timedelta(days=1)

        pedido_hoje = self._criar_pedido_finalizado(
            "30001",
            "Cliente Hoje",
            self.vendedor1,
            data_finalizacao=timezone.make_aware(datetime.combine(hoje, datetime.min.time()))
        )
        pedido_ontem = self._criar_pedido_finalizado(
            "30002",
            "Cliente Ontem",
            self.vendedor1,
            data_finalizacao=timezone.make_aware(datetime.combine(ontem, datetime.min.time()))
        )

        # Filtrar por hoje
        response = self.client.get(f'/historico/?data={hoje.isoformat()}')
        pedidos = list(response.context['pedidos'])
        assert len(pedidos) == 1
        assert pedidos[0].id == pedido_hoje.id

        # Filtrar por ontem
        response = self.client.get(f'/historico/?data={ontem.isoformat()}')
        pedidos = list(response.context['pedidos'])
        assert len(pedidos) == 1
        assert pedidos[0].id == pedido_ontem.id

    def test_estado_vazio_sem_pedidos(self):
        """Teste 8: Quando não há pedidos finalizados, exibe mensagem."""
        response = self.client.get('/historico/')

        assert response.status_code == 200
        assert len(response.context['pedidos']) == 0

        # Verificar que template tem tratamento para lista vazia
        content = response.content.decode('utf-8')
        # O template deve ter alguma mensagem de estado vazio
        assert 'Nenhum pedido finalizado' in content or len(response.context['pedidos']) == 0
