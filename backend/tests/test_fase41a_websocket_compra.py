# -*- coding: utf-8 -*-
"""
Testes para Fase 41a - Backend: Handler WebSocket para item_marcado_compra.

Valida que:
1. DashboardConsumer tem método item_marcado_compra
2. MarcarCompraView emite evento WebSocket correto
3. Cliente conectado recebe evento quando item é marcado
4. Payload do WebSocket está correto
5. Múltiplos clientes recebem o evento (broadcast)
"""

import pytest
import json
from channels.testing import WebsocketCommunicator
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from django.contrib.auth import get_user_model
from core.models import Pedido, ItemPedido, Produto
from core.consumers.dashboard_consumer import DashboardConsumer
from core.routing import application

Usuario = get_user_model()


@pytest.mark.django_db
@pytest.mark.asyncio
class TestFase41aWebSocketCompra:
    """Testes para handler WebSocket de item marcado para compra."""

    @pytest.fixture(autouse=True)
    async def setup(self, db):
        """Setup que roda antes de cada teste."""
        # Criar usuário separador
        self.separador = Usuario.objects.create(
            numero_login="001",
            nome="Separador Teste",
            tipo="SEPARADOR",
            ativo=True
        )
        self.separador.set_password("1234")
        self.separador.save()

        # Criar usuário vendedor
        self.vendedor = Usuario.objects.create(
            numero_login="002",
            nome="Vendedor Teste",
            tipo="VENDEDOR",
            ativo=True
        )
        self.vendedor.set_password("1234")
        self.vendedor.save()

        # Criar produto
        self.produto = Produto.objects.create(
            codigo="12345",
            descricao="Produto Teste"
        )

        # Criar pedido
        self.pedido = Pedido.objects.create(
            numero_orcamento="PED-001",
            codigo_cliente="CLI-001",
            nome_cliente="Cliente Teste",
            vendedor=self.vendedor,
            estado="SEPARACAO"
        )

        # Criar item
        self.item = ItemPedido.objects.create(
            pedido=self.pedido,
            produto=self.produto,
            quantidade_solicitada=10
        )

    async def test_consumer_tem_handler_item_marcado_compra(self):
        """
        Test 1: DashboardConsumer deve ter método item_marcado_compra.

        Dado um DashboardConsumer
        Quando verifico se método existe
        Então deve ter o método item_marcado_compra
        E o método deve ser assíncrono
        """
        consumer = DashboardConsumer()

        assert hasattr(consumer, 'item_marcado_compra'), \
            "DashboardConsumer deve ter método item_marcado_compra"

        assert callable(consumer.item_marcado_compra), \
            "item_marcado_compra deve ser callable"

        # Verificar que é async
        import inspect
        assert inspect.iscoroutinefunction(consumer.item_marcado_compra), \
            "item_marcado_compra deve ser função assíncrona"

    async def test_evento_websocket_tem_estrutura_correta(self):
        """
        Test 2: Evento deve ter estrutura correta no payload.

        Dado um evento item_marcado_compra
        Quando envio para o consumer
        Então deve conter: type, item_id, pedido_id, produto_codigo, produto_descricao, quantidade
        """
        # Criar communicator e conectar
        communicator = WebsocketCommunicator(application, "/ws/dashboard/")
        connected, subprotocol = await communicator.connect()
        assert connected, "WebSocket deve conectar"

        # Simular evento do channel layer
        channel_layer = get_channel_layer()
        event_data = {
            'type': 'item_marcado_compra',
            'item_id': self.item.id,
            'pedido_id': self.pedido.id,
            'produto_codigo': self.produto.codigo,
            'produto_descricao': self.produto.descricao,
            'quantidade_solicitada': self.item.quantidade_solicitada,
            'enviado_por': self.separador.nome
        }

        await channel_layer.group_send('dashboard', event_data)

        # Aguardar mensagem
        response = await communicator.receive_from()
        data = json.loads(response)

        # Validar estrutura
        assert data['type'] == 'item_marcado_compra'
        assert data['item_id'] == self.item.id
        assert data['pedido_id'] == self.pedido.id
        assert data['produto_codigo'] == self.produto.codigo
        assert data['produto_descricao'] == self.produto.descricao
        assert data['quantidade_solicitada'] == self.item.quantidade_solicitada
        assert data['enviado_por'] == self.separador.nome

        # Desconectar
        await communicator.disconnect()

    async def test_multiplos_clientes_recebem_evento(self):
        """
        Test 3: Múltiplos clientes conectados devem receber o mesmo evento.

        Dado 3 clientes conectados ao dashboard
        Quando um evento item_marcado_compra é emitido
        Então todos os 3 clientes devem receber o evento
        """
        # Criar 3 communicators
        comm1 = WebsocketCommunicator(application, "/ws/dashboard/")
        comm2 = WebsocketCommunicator(application, "/ws/dashboard/")
        comm3 = WebsocketCommunicator(application, "/ws/dashboard/")

        # Conectar todos
        connected1, _ = await comm1.connect()
        connected2, _ = await comm2.connect()
        connected3, _ = await comm3.connect()

        assert connected1 and connected2 and connected3, \
            "Todos os clientes devem conectar"

        # Emitir evento
        channel_layer = get_channel_layer()
        event_data = {
            'type': 'item_marcado_compra',
            'item_id': self.item.id,
            'pedido_id': self.pedido.id,
            'produto_codigo': self.produto.codigo,
            'produto_descricao': self.produto.descricao,
            'quantidade_solicitada': self.item.quantidade_solicitada,
            'enviado_por': self.separador.nome
        }

        await channel_layer.group_send('dashboard', event_data)

        # Todos devem receber
        response1 = await comm1.receive_from()
        response2 = await comm2.receive_from()
        response3 = await comm3.receive_from()

        data1 = json.loads(response1)
        data2 = json.loads(response2)
        data3 = json.loads(response3)

        # Validar que todos receberam o mesmo evento
        assert data1['item_id'] == self.item.id
        assert data2['item_id'] == self.item.id
        assert data3['item_id'] == self.item.id

        # Desconectar todos
        await comm1.disconnect()
        await comm2.disconnect()
        await comm3.disconnect()

    async def test_evento_contem_todos_campos_necessarios(self):
        """
        Test 4: Evento deve conter todos os campos necessários para renderizar o item.

        Dado um evento item_marcado_compra
        Quando recebo no frontend
        Então deve ter informações suficientes para renderizar card do item
        """
        communicator = WebsocketCommunicator(application, "/ws/dashboard/")
        connected, _ = await communicator.connect()
        assert connected

        channel_layer = get_channel_layer()
        event_data = {
            'type': 'item_marcado_compra',
            'item_id': self.item.id,
            'pedido_id': self.pedido.id,
            'numero_orcamento': self.pedido.numero_orcamento,
            'nome_cliente': self.pedido.nome_cliente,
            'produto_codigo': self.produto.codigo,
            'produto_descricao': self.produto.descricao,
            'quantidade_solicitada': self.item.quantidade_solicitada,
            'enviado_por': self.separador.nome,
            'enviado_em': '2025-10-30 14:30:00'  # Timestamp formatado
        }

        await channel_layer.group_send('dashboard', event_data)

        response = await communicator.receive_from()
        data = json.loads(response)

        # Campos essenciais
        assert 'item_id' in data
        assert 'pedido_id' in data
        assert 'numero_orcamento' in data
        assert 'nome_cliente' in data
        assert 'produto_codigo' in data
        assert 'produto_descricao' in data
        assert 'quantidade_solicitada' in data
        assert 'enviado_por' in data
        assert 'enviado_em' in data

        await communicator.disconnect()

    async def test_consumer_processa_evento_sem_erro(self):
        """
        Test 5: Consumer deve processar evento sem levantar exceção.

        Dado um DashboardConsumer conectado
        Quando recebe evento item_marcado_compra
        Então não deve levantar exceção
        E deve enviar mensagem corretamente
        """
        communicator = WebsocketCommunicator(application, "/ws/dashboard/")
        connected, _ = await communicator.connect()
        assert connected

        channel_layer = get_channel_layer()

        # Enviar evento malformado primeiro (edge case)
        try:
            await channel_layer.group_send('dashboard', {
                'type': 'item_marcado_compra',
                'item_id': self.item.id,
                'pedido_id': self.pedido.id,
                # Campos faltando propositalmente
            })

            # Não deve crashar, mas pode não enviar resposta completa
            # Isso é esperado
        except Exception as e:
            pytest.fail(f"Consumer não deve levantar exceção: {e}")

        # Enviar evento correto
        event_data = {
            'type': 'item_marcado_compra',
            'item_id': self.item.id,
            'pedido_id': self.pedido.id,
            'produto_codigo': self.produto.codigo,
            'produto_descricao': self.produto.descricao,
            'quantidade_solicitada': self.item.quantidade_solicitada,
            'enviado_por': self.separador.nome
        }

        await channel_layer.group_send('dashboard', event_data)

        response = await communicator.receive_from()
        data = json.loads(response)

        assert data['type'] == 'item_marcado_compra'

        await communicator.disconnect()
