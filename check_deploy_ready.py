#!/usr/bin/env python3
"""
Script de Validação Pré-Deploy para Railway
Verifica se o projeto está pronto para deploy
"""

import os
import sys
from pathlib import Path

# Cores para terminal
RED = '\033[0;31m'
GREEN = '\033[0;32m'
YELLOW = '\033[1;33m'
BLUE = '\033[0;34m'
NC = '\033[0m'  # No Color

def print_header(text):
    print(f"\n{BLUE}{'='*60}{NC}")
    print(f"{BLUE}{text:^60}{NC}")
    print(f"{BLUE}{'='*60}{NC}\n")

def check_ok(text):
    print(f"{GREEN}✅ {text}{NC}")

def check_fail(text):
    print(f"{RED}❌ {text}{NC}")
    return False

def check_warning(text):
    print(f"{YELLOW}⚠️  {text}{NC}")

def check_info(text):
    print(f"{BLUE}ℹ️  {text}{NC}")

def main():
    print_header("Validação Pré-Deploy - Railway")

    all_checks_passed = True

    # 1. Verificar estrutura de diretórios
    print(f"{YELLOW}[1] Verificando estrutura de diretórios...{NC}")

    backend_dir = Path("backend")
    if backend_dir.exists():
        check_ok("Diretório backend/ encontrado")
    else:
        all_checks_passed = check_fail("Diretório backend/ não encontrado!")

    # 2. Verificar arquivos essenciais
    print(f"\n{YELLOW}[2] Verificando arquivos essenciais...{NC}")

    essential_files = {
        "backend/Dockerfile": "Dockerfile para build",
        "railway.json": "Configuração Railway",
        "backend/requirements.txt": "Dependências Python",
        "backend/manage.py": "Django manage.py",
        "backend/separacao_pmcell/settings.py": "Django settings",
        "backend/separacao_pmcell/asgi.py": "ASGI application",
    }

    for file_path, description in essential_files.items():
        if Path(file_path).exists():
            check_ok(f"{description}: {file_path}")
        else:
            all_checks_passed = check_fail(f"{description} não encontrado: {file_path}")

    # 3. Verificar dependências no requirements.txt
    print(f"\n{YELLOW}[3] Verificando dependências...{NC}")

    try:
        with open("backend/requirements.txt", "r") as f:
            requirements = f.read().lower()

        required_packages = [
            "django",
            "psycopg2-binary",
            "daphne",
            "channels",
            "channels-redis",
            "redis",
            "whitenoise",
            "python-decouple",
            "dj-database-url",
        ]

        for package in required_packages:
            if package in requirements:
                check_ok(f"Pacote encontrado: {package}")
            else:
                all_checks_passed = check_fail(f"Pacote não encontrado: {package}")
    except FileNotFoundError:
        all_checks_passed = check_fail("Arquivo requirements.txt não encontrado!")

    # 4. Verificar Dockerfile
    print(f"\n{YELLOW}[4] Verificando Dockerfile...{NC}")

    try:
        with open("backend/Dockerfile", "r") as f:
            dockerfile = f.read()

        dockerfile_checks = [
            ("FROM python", "Imagem base Python"),
            ("WORKDIR", "Working directory definido"),
            ("COPY requirements.txt", "Cópia de requirements"),
            ("pip install", "Instalação de dependências"),
            ("daphne", "Comando Daphne para ASGI"),
            ("$PORT", "Uso da variável $PORT do Railway"),
        ]

        for check_str, description in dockerfile_checks:
            if check_str in dockerfile:
                check_ok(description)
            else:
                check_warning(f"{description} pode estar faltando")
    except FileNotFoundError:
        all_checks_passed = check_fail("Dockerfile não encontrado!")

    # 5. Verificar railway.json
    print(f"\n{YELLOW}[5] Verificando railway.json...{NC}")

    try:
        import json
        with open("railway.json", "r") as f:
            railway_config = json.load(f)

        if "build" in railway_config:
            check_ok("Configuração de build presente")

            if railway_config["build"].get("builder") == "DOCKERFILE":
                check_ok("Builder: DOCKERFILE")
            else:
                check_warning("Builder não é DOCKERFILE")

            if "dockerfilePath" in railway_config["build"]:
                check_ok(f"Dockerfile path: {railway_config['build']['dockerfilePath']}")
        else:
            check_warning("Configuração de build não encontrada")

        if "deploy" in railway_config:
            check_ok("Configuração de deploy presente")

            if "startCommand" in railway_config["deploy"]:
                check_ok(f"Start command: {railway_config['deploy']['startCommand']}")
        else:
            check_warning("Configuração de deploy não encontrada")

    except FileNotFoundError:
        all_checks_passed = check_fail("railway.json não encontrado!")
    except json.JSONDecodeError:
        all_checks_passed = check_fail("railway.json inválido (erro de JSON)!")

    # 6. Verificar settings.py
    print(f"\n{YELLOW}[6] Verificando Django settings.py...{NC}")

    try:
        with open("backend/separacao_pmcell/settings.py", "r") as f:
            settings = f.read()

        settings_checks = [
            ("from decouple import config", "python-decouple importado"),
            ("import dj_database_url", "dj-database-url importado"),
            ("SECRET_KEY = config", "SECRET_KEY usando decouple"),
            ("DEBUG = config", "DEBUG usando decouple"),
            ("ALLOWED_HOSTS = config", "ALLOWED_HOSTS usando decouple"),
            ("DATABASE_URL", "DATABASE_URL configurado"),
            ("REDIS_URL", "REDIS_URL configurado"),
            ("whitenoise", "Whitenoise configurado"),
            ("ASGI_APPLICATION", "ASGI_APPLICATION definido"),
            ("CHANNEL_LAYERS", "Channel layers configurado"),
        ]

        for check_str, description in settings_checks:
            if check_str in settings:
                check_ok(description)
            else:
                check_warning(f"{description} pode estar faltando")
    except FileNotFoundError:
        all_checks_passed = check_fail("settings.py não encontrado!")

    # 7. Verificar .env.example
    print(f"\n{YELLOW}[7] Verificando .env.example...{NC}")

    try:
        with open("backend/.env.example", "r") as f:
            env_example = f.read()

        check_ok(".env.example encontrado")

        env_vars = [
            "SECRET_KEY",
            "DEBUG",
            "ALLOWED_HOSTS",
            "DATABASE_URL",
            "REDIS_URL",
            "CSRF_TRUSTED_ORIGINS",
        ]

        for var in env_vars:
            if var in env_example:
                check_ok(f"Variável documentada: {var}")
            else:
                check_warning(f"Variável não documentada: {var}")
    except FileNotFoundError:
        check_warning(".env.example não encontrado (não obrigatório, mas recomendado)")

    # 8. Verificar migrations
    print(f"\n{YELLOW}[8] Verificando migrations...{NC}")

    migrations_dir = Path("backend/core/migrations")
    if migrations_dir.exists():
        migration_files = list(migrations_dir.glob("*.py"))
        migration_files = [f for f in migration_files if f.name != "__init__.py"]

        if migration_files:
            check_ok(f"Migrations encontradas: {len(migration_files)} arquivo(s)")
        else:
            check_warning("Nenhuma migration encontrada (pode ser necessário criar)")
    else:
        check_warning("Diretório de migrations não encontrado")

    # 9. Verificar static files
    print(f"\n{YELLOW}[9] Verificando arquivos estáticos...{NC}")

    static_dir = Path("backend/static")
    if static_dir.exists():
        check_ok("Diretório static/ encontrado")
    else:
        check_warning("Diretório static/ não encontrado")

    staticfiles_dir = Path("backend/staticfiles")
    if staticfiles_dir.exists():
        check_info("Diretório staticfiles/ existe (será recriado no deploy)")

    # 10. Resumo final
    print_header("Resumo da Validação")

    if all_checks_passed:
        print(f"{GREEN}✅ Todos os checks essenciais passaram!{NC}")
        print(f"{GREEN}✅ Projeto pronto para deploy no Railway!{NC}\n")

        print(f"{BLUE}Próximos passos:{NC}")
        print("1. Execute: ./deploy_railway.sh")
        print("2. Ou siga o guia manual em DEPLOY_QUICKSTART.md\n")
        return 0
    else:
        print(f"{RED}❌ Alguns checks falharam!{NC}")
        print(f"{YELLOW}⚠️  Corrija os problemas antes de fazer deploy.{NC}\n")

        print(f"{BLUE}Para mais informações:{NC}")
        print("- Veja RAILWAY_DEPLOY_GUIDE.md")
        print("- Veja DEPLOY_QUICKSTART.md\n")
        return 1

if __name__ == "__main__":
    sys.exit(main())
