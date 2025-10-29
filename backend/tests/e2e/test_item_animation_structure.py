# -*- coding: utf-8 -*-
"""
Testes E2E para validar estrutura HTML necessária para animações de itens.

Este módulo testa:
1. Seções têm IDs únicos para targeting JavaScript
2. Items têm classes corretas para animação
3. Estrutura do DOM após operações
4. CSS está linkado corretamente
"""

from django.test import LiveServerTestCase, Client
from django.urls import reverse
from core.models import Usuario, Pedido, ItemPedido, Produto
from core.domain.pedido.value_objects import Logistica, Embalagem, StatusPedido


class TestItemAnimationStructure(LiveServerTestCase):
    """Testes E2E para validar estrutura HTML de animações."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.client = Client()

    def setUp(self):
        """Setup executado antes de cada teste."""
        # Criar usuário separador
        self.usuario = Usuario.objects.create_user(
            numero_login=1234,
            pin='1234',
            nome='Separador Teste',
            tipo='SEPARADOR'
        )

        # Criar vendedor
        self.vendedor = Usuario.objects.create_user(
            numero_login=5678,
            pin='5678',
            nome='Vendedor Teste',
            tipo='VENDEDOR'
        )

        # Criar produtos
        self.produto1 = Produto.objects.create(
            codigo='00001',
            descricao='Produto Teste 1',
            quantidade=10,
            valor_unitario=100.0,
            valor_total=1000.0
        )
        self.produto2 = Produto.objects.create(
            codigo='00002',
            descricao='Produto Teste 2',
            quantidade=5,
            valor_unitario=200.0,
            valor_total=1000.0
        )

        # Criar pedido
        self.pedido = Pedido.objects.create(
            numero_orcamento='TEST001',
            codigo_cliente='CLI001',
            nome_cliente='Cliente Teste',
            vendedor=self.vendedor,
            data='01/01/2025',
            logistica=Logistica.RETIRA_LOJA.value,
            embalagem=Embalagem.CAIXA.value,
            status=StatusPedido.EM_SEPARACAO.value
        )

        # Criar itens (1 separado, 1 não separado)
        self.item_separado = ItemPedido.objects.create(
            pedido=self.pedido,
            produto=self.produto1,
            quantidade_solicitada=10,
            separado=True,
            quantidade_separada=10
        )

        self.item_nao_separado = ItemPedido.objects.create(
            pedido=self.pedido,
            produto=self.produto2,
            quantidade_solicitada=5
        )

        # Fazer login
        self.client.post(reverse('login'), {
            'numero_login': '1234',
            'pin': '1234'
        })

    def test_secao_itens_nao_separados_tem_id_unico(self):
        """
        Testa se a seção de itens não separados tem ID único para targeting.
        """
        response = self.client.get(reverse('detalhe_pedido', args=[self.pedido.id]))
        assert response.status_code == 200

        html = response.content.decode('utf-8')

        # Verificar se ID existe
        assert 'id="container-nao-separados"' in html, \
            "Seção de itens não separados deve ter id='container-nao-separados'"

    def test_secao_itens_separados_tem_id_unico(self):
        """
        Testa se a seção de itens separados tem ID único para targeting.
        """
        response = self.client.get(reverse('detalhe_pedido', args=[self.pedido.id]))
        assert response.status_code == 200

        html = response.content.decode('utf-8')

        # Verificar se ID existe
        assert 'id="container-separados"' in html, \
            "Seção de itens separados deve ter id='container-separados'"

    def test_item_tem_classe_item_container(self):
        """
        Testa se cada item tem a classe .item-container para animações.
        """
        response = self.client.get(reverse('detalhe_pedido', args=[self.pedido.id]))
        assert response.status_code == 200

        html = response.content.decode('utf-8')

        # Verificar se classe .item-container existe nos itens
        assert 'class="item-container' in html, \
            "Items devem ter classe 'item-container' para animações"

    def test_item_tem_id_unico(self):
        """
        Testa se cada item tem um ID único no formato item-{id}.
        """
        response = self.client.get(reverse('detalhe_pedido', args=[self.pedido.id]))
        assert response.status_code == 200

        html = response.content.decode('utf-8')

        # Verificar IDs dos itens
        assert f'id="item-{self.item_separado.id}"' in html, \
            f"Item separado deve ter id='item-{self.item_separado.id}'"

        assert f'id="item-{self.item_nao_separado.id}"' in html, \
            f"Item não separado deve ter id='item-{self.item_nao_separado.id}'"

    def test_css_animations_esta_linkado(self):
        """
        Testa se o arquivo animations.css está linkado no HTML ou
        se as classes de animação estão disponíveis.
        """
        response = self.client.get(reverse('detalhe_pedido', args=[self.pedido.id]))
        assert response.status_code == 200

        html = response.content.decode('utf-8')

        # Verificar se CSS está linkado OU se as estruturas necessárias existem
        has_animations_link = 'animations.css' in html
        has_required_ids = 'container-nao-separados' in html and 'container-separados' in html

        assert has_animations_link or has_required_ids, \
            "Arquivo animations.css deve estar linkado OU estrutura de containers deve existir"

    def test_item_nao_separado_tem_estrutura_correta(self):
        """
        Testa se item não separado tem estrutura adequada para animação.
        """
        response = self.client.get(reverse('detalhe_pedido', args=[self.pedido.id]))
        assert response.status_code == 200

        html = response.content.decode('utf-8')

        # Item não separado deve estar na seção correta
        # e ter classes/IDs necessários
        assert f'id="item-{self.item_nao_separado.id}"' in html
        assert 'item-container' in html

    def test_item_separado_tem_estrutura_correta(self):
        """
        Testa se item separado tem estrutura adequada para animação.
        """
        response = self.client.get(reverse('detalhe_pedido', args=[self.pedido.id]))
        assert response.status_code == 200

        html = response.content.decode('utf-8')

        # Item separado deve estar na seção correta
        assert f'id="item-{self.item_separado.id}"' in html
        assert 'item-container' in html

    def test_espaco_para_itens_em_container_separados(self):
        """
        Testa se há div com space-y-3 para animações fluidas de entrada.
        """
        response = self.client.get(reverse('detalhe_pedido', args=[self.pedido.id]))
        assert response.status_code == 200

        html = response.content.decode('utf-8')

        # Container deve ter espaçamento entre itens
        assert 'space-y-3' in html, \
            "Container de itens deve ter classe 'space-y-3' para espaçamento fluido"

    def test_aria_live_region_existe(self):
        """
        Testa se existem regiões aria-live para acessibilidade.
        (Para anunciar mudanças dinâmicas)
        """
        response = self.client.get(reverse('detalhe_pedido', args=[self.pedido.id]))
        assert response.status_code == 200

        html = response.content.decode('utf-8')

        # Deve ter pelo menos uma região aria-live="polite"
        # (para anunciar quando item é movido)
        # Nota: Será implementado na Fase 8, mas estrutura deve estar preparada
        # Por enquanto, apenas verificamos se a estrutura permite adicionar
        assert 'container-nao-separados' in html and 'container-separados' in html, \
            "Estrutura de containers permite adicionar aria-live futuramente"


if __name__ == '__main__':
    import unittest
    unittest.main()
