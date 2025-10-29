# -*- coding: utf-8 -*-
"""
Configuração de fixtures para testes E2E com Playwright.

Este módulo cria dados de teste no banco antes de executar testes E2E.
"""

import pytest
import django
import os
import sys

# Configurar Django antes de importar models
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'separacao_pmcell.settings')
django.setup()

from core.models import Usuario, Pedido as PedidoModel, ItemPedido as ItemPedidoModel, Produto as ProdutoModel


@pytest.fixture(scope="session", autouse=True)
def preparar_dados_teste():
    """
    Cria dados de teste no banco antes de executar testes E2E.

    Cria:
    - 2 separadores (login 2 e 3)
    - 1 vendedor
    - 1 pedido em separação
    - 5 itens no pedido (para testar diferentes ações)
    """
    print("\n" + "="*60)
    print("PREPARANDO DADOS DE TESTE PARA E2E")
    print("="*60)

    # Limpar dados antigos de teste (se existirem)
    Usuario.objects.filter(numero_login__in=[2, 3, 99]).delete()
    PedidoModel.objects.filter(numero_orcamento='E2E-TEST-001').delete()

    # Criar separadores
    separador1 = Usuario.objects.create_user(
        numero_login=2,
        pin='1234',
        nome='Separador Teste 1',
        tipo='SEPARADOR'
    )
    print(f"✓ Separador 1 criado: {separador1.nome} (login: 2)")

    separador2 = Usuario.objects.create_user(
        numero_login=3,
        pin='1234',
        nome='Separador Teste 2',
        tipo='SEPARADOR'
    )
    print(f"✓ Separador 2 criado: {separador2.nome} (login: 3)")

    # Criar vendedor
    vendedor = Usuario.objects.create_user(
        numero_login=99,
        pin='9999',
        nome='Vendedor Teste',
        tipo='VENDEDOR'
    )
    print(f"✓ Vendedor criado: {vendedor.nome}")

    # Criar produtos
    produtos = []
    for i in range(1, 6):
        produto = ProdutoModel.objects.create(
            codigo=f'PROD-E2E-{i:03d}',
            descricao=f'Produto Teste E2E {i}',
            quantidade=10,
            valor_unitario=10.00 * i,
            valor_total=100.00 * i
        )
        produtos.append(produto)
    print(f"✓ {len(produtos)} produtos criados")

    # Criar pedido
    pedido = PedidoModel.objects.create(
        numero_orcamento='E2E-TEST-001',
        codigo_cliente='CLI-E2E-001',
        nome_cliente='Cliente Teste E2E',
        vendedor=vendedor,
        logistica='MOTOBOY',
        embalagem='CAIXA',
        status='EM_SEPARACAO'
    )
    print(f"✓ Pedido criado: {pedido.numero_orcamento} (ID: {pedido.id})")

    # Criar itens no pedido
    itens = []
    for i, produto in enumerate(produtos, start=1):
        item = ItemPedidoModel.objects.create(
            pedido=pedido,
            produto=produto,
            quantidade_solicitada=i * 2,  # 2, 4, 6, 8, 10
            separado=False,
            em_compra=False,
            substituido=False
        )
        itens.append(item)
    print(f"✓ {len(itens)} itens criados no pedido")

    # Salvar IDs em arquivo para uso nos testes
    with open('/tmp/e2e_test_data.txt', 'w') as f:
        f.write(f"PEDIDO_ID={pedido.id}\n")
        f.write(f"SEPARADOR1_LOGIN=2\n")
        f.write(f"SEPARADOR2_LOGIN=3\n")
        for i, item in enumerate(itens, start=1):
            f.write(f"ITEM{i}_ID={item.id}\n")

    print(f"\n✓ Dados salvos em /tmp/e2e_test_data.txt")
    print("="*60 + "\n")

    # Retornar dados para uso nos testes
    yield {
        'pedido_id': pedido.id,
        'item_ids': [item.id for item in itens],
        'separador1_login': 2,
        'separador2_login': 3,
    }

    # Cleanup após testes (opcional - comentado para permitir inspeção manual)
    # print("\nLimpando dados de teste...")
    # Usuario.objects.filter(numero_login__in=[2, 3, 99]).delete()
    # PedidoModel.objects.filter(numero_orcamento='E2E-TEST-001').delete()


def ler_dados_teste():
    """Lê dados de teste do arquivo temporário."""
    dados = {}
    try:
        with open('/tmp/e2e_test_data.txt', 'r') as f:
            for line in f:
                key, value = line.strip().split('=')
                dados[key] = int(value)
    except FileNotFoundError:
        raise RuntimeError(
            "Arquivo de dados de teste não encontrado. "
            "Execute pytest para gerar dados de teste primeiro."
        )
    return dados
