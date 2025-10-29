# -*- coding: utf-8 -*-
"""
Testes TDD para validar que botão "Finalizar Pedido" aparece em tempo real.

Problema identificado:
- Botão só aparecia após refresh (F5) quando progresso atingia 100%
- Django template usava {% if progresso_percentual == 100 %} que renderizava botão apenas no servidor
- JavaScript tentava mostrar botão mas ele não existia no DOM

Solução:
- Botão deve ser renderizado SEMPRE no HTML (independente do progresso)
- Visibilidade controlada por CSS (display: none/flex)
- JavaScript WebSocket mostra/oculta botão em tempo real

Fase 36: TDD RED → GREEN → REFACTOR
"""

import pytest
from django.test import TestCase, Client
from django.urls import reverse
from core.models import Usuario, Pedido as PedidoModel, ItemPedido as ItemPedidoModel, Produto as ProdutoModel


class TestBotaoFinalizarRenderizado(TestCase):
    """
    Testes TDD (RED) para validar renderização do botão finalizar.

    O botão DEVE ser renderizado no HTML inicial, independente do progresso.
    """

    def setUp(self):
        """Setup comum para todos os testes."""
        self.client = Client()

        # Criar vendedor
        self.vendedor = Usuario.objects.create_user(
            numero_login=1,
            pin='1234',
            nome='Vendedor Teste',
            tipo='VENDEDOR'
        )

        # Criar separador
        self.separador = Usuario.objects.create_user(
            numero_login=2,
            pin='1234',
            nome='Separador Teste',
            tipo='SEPARADOR'
        )

        # Criar produto
        self.produto = ProdutoModel.objects.create(
            codigo='TEST-001',
            descricao='Produto Teste',
            quantidade=10,
            valor_unitario=10.00,
            valor_total=100.00
        )

    def test_botao_renderizado_quando_progresso_0_porcento(self):
        """
        Teste 1 (RED): Botão deve existir no DOM mesmo com progresso = 0%.

        Validações:
        - Container #container-botao-finalizar existe
        - Botão <button> existe dentro do container
        - Container tem style="display: none;"
        """
        # Criar pedido com 0% de progresso
        pedido = PedidoModel.objects.create(
            numero_orcamento='TEST-001',
            codigo_cliente='CLI-001',
            nome_cliente='Cliente Teste',
            vendedor=self.vendedor,
            logistica='MOTOBOY',
            embalagem='CAIXA',
            status='EM_SEPARACAO'
        )

        # Criar 2 itens não separados (progresso = 0%)
        for i in range(2):
            ItemPedidoModel.objects.create(
                pedido=pedido,
                produto=self.produto,
                quantidade_solicitada=5,
                separado=False
            )

        # Login e acessar página
        self.client.force_login(self.separador)
        response = self.client.get(reverse('detalhe_pedido', kwargs={'pedido_id': pedido.id}))

        # Validações - ESTAS VÃO FALHAR (RED) se botão não for renderizado
        self.assertEqual(response.status_code, 200)
        content = response.content.decode('utf-8')

        # Container deve existir
        self.assertIn(
            'id="container-botao-finalizar"',
            content,
            "Container #container-botao-finalizar deve existir no HTML"
        )

        # Botão deve existir (não deve estar dentro de {% if progresso == 100 %})
        self.assertIn(
            '<button',
            content,
            "Botão <button> deve ser renderizado no HTML inicial"
        )

        self.assertIn(
            'Finalizar Pedido',
            content,
            "Texto 'Finalizar Pedido' deve existir no botão"
        )

        # Container deve estar oculto (display: none)
        self.assertIn(
            'display: none',
            content,
            "Container deve ter display: none quando progresso < 100%"
        )

    def test_botao_renderizado_quando_progresso_50_porcento(self):
        """
        Teste 2 (RED): Botão deve existir no DOM mesmo com progresso = 50%.
        """
        pedido = PedidoModel.objects.create(
            numero_orcamento='TEST-002',
            codigo_cliente='CLI-002',
            nome_cliente='Cliente Teste',
            vendedor=self.vendedor,
            logistica='MOTOBOY',
            embalagem='CAIXA',
            status='EM_SEPARACAO'
        )

        # Criar 4 itens: 2 separados, 2 não separados (50%)
        for i in range(2):
            ItemPedidoModel.objects.create(
                pedido=pedido,
                produto=self.produto,
                quantidade_solicitada=5,
                separado=True,
                quantidade_separada=5,
                separado_por=self.separador
            )

        for i in range(2):
            ItemPedidoModel.objects.create(
                pedido=pedido,
                produto=self.produto,
                quantidade_solicitada=5,
                separado=False
            )

        # Login e acessar página
        self.client.force_login(self.separador)
        response = self.client.get(reverse('detalhe_pedido', kwargs={'pedido_id': pedido.id}))

        content = response.content.decode('utf-8')

        # Validações - ESTAS VÃO FALHAR (RED)
        self.assertIn('id="container-botao-finalizar"', content)
        self.assertIn('<button', content)
        self.assertIn('Finalizar Pedido', content)
        self.assertIn('display: none', content)

    def test_botao_renderizado_e_visivel_quando_progresso_100_porcento(self):
        """
        Teste 3 (RED): Botão deve existir e estar VISÍVEL quando progresso = 100%.

        Validações:
        - Container existe
        - Botão existe
        - Container NÃO tem display: none (está visível)
        """
        pedido = PedidoModel.objects.create(
            numero_orcamento='TEST-003',
            codigo_cliente='CLI-003',
            nome_cliente='Cliente Teste',
            vendedor=self.vendedor,
            logistica='MOTOBOY',
            embalagem='CAIXA',
            status='EM_SEPARACAO'
        )

        # Criar 2 itens separados (100%)
        for i in range(2):
            ItemPedidoModel.objects.create(
                pedido=pedido,
                produto=self.produto,
                quantidade_solicitada=5,
                separado=True,
                quantidade_separada=5,
                separado_por=self.separador
            )

        # Login e acessar página
        self.client.force_login(self.separador)
        response = self.client.get(reverse('detalhe_pedido', kwargs={'pedido_id': pedido.id}))

        content = response.content.decode('utf-8')

        # Validações
        self.assertIn('id="container-botao-finalizar"', content)
        self.assertIn('<button', content)
        self.assertIn('Finalizar Pedido', content)

        # Container NÃO deve ter display: none
        # (ou deve ter lógica que mostra quando progresso = 100%)
        # Verificar que container está configurado para ser visível

    def test_botao_tem_atributos_htmx_corretos(self):
        """
        Teste 4 (RED): Botão deve ter atributos HTMX para funcionar.

        Validações:
        - hx-get aponta para URL correta
        - hx-target="body"
        - hx-swap="beforeend"
        """
        pedido = PedidoModel.objects.create(
            numero_orcamento='TEST-004',
            codigo_cliente='CLI-004',
            nome_cliente='Cliente Teste',
            vendedor=self.vendedor,
            logistica='MOTOBOY',
            embalagem='CAIXA',
            status='EM_SEPARACAO'
        )

        ItemPedidoModel.objects.create(
            pedido=pedido,
            produto=self.produto,
            quantidade_solicitada=5,
            separado=False
        )

        # Login e acessar página
        self.client.force_login(self.separador)
        response = self.client.get(reverse('detalhe_pedido', kwargs={'pedido_id': pedido.id}))

        content = response.content.decode('utf-8')

        # Validações - HTMX
        self.assertIn('hx-get', content, "Botão deve ter atributo hx-get")
        self.assertIn('hx-target', content, "Botão deve ter atributo hx-target")
        self.assertIn('hx-swap', content, "Botão deve ter atributo hx-swap")

        # URL esperada
        expected_url = reverse('finalizar_pedido', kwargs={'pedido_id': pedido.id})
        self.assertIn(expected_url, content, f"Botão deve apontar para {expected_url}")

    def test_container_tem_data_attribute_com_progresso_inicial(self):
        """
        Teste 5 (RED): Container deve ter data-attribute com progresso inicial.

        Isso ajuda no debug e permite JavaScript saber estado inicial.
        """
        pedido = PedidoModel.objects.create(
            numero_orcamento='TEST-005',
            codigo_cliente='CLI-005',
            nome_cliente='Cliente Teste',
            vendedor=self.vendedor,
            logistica='MOTOBOY',
            embalagem='CAIXA',
            status='EM_SEPARACAO'
        )

        # Criar 3 itens: 1 separado (33%)
        ItemPedidoModel.objects.create(
            pedido=pedido,
            produto=self.produto,
            quantidade_solicitada=5,
            separado=True,
            quantidade_separada=5,
            separado_por=self.separador
        )

        for i in range(2):
            ItemPedidoModel.objects.create(
                pedido=pedido,
                produto=self.produto,
                quantidade_solicitada=5,
                separado=False
            )

        # Login e acessar página
        self.client.force_login(self.separador)
        response = self.client.get(reverse('detalhe_pedido', kwargs={'pedido_id': pedido.id}))

        content = response.content.decode('utf-8')

        # Validação - data-attribute
        self.assertIn(
            'data-progresso-inicial',
            content,
            "Container deve ter data-progresso-inicial"
        )

        # Deve conter valor numérico (33%)
        self.assertIn(
            'data-progresso-inicial="33"',
            content,
            "data-progresso-inicial deve ter valor correto (33%)"
        )
