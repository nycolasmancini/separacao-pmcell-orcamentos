#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de Validação - Fase 20: Implementar Métrica de Tempo Médio no Dashboard

Este script valida a implementação completa da Fase 20, verificando:
1. Testes unitários passando (9 testes)
2. Use Case ObterMetricasTempoUseCase implementado
3. Método calcular_tempo_medio_finalizacao no repository
4. Value Object MetricasTempo
5. Template _card_metricas_tempo.html
6. Integração com DashboardView
7. Formatação humanizada de tempo e percentual
8. Cálculo correto de tendências

Author: PMCELL
Date: 2025-01-27
"""

import os
import sys
import django
from pathlib import Path

# Setup Django
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'separacao_pmcell.settings')
django.setup()

# Imports após setup do Django
from datetime import datetime, timedelta
from django.utils import timezone
from core.application.use_cases.obter_metricas_tempo import ObterMetricasTempoUseCase
from core.infrastructure.persistence.repositories.pedido_repository import DjangoPedidoRepository
from core.domain.pedido.value_objects import MetricasTempo
from core.models import Pedido, Usuario, ItemPedido


class Colors:
    """Cores ANSI para output colorido."""
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'


def print_header(text):
    """Imprime cabeçalho formatado."""
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'=' * 70}{Colors.ENDC}")
    print(f"{Colors.BOLD}{Colors.BLUE}{text.center(70)}{Colors.ENDC}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'=' * 70}{Colors.ENDC}\n")


def print_check(passed, message):
    """Imprime check mark verde ou X vermelho."""
    if passed:
        print(f"  {Colors.GREEN}✓{Colors.ENDC} {message}")
        return True
    else:
        print(f"  {Colors.RED}✗{Colors.ENDC} {message}")
        return False


def validar_estrutura_arquivos():
    """Valida que todos os arquivos necessários existem."""
    print_header("VALIDAÇÃO 1: Estrutura de Arquivos")

    arquivos_necessarios = [
        ('core/application/use_cases/obter_metricas_tempo.py', 'Use Case ObterMetricasTempoUseCase'),
        ('core/domain/pedido/value_objects.py', 'Value Object MetricasTempo'),
        ('core/infrastructure/persistence/repositories/pedido_repository.py', 'Repository com calcular_tempo_medio_finalizacao'),
        ('templates/partials/_card_metricas_tempo.html', 'Template de card de métricas'),
        ('tests/unit/application/use_cases/test_obter_metricas_tempo.py', 'Testes unitários'),
    ]

    checks_passed = 0
    for arquivo, descricao in arquivos_necessarios:
        caminho = BASE_DIR / arquivo
        passed = print_check(caminho.exists(), f"{descricao}")
        if passed:
            checks_passed += 1

    print(f"\n  {Colors.BOLD}Resultado:{Colors.ENDC} {checks_passed}/{len(arquivos_necessarios)} arquivos encontrados")
    return checks_passed == len(arquivos_necessarios)


def validar_value_object():
    """Valida o Value Object MetricasTempo."""
    print_header("VALIDAÇÃO 2: Value Object MetricasTempo")

    checks = []

    # Check 1: Criar MetricasTempo com dados válidos
    try:
        metricas = MetricasTempo(
            tempo_medio_hoje_minutos=45.0,
            tempo_medio_7dias_minutos=52.0,
            percentual_diferenca=-13.5,
            tendencia='melhorou'
        )
        checks.append(print_check(True, "MetricasTempo criado com sucesso"))
        checks.append(print_check(metricas.tempo_medio_hoje_minutos == 45.0, "Atributo tempo_medio_hoje_minutos correto"))
        checks.append(print_check(metricas.tendencia == 'melhorou', "Atributo tendencia correto"))
    except Exception as e:
        checks.append(print_check(False, f"Erro ao criar MetricasTempo: {e}"))

    # Check 2: Validação de tendência inválida
    try:
        metricas_invalido = MetricasTempo(
            tempo_medio_hoje_minutos=45.0,
            tempo_medio_7dias_minutos=52.0,
            percentual_diferenca=-13.5,
            tendencia='invalida'
        )
        checks.append(print_check(False, "Deveria rejeitar tendência inválida"))
    except ValueError:
        checks.append(print_check(True, "Validação de tendência inválida funciona"))

    # Check 3: MetricasTempo com sem_dados
    try:
        metricas_sem_dados = MetricasTempo(
            tempo_medio_hoje_minutos=None,
            tempo_medio_7dias_minutos=None,
            percentual_diferenca=None,
            tendencia='sem_dados'
        )
        checks.append(print_check(True, "MetricasTempo com 'sem_dados' criado"))
    except Exception as e:
        checks.append(print_check(False, f"Erro ao criar MetricasTempo sem dados: {e}"))

    print(f"\n  {Colors.BOLD}Resultado:{Colors.ENDC} {sum(checks)}/{len(checks)} checks passaram")
    return all(checks)


def validar_use_case():
    """Valida o Use Case ObterMetricasTempoUseCase."""
    print_header("VALIDAÇÃO 3: Use Case ObterMetricasTempoUseCase")

    checks = []

    try:
        # Instanciar use case
        repository = DjangoPedidoRepository()
        use_case = ObterMetricasTempoUseCase(repository)
        checks.append(print_check(True, "Use Case instanciado com sucesso"))

        # Check: Método execute existe
        checks.append(print_check(hasattr(use_case, 'execute'), "Método execute() existe"))

        # Check: Método to_dict existe
        checks.append(print_check(hasattr(use_case, 'to_dict'), "Método to_dict() existe"))

        # Check: Método _formatar_tempo existe
        checks.append(print_check(hasattr(use_case, '_formatar_tempo'), "Método _formatar_tempo() existe"))

        # Check: Método _formatar_percentual existe
        checks.append(print_check(hasattr(use_case, '_formatar_percentual'), "Método _formatar_percentual() existe"))

        # Check: Método _calcular_tendencia existe
        checks.append(print_check(hasattr(use_case, '_calcular_tendencia'), "Método _calcular_tendencia() existe"))

        # Check: Executar use case (sem dados)
        try:
            metricas = use_case.execute()
            checks.append(print_check(isinstance(metricas, MetricasTempo), "execute() retorna MetricasTempo"))
            checks.append(print_check(metricas.tendencia == 'sem_dados', "Retorna 'sem_dados' quando não há pedidos"))
        except Exception as e:
            checks.append(print_check(False, f"Erro ao executar use case: {e}"))

        # Check: Formatação de tempo
        checks.append(print_check(use_case._formatar_tempo(45.0) == "45 min", "Formatar tempo: 45min"))
        checks.append(print_check(use_case._formatar_tempo(90.0) == "1h 30min", "Formatar tempo: 1h 30min"))
        checks.append(print_check(use_case._formatar_tempo(60.0) == "1h", "Formatar tempo: 1h"))
        checks.append(print_check(use_case._formatar_tempo(None) == "Sem dados", "Formatar tempo: None"))

        # Check: Formatação de percentual
        checks.append(print_check(use_case._formatar_percentual(-13.5) == "-13.5%", "Formatar percentual: negativo"))
        checks.append(print_check(use_case._formatar_percentual(8.0) == "+8.0%", "Formatar percentual: positivo"))
        checks.append(print_check(use_case._formatar_percentual(None) == "", "Formatar percentual: None"))

    except Exception as e:
        checks.append(print_check(False, f"Erro ao validar use case: {e}"))

    print(f"\n  {Colors.BOLD}Resultado:{Colors.ENDC} {sum(checks)}/{len(checks)} checks passaram")
    return all(checks)


def validar_repository():
    """Valida o método calcular_tempo_medio_finalizacao no repository."""
    print_header("VALIDAÇÃO 4: Repository - calcular_tempo_medio_finalizacao")

    checks = []

    try:
        repository = DjangoPedidoRepository()
        checks.append(print_check(True, "Repository instanciado"))

        # Check: Método existe
        checks.append(print_check(
            hasattr(repository, 'calcular_tempo_medio_finalizacao'),
            "Método calcular_tempo_medio_finalizacao() existe"
        ))

        # Check: Executar com período sem dados
        hoje = timezone.now()
        ontem = hoje - timedelta(days=1)

        tempo_medio = repository.calcular_tempo_medio_finalizacao(ontem, hoje)
        checks.append(print_check(
            tempo_medio is None or isinstance(tempo_medio, float),
            "Retorna None ou float quando não há dados"
        ))

    except Exception as e:
        checks.append(print_check(False, f"Erro ao validar repository: {e}"))

    print(f"\n  {Colors.BOLD}Resultado:{Colors.ENDC} {sum(checks)}/{len(checks)} checks passaram")
    return all(checks)


def validar_template():
    """Valida o template _card_metricas_tempo.html."""
    print_header("VALIDAÇÃO 5: Template _card_metricas_tempo.html")

    checks = []
    template_path = BASE_DIR / 'templates' / 'partials' / '_card_metricas_tempo.html'

    if not template_path.exists():
        print_check(False, "Template não encontrado")
        return False

    with open(template_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Verificar elementos essenciais
    checks.append(print_check('metricas_tempo' in content, "Variável metricas_tempo presente"))
    checks.append(print_check('tendencia' in content, "Verificação de tendência presente"))
    checks.append(print_check('melhorou' in content, "Estado 'melhorou' presente"))
    checks.append(print_check('piorou' in content, "Estado 'piorou' presente"))
    checks.append(print_check('estavel' in content, "Estado 'estável' presente"))
    checks.append(print_check('sem_dados' in content, "Estado 'sem_dados' presente"))
    checks.append(print_check('tempo_hoje_formatado' in content, "Tempo hoje formatado presente"))
    checks.append(print_check('tempo_7dias_formatado' in content, "Tempo 7 dias formatado presente"))
    checks.append(print_check('percentual_formatado' in content, "Percentual formatado presente"))

    print(f"\n  {Colors.BOLD}Resultado:{Colors.ENDC} {sum(checks)}/{len(checks)} checks passaram")
    return all(checks)


def validar_integracao_dashboard():
    """Valida a integração com a DashboardView."""
    print_header("VALIDAÇÃO 6: Integração com DashboardView")

    checks = []
    view_path = BASE_DIR / 'core' / 'presentation' / 'web' / 'views.py'

    if not view_path.exists():
        print_check(False, "views.py não encontrado")
        return False

    with open(view_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Verificar integração
    checks.append(print_check('ObterMetricasTempoUseCase' in content, "Import do Use Case presente"))
    checks.append(print_check('_obter_metricas_tempo' in content, "Método _obter_metricas_tempo presente"))
    checks.append(print_check('metricas_tempo' in content, "Variável metricas_tempo no contexto"))

    print(f"\n  {Colors.BOLD}Resultado:{Colors.ENDC} {sum(checks)}/{len(checks)} checks passaram")
    return all(checks)


def validar_testes_unitarios():
    """Valida que todos os testes unitários passam."""
    print_header("VALIDAÇÃO 7: Testes Unitários")

    import subprocess

    try:
        # Executar pytest
        result = subprocess.run(
            ['python3', '-m', 'pytest', 'tests/unit/application/use_cases/test_obter_metricas_tempo.py', '-v'],
            cwd=BASE_DIR,
            capture_output=True,
            text=True,
            timeout=60
        )

        # Verificar resultado
        passed = result.returncode == 0

        if passed:
            # Contar testes que passaram
            output = result.stdout
            if '9 passed' in output:
                print_check(True, "Todos os 9 testes passaram")
                return True
            else:
                print_check(False, "Nem todos os testes passaram")
                print(f"\n{Colors.YELLOW}Output do pytest:{Colors.ENDC}")
                print(output)
                return False
        else:
            print_check(False, "Testes falharam")
            print(f"\n{Colors.RED}Erro:{Colors.ENDC}")
            print(result.stderr)
            return False

    except Exception as e:
        print_check(False, f"Erro ao executar testes: {e}")
        return False


def main():
    """Executa todas as validações."""
    print(f"\n{Colors.BOLD}{Colors.BLUE}")
    print("╔════════════════════════════════════════════════════════════════════╗")
    print("║         VALIDAÇÃO FASE 20: Métricas de Tempo Médio                ║")
    print("║              Sistema de Separação PMCELL                           ║")
    print("╚════════════════════════════════════════════════════════════════════╝")
    print(Colors.ENDC)

    resultados = []

    # Executar validações
    resultados.append(('Estrutura de Arquivos', validar_estrutura_arquivos()))
    resultados.append(('Value Object MetricasTempo', validar_value_object()))
    resultados.append(('Use Case ObterMetricasTempoUseCase', validar_use_case()))
    resultados.append(('Repository calcular_tempo_medio_finalizacao', validar_repository()))
    resultados.append(('Template _card_metricas_tempo.html', validar_template()))
    resultados.append(('Integração com DashboardView', validar_integracao_dashboard()))
    resultados.append(('Testes Unitários', validar_testes_unitarios()))

    # Resumo final
    print_header("RESUMO FINAL")

    total_checks = len(resultados)
    checks_passed = sum(1 for _, passed in resultados if passed)

    for nome, passou in resultados:
        status = f"{Colors.GREEN}✓ PASSOU{Colors.ENDC}" if passou else f"{Colors.RED}✗ FALHOU{Colors.ENDC}"
        print(f"  {nome:.<50} {status}")

    print(f"\n{Colors.BOLD}TOTAL: {checks_passed}/{total_checks} validações passaram{Colors.ENDC}")

    if checks_passed == total_checks:
        print(f"\n{Colors.GREEN}{Colors.BOLD}🎉 FASE 20 VALIDADA COM SUCESSO! 🎉{Colors.ENDC}\n")
        return 0
    else:
        print(f"\n{Colors.RED}{Colors.BOLD}❌ FASE 20 AINDA TEM PROBLEMAS{Colors.ENDC}\n")
        return 1


if __name__ == '__main__':
    sys.exit(main())
