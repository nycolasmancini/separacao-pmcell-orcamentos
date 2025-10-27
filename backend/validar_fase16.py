#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de validação da Fase 16: Feedback Visual e Animações no Upload

Valida:
1. Existência dos arquivos estáticos (CSS e JS)
2. Integração correta no template
3. Configuração de arquivos estáticos no settings.py
4. Estrutura de pastas
5. Tamanho e qualidade dos arquivos

Uso:
    python validar_fase16.py
"""

import os
import sys


def print_header(text):
    """Imprime cabeçalho formatado."""
    print("\n" + "=" * 70)
    print(f"  {text}")
    print("=" * 70)


def print_success(text):
    """Imprime mensagem de sucesso."""
    print(f"✅ {text}")


def print_error(text):
    """Imprime mensagem de erro."""
    print(f"❌ {text}")


def print_info(text):
    """Imprime mensagem informativa."""
    print(f"ℹ️  {text}")


def validate_file_exists(file_path, description):
    """Valida se um arquivo existe."""
    if os.path.exists(file_path):
        size = os.path.getsize(file_path)
        print_success(f"{description} existe ({size} bytes)")
        return True
    else:
        print_error(f"{description} NÃO encontrado: {file_path}")
        return False


def validate_file_content(file_path, search_strings, description):
    """Valida se um arquivo contém determinadas strings."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        missing = []
        for search_str in search_strings:
            if search_str not in content:
                missing.append(search_str)

        if not missing:
            print_success(f"{description} contém todas as strings esperadas")
            return True
        else:
            print_error(f"{description} está faltando: {', '.join(missing)}")
            return False
    except Exception as e:
        print_error(f"Erro ao ler {file_path}: {e}")
        return False


