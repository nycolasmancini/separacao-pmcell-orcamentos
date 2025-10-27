# -*- coding: utf-8 -*-
"""
Testes para o partial template _card_pedido.html
Fase 18: Criar Componente de Card de Pedido
TDD - RED Phase
"""
import pytest
from django.template import Context, Template
from core.models import (
    Usuario, Pedido, ItemPedido, Produto,
    StatusPedidoChoices, LogisticaChoices, EmbalagemChoices
)


@pytest.fixture
def usuario_vendedor(db):
    """Cria um usuário vendedor para testes."""
    return Usuario.objects.create_user(
        numero_login=1,
        pin='1234',
        nome='Vendedor Teste',
        tipo='VENDEDOR'
    )


@pytest.fixture
def usuario_separador(db):
    """Cria um usuário separador para testes."""
    return Usuario.objects.create_user(
        numero_login=2,
        pin='5678',
        nome='Separador Teste',
        tipo='SEPARADOR'
    )


@pytest.fixture
def produto(db):
    """Cria um produto para testes."""
    from decimal import Decimal
    return Produto.objects.create(
        codigo='00001',
        descricao='Produto Teste',
        quantidade=10,
        valor_unitario=Decimal('10.00'),
        valor_total=Decimal('100.00')
    )


@pytest.fixture
def pedido_com_dados(db, usuario_vendedor, produto):
    """Cria um pedido completo para testes."""
    from decimal import Decimal
    from django.utils import timezone

    pedido = Pedido.objects.create(
        numero_orcamento='30567',
        codigo_cliente='CLI001',
        nome_cliente='Cliente Teste',
        vendedor=usuario_vendedor,
        data='25/01/2025',
        logistica='CORREIOS',
        embalagem='CAIXA',
        status=StatusPedidoChoices.EM_SEPARACAO
    )

    # Definir data_inicio manualmente
    pedido.data_inicio = timezone.now()
    pedido.save()

    # Criar itens
    ItemPedido.objects.create(
        pedido=pedido,
        produto=produto,
        quantidade_solicitada=5
    )
    ItemPedido.objects.create(
        pedido=pedido,
        produto=produto,
        quantidade_solicitada=3
    )

    return pedido


