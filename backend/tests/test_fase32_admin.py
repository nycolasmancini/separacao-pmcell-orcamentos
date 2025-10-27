# -*- coding: utf-8 -*-
"""
Testes para Fase 32: Implementar Sistema de Admin Django
TDD: RED → GREEN → REFACTOR

Este módulo testa a funcionalidade do Django Admin:
- Acesso restrito apenas para admins
- CRUD funcional para todos os modelos
- List views com campos corretos
- Filtros e busca funcionando
- Ações em lote
- Inlines de ItemPedido no Pedido
"""

import pytest
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from decimal import Decimal

from core.models import Pedido, ItemPedido, Usuario, Produto


Usuario = get_user_model()


class TestFase32AdminAccess(TestCase):
    """
    Testes de controle de acesso ao Django Admin.

    Cobertura:
    1. Admin acessível para usuários admin
    2. Usuários não-admin são bloqueados
    3. Redirecionamento de login funciona
    """

    def setUp(self):
        """Setup para cada teste."""
        self.client = Client()

        # Criar usuário admin
        self.admin = Usuario.objects.create_user(
            numero_login="9999",
            pin="9999",
            nome="Admin Master",
            tipo="ADMINISTRADOR"
        )
        self.admin.is_admin = True
        self.admin.save()

        # Criar usuário regular (não-admin)
        self.separador = Usuario.objects.create_user(
            numero_login="1001",
            pin="1234",
            nome="João Separador",
            tipo="SEPARADOR"
        )

    def test_admin_acessivel_para_usuarios_admin(self):
        """Testa que usuários admin podem acessar o admin."""
        self.client.force_login(self.admin)
        response = self.client.get('/admin/')

        assert response.status_code == 200
        # Verificar que admin está acessível através de elementos presentes na página
        content = response.content.decode('utf-8')
        assert 'site-name' in content or 'Administração' in content

    def test_usuarios_nao_admin_sao_bloqueados(self):
        """Testa que usuários não-admin não podem acessar o admin."""
        self.client.force_login(self.separador)
        response = self.client.get('/admin/')

        # Deve redirecionar para login do admin ou retornar 403/302
        assert response.status_code in [302, 403]

    def test_usuarios_anonimos_redirecionados_para_login(self):
        """Testa que usuários não autenticados são redirecionados."""
        response = self.client.get('/admin/')

        assert response.status_code == 302
        assert '/admin/login/' in response.url


class TestFase32UsuarioAdmin(TestCase):
    """
    Testes para UsuarioAdmin no Django Admin.

    Cobertura:
    1. List view exibe campos corretos
    2. Filtros funcionam (tipo, ativo, is_admin)
    3. Busca funciona (numero_login, nome)
    4. CRUD funcional
    """

    def setUp(self):
        """Setup para cada teste."""
        self.client = Client()

        # Criar usuário admin
        self.admin = Usuario.objects.create_user(
            numero_login="9999",
            pin="9999",
            nome="Admin Master",
            tipo="ADMINISTRADOR"
        )
        self.admin.is_admin = True
        self.admin.save()

        self.client.force_login(self.admin)

        # Criar usuários de teste
        Usuario.objects.create_user(
            numero_login="1001",
            pin="1234",
            nome="Maria Vendedora",
            tipo="VENDEDOR"
        )
        Usuario.objects.create_user(
            numero_login="2001",
            pin="2345",
            nome="João Separador",
            tipo="SEPARADOR"
        )

    def test_usuario_admin_listview_exibe_campos_corretos(self):
        """Testa que list view de Usuario exibe campos corretos."""
        response = self.client.get('/admin/core/usuario/')

        assert response.status_code == 200
        # Verificar que campos aparecem na tabela
        content = response.content.decode('utf-8')
        assert 'numero_login' in content.lower() or 'número' in content.lower()
        assert 'Maria Vendedora' in content
        assert 'João Separador' in content

    def test_usuario_admin_busca_por_nome(self):
        """Testa que busca por nome funciona."""
        response = self.client.get('/admin/core/usuario/?q=Maria')

        assert response.status_code == 200
        assert 'Maria Vendedora' in str(response.content)
        assert 'João Separador' not in str(response.content)

    def test_usuario_admin_busca_por_numero_login(self):
        """Testa que busca por numero_login funciona."""
        response = self.client.get('/admin/core/usuario/?q=1001')

        assert response.status_code == 200
        assert 'Maria Vendedora' in str(response.content)

    def test_usuario_admin_filtro_por_tipo(self):
        """Testa que filtro por tipo funciona."""
        response = self.client.get('/admin/core/usuario/?tipo=VENDEDOR')

        assert response.status_code == 200
        assert 'Maria Vendedora' in str(response.content)


