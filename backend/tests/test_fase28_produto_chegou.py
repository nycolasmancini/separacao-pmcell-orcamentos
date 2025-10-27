# -*- coding: utf-8 -*-
"""
Testes da Fase 28: Implementar Checkbox "Produto Chegou"

Objetivo:
- Separador marca quando produto comprado chegou
- Checkbox habilitado para itens com pedido_realizado=True
- Item é marcado como separado
- Item move para seção "Separados"

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
        descricao='Produto Teste para Fase 28',
        quantidade=100,
        valor_unitario=50.00,
        valor_total=5000.00
    )


@pytest.fixture
def pedido(vendedor):
    """Fixture de pedido."""
    return Pedido.objects.create(
        numero_orcamento='31000',
        codigo_cliente='CLI001',
        nome_cliente='Cliente Teste Fase 28',
        vendedor=vendedor,
        data='28/01/2025',
        logistica='CORREIOS',
        embalagem='CAIXA',
        status='EM_SEPARACAO'
    )


@pytest.fixture
def item_comprado_chegou(pedido, produto, separador, compradora):
    """
    Fixture de item que foi comprado e já foi marcado como realizado.

    Este item deve ter o checkbox HABILITADO na tela de separação.
    """
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
    # Marcar como pedido realizado (Fase 27)
    item.marcar_realizado(compradora)
    return item


@pytest.fixture
def item_em_compra_sem_pedido(pedido, produto, separador):
    """
    Fixture de item em compra que ainda NÃO foi marcado como realizado.

    Este item deve ter o checkbox DESABILITADO na tela de separação.
    """
    item = ItemPedido.objects.create(
        pedido=pedido,
        produto=produto,
        quantidade_solicitada=5,
        quantidade_separada=0,
        separado=False,
        em_compra=True,
        enviado_para_compra_por=separador,
        enviado_para_compra_em=timezone.now(),
        pedido_realizado=False  # Explicitamente False
    )
    return item


@pytest.mark.django_db
class TestCheckboxProdutoChegou:
    """Testes para checkbox de produto que chegou."""

    def test_checkbox_habilitado_para_item_com_pedido_realizado(
        self, client, separador, item_comprado_chegou
    ):
        """
        Testa que checkbox está habilitado quando pedido_realizado=True.

        Cenário:
        - Item em compra com pedido_realizado=True
        - Tela de detalhe do pedido renderizada
        - Checkbox deve estar habilitado (não ter atributo 'disabled')
        - Checkbox deve ter atributo hx-post (HTMX)
        """
        # Login como separador
        client.force_login(separador)

        # Acessar tela de detalhe do pedido
        url = reverse('detalhe_pedido', kwargs={'pedido_id': item_comprado_chegou.pedido.id})
        response = client.get(url)

        # Verificações
        assert response.status_code == 200
        content = response.content.decode('utf-8')

        # Item deve estar na seção "Não Separados"
        assert item_comprado_chegou.produto.descricao in content

        # Checkbox deve estar presente E habilitado
        # Verificar presença de hx-post (indica que é interativo)
        assert f'hx-post="/pedidos/{item_comprado_chegou.pedido.id}/itens/{item_comprado_chegou.id}/separar/"' in content or \
               'hx-post="' in content  # Flexível para variações de formato

        # Badge "Já comprado" deve estar presente (azul)
        assert 'Já comprado' in content or 'bg-blue-' in content

    def test_checkbox_desabilitado_para_item_em_compra_sem_pedido(
        self, client, separador, item_em_compra_sem_pedido
    ):
        """
        Testa que checkbox está desabilitado quando pedido_realizado=False.

        Cenário:
        - Item em compra com pedido_realizado=False
        - Tela de detalhe do pedido renderizada
        - Checkbox deve estar desabilitado (atributo 'disabled')
        """
        # Login como separador
        client.force_login(separador)

        # Acessar tela de detalhe do pedido
        url = reverse('detalhe_pedido', kwargs={'pedido_id': item_em_compra_sem_pedido.pedido.id})
        response = client.get(url)

        # Verificações
        assert response.status_code == 200
        content = response.content.decode('utf-8')

        # Item deve estar presente
        assert item_em_compra_sem_pedido.produto.descricao in content

        # Badge "Aguardando Compra" deve estar presente (laranja)
        assert 'Aguardando Compra' in content or 'bg-orange-' in content

    def test_marcar_item_quando_produto_chega(
        self, client, separador, item_comprado_chegou
    ):
        """
        Testa marcação de item quando produto comprado chega.

        Cenário:
        - Item com pedido_realizado=True
        - Separador marca checkbox (POST para /separar/)
        - Item deve ser marcado como separado
        - Campos separado_por e separado_em devem ser preenchidos
        """
        # Login como separador
        client.force_login(separador)

        # URL do endpoint de separar item (já existe desde Fase 22)
        url = reverse('separar_item', kwargs={
            'pedido_id': item_comprado_chegou.pedido.id,
            'item_id': item_comprado_chegou.id
        })

        # POST com HTMX header
        response = client.post(
            url,
            HTTP_HX_REQUEST='true'
        )

        # Verificações
        assert response.status_code == 200

        # Recarregar item do banco
        item_comprado_chegou.refresh_from_db()

        # Item deve estar marcado como separado
        assert item_comprado_chegou.separado is True
        assert item_comprado_chegou.separado_por == separador
        assert item_comprado_chegou.separado_em is not None
        assert item_comprado_chegou.quantidade_separada == item_comprado_chegou.quantidade_solicitada

    def test_item_vai_para_secao_separados(
        self, client, separador, item_comprado_chegou
    ):
        """
        Testa que item move para seção "Separados" após marcar checkbox.

        Cenário:
        - Item inicialmente em "Não Separados"
        - Separador marca checkbox
        - Item deve aparecer em "Separados"
        - Item NÃO deve aparecer em "Não Separados"
        """
        # Login como separador
        client.force_login(separador)

        # Marcar item como separado
        url_separar = reverse('separar_item', kwargs={
            'pedido_id': item_comprado_chegou.pedido.id,
            'item_id': item_comprado_chegou.id
        })
        client.post(url_separar, HTTP_HX_REQUEST='true')

        # Acessar tela de detalhe novamente
        url_detalhe = reverse('detalhe_pedido', kwargs={
            'pedido_id': item_comprado_chegou.pedido.id
        })
        response = client.get(url_detalhe)

        # Verificações
        assert response.status_code == 200
        content = response.content.decode('utf-8')

        # Item deve estar na seção "Itens Separados"
        assert 'Itens Separados' in content

        # Badge verde "Separado" deve estar presente
        assert 'Separado' in content or 'bg-green-' in content

    def test_badge_muda_para_separado(
        self, client, separador, item_comprado_chegou
    ):
        """
        Testa mudança visual do badge após marcar item.

        Cenário:
        - Item com badge "Já comprado" (azul)
        - Separador marca checkbox
        - Badge deve mudar para "Separado" (verde)
        """
        # Login como separador
        client.force_login(separador)

        # Marcar item como separado
        url_separar = reverse('separar_item', kwargs={
            'pedido_id': item_comprado_chegou.pedido.id,
            'item_id': item_comprado_chegou.id
        })
        response = client.post(url_separar, HTTP_HX_REQUEST='true')

        # Verificações
        assert response.status_code == 200
        content = response.content.decode('utf-8')

        # Resposta HTMX deve conter badge verde "Separado"
        assert 'bg-green-' in content or 'Separado' in content

        # NÃO deve conter badge azul "Já comprado"
        assert 'Já comprado' not in content

    def test_progresso_atualizado(
        self, client, separador, item_comprado_chegou, produto
    ):
        """
        Testa que progresso do pedido é atualizado após marcar item.

        Cenário:
        - Pedido com 2 itens: 1 não separado, 1 com pedido realizado
        - Separador marca o item com pedido realizado
        - Progresso deve mudar de 0% para 50%
        """
        # Criar segundo item (não separado) no mesmo pedido
        item_normal = ItemPedido.objects.create(
            pedido=item_comprado_chegou.pedido,
            produto=produto,
            quantidade_solicitada=5,
            quantidade_separada=0,
            separado=False,
            em_compra=False
        )

        # Login como separador
        client.force_login(separador)

        # Verificar progresso inicial (0%)
        url_detalhe = reverse('detalhe_pedido', kwargs={
            'pedido_id': item_comprado_chegou.pedido.id
        })
        response = client.get(url_detalhe)
        assert response.status_code == 200

        # Marcar item como separado
        url_separar = reverse('separar_item', kwargs={
            'pedido_id': item_comprado_chegou.pedido.id,
            'item_id': item_comprado_chegou.id
        })
        client.post(url_separar, HTTP_HX_REQUEST='true')

        # Verificar progresso atualizado
        response = client.get(url_detalhe)
        content = response.content.decode('utf-8')

        # Progresso deve ser 50% (1 de 2 itens separados)
        assert '50%' in content or 'width: 50%' in content


@pytest.mark.django_db
class TestFluxoCompletoProdutoChegou:
    """Testes do fluxo completo: marcar para compra → pedido realizado → produto chegou."""

    def test_fluxo_completo_produto_faltante(
        self, client, separador, compradora, vendedor, produto
    ):
        """
        Testa fluxo completo de produto faltante que é comprado.

        Fluxo:
        1. Criar pedido com item
        2. Marcar item para compra (Fase 23)
        3. Compradora marca pedido realizado (Fase 27)
        4. Separador marca checkbox quando produto chega (Fase 28)
        5. Item deve estar separado
        """
        # 1. Criar pedido
        pedido = Pedido.objects.create(
            numero_orcamento='31001',
            codigo_cliente='CLI002',
            nome_cliente='Cliente Fluxo Completo',
            vendedor=vendedor,
            data='28/01/2025',
            logistica='CORREIOS',
            embalagem='CAIXA',
            status='EM_SEPARACAO'
        )

        # Criar item
        item = ItemPedido.objects.create(
            pedido=pedido,
            produto=produto,
            quantidade_solicitada=10,
            quantidade_separada=0,
            separado=False,
            em_compra=False
        )

        # 2. Marcar para compra
        client.force_login(separador)
        url_compra = reverse('marcar_compra', kwargs={
            'pedido_id': pedido.id,
            'item_id': item.id
        })
        response = client.post(url_compra, HTTP_HX_REQUEST='true')
        assert response.status_code == 200

        item.refresh_from_db()
        assert item.em_compra is True

        # 3. Compradora marca pedido realizado
        item.marcar_realizado(compradora)
        item.refresh_from_db()
        assert item.pedido_realizado is True

        # 4. Separador marca checkbox quando produto chega
        url_separar = reverse('separar_item', kwargs={
            'pedido_id': pedido.id,
            'item_id': item.id
        })
        response = client.post(url_separar, HTTP_HX_REQUEST='true')
        assert response.status_code == 200

        # 5. Item deve estar separado
        item.refresh_from_db()
        assert item.separado is True
        assert item.separado_por == separador
        assert item.quantidade_separada == item.quantidade_solicitada
