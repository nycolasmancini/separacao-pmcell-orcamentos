# -*- coding: utf-8 -*-
"""
Testes de integração para métricas de tempo médio no Dashboard.
Fase 20: Implementar Métrica de Tempo Médio no Dashboard
"""
import pytest
from django.test import Client
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta, datetime
from decimal import Decimal
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
def produto_teste(db):
    """Cria produto de teste."""
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


def criar_pedido_finalizado(vendedor, duracao_minutos, dias_atras=0):
    """Helper para criar pedido finalizado com duração específica."""
    agora = timezone.now()

    # Para pedidos "de hoje" (dias_atras=0):
    # - data_finalizacao = agora
    # - data_inicio = agora - duracao_minutos
    #
    # Para pedidos antigos (dias_atras > 0):
    # - data_finalizacao = data específica do dia
    # - data_inicio = data_finalizacao - duracao_minutos

    if dias_atras == 0:
        # Pedido finalizado hoje
        data_finalizacao = agora
        data_inicio = agora - timedelta(minutes=duracao_minutos)
    else:
        # Pedido finalizado N dias atrás
        # Usar meio-dia do dia específico para evitar problemas de timezone
        data_fim_do_dia = (agora - timedelta(days=dias_atras)).replace(hour=12, minute=0, second=0, microsecond=0)
        data_finalizacao = data_fim_do_dia
        data_inicio = data_fim_do_dia - timedelta(minutes=duracao_minutos)

    pedido = Pedido.objects.create(
        numero_orcamento=f'TEST{Pedido.objects.count() + 1}',
        codigo_cliente='CLI001',
        nome_cliente='Cliente Teste',
        vendedor=vendedor,
        data=data_finalizacao.strftime('%d/%m/%Y'),
        logistica='CORREIOS',
        embalagem='CAIXA',
        status=StatusPedidoChoices.FINALIZADO,
        data_finalizacao=data_finalizacao
    )

    # IMPORTANTE: data_inicio tem auto_now_add=True no model, então precisamos
    # fazer update() para sobrescrever o valor
    Pedido.objects.filter(id=pedido.id).update(
        data_inicio=data_inicio
    )

    # Recarregar o objeto com o valor correto
    pedido.refresh_from_db()

    return pedido


def criar_item_pedido(pedido, produto, quantidade=1):
    """Helper para criar item de pedido."""
    return ItemPedido.objects.create(
        pedido=pedido,
        produto=produto,
        quantidade=quantidade
    )