class TestFase32ProdutoAdmin(TestCase):
    """
    Testes para ProdutoAdmin no Django Admin.

    Cobertura:
    1. List view exibe campos corretos
    2. Busca funciona (codigo, descricao)
    3. CRUD funcional
    """

    def setUp(self):
        """Setup para cada teste."""
        self.client = Client()

        # Criar usuário admin
        self.admin = Usuario.objects.create_user(
            numero_login="9999",
            pin="9999",
            nome="Admin Master",
            tipo="ADMINISTRADOR"
        )
        self.admin.is_admin = True
        self.admin.save()

        self.client.force_login(self.admin)

        # Criar produtos de teste
        Produto.objects.create(
            codigo="00010",
            descricao="CABO USB TIPO-C",
            quantidade=10,
            valor_unitario=Decimal("15.00"),
            valor_total=Decimal("150.00")
        )
        Produto.objects.create(
            codigo="00020",
            descricao="FONE DE OUVIDO",
            quantidade=5,
            valor_unitario=Decimal("25.00"),
            valor_total=Decimal("125.00")
        )

    def test_produto_admin_listview_exibe_campos_corretos(self):
        """Testa que list view de Produto exibe campos corretos."""
        response = self.client.get('/admin/core/produto/')

        assert response.status_code == 200
        content = str(response.content)
        assert '00010' in content
        assert 'CABO USB TIPO-C' in content
        assert '00020' in content
        assert 'FONE DE OUVIDO' in content

    def test_produto_admin_busca_por_codigo(self):
        """Testa que busca por codigo funciona."""
        response = self.client.get('/admin/core/produto/?q=00010')

        assert response.status_code == 200
        assert 'CABO USB TIPO-C' in str(response.content)
        assert 'FONE DE OUVIDO' not in str(response.content)

    def test_produto_admin_busca_por_descricao(self):
        """Testa que busca por descricao funciona."""
        response = self.client.get('/admin/core/produto/?q=CABO')

        assert response.status_code == 200
        assert 'CABO USB TIPO-C' in str(response.content)


class TestFase32PedidoAdmin(TestCase):
    """
    Testes para PedidoAdmin no Django Admin.

    Cobertura:
    1. List view exibe campos corretos
    2. Filtros funcionam (status, logistica, vendedor)
    3. Busca funciona (numero_orcamento, nome_cliente)
    4. Inline de ItemPedido aparece
    5. Ação em lote: finalizar múltiplos pedidos
    """

    def setUp(self):
        """Setup para cada teste."""
        self.client = Client()

        # Criar usuário admin
        self.admin = Usuario.objects.create_user(
            numero_login="9999",
            pin="9999",
            nome="Admin Master",
            tipo="ADMINISTRADOR"
        )
        self.admin.is_admin = True
        self.admin.save()

        self.client.force_login(self.admin)

        # Criar vendedor
        self.vendedor = Usuario.objects.create_user(
            numero_login="2001",
            pin="2345",
            nome="Maria Vendedora",
            tipo="VENDEDOR"
        )

        # Criar produtos
        self.produto1 = Produto.objects.create(
            codigo="00010",
            descricao="CABO USB TIPO-C",
            quantidade=10,
            valor_unitario=Decimal("15.00"),
            valor_total=Decimal("150.00")
        )

        # Criar pedidos
        self.pedido1 = Pedido.objects.create(
            numero_orcamento="30567",
            codigo_cliente="CLI001",
            nome_cliente="João Silva",
            vendedor=self.vendedor,
            data="25/10/2025",
            logistica="CORREIOS",
            embalagem="CAIXA",
            status="EM_SEPARACAO"
        )

        self.pedido2 = Pedido.objects.create(
            numero_orcamento="30568",
            codigo_cliente="CLI002",
            nome_cliente="Maria Santos",
            vendedor=self.vendedor,
            data="26/10/2025",
            logistica="MOTOBOY",
            embalagem="SACOLA",
            status="FINALIZADO"
        )

        # Criar itens
        ItemPedido.objects.create(
            pedido=self.pedido1,
            produto=self.produto1,
            quantidade_solicitada=5,
            quantidade_separada=0
        )

    def test_pedido_admin_listview_exibe_campos_corretos(self):
        """Testa que list view de Pedido exibe campos corretos."""
        response = self.client.get('/admin/core/pedido/')

        assert response.status_code == 200
        content = response.content.decode('utf-8')
        assert '30567' in content
        assert 'João Silva' in content
        assert '30568' in content
        assert 'Maria Santos' in content

    def test_pedido_admin_busca_por_numero_orcamento(self):
        """Testa que busca por numero_orcamento funciona."""
        response = self.client.get('/admin/core/pedido/?q=30567')

        assert response.status_code == 200
        content = response.content.decode('utf-8')
        assert 'João Silva' in content
        assert 'Maria Santos' not in content

    def test_pedido_admin_busca_por_nome_cliente(self):
        """Testa que busca por nome_cliente funciona."""
        response = self.client.get('/admin/core/pedido/?q=Maria+Santos')

        assert response.status_code == 200
        assert 'Maria Santos' in str(response.content)

    def test_pedido_admin_filtro_por_status(self):
        """Testa que filtro por status funciona."""
        response = self.client.get('/admin/core/pedido/?status=FINALIZADO')

        assert response.status_code == 200
        assert 'Maria Santos' in str(response.content)

    def test_pedido_admin_inline_itempedido_aparece(self):
        """Testa que inline de ItemPedido aparece no form do Pedido."""
        response = self.client.get(f'/admin/core/pedido/{self.pedido1.id}/change/')

        assert response.status_code == 200
        content = str(response.content)
        # Deve mostrar o produto inline
        assert 'CABO USB TIPO-C' in content or 'produto' in content.lower()

    def test_pedido_admin_acao_finalizar_multiplos_pedidos(self):
        """Testa ação em lote para finalizar múltiplos pedidos."""
        # Criar mais pedidos em separação
        pedido3 = Pedido.objects.create(
            numero_orcamento="30569",
            codigo_cliente="CLI003",
            nome_cliente="Pedro Costa",
            vendedor=self.vendedor,
            data="27/10/2025",
            logistica="CORREIOS",
            embalagem="CAIXA",
            status="EM_SEPARACAO"
        )

        # Executar ação em lote
        response = self.client.post(
            '/admin/core/pedido/',
            data={
                'action': 'finalizar_pedidos',
                '_selected_action': [str(self.pedido1.id), str(pedido3.id)]
            },
            follow=True
        )

        # Verificar que pedidos foram finalizados
        self.pedido1.refresh_from_db()
        pedido3.refresh_from_db()

        assert self.pedido1.status == 'FINALIZADO'
        assert pedido3.status == 'FINALIZADO'