def main():
    """Função principal de validação."""
    print_header("VALIDAÇÃO DA FASE 16: FEEDBACK VISUAL E ANIMAÇÕES")

    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

    # Contadores
    total_checks = 0
    passed_checks = 0

    # ============================================
    # 1. VALIDAR ESTRUTURA DE PASTAS
    # ============================================
    print_header("1. ESTRUTURA DE PASTAS")

    folders = [
        (os.path.join(BASE_DIR, 'static'), "Pasta static/"),
        (os.path.join(BASE_DIR, 'static', 'css'), "Pasta static/css/"),
        (os.path.join(BASE_DIR, 'static', 'js'), "Pasta static/js/"),
    ]

    for folder_path, description in folders:
        total_checks += 1
        if os.path.isdir(folder_path):
            print_success(f"{description} existe")
            passed_checks += 1
        else:
            print_error(f"{description} NÃO encontrada")

    # ============================================
    # 2. VALIDAR ARQUIVOS ESTÁTICOS
    # ============================================
    print_header("2. ARQUIVOS ESTÁTICOS")

    # Arquivo CSS
    css_file = os.path.join(BASE_DIR, 'static', 'css', 'animations.css')
    total_checks += 1
    if validate_file_exists(css_file, "animations.css"):
        passed_checks += 1

        # Validar conteúdo do CSS
        total_checks += 1
        css_required = [
            '@keyframes spin',
            '@keyframes slideDown',
            '@keyframes fadeIn',
            '@keyframes shake',
            '.spinner',
            '.loading-overlay',
            'progress-bar',
        ]
        if validate_file_content(css_file, css_required, "animations.css"):
            passed_checks += 1

    # Arquivo JavaScript
    js_file = os.path.join(BASE_DIR, 'static', 'js', 'upload_feedback.js')
    total_checks += 1
    if validate_file_exists(js_file, "upload_feedback.js"):
        passed_checks += 1

        # Validar conteúdo do JS
        total_checks += 1
        js_required = [
            'createLoadingOverlay',
            'createProgressBar',
            'updateEmbalagemValidation',
            'validateFile',
            'handleFormSubmit',
            'CONFIG',
        ]
        if validate_file_content(js_file, js_required, "upload_feedback.js"):
            passed_checks += 1

    # ============================================
    # 3. VALIDAR INTEGRAÇÃO NO TEMPLATE
    # ============================================
    print_header("3. INTEGRAÇÃO NO TEMPLATE")

    template_file = os.path.join(BASE_DIR, 'templates', 'upload_orcamento.html')
    total_checks += 1
    if validate_file_exists(template_file, "upload_orcamento.html"):
        passed_checks += 1

        # Validar que o template carrega os arquivos estáticos
        total_checks += 1
        template_required = [
            "{% load static %}",
            "{% static 'css/animations.css' %}",
            "{% static 'js/upload_feedback.js' %}",
        ]
        if validate_file_content(template_file, template_required, "Template de upload"):
            passed_checks += 1

    # Validar base.html tem bloco extra_css
    base_template = os.path.join(BASE_DIR, 'templates', 'base.html')
    total_checks += 1
    if validate_file_exists(base_template, "base.html"):
        passed_checks += 1

        total_checks += 1
        base_required = ["{% block extra_css %}"]
        if validate_file_content(base_template, base_required, "Template base"):
            passed_checks += 1

    # ============================================
    # 4. VALIDAR SETTINGS.PY
    # ============================================
    print_header("4. CONFIGURAÇÃO DO DJANGO")

    settings_file = os.path.join(BASE_DIR, 'separacao_pmcell', 'settings.py')
    total_checks += 1
    if validate_file_exists(settings_file, "settings.py"):
        passed_checks += 1

        # Validar configurações de static files
        total_checks += 1
        settings_required = [
            "STATIC_URL",
            "STATIC_ROOT",
            "STATICFILES_DIRS",
            "'django.contrib.staticfiles'",
        ]
        if validate_file_content(settings_file, settings_required, "Configuração de static files"):
            passed_checks += 1

    # ============================================
    # 5. VALIDAR QUALIDADE DOS ARQUIVOS
    # ============================================
    print_header("5. QUALIDADE DOS ARQUIVOS")

    # Validar tamanho mínimo dos arquivos (garantir que não estão vazios)
    total_checks += 1
    css_size = os.path.getsize(css_file) if os.path.exists(css_file) else 0
    if css_size > 1000:  # Pelo menos 1KB
        print_success(f"animations.css tem tamanho adequado ({css_size} bytes)")
        passed_checks += 1
    else:
        print_error(f"animations.css muito pequeno ({css_size} bytes)")

    total_checks += 1
    js_size = os.path.getsize(js_file) if os.path.exists(js_file) else 0
    if js_size > 2000:  # Pelo menos 2KB
        print_success(f"upload_feedback.js tem tamanho adequado ({js_size} bytes)")
        passed_checks += 1
    else:
        print_error(f"upload_feedback.js muito pequeno ({js_size} bytes)")

    # Validar encoding UTF-8
    total_checks += 1
    try:
        with open(css_file, 'r', encoding='utf-8') as f:
            f.read()
        with open(js_file, 'r', encoding='utf-8') as f:
            f.read()
        print_success("Todos os arquivos estão em UTF-8")
        passed_checks += 1
    except UnicodeDecodeError:
        print_error("Erro de encoding em alguns arquivos")

    # ============================================
    # 6. FUNCIONALIDADES IMPLEMENTADAS
    # ============================================
    print_header("6. FUNCIONALIDADES IMPLEMENTADAS")

    features = [
        "✨ Loading spinner durante processamento do PDF",
        "📊 Progress bar para upload de arquivos grandes",
        "🎨 Animações de transição (slide down, fade in/out, scale)",
        "🔄 Validação em tempo real de embalagem vs logística",
        "💬 Tooltips explicativos automáticos",
        "⚠️  Mensagens de erro inline com ícones SVG",
        "✅ Feedback visual de sucesso",
        "🚫 Validação client-side de arquivos PDF",
        "🎯 Animação de shake para campos com erro",
        "♿ Suporte para prefers-reduced-motion (acessibilidade)",
        "📱 Responsivo e adaptável",
    ]

    print("\nFuncionalidades da Fase 16:")
    for feature in features:
        print(f"  {feature}")

    # ============================================
    # RESULTADO FINAL
    # ============================================
    print_header("RESULTADO DA VALIDAÇÃO")

    percentage = (passed_checks / total_checks * 100) if total_checks > 0 else 0

    print(f"\nChecks passados: {passed_checks}/{total_checks} ({percentage:.1f}%)")

    if passed_checks == total_checks:
        print_success("FASE 16 VALIDADA COM SUCESSO! ✨")
        print_info("Todos os arquivos e configurações estão corretos.")
        print_info("Próximo passo: Testar manualmente no navegador (http://localhost:8000)")
        return 0
    elif percentage >= 80:
        print_info("FASE 16 QUASE COMPLETA")
        print_info("Alguns checks falharam, mas a maioria está OK.")
        return 1
    else:
        print_error("FASE 16 INCOMPLETA")
        print_error("Vários checks falharam. Revise os erros acima.")
        return 2


if __name__ == '__main__':
    sys.exit(main())
