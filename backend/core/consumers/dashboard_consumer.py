# -*- coding: utf-8 -*-
"""
DashboardConsumer - WebSocket Consumer para Dashboard
Fase 29: Configurar Django Channels e WebSockets

Este consumer gerencia conexões WebSocket para o dashboard,
permitindo atualizações em tempo real dos pedidos.

Funcionalidades:
- Conectar/desconectar clientes
- Adicionar cliente ao grupo 'dashboard'
- Receber e processar mensagens (Fase 30)
- Broadcast de eventos (Fase 30)
"""

import json
from channels.generic.websocket import AsyncWebsocketConsumer


class DashboardConsumer(AsyncWebsocketConsumer):
    """
    Consumer para gerenciar WebSocket connections no dashboard.

    Grupo: 'dashboard'
    - Todos os clientes conectados ao dashboard fazem parte deste grupo
    - Eventos são broadcasted para todos os membros do grupo

    Métodos:
    - connect(): Aceita conexão e adiciona ao grupo
    - disconnect(): Remove do grupo e fecha conexão
    - receive(): Recebe mensagens do cliente (futuro)
    """

    async def connect(self):
        """
        Chamado quando cliente tenta conectar ao WebSocket.

        Fluxo:
        1. Adiciona cliente ao grupo 'dashboard'
        2. Aceita a conexão WebSocket
        """
        # Nome do grupo (todos os clientes do dashboard)
        self.group_name = 'dashboard'

        # Adicionar este canal ao grupo
        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )

        # Aceitar conexão WebSocket
        await self.accept()

    async def disconnect(self, close_code):
        """
        Chamado quando cliente desconecta do WebSocket.

        Args:
            close_code: Código de fechamento da conexão

        Fluxo:
        1. Remove cliente do grupo 'dashboard'
        """
        # Remover deste grupo
        await self.channel_layer.group_discard(
            self.group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        """
        Recebe mensagem do cliente WebSocket.

        Args:
            text_data: JSON string com dados da mensagem

        Nota: Implementação completa na Fase 30
        """
        # Parse JSON
        data = json.loads(text_data)

        # TODO Fase 30: Processar diferentes tipos de mensagens
        # - ping/pong para keep-alive
        # - comandos do cliente

    # Handlers para eventos do grupo (Fase 30)
    async def pedido_criado(self, event):
        """
        Handler para evento 'pedido_criado'.
        Envia notificação para o cliente quando novo pedido é criado.

        Implementação completa na Fase 30.
        """
        await self.send(text_data=json.dumps({
            'type': 'pedido_criado',
            'pedido_id': event['pedido_id'],
        }))

    async def item_separado(self, event):
        """
        Handler para evento 'item_separado'.
        Atualiza progresso do pedido em tempo real.

        Args:
            event (dict): Evento recebido do channel layer
                - pedido_id: ID do pedido
                - progresso: Progresso percentual (0-100)
                - itens_separados: Número de itens já separados
                - total_itens: Número total de itens do pedido
                - item_id: ID do item que foi marcado/desmarcado

        Envia para o cliente WebSocket todos os dados necessários para
        atualizar a UI em tempo real sem recarregar a página.
        """
        await self.send(text_data=json.dumps({
            'type': 'item_separado',
            'pedido_id': event['pedido_id'],
            'progresso': event['progresso'],
            'itens_separados': event['itens_separados'],
            'total_itens': event['total_itens'],
            'item_id': event['item_id'],
            'em_compra': event.get('em_compra', False)  # Fase 43a: Flag para remover do painel de compras
        }))

    async def pedido_finalizado(self, event):
        """
        Handler para evento 'pedido_finalizado'.
        Remove card do pedido do dashboard.

        Implementação completa na Fase 30.
        """
        await self.send(text_data=json.dumps({
            'type': 'pedido_finalizado',
            'pedido_id': event['pedido_id'],
        }))

    async def item_marcado_compra(self, event):
        """
        Handler para evento 'item_marcado_compra'.
        Notifica painel de compras quando novo item é enviado para compra.

        Args:
            event (dict): Evento recebido do channel layer
                - item_id: ID do item
                - pedido_id: ID do pedido
                - numero_orcamento: Número do orçamento
                - nome_cliente: Nome do cliente
                - produto_codigo: Código do produto
                - produto_descricao: Descrição do produto
                - quantidade_solicitada: Quantidade
                - enviado_por: Nome do usuário que enviou
                - enviado_em: Timestamp formatado

        Envia para o cliente WebSocket dados necessários para
        renderizar o item no painel de compras em tempo real.
        """
        await self.send(text_data=json.dumps({
            'type': 'item_marcado_compra',
            'item_id': event.get('item_id'),
            'pedido_id': event.get('pedido_id'),
            'numero_orcamento': event.get('numero_orcamento'),
            'nome_cliente': event.get('nome_cliente'),
            'produto_codigo': event.get('produto_codigo'),
            'produto_descricao': event.get('produto_descricao'),
            'quantidade_solicitada': event.get('quantidade_solicitada'),
            'enviado_por': event.get('enviado_por'),
            'enviado_em': event.get('enviado_em')
        }))

    async def item_desmarcado_compra(self, event):
        """
        Handler para evento 'item_desmarcado_compra' (Fase 42c).
        Notifica painel de compras quando item é desmarcado de compra.

        Args:
            event (dict): Evento recebido do channel layer
                - item_id: ID do item
                - pedido_id: ID do pedido
                - numero_orcamento: Número do orçamento
                - produto_codigo: Código do produto
                - produto_descricao: Descrição do produto
                - desmarcado_por: Nome do usuário que desmarcou

        Envia para o cliente WebSocket dados necessários para
        remover o item do painel de compras em tempo real.
        """
        await self.send(text_data=json.dumps({
            'type': 'item_desmarcado_compra',
            'item_id': event.get('item_id'),
            'pedido_id': event.get('pedido_id'),
            'numero_orcamento': event.get('numero_orcamento'),
            'produto_codigo': event.get('produto_codigo'),
            'produto_descricao': event.get('produto_descricao'),
            'desmarcado_por': event.get('desmarcado_por')
        }))

    async def item_pedido_realizado(self, event):
        """
        Handler para evento 'item_pedido_realizado' (Fase 43c).
        Notifica dashboard quando item em compra é marcado como realizado,
        permitindo atualizar badge de "Aguardando Compra" para "Já Comprado".

        Args:
            event (dict): Evento recebido do channel layer
                - item_id: ID do item
                - pedido_id: ID do pedido
                - pedido_realizado: Boolean indicando estado (True/False)

        Envia para o cliente WebSocket dados necessários para
        atualizar o badge no dashboard em tempo real.
        """
        await self.send(text_data=json.dumps({
            'type': 'item_pedido_realizado',
            'item_id': event.get('item_id'),
            'pedido_id': event.get('pedido_id'),
            'pedido_realizado': event.get('pedido_realizado', False)
        }))
