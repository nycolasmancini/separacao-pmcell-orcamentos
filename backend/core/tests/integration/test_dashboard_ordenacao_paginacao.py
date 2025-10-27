# -*- coding: utf-8 -*-
"""
Testes de integração para ordenação e paginação no Dashboard - Fase 19.

Testa:
- Ordenação por tempo decorrido (mais antigos primeiro)
- Paginação (10 cards por página)
- Navegação entre páginas com HTMX
- Busca por número de orçamento
- Busca por nome de cliente
- Filtro por vendedor
- Combinação de busca + paginação
- Resposta HTMX (partial HTML)
"""
import pytest
from django.test import Client
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal
from core.models import Usuario, Pedido, ItemPedido, StatusPedidoChoices
from core.domain.pedido.value_objects import Logistica, Embalagem
from core.infrastructure.persistence.models.produto import Produto


@pytest.fixture
def vendedor_usuario(db):
    """Cria usuário vendedor para testes."""
    return Usuario.objects.create_user(
        numero_login='1001',
        nome='Vendedor Teste',
        tipo='VENDEDOR',
        pin='1234',
        ativo=True
    )


@pytest.fixture
def vendedor_usuario_2(db):
    """Cria segundo usuário vendedor para testes de filtro."""
    return Usuario.objects.create_user(
        numero_login='1002',
        nome='Vendedor Dois',
        tipo='VENDEDOR',
        pin='5678',
        ativo=True
    )


@pytest.fixture
def separador_usuario(db):
    """Cria usuário separador para autenticação nos testes."""
    return Usuario.objects.create_user(
        numero_login='2001',
        nome='Separador Teste',
        tipo='SEPARADOR',
        pin='4321',
        ativo=True
    )


@pytest.fixture
def logged_in_client(client, separador_usuario):
    """Cliente autenticado como separador."""
    client.force_login(separador_usuario)
    session = client.session
    session['usuario_id'] = separador_usuario.id
    session['nome'] = separador_usuario.nome
    session['numero_login'] = separador_usuario.numero_login
    session['tipo'] = separador_usuario.tipo
    session.save()
    return client


@pytest.fixture
def create_pedido():
    """Factory para criar pedidos de teste."""
    def _create_pedido(numero_orcamento, nome_cliente, vendedor, minutes_ago=0):
        """
        Cria um pedido em separação.

        Args:
            numero_orcamento: Número do orçamento
            nome_cliente: Nome do cliente
            vendedor: Usuário vendedor
            minutes_ago: Quantos minutos atrás o pedido foi iniciado
        """
        pedido = Pedido.objects.create(
            numero_orcamento=numero_orcamento,
            codigo_cliente='12345',
            nome_cliente=nome_cliente,
            vendedor=vendedor,
            data='25/10/2025',
            logistica=Logistica.CORREIOS.value,
            embalagem=Embalagem.CAIXA.value,
            observacoes='Teste',
            status=StatusPedidoChoices.EM_SEPARACAO
        )

        # Ajustar data_inicio para simular tempo decorrido
        if minutes_ago > 0:
            pedido.data_inicio = timezone.now() - timedelta(minutes=minutes_ago)
            pedido.save()

        # Criar alguns produtos e itens para o pedido
        for i in range(3):
            # Criar produto
            produto, _ = Produto.objects.get_or_create(
                codigo=f'PR{pedido.id}{i:02d}',
                defaults={
                    'descricao': f'Produto {i}',
                    'quantidade': 1,
                    'valor_unitario': Decimal('100.00'),
                    'valor_total': Decimal('100.00')
                }
            )

            # Criar item do pedido
            ItemPedido.objects.create(
                pedido=pedido,
                produto=produto,
                quantidade_solicitada=1
            )

        return pedido

    return _create_pedido


@pytest.mark.django_db
class TestDashboardOrdenacao:
    """Testes de ordenação no dashboard."""

    def test_pedidos_ordenados_por_tempo_decorrido_mais_antigos_primeiro(
        self, logged_in_client, create_pedido, vendedor_usuario
    ):
        """
        Testa se pedidos são ordenados por tempo decorrido (mais antigos primeiro).
        """
        # Criar pedidos com tempos diferentes
        pedido_recente = create_pedido('ORC-001', 'Cliente A', vendedor_usuario, minutes_ago=5)
        pedido_medio = create_pedido('ORC-002', 'Cliente B', vendedor_usuario, minutes_ago=15)
        pedido_antigo = create_pedido('ORC-003', 'Cliente C', vendedor_usuario, minutes_ago=30)

        response = logged_in_client.get(reverse('dashboard'))

        assert response.status_code == 200
        pedidos = response.context['pedidos']['results']

        # Mais antigos devem aparecer primeiro
        assert len(pedidos) == 3
        assert pedidos[0]['pedido'].numero_orcamento == 'ORC-003'  # 30 min
        assert pedidos[1]['pedido'].numero_orcamento == 'ORC-002'  # 15 min
        assert pedidos[2]['pedido'].numero_orcamento == 'ORC-001'  # 5 min


