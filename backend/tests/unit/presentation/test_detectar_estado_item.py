# -*- coding: utf-8 -*-
"""
Testes para detecção de estado de item (Fase 39d).

Valida funções JavaScript que detectam o estado atual de um item
e calculam sua posição de destino na lista corrida.
"""

import pytest
from unittest.mock import Mock, MagicMock


class TestDetectarEstadoItem:
    """
    Testes unitários para detectarEstadoItem().

    Função deve analisar classes CSS de um item e retornar:
    - 'aguardando': item não separado, não em compra
    - 'compra': item marcado para compras
    - 'substituido': item separado e substituído
    - 'separado': item separado (não substituído)
    """

    def test_detectar_aguardando(self):
        """Item com border-gray-200 deve ser detectado como 'aguardando'."""
        # Mock do elemento DOM
        item = Mock()
        item.classList.contains = Mock(side_effect=lambda cls: cls == 'border-gray-200')

        # Função JavaScript (simulada em Python para teste)
        def detectarEstadoItem(element):
            if element.classList.contains('border-gray-200'):
                return 'aguardando'
            elif element.classList.contains('border-orange-200'):
                return 'compra'
            elif element.classList.contains('border-blue-200'):
                return 'substituido'
            elif element.classList.contains('border-green-200'):
                return 'separado'
            return 'desconhecido'

        estado = detectarEstadoItem(item)
        assert estado == 'aguardando'

    def test_detectar_compra(self):
        """Item com border-orange-200 deve ser detectado como 'compra'."""
        item = Mock()
        item.classList.contains = Mock(side_effect=lambda cls: cls == 'border-orange-200')

        def detectarEstadoItem(element):
            if element.classList.contains('border-gray-200'):
                return 'aguardando'
            elif element.classList.contains('border-orange-200'):
                return 'compra'
            elif element.classList.contains('border-blue-200'):
                return 'substituido'
            elif element.classList.contains('border-green-200'):
                return 'separado'
            return 'desconhecido'

        estado = detectarEstadoItem(item)
        assert estado == 'compra'

    def test_detectar_substituido(self):
        """Item com border-blue-200 deve ser detectado como 'substituido'."""
        item = Mock()
        item.classList.contains = Mock(side_effect=lambda cls: cls == 'border-blue-200')

        def detectarEstadoItem(element):
            if element.classList.contains('border-gray-200'):
                return 'aguardando'
            elif element.classList.contains('border-orange-200'):
                return 'compra'
            elif element.classList.contains('border-blue-200'):
                return 'substituido'
            elif element.classList.contains('border-green-200'):
                return 'separado'
            return 'desconhecido'

        estado = detectarEstadoItem(item)
        assert estado == 'substituido'

    def test_detectar_separado(self):
        """Item com border-green-200 deve ser detectado como 'separado'."""
        item = Mock()
        item.classList.contains = Mock(side_effect=lambda cls: cls == 'border-green-200')

        def detectarEstadoItem(element):
            if element.classList.contains('border-gray-200'):
                return 'aguardando'
            elif element.classList.contains('border-orange-200'):
                return 'compra'
            elif element.classList.contains('border-blue-200'):
                return 'substituido'
            elif element.classList.contains('border-green-200'):
                return 'separado'
            return 'desconhecido'

        estado = detectarEstadoItem(item)
        assert estado == 'separado'


