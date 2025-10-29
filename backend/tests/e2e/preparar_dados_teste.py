# -*- coding: utf-8 -*-
"""
Script para preparar dados de teste para E2E.

Execute este script antes de rodar testes E2E ou testes manuais.
"""

import os
import sys
import django

# Configurar Django
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'separacao_pmcell.settings')
django.setup()

from core.models import Usuario, Pedido as PedidoModel, ItemPedido as ItemPedidoModel, Produto as ProdutoModel


def main():
    print("\n" + "="*60)
    print("PREPARANDO DADOS DE TESTE PARA E2E")
    print("="*60)

    # Limpar dados antigos de teste (se existirem)
    Usuario.objects.filter(numero_login__in=[2, 3, 99]).delete()
    PedidoModel.objects.filter(numero_orcamento='E2E-TEST-001').delete()
    print("✓ Dados antigos limpos")

    # Criar separadores
    separador1 = Usuario.objects.create_user(
        numero_login=2,
        pin='1234',
        nome='Separador Teste 1',
        tipo='SEPARADOR'
    )
    print(f"✓ Separador 1 criado: {separador1.nome} (login: 2, PIN: 1234)")

    separador2 = Usuario.objects.create_user(
        numero_login=3,
        pin='1234',
        nome='Separador Teste 2',
        tipo='SEPARADOR'
    )
    print(f"✓ Separador 2 criado: {separador2.nome} (login: 3, PIN: 1234)")

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

    print(f"\n✓ IDs salvos em /tmp/e2e_test_data.txt")
    print("="*60)
    print("DADOS DE TESTE CRIADOS COM SUCESSO!")
    print("="*60)

    print("\n📝 INSTRUÇÕES PARA TESTE MANUAL:")
    print("-" * 60)
    print(f"1. Abra 2 navegadores (ou 2 abas em modo anônimo)")
    print(f"2. Browser 1: Acesse http://192.168.15.110:8000/login/")
    print(f"   - Login: 2")
    print(f"   - PIN: 1234")
    print(f"\n3. Browser 2: Acesse http://192.168.15.110:8000/login/")
    print(f"   - Login: 3")
    print(f"   - PIN: 1234")
    print(f"\n4. Em ambos navegadores, clique no pedido '{pedido.numero_orcamento}'")
    print(f"   URL direta: http://192.168.15.110:8000/pedidos/{pedido.id}/")
    print(f"\n5. No Browser 1:")
    print(f"   - Item 1 (ID: {itens[0].id}): Marcar para Compra")
    print(f"   - Item 2 (ID: {itens[1].id}): Marcar como Substituído")
    print(f"\n6. No Browser 2: Verificar se os itens atualizam em tempo real!")
    print("-" * 60)

    return pedido.id, [item.id for item in itens]


if __name__ == '__main__':
    main()
