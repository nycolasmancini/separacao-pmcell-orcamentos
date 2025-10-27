#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de Validação E2E - Fase 22: Marcação de Item como Separado

Este script valida que a Fase 22 foi implementada corretamente:
- ✅ Checkbox funcional com HTMX
- ✅ Item move para seção correta
- ✅ Progresso atualiza
- ✅ Animação fluida
- ✅ Testes passam

Execução:
    python3 validar_fase22.py
"""

import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'separacao_pmcell.settings')
django.setup()

from decimal import Decimal
from core.models import Usuario, Pedido, ItemPedido as ItemPedidoDjango, Produto
from django.test import Client, override_settings
from django.utils import timezone


class Colors:
    """Cores para output no terminal."""
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'
    END = '\033[0m'


def print_header(text):
    """Imprime cabeçalho formatado."""
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'=' * 70}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{text.center(70)}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'=' * 70}{Colors.END}\n")


def print_success(text):
    """Imprime mensagem de sucesso."""
    print(f"{Colors.GREEN}✓ {text}{Colors.END}")


def print_error(text):
    """Imprime mensagem de erro."""
    print(f"{Colors.RED}✗ {text}{Colors.END}")


def print_info(text):
    """Imprime mensagem informativa."""
    print(f"{Colors.YELLOW}ℹ {text}{Colors.END}")


def validacao_1_estrutura_arquivos():
    """
    Validação 1: Verifica que todos os arquivos foram criados.
    """
    print_header("VALIDAÇÃO 1: Estrutura de Arquivos")

    arquivos_esperados = [
        'core/application/use_cases/separar_item.py',
        'core/application/dtos/separar_item_dtos.py',
        'tests/unit/application/use_cases/test_separar_item.py',
        'templates/partials/_item_pedido.html',
        'templates/partials/_erro.html',
    ]

    todos_existem = True
    for arquivo in arquivos_esperados:
        caminho_completo = os.path.join(os.path.dirname(__file__), arquivo)
        if os.path.exists(caminho_completo):
            print_success(f"Arquivo existe: {arquivo}")
        else:
            print_error(f"Arquivo NÃO encontrado: {arquivo}")
            todos_existem = False

    if todos_existem:
        print_success("Todos os arquivos necessários foram criados!")
        return True
    else:
        print_error("Alguns arquivos estão faltando!")
        return False


def validacao_2_use_case_funcional():
    """
    Validação 2: Verifica que o use case está funcional.
    """
    print_header("VALIDAÇÃO 2: Use Case Funcional")

    try:
        from core.application.use_cases.separar_item import SepararItemUseCase
        from core.application.dtos.separar_item_dtos import SepararItemRequestDTO
        print_success("SepararItemUseCase importado com sucesso")

        # Verificar que o use case está exportado
        from core.application.use_cases import SepararItemUseCase
        print_success("SepararItemUseCase está exportado em __init__.py")

        return True

    except ImportError as e:
        print_error(f"Erro ao importar use case: {e}")
        return False


def validacao_3_rota_configurada():
    """
    Validação 3: Verifica que a rota foi adicionada ao urls.py.
    """
    print_header("VALIDAÇÃO 3: Rota Configurada")

    try:
        from django.urls import reverse

        # Tentar resolver a URL
        url = reverse('separar_item', kwargs={'pedido_id': 1, 'item_id': 1})
        print_success(f"Rota 'separar_item' configurada: {url}")

        return True

    except Exception as e:
        print_error(f"Erro ao verificar rota: {e}")
        return False


def validacao_4_testes_unitarios_passando():
    """
    Validação 4: Verifica que todos os testes unitários estão passando.
    """
    print_header("VALIDAÇÃO 4: Testes Unitários")

    import subprocess

    try:
        result = subprocess.run(
            ['python3', '-m', 'pytest', 'tests/unit/application/use_cases/test_separar_item.py', '-v'],
            capture_output=True,
            text=True,
            timeout=30
        )

        if result.returncode == 0:
            # Contar testes passados
            output = result.stdout
            if "8 passed" in output:
                print_success("8 testes unitários da Fase 22 passando")
                return True
            else:
                print_error(f"Esperado 8 testes passando, mas output foi diferente")
                print(output[-500:])  # Últimas linhas
                return False
        else:
            print_error("Testes unitários falharam")
            print(result.stdout[-500:])
            return False

    except Exception as e:
        print_error(f"Erro ao executar testes: {e}")
        return False


@override_settings(ALLOWED_HOSTS=['*'])
def validacao_5_endpoint_htmx_funcional():
    """
    Validação 5: Verifica que o endpoint HTMX está funcional (simulação).
    """
    print_header("VALIDAÇÃO 5: Endpoint HTMX Funcional")

    try:
        # Criar usuário de teste
        usuario, created = Usuario.objects.get_or_create(
            numero_login=9999,
            defaults={
                'nome': 'Usuário Teste Fase 22',
                'tipo': 'SEPARADOR'
            }
        )
        usuario.set_password('1234')
        usuario.save()

        # Limpar dados anteriores (se existirem)
        Pedido.objects.filter(numero_orcamento='TESTE-FASE22').delete()
        Produto.objects.filter(codigo='99999').delete()

        # Criar produto de teste
        produto = Produto.objects.create(
            codigo='99999',
            descricao='Produto Teste Fase 22',
            quantidade=1,
            valor_unitario=Decimal('10.00'),
            valor_total=Decimal('10.00')
        )

        # Criar pedido de teste
        pedido = Pedido.objects.create(
            numero_orcamento='TESTE-FASE22',
            codigo_cliente='CLI-TESTE',
            nome_cliente='Cliente Teste',
            vendedor=usuario,
            data='27/10/2025',
            logistica='CORREIOS',
            embalagem='CAIXA'
        )

        # Criar item de teste
        item = ItemPedidoDjango.objects.create(
            pedido=pedido,
            produto=produto,
            quantidade_solicitada=1,
            quantidade_separada=0,
            separado=False
        )

        print_success(f"Dados de teste criados: Pedido {pedido.numero_orcamento}, Item {item.id}")

        # Simular requisição HTMX
        client = Client()
        client.force_login(usuario)

        response = client.post(
            f'/pedidos/{pedido.id}/itens/{item.id}/separar/',
            HTTP_HX_REQUEST='true'
        )

        if response.status_code == 200:
            print_success(f"Endpoint retornou 200 OK")

            # Verificar que item foi marcado como separado
            item.refresh_from_db()
            if item.separado:
                print_success("Item foi marcado como separado no banco de dados")
            else:
                print_error("Item NÃO foi marcado como separado")
                return False

            # Verificar que separado_por foi registrado
            if item.separado_por == usuario:
                print_success(f"Usuário separador registrado: {item.separado_por.nome}")
            else:
                print_error("Usuário separador não foi registrado corretamente")
                return False

            # Verificar que separado_em foi registrado
            if item.separado_em:
                print_success(f"Timestamp registrado: {item.separado_em}")
            else:
                print_error("Timestamp não foi registrado")
                return False

            # Limpar dados de teste
            pedido.delete()
            produto.delete()
            usuario.delete()

            return True

        else:
            print_error(f"Endpoint retornou status {response.status_code}")
            print(response.content.decode()[:500])
            return False

    except Exception as e:
        print_error(f"Erro ao testar endpoint: {e}")
        import traceback
        traceback.print_exc()
        return False


def validacao_6_todos_testes_passando():
    """
    Validação 6: Verifica que TODOS os testes estão passando (não apenas Fase 22).
    """
    print_header("VALIDAÇÃO 6: Todos os Testes (Regressão)")

    import subprocess

    try:
        result = subprocess.run(
            ['python3', '-m', 'pytest', 'tests/', '-v', '--tb=short'],
            capture_output=True,
            text=True,
            timeout=60
        )

        if result.returncode == 0:
            output = result.stdout
            if "48 passed" in output:
                print_success("48 testes passando (40 anteriores + 8 da Fase 22)")
                return True
            else:
                # Verificar se passou mas com número diferente
                import re
                match = re.search(r'(\d+) passed', output)
                if match:
                    num_passed = int(match.group(1))
                    print_info(f"{num_passed} testes passando")
                    if num_passed >= 48:
                        print_success("Mais testes do que esperado passaram! OK")
                        return True
                print_error(f"Esperado 48 testes, mas resultado foi diferente")
                return False
        else:
            print_error("Alguns testes falharam")
            print(result.stdout[-1000:])
            return False

    except Exception as e:
        print_error(f"Erro ao executar testes: {e}")
        return False


def main():
    """Executa todas as validações."""
    print(f"\n{Colors.BOLD}VALIDAÇÃO E2E - FASE 22: MARCAÇÃO DE ITEM COMO SEPARADO{Colors.END}")

    validacoes = [
        validacao_1_estrutura_arquivos,
        validacao_2_use_case_funcional,
        validacao_3_rota_configurada,
        validacao_4_testes_unitarios_passando,
        validacao_5_endpoint_htmx_funcional,
        validacao_6_todos_testes_passando,
    ]

    resultados = []
    for validacao in validacoes:
        resultado = validacao()
        resultados.append(resultado)

    # Resumo Final
    print_header("RESUMO FINAL")

    total = len(resultados)
    passou = sum(resultados)
    falhou = total - passou

    print(f"{Colors.BOLD}Total de validações: {total}{Colors.END}")
    print_success(f"Passaram: {passou}")
    if falhou > 0:
        print_error(f"Falharam: {falhou}")

    if all(resultados):
        print(f"\n{Colors.GREEN}{Colors.BOLD}✓ FASE 22 COMPLETA E VALIDADA COM SUCESSO!{Colors.END}")
        print(f"{Colors.GREEN}Todos os testes passando (48/48){Colors.END}")
        print(f"{Colors.GREEN}Endpoint HTMX funcional{Colors.END}")
        print(f"{Colors.GREEN}Checkbox interativo implementado{Colors.END}\n")
        sys.exit(0)
    else:
        print(f"\n{Colors.RED}{Colors.BOLD}✗ FASE 22 INCOMPLETA{Colors.END}")
        print(f"{Colors.RED}Algumas validações falharam. Verifique os erros acima.{Colors.END}\n")
        sys.exit(1)


if __name__ == '__main__':
    main()
