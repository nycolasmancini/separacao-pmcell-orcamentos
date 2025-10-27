# -*- coding: utf-8 -*-
"""
Testes unitários para LoginUseCase.

Fase 6: Implementar Caso de Uso de Login
TDD: RED → GREEN → REFACTOR
"""

import pytest
from unittest.mock import Mock, MagicMock
from datetime import datetime
import time

from core.domain.usuario.entities import Usuario, TipoUsuario
from core.application.use_cases.login import LoginUseCase
from core.application.dtos.login_dtos import LoginResponseDTO


@pytest.fixture
def mock_usuario_repository():
    """Mock do repositório de usuários."""
    return Mock()


@pytest.fixture
def mock_redis_client():
    """Mock do cliente Redis."""
    redis_mock = Mock()
    redis_mock.get = Mock(return_value=None)
    redis_mock.set = Mock(return_value=True)
    redis_mock.delete = Mock(return_value=True)
    redis_mock.incr = Mock(return_value=1)
    redis_mock.expire = Mock(return_value=True)
    return redis_mock


@pytest.fixture
def usuario_valido():
    """Fixture de usuário válido para testes."""
    usuario = Usuario(
        numero_login=1,
        nome="João Separador",
        tipo=TipoUsuario.SEPARADOR,
        ativo=True
    )
    usuario.set_password("1234")
    return usuario


@pytest.fixture
def login_use_case(mock_usuario_repository, mock_redis_client):
    """Fixture do LoginUseCase."""
    return LoginUseCase(
        usuario_repository=mock_usuario_repository,
        redis_client=mock_redis_client
    )


class TestLoginUseCaseSuccess:
    """Testes de login bem-sucedido."""

    def test_login_success_with_valid_credentials(
        self, login_use_case, mock_usuario_repository, usuario_valido
    ):
        """
        Testa login bem-sucedido com credenciais válidas.

        Cenário:
        - Usuário existe no banco
        - PIN está correto
        - Nenhuma tentativa anterior de login falho

        Resultado esperado:
        - success = True
        - usuario retornado corretamente
        - blocked = False
        - error_message = None
        """
        # Arrange
        mock_usuario_repository.buscar_por_numero_login.return_value = usuario_valido

        # Act
        result = login_use_case.execute(numero_login=1, pin="1234")

        # Assert
        assert isinstance(result, LoginResponseDTO)
        assert result.success is True
        assert result.usuario is not None
        assert result.usuario.numero_login == 1
        assert result.usuario.nome == "João Separador"
        assert result.blocked is False
        assert result.error_message is None

    def test_login_returns_correct_user_data_in_dto(
        self, login_use_case, mock_usuario_repository, usuario_valido
    ):
        """
        Testa que LoginResponseDTO retorna dados corretos do usuário.

        Cenário:
        - Login bem-sucedido

        Resultado esperado:
        - DTO contém todos os dados do usuário
        - Tipo do usuário está correto
        - Status ativo está correto
        """
        # Arrange
        mock_usuario_repository.buscar_por_numero_login.return_value = usuario_valido

        # Act
        result = login_use_case.execute(numero_login=1, pin="1234")

        # Assert
        assert result.usuario.numero_login == 1
        assert result.usuario.nome == "João Separador"
        assert result.usuario.tipo == TipoUsuario.SEPARADOR
        assert result.usuario.ativo is True

    def test_successful_login_resets_rate_limit_counter(
        self, login_use_case, mock_usuario_repository, mock_redis_client, usuario_valido
    ):
        """
        Testa que login bem-sucedido reseta contador de tentativas falhas.

        Cenário:
        - Havia tentativas falhas anteriores (contador no Redis)
        - Login bem-sucedido

        Resultado esperado:
        - Chave do Redis é deletada (contador resetado)
        """
        # Arrange
        mock_usuario_repository.buscar_por_numero_login.return_value = usuario_valido
        mock_redis_client.get.return_value = b"3"  # 3 tentativas falhas anteriores

        # Act
        result = login_use_case.execute(numero_login=1, pin="1234")

        # Assert
        assert result.success is True
        mock_redis_client.delete.assert_called_once_with("login_attempts:1")


