#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Testes de Validação de Configuração para Deploy - Fase 35
Garante que as configurações de produção estão corretas antes do deploy
"""

import os
import pytest
from django.conf import settings


class TestDeployConfiguration:
    """Testes de configuração para deploy em produção"""

    def test_secret_key_nao_pode_ser_chave_de_desenvolvimento_em_producao(self):
        """
        GIVEN: ambiente de produção (DEBUG=False)
        WHEN: verifico SECRET_KEY
        THEN: não deve ser a chave de desenvolvimento padrão
        """
        # Simula produção
        if not settings.DEBUG:
            assert settings.SECRET_KEY != 'django-insecure-dev-key-change-in-production-8#v7x$@p&m9z2k!', \
                "SECRET_KEY de desenvolvimento detectada em produção! Configure SECRET_KEY no .env"

    def test_debug_deve_ser_false_em_producao(self):
        """
        GIVEN: variável DATABASE_URL configurada (indica produção)
        WHEN: verifico DEBUG
        THEN: deve ser False em produção
        """
        # Se DATABASE_URL existe, assume produção
        database_url = os.environ.get('DATABASE_URL')
        if database_url:
            assert settings.DEBUG is False, \
                "DEBUG=True detectado em produção! Configure DEBUG=False no .env"

    def test_allowed_hosts_deve_estar_configurado(self):
        """
        GIVEN: configuração do Django
        WHEN: verifico ALLOWED_HOSTS
        THEN: deve conter pelo menos um host
        """
        assert len(settings.ALLOWED_HOSTS) > 0, \
            "ALLOWED_HOSTS vazio! Configure ALLOWED_HOSTS no .env"

        # Em desenvolvimento, deve ter localhost
        if settings.DEBUG:
            assert 'localhost' in settings.ALLOWED_HOSTS or '127.0.0.1' in settings.ALLOWED_HOSTS, \
                "ALLOWED_HOSTS deve conter localhost ou 127.0.0.1 em desenvolvimento"

    def test_csrf_trusted_origins_deve_estar_configurado_em_producao(self):
        """
        GIVEN: ambiente de produção
        WHEN: verifico CSRF_TRUSTED_ORIGINS
        THEN: deve estar configurado (não vazio)
        """
        # Apenas valida em produção
        if not settings.DEBUG:
            assert len(settings.CSRF_TRUSTED_ORIGINS) > 0, \
                "CSRF_TRUSTED_ORIGINS vazio em produção! Configure no .env (ex: https://seu-app.railway.app)"

    def test_database_configurado_corretamente(self):
        """
        GIVEN: configuração do Django
        WHEN: verifico DATABASES
        THEN: deve estar configurado com um backend válido
        """
        assert 'default' in settings.DATABASES, \
            "Banco de dados padrão não configurado!"

        db_engine = settings.DATABASES['default']['ENGINE']
        assert db_engine in [
            'django.db.backends.sqlite3',
            'django.db.backends.postgresql'
        ], f"Engine de banco inválido: {db_engine}"

    def test_postgresql_em_producao(self):
        """
        GIVEN: ambiente de produção (DATABASE_URL configurado)
        WHEN: verifico o banco de dados
        THEN: deve ser PostgreSQL
        """
        database_url = os.environ.get('DATABASE_URL')
        if database_url:
            db_engine = settings.DATABASES['default']['ENGINE']
            assert db_engine == 'django.db.backends.postgresql', \
                f"PostgreSQL esperado em produção, encontrado: {db_engine}"

    def test_redis_url_configurado(self):
        """
        GIVEN: configuração do Django
        WHEN: verifico REDIS_URL
        THEN: deve estar configurado
        """
        # Redis é usado para cache e channel layers
        assert hasattr(settings, 'CACHES'), "CACHES não configurado!"
        cache_location = settings.CACHES['default']['LOCATION']
        assert cache_location.startswith('redis://'), \
            f"Redis esperado para cache, encontrado: {cache_location}"

    def test_whitenoise_middleware_presente(self):
        """
        GIVEN: configuração do Django
        WHEN: verifico MIDDLEWARE
        THEN: Whitenoise deve estar presente
        """
        assert 'whitenoise.middleware.WhiteNoiseMiddleware' in settings.MIDDLEWARE, \
            "WhiteNoiseMiddleware não encontrado! Necessário para servir arquivos estáticos em produção"

        # Deve estar logo após SecurityMiddleware
        security_idx = settings.MIDDLEWARE.index('django.middleware.security.SecurityMiddleware')
        whitenoise_idx = settings.MIDDLEWARE.index('whitenoise.middleware.WhiteNoiseMiddleware')
        assert whitenoise_idx == security_idx + 1, \
            "WhiteNoiseMiddleware deve vir logo após SecurityMiddleware"

    def test_static_files_configurados(self):
        """
        GIVEN: configuração do Django
        WHEN: verifico configurações de arquivos estáticos
        THEN: STATIC_ROOT e STATIC_URL devem estar configurados
        """
        assert settings.STATIC_URL == '/static/', \
            f"STATIC_URL incorreto: {settings.STATIC_URL}"

        assert settings.STATIC_ROOT is not None, \
            "STATIC_ROOT não configurado!"

    def test_whitenoise_storage_configurado(self):
        """
        GIVEN: configuração do Django
        WHEN: verifico STORAGES
        THEN: Whitenoise deve estar configurado para staticfiles
        """
        assert 'staticfiles' in settings.STORAGES, \
            "STORAGES['staticfiles'] não configurado!"

        staticfiles_backend = settings.STORAGES['staticfiles']['BACKEND']
        assert 'whitenoise' in staticfiles_backend.lower(), \
            f"Whitenoise esperado para staticfiles, encontrado: {staticfiles_backend}"

    def test_channel_layers_configurado(self):
        """
        GIVEN: configuração do Django
        WHEN: verifico CHANNEL_LAYERS
        THEN: Redis deve estar configurado para WebSockets
        """
        assert 'default' in settings.CHANNEL_LAYERS, \
            "CHANNEL_LAYERS não configurado!"

        backend = settings.CHANNEL_LAYERS['default']['BACKEND']
        assert 'redis' in backend.lower(), \
            f"Redis esperado para channel layers, encontrado: {backend}"

    def test_timezone_configurado_para_sao_paulo(self):
        """
        GIVEN: configuração do Django
        WHEN: verifico TIME_ZONE
        THEN: deve ser America/Sao_Paulo
        """
        assert settings.TIME_ZONE == 'America/Sao_Paulo', \
            f"TIME_ZONE incorreto: {settings.TIME_ZONE}"

    def test_language_code_configurado_para_pt_br(self):
        """
        GIVEN: configuração do Django
        WHEN: verifico LANGUAGE_CODE
        THEN: deve ser pt-br
        """
        assert settings.LANGUAGE_CODE == 'pt-br', \
            f"LANGUAGE_CODE incorreto: {settings.LANGUAGE_CODE}"

    def test_custom_user_model_configurado(self):
        """
        GIVEN: configuração do Django
        WHEN: verifico AUTH_USER_MODEL
        THEN: deve ser core.Usuario
        """
        assert settings.AUTH_USER_MODEL == 'core.Usuario', \
            f"AUTH_USER_MODEL incorreto: {settings.AUTH_USER_MODEL}"

    def test_asgi_application_configurado(self):
        """
        GIVEN: configuração do Django
        WHEN: verifico ASGI_APPLICATION
        THEN: deve estar configurado para WebSockets
        """
        assert settings.ASGI_APPLICATION == 'separacao_pmcell.asgi.application', \
            f"ASGI_APPLICATION incorreto: {settings.ASGI_APPLICATION}"

    def test_daphne_instalado_antes_de_staticfiles(self):
        """
        GIVEN: configuração do Django
        WHEN: verifico INSTALLED_APPS
        THEN: daphne deve vir antes de staticfiles
        """
        assert 'daphne' in settings.INSTALLED_APPS, \
            "daphne não encontrado em INSTALLED_APPS!"

        daphne_idx = settings.INSTALLED_APPS.index('daphne')
        staticfiles_idx = settings.INSTALLED_APPS.index('django.contrib.staticfiles')

        assert daphne_idx < staticfiles_idx, \
            "daphne deve vir ANTES de django.contrib.staticfiles em INSTALLED_APPS"


@pytest.mark.skipif(
    os.environ.get('DATABASE_URL') is None,
    reason="Testes de produção apenas quando DATABASE_URL está configurado"
)
class TestProductionOnlyConfig:
    """Testes que só rodam quando DATABASE_URL está configurado (produção)"""

    def test_producao_detectada(self):
        """Confirma que estamos testando configuração de produção"""
        assert os.environ.get('DATABASE_URL') is not None
        assert settings.DEBUG is False

    def test_secret_key_forte_em_producao(self):
        """
        GIVEN: ambiente de produção
        WHEN: verifico SECRET_KEY
        THEN: deve ter pelo menos 50 caracteres
        """
        assert len(settings.SECRET_KEY) >= 50, \
            "SECRET_KEY muito curta para produção! Gere uma chave forte."
