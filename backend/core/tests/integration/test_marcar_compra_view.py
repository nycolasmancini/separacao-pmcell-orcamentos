# -*- coding: utf-8 -*-
"""
Testes de Integração para MarcarParaCompraView (Fase 23).

Testes E2E da view HTMX que permite marcar itens para compra.

Author: PMCELL
Date: 2025-01-27
"""

import pytest
from decimal import Decimal
from django.test import Client
from django.urls import reverse

from core.models import Usuario, Pedido, ItemPedido, Produto
from core.domain.pedido.value_objects import StatusPedido, Logistica, Embalagem


@pytest.fixture
def client():
    """Cliente Django para testes."""
    return Client()


@pytest.fixture
def usuario_teste(db):
    """Cria usuário de teste."""
    usuario = Usuario.objects.create(
        numero_login=1,
        nome="Maria Separadora",
        tipo="SEPARADOR",
        ativo=True
    )
    usuario.set_password("1234")
    usuario.save()
    return usuario


@pytest.fixture
def vendedor_teste(db):
    """Cria vendedor de teste."""
    vendedor = Usuario.objects.create(
        numero_login=2,
        nome="João Silva",
        tipo="VENDEDOR",
        ativo=True
    )
    vendedor.set_password("1234")
    vendedor.save()
    return vendedor


@pytest.fixture
def produto_teste(db):
    """Cria produto de teste."""
    return Produto.objects.create(
        codigo="12345",
        descricao="Capinha iPhone 13 Pro",
        quantidade=1,
        valor_unitario=Decimal("59.90"),
        valor_total=Decimal("59.90")
    )


@pytest.fixture
def pedido_com_itens(db, produto_teste, vendedor_teste):
    """Cria pedido com itens não separados."""
    pedido = Pedido.objects.create(
        numero_orcamento="30567",
        codigo_cliente="CLI001",
        nome_cliente="Rosana",
        vendedor=vendedor_teste,
        data="27/10/2025",
        logistica=Logistica.CORREIOS.value,
        embalagem=Embalagem.CAIXA.value,
        status=StatusPedido.EM_SEPARACAO.value,
        observacoes="Teste"
    )

    # Criar 3 itens
    item1 = ItemPedido.objects.create(
        pedido=pedido,
        produto=produto_teste,
        quantidade_solicitada=2,
        quantidade_separada=0,
        separado=False,
        em_compra=False
    )

    item2 = ItemPedido.objects.create(
        pedido=pedido,
        produto=produto_teste,
        quantidade_solicitada=1,
        quantidade_separada=0,
        separado=False,
        em_compra=False
    )

    item3 = ItemPedido.objects.create(
        pedido=pedido,
        produto=produto_teste,
        quantidade_solicitada=3,
        quantidade_separada=0,
        separado=False,
        em_compra=False
    )

    return pedido


