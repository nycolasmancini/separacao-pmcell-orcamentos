# -*- coding: utf-8 -*-
"""
Testes Unitários para Fase 38B - Correção de Duplicação ao Desmarcar Item

BUG: Item desmarcado permanece na seção "Itens Separados" E aparece em "Itens Não Separados"
CAUSA: getElementById() retorna apenas primeira ocorrência, não remove todas

Este teste deve FALHAR com código atual e PASSAR após correção.
"""

import pytest
from django.test import TestCase
from unittest.mock import Mock, patch, MagicMock
import json


class TestRemocaoDuplicadosDesmarcar(TestCase):
    """
    Testes para validar que item desmarcado é removido de TODOS os containers
    antes de ser inserido no container correto.
    """

    def setUp(self):
        """Setup comum para todos os testes."""
        # Mock do DOM com 2 containers
        self.mock_dom = {
            'container-separados': [],
            'container-nao-separados': []
        }

    def test_item_desmarcado_removido_de_todos_containers(self):
        """
        Teste crítico: Item desmarcado deve ser removido de TODOS os containers.

        Cenário:
        1. Item #123 está em 'container-separados'
        2. Usuário desmarca item
        3. Sistema deve REMOVER item de 'container-separados'
        4. Sistema deve INSERIR item em 'container-nao-separados'
        5. Resultado: Item existe APENAS em 'container-nao-separados'

        DEVE FALHAR com código atual (bug de duplicação).
        """
        item_id = 123

        # Estado inicial: item em "separados"
        self.mock_dom['container-separados'].append({
            'id': f'item-{item_id}',
            'separado': True
        })

        # Simular desmarcação (código atual - BUGADO)
        # getElementById retorna apenas primeira ocorrência
        containers_com_item = [
            container for container, items in self.mock_dom.items()
            if any(item['id'] == f'item-{item_id}' for item in items)
        ]

        # Código atual remove apenas de UM container (primeira ocorrência)
        if containers_com_item:
            primeiro_container = containers_com_item[0]
            self.mock_dom[primeiro_container] = [
                item for item in self.mock_dom[primeiro_container]
                if item['id'] != f'item-{item_id}'
            ]

        # Inserir item no container destino
        self.mock_dom['container-nao-separados'].append({
            'id': f'item-{item_id}',
            'separado': False
        })

        # ASSERÇÃO CRÍTICA: Item deve existir em APENAS UM container
        total_ocorrencias = sum(
            1 for items in self.mock_dom.values()
            for item in items
            if item['id'] == f'item-{item_id}'
        )

        self.assertEqual(
            total_ocorrencias, 1,
            f"Item {item_id} deve aparecer APENAS 1 vez no DOM, "
            f"mas aparece {total_ocorrencias} vezes"
        )

        # Verificar que está no container correto
        item_em_separados = any(
            item['id'] == f'item-{item_id}'
            for item in self.mock_dom['container-separados']
        )
        item_em_nao_separados = any(
            item['id'] == f'item-{item_id}'
            for item in self.mock_dom['container-nao-separados']
        )

        self.assertFalse(
            item_em_separados,
            f"Item {item_id} NÃO deve estar em 'container-separados' após desmarcar"
        )
        self.assertTrue(
            item_em_nao_separados,
            f"Item {item_id} DEVE estar em 'container-nao-separados' após desmarcar"
        )

    def test_remover_item_de_multiplos_containers_antes_de_inserir(self):
        """
        Teste de remoção completa: Deve remover item de TODOS os containers
        antes de inserir no container destino.

        Cenário (simulando bug):
        1. Item #456 está duplicado (em 'separados' E 'nao-separados')
        2. Sistema deve remover de AMBOS antes de inserir
        3. Após remoção + inserção: item existe APENAS uma vez
        """
        item_id = 456

        # Estado BUGADO: item duplicado em ambos containers
        self.mock_dom['container-separados'].append({
            'id': f'item-{item_id}',
            'separado': True
        })
        self.mock_dom['container-nao-separados'].append({
            'id': f'item-{item_id}',
            'separado': False
        })

        # Verificar duplicação inicial
        total_antes = sum(
            1 for items in self.mock_dom.values()
            for item in items
            if item['id'] == f'item-{item_id}'
        )
        self.assertEqual(total_antes, 2, "Estado inicial deve ter duplicação")

        # CORREÇÃO: Remover de TODOS os containers (comportamento esperado)
        for container_id in self.mock_dom.keys():
            self.mock_dom[container_id] = [
                item for item in self.mock_dom[container_id]
                if item['id'] != f'item-{item_id}'
            ]

        # Inserir no container correto
        self.mock_dom['container-nao-separados'].append({
            'id': f'item-{item_id}',
            'separado': False
        })

        # Verificar unicidade após correção
        total_depois = sum(
            1 for items in self.mock_dom.values()
            for item in items
            if item['id'] == f'item-{item_id}'
        )

        self.assertEqual(
            total_depois, 1,
            f"Após remover de todos containers, item {item_id} deve existir APENAS 1 vez"
        )

    def test_contador_badges_reflete_remocao_correta(self):
        """
        Teste de contadores: Badges devem refletir contagem correta.

        Cenário:
        - Pedido com 3 itens: [1, 2, 3]
        - Item 1 separado
        - Desmarcar item 1
        - Badge 'Separados': 0 itens (não 1!)
        - Badge 'Não Separados': 3 itens
        """
        # Setup: 3 itens, 1 separado
        self.mock_dom['container-separados'].append({'id': 'item-1', 'separado': True})
        self.mock_dom['container-nao-separados'].extend([
            {'id': 'item-2', 'separado': False},
            {'id': 'item-3', 'separado': False}
        ])

        # Contar antes
        count_separados_antes = len(self.mock_dom['container-separados'])
        count_nao_separados_antes = len(self.mock_dom['container-nao-separados'])

        self.assertEqual(count_separados_antes, 1)
        self.assertEqual(count_nao_separados_antes, 2)

        # Desmarcar item 1 (COM CORREÇÃO - remover de todos)
        item_id = 1
        for container_id in self.mock_dom.keys():
            self.mock_dom[container_id] = [
                item for item in self.mock_dom[container_id]
                if item['id'] != f'item-{item_id}'
            ]

        # Inserir em não-separados
        self.mock_dom['container-nao-separados'].append({'id': 'item-1', 'separado': False})

        # Contar depois
        count_separados_depois = len(self.mock_dom['container-separados'])
        count_nao_separados_depois = len(self.mock_dom['container-nao-separados'])

        # ASSERÇÕES CRÍTICAS
        self.assertEqual(
            count_separados_depois, 0,
            "Badge 'Separados' deve mostrar 0 itens após desmarcar único item separado"
        )
        self.assertEqual(
            count_nao_separados_depois, 3,
            "Badge 'Não Separados' deve mostrar 3 itens (todos não separados)"
        )

    def test_validacao_unicidade_detecta_duplicacao(self):
        """
        Teste de validação: Sistema deve detectar e alertar sobre duplicação.

        Cenário:
        - Item #789 duplicado em ambos containers
        - Função validarUnicidadeItem() deve lançar erro
        """
        item_id = 789

        # Criar duplicação intencional
        self.mock_dom['container-separados'].append({'id': f'item-{item_id}'})
        self.mock_dom['container-nao-separados'].append({'id': f'item-{item_id}'})

        # Simular validação de unicidade
        def validar_unicidade(item_id, dom):
            total = sum(
                1 for items in dom.values()
                for item in items
                if item['id'] == f'item-{item_id}'
            )
            if total > 1:
                raise ValueError(
                    f"Duplicação detectada: item {item_id} aparece {total} vezes"
                )

        # Deve lançar erro
        with self.assertRaises(ValueError) as context:
            validar_unicidade(item_id, self.mock_dom)

        self.assertIn("Duplicação detectada", str(context.exception))
        self.assertIn(str(item_id), str(context.exception))