class TestLoginUseCaseFailure:
    """Testes de falhas de login."""

    def test_login_fails_with_invalid_numero_login(
        self, login_use_case, mock_usuario_repository
    ):
        """
        Testa que login falha com numero_login inexistente.

        Cenário:
        - numero_login não existe no banco

        Resultado esperado:
        - success = False
        - usuario = None
        - error_message com mensagem adequada
        - blocked = False (ainda não atingiu limite)
        """
        # Arrange
        mock_usuario_repository.buscar_por_numero_login.return_value = None

        # Act
        result = login_use_case.execute(numero_login=999, pin="1234")

        # Assert
        assert result.success is False
        assert result.usuario is None
        assert result.error_message == "Credenciais inválidas"
        assert result.blocked is False

    def test_login_fails_with_invalid_pin(
        self, login_use_case, mock_usuario_repository, usuario_valido
    ):
        """
        Testa que login falha com PIN incorreto.

        Cenário:
        - numero_login existe
        - PIN está incorreto

        Resultado esperado:
        - success = False
        - usuario = None
        - error_message com mensagem adequada
        - Contador de tentativas incrementado
        """
        # Arrange
        mock_usuario_repository.buscar_por_numero_login.return_value = usuario_valido

        # Act
        result = login_use_case.execute(numero_login=1, pin="9999")

        # Assert
        assert result.success is False
        assert result.usuario is None
        assert result.error_message == "Credenciais inválidas"


class TestLoginRateLimiting:
    """Testes de rate limiting."""

    def test_login_rate_limiting_blocks_after_5_attempts(
        self, login_use_case, mock_usuario_repository, mock_redis_client, usuario_valido
    ):
        """
        Testa que rate limiting bloqueia após 5 tentativas falhas.

        Cenário:
        - 5 tentativas falhas consecutivas
        - 6ª tentativa deve ser bloqueada

        Resultado esperado:
        - Na 6ª tentativa: blocked = True
        - error_message indica bloqueio
        - remaining_attempts = 0
        """
        # Arrange
        mock_usuario_repository.buscar_por_numero_login.return_value = usuario_valido

        # Simular 5 tentativas falhas (contador = 5 no Redis)
        mock_redis_client.get.return_value = b"5"

        # Act
        result = login_use_case.execute(numero_login=1, pin="1234")

        # Assert
        assert result.blocked is True
        assert result.success is False
        assert "bloqueado" in result.error_message.lower()
        assert result.remaining_attempts == 0

    def test_login_rate_limiting_uses_redis(
        self, login_use_case, mock_usuario_repository, mock_redis_client, usuario_valido
    ):
        """
        Testa que rate limiting usa Redis para armazenar contador.

        Cenário:
        - Login falho

        Resultado esperado:
        - Redis.incr() é chamado para incrementar contador
        - Redis.expire() é chamado para definir TTL de 60 segundos
        - Chave correta: "login_attempts:{numero_login}"
        """
        # Arrange
        mock_usuario_repository.buscar_por_numero_login.return_value = usuario_valido
        mock_redis_client.incr.return_value = 1

        # Act
        result = login_use_case.execute(numero_login=1, pin="9999")  # PIN errado

        # Assert
        assert result.success is False
        mock_redis_client.incr.assert_called_once_with("login_attempts:1")
        mock_redis_client.expire.assert_called_once_with("login_attempts:1", 60)

    def test_login_rate_limiting_resets_after_1_minute(
        self, login_use_case, mock_usuario_repository, mock_redis_client, usuario_valido
    ):
        """
        Testa que bloqueio expira após 1 minuto.

        Cenário:
        - Tentativa de login quando chave do Redis já expirou
        - Redis retorna None (chave expirada)

        Resultado esperado:
        - Login é permitido (não está bloqueado)
        - Novo contador inicia do zero
        """
        # Arrange
        mock_usuario_repository.buscar_por_numero_login.return_value = usuario_valido
        mock_redis_client.get.return_value = None  # Chave expirou
        mock_redis_client.incr.return_value = 1

        # Act
        result = login_use_case.execute(numero_login=1, pin="9999")

        # Assert
        # Não está bloqueado (contador resetado)
        assert result.blocked is False
        # Contador incrementado novamente (nova tentativa)
        mock_redis_client.incr.assert_called_once_with("login_attempts:1")
