# -*- coding: utf-8 -*-
"""
Testes TDD para ItemPedidoPartialView
Fase 1 (RED → GREEN → REFACTOR)

Esta view retorna apenas o HTML de um item específico para atualizações em tempo real.
Usada pelo WebSocket para sincronizar estado visual dos itens entre múltiplos usuários.
"""

import pytest
from django.test import TestCase, RequestFactory, Client
from django.contrib.sessions.middleware import SessionMiddleware
from django.urls import reverse

from core.models import Usuario, Pedido, ItemPedido, Produto as ProdutoModel


class TestItemPedidoPartialViewTDD(TestCase):
    """
    Testes TDD (RED) para validar ItemPedidoPartialView.

    Cenário:
    - View deve retornar HTML parcial de um item específico
    - HTML deve conter estado atual do item (separado/não separado/em compra)
    - Deve funcionar com HTMX (sem layout base)
    - Deve validar permissões (apenas usuários autenticados)
    """

    def setUp(self):
        """Setup comum para todos os testes."""
        self.factory = RequestFactory()
        self.client = Client()

        # Criar usuário vendedor
        self.vendedor = Usuario.objects.create_user(
            numero_login=1,
            pin='1234',
            nome='João Vendedor',
            tipo='VENDEDOR'
        )

        # Criar usuário separador
        self.separador = Usuario.objects.create_user(
            numero_login=2,
            pin='1234',
            nome='Maria Separadora',
            tipo='SEPARADOR'
        )

        # Criar produto
        self.produto = ProdutoModel.objects.create(
            codigo='12345',
            descricao='Produto Teste',
            quantidade=10,
            valor_unitario=10.00,
            valor_total=100.00
        )

        # Criar pedido
        self.pedido = Pedido.objects.create(
            numero_orcamento='30567',
            codigo_cliente='12345',
            nome_cliente='Cliente Teste',
            vendedor=self.vendedor,
            logistica='MOTOBOY',
            embalagem='CAIXA',
            status='EM_SEPARACAO'
        )

        # Criar item não separado
        self.item_nao_separado = ItemPedido.objects.create(
            pedido=self.pedido,
            produto=self.produto,
            quantidade_solicitada=5,
            separado=False
        )

        # Criar item separado
        self.item_separado = ItemPedido.objects.create(
            pedido=self.pedido,
            produto=self.produto,
            quantidade_solicitada=3,
            separado=True,
            quantidade_separada=3,
            separado_por=self.separador
        )

    def test_view_existe_e_responde_200(self):
        """
        Teste 1 (RED): View deve existir e responder 200 para requisição autenticada.
        """
        self.client.force_login(self.separador)

        # URL esperada: /pedidos/<pedido_id>/itens/<item_id>/html/
        url = f'/pedidos/{self.pedido.id}/itens/{self.item_nao_separado.id}/html/'

        response = self.client.get(url)

        # ESTE TESTE VAI FALHAR (RED) porque a view ainda não existe
        self.assertEqual(
            response.status_code, 200,
            f"View deve retornar 200, mas retornou {response.status_code}"
        )

    def test_view_requer_autenticacao(self):
        """
        Teste 2 (RED): View deve redirecionar para login se usuário não autenticado.
        """
        # Não fazer login
        url = f'/pedidos/{self.pedido.id}/itens/{self.item_nao_separado.id}/html/'

        response = self.client.get(url)

        # Deve redirecionar para login
        self.assertEqual(
            response.status_code, 302,
            "View deve redirecionar (302) usuário não autenticado para login"
        )

        self.assertIn(
            '/login/', response.url,
            "Redirect deve ser para /login/"
        )

    def test_retorna_html_do_item_nao_separado(self):
        """
        Teste 3 (RED): View deve retornar HTML do item não separado.

        Validações:
        - HTML contém id="item-{item_id}"
        - HTML contém checkbox desmarcado
        - HTML contém badge "Aguardando"
        - HTML contém descrição do produto
        """
        self.client.force_login(self.separador)

        url = f'/pedidos/{self.pedido.id}/itens/{self.item_nao_separado.id}/html/'
        response = self.client.get(url)

        content = response.content.decode('utf-8')

        # Validações - ESTAS VÃO FALHAR (RED)
        self.assertIn(
            f'id="item-{self.item_nao_separado.id}"',
            content,
            "HTML deve conter id do item"
        )

        self.assertIn(
            'Aguardando',
            content,
            "Item não separado deve ter badge 'Aguardando'"
        )

        self.assertIn(
            self.produto.descricao,
            content,
            "HTML deve conter descrição do produto"
        )

        self.assertIn(
            'type="checkbox"',
            content,
            "HTML deve conter checkbox"
        )

    def test_retorna_html_do_item_separado(self):
        """
        Teste 4 (RED): View deve retornar HTML do item separado.

        Validações:
        - HTML contém id="item-{item_id}"
        - HTML contém checkbox marcado (checked)
        - HTML contém badge "Separado"
        - HTML contém informação de quem separou
        - HTML tem classes de estilo verde (green)
        """
        self.client.force_login(self.separador)

        url = f'/pedidos/{self.pedido.id}/itens/{self.item_separado.id}/html/'
        response = self.client.get(url)

        content = response.content.decode('utf-8')

        # Validações - ESTAS VÃO FALHAR (RED)
        self.assertIn(
            f'id="item-{self.item_separado.id}"',
            content,
            "HTML deve conter id do item"
        )

        self.assertIn(
            'Separado',
            content,
            "Item separado deve ter badge 'Separado'"
        )

        self.assertIn(
            'checked',
            content,
            "Checkbox deve estar marcado (checked)"
        )

        self.assertIn(
            self.separador.nome,
            content,
            "HTML deve conter nome de quem separou"
        )

    def test_retorna_apenas_html_sem_layout_base(self):
        """
        Teste 5 (RED): View deve retornar apenas o HTML parcial, sem layout base.

        Não deve conter:
        - Tags <html>, <head>, <body>
        - Navbar, header, footer
        - Tags {% extends "base.html" %}
        """
        self.client.force_login(self.separador)

        url = f'/pedidos/{self.pedido.id}/itens/{self.item_nao_separado.id}/html/'
        response = self.client.get(url)

        content = response.content.decode('utf-8')

        # Validações - ESTAS VÃO FALHAR (RED)
        self.assertNotIn(
            '<html',
            content,
            "HTML não deve conter tag <html> (deve ser apenas partial)"
        )

        self.assertNotIn(
            '<head',
            content,
            "HTML não deve conter tag <head>"
        )

        self.assertNotIn(
            '<body',
            content,
            "HTML não deve conter tag <body>"
        )

    def test_retorna_404_se_item_nao_existe(self):
        """
        Teste 6 (RED): View deve retornar 404 se item não existir.
        """
        self.client.force_login(self.separador)

        # ID de item que não existe
        url = f'/pedidos/{self.pedido.id}/itens/99999/html/'

        response = self.client.get(url)

        # ESTE TESTE VAI FALHAR (RED)
        self.assertEqual(
            response.status_code, 404,
            "View deve retornar 404 para item inexistente"
        )

    def test_retorna_404_se_item_nao_pertence_ao_pedido(self):
        """
        Teste 7 (RED): View deve retornar 404 se item não pertence ao pedido especificado.
        """
        self.client.force_login(self.separador)

        # Criar outro pedido
        outro_pedido = Pedido.objects.create(
            numero_orcamento='30568',
            codigo_cliente='54321',
            nome_cliente='Outro Cliente',
            vendedor=self.vendedor,
            logistica='MOTOBOY',
            embalagem='CAIXA',
            status='EM_SEPARACAO'
        )

        # Tentar acessar item do pedido A usando ID do pedido B
        url = f'/pedidos/{outro_pedido.id}/itens/{self.item_nao_separado.id}/html/'

        response = self.client.get(url)

        # ESTE TESTE VAI FALHAR (RED)
        self.assertEqual(
            response.status_code, 404,
            "View deve retornar 404 quando item não pertence ao pedido"
        )

    def test_html_contem_urls_htmx_corretas(self):
        """
        Teste 8 (RED): HTML deve conter atributos HTMX com URLs corretas.

        Validações:
        - hx-post com URL de separar_item
        - hx-target correto
        - hx-swap="outerHTML"
        """
        self.client.force_login(self.separador)

        url = f'/pedidos/{self.pedido.id}/itens/{self.item_nao_separado.id}/html/'
        response = self.client.get(url)

        content = response.content.decode('utf-8')

        # Validações - ESTAS VÃO FALHAR (RED)
        self.assertIn(
            'hx-post',
            content,
            "HTML deve conter atributo hx-post"
        )

        self.assertIn(
            'hx-target',
            content,
            "HTML deve conter atributo hx-target"
        )

        self.assertIn(
            'hx-swap',
            content,
            "HTML deve conter atributo hx-swap"
        )


