#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script de Validação Pré-Deploy - Fase 35
Valida configurações antes de fazer deploy para produção

Usage:
    python validar_fase35.py                 # Valida desenvolvimento
    python validar_fase35.py --production    # Valida produção (requer .env)
"""

import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.dirname(__file__))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'separacao_pmcell.settings')
django.setup()

from django.conf import settings


class Colors:
    """Cores para output no terminal"""
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'
    END = '\033[0m'


def print_header(text):
    """Imprime cabeçalho colorido"""
    print(f"\n{Colors.BLUE}{Colors.BOLD}{'=' * 70}{Colors.END}")
    print(f"{Colors.BLUE}{Colors.BOLD}{text.center(70)}{Colors.END}")
    print(f"{Colors.BLUE}{Colors.BOLD}{'=' * 70}{Colors.END}\n")


def print_success(text):
    """Imprime mensagem de sucesso"""
    print(f"{Colors.GREEN}✓ {text}{Colors.END}")


def print_error(text):
    """Imprime mensagem de erro"""
    print(f"{Colors.RED}✗ {text}{Colors.END}")


def print_warning(text):
    """Imprime mensagem de aviso"""
    print(f"{Colors.YELLOW}⚠ {text}{Colors.END}")


def print_info(text):
    """Imprime informação"""
    print(f"  {text}")


def validate_basic_config():
    """Valida configurações básicas"""
    print_header("VALIDAÇÃO DE CONFIGURAÇÕES BÁSICAS")

    errors = []
    warnings = []

    # 1. SECRET_KEY
    if settings.SECRET_KEY == 'django-insecure-dev-key-change-in-production-8#v7x$@p&m9z2k!':
        if not settings.DEBUG:
            errors.append("SECRET_KEY de desenvolvimento em produção!")
        else:
            warnings.append("Usando SECRET_KEY de desenvolvimento (OK para dev)")
    else:
        print_success("SECRET_KEY configurado")

    # 2. DEBUG
    if settings.DEBUG:
        warnings.append("DEBUG=True (certifique-se de que isso é desenvolvimento)")
    else:
        print_success("DEBUG=False (produção)")

    # 3. ALLOWED_HOSTS
    if len(settings.ALLOWED_HOSTS) > 0:
        print_success(f"ALLOWED_HOSTS: {', '.join(settings.ALLOWED_HOSTS)}")
    else:
        errors.append("ALLOWED_HOSTS vazio!")

    # 4. CSRF_TRUSTED_ORIGINS
    if not settings.DEBUG and len(settings.CSRF_TRUSTED_ORIGINS) == 0:
        errors.append("CSRF_TRUSTED_ORIGINS vazio em produção!")
    elif len(settings.CSRF_TRUSTED_ORIGINS) > 0:
        print_success(f"CSRF_TRUSTED_ORIGINS: {', '.join(settings.CSRF_TRUSTED_ORIGINS)}")

    return errors, warnings


def validate_database():
    """Valida configuração de banco de dados"""
    print_header("VALIDAÇÃO DE BANCO DE DADOS")

    errors = []
    warnings = []

    db_config = settings.DATABASES['default']
    engine = db_config['ENGINE']

    if 'sqlite' in engine:
        warnings.append("Usando SQLite (OK para desenvolvimento, não recomendado para produção)")
        print_info(f"Database: {db_config.get('NAME')}")
    elif 'postgresql' in engine:
        print_success("Usando PostgreSQL (produção)")
        print_info(f"Database: {db_config.get('NAME')}")
        print_info(f"Host: {db_config.get('HOST', 'padrão')}")
    else:
        errors.append(f"Engine de banco desconhecido: {engine}")

    return errors, warnings


def validate_redis():
    """Valida configuração do Redis"""
    print_header("VALIDAÇÃO DO REDIS")

    errors = []
    warnings = []

    # Cache
    cache_location = settings.CACHES['default']['LOCATION']
    if 'redis://' in cache_location:
        print_success(f"Cache Redis: {cache_location}")
    else:
        errors.append(f"Redis esperado para cache, encontrado: {cache_location}")

    # Channel Layers
    channel_backend = settings.CHANNEL_LAYERS['default']['BACKEND']
    if 'redis' in channel_backend.lower():
        print_success(f"Channel Layer: {channel_backend}")
    else:
        errors.append(f"Redis esperado para channel layers, encontrado: {channel_backend}")

    return errors, warnings


def validate_static_files():
    """Valida configuração de arquivos estáticos"""
    print_header("VALIDAÇÃO DE ARQUIVOS ESTÁTICOS")

    errors = []
    warnings = []

    # STATIC_URL
    if settings.STATIC_URL == '/static/':
        print_success(f"STATIC_URL: {settings.STATIC_URL}")
    else:
        errors.append(f"STATIC_URL incorreto: {settings.STATIC_URL}")

    # STATIC_ROOT
    if settings.STATIC_ROOT:
        print_success(f"STATIC_ROOT: {settings.STATIC_ROOT}")
    else:
        errors.append("STATIC_ROOT não configurado!")

    # Whitenoise Middleware
    if 'whitenoise.middleware.WhiteNoiseMiddleware' in settings.MIDDLEWARE:
        print_success("WhiteNoiseMiddleware configurado")
    else:
        errors.append("WhiteNoiseMiddleware não encontrado!")

    # Whitenoise Storage
    if 'staticfiles' in settings.STORAGES:
        backend = settings.STORAGES['staticfiles']['BACKEND']
        if 'whitenoise' in backend.lower():
            print_success(f"Whitenoise Storage: {backend}")
        else:
            warnings.append(f"Whitenoise esperado, encontrado: {backend}")

    return errors, warnings


def validate_apps_and_middleware():
    """Valida INSTALLED_APPS e MIDDLEWARE"""
    print_header("VALIDAÇÃO DE APPS E MIDDLEWARE")

    errors = []
    warnings = []

    # Daphne antes de staticfiles
    if 'daphne' in settings.INSTALLED_APPS:
        daphne_idx = settings.INSTALLED_APPS.index('daphne')
        staticfiles_idx = settings.INSTALLED_APPS.index('django.contrib.staticfiles')
        if daphne_idx < staticfiles_idx:
            print_success("Daphne configurado corretamente (antes de staticfiles)")
        else:
            errors.append("Daphne deve vir ANTES de staticfiles!")
    else:
        errors.append("Daphne não encontrado em INSTALLED_APPS!")

    # Channels
    if 'channels' in settings.INSTALLED_APPS:
        print_success("Django Channels instalado")
    else:
        errors.append("Django Channels não encontrado!")

    # Custom user model
    if settings.AUTH_USER_MODEL == 'core.Usuario':
        print_success("Custom user model configurado")
    else:
        errors.append(f"AUTH_USER_MODEL incorreto: {settings.AUTH_USER_MODEL}")

    # ASGI Application
    if settings.ASGI_APPLICATION == 'separacao_pmcell.asgi.application':
        print_success("ASGI Application configurado")
    else:
        errors.append(f"ASGI_APPLICATION incorreto: {settings.ASGI_APPLICATION}")

    return errors, warnings


def validate_localization():
    """Valida configurações de localização"""
    print_header("VALIDAÇÃO DE LOCALIZAÇÃO")

    errors = []
    warnings = []

    if settings.LANGUAGE_CODE == 'pt-br':
        print_success("LANGUAGE_CODE: pt-br")
    else:
        warnings.append(f"LANGUAGE_CODE: {settings.LANGUAGE_CODE} (esperado: pt-br)")

    if settings.TIME_ZONE == 'America/Sao_Paulo':
        print_success("TIME_ZONE: America/Sao_Paulo")
    else:
        warnings.append(f"TIME_ZONE: {settings.TIME_ZONE} (esperado: America/Sao_Paulo)")

    return errors, warnings


def print_summary(all_errors, all_warnings):
    """Imprime resumo final"""
    print_header("RESUMO DA VALIDAÇÃO")

    total_errors = sum(len(e) for e in all_errors)
    total_warnings = sum(len(w) for w in all_warnings)

    if total_errors > 0:
        print_error(f"\nEncontrados {total_errors} erro(s):")
        for errors in all_errors:
            for error in errors:
                print(f"  {Colors.RED}• {error}{Colors.END}")

    if total_warnings > 0:
        print_warning(f"\nEncontrados {total_warnings} aviso(s):")
        for warnings in all_warnings:
            for warning in warnings:
                print(f"  {Colors.YELLOW}• {warning}{Colors.END}")

    print()

    if total_errors == 0:
        if total_warnings == 0:
            print_success("✓ Todas as validações passaram! Sistema pronto para deploy.")
            return 0
        else:
            print_warning("⚠ Validação passou com avisos. Revise antes de fazer deploy.")
            return 0
    else:
        print_error("✗ Validação falhou! Corrija os erros antes de fazer deploy.")
        return 1


def main():
    """Função principal"""
    production_mode = '--production' in sys.argv

    if production_mode:
        print_header("MODO DE VALIDAÇÃO: PRODUÇÃO")
        if not os.environ.get('DATABASE_URL'):
            print_error("DATABASE_URL não configurado! Configure o .env para simular produção.")
            return 1
    else:
        print_header("MODO DE VALIDAÇÃO: DESENVOLVIMENTO")

    all_errors = []
    all_warnings = []

    # Executar todas as validações
    errors, warnings = validate_basic_config()
    all_errors.append(errors)
    all_warnings.append(warnings)

    errors, warnings = validate_database()
    all_errors.append(errors)
    all_warnings.append(warnings)

    errors, warnings = validate_redis()
    all_errors.append(errors)
    all_warnings.append(warnings)

    errors, warnings = validate_static_files()
    all_errors.append(errors)
    all_warnings.append(warnings)

    errors, warnings = validate_apps_and_middleware()
    all_errors.append(errors)
    all_warnings.append(warnings)

    errors, warnings = validate_localization()
    all_errors.append(errors)
    all_warnings.append(warnings)

    # Imprimir resumo
    return print_summary(all_errors, all_warnings)


if __name__ == '__main__':
    sys.exit(main())