class TestFase32ItemPedidoAdmin(TestCase):
    """
    Testes para ItemPedidoAdmin no Django Admin.

    Cobertura:
    1. List view exibe campos corretos
    2. Filtros funcionam (separado, em_compra, pedido_realizado)
    3. Busca funciona
    """

    def setUp(self):
        """Setup para cada teste."""
        self.client = Client()

        # Criar usuário admin
        self.admin = Usuario.objects.create_user(
            numero_login="9999",
            pin="9999",
            nome="Admin Master",
            tipo="ADMINISTRADOR"
        )
        self.admin.is_admin = True
        self.admin.save()

        self.client.force_login(self.admin)

        # Criar dados de teste
        vendedor = Usuario.objects.create_user(
            numero_login="2001",
            pin="2345",
            nome="Maria Vendedora",
            tipo="VENDEDOR"
        )

        produto1 = Produto.objects.create(
            codigo="00010",
            descricao="CABO USB TIPO-C",
            quantidade=10,
            valor_unitario=Decimal("15.00"),
            valor_total=Decimal("150.00")
        )

        produto2 = Produto.objects.create(
            codigo="00020",
            descricao="FONE DE OUVIDO",
            quantidade=5,
            valor_unitario=Decimal("25.00"),
            valor_total=Decimal("125.00")
        )

        pedido = Pedido.objects.create(
            numero_orcamento="30567",
            codigo_cliente="CLI001",
            nome_cliente="João Silva",
            vendedor=vendedor,
            data="25/10/2025",
            logistica="CORREIOS",
            embalagem="CAIXA",
            status="EM_SEPARACAO"
        )

        # Criar itens com estados diferentes
        self.item1 = ItemPedido.objects.create(
            pedido=pedido,
            produto=produto1,
            quantidade_solicitada=5,
            quantidade_separada=5,
            separado=True
        )

        self.item2 = ItemPedido.objects.create(
            pedido=pedido,
            produto=produto2,
            quantidade_solicitada=3,
            quantidade_separada=0,
            em_compra=True
        )

    def test_itempedido_admin_listview_exibe_campos_corretos(self):
        """Testa que list view de ItemPedido exibe campos corretos."""
        response = self.client.get('/admin/core/itempedido/')

        assert response.status_code == 200
        content = str(response.content)
        assert '30567' in content
        assert 'CABO USB TIPO-C' in content

    def test_itempedido_admin_filtro_por_separado(self):
        """Testa que filtro por separado funciona."""
        response = self.client.get('/admin/core/itempedido/?separado=1')

        assert response.status_code == 200
        content = str(response.content)
        assert 'CABO USB TIPO-C' in content

    def test_itempedido_admin_filtro_por_em_compra(self):
        """Testa que filtro por em_compra funciona."""
        response = self.client.get('/admin/core/itempedido/?em_compra=1')

        assert response.status_code == 200
        content = str(response.content)
        assert 'FONE DE OUVIDO' in content

    def test_itempedido_admin_busca_por_pedido(self):
        """Testa que busca por numero do pedido funciona."""
        response = self.client.get('/admin/core/itempedido/?q=30567')

        assert response.status_code == 200
        assert '30567' in str(response.content)
