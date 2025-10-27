#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de Validação E2E - Fase 23: Implementar "Marcar para Compra"

Este script valida que a Fase 23 foi implementada corretamente.

Validações:
1. Migration 0004 criada e aplicada
2. Campos em_compra, enviado_para_compra_por, enviado_para_compra_em no modelo ItemPedido
3. Método marcar_para_compra() na entidade ItemPedido
4. Use case MarcarParaCompraUseCase implementado
5. View MarcarParaCompraView implementada
6. Rota /pedidos/<id>/itens/<id>/marcar-compra/ configurada
7. Template _item_pedido.html atualizado com menu e badge laranja
8. Testes unitários passando (8/8)

Author: PMCELL
Date: 2025-01-27
"""

import os
import sys
import django
from pathlib import Path

# Setup Django
sys.path.insert(0, str(Path(__file__).parent))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'separacao_pmcell.settings')
django.setup()

from django.core.management import call_command
from core.models import ItemPedido, Pedido, Usuario, Produto
from core.domain.pedido.entities import ItemPedido as ItemPedidoDomain
from core.domain.pedido.entities import ValidationError
from core.domain.produto.entities import Produto as ProdutoDomain
from decimal import Decimal
from django.urls import reverse, resolve
import inspect


class Colors:
    """Cores para terminal."""
    GREEN = '\033[92m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    YELLOW = '\033[93m'
    END = '\033[0m'
    BOLD = '\033[1m'


def print_header(text):
    """Imprime cabeçalho."""
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*70}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{text:^70}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*70}{Colors.END}\n")


def print_success(text):
    """Imprime mensagem de sucesso."""
    print(f"{Colors.GREEN}✓ {text}{Colors.END}")


def print_error(text):
    """Imprime mensagem de erro."""
    print(f"{Colors.RED}✗ {text}{Colors.END}")


def print_info(text):
    """Imprime mensagem informativa."""
    print(f"{Colors.BLUE}ℹ {text}{Colors.END}")


def validar_migration():
    """Valida que a migration 0004 existe e foi aplicada."""
    print_header("VALIDAÇÃO 1: Migration 0004")

    # Verificar se arquivo existe
    migration_file = Path(__file__).parent / 'core' / 'migrations' / '0004_itempedido_em_compra_and_more.py'
    if not migration_file.exists():
        print_error("Migration 0004_itempedido_em_compra_and_more.py não encontrada")
        return False

    print_success(f"Migration encontrada: {migration_file.name}")

    # Verificar se foi aplicada
    from django.db.migrations.recorder import MigrationRecorder
    recorder = MigrationRecorder.Migration
    try:
        migration = recorder.objects.get(app='core', name='0004_itempedido_em_compra_and_more')
        print_success(f"Migration aplicada em: {migration.applied}")
        return True
    except recorder.DoesNotExist:
        print_error("Migration 0004 NÃO foi aplicada no banco de dados")
        return False


def validar_campos_modelo():
    """Valida que os campos foram adicionados ao modelo Django."""
    print_header("VALIDAÇÃO 2: Campos no Modelo Django ItemPedido")

    campos_esperados = ['em_compra', 'enviado_para_compra_por', 'enviado_para_compra_em']
    todos_campos_existem = True

    for campo in campos_esperados:
        if hasattr(ItemPedido, campo):
            print_success(f"Campo '{campo}' existe no modelo ItemPedido")
        else:
            print_error(f"Campo '{campo}' NÃO existe no modelo ItemPedido")
            todos_campos_existem = False

    return todos_campos_existem


def validar_metodo_dominio():
    """Valida que o método marcar_para_compra() existe na entidade de domínio."""
    print_header("VALIDAÇÃO 3: Método marcar_para_compra() na Entidade")

    if hasattr(ItemPedidoDomain, 'marcar_para_compra'):
        print_success("Método marcar_para_compra() existe na entidade ItemPedido")

        # Testar o método
        try:
            produto = ProdutoDomain(
                id=1,
                codigo="12345",
                descricao="Teste",
                quantidade=1,
                valor_unitario=Decimal("10.00"),
                valor_total=Decimal("10.00")
            )
            item = ItemPedidoDomain(
                produto=produto,
                quantidade_solicitada=1
            )
            item.marcar_para_compra("Testador")

            if item.em_compra and item.enviado_para_compra_por == "Testador":
                print_success("Método marcar_para_compra() funciona corretamente")
                return True
            else:
                print_error("Método marcar_para_compra() não atualiza campos corretamente")
                return False

        except Exception as e:
            print_error(f"Erro ao testar método: {e}")
            return False
    else:
        print_error("Método marcar_para_compra() NÃO existe na entidade ItemPedido")
        return False


def validar_use_case():
    """Valida que o use case MarcarParaCompraUseCase foi implementado."""
    print_header("VALIDAÇÃO 4: Use Case MarcarParaCompraUseCase")

    try:
        from core.application.use_cases.marcar_para_compra import MarcarParaCompraUseCase
        print_success("Use case MarcarParaCompraUseCase importado com sucesso")

        # Verificar método execute
        if hasattr(MarcarParaCompraUseCase, 'execute'):
            print_success("Método execute() existe no use case")
            return True
        else:
            print_error("Método execute() NÃO existe no use case")
            return False

    except ImportError as e:
        print_error(f"Não foi possível importar MarcarParaCompraUseCase: {e}")
        return False


def validar_dtos():
    """Valida que os DTOs foram criados."""
    print_header("VALIDAÇÃO 5: DTOs MarcarParaCompra")

    try:
        from core.application.dtos.marcar_para_compra_dtos import (
            MarcarParaCompraRequestDTO,
            MarcarParaCompraResponseDTO
        )
        print_success("MarcarParaCompraRequestDTO importado com sucesso")
        print_success("MarcarParaCompraResponseDTO importado com sucesso")

        # Testar validações dos DTOs
        try:
            request = MarcarParaCompraRequestDTO(
                pedido_id=1,
                item_id=1,
                usuario_id=1
            )
            print_success("MarcarParaCompraRequestDTO validações OK")
        except Exception as e:
            print_error(f"Erro nas validações do RequestDTO: {e}")
            return False

        return True

    except ImportError as e:
        print_error(f"Não foi possível importar DTOs: {e}")
        return False


def validar_view():
    """Valida que a view MarcarParaCompraView foi implementada."""
    print_header("VALIDAÇÃO 6: View MarcarParaCompraView")

    try:
        from core.presentation.web.views import MarcarParaCompraView
        print_success("View MarcarParaCompraView importada com sucesso")

        # Verificar método post
        if hasattr(MarcarParaCompraView, 'post'):
            print_success("Método post() existe na view")
            return True
        else:
            print_error("Método post() NÃO existe na view")
            return False

    except ImportError as e:
        print_error(f"Não foi possível importar MarcarParaCompraView: {e}")
        return False


def validar_rota():
    """Valida que a rota foi configurada."""
    print_header("VALIDAÇÃO 7: Rota /pedidos/<id>/itens/<id>/marcar-compra/")

    try:
        url = reverse('marcar_compra', args=[1, 1])
        print_success(f"Rota 'marcar_compra' encontrada: {url}")

        # Verificar que resolve para a view correta
        resolver = resolve(url)
        from core.presentation.web.views import MarcarParaCompraView
        if resolver.func.view_class == MarcarParaCompraView:
            print_success("Rota resolve para MarcarParaCompraView")
            return True
        else:
            print_error(f"Rota resolve para {resolver.func.view_class}, esperava MarcarParaCompraView")
            return False

    except Exception as e:
        print_error(f"Erro ao validar rota: {e}")
        return False


def validar_template():
    """Valida que o template foi atualizado."""
    print_header("VALIDAÇÃO 8: Template _item_pedido.html")

    template_file = Path(__file__).parent / 'templates' / 'partials' / '_item_pedido.html'

    if not template_file.exists():
        print_error("Template _item_pedido.html não encontrado")
        return False

    print_success(f"Template encontrado: {template_file.name}")

    content = template_file.read_text()

    # Verificar if item.em_compra
    if 'item.em_compra' in content:
        print_success("Verificação 'item.em_compra' encontrada no template")
    else:
        print_error("Verificação 'item.em_compra' NÃO encontrada no template")
        return False

    # Verificar badge laranja
    if 'Aguardando Compra' in content and 'orange' in content:
        print_success("Badge laranja 'Aguardando Compra' encontrado")
    else:
        print_error("Badge laranja 'Aguardando Compra' NÃO encontrado")
        return False

    # Verificar menu de opções
    if 'menuOpen' in content or 'x-data' in content:
        print_success("Menu de opções (Alpine.js) encontrado")
    else:
        print_error("Menu de opções NÃO encontrado")
        return False

    # Verificar botão "Marcar para Compra"
    if 'marcar_compra' in content:
        print_success("Botão 'Marcar para Compra' encontrado")
    else:
        print_error("Botão 'Marcar para Compra' NÃO encontrado")
        return False

    return True


def validar_testes():
    """Valida que os testes unitários estão passando."""
    print_header("VALIDAÇÃO 9: Testes Unitários (8 testes)")

    import subprocess

    try:
        result = subprocess.run(
            ['python3', '-m', 'pytest',
             'tests/unit/application/use_cases/test_marcar_para_compra.py',
             '-v', '--tb=short'],
            capture_output=True,
            text=True,
            timeout=30
        )

        if result.returncode == 0:
            # Contar testes passados
            output = result.stdout
            if '8 passed' in output:
                print_success("Todos os 8 testes passaram!")
                return True
            else:
                print_error("Nem todos os testes passaram")
                print_info(output)
                return False
        else:
            print_error("Falha ao executar testes")
            print_info(result.stdout)
            print_info(result.stderr)
            return False

    except Exception as e:
        print_error(f"Erro ao executar testes: {e}")
        return False


def main():
    """Função principal."""
    print_header("VALIDAÇÃO FASE 23: IMPLEMENTAR 'MARCAR PARA COMPRA'")

    validacoes = [
        ("Migration 0004", validar_migration),
        ("Campos no Modelo", validar_campos_modelo),
        ("Método de Domínio", validar_metodo_dominio),
        ("Use Case", validar_use_case),
        ("DTOs", validar_dtos),
        ("View", validar_view),
        ("Rota", validar_rota),
        ("Template", validar_template),
        ("Testes Unitários", validar_testes),
    ]

    resultados = []
    for nome, func in validacoes:
        try:
            resultado = func()
            resultados.append((nome, resultado))
        except Exception as e:
            print_error(f"Erro inesperado em {nome}: {e}")
            resultados.append((nome, False))

    # Resumo
    print_header("RESUMO")

    total = len(resultados)
    passou = sum(1 for _, r in resultados if r)

    for nome, resultado in resultados:
        if resultado:
            print_success(f"{nome}: OK")
        else:
            print_error(f"{nome}: FALHOU")

    print(f"\n{Colors.BOLD}Resultado Final: {passou}/{total} validações passaram{Colors.END}")

    if passou == total:
        print(f"\n{Colors.GREEN}{Colors.BOLD}🎉 FASE 23 CONCLUÍDA COM SUCESSO! 🎉{Colors.END}\n")
        return 0
    else:
        print(f"\n{Colors.RED}{Colors.BOLD}❌ FASE 23 INCOMPLETA - Corrija os erros acima{Colors.END}\n")
        return 1


if __name__ == '__main__':
    sys.exit(main())