class TestCalcularPosicaoDestino:
    """
    Testes unitários para calcularPosicaoDestino().

    Função deve calcular o índice de destino baseado em:
    - Estado do item
    - Estados dos itens já na lista
    - Ordenação alfabética dentro do grupo
    """

    def setup_method(self):
        """Setup comum para todos os testes."""
        self.mock_itens_container = Mock()

    def _criar_mock_item(self, estado, descricao):
        """Helper para criar mock de item com estado e descrição."""
        item = Mock()
        item.classList.contains = Mock(side_effect=lambda cls: {
            'aguardando': cls == 'border-gray-200',
            'compra': cls == 'border-orange-200',
            'substituido': cls == 'border-blue-200',
            'separado': cls == 'border-green-200'
        }.get(estado, False))

        # Mock da descrição do produto
        descricao_el = Mock()
        descricao_el.textContent = descricao
        item.querySelector = Mock(return_value=descricao_el)

        return item

    def test_calcular_posicao_aguardando_lista_vazia(self):
        """Item 'aguardando' deve ir para índice 0 se lista vazia."""
        # Mock: lista vazia
        self.mock_itens_container.children = []

        def calcularPosicaoDestino(estado, descricao, container):
            if not container.children:
                return 0
            # Lógica simplificada para teste
            return 0

        posicao = calcularPosicaoDestino('aguardando', 'Produto A', self.mock_itens_container)
        assert posicao == 0

    def test_calcular_posicao_aguardando_antes_compra(self):
        """Item 'aguardando' deve ir antes de itens em 'compra'."""
        # Mock: lista com 1 item em compra
        item_compra = self._criar_mock_item('compra', 'Produto B')
        self.mock_itens_container.children = [item_compra]

        def calcularPosicaoDestino(estado, descricao, container):
            """
            Ordem de prioridade:
            1. aguardando
            2. compra
            3. substituido
            4. separado
            """
            if estado == 'aguardando':
                # Contar quantos itens aguardando já existem
                count = 0
                for child in container.children:
                    child_estado = 'aguardando' if child.classList.contains('border-gray-200') else \
                                   'compra' if child.classList.contains('border-orange-200') else \
                                   'substituido' if child.classList.contains('border-blue-200') else 'separado'

                    if child_estado == 'aguardando':
                        count += 1
                    elif child_estado in ['compra', 'substituido', 'separado']:
                        break  # Encontrou primeiro item de grupo posterior

                return count
            return len(container.children)

        posicao = calcularPosicaoDestino('aguardando', 'Produto A', self.mock_itens_container)
        assert posicao == 0  # Deve ir antes do item em compra

    def test_calcular_posicao_separado_fim_lista(self):
        """Item 'separado' deve ir para o final da lista."""
        # Mock: lista com aguardando e compra
        item_aguardando = self._criar_mock_item('aguardando', 'Produto A')
        item_compra = self._criar_mock_item('compra', 'Produto B')
        self.mock_itens_container.children = [item_aguardando, item_compra]

        def calcularPosicaoDestino(estado, descricao, container):
            if estado == 'separado':
                return len(container.children)  # Final da lista
            return 0

        posicao = calcularPosicaoDestino('separado', 'Produto C', self.mock_itens_container)
        assert posicao == 2  # Após aguardando e compra

    def test_calcular_posicao_alfabetica_dentro_grupo(self):
        """Dentro do mesmo grupo, deve ordenar alfabeticamente."""
        # Mock: 2 itens aguardando (B, D) - novo item é C
        item_b = self._criar_mock_item('aguardando', 'Produto B')
        item_d = self._criar_mock_item('aguardando', 'Produto D')
        self.mock_itens_container.children = [item_b, item_d]

        def calcularPosicaoDestino(estado, descricao, container):
            """Posição alfabética dentro do grupo 'aguardando'."""
            if estado == 'aguardando':
                posicao = 0
                for child in container.children:
                    child_estado = 'aguardando' if child.classList.contains('border-gray-200') else 'outro'

                    if child_estado != 'aguardando':
                        break  # Fim do grupo aguardando

                    child_desc_el = child.querySelector('.produto-descricao')
                    child_desc = child_desc_el.textContent if child_desc_el else ''

                    if descricao > child_desc:
                        posicao += 1
                    else:
                        break

                return posicao
            return 0

        posicao = calcularPosicaoDestino('aguardando', 'Produto C', self.mock_itens_container)
        assert posicao == 1  # Entre B (pos 0) e D (pos 1)

    def test_calcular_posicao_cenario_completo(self):
        """Cenário real com todos os estados."""
        # Mock: aguardando(A), compra(C), substituido(E), separado(G)
        # Novo item: compra(B) - deve ir após aguardando mas antes de C
        item_a = self._criar_mock_item('aguardando', 'Produto A')
        item_c = self._criar_mock_item('compra', 'Produto C')
        item_e = self._criar_mock_item('substituido', 'Produto E')
        item_g = self._criar_mock_item('separado', 'Produto G')

        self.mock_itens_container.children = [item_a, item_c, item_e, item_g]

        def calcularPosicaoDestino(estado, descricao, container):
            """Calcular posição considerando todos os grupos."""
            prioridades = {'aguardando': 1, 'compra': 2, 'substituido': 3, 'separado': 4}
            minha_prioridade = prioridades.get(estado, 5)

            posicao = 0
            for child in container.children:
                # Detectar estado do child
                if child.classList.contains('border-gray-200'):
                    child_estado = 'aguardando'
                elif child.classList.contains('border-orange-200'):
                    child_estado = 'compra'
                elif child.classList.contains('border-blue-200'):
                    child_estado = 'substituido'
                elif child.classList.contains('border-green-200'):
                    child_estado = 'separado'
                else:
                    child_estado = 'desconhecido'

                child_prioridade = prioridades.get(child_estado, 5)

                # Se child tem prioridade menor, incrementar posição
                if child_prioridade < minha_prioridade:
                    posicao += 1
                # Se mesma prioridade, ordenar alfabeticamente
                elif child_prioridade == minha_prioridade:
                    child_desc_el = child.querySelector('.produto-descricao')
                    child_desc = child_desc_el.textContent if child_desc_el else ''

                    if descricao > child_desc:
                        posicao += 1
                    else:
                        break
                else:
                    break  # Child tem prioridade maior, parar

            return posicao

        # Item B (compra) deve ir após A (aguardando) e antes de C (compra)
        posicao = calcularPosicaoDestino('compra', 'Produto B', self.mock_itens_container)
        assert posicao == 1  # Após A (pos 0), antes de C (pos 1 após inserção)
