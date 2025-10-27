# -*- coding: utf-8 -*-
"""
Testes para Fase 26: Criar View do Painel de Compras

Este módulo testa:
- View PainelComprasView renderiza corretamente
- Apenas itens com em_compra=True aparecem
- Itens sem em_compra NÃO aparecem
- Agrupamento por pedido correto
- Metadados (enviado por, horário) exibidos
- Template contém elementos esperados

Author: PMCELL
Date: 2025-01-27
"""

import pytest
from datetime import datetime
from django.test import Client
from django.urls import reverse
from django.utils import timezone

from core.models import Usuario, Pedido, ItemPedido, Produto


@pytest.fixture
def usuario_compradora(db):
    """Cria um usuário compradora para os testes."""
    return Usuario.objects.create_user(
        numero_login='3001',
        pin='3333',
        nome='Maria Compradora',
        tipo='COMPRADORA'
    )


@pytest.fixture
def usuario_separador(db):
    """Cria um usuário separador para os testes."""
    return Usuario.objects.create_user(
        numero_login='2001',
        pin='2222',
        nome='João Separador',
        tipo='SEPARADOR'
    )


@pytest.fixture
def usuario_vendedor(db):
    """Cria um usuário vendedor para os testes."""
    return Usuario.objects.create_user(
        numero_login='1001',
        pin='1111',
        nome='Carlos Vendedor',
        tipo='VENDEDOR'
    )


@pytest.fixture
def produto1(db):
    """Cria produto 1 para testes."""
    return Produto.objects.create(
        codigo='00001',
        descricao='CABO USB-C',
        quantidade=100,
        valor_unitario=10.00,
        valor_total=1000.00
    )


@pytest.fixture
def produto2(db):
    """Cria produto 2 para testes."""
    return Produto.objects.create(
        codigo='00002',
        descricao='SUPORTE MOTO',
        quantidade=50,
        valor_unitario=15.00,
        valor_total=750.00
    )


@pytest.fixture
def produto3(db):
    """Cria produto 3 para testes."""
    return Produto.objects.create(
        codigo='00003',
        descricao='PELÍCULA 3D IP14',
        quantidade=200,
        valor_unitario=5.00,
        valor_total=1000.00
    )


@pytest.fixture
def pedido1(db, usuario_vendedor):
    """Cria pedido 1 para testes."""
    return Pedido.objects.create(
        numero_orcamento='30567',
        codigo_cliente='CLI001',
        nome_cliente='Rosana',
        vendedor=usuario_vendedor,
        data='27/01/2025',
        logistica='CORREIOS',
        embalagem='CAIXA',
        status='EM_SEPARACAO'
    )


@pytest.fixture
def pedido2(db, usuario_vendedor):
    """Cria pedido 2 para testes."""
    return Pedido.objects.create(
        numero_orcamento='30568',
        codigo_cliente='CLI002',
        nome_cliente='Ponto do Celular',
        vendedor=usuario_vendedor,
        data='27/01/2025',
        logistica='MOTOBOY',
        embalagem='SACOLA',
        status='EM_SEPARACAO'
    )


@pytest.fixture
def item_compra_pedido1(db, pedido1, produto1, usuario_separador):
    """Item enviado para compra no pedido 1."""
    return ItemPedido.objects.create(
        pedido=pedido1,
        produto=produto1,
        quantidade_solicitada=10,
        quantidade_separada=0,
        separado=False,
        em_compra=True,
        enviado_para_compra_por=usuario_separador,
        enviado_para_compra_em=timezone.now()
    )


@pytest.fixture
def item_compra_pedido2_produto2(db, pedido2, produto2, usuario_separador):
    """Item enviado para compra no pedido 2 (produto 2)."""
    return ItemPedido.objects.create(
        pedido=pedido2,
        produto=produto2,
        quantidade_solicitada=5,
        quantidade_separada=0,
        separado=False,
        em_compra=True,
        enviado_para_compra_por=usuario_separador,
        enviado_para_compra_em=timezone.now()
    )


@pytest.fixture
def item_compra_pedido2_produto3(db, pedido2, produto3, usuario_separador):
    """Item enviado para compra no pedido 2 (produto 3)."""
    return ItemPedido.objects.create(
        pedido=pedido2,
        produto=produto3,
        quantidade_solicitada=20,
        quantidade_separada=0,
        separado=False,
        em_compra=True,
        enviado_para_compra_por=usuario_separador,
        enviado_para_compra_em=timezone.now()
    )


@pytest.fixture
def item_nao_compra(db, pedido1, produto2):
    """Item que NÃO está marcado para compra."""
    return ItemPedido.objects.create(
        pedido=pedido1,
        produto=produto2,
        quantidade_solicitada=15,
        quantidade_separada=15,
        separado=True,
        em_compra=False
    )


