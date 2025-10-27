#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de validação da Fase 21: Criar Tela de Detalhe do Pedido
Verifica se todos os componentes foram implementados corretamente.
"""

import os
import sys


def validar_arquivo_existe(caminho, nome):
    """Valida se arquivo existe."""
    if os.path.exists(caminho):
        print(f"✅ {nome}: OK")
        return True
    else:
        print(f"❌ {nome}: FALTANDO")
        return False


def validar_conteudo_arquivo(caminho, strings_obrigatorias, nome):
    """Valida se arquivo contém strings obrigatórias."""
    if not os.path.exists(caminho):
        print(f"❌ {nome}: Arquivo não existe")
        return False

    with open(caminho, 'r', encoding='utf-8') as f:
        conteudo = f.read()

    missing = []
    for string in strings_obrigatorias:
        if string not in conteudo:
            missing.append(string)

    if missing:
        print(f"❌ {nome}: Faltando conteúdo - {', '.join(missing)}")
        return False
    else:
        print(f"✅ {nome}: Conteúdo OK")
        return True


def main():
    """Executa todas as validações."""
    print("=" * 60)
    print("VALIDAÇÃO - FASE 21: Criar Tela de Detalhe do Pedido")
    print("=" * 60)
    print()

    resultados = []

    # 1. Validar View
    print("1. Validando DetalhePedidoView...")
    view_checks = validar_conteudo_arquivo(
        'core/presentation/web/views.py',
        [
            'class DetalhePedidoView',
            'detalhe_pedido.html',
            'itens_nao_separados',
            'itens_separados',
            'tempo_decorrido_minutos',
            'progresso_percentual',
            '_calcular_tempo_decorrido',
            '_calcular_progresso'
        ],
        "DetalhePedidoView"
    )
    resultados.append(view_checks)
    print()

    # 2. Validar URL
    print("2. Validando rota em urls.py...")
    url_checks = validar_conteudo_arquivo(
        'core/urls.py',
        [
            'DetalhePedidoView',
            "path('pedidos/<int:pedido_id>/'",
            "name='detalhe_pedido'"
        ],
        "URL detalhe_pedido"
    )
    resultados.append(url_checks)
    print()

    # 3. Validar Template
    print("3. Validando template detalhe_pedido.html...")
    template_exists = validar_arquivo_existe(
        'templates/detalhe_pedido.html',
        "Template detalhe_pedido.html"
    )
    if template_exists:
        template_checks = validar_conteudo_arquivo(
            'templates/detalhe_pedido.html',
            [
                'Itens Não Separados',
                'Itens Separados',
                'itens_nao_separados',
                'itens_separados',
                'tempo_decorrido_minutos',
                'progresso_percentual',
                'Voltar ao Dashboard',
                'pedido.numero_orcamento',
                'pedido.nome_cliente',
                'pedido.vendedor.nome',
                'pedido.get_logistica_display',
                'pedido.get_embalagem_display'
            ],
            "Conteúdo do template"
        )
        resultados.append(template_checks)
    else:
        resultados.append(False)
    print()

    # 4. Validar Testes
    print("4. Validando testes automatizados...")
    tests_checks = validar_conteudo_arquivo(
        'tests/unit/presentation/test_detalhe_pedido_view.py',
        [
            'test_acesso_detalhe_sem_login_redireciona',
            'test_acesso_detalhe_com_login_mostra_template',
            'test_pedido_inexistente_retorna_404',
            'test_itens_separados_e_nao_separados_em_secoes_corretas',
            'test_tempo_decorrido_calculado_corretamente',
            'test_progresso_exibido_no_contexto',
            'test_informacoes_pedido_renderizadas_no_template',
            'test_htmx_request_retorna_partial_sem_layout'
        ],
        "Testes da Fase 21"
    )
    resultados.append(tests_checks)
    print()

    # 5. Executar testes
    print("5. Executando testes automatizados...")
    import subprocess
    try:
        result = subprocess.run(
            ['python3', '-m', 'pytest', 'tests/unit/presentation/test_detalhe_pedido_view.py', '-v'],
            capture_output=True,
            text=True,
            timeout=30
        )
        if result.returncode == 0:
            print("✅ Todos os testes passaram")
            resultados.append(True)
        else:
            print("❌ Alguns testes falharam")
            print(result.stdout)
            resultados.append(False)
    except Exception as e:
        print(f"❌ Erro ao executar testes: {e}")
        resultados.append(False)
    print()

    # Resultado Final
    print("=" * 60)
    total = len(resultados)
    passou = sum(resultados)
    percentual = (passou / total) * 100

    print(f"RESULTADO FINAL: {passou}/{total} validações passaram ({percentual:.1f}%)")

    if all(resultados):
        print("✅ FASE 21 CONCLUÍDA COM SUCESSO!")
        print("=" * 60)
        return 0
    else:
        print("❌ FASE 21 INCOMPLETA - Verifique os erros acima")
        print("=" * 60)
        return 1


if __name__ == "__main__":
    sys.exit(main())
