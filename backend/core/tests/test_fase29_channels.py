# -*- coding: utf-8 -*-
"""
Testes para Fase 29: Configurar Django Channels e WebSockets
TDD - RED Phase

Objetivo: Configurar infraestrutura de WebSockets para atualização em tempo real

Testes:
1. test_channels_installed - Channels está instalado
2. test_asgi_application_configured - ASGI configurado corretamente
3. test_redis_channel_layer_configured - Redis como backend do channel layer
4. test_websocket_connection_success - Conectar ao WebSocket funciona
5. test_websocket_disconnect_clean - Desconectar limpa recursos
6. test_multiple_clients_can_connect - Múltiplos clientes simultâneos
"""

import pytest
from channels.testing import WebsocketCommunicator
from django.conf import settings


class TestFase29Channels:
    """
    Testes para configuração do Django Channels e WebSockets.
    Fase 29: Infraestrutura de tempo real.
    """

    def test_channels_installed(self):
        """
        Testa se Django Channels está instalado e configurado.

        Verifica:
        - channels está em INSTALLED_APPS
        - daphne está em INSTALLED_APPS
        """
        assert 'channels' in settings.INSTALLED_APPS, \
            "Django Channels não está em INSTALLED_APPS"
        assert 'daphne' in settings.INSTALLED_APPS, \
            "Daphne não está em INSTALLED_APPS"

    def test_asgi_application_configured(self):
        """
        Testa se ASGI application está configurada corretamente.

        Verifica:
        - ASGI_APPLICATION está definido em settings
        - ASGI application aponta para o arquivo correto
        """
        assert hasattr(settings, 'ASGI_APPLICATION'), \
            "ASGI_APPLICATION não está configurado no settings"

        assert settings.ASGI_APPLICATION == 'separacao_pmcell.asgi.application', \
            f"ASGI_APPLICATION incorreto: {settings.ASGI_APPLICATION}"

    def test_redis_channel_layer_configured(self):
        """
        Testa se Redis está configurado como channel layer.

        Verifica:
        - CHANNEL_LAYERS está configurado
        - Backend é channels_redis.core.RedisChannelLayer
        - Configuração de host Redis
        """
        assert hasattr(settings, 'CHANNEL_LAYERS'), \
            "CHANNEL_LAYERS não está configurado no settings"

        channel_layers = settings.CHANNEL_LAYERS
        assert 'default' in channel_layers, \
            "Channel layer 'default' não está configurado"

        default_layer = channel_layers['default']
        assert 'BACKEND' in default_layer, \
            "BACKEND não está definido no channel layer"

        expected_backend = 'channels_redis.core.RedisChannelLayer'
        assert default_layer['BACKEND'] == expected_backend, \
            f"Backend incorreto: {default_layer['BACKEND']}"

    @pytest.mark.asyncio
    async def test_websocket_connection_success(self):
        """
        Testa se é possível conectar ao WebSocket.

        Verifica:
        - Conexão WebSocket é aceita
        - Status de conexão é True
        """
        from separacao_pmcell.asgi import application

        # Criar communicator para /ws/dashboard/ com headers de origem válida
        communicator = WebsocketCommunicator(
            application,
            "/ws/dashboard/",
            headers=[(b"origin", b"http://localhost")]
        )

        # Tentar conectar
        connected, subprotocol = await communicator.connect()

        assert connected is True, \
            "Falha ao conectar no WebSocket /ws/dashboard/"

        # Limpar conexão
        await communicator.disconnect()

    @pytest.mark.asyncio
    async def test_websocket_disconnect_clean(self):
        """
        Testa se desconexão do WebSocket é limpa.

        Verifica:
        - Conectar funciona
        - Desconectar não gera exceções
        - Recursos são liberados
        """
        from separacao_pmcell.asgi import application

        communicator = WebsocketCommunicator(
            application,
            "/ws/dashboard/",
            headers=[(b"origin", b"http://localhost")]
        )

        # Conectar
        connected, _ = await communicator.connect()
        assert connected is True, "Falha ao conectar"

        # Desconectar (não deve gerar exceções)
        try:
            await communicator.disconnect()
            disconnect_success = True
        except Exception as e:
            disconnect_success = False
            pytest.fail(f"Erro ao desconectar: {e}")

        assert disconnect_success is True, \
            "Desconexão do WebSocket falhou"

    @pytest.mark.asyncio
    async def test_multiple_clients_can_connect(self):
        """
        Testa se múltiplos clientes podem conectar simultaneamente.

        Verifica:
        - 3 clientes conectam ao mesmo tempo
        - Todos recebem status connected=True
        - Todos desconectam sem erros
        """
        from separacao_pmcell.asgi import application

        # Criar 3 communicators com headers válidos
        communicators = [
            WebsocketCommunicator(
                application,
                "/ws/dashboard/",
                headers=[(b"origin", b"http://localhost")]
            )
            for _ in range(3)
        ]

        # Conectar todos
        connections = []
        for comm in communicators:
            connected, _ = await comm.connect()
            connections.append(connected)

        # Verificar que todos conectaram
        assert all(connections), \
            f"Nem todos os clientes conectaram: {connections}"

        # Desconectar todos
        for comm in communicators:
            await comm.disconnect()


# Configuração do pytest para testes assíncronos
@pytest.fixture(scope='session')
def django_db_setup():
    """Setup do banco para testes assíncronos."""
    pass