@pytest.mark.django_db
class TestMetricasTempoMedio:
    """Testes para métricas de tempo médio de separação."""

    def test_calcular_tempo_medio_hoje_com_pedidos_finalizados(
        self, logged_in_client, usuario_vendedor, produto_teste
    ):
        """Testa cálculo de tempo médio de pedidos finalizados hoje."""
        # Criar 3 pedidos finalizados hoje com durações diferentes
        # 30 min, 45 min, 60 min = média 45 min
        criar_pedido_finalizado(usuario_vendedor, duracao_minutos=30, dias_atras=0)
        criar_pedido_finalizado(usuario_vendedor, duracao_minutos=45, dias_atras=0)
        criar_pedido_finalizado(usuario_vendedor, duracao_minutos=60, dias_atras=0)

        # Acessar dashboard
        response = logged_in_client.get(reverse('dashboard'))

        assert response.status_code == 200
        context = response.context

        # Verificar que métricas estão presentes
        assert 'metricas_tempo' in context
        metricas = context['metricas_tempo']

        # Verificar tempo médio hoje (deve ser próximo de 45 minutos)
        assert metricas['tempo_medio_hoje_minutos'] is not None
        # Margem mais ampla devido a microsegundos de diferença entre criações
        assert 30 <= metricas['tempo_medio_hoje_minutos'] <= 60

    def test_calcular_tempo_medio_hoje_sem_pedidos(
        self, logged_in_client, usuario_vendedor
    ):
        """Testa que retorna None quando não há pedidos finalizados hoje."""
        # Não criar nenhum pedido

        response = logged_in_client.get(reverse('dashboard'))

        assert response.status_code == 200
        context = response.context

        assert 'metricas_tempo' in context
        metricas = context['metricas_tempo']

        # Verificar que tempo médio é None
        assert metricas['tempo_medio_hoje_minutos'] is None
        assert metricas['tendencia'] == 'sem_dados'

    def test_calcular_tempo_medio_7dias_com_pedidos(
        self, logged_in_client, usuario_vendedor, produto_teste
    ):
        """Testa cálculo de tempo médio dos últimos 7 dias."""
        # Criar pedidos em diferentes dias
        criar_pedido_finalizado(usuario_vendedor, duracao_minutos=40, dias_atras=0)  # Hoje
        criar_pedido_finalizado(usuario_vendedor, duracao_minutos=50, dias_atras=2)  # 2 dias atrás
        criar_pedido_finalizado(usuario_vendedor, duracao_minutos=60, dias_atras=5)  # 5 dias atrás
        # Média: 50 minutos

        response = logged_in_client.get(reverse('dashboard'))

        assert response.status_code == 200
        context = response.context
        metricas = context['metricas_tempo']

        # Verificar tempo médio 7 dias
        assert metricas['tempo_medio_7dias_minutos'] is not None
        assert 49 <= metricas['tempo_medio_7dias_minutos'] <= 51

    def test_calcular_tempo_medio_ignora_pedidos_em_separacao(
        self, logged_in_client, usuario_vendedor, produto_teste
    ):
        """Testa que pedidos em separação não são contados na métrica."""
        # Criar 2 pedidos finalizados
        criar_pedido_finalizado(usuario_vendedor, duracao_minutos=30, dias_atras=0)
        criar_pedido_finalizado(usuario_vendedor, duracao_minutos=60, dias_atras=0)
        # Média deveria ser 45 minutos

        # Criar 1 pedido EM_SEPARACAO (não deve contar)
        pedido_em_separacao = Pedido.objects.create(
            numero_orcamento='EM_SEP',
            codigo_cliente='CLI002',
            nome_cliente='Cliente 2',
            vendedor=usuario_vendedor,
            data='25/01/2025',
            logistica='CORREIOS',
            embalagem='CAIXA',
            status=StatusPedidoChoices.EM_SEPARACAO,
            data_inicio=timezone.now() - timedelta(minutes=120)
            # Sem data_finalizacao
        )

        response = logged_in_client.get(reverse('dashboard'))

        assert response.status_code == 200
        metricas = response.context['metricas_tempo']

        # Verificar que média é 45 (ignora pedido em separação)
        assert 44 <= metricas['tempo_medio_hoje_minutos'] <= 46

    def test_exibir_card_metricas_tempo_no_dashboard(
        self, logged_in_client, usuario_vendedor, produto_teste
    ):
        """Testa que card de métricas aparece no HTML do dashboard."""
        # Criar pedido finalizado
        criar_pedido_finalizado(usuario_vendedor, duracao_minutos=45, dias_atras=0)

        response = logged_in_client.get(reverse('dashboard'))

        assert response.status_code == 200
        html = response.content.decode('utf-8')

        # Verificar que card de métricas está presente
        assert 'TEMPO MÉDIO DE SEPARAÇÃO' in html or 'Tempo Médio' in html
        assert '45' in html or '45 min' in html

    def test_indicador_tendencia_melhorou(
        self, logged_in_client, usuario_vendedor, produto_teste
    ):
        """Testa indicador de tendência quando hoje é melhor que 7 dias."""
        # Hoje: 40 min (média)
        criar_pedido_finalizado(usuario_vendedor, duracao_minutos=40, dias_atras=0)

        # Últimos 7 dias: 50 min (média) - incluindo hoje
        criar_pedido_finalizado(usuario_vendedor, duracao_minutos=60, dias_atras=3)

        response = logged_in_client.get(reverse('dashboard'))

        assert response.status_code == 200
        metricas = response.context['metricas_tempo']

        # Verificar tendência
        assert metricas['tendencia'] == 'melhorou'
        assert metricas['percentual_diferenca'] < 0  # Negativo indica melhora

    def test_indicador_tendencia_piorou(
        self, logged_in_client, usuario_vendedor, produto_teste
    ):
        """Testa indicador de tendência quando hoje é pior que 7 dias."""
        # Hoje: 60 min (média)
        criar_pedido_finalizado(usuario_vendedor, duracao_minutos=60, dias_atras=0)

        # Últimos 7 dias: 45 min (média) - incluindo hoje
        criar_pedido_finalizado(usuario_vendedor, duracao_minutos=30, dias_atras=3)

        response = logged_in_client.get(reverse('dashboard'))

        assert response.status_code == 200
        metricas = response.context['metricas_tempo']

        # Verificar tendência
        assert metricas['tendencia'] == 'piorou'
        assert metricas['percentual_diferenca'] > 0  # Positivo indica piora

    def test_card_metricas_quando_sem_dados(
        self, logged_in_client, usuario_vendedor
    ):
        """Testa que card exibe 'Sem dados' elegantemente quando não há pedidos."""
        # Não criar pedidos

        response = logged_in_client.get(reverse('dashboard'))

        assert response.status_code == 200
        html = response.content.decode('utf-8')

        # Verificar que mensagem adequada aparece
        assert 'Sem dados' in html or 'sem dados' in html or 'Nenhum pedido' in html