@pytest.mark.django_db
class TestDashboardPaginacao:
    """Testes de paginação no dashboard."""

    def test_paginacao_mostra_10_pedidos_por_pagina(
        self, logged_in_client, create_pedido, vendedor_usuario
    ):
        """
        Testa se paginação exibe 10 pedidos por página.
        """
        # Criar 15 pedidos
        for i in range(15):
            create_pedido(f'ORC-{i:03d}', f'Cliente {i}', vendedor_usuario)

        # Página 1
        response = logged_in_client.get(reverse('dashboard'))
        assert response.status_code == 200

        pedidos_data = response.context['pedidos']
        assert pedidos_data['count'] == 15
        assert len(pedidos_data['results']) == 10
        assert pedidos_data['has_next'] is True
        assert pedidos_data['has_previous'] is False

    def test_navegacao_para_pagina_2(
        self, logged_in_client, create_pedido, vendedor_usuario
    ):
        """
        Testa navegação para segunda página.
        """
        # Criar 15 pedidos
        for i in range(15):
            create_pedido(f'ORC-{i:03d}', f'Cliente {i}', vendedor_usuario)

        # Página 2
        response = logged_in_client.get(reverse('dashboard'), {'page': 2})
        assert response.status_code == 200

        pedidos_data = response.context['pedidos']
        assert len(pedidos_data['results']) == 5  # Restante
        assert pedidos_data['has_next'] is False
        assert pedidos_data['has_previous'] is True

    def test_resposta_htmx_retorna_partial_html(
        self, logged_in_client, create_pedido, vendedor_usuario
    ):
        """
        Testa se requisição HTMX retorna apenas o partial HTML.
        """
        create_pedido('ORC-001', 'Cliente A', vendedor_usuario)

        response = logged_in_client.get(
            reverse('dashboard'),
            HTTP_HX_REQUEST='true'  # Header HTMX
        )

        assert response.status_code == 200
        # Verifica que não tem template base (sem <html>, <head>, etc)
        assert b'<!DOCTYPE html>' not in response.content
        # Deve ter apenas o grid de pedidos
        assert b'pedidos-grid' in response.content or b'ORC-001' in response.content


@pytest.mark.django_db
class TestDashboardBusca:
    """Testes de busca no dashboard."""

    def test_busca_por_numero_orcamento(
        self, logged_in_client, create_pedido, vendedor_usuario
    ):
        """
        Testa busca por número de orçamento.
        """
        create_pedido('ORC-123', 'Cliente A', vendedor_usuario)
        create_pedido('ORC-456', 'Cliente B', vendedor_usuario)
        create_pedido('ORC-789', 'Cliente C', vendedor_usuario)

        response = logged_in_client.get(reverse('dashboard'), {'search': 'ORC-123'})

        assert response.status_code == 200
        pedidos = response.context['pedidos']['results']
        assert len(pedidos) == 1
        assert pedidos[0]['pedido'].numero_orcamento == 'ORC-123'

    def test_busca_por_nome_cliente(
        self, logged_in_client, create_pedido, vendedor_usuario
    ):
        """
        Testa busca por nome de cliente.
        """
        create_pedido('ORC-001', 'João Silva', vendedor_usuario)
        create_pedido('ORC-002', 'Maria Santos', vendedor_usuario)
        create_pedido('ORC-003', 'João Pedro', vendedor_usuario)

        response = logged_in_client.get(reverse('dashboard'), {'search': 'João'})

        assert response.status_code == 200
        pedidos = response.context['pedidos']['results']
        assert len(pedidos) == 2
        assert 'João' in pedidos[0]['pedido'].nome_cliente
        assert 'João' in pedidos[1]['pedido'].nome_cliente


@pytest.mark.django_db
class TestDashboardFiltros:
    """Testes de filtros no dashboard."""

    def test_filtro_por_vendedor(
        self, logged_in_client, create_pedido, vendedor_usuario, vendedor_usuario_2
    ):
        """
        Testa filtro por vendedor.
        """
        create_pedido('ORC-001', 'Cliente A', vendedor_usuario)
        create_pedido('ORC-002', 'Cliente B', vendedor_usuario)
        create_pedido('ORC-003', 'Cliente C', vendedor_usuario_2)

        response = logged_in_client.get(
            reverse('dashboard'),
            {'vendedor': vendedor_usuario.id}
        )

        assert response.status_code == 200
        pedidos = response.context['pedidos']['results']
        assert len(pedidos) == 2
        assert pedidos[0]['pedido'].vendedor.id == vendedor_usuario.id
        assert pedidos[1]['pedido'].vendedor.id == vendedor_usuario.id

    def test_combinar_busca_e_filtro(
        self, logged_in_client, create_pedido, vendedor_usuario, vendedor_usuario_2
    ):
        """
        Testa combinação de busca e filtro por vendedor.
        """
        create_pedido('ORC-001', 'João Silva', vendedor_usuario)
        create_pedido('ORC-002', 'Maria Santos', vendedor_usuario)
        create_pedido('ORC-003', 'João Pedro', vendedor_usuario_2)

        response = logged_in_client.get(
            reverse('dashboard'),
            {'search': 'João', 'vendedor': vendedor_usuario.id}
        )

        assert response.status_code == 200
        pedidos = response.context['pedidos']['results']
        assert len(pedidos) == 1
        assert pedidos[0]['pedido'].numero_orcamento == 'ORC-001'
        assert pedidos[0]['pedido'].vendedor.id == vendedor_usuario.id