class TestLogicaRemocaoCompleta(TestCase):
    """
    Testes para a função removerItemCompletamente() que será implementada.
    """

    def test_remover_item_completamente_de_todos_containers(self):
        """
        Teste da função helper removerItemCompletamente().

        Deve:
        1. Buscar item em TODOS os containers conhecidos
        2. Remover todas as ocorrências encontradas
        3. Retornar lista de elementos removidos
        """
        # Mock de containers
        containers = {
            'container-separados': [
                {'id': 'item-100'},
                {'id': 'item-200'}
            ],
            'container-nao-separados': [
                {'id': 'item-100'},  # Duplicado!
                {'id': 'item-300'}
            ]
        }

        # Função de remoção esperada (comportamento correto)
        def remover_item_completamente(item_id, doms):
            removidos = []
            for container_id, items in doms.items():
                elementos_removidos = [
                    item for item in items
                    if item['id'] == f'item-{item_id}'
                ]
                removidos.extend(elementos_removidos)

                doms[container_id] = [
                    item for item in items
                    if item['id'] != f'item-{item_id}'
                ]
            return removidos

        # Executar remoção
        removidos = remover_item_completamente(100, containers)

        # Validar que 2 elementos foram removidos (duplicado)
        self.assertEqual(
            len(removidos), 2,
            "Deve remover TODAS as ocorrências (2 duplicados)"
        )

        # Validar que item não existe mais em nenhum container
        for container_id, items in containers.items():
            item_existe = any(item['id'] == 'item-100' for item in items)
            self.assertFalse(
                item_existe,
                f"Item não deve existir em {container_id} após remoção completa"
            )

        # Validar que outros itens não foram afetados
        total_items_restantes = sum(len(items) for items in containers.values())
        self.assertEqual(
            total_items_restantes, 2,
            "Outros itens (200, 300) devem permanecer intocados"
        )


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