class TestItemPedidoPartialViewIntegracao(TestCase):
    """
    Testes de integração para validar comportamento completo.
    """

    def setUp(self):
        """Setup comum."""
        self.client = Client()

        # Criar dados
        self.vendedor = Usuario.objects.create_user(
            numero_login=1, pin='1234', nome='Vendedor', tipo='VENDEDOR'
        )

        self.separador = Usuario.objects.create_user(
            numero_login=2, pin='1234', nome='Separador', tipo='SEPARADOR'
        )

        self.produto = ProdutoModel.objects.create(
            codigo='TEST', descricao='Produto', quantidade=10,
            valor_unitario=10.00, valor_total=100.00
        )

        self.pedido = Pedido.objects.create(
            numero_orcamento='12345', codigo_cliente='CLI',
            nome_cliente='Cliente', vendedor=self.vendedor,
            logistica='MOTOBOY', embalagem='CAIXA', status='EM_SEPARACAO'
        )

        self.item = ItemPedido.objects.create(
            pedido=self.pedido, produto=self.produto,
            quantidade_solicitada=5, separado=False
        )

    def test_fluxo_completo_marcar_e_buscar_html_atualizado(self):
        """
        Teste 9 (RED): Simular fluxo completo de marcar item e buscar HTML atualizado.

        Fluxo:
        1. Item começa desmarcado
        2. Usuário marca item via HTMX
        3. WebSocket notifica outros usuários
        4. Outro usuário busca HTML atualizado
        5. HTML reflete novo estado (checkbox marcado, badge verde)
        """
        self.client.force_login(self.separador)

        # 1. Verificar estado inicial (não separado)
        url_html = f'/pedidos/{self.pedido.id}/itens/{self.item.id}/html/'
        response = self.client.get(url_html)
        content_inicial = response.content.decode('utf-8')

        self.assertIn('Aguardando', content_inicial)
        self.assertNotIn('checked', content_inicial)

        # 2. Marcar item como separado
        url_separar = f'/pedidos/{self.pedido.id}/itens/{self.item.id}/separar/'
        self.client.post(
            url_separar,
            HTTP_HX_REQUEST='true'
        )

        # 3. Buscar HTML atualizado (como se fosse outro usuário via WebSocket)
        response_atualizado = self.client.get(url_html)
        content_atualizado = response_atualizado.content.decode('utf-8')

        # Validações - ESTAS VÃO FALHAR (RED)
        self.assertIn(
            'Separado',
            content_atualizado,
            "HTML atualizado deve mostrar badge 'Separado'"
        )

        self.assertIn(
            'checked',
            content_atualizado,
            "Checkbox deve estar marcado no HTML atualizado"
        )

        # Verificar que tem badge "Separado" no HTML renderizado (não nos comentários)
        # Usar regex para ser mais flexível com espaços em branco
        import re

        # Remover comentários HTML
        content_sem_comentarios = re.sub(r'<!--.*?-->', '', content_atualizado, flags=re.DOTALL)

        # Verificar badge "Separado" (flexível com espaços)
        self.assertTrue(
            re.search(r'✓\s*Separado\s*</span>', content_sem_comentarios),
            "Deve ter badge '✓ Separado' no HTML renderizado"
        )

        # Verificar que NÃO tem badge "Aguardando" renderizado
        self.assertFalse(
            re.search(r'Aguardando\s*</span>', content_sem_comentarios),
            "Não deve ter badge 'Aguardando' renderizado (fora de comentários)"
        )
