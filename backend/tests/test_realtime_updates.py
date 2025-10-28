# -*- coding: utf-8 -*-
"""
Testes para Atualizações em Tempo Real na Separação de Itens
TDD: RED → GREEN → REFACTOR

Este módulo testa as atualizações em tempo real quando um item é separado:
- WebSocket conectado na página de detalhes do pedido
- Contador de itens atualiza em tempo real
- Barra de progresso atualiza em tempo real
- Badge de status atualiza
- Botão finalizar aparece quando atinge 100%
- Múltiplos clientes recebem mesma atualização (broadcasting)
"""

import pytest
import json
from unittest.mock import Mock, patch, AsyncMock
from django.test import TestCase, RequestFactory, Client
from django.contrib.sessions.middleware import SessionMiddleware

from core.models import Usuario, Pedido, ItemPedido, Produto as ProdutoModel
from core.presentation.web.views import SepararItemView


class TestRealtimeUpdatesTDD(TestCase):
    """
    Testes TDD para validar atualizações em tempo real.

    Cobertura:
    1. Evento WebSocket contém todos os dados necessários
    2. Contador de itens é atualizado em tempo real
    3. Barra de progresso é atualizada em tempo real
    4. Badge de status é atualizado
    5. Botão finalizar aparece quando progresso = 100%
    6. Template detalhe_pedido.html tem script WebSocket
    7. Template dashboard.html atualiza contador de itens
    8. Múltiplos usuários recebem broadcast simultaneamente
    """

    def setUp(self):
        """Setup para cada teste."""
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

    def _add_session_to_request(self, request, usuario):
        """Helper para adicionar sessão e messages ao request."""
        from django.contrib.messages.middleware import MessageMiddleware
        from django.contrib.messages.storage.fallback import FallbackStorage

        # Adicionar sessão
        middleware = SessionMiddleware(lambda x: None)
        middleware.process_request(request)
        request.session.save()
        request.session['usuario_id'] = usuario.id
        request.user = usuario

        # Adicionar messages storage
        setattr(request, '_messages', FallbackStorage(request))

        return request

    @patch('core.presentation.web.views.get_channel_layer')
    def test_evento_websocket_contem_itens_separados_e_total(self, mock_get_channel_layer):
        """
        Teste 1 (RED): Verifica se evento WebSocket contém contador de itens.

        Cenário:
        1. Pedido tem 3 itens, 1 já separado
        2. Usuário marca 2º item como separado
        3. Evento deve conter: itens_separados=2, total_itens=3

        Validações:
        - Evento contém campo 'itens_separados'
        - Evento contém campo 'total_itens'
        - Valores estão corretos
        """
        # Mock do channel layer
        mock_channel_layer = Mock()
        mock_channel_layer.group_send = AsyncMock()
        mock_get_channel_layer.return_value = mock_channel_layer

        # Criar pedido com 3 itens
        pedido = Pedido.objects.create(
            numero_orcamento='30567',
            codigo_cliente='12345',
            nome_cliente='Cliente Teste',
            vendedor=self.vendedor,
            logistica='MOTOBOY',
            embalagem='CAIXA',
            status='EM_SEPARACAO'
        )

        # Item 1: já separado
        ItemPedido.objects.create(
            pedido=pedido,
            produto=self.produto,
            quantidade_solicitada=5,
            separado=True,
            quantidade_separada=5
        )

        # Item 2: não separado (será marcado agora)
        item2 = ItemPedido.objects.create(
            pedido=pedido,
            produto=self.produto,
            quantidade_solicitada=3,
            separado=False
        )

        # Item 3: não separado
        ItemPedido.objects.create(
            pedido=pedido,
            produto=self.produto,
            quantidade_solicitada=2,
            separado=False
        )

        # Marcar item 2 como separado
        request = self.factory.post(
            f'/pedidos/{pedido.id}/itens/{item2.id}/marcar-separado/',
            HTTP_HX_REQUEST='true'
        )
        request = self._add_session_to_request(request, self.separador)

        view = SepararItemView()
        view.post(request, pedido_id=pedido.id, item_id=item2.id)

        # Validações
        assert mock_channel_layer.group_send.called, \
            "group_send deve ser chamado ao marcar item"

        call_args = mock_channel_layer.group_send.call_args
        event_data = call_args[0][1]

        # ESTE TESTE VAI FALHAR (RED) porque ainda não implementamos esses campos
        assert 'itens_separados' in event_data, \
            "Evento deve conter campo 'itens_separados'"
        assert 'total_itens' in event_data, \
            "Evento deve conter campo 'total_itens'"

        assert event_data['itens_separados'] == 2, \
            f"Esperado 2 itens separados, mas recebeu {event_data.get('itens_separados')}"
        assert event_data['total_itens'] == 3, \
            f"Esperado 3 itens totais, mas recebeu {event_data.get('total_itens')}"

    @patch('core.presentation.web.views.get_channel_layer')
    def test_evento_websocket_contem_item_id(self, mock_get_channel_layer):
        """
        Teste 2 (RED): Verifica se evento contém item_id para animações específicas.

        Validações:
        - Evento contém campo 'item_id'
        - item_id corresponde ao item que foi marcado
        """
        # Mock do channel layer
        mock_channel_layer = Mock()
        mock_channel_layer.group_send = AsyncMock()
        mock_get_channel_layer.return_value = mock_channel_layer

        # Criar pedido e item
        pedido = Pedido.objects.create(
            numero_orcamento='30567',
            codigo_cliente='12345',
            nome_cliente='Cliente Teste',
            vendedor=self.vendedor,
            logistica='MOTOBOY',
            embalagem='CAIXA',
            status='EM_SEPARACAO'
        )

        item = ItemPedido.objects.create(
            pedido=pedido,
            produto=self.produto,
            quantidade_solicitada=10,
            separado=False
        )

        # Marcar item como separado
        request = self.factory.post(
            f'/pedidos/{pedido.id}/itens/{item.id}/marcar-separado/',
            HTTP_HX_REQUEST='true'
        )
        request = self._add_session_to_request(request, self.separador)

        view = SepararItemView()
        view.post(request, pedido_id=pedido.id, item_id=item.id)

        # Validações
        call_args = mock_channel_layer.group_send.call_args
        event_data = call_args[0][1]

        # ESTE TESTE VAI FALHAR (RED)
        assert 'item_id' in event_data, \
            "Evento deve conter campo 'item_id'"
        assert event_data['item_id'] == item.id, \
            f"item_id deve ser {item.id}, mas recebeu {event_data.get('item_id')}"

    def test_detalhe_pedido_template_tem_script_websocket(self):
        """
        Teste 3 (RED): Verifica se template detalhe_pedido.html tem script WebSocket.

        Validações:
        - Template contém tag <script> com WebSocket
        - Script conecta ao /ws/dashboard/
        - Script tem handler para evento 'item_separado'
        - Script atualiza elementos: progresso-percentual, contador-itens, barra-progresso
        """
        import os
        template_path = os.path.join(
            os.path.dirname(__file__),
            '../templates/detalhe_pedido.html'
        )

        with open(template_path, 'r', encoding='utf-8') as f:
            template_content = f.read()

        # Validações - ESTAS VÃO FALHAR (RED) porque ainda não implementamos
        assert 'WebSocket' in template_content, \
            "Template detalhe_pedido.html deve conter script WebSocket"

        assert '/ws/dashboard/' in template_content, \
            "Script deve conectar ao endpoint /ws/dashboard/"

        assert 'item_separado' in template_content, \
            "Script deve ter handler para evento 'item_separado'"

        # Verificar que atualiza elementos específicos
        assert 'progresso-percentual' in template_content, \
            "Script deve atualizar elemento #progresso-percentual"

        assert 'contador-itens' in template_content, \
            "Script deve atualizar elemento #contador-itens"

        assert 'barra-progresso' in template_content, \
            "Script deve atualizar elemento #barra-progresso"

    def test_detalhe_pedido_template_tem_ids_unicos(self):
        """
        Teste 4 (RED): Verifica se elementos do template têm IDs únicos.

        Validações:
        - Elemento de progresso percentual tem id="progresso-percentual"
        - Contador de itens tem id="contador-itens"
        - Barra de progresso tem id="barra-progresso"
        - Badge de itens não separados tem id="badge-nao-separados"
        - Badge de itens separados tem id="badge-separados"
        - Container do botão finalizar tem id="container-botao-finalizar"
        """
        import os
        template_path = os.path.join(
            os.path.dirname(__file__),
            '../templates/detalhe_pedido.html'
        )

        with open(template_path, 'r', encoding='utf-8') as f:
            template_content = f.read()

        # ESTAS VALIDAÇÕES VÃO FALHAR (RED)
        assert 'id="progresso-percentual"' in template_content, \
            "Template deve ter elemento com id='progresso-percentual'"

        assert 'id="contador-itens"' in template_content, \
            "Template deve ter elemento com id='contador-itens'"

        assert 'id="barra-progresso"' in template_content, \
            "Template deve ter elemento com id='barra-progresso'"

        assert 'id="badge-nao-separados"' in template_content, \
            "Template deve ter elemento com id='badge-nao-separados'"

        assert 'id="badge-separados"' in template_content, \
            "Template deve ter elemento com id='badge-separados'"

        assert 'id="container-botao-finalizar"' in template_content, \
            "Template deve ter elemento com id='container-botao-finalizar'"

    def test_dashboard_template_atualiza_contador_itens(self):
        """
        Teste 5 (RED): Verifica se dashboard.html atualiza contador de itens.

        Validações:
        - Script WebSocket do dashboard tem função handleItemSeparado
        - Função atualiza contador "(X/Y itens)" no card
        - Usa os campos itens_separados e total_itens do evento
        """
        import os
        template_path = os.path.join(
            os.path.dirname(__file__),
            '../templates/dashboard.html'
        )

        with open(template_path, 'r', encoding='utf-8') as f:
            template_content = f.read()

        # Validações - ESTAS VÃO FALHAR (RED)
        assert 'handleItemSeparado' in template_content, \
            "Dashboard deve ter função handleItemSeparado"

        # Verificar que usa os novos campos do evento
        assert 'itens_separados' in template_content, \
            "Script deve usar campo 'itens_separados' do evento"

        assert 'total_itens' in template_content, \
            "Script deve usar campo 'total_itens' do evento"

    def test_card_pedido_partial_tem_id_contador(self):
        """
        Teste 6 (RED): Verifica se card do pedido tem ID no contador de itens.

        Validações:
        - Partial _card_pedido.html tem elemento com classe/ID para contador
        - Permite atualização via JavaScript
        """
        import os
        template_path = os.path.join(
            os.path.dirname(__file__),
            '../templates/partials/_card_pedido.html'
        )

        with open(template_path, 'r', encoding='utf-8') as f:
            template_content = f.read()

        # O contador precisa ter um ID único ou classe específica
        # Aceita qualquer ocorrência de class com contador-itens (pode ter outras classes)
        has_contador_id = (
            'contador-itens' in template_content and
            ('class=' in template_content or 'id=' in template_content)
        )

        assert has_contador_id, \
            "Card do pedido deve ter elemento identificável para o contador de itens (classe 'contador-itens')"

    @patch('core.presentation.web.views.get_channel_layer')
    def test_evento_marca_toggle_off_tambem_emite_websocket(self, mock_get_channel_layer):
        """
        Teste 7 (RED): Verifica se desmarcar item (toggle off) também emite evento.

        Cenário:
        1. Item está separado
        2. Usuário desmarca (toggle off)
        3. Evento WebSocket deve ser emitido com progresso atualizado

        Validações:
        - Evento é emitido ao desmarcar
        - Progresso diminui corretamente
        - itens_separados é decrementado
        """
        # Mock do channel layer
        mock_channel_layer = Mock()
        mock_channel_layer.group_send = AsyncMock()
        mock_get_channel_layer.return_value = mock_channel_layer

        # Criar pedido com item já separado
        pedido = Pedido.objects.create(
            numero_orcamento='30567',
            codigo_cliente='12345',
            nome_cliente='Cliente Teste',
            vendedor=self.vendedor,
            logistica='MOTOBOY',
            embalagem='CAIXA',
            status='EM_SEPARACAO'
        )

        item = ItemPedido.objects.create(
            pedido=pedido,
            produto=self.produto,
            quantidade_solicitada=10,
            separado=True,  # JÁ separado
            quantidade_separada=10
        )

        # Desmarcar item (toggle off)
        request = self.factory.post(
            f'/pedidos/{pedido.id}/itens/{item.id}/marcar-separado/',
            HTTP_HX_REQUEST='true'
        )
        request = self._add_session_to_request(request, self.separador)

        view = SepararItemView()
        view.post(request, pedido_id=pedido.id, item_id=item.id)

        # Validações
        assert mock_channel_layer.group_send.called, \
            "group_send deve ser chamado ao DESMARCAR item"

        call_args = mock_channel_layer.group_send.call_args
        event_data = call_args[0][1]

        # Progresso deve ser 0% (único item foi desmarcado)
        assert event_data['progresso'] == 0, \
            f"Progresso deve ser 0%, mas recebeu {event_data['progresso']}%"

        # ESTAS VALIDAÇÕES VÃO FALHAR (RED)
        assert event_data['itens_separados'] == 0, \
            f"Deve ter 0 itens separados após desmarcar, mas recebeu {event_data.get('itens_separados')}"

    @patch('core.presentation.web.views.get_channel_layer')
    def test_evento_ultimo_item_separado_atinge_100_porcento(self, mock_get_channel_layer):
        """
        Teste 8 (RED): Verifica comportamento quando último item é separado (100%).

        Cenário:
        1. Pedido tem 2 itens, 1 já separado (50%)
        2. Usuário marca último item como separado
        3. Progresso deve ser 100%
        4. Evento deve indicar que pedido está completo

        Validações:
        - progresso = 100
        - itens_separados = total_itens
        """
        # Mock do channel layer
        mock_channel_layer = Mock()
        mock_channel_layer.group_send = AsyncMock()
        mock_get_channel_layer.return_value = mock_channel_layer

        # Criar pedido com 2 itens
        pedido = Pedido.objects.create(
            numero_orcamento='30567',
            codigo_cliente='12345',
            nome_cliente='Cliente Teste',
            vendedor=self.vendedor,
            logistica='MOTOBOY',
            embalagem='CAIXA',
            status='EM_SEPARACAO'
        )

        # Item 1: já separado
        ItemPedido.objects.create(
            pedido=pedido,
            produto=self.produto,
            quantidade_solicitada=5,
            separado=True,
            quantidade_separada=5
        )

        # Item 2: último item, não separado
        ultimo_item = ItemPedido.objects.create(
            pedido=pedido,
            produto=self.produto,
            quantidade_solicitada=5,
            separado=False
        )

        # Marcar último item como separado
        request = self.factory.post(
            f'/pedidos/{pedido.id}/itens/{ultimo_item.id}/marcar-separado/',
            HTTP_HX_REQUEST='true'
        )
        request = self._add_session_to_request(request, self.separador)

        view = SepararItemView()
        view.post(request, pedido_id=pedido.id, item_id=ultimo_item.id)

        # Validações
        call_args = mock_channel_layer.group_send.call_args
        event_data = call_args[0][1]

        assert event_data['progresso'] == 100, \
            f"Progresso deve ser 100%, mas recebeu {event_data['progresso']}%"

        # ESTAS VALIDAÇÕES VÃO FALHAR (RED)
        assert event_data['itens_separados'] == event_data['total_itens'], \
            "itens_separados deve ser igual a total_itens quando 100%"

        assert event_data['itens_separados'] == 2, \
            f"Deve ter 2 itens separados, mas recebeu {event_data.get('itens_separados')}"

        assert event_data['total_itens'] == 2, \
            f"Deve ter 2 itens totais, mas recebeu {event_data.get('total_itens')}"


