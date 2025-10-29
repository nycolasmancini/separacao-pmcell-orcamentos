# -*- coding: utf-8 -*-
"""
Testes unitários para o comportamento de desmarcar item com animações.

Fase 37 - Correção de Bug: Quando um item separado é desmarcado, ele deve
fazer fade out e aparecer na seção "Itens Não Separados" SEM NECESSIDADE DE REFRESH.

Estes testes validam que:
1. Backend retorna resposta correta ao desmarcar
2. Header X-Item-Id é enviado
3. Endpoint GET para buscar partial fresco funciona
4. HTML retornado está correto (borda cinza, não separado)
"""

import pytest
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from core.models import Pedido, ItemPedido, Produto


User = get_user_model()


class TestDesmarcarItemAnimations(TestCase):
    """
    Testes unitários para validar correção do bug de desmarcar item.
    """

    def setUp(self):
        """Setup de dados de teste."""
        # Criar usuários
        self.vendedor = User.objects.create_user(
            numero_login=9001,
            nome="Vendedor Teste",
            tipo="VENDEDOR",
            pin="9999"
        )

        self.separador = User.objects.create_user(
            numero_login=1001,
            nome="Separador Teste",
            tipo="SEPARADOR",
            pin="1234"
        )

        # Criar pedido
        self.pedido = Pedido.objects.create(
            numero_orcamento="TEST-DESMARCAR-001",
            codigo_cliente="CLI001",
            nome_cliente="Cliente Teste Desmarcar",
            vendedor=self.vendedor,
            data="28/10/2025",
            status="EM_SEPARACAO"
        )

        # Criar produto e item SEPARADO
        self.produto = Produto.objects.create(
            codigo="PROD001",
            descricao="Produto Teste Desmarcar",
            quantidade=10,
            valor_unitario=100.0,
            valor_total=1000.0
        )

        self.item = ItemPedido.objects.create(
            pedido=self.pedido,
            produto=self.produto,
            quantidade_solicitada=5,
            separado=True,  # JÁ SEPARADO
            separado_por=self.separador
        )

        # Client Django para testes
        self.client = Client()
        self.client.force_login(self.separador)

    def test_desmarcar_item_retorna_confirmacao_sem_html(self):
        """
        Teste: Ao desmarcar item (separado=True → False), backend deve
        retornar HTTP 200 SEM HTML, apenas headers customizados.

        Motivo: Evitar que HTMX faça swap in-place que causa bug.
        """
        # Marcar item como não separado (desmarcar)
        response = self.client.post(
            reverse('separar_item', args=[self.pedido.id, self.item.id]),
            HTTP_HX_REQUEST='true'
        )

        # Validar resposta
        assert response.status_code == 200

        # Validar que NÃO retornou HTML (body vazio ou muito pequeno)
        assert len(response.content) < 50, \
            "Backend deve retornar confirmação mínima, não HTML completo"

    def test_desmarcar_item_envia_header_item_id(self):
        """
        Teste: Backend deve enviar header X-Item-Id para JavaScript
        saber qual item movimentar.
        """
        response = self.client.post(
            reverse('separar_item', args=[self.pedido.id, self.item.id]),
            HTTP_HX_REQUEST='true'
        )

        # Validar header
        assert 'X-Item-Id' in response, "Header X-Item-Id deve estar presente"
        assert response['X-Item-Id'] == str(self.item.id)

    def test_desmarcar_item_envia_trigger_item_desmarcado(self):
        """
        Teste: Backend deve enviar HX-Trigger: itemDesmarcado para
        JavaScript interceptar e aplicar animação.
        """
        response = self.client.post(
            reverse('separar_item', args=[self.pedido.id, self.item.id]),
            HTTP_HX_REQUEST='true'
        )

        # Validar header
        assert 'HX-Trigger' in response
        assert response['HX-Trigger'] == 'itemDesmarcado'

    def test_endpoint_get_partial_existe(self):
        """
        Teste: Deve existir endpoint GET para buscar HTML fresco do item.

        URL esperada: /pedidos/<pedido_id>/itens/<item_id>/partial/
        """
        url = reverse('item_pedido_partial', args=[self.pedido.id, self.item.id])

        response = self.client.get(url, HTTP_HX_REQUEST='true')

        # Validar que endpoint existe
        assert response.status_code == 200, \
            f"Endpoint {url} deve existir e retornar 200"

    def test_endpoint_get_partial_retorna_html_correto(self):
        """
        Teste: Endpoint GET deve retornar HTML parcial do item com
        classes corretas (border-gray-200 quando não separado).
        """
        # Garantir que item NÃO está separado
        self.item.separado = False
        self.item.save()

        url = reverse('item_pedido_partial', args=[self.pedido.id, self.item.id])
        response = self.client.get(url, HTTP_HX_REQUEST='true')

        html = response.content.decode('utf-8')

        # Validar HTML
        assert 'border-gray-200' in html, \
            "Item não separado deve ter borda cinza (border-gray-200)"

        assert 'border-green-200' not in html, \
            "Item não separado NÃO deve ter borda verde"

        assert f'id="item-{self.item.id}"' in html, \
            "HTML deve ter ID correto do item"

    def test_endpoint_get_partial_retorna_html_com_separado_true(self):
        """
        Teste: Endpoint GET deve retornar HTML com borda verde quando
        item está separado.
        """
        # Garantir que item ESTÁ separado
        self.item.separado = True
        self.item.save()

        url = reverse('item_pedido_partial', args=[self.pedido.id, self.item.id])
        response = self.client.get(url, HTTP_HX_REQUEST='true')

        html = response.content.decode('utf-8')

        # Validar HTML
        assert 'border-green-200' in html, \
            "Item separado deve ter borda verde (border-green-200)"

        assert 'border-gray-200' not in html, \
            "Item separado NÃO deve ter borda cinza"

    def test_desmarcar_item_atualiza_banco_dados(self):
        """
        Teste: Desmarcar item deve persistir mudança no banco de dados.
        """
        # Estado inicial
        assert self.item.separado is True

        # Desmarcar
        self.client.post(
            reverse('separar_item', args=[self.pedido.id, self.item.id]),
            HTTP_HX_REQUEST='true'
        )

        # Recarregar do banco
        self.item.refresh_from_db()

        # Validar
        assert self.item.separado is False, \
            "Item deve estar desmarcado no banco de dados"

    def test_endpoint_partial_requer_autenticacao(self):
        """
        Teste: Endpoint GET partial deve exigir autenticação.
        """
        # Fazer logout
        self.client.logout()

        url = reverse('item_pedido_partial', args=[self.pedido.id, self.item.id])
        response = self.client.get(url)

        # Deve redirecionar para login
        assert response.status_code == 302, \
            "Endpoint deve redirecionar usuário não autenticado"

    def test_endpoint_partial_valida_pedido_existe(self):
        """
        Teste: Endpoint GET deve retornar 404 se pedido não existe.
        """
        url_fake = f'/pedidos/99999/itens/{self.item.id}/partial/'

        response = self.client.get(url_fake, HTTP_HX_REQUEST='true')

        # Deve retornar 404
        assert response.status_code == 404, \
            "Endpoint deve retornar 404 para pedido inexistente"

    def test_endpoint_partial_valida_item_existe(self):
        """
        Teste: Endpoint GET deve retornar 404 se item não existe.
        """
        url_fake = f'/pedidos/{self.pedido.id}/itens/99999/partial/'

        response = self.client.get(url_fake, HTTP_HX_REQUEST='true')

        # Deve retornar 404
        assert response.status_code == 404, \
            "Endpoint deve retornar 404 para item inexistente"
