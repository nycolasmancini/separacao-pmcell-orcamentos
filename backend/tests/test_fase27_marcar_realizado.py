# -*- coding: utf-8 -*-
"""
Testes da Fase 27: Implementar Checkbox "Pedido Realizado"

Objetivo:
- Compradora marca quando pedido foi feito
- Checkbox funcional com HTMX
- Badge muda de cor (laranja → azul)
- Metadados salvos (usuário, timestamp)

Metodologia TDD: RED → GREEN → REFACTOR
"""
import pytest
from django.test import Client
from django.urls import reverse
from django.utils import timezone
from core.models import Usuario, Pedido, ItemPedido, Produto


@pytest.fixture
def client():
    """Fixture do Django test client."""
    return Client()


@pytest.fixture
def compradora():
    """Fixture de usuário compradora."""
    usuario = Usuario.objects.create_user(
        numero_login=300,
        pin='3000',
        nome='Compradora Teste',
        tipo='COMPRADORA'
    )
    return usuario


@pytest.fixture
def separador():
    """Fixture de usuário separador."""
    usuario = Usuario.objects.create_user(
        numero_login=200,
        pin='2000',
        nome='Separador Teste',
        tipo='SEPARADOR'
    )
    return usuario


@pytest.fixture
def vendedor():
    """Fixture de usuário vendedor."""
    usuario = Usuario.objects.create_user(
        numero_login=100,
        pin='1000',
        nome='Vendedor Teste',
        tipo='VENDEDOR'
    )
    return usuario


@pytest.fixture
def produto():
    """Fixture de produto."""
    return Produto.objects.create(
        codigo='00010',
        descricao='Produto Teste para Compra',
        quantidade=100,
        valor_unitario=50.00,
        valor_total=5000.00
    )


@pytest.fixture
def pedido(vendedor):
    """Fixture de pedido."""
    return Pedido.objects.create(
        numero_orcamento='30999',
        codigo_cliente='CLI001',
        nome_cliente='Cliente Teste',
        vendedor=vendedor,
        data='27/01/2025',
        logistica='CORREIOS',
        embalagem='CAIXA',
        status='EM_SEPARACAO'
    )


@pytest.fixture
def item_em_compra(pedido, produto, separador):
    """Fixture de item enviado para compra."""
    item = ItemPedido.objects.create(
        pedido=pedido,
        produto=produto,
        quantidade_solicitada=10,
        quantidade_separada=0,
        separado=False,
        em_compra=True,
        enviado_para_compra_por=separador,
        enviado_para_compra_em=timezone.now()
    )
    return item