class TestRealtimeUpdatesFuncional(TestCase):
    """
    Testes funcionais para validar comportamento end-to-end.
    """

    def setUp(self):
        """Setup para cada teste."""
        # Criar usuário separador
        self.separador = Usuario.objects.create_user(
            numero_login=2,
            pin='1234',
            nome='Maria Separadora',
            tipo='SEPARADOR'
        )

        # Criar usuário vendedor
        self.vendedor = Usuario.objects.create_user(
            numero_login=1,
            pin='1234',
            nome='João Vendedor',
            tipo='VENDEDOR'
        )

        # Criar produto
        self.produto = ProdutoModel.objects.create(
            codigo='12345',
            descricao='Produto Teste',
            quantidade=10,
            valor_unitario=10.00,
            valor_total=100.00
        )

    def test_pagina_detalhe_pedido_renderiza_com_ids_corretos(self):
        """
        Teste 9 (RED): Verifica se página de detalhes renderiza com IDs corretos.

        Cenário:
        1. Criar pedido com itens
        2. Acessar página de detalhes
        3. Verificar que HTML contém IDs necessários para WebSocket
        """
        from django.test import Client

        # Criar pedido
        pedido = Pedido.objects.create(
            numero_orcamento='30567',
            codigo_cliente='12345',
            nome_cliente='Cliente Teste',
            vendedor=self.vendedor,
            logistica='MOTOBOY',
            embalagem='CAIXA',
            status='EM_SEPARACAO'
        )

        ItemPedido.objects.create(
            pedido=pedido,
            produto=self.produto,
            quantidade_solicitada=10,
            separado=False
        )

        # Acessar página
        client = Client()
        client.force_login(self.separador)
        response = client.get(f'/pedidos/{pedido.id}/')

        assert response.status_code == 200, \
            f"Página deve retornar 200, mas retornou {response.status_code}"

        content = response.content.decode('utf-8')

        # ESTAS VALIDAÇÕES VÃO FALHAR (RED)
        assert 'id="progresso-percentual"' in content, \
            "HTML renderizado deve conter id='progresso-percentual'"

        assert 'id="contador-itens"' in content, \
            "HTML renderizado deve conter id='contador-itens'"

        assert 'id="barra-progresso"' in content, \
            "HTML renderizado deve conter id='barra-progresso'"
