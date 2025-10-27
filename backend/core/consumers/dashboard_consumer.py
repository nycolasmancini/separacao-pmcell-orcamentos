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

        Implementação completa na Fase 30.
        """
        await self.send(text_data=json.dumps({
            'type': 'item_separado',
            'pedido_id': event['pedido_id'],
            'progresso': event['progresso'],
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