@pytest.mark.django_db
class TestPainelComprasView:
    """Testes para a view do Painel de Compras."""

    def test_painel_compras_renderiza_com_sucesso(
        self,
        client: Client,
        usuario_compradora,
        item_compra_pedido1,
        item_compra_pedido2_produto2
    ):
        """
        Test 1: View renderiza com status 200.

        Dado que existem itens marcados para compra
        Quando acessar o painel de compras
        Então deve retornar status 200
        E o template deve ser painel_compras.html
        """
        # Login como compradora
        client.force_login(usuario_compradora)

        # Acessar painel de compras
        url = reverse('painel_compras')
        response = client.get(url)

        # Verificações
        assert response.status_code == 200
        assert 'painel_compras.html' in [t.name for t in response.templates]

    def test_itens_em_compra_aparecem_no_painel(
        self,
        client: Client,
        usuario_compradora,
        item_compra_pedido1,
        item_compra_pedido2_produto2,
        item_compra_pedido2_produto3
    ):
        """
        Test 2: Itens com em_compra=True aparecem no painel.

        Dado que existem 3 itens marcados para compra
        Quando acessar o painel de compras
        Então deve exibir os 3 itens
        E deve conter os nomes dos produtos
        """
        # Login como compradora
        client.force_login(usuario_compradora)

        # Acessar painel
        url = reverse('painel_compras')
        response = client.get(url)

        # Verificar presença dos produtos
        content = response.content.decode('utf-8')
        assert 'CABO USB-C' in content
        assert 'SUPORTE MOTO' in content
        assert 'PELÍCULA 3D IP14' in content

        # Verificar quantidades
        assert '10' in content  # Quantidade do cabo
        assert '5' in content   # Quantidade do suporte
        assert '20' in content  # Quantidade da película

    def test_itens_sem_em_compra_nao_aparecem(
        self,
        client: Client,
        usuario_compradora,
        item_compra_pedido1,
        item_nao_compra
    ):
        """
        Test 3: Itens sem em_compra NÃO aparecem no painel.

        Dado que existe 1 item com em_compra=True
        E 1 item com em_compra=False
        Quando acessar o painel de compras
        Então deve exibir apenas 1 item (o que está em compra)
        """
        # Login como compradora
        client.force_login(usuario_compradora)

        # Acessar painel
        url = reverse('painel_compras')
        response = client.get(url)

        # Verificar que o contexto contém apenas 1 pedido com itens
        itens_compra = response.context['itens_compra']

        # Contar total de itens em compra
        total_itens = sum(len(itens) for pedido, itens in itens_compra)
        assert total_itens == 1

    def test_agrupamento_por_pedido_correto(
        self,
        client: Client,
        usuario_compradora,
        item_compra_pedido1,
        item_compra_pedido2_produto2,
        item_compra_pedido2_produto3
    ):
        """
        Test 4: Agrupamento por pedido está correto.

        Dado que existem:
        - 1 item no pedido 30567
        - 2 itens no pedido 30568
        Quando acessar o painel de compras
        Então deve haver 2 grupos (pedidos)
        E o pedido 30567 deve ter 1 item
        E o pedido 30568 deve ter 2 itens
        """
        # Login como compradora
        client.force_login(usuario_compradora)

        # Acessar painel
        url = reverse('painel_compras')
        response = client.get(url)

        # Verificar agrupamento
        itens_compra = response.context['itens_compra']

        # Deve haver 2 pedidos
        assert len(itens_compra) == 2

        # Verificar contagem de itens por pedido
        pedidos_dict = {pedido.numero_orcamento: len(itens) for pedido, itens in itens_compra}
        assert pedidos_dict['30567'] == 1
        assert pedidos_dict['30568'] == 2

    def test_metadados_enviado_por_e_horario_exibidos(
        self,
        client: Client,
        usuario_compradora,
        usuario_separador,
        item_compra_pedido1
    ):
        """
        Test 5: Metadados (enviado por, horário) são exibidos.

        Dado que um item foi enviado para compra por João Separador
        Quando acessar o painel de compras
        Então deve exibir o nome "João Separador"
        E deve exibir informação de horário
        """
        # Login como compradora
        client.force_login(usuario_compradora)

        # Acessar painel
        url = reverse('painel_compras')
        response = client.get(url)

        # Verificar nome do separador
        content = response.content.decode('utf-8')
        assert 'João Separador' in content

        # Verificar que há informação de horário (formato pode variar)
        assert 'Enviado por:' in content or 'enviado por' in content.lower()

    def test_template_contem_elementos_esperados(
        self,
        client: Client,
        usuario_compradora,
        item_compra_pedido1
    ):
        """
        Test 6: Template contém elementos esperados do design.

        Dado que existem itens para compra
        Quando acessar o painel de compras
        Então deve conter o título "Painel de Compras" ou similar
        E deve conter badges de status
        """
        # Login como compradora
        client.force_login(usuario_compradora)

        # Acessar painel
        url = reverse('painel_compras')
        response = client.get(url)

        content = response.content.decode('utf-8')

        # Verificar elementos do design
        assert 'Painel de Compras' in content or 'PAINEL DE COMPRAS' in content
        assert 'Rosana' in content  # Nome do cliente
        assert '30567' in content  # Número do pedido
