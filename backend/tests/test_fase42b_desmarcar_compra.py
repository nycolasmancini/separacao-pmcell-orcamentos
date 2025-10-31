# -*- coding: utf-8 -*-
"""
Fase 42b - Testes Backend: Desmarcar Item de Compra
====================================================

Objetivo: Validar que DesmarcarCompraView limpa badge localmente
          E emite evento WebSocket para remover item do Painel de Compras.

Testes:
1. test_desmarcar_compra_limpa_campos
2. test_desmarcar_compra_retorna_badge_vazio
3. test_desmarcar_compra_emite_websocket
4. test_desmarcar_compra_payload_completo
5. test_desmarcar_apenas_se_estava_em_compra

Total: 5 testes backend
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
class TestFase42bDesmarcarCompra(TestCase):
    """
    Suite de testes para desmarcar item de compra.

    Valida que ao desmarcar um item:
    1. Campos são limpos no banco
    2. Badge é removido/atualizado localmente via HTMX
    3. WebSocket emite evento para outros dispositivos
    4. Painel de Compras remove o item em tempo real
    """

    def setUp(self):
        """Configurar dados de teste."""
        # Usuário autenticado (separador)
        self.user = User.objects.create_user(
            numero_login=1001,
            pin='1234',
            nome='Separador Teste',
            tipo='SEPARADOR'
        )

        # Vendedor
        self.vendedor = User.objects.create_user(
            numero_login=2001,
            pin='5678',
            nome='Vendedor Teste',
            tipo='VENDEDOR'
        )

        # Produto
        self.produto = Produto.objects.create(
            codigo='PROD001',
            descricao='Produto Teste Desmarcar',
            quantidade=10,
            valor_unitario=100.00,
            valor_total=1000.00
        )

        # Pedido
        self.pedido = Pedido.objects.create(
            numero_orcamento='ORD-DESMARCAR-001',
            nome_cliente='Cliente Desmarcar Teste',
            codigo_cliente='CLI001',
            vendedor=self.vendedor,
            data=timezone.now().date()
        )

        # Item do pedido JÁ em compra
        self.item = ItemPedido.objects.create(
            pedido=self.pedido,
            produto=self.produto,
            quantidade_solicitada=5,
            quantidade_separada=0,
            separado=False,
            separado_por=None,
            separado_em=None,
            em_compra=True,  # JÁ está em compra
            enviado_para_compra_por=self.user,
            enviado_para_compra_em=timezone.now()
        )

        # Client autenticado
        self.client = Client()
        self.client.force_login(self.user)

    def test_desmarcar_compra_limpa_campos(self):
        """
        Teste 1: Desmarcar compra deve limpar campos relacionados.

        Valida:
        - em_compra = False
        - enviado_para_compra_por = None
        - enviado_para_compra_em = None
        """
        # Verificar estado inicial
        self.assertTrue(self.item.em_compra)
        self.assertIsNotNone(self.item.enviado_para_compra_por)
        self.assertIsNotNone(self.item.enviado_para_compra_em)

        # Desmarcar compra
        url = reverse('desmarcar_compra', kwargs={'pedido_id': self.pedido.id, 'item_id': self.item.id})
        response = self.client.post(url, HTTP_X_REQUESTED_WITH='XMLHttpRequest')

        # Validar response
        self.assertEqual(response.status_code, 200)

        # Verificar banco de dados
        self.item.refresh_from_db()
        self.assertFalse(self.item.em_compra, "em_compra deve ser False")
        self.assertIsNone(self.item.enviado_para_compra_por, "enviado_para_compra_por deve ser None")
        self.assertIsNone(self.item.enviado_para_compra_em, "enviado_para_compra_em deve ser None")

    def test_desmarcar_compra_retorna_badge_vazio(self):
        """
        Teste 2: Response deve retornar badge "limpo" (sem indicador de compra).

        Valida que o HTML retornado NÃO contém:
        - Texto "Aguardando Compra"
        - Classe bg-orange-100

        E pode conter badge de estado normal do item (ex: "Faltante").
        """
        url = reverse('desmarcar_compra', kwargs={'pedido_id': self.pedido.id, 'item_id': self.item.id})
        response = self.client.post(url, HTTP_X_REQUESTED_WITH='XMLHttpRequest')

        # Parse HTML
        soup = BeautifulSoup(response.content, 'html.parser')
        html_text = soup.get_text()

        # Validar que NÃO contém indicadores de compra
        self.assertNotIn('Aguardando Compra', html_text,
                        "Badge não deve mostrar 'Aguardando Compra' após desmarcar")

        # Badge deve existir com ID correto
        badge = soup.find('span', id=f'badge-{self.item.id}')
        self.assertIsNotNone(badge, "Badge deve existir no HTML retornado")

        # Badge NÃO deve ter classes de compra
        badge_classes = badge.get('class', [])
        self.assertNotIn('bg-orange-100', badge_classes,
                        "Badge não deve ter estilo de compra após desmarcar")

    @patch('core.presentation.web.views.get_channel_layer')
    def test_desmarcar_compra_emite_websocket(self, mock_channel_layer):
        """
        Teste 3: Desmarcar compra deve emitir evento WebSocket.

        Valida que evento 'item_desmarcado_compra' é emitido
        para grupo 'dashboard'.
        """
        # Mock do channel layer
        mock_layer = MagicMock()
        mock_channel_layer.return_value = mock_layer

        url = reverse('desmarcar_compra', kwargs={'pedido_id': self.pedido.id, 'item_id': self.item.id})
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

        # Validar tipo de evento
        self.assertEqual(event_data['type'], 'item_desmarcado_compra')

    @patch('core.presentation.web.views.get_channel_layer')
    def test_desmarcar_compra_payload_completo(self, mock_channel_layer):
        """
        Teste 4: Payload WebSocket deve conter dados completos do item.

        Valida que evento contém:
        - item_id
        - pedido_id
        - numero_orcamento
        - produto_codigo
        - desmarcado_por (usuário que desmarcou)
        """
        # Mock do channel layer
        mock_layer = MagicMock()
        mock_channel_layer.return_value = mock_layer

        url = reverse('desmarcar_compra', kwargs={'pedido_id': self.pedido.id, 'item_id': self.item.id})
        response = self.client.post(url, HTTP_X_REQUESTED_WITH='XMLHttpRequest')

        # Validar response OK
        self.assertEqual(response.status_code, 200)

        # Extrair argumentos da chamada
        call_args = mock_layer.group_send.call_args
        event_data = call_args[0][1]

        # Validar dados do item
        self.assertEqual(event_data['item_id'], self.item.id)
        self.assertEqual(event_data['pedido_id'], self.pedido.id)
        self.assertEqual(event_data['numero_orcamento'], self.pedido.numero_orcamento)
        self.assertEqual(event_data['produto_codigo'], self.produto.codigo)
        self.assertEqual(event_data['produto_descricao'], self.produto.descricao)

        # Validar usuário que desmarcou
        self.assertEqual(event_data['desmarcado_por'], self.user.nome)

    def test_desmarcar_apenas_se_estava_em_compra(self):
        """
        Teste 5: Desmarcar deve funcionar apenas se item estava em compra.

        Valida comportamento com item que NÃO está em compra:
        - Não deve gerar erro
        - Campos devem permanecer None
        """
        # Criar item que NÃO está em compra
        item_nao_compra = ItemPedido.objects.create(
            pedido=self.pedido,
            produto=self.produto,
            quantidade_solicitada=3,
            quantidade_separada=0,
            separado=False,
            em_compra=False,  # NÃO está em compra
            enviado_para_compra_por=None,
            enviado_para_compra_em=None
        )

        url = reverse('desmarcar_compra', kwargs={
            'pedido_id': self.pedido.id,
            'item_id': item_nao_compra.id
        })
        response = self.client.post(url, HTTP_X_REQUESTED_WITH='XMLHttpRequest')

        # Validar response OK (não deve dar erro)
        self.assertEqual(response.status_code, 200)

        # Verificar que campos continuam limpos
        item_nao_compra.refresh_from_db()
        self.assertFalse(item_nao_compra.em_compra)
        self.assertIsNone(item_nao_compra.enviado_para_compra_por)
        self.assertIsNone(item_nao_compra.enviado_para_compra_em)
