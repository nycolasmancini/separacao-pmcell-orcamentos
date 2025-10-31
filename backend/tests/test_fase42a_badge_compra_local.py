# -*- coding: utf-8 -*-
"""
Fase 42a - Testes Backend: Badge Compra Local
===============================================

Objetivo: Validar que MarcarCompraView retorna partial específico
          com badge atualizado que aparece localmente (sem reload).

Testes:
1. test_marcar_compra_retorna_partial_com_badge
2. test_badge_inclui_enviado_por
3. test_badge_inclui_timestamp_formatado
4. test_badge_css_classe_correta_aguardando
5. test_htmx_target_badge_correto
6. test_websocket_broadcast_outros_devices

Total: 6 testes backend
"""

import pytest
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from unittest.mock import patch, MagicMock
from bs4 import BeautifulSoup

from core.models import Pedido, ItemPedido, Produto


User = get_user_model()


@pytest.mark.django_db
class TestFase42aBadgeCompraLocal(TestCase):
    """
    Suite de testes para badge local de compra.

    Valida que ao clicar em "Enviar para Compra", o badge
    aparece imediatamente no dispositivo local sem reload.
    """

    def setUp(self):
        """Configurar dados de teste."""
        # Usuário autenticado
        self.user = User.objects.create_user(
            numero_login=1001,
            pin='1234',
            nome='Separador Teste',
            tipo='SEPARADOR'
        )

        # Vendedor (também é um Usuario)
        self.vendedor = User.objects.create_user(
            numero_login=2001,
            pin='5678',
            nome='Vendedor Teste',
            tipo='VENDEDOR'
        )

        # Produto
        self.produto = Produto.objects.create(
            codigo='PROD001',
            descricao='Produto Teste Badge',
            quantidade=10,
            valor_unitario=100.00,
            valor_total=1000.00
        )

        # Pedido
        self.pedido = Pedido.objects.create(
            numero_orcamento='ORD-BADGE-001',
            nome_cliente='Cliente Badge Teste',
            codigo_cliente='CLI001',
            vendedor=self.vendedor,
            data=timezone.now().date()
        )

        # Item do pedido (NÃO separado e NÃO em compra - faltante)
        self.item = ItemPedido.objects.create(
            pedido=self.pedido,
            produto=self.produto,
            quantidade_solicitada=5,
            quantidade_separada=0,  # Não separado ainda
            separado=False,  # CRUCIAL: item faltante que precisa ser comprado
            separado_por=None,
            separado_em=None,
            em_compra=False  # CRUCIAL: não está em compra ainda
        )

        # Client autenticado
        self.client = Client()
        self.client.force_login(self.user)

    def test_marcar_compra_retorna_partial_com_badge(self):
        """
        Teste 1: MarcarCompraView retorna partial HTML com badge visível.

        Valida:
        - Response 200 OK
        - HTML contém badge com id correto
        - Badge contém texto "Aguardando Compra"
        - Badge tem ícone de relógio
        """
        url = reverse('marcar_compra', kwargs={'pedido_id': self.pedido.id, 'item_id': self.item.id})

        response = self.client.post(url, HTTP_X_REQUESTED_WITH='XMLHttpRequest')

        # Validar response
        self.assertEqual(response.status_code, 200)

        # Parse HTML response
        soup = BeautifulSoup(response.content, 'html.parser')

        # Encontrar badge
        badge = soup.find('span', id=f'badge-{self.item.id}')

        # Validações
        self.assertIsNotNone(badge, "Badge deve existir no HTML retornado")
        self.assertIn('Aguardando Compra', badge.text, "Badge deve mostrar 'Aguardando Compra'")

        # Verificar ícone de relógio (SVG)
        svg_icon = badge.find('svg')
        self.assertIsNotNone(svg_icon, "Badge deve ter ícone SVG")

    def test_badge_inclui_enviado_por(self):
        """
        Teste 2: Badge deve incluir informação de quem enviou para compra.

        Valida que o partial contém metadados do usuário que
        marcou o item para compra (mesmo que não visível no badge).
        """
        url = reverse('marcar_compra', kwargs={'pedido_id': self.pedido.id, 'item_id': self.item.id})

        response = self.client.post(url, HTTP_X_REQUESTED_WITH='XMLHttpRequest')

        # Parse HTML
        soup = BeautifulSoup(response.content, 'html.parser')

        # Verificar que HTML contém nome do usuário
        html_text = soup.get_text()
        self.assertIn(self.user.nome, html_text,
                     "HTML deve conter nome do usuário que enviou")

        # Verificar no banco de dados
        self.item.refresh_from_db()
        self.assertEqual(self.item.enviado_para_compra_por, self.user)

    def test_badge_inclui_timestamp_formatado(self):
        """
        Teste 3: Badge deve incluir timestamp formatado de quando foi enviado.

        Valida formato brasileiro: dd/mm/YYYY HH:MM
        """
        from django.utils import timezone as tz
        import pytz

        url = reverse('marcar_compra', kwargs={'pedido_id': self.pedido.id, 'item_id': self.item.id})

        response = self.client.post(url, HTTP_X_REQUESTED_WITH='XMLHttpRequest')

        # Verificar no banco
        self.item.refresh_from_db()
        self.assertIsNotNone(self.item.enviado_para_compra_em)

        # Verificar formato no HTML
        soup = BeautifulSoup(response.content, 'html.parser')
        html_text = soup.get_text()

        # Timestamp deve estar no formato brasileiro com timezone local
        local_tz = pytz.timezone('America/Sao_Paulo')
        local_time = self.item.enviado_para_compra_em.astimezone(local_tz)
        expected_timestamp = local_time.strftime('%d/%m/%Y %H:%M')
        self.assertIn(expected_timestamp, html_text,
                     "HTML deve conter timestamp formatado (dd/mm/YYYY HH:MM)")

    def test_badge_css_classe_correta_aguardando(self):
        """
        Teste 4: Badge deve ter classes CSS corretas para estado "Aguardando Compra".

        Valida:
        - bg-orange-100 (fundo laranja claro)
        - text-orange-800 (texto laranja escuro)
        """
        url = reverse('marcar_compra', kwargs={'pedido_id': self.pedido.id, 'item_id': self.item.id})

        response = self.client.post(url, HTTP_X_REQUESTED_WITH='XMLHttpRequest')

        # Parse HTML
        soup = BeautifulSoup(response.content, 'html.parser')
        badge = soup.find('span', id=f'badge-{self.item.id}')

        # Validar classes CSS
        self.assertIsNotNone(badge)
        badge_classes = badge.get('class', [])

        self.assertIn('bg-orange-100', badge_classes,
                     "Badge deve ter fundo laranja claro")
        self.assertIn('text-orange-800', badge_classes,
                     "Badge deve ter texto laranja escuro")

    def test_htmx_target_badge_correto(self):
        """
        Teste 5: Response deve ser compatível com HTMX swap do badge.

        Valida que o HTML retornado pode ser usado diretamente
        pelo HTMX para substituir o badge existente.
        """
        url = reverse('marcar_compra', kwargs={'pedido_id': self.pedido.id, 'item_id': self.item.id})

        response = self.client.post(url, HTTP_X_REQUESTED_WITH='XMLHttpRequest')

        # Parse HTML
        soup = BeautifulSoup(response.content, 'html.parser')

        # Badge deve ter ID único para HTMX targeting
        badge = soup.find('span', id=f'badge-{self.item.id}')
        self.assertIsNotNone(badge)

        # Badge ID deve permitir swap via HTMX
        # HTMX usa hx-target="#badge-{id}" e hx-swap="outerHTML"
        badge_id = badge.get('id')
        self.assertEqual(badge_id, f'badge-{self.item.id}')

    @patch('core.presentation.web.views.get_channel_layer')
    def test_websocket_broadcast_outros_devices(self, mock_channel_layer):
        """
        Teste 6: WebSocket deve fazer broadcast para outros dispositivos.

        Valida que quando item é marcado para compra:
        - WebSocket emite evento 'item_marcado_compra'
        - Evento contém dados completos do item
        - Outros dispositivos recebem atualização
        """
        # Mock do channel layer
        mock_layer = MagicMock()
        mock_channel_layer.return_value = mock_layer

        url = reverse('marcar_compra', kwargs={'pedido_id': self.pedido.id, 'item_id': self.item.id})

        response = self.client.post(url, HTTP_X_REQUESTED_WITH='XMLHttpRequest')

        # Validar response OK
        self.assertEqual(response.status_code, 200)

        # Verificar que group_send foi chamado
        mock_layer.group_send.assert_called_once()

        # Extrair argumentos da chamada
        call_args = mock_layer.group_send.call_args
        group_name = call_args[0][0]
        event_data = call_args[0][1]

        # Validar grupo correto
        self.assertEqual(group_name, 'dashboard')

        # Validar evento
        self.assertEqual(event_data['type'], 'item_marcado_compra')
        self.assertEqual(event_data['item_id'], self.item.id)
        self.assertEqual(event_data['pedido_id'], self.pedido.id)
        self.assertEqual(event_data['numero_orcamento'], self.pedido.numero_orcamento)
        self.assertEqual(event_data['nome_cliente'], self.pedido.nome_cliente)
        self.assertEqual(event_data['produto_codigo'], self.produto.codigo)
        self.assertEqual(event_data['produto_descricao'], self.produto.descricao)
        self.assertEqual(event_data['enviado_por'], self.user.nome)

        # Verificar timestamp formatado
        self.assertIn('enviado_em', event_data)
        self.assertIsNotNone(event_data['enviado_em'])


