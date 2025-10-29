# -*- coding: utf-8 -*-
"""
Testes para ordenação de itens em lista corrida (Fase 39a).

Testa a lógica de ordenação que agrupa itens por estado:
1. Aguardando separação (ordem alfabética)
2. Enviados para compras (alfabética)
3. Substituídos (alfabética)
4. Separados (alfabética)
"""

import pytest
from datetime import datetime
from django.utils import timezone
from core.models import Pedido, ItemPedido, Produto, Usuario
from core.infrastructure.persistence.repositories.pedido_repository import DjangoPedidoRepository


@pytest.mark.django_db
class TestOrdenacaoListaCorrida:
    """Testes de ordenação de itens em lista corrida."""

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

        # Criar usuário separador
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
        self.produtos = {
            'A': Produto.objects.create(
                codigo='PROD-A', descricao='Produto A',
                quantidade=10, valor_unitario=100.00, valor_total=1000.00
            ),
            'B': Produto.objects.create(
                codigo='PROD-B', descricao='Produto B',
                quantidade=10, valor_unitario=100.00, valor_total=1000.00
            ),
            'C': Produto.objects.create(
                codigo='PROD-C', descricao='Produto C',
                quantidade=10, valor_unitario=100.00, valor_total=1000.00
            ),
            'D': Produto.objects.create(
                codigo='PROD-D', descricao='Produto D',
                quantidade=10, valor_unitario=100.00, valor_total=1000.00
            ),
            'E': Produto.objects.create(
                codigo='PROD-E', descricao='Produto E',
                quantidade=10, valor_unitario=100.00, valor_total=1000.00
            ),
            'F': Produto.objects.create(
                codigo='PROD-F', descricao='Produto F',
                quantidade=10, valor_unitario=100.00, valor_total=1000.00
            ),
            'G': Produto.objects.create(
                codigo='PROD-G', descricao='Produto G',
                quantidade=10, valor_unitario=100.00, valor_total=1000.00
            ),
            'H': Produto.objects.create(
                codigo='PROD-H', descricao='Produto H',
                quantidade=10, valor_unitario=100.00, valor_total=1000.00
            ),
        }

        self.repository = DjangoPedidoRepository()

    def test_itens_ordenados_aguardando_primeiro(self):
        """Itens aguardando separação devem aparecer primeiro (ordem alfabética)."""
        # Criar itens: 2 aguardando, 1 separado
        ItemPedido.objects.create(
            pedido=self.pedido,
            produto=self.produtos['C'],
            quantidade_solicitada=1,
            separado=False
        )
        ItemPedido.objects.create(
            pedido=self.pedido,
            produto=self.produtos['A'],
            quantidade_solicitada=1,
            separado=False
        )
        ItemPedido.objects.create(
            pedido=self.pedido,
            produto=self.produtos['B'],
            quantidade_solicitada=1,
            separado=True,
            separado_por=self.separador,
            separado_em=timezone.now()
        )

        # Buscar itens ordenados
        itens = self.repository.obter_itens_ordenados_por_estado(self.pedido.id)

        # Validar ordem: aguardando (A, C) antes de separado (B)
        assert len(itens) == 3
        assert itens[0].produto.codigo == 'PROD-A'  # Aguardando (alfabética)
        assert itens[1].produto.codigo == 'PROD-C'  # Aguardando (alfabética)
        assert itens[2].produto.codigo == 'PROD-B'  # Separado

    def test_itens_ordenados_compras_segundo(self):
        """Itens enviados para compras devem aparecer depois de aguardando."""
        # Criar itens: aguardando, compra, separado
        ItemPedido.objects.create(
            pedido=self.pedido,
            produto=self.produtos['B'],
            quantidade_solicitada=1,
            separado=False,
            em_compra=False
        )
        ItemPedido.objects.create(
            pedido=self.pedido,
            produto=self.produtos['D'],
            quantidade_solicitada=1,
            separado=False,
            em_compra=True,
            enviado_para_compra_por=self.separador,
            enviado_para_compra_em=timezone.now()
        )
        ItemPedido.objects.create(
            pedido=self.pedido,
            produto=self.produtos['A'],
            quantidade_solicitada=1,
            separado=True,
            separado_por=self.separador,
            separado_em=timezone.now()
        )

        # Buscar itens ordenados
        itens = self.repository.obter_itens_ordenados_por_estado(self.pedido.id)

        # Validar ordem: aguardando (B), compra (D), separado (A)
        assert len(itens) == 3
        assert itens[0].produto.codigo == 'PROD-B'  # Aguardando
        assert itens[1].produto.codigo == 'PROD-D'  # Em compra
        assert itens[2].produto.codigo == 'PROD-A'  # Separado

    def test_itens_ordenados_substituidos_terceiro(self):
        """Itens substituídos devem aparecer depois de compras e antes de separados."""
        # Criar itens: aguardando, compra, substituído, separado
        ItemPedido.objects.create(
            pedido=self.pedido,
            produto=self.produtos['C'],
            quantidade_solicitada=1,
            separado=False
        )
        ItemPedido.objects.create(
            pedido=self.pedido,
            produto=self.produtos['B'],
            quantidade_solicitada=1,
            separado=False,
            em_compra=True,
            enviado_para_compra_por=self.separador,
            enviado_para_compra_em=timezone.now()
        )
        ItemPedido.objects.create(
            pedido=self.pedido,
            produto=self.produtos['D'],
            quantidade_solicitada=1,
            separado=True,
            substituido=True,
            produto_substituto="Produto Substituto D",
            separado_por=self.separador,
            separado_em=timezone.now()
        )
        ItemPedido.objects.create(
            pedido=self.pedido,
            produto=self.produtos['A'],
            quantidade_solicitada=1,
            separado=True,
            separado_por=self.separador,
            separado_em=timezone.now()
        )

        # Buscar itens ordenados
        itens = self.repository.obter_itens_ordenados_por_estado(self.pedido.id)

        # Validar ordem: aguardando (C), compra (B), substituído (D), separado (A)
        assert len(itens) == 4
        assert itens[0].produto.codigo == 'PROD-C'  # Aguardando
        assert itens[1].produto.codigo == 'PROD-B'  # Em compra
        assert itens[2].produto.codigo == 'PROD-D'  # Substituído
        assert itens[3].produto.codigo == 'PROD-A'  # Separado (não substituído)

    def test_itens_ordenados_separados_quarto(self):
        """Itens separados (não substituídos) devem aparecer por último."""
        # Criar itens: separados não substituídos
        ItemPedido.objects.create(
            pedido=self.pedido,
            produto=self.produtos['C'],
            quantidade_solicitada=1,
            separado=True,
            separado_por=self.separador,
            separado_em=timezone.now()
        )
        ItemPedido.objects.create(
            pedido=self.pedido,
            produto=self.produtos['A'],
            quantidade_solicitada=1,
            separado=True,
            separado_por=self.separador,
            separado_em=timezone.now()
        )

        # Buscar itens ordenados
        itens = self.repository.obter_itens_ordenados_por_estado(self.pedido.id)

        # Validar ordem alfabética dentro de separados
        assert len(itens) == 2
        assert itens[0].produto.codigo == 'PROD-A'
        assert itens[1].produto.codigo == 'PROD-C'

    def test_ordenacao_alfabetica_dentro_grupo(self):
        """Dentro de cada grupo, itens devem estar ordenados alfabeticamente."""
        # Criar 2 de cada estado
        # Aguardando: E, B
        ItemPedido.objects.create(
            pedido=self.pedido,
            produto=self.produtos['E'],
            quantidade_solicitada=1
        )
        ItemPedido.objects.create(
            pedido=self.pedido,
            produto=self.produtos['B'],
            quantidade_solicitada=1
        )

        # Compras: H, D
        ItemPedido.objects.create(
            pedido=self.pedido,
            produto=self.produtos['H'],
            quantidade_solicitada=1,
            em_compra=True,
            enviado_para_compra_por=self.separador,
            enviado_para_compra_em=timezone.now()
        )
        ItemPedido.objects.create(
            pedido=self.pedido,
            produto=self.produtos['D'],
            quantidade_solicitada=1,
            em_compra=True,
            enviado_para_compra_por=self.separador,
            enviado_para_compra_em=timezone.now()
        )

        # Substituídos: G, C
        ItemPedido.objects.create(
            pedido=self.pedido,
            produto=self.produtos['G'],
            quantidade_solicitada=1,
            separado=True,
            substituido=True,
            produto_substituto="Substituto G",
            separado_por=self.separador,
            separado_em=timezone.now()
        )
        ItemPedido.objects.create(
            pedido=self.pedido,
            produto=self.produtos['C'],
            quantidade_solicitada=1,
            separado=True,
            substituido=True,
            produto_substituto="Substituto C",
            separado_por=self.separador,
            separado_em=timezone.now()
        )

        # Separados: F, A
        ItemPedido.objects.create(
            pedido=self.pedido,
            produto=self.produtos['F'],
            quantidade_solicitada=1,
            separado=True,
            separado_por=self.separador,
            separado_em=timezone.now()
        )
        ItemPedido.objects.create(
            pedido=self.pedido,
            produto=self.produtos['A'],
            quantidade_solicitada=1,
            separado=True,
            separado_por=self.separador,
            separado_em=timezone.now()
        )

        # Buscar itens ordenados
        itens = self.repository.obter_itens_ordenados_por_estado(self.pedido.id)

        # Validar ordem completa
        assert len(itens) == 8
        codigos = [item.produto.codigo for item in itens]

        # Aguardando (B, E)
        assert codigos[0] == 'PROD-B'
        assert codigos[1] == 'PROD-E'

        # Compras (D, H)
        assert codigos[2] == 'PROD-D'
        assert codigos[3] == 'PROD-H'

        # Substituídos (C, G)
        assert codigos[4] == 'PROD-C'
        assert codigos[5] == 'PROD-G'

        # Separados (A, F)
        assert codigos[6] == 'PROD-A'
        assert codigos[7] == 'PROD-F'

    def test_ordenacao_mixto_completo(self):
        """Teste completo com todos os estados e validação da ordem."""
        # Criar cenário realista
        itens_data = [
            ('B', False, False, False),  # Aguardando
            ('A', False, False, False),  # Aguardando
            ('D', False, True, False),   # Compra
            ('C', False, True, False),   # Compra
            ('F', True, False, True),    # Substituído
            ('E', True, False, True),    # Substituído
            ('H', True, False, False),   # Separado
            ('G', True, False, False),   # Separado
        ]

        for codigo, separado, em_compra, substituido in itens_data:
            item_data = {
                'pedido': self.pedido,
                'produto': self.produtos[codigo],
                'quantidade_solicitada': 1,
                'separado': separado,
                'em_compra': em_compra,
                'substituido': substituido,
            }

            if separado or em_compra:
                item_data['separado_por'] = self.separador
                item_data['separado_em'] = timezone.now()

            if em_compra:
                item_data['enviado_para_compra_por'] = self.separador
                item_data['enviado_para_compra_em'] = timezone.now()

            if substituido:
                item_data['produto_substituto'] = f"Substituto {codigo}"

            ItemPedido.objects.create(**item_data)

        # Buscar itens ordenados
        itens = self.repository.obter_itens_ordenados_por_estado(self.pedido.id)
        codigos = [item.produto.codigo for item in itens]

        # Ordem esperada:
        # Aguardando: A, B
        # Compra: C, D
        # Substituído: E, F
        # Separado: G, H
        ordem_esperada = ['PROD-A', 'PROD-B', 'PROD-C', 'PROD-D',
                          'PROD-E', 'PROD-F', 'PROD-G', 'PROD-H']

        assert codigos == ordem_esperada