@pytest.mark.django_db
class TestMarcarPedidoRealizado:
    """Testes para marcar item como pedido realizado."""

    def test_marcar_item_como_realizado(self, client, compradora, item_em_compra):
        """
        Testa marcação de item como pedido realizado.

        Cenário:
        - Compradora autenticada
        - Item em compra existe
        - POST para endpoint de marcar realizado
        - Item deve ser atualizado com pedido_realizado=True
        """
        # Login da compradora
        client.force_login(compradora)

        # URL do endpoint
        url = reverse('marcar_realizado', kwargs={'item_id': item_em_compra.id})

        # POST com HTMX header
        response = client.post(
            url,
            HTTP_HX_REQUEST='true'
        )

        # Verificações
        assert response.status_code == 200

        # Recarregar item do banco
        item_em_compra.refresh_from_db()

        assert item_em_compra.pedido_realizado is True
        assert item_em_compra.realizado_por == compradora
        assert item_em_compra.realizado_em is not None

    def test_badge_muda_quando_pedido_realizado(self, client, compradora, item_em_compra):
        """
        Testa mudança visual do badge após marcar realizado.

        Cenário:
        - Item marcado como realizado
        - Badge deve mudar de laranja para azul
        - Texto deve mudar para "Já comprado"
        """
        # Login e marcar item
        client.force_login(compradora)
        item_em_compra.marcar_realizado(compradora)

        # Requisitar painel de compras
        url = reverse('painel_compras')
        response = client.get(url)

        # Verificações no HTML
        content = response.content.decode('utf-8')

        # Badge azul deve aparecer (bg-blue-100 text-blue-800)
        assert 'bg-blue-100' in content
        assert 'text-blue-800' in content
        assert 'Já comprado' in content or 'Pedido Realizado' in content

    def test_apenas_compradora_pode_marcar(self, client, separador, item_em_compra):
        """
        Testa que apenas compradora pode marcar pedido realizado.

        Cenário:
        - Separador tenta marcar item
        - Deve retornar erro 403 (Forbidden)
        """
        # Login como separador
        client.force_login(separador)

        # URL do endpoint
        url = reverse('marcar_realizado', kwargs={'item_id': item_em_compra.id})

        # POST com HTMX header
        response = client.post(
            url,
            HTTP_HX_REQUEST='true'
        )

        # Verificações
        assert response.status_code == 403

        # Item não deve ter sido alterado
        item_em_compra.refresh_from_db()
        assert item_em_compra.pedido_realizado is False

    def test_item_realizado_aparece_diferente(self, client, compradora, item_em_compra):
        """
        Testa que item realizado aparece com badge azul.

        Cenário:
        - Item marcado como realizado
        - Painel de compras renderizado
        - Badge deve ser azul (não laranja)
        """
        # Marcar item como realizado
        item_em_compra.marcar_realizado(compradora)

        # Login e acessar painel
        client.force_login(compradora)
        url = reverse('painel_compras')
        response = client.get(url)

        # Verificações
        assert response.status_code == 200
        content = response.content.decode('utf-8')

        # Badge azul deve estar presente
        assert 'bg-blue-100 text-blue-800' in content or 'bg-blue-' in content

    def test_checkbox_funciona_com_htmx(self, client, compradora, item_em_compra):
        """
        Testa integração com HTMX (resposta parcial).

        Cenário:
        - POST com header HX-Request
        - Resposta deve conter apenas o badge atualizado (HTML parcial)
        - Não deve ser página completa
        """
        # Login
        client.force_login(compradora)

        # URL do endpoint
        url = reverse('marcar_realizado', kwargs={'item_id': item_em_compra.id})

        # POST com HTMX header
        response = client.post(
            url,
            HTTP_HX_REQUEST='true'
        )

        # Verificações
        assert response.status_code == 200

        content = response.content.decode('utf-8')

        # Resposta deve ser HTML parcial (badge)
        assert '<span' in content
        assert 'badge' in content.lower() or 'bg-' in content

        # NÃO deve conter estrutura completa de página
        assert '<!DOCTYPE html>' not in content
        assert '<html>' not in content

    def test_metadados_realizado_salvos(self, client, compradora, item_em_compra):
        """
        Testa que metadados (usuário, timestamp) são salvos corretamente.

        Cenário:
        - Compradora marca item como realizado
        - realizado_por deve ser a compradora
        - realizado_em deve ser timestamp atual
        """
        # Login
        client.force_login(compradora)

        # Timestamp antes da ação
        before = timezone.now()

        # URL do endpoint
        url = reverse('marcar_realizado', kwargs={'item_id': item_em_compra.id})

        # POST
        response = client.post(
            url,
            HTTP_HX_REQUEST='true'
        )

        # Timestamp depois da ação
        after = timezone.now()

        # Verificações
        assert response.status_code == 200

        item_em_compra.refresh_from_db()

        # Verificar usuário
        assert item_em_compra.realizado_por == compradora

        # Verificar timestamp (entre before e after)
        assert item_em_compra.realizado_em is not None
        assert before <= item_em_compra.realizado_em <= after


@pytest.mark.django_db
class TestMetodoMarcarRealizado:
    """Testes do método marcar_realizado() do modelo."""

    def test_metodo_marca_item_corretamente(self, compradora, item_em_compra):
        """
        Testa método marcar_realizado() do modelo ItemPedido.

        Cenário:
        - Método deve atualizar todos os campos
        - Deve salvar no banco automaticamente
        """
        # Estado inicial
        assert item_em_compra.pedido_realizado is False
        assert item_em_compra.realizado_por is None
        assert item_em_compra.realizado_em is None

        # Executar método
        item_em_compra.marcar_realizado(compradora)

        # Recarregar do banco
        item_em_compra.refresh_from_db()

        # Verificações
        assert item_em_compra.pedido_realizado is True
        assert item_em_compra.realizado_por == compradora
        assert item_em_compra.realizado_em is not None
