# -*- coding: utf-8 -*-
"""
Testes de integração para a view do Dashboard.
Fase 17: Criar View do Dashboard
"""
import pytest
from django.test import Client
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta
from core.models import Usuario, Pedido, ItemPedido, Produto, StatusPedidoChoices


@pytest.fixture
def client():
    """Cliente Django para testes."""
    return Client()


@pytest.fixture
def usuario_vendedor(db):
    """Cria usuário vendedor de teste."""
    return Usuario.objects.create_user(
        numero_login=100,
        pin='1111',
        nome='Vendedor Teste',
        tipo='VENDEDOR'
    )


@pytest.fixture
def usuario_separador(db):
    """Cria usuário separador de teste."""
    return Usuario.objects.create_user(
        numero_login=200,
        pin='2222',
        nome='Separador Teste',
        tipo='SEPARADOR'
    )


@pytest.fixture
def usuario_separador2(db):
    """Cria segundo usuário separador de teste."""
    return Usuario.objects.create_user(
        numero_login=201,
        pin='2223',
        nome='Separador Dois',
        tipo='SEPARADOR'
    )


@pytest.fixture
def produto_teste(db):
    """Cria produto de teste."""
    from decimal import Decimal
    return Produto.objects.create(
        codigo='00001',
        descricao='Produto Teste',
        quantidade=10,
        valor_unitario=Decimal('10.00'),
        valor_total=Decimal('100.00')
    )


@pytest.fixture
def logged_in_client(client, usuario_separador):
    """Cliente autenticado."""
    client.force_login(usuario_separador)
    session = client.session
    session['usuario_id'] = usuario_separador.id
    session['numero_login'] = usuario_separador.numero_login
    session['nome'] = usuario_separador.nome
    session['tipo'] = usuario_separador.tipo
    session.save()
    return client


def criar_pedido(vendedor, status=StatusPedidoChoices.EM_SEPARACAO, minutes_ago=0):
    """Helper para criar pedido de teste."""
    pedido = Pedido.objects.create(
        numero_orcamento=f'TEST{Pedido.objects.count() + 1}',
        codigo_cliente='CLI001',
        nome_cliente='Cliente Teste',
        vendedor=vendedor,
        data='25/01/2025',
        logistica='CORREIOS',
        embalagem='CAIXA',
        status=status
    )

    # Ajustar data_inicio para simular tempo decorrido
    if minutes_ago > 0:
        pedido.data_inicio = timezone.now() - timedelta(minutes=minutes_ago)
        pedido.save()

    return pedido


def criar_item_pedido(pedido, produto, quantidade=5, separado=False, separado_por=None):
    """Helper para criar item de pedido."""
    item = ItemPedido.objects.create(
        pedido=pedido,
        produto=produto,
        quantidade_solicitada=quantidade,
        quantidade_separada=quantidade if separado else 0,
        separado=separado,
        separado_por=separado_por,
        separado_em=timezone.now() if separado else None
    )
    return item