@pytest.mark.django_db
class TestMarcarParaCompraView:
    """Testes de integração para MarcarParaCompraView."""

    def test_marcar_item_para_compra_com_sucesso(self, client, usuario_teste, pedido_com_itens):
        """
        Testa marcação bem-sucedida de item para compra via HTMX.

        Given: Um usuário autenticado e um pedido com itens não separados
        When: Usuário clica em "Marcar para Compra" via HTMX
        Then: Item é marcado como em_compra e retorna HTML atualizado
        """
        # Autenticar usuário
        client.force_login(usuario_teste)
        session = client.session
        session['usuario_id'] = usuario_teste.id
        session.save()

        item = pedido_com_itens.itens.first()
        url = reverse('marcar_compra', args=[pedido_com_itens.id, item.id])

        # Fazer requisição HTMX
        response = client.post(url, HTTP_HX_REQUEST='true')

        # Assert
        assert response.status_code == 200
        assert 'item-container' in response.content.decode()
        assert 'orange' in response.content.decode()  # Cor laranja
        assert 'Aguardando Compra' in response.content.decode()

        # Verificar banco de dados
        item.refresh_from_db()
        assert item.em_compra is True
        assert item.enviado_para_compra_por == usuario_teste
        assert item.enviado_para_compra_em is not None
        assert item.separado is False  # NÃO conta como separado

    def test_requisicao_sem_htmx_header_retorna_erro(self, client, usuario_teste, pedido_com_itens):
        """
        Testa que requisição sem HX-Request header é rejeitada.

        Given: Um usuário autenticado
        When: Requisição é feita SEM header HX-Request
        Then: Retorna erro 400
        """
        # Autenticar usuário
        client.force_login(usuario_teste)
        session = client.session
        session['usuario_id'] = usuario_teste.id
        session.save()

        item = pedido_com_itens.itens.first()
        url = reverse('marcar_compra', args=[pedido_com_itens.id, item.id])

        # Fazer requisição SEM HTMX
        response = client.post(url)

        # Assert
        assert response.status_code == 400
        assert b'erro' in response.content.lower()

    def test_marcar_item_ja_separado_retorna_erro(self, client, usuario_teste, pedido_com_itens):
        """
        Testa erro ao tentar marcar item já separado.

        Given: Um item já marcado como separado
        When: Tentativa de marcar para compra
        Then: Retorna erro 400 com mensagem
        """
        # Autenticar usuário
        client.force_login(usuario_teste)
        session = client.session
        session['usuario_id'] = usuario_teste.id
        session.save()

        # Marcar item como separado
        item = pedido_com_itens.itens.first()
        item.separado = True
        item.separado_por = usuario_teste
        item.quantidade_separada = item.quantidade_solicitada
        item.save()

        url = reverse('marcar_compra', args=[pedido_com_itens.id, item.id])

        # Fazer requisição HTMX
        response = client.post(url, HTTP_HX_REQUEST='true')

        # Assert
        assert response.status_code == 400
        assert 'já foi separado' in response.content.decode().lower()

    def test_marcar_item_ja_em_compra_retorna_erro(self, client, usuario_teste, pedido_com_itens):
        """
        Testa erro ao tentar marcar item que já está em compra.

        Given: Um item já marcado como em_compra
        When: Tentativa de marcar novamente
        Then: Retorna erro 400
        """
        # Autenticar usuário
        client.force_login(usuario_teste)
        session = client.session
        session['usuario_id'] = usuario_teste.id
        session.save()

        # Marcar item como em compra
        item = pedido_com_itens.itens.first()
        item.em_compra = True
        item.enviado_para_compra_por = usuario_teste
        item.save()

        url = reverse('marcar_compra', args=[pedido_com_itens.id, item.id])

        # Fazer requisição HTMX
        response = client.post(url, HTTP_HX_REQUEST='true')

        # Assert
        assert response.status_code == 400
        assert 'já está marcado para compra' in response.content.decode().lower()

    def test_item_inexistente_retorna_erro(self, client, usuario_teste, pedido_com_itens):
        """
        Testa erro ao tentar marcar item inexistente.

        Given: Um pedido válido
        When: Requisição com item_id inexistente
        Then: Retorna erro 400
        """
        # Autenticar usuário
        client.force_login(usuario_teste)
        session = client.session
        session['usuario_id'] = usuario_teste.id
        session.save()

        url = reverse('marcar_compra', args=[pedido_com_itens.id, 99999])

        # Fazer requisição HTMX
        response = client.post(url, HTTP_HX_REQUEST='true')

        # Assert
        assert response.status_code == 400
        assert 'não encontrado' in response.content.decode().lower()

    def test_progresso_nao_muda_ao_marcar_para_compra(self, client, usuario_teste, pedido_com_itens):
        """
        Testa que o progresso do pedido não muda ao marcar item para compra.

        Given: Um pedido com progresso inicial
        When: Item é marcado para compra
        Then: Progresso permanece inalterado (itens em compra não contam como separados)
        """
        # Autenticar usuário
        client.force_login(usuario_teste)
        session = client.session
        session['usuario_id'] = usuario_teste.id
        session.save()

        # Marcar primeiro item como separado
        primeiro_item = pedido_com_itens.itens.first()
        primeiro_item.separado = True
        primeiro_item.quantidade_separada = primeiro_item.quantidade_solicitada
        primeiro_item.separado_por = usuario_teste
        primeiro_item.save()

        # Contar itens separados antes
        itens_separados_antes = pedido_com_itens.itens.filter(separado=True).count()
        assert itens_separados_antes == 1  # Apenas o primeiro

        # Marcar segundo item para compra
        segundo_item = pedido_com_itens.itens.all()[1]
        url = reverse('marcar_compra', args=[pedido_com_itens.id, segundo_item.id])

        response = client.post(url, HTTP_HX_REQUEST='true')

        # Assert
        assert response.status_code == 200

        # Contar itens separados depois - deve continuar 1
        itens_separados_depois = pedido_com_itens.itens.filter(separado=True).count()
        assert itens_separados_depois == 1  # Continua 1 (item em compra não conta)

    def test_badge_laranja_presente_no_html_retornado(self, client, usuario_teste, pedido_com_itens):
        """
        Testa que o badge laranja "Aguardando Compra" está presente no HTML.

        Given: Item marcado para compra
        When: View retorna HTML
        Then: Badge laranja com "📦 Aguardando Compra" está presente
        """
        # Autenticar usuário
        client.force_login(usuario_teste)
        session = client.session
        session['usuario_id'] = usuario_teste.id
        session.save()

        item = pedido_com_itens.itens.first()
        url = reverse('marcar_compra', args=[pedido_com_itens.id, item.id])

        # Fazer requisição HTMX
        response = client.post(url, HTTP_HX_REQUEST='true')

        # Assert
        html = response.content.decode()
        assert response.status_code == 200
        assert 'bg-orange' in html or 'orange' in html
        assert 'Aguardando Compra' in html
        assert '📦' in html  # Emoji do pacote

    def test_informacoes_usuario_e_timestamp_presentes_no_html(self, client, usuario_teste, pedido_com_itens):
        """
        Testa que nome do usuário e timestamp aparecem no HTML.

        Given: Item marcado para compra por usuário específico
        When: View retorna HTML
        Then: Nome do usuário e data estão presentes
        """
        # Autenticar usuário
        client.force_login(usuario_teste)
        session = client.session
        session['usuario_id'] = usuario_teste.id
        session.save()

        item = pedido_com_itens.itens.first()
        url = reverse('marcar_compra', args=[pedido_com_itens.id, item.id])

        # Fazer requisição HTMX
        response = client.post(url, HTTP_HX_REQUEST='true')

        # Assert
        html = response.content.decode()
        assert response.status_code == 200
        assert usuario_teste.nome in html
        assert 'Enviado para compra' in html or 'enviado para compra' in html

    def test_usuario_nao_autenticado_retorna_redirect(self, client, pedido_com_itens):
        """
        Testa que usuário não autenticado é redirecionado.

        Given: Nenhum usuário autenticado
        When: Tentativa de marcar item para compra
        Then: Retorna redirect para login
        """
        item = pedido_com_itens.itens.first()
        url = reverse('marcar_compra', args=[pedido_com_itens.id, item.id])

        # Fazer requisição sem autenticação
        response = client.post(url, HTTP_HX_REQUEST='true')

        # Assert
        assert response.status_code == 302  # Redirect
        assert '/login/' in response.url