@pytest.mark.django_db
class TestCardPedidoPartial:
    """Testes para o partial template de card de pedido."""

    def test_partial_renderiza_com_dados_validos(self, pedido_com_dados):
        """Testa se o partial renderiza sem erros com dados válidos."""
        pedido_data = {
            'pedido': pedido_com_dados,
            'tempo_decorrido_minutos': 15,
            'progresso_percentual': 50,
            'itens_separados': 1,
            'total_itens': 2,
            'separadores': []
        }

        template = Template("{% load static %}{% include 'partials/_card_pedido.html' %}")
        context = Context({'pedido_data': pedido_data})
        rendered = template.render(context)

        assert rendered is not None
        assert len(rendered.strip()) > 0

    def test_partial_exibe_numero_orcamento(self, pedido_com_dados):
        """Testa se o partial exibe o número do orçamento corretamente."""
        pedido_data = {
            'pedido': pedido_com_dados,
            'tempo_decorrido_minutos': 15,
            'progresso_percentual': 50,
            'itens_separados': 1,
            'total_itens': 2,
            'separadores': []
        }

        template = Template("{% load static %}{% include 'partials/_card_pedido.html' %}")
        context = Context({'pedido_data': pedido_data})
        rendered = template.render(context)

        assert '#30567' in rendered

    def test_partial_exibe_nome_cliente(self, pedido_com_dados):
        """Testa se o partial exibe o nome do cliente."""
        pedido_data = {
            'pedido': pedido_com_dados,
            'tempo_decorrido_minutos': 15,
            'progresso_percentual': 50,
            'itens_separados': 1,
            'total_itens': 2,
            'separadores': []
        }

        template = Template("{% load static %}{% include 'partials/_card_pedido.html' %}")
        context = Context({'pedido_data': pedido_data})
        rendered = template.render(context)

        assert 'Cliente Teste' in rendered

    def test_partial_exibe_vendedor(self, pedido_com_dados):
        """Testa se o partial exibe o nome do vendedor."""
        pedido_data = {
            'pedido': pedido_com_dados,
            'tempo_decorrido_minutos': 15,
            'progresso_percentual': 50,
            'itens_separados': 1,
            'total_itens': 2,
            'separadores': []
        }

        template = Template("{% load static %}{% include 'partials/_card_pedido.html' %}")
        context = Context({'pedido_data': pedido_data})
        rendered = template.render(context)

        assert 'Vendedor Teste' in rendered

    def test_partial_exibe_badges_logistica_embalagem(self, pedido_com_dados):
        """Testa se o partial exibe os badges de logística e embalagem."""
        pedido_data = {
            'pedido': pedido_com_dados,
            'tempo_decorrido_minutos': 15,
            'progresso_percentual': 50,
            'itens_separados': 1,
            'total_itens': 2,
            'separadores': []
        }

        template = Template("{% load static %}{% include 'partials/_card_pedido.html' %}")
        context = Context({'pedido_data': pedido_data})
        rendered = template.render(context)

        assert 'Correios' in rendered
        assert 'Caixa' in rendered

    def test_partial_exibe_tempo_decorrido(self, pedido_com_dados):
        """Testa se o partial exibe o tempo decorrido em minutos."""
        pedido_data = {
            'pedido': pedido_com_dados,
            'tempo_decorrido_minutos': 25,
            'progresso_percentual': 50,
            'itens_separados': 1,
            'total_itens': 2,
            'separadores': []
        }

        template = Template("{% load static %}{% include 'partials/_card_pedido.html' %}")
        context = Context({'pedido_data': pedido_data})
        rendered = template.render(context)

        assert '25 min' in rendered

    def test_partial_exibe_progresso_percentual(self, pedido_com_dados):
        """Testa se o partial exibe o progresso percentual corretamente."""
        pedido_data = {
            'pedido': pedido_com_dados,
            'tempo_decorrido_minutos': 15,
            'progresso_percentual': 75,
            'itens_separados': 3,
            'total_itens': 4,
            'separadores': []
        }

        template = Template("{% load static %}{% include 'partials/_card_pedido.html' %}")
        context = Context({'pedido_data': pedido_data})
        rendered = template.render(context)

        assert '75%' in rendered
        assert '3/4 itens separados' in rendered

    def test_partial_barra_progresso_tem_largura_correta(self, pedido_com_dados):
        """Testa se a barra de progresso tem a largura CSS correta."""
        pedido_data = {
            'pedido': pedido_com_dados,
            'tempo_decorrido_minutos': 15,
            'progresso_percentual': 60,
            'itens_separados': 3,
            'total_itens': 5,
            'separadores': []
        }

        template = Template("{% load static %}{% include 'partials/_card_pedido.html' %}")
        context = Context({'pedido_data': pedido_data})
        rendered = template.render(context)

        assert 'width: 60%' in rendered

    def test_partial_exibe_separadores_ativos(self, pedido_com_dados, usuario_separador):
        """Testa se o partial exibe a lista de separadores ativos."""
        separador2 = Usuario.objects.create_user(
            numero_login=3,
            pin='9999',
            nome='Separador 2',
            tipo='SEPARADOR'
        )

        pedido_data = {
            'pedido': pedido_com_dados,
            'tempo_decorrido_minutos': 15,
            'progresso_percentual': 50,
            'itens_separados': 1,
            'total_itens': 2,
            'separadores': [usuario_separador, separador2]
        }

        template = Template("{% load static %}{% include 'partials/_card_pedido.html' %}")
        context = Context({'pedido_data': pedido_data})
        rendered = template.render(context)

        assert 'Separando:' in rendered
        assert 'Separador Teste' in rendered
        assert 'Separador 2' in rendered

    def test_partial_exibe_mensagem_sem_separadores(self, pedido_com_dados):
        """Testa se o partial exibe mensagem quando não há separadores ativos."""
        pedido_data = {
            'pedido': pedido_com_dados,
            'tempo_decorrido_minutos': 15,
            'progresso_percentual': 50,
            'itens_separados': 1,
            'total_itens': 2,
            'separadores': []
        }

        template = Template("{% load static %}{% include 'partials/_card_pedido.html' %}")
        context = Context({'pedido_data': pedido_data})
        rendered = template.render(context)

        assert 'Nenhum separador ativo' in rendered

    def test_partial_tem_classes_hover_effect(self, pedido_com_dados):
        """Testa se o partial tem as classes CSS para hover effect."""
        pedido_data = {
            'pedido': pedido_com_dados,
            'tempo_decorrido_minutos': 15,
            'progresso_percentual': 50,
            'itens_separados': 1,
            'total_itens': 2,
            'separadores': []
        }

        template = Template("{% load static %}{% include 'partials/_card_pedido.html' %}")
        context = Context({'pedido_data': pedido_data})
        rendered = template.render(context)

        assert 'hover:shadow-xl' in rendered
        assert 'cursor-pointer' in rendered