@pytest.mark.django_db
class TestDashboardView:
    """Testes da view do Dashboard - Fase 17."""

    def test_dashboard_requires_authentication(self, client):
        """Testa que dashboard requer autenticação."""
        response = client.get('/dashboard/')

        # Deve redirecionar para login
        assert response.status_code == 302
        assert '/login/' in response.url

    def test_dashboard_shows_pedidos_em_separacao(
        self, logged_in_client, usuario_vendedor, produto_teste
    ):
        """Testa que dashboard mostra apenas pedidos EM_SEPARACAO."""
        # Criar pedidos com diferentes status
        pedido_em_separacao = criar_pedido(usuario_vendedor, StatusPedidoChoices.EM_SEPARACAO)
        criar_item_pedido(pedido_em_separacao, produto_teste)

        pedido_finalizado = criar_pedido(usuario_vendedor, StatusPedidoChoices.FINALIZADO)
        criar_item_pedido(pedido_finalizado, produto_teste)

        pedido_cancelado = criar_pedido(usuario_vendedor, StatusPedidoChoices.CANCELADO)
        criar_item_pedido(pedido_cancelado, produto_teste)

        response = logged_in_client.get('/dashboard/')

        assert response.status_code == 200
        pedidos_data = response.context['pedidos']

        # Deve mostrar apenas 1 pedido (EM_SEPARACAO)
        assert pedidos_data['count'] == 1
        pedidos = pedidos_data['results']
        assert pedidos[0]['pedido'].status == StatusPedidoChoices.EM_SEPARACAO

    def test_dashboard_calculates_time_elapsed(
        self, logged_in_client, usuario_vendedor, produto_teste
    ):
        """Testa cálculo de tempo decorrido."""
        # Criar pedido com 15 minutos de idade
        pedido = criar_pedido(usuario_vendedor, minutes_ago=15)
        criar_item_pedido(pedido, produto_teste)

        response = logged_in_client.get('/dashboard/')

        pedidos_data = response.context['pedidos']
        assert pedidos_data['count'] == 1
        pedidos = pedidos_data['results']

        # Tempo decorrido deve ser aproximadamente 15 minutos
        tempo_minutos = pedidos[0]['tempo_decorrido_minutos']
        assert 14 <= tempo_minutos <= 16  # Tolerância de ±1 minuto

    def test_dashboard_calculates_progress(
        self, logged_in_client, usuario_vendedor, produto_teste, usuario_separador
    ):
        """Testa cálculo de progresso (itens separados/total)."""
        pedido = criar_pedido(usuario_vendedor)

        # Criar 10 itens: 4 separados, 6 não separados
        for i in range(4):
            criar_item_pedido(pedido, produto_teste, separado=True, separado_por=usuario_separador)
        for i in range(6):
            criar_item_pedido(pedido, produto_teste, separado=False)

        response = logged_in_client.get('/dashboard/')

        pedidos_data = response.context['pedidos']
        assert pedidos_data['count'] == 1
        pedidos = pedidos_data['results']

        # Progresso: 4/10 = 40%
        assert pedidos[0]['total_itens'] == 10
        assert pedidos[0]['itens_separados'] == 4
        assert pedidos[0]['progresso_percentual'] == 40

    def test_dashboard_identifies_separadores(
        self, logged_in_client, usuario_vendedor, produto_teste,
        usuario_separador, usuario_separador2
    ):
        """Testa identificação de separadores ativos."""
        pedido = criar_pedido(usuario_vendedor)

        # Criar itens separados por diferentes usuários
        criar_item_pedido(pedido, produto_teste, separado=True, separado_por=usuario_separador)
        criar_item_pedido(pedido, produto_teste, separado=True, separado_por=usuario_separador)
        criar_item_pedido(pedido, produto_teste, separado=True, separado_por=usuario_separador2)

        response = logged_in_client.get('/dashboard/')

        pedidos_data = response.context['pedidos']
        assert pedidos_data['count'] == 1
        pedidos = pedidos_data['results']

        # Deve identificar os 2 separadores
        separadores = pedidos[0]['separadores']
        nomes_separadores = [s.nome for s in separadores]

        assert len(separadores) == 2
        assert 'Separador Teste' in nomes_separadores
        assert 'Separador Dois' in nomes_separadores

    def test_dashboard_empty_when_no_pedidos_em_separacao(
        self, logged_in_client, usuario_vendedor, produto_teste
    ):
        """Testa dashboard vazio quando não há pedidos em separação."""
        # Criar apenas pedidos finalizados
        pedido = criar_pedido(usuario_vendedor, StatusPedidoChoices.FINALIZADO)
        criar_item_pedido(pedido, produto_teste)

        response = logged_in_client.get('/dashboard/')

        assert response.status_code == 200
        pedidos_data = response.context['pedidos']
        assert pedidos_data['count'] == 0

    def test_dashboard_shows_multiple_pedidos(
        self, logged_in_client, usuario_vendedor, produto_teste
    ):
        """Testa que dashboard mostra múltiplos pedidos em separação."""
        # Criar 3 pedidos em separação
        for i in range(3):
            pedido = criar_pedido(usuario_vendedor)
            criar_item_pedido(pedido, produto_teste)

        response = logged_in_client.get('/dashboard/')

        pedidos_data = response.context['pedidos']
        assert pedidos_data['count'] == 3

    def test_dashboard_calculates_zero_progress_when_no_items_separated(
        self, logged_in_client, usuario_vendedor, produto_teste
    ):
        """Testa progresso zero quando nenhum item foi separado."""
        pedido = criar_pedido(usuario_vendedor)
        criar_item_pedido(pedido, produto_teste, separado=False)
        criar_item_pedido(pedido, produto_teste, separado=False)

        response = logged_in_client.get('/dashboard/')

        pedidos_data = response.context['pedidos']
        pedidos = pedidos_data['results']
        assert pedidos[0]['progresso_percentual'] == 0
        assert pedidos[0]['itens_separados'] == 0
        assert pedidos[0]['total_itens'] == 2

    def test_dashboard_shows_no_separadores_when_no_items_separated(
        self, logged_in_client, usuario_vendedor, produto_teste
    ):
        """Testa que não mostra separadores quando nenhum item foi separado."""
        pedido = criar_pedido(usuario_vendedor)
        criar_item_pedido(pedido, produto_teste, separado=False)

        response = logged_in_client.get('/dashboard/')

        pedidos_data = response.context['pedidos']
        pedidos = pedidos_data['results']
        assert len(pedidos[0]['separadores']) == 0