# Teste adicional: Verificar estado inicial (antes de marcar)
@pytest.mark.django_db
class TestEstadoInicialBadge(TestCase):
    """
    Testes auxiliares para validar estado inicial do badge.
    """

    def setUp(self):
        """Configurar dados de teste."""
        self.user = User.objects.create_user(
            numero_login=1002,
            pin='9999',
            nome='Separador Inicial',
            tipo='SEPARADOR'
        )

        self.vendedor = User.objects.create_user(
            numero_login=2002,
            pin='8888',
            nome='Vendedor Inicial',
            tipo='VENDEDOR'
        )

        self.produto = Produto.objects.create(
            codigo='PROD002',
            descricao='Produto Inicial',
            quantidade=5,
            valor_unitario=50.00,
            valor_total=250.00
        )

        self.pedido = Pedido.objects.create(
            numero_orcamento='ORD-INICIAL-001',
            nome_cliente='Cliente Inicial',
            codigo_cliente='CLI002',
            vendedor=self.vendedor,
            data=timezone.now().date()
        )

        self.item = ItemPedido.objects.create(
            pedido=self.pedido,
            produto=self.produto,
            quantidade_solicitada=3,
            quantidade_separada=0,  # Não separado - item faltante
            separado=False,  # Não separado
            separado_por=None,
            separado_em=None,
            em_compra=False
        )

    def test_item_inicial_nao_tem_badge_compra(self):
        """
        Validar que item recém-separado NÃO tem badge de compra.

        Estado inicial esperado:
        - em_compra = False
        - enviado_para_compra_por = None
        - enviado_para_compra_em = None
        """
        self.assertFalse(self.item.em_compra)
        self.assertIsNone(self.item.enviado_para_compra_por)
        self.assertIsNone(self.item.enviado_para_compra_em)
