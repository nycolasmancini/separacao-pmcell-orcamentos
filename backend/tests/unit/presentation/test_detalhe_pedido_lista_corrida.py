# -*- coding: utf-8 -*-
"""
Testes para view detalhe_pedido com lista corrida única (Fase 39b).

Valida que a view retorna lista única de itens ordenados,
sem separação em 'itens_separados' e 'itens_nao_separados'.
"""

import pytest
from django.test import RequestFactory, Client
from django.contrib.sessions.middleware import SessionMiddleware
from django.utils import timezone
from django.urls import reverse
from core.models import Pedido, ItemPedido, Produto, Usuario
from core.presentation.web.views import DetalhePedidoView


@pytest.mark.django_db
class TestDetalhePedidoListaCorrida:
    """Testes da view detalhe_pedido com lista corrida."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup que roda antes de cada teste."""
        # Criar usuário vendedor
        self.vendedor = Usuario.objects.create(
            numero_login="001",
            nome="Vendedor Teste",
            tipo="VENDEDOR",
            ativo=True
        )
        self.vendedor.set_password("1234")
        self.vendedor.save()

        # Criar usuário separador (para sessão)
        self.separador = Usuario.objects.create(
            numero_login="002",
            nome="Separador Teste",
            tipo="SEPARADOR",
            ativo=True
        )

        # Criar pedido
        self.pedido = Pedido.objects.create(
            numero_orcamento="ORD-001",
            codigo_cliente="CLI-001",
            nome_cliente="Cliente Teste",
            vendedor=self.vendedor,
            logistica="MOTOBOY",
            embalagem="CAIXA",
            status="EM_SEPARACAO"
        )

        # Criar produtos
        self.produto_a = Produto.objects.create(
            codigo='PROD-A',
            descricao='Produto A',
            quantidade=10,
            valor_unitario=100.00,
            valor_total=1000.00
        )
        self.produto_b = Produto.objects.create(
            codigo='PROD-B',
            descricao='Produto B',
            quantidade=10,
            valor_unitario=100.00,
            valor_total=1000.00
        )
        self.produto_c = Produto.objects.create(
            codigo='PROD-C',
            descricao='Produto C',
            quantidade=10,
            valor_unitario=100.00,
            valor_total=1000.00
        )

        self.factory = RequestFactory()

    def _login_client(self):
        """Helper para fazer login no client."""
        client = Client()
        # Forçar login (bypass do decorator de autenticação)
        client.force_login(self.separador)
        # Também adicionar na sessão para compatibilidade
        session = client.session
        session['usuario_id'] = self.separador.id
        session['nome'] = self.separador.nome
        session['tipo'] = self.separador.tipo
        session.save()
        return client

    def test_view_retorna_lista_unica(self):
        """View deve retornar 'itens' como lista única ordenada."""
        # Criar itens com estados diferentes
        ItemPedido.objects.create(
            pedido=self.pedido,
            produto=self.produto_a,
            quantidade_solicitada=1,
            separado=False
        )
        ItemPedido.objects.create(
            pedido=self.pedido,
            produto=self.produto_b,
            quantidade_solicitada=1,
            separado=True,
            separado_por=self.separador,
            separado_em=timezone.now()
        )

        # Chamar view via client
        client = self._login_client()
        url = reverse('detalhe_pedido', kwargs={'pedido_id': self.pedido.id})
        response = client.get(url)

        # Validar que context contém 'itens'
        assert response.status_code == 200
        assert 'itens' in response.context

        # Validar que é uma lista
        itens = response.context['itens']
        assert isinstance(itens, list)
        assert len(itens) == 2

    def test_view_nao_retorna_itens_separados_e_nao_separados(self):
        """View NÃO deve retornar 'itens_separados' nem 'itens_nao_separados'."""
        # Criar itens
        ItemPedido.objects.create(
            pedido=self.pedido,
            produto=self.produto_a,
            quantidade_solicitada=1,
            separado=False
        )
        ItemPedido.objects.create(
            pedido=self.pedido,
            produto=self.produto_b,
            quantidade_solicitada=1,
            separado=True,
            separado_por=self.separador,
            separado_em=timezone.now()
        )

        # Chamar view via client
        client = self._login_client()
        url = reverse('detalhe_pedido', kwargs={'pedido_id': self.pedido.id})
        response = client.get(url)

        # Validar que NÃO existem chaves antigas
        assert 'itens_separados' not in response.context
        assert 'itens_nao_separados' not in response.context

    def test_context_contem_apenas_itens(self):
        """Context deve conter apenas 'itens', sem separação por estado."""
        # Criar itens: aguardando, compra, substituído, separado
        ItemPedido.objects.create(
            pedido=self.pedido,
            produto=self.produto_a,
            quantidade_solicitada=1,
            separado=False
        )
        ItemPedido.objects.create(
            pedido=self.pedido,
            produto=self.produto_b,
            quantidade_solicitada=1,
            separado=False,
            em_compra=True,
            enviado_para_compra_por=self.separador,
            enviado_para_compra_em=timezone.now()
        )
        ItemPedido.objects.create(
            pedido=self.pedido,
            produto=self.produto_c,
            quantidade_solicitada=1,
            separado=True,
            separado_por=self.separador,
            separado_em=timezone.now()
        )

        # Chamar view via client
        client = self._login_client()
        url = reverse('detalhe_pedido', kwargs={'pedido_id': self.pedido.id})
        response = client.get(url)

        # Validar estrutura do context
        assert 'itens' in response.context
        assert len(response.context['itens']) == 3

        # Validar que ainda existem outras chaves necessárias
        assert 'pedido' in response.context
        assert 'progresso_percentual' in response.context
        assert 'tempo_decorrido_minutos' in response.context

    def test_itens_retornados_estao_ordenados(self):
        """Itens devem estar ordenados por estado (aguardando, compra, substituído, separado)."""
        # Criar itens em ordem aleatória, mas esperando ordem específica
        # C - Separado
        ItemPedido.objects.create(
            pedido=self.pedido,
            produto=self.produto_c,
            quantidade_solicitada=1,
            separado=True,
            separado_por=self.separador,
            separado_em=timezone.now()
        )
        # A - Aguardando
        ItemPedido.objects.create(
            pedido=self.pedido,
            produto=self.produto_a,
            quantidade_solicitada=1,
            separado=False
        )
        # B - Compra
        ItemPedido.objects.create(
            pedido=self.pedido,
            produto=self.produto_b,
            quantidade_solicitada=1,
            separado=False,
            em_compra=True,
            enviado_para_compra_por=self.separador,
            enviado_para_compra_em=timezone.now()
        )

        # Chamar view via client
        client = self._login_client()
        url = reverse('detalhe_pedido', kwargs={'pedido_id': self.pedido.id})
        response = client.get(url)

        # Validar ordem: A (aguardando), B (compra), C (separado)
        itens = response.context['itens']
        assert len(itens) == 3
        assert itens[0].produto.codigo == 'PROD-A'  # Aguardando
        assert itens[1].produto.codigo == 'PROD-B'  # Compra
        assert itens[2].produto.codigo == 'PROD-C'  # Separado

    def test_progresso_calculado_corretamente(self):
        """Progresso deve ser calculado corretamente mesmo com lista única."""
        # Criar 4 itens: 1 separado, 3 não separados
        ItemPedido.objects.create(
            pedido=self.pedido,
            produto=self.produto_a,
            quantidade_solicitada=1,
            separado=True,
            separado_por=self.separador,
            separado_em=timezone.now()
        )
        for _ in range(3):
            ItemPedido.objects.create(
                pedido=self.pedido,
                produto=Produto.objects.create(
                    codigo=f'PROD-{_}',
                    descricao=f'Produto {_}',
                    quantidade=10,
                    valor_unitario=100.00,
                    valor_total=1000.00
                ),
                quantidade_solicitada=1,
                separado=False
            )

        # Chamar view via client
        client = self._login_client()
        url = reverse('detalhe_pedido', kwargs={'pedido_id': self.pedido.id})
        response = client.get(url)

        # Validar progresso: 1/4 = 25%
        assert response.context['progresso_percentual'] == 25

    def test_pedido_vazio_retorna_lista_vazia(self):
        """Pedido sem itens deve retornar lista vazia."""
        # Não criar nenhum item

        # Chamar view via client
        client = self._login_client()
        url = reverse('detalhe_pedido', kwargs={'pedido_id': self.pedido.id})
        response = client.get(url)

        # Validar lista vazia
        assert response.context['itens'] == []
        assert response.context['progresso_percentual'] == 0
