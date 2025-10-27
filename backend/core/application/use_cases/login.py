# -*- coding: utf-8 -*-
"""
Caso de uso de autenticação de usuário.

Fase 6: Implementar Caso de Uso de Login

Este módulo implementa o use case de autenticação com validação de credenciais
e rate limiting via Redis para prevenir ataques de força bruta.
"""

from typing import Optional
import logging
from redis import Redis

from core.domain.usuario.entities import Usuario
from core.infrastructure.persistence.repositories.usuario_repository import (
    UsuarioRepositoryInterface,
)
from core.application.dtos.login_dtos import LoginResponseDTO


# Configuração de logging
logger = logging.getLogger(__name__)

# Constantes de rate limiting
MAX_LOGIN_ATTEMPTS = 5
RATE_LIMIT_DURATION_SECONDS = 60
REDIS_KEY_PREFIX = "login_attempts"

# Mensagens de erro
ERROR_MESSAGE_INVALID_CREDENTIALS = "Credenciais inválidas"
ERROR_MESSAGE_BLOCKED = (
    f"Usuário bloqueado por {RATE_LIMIT_DURATION_SECONDS} segundos "
    "devido a múltiplas tentativas falhas"
)


class LoginUseCase:
    """
    Caso de uso para autenticação de usuário.

    Responsabilidades:
    - Validar credenciais (numero_login + PIN)
    - Implementar rate limiting (5 tentativas por minuto)
    - Retornar DTO com resultado da autenticação

    Nota: Este use case NÃO cria sessão Django (isso é responsabilidade da Fase 8).
    """

    def __init__(
        self, usuario_repository: UsuarioRepositoryInterface, redis_client: Redis
    ):
        """
        Inicializa o caso de uso.

        Args:
            usuario_repository: Repositório de usuários.
            redis_client: Cliente Redis para rate limiting.
        """
        self.usuario_repository = usuario_repository
        self.redis_client = redis_client

    def execute(self, numero_login: int, pin: str) -> LoginResponseDTO:
        """
        Executa o caso de uso de login.

        Args:
            numero_login: Número de login do usuário (inteiro).
            pin: PIN de 4 dígitos (string).

        Returns:
            LoginResponseDTO com resultado da autenticação.

        Processo:
        1. Verificar rate limiting
        2. Buscar usuário por numero_login
        3. Validar PIN
        4. Se sucesso: resetar contador de rate limiting
        5. Se falha: incrementar contador de rate limiting
        """
        # 1. Verificar rate limiting
        is_blocked, remaining_attempts = self._check_rate_limit(numero_login)
        if is_blocked:
            logger.warning(
                f"Login bloqueado para numero_login={numero_login} devido a rate limiting"
            )
            return LoginResponseDTO(
                success=False,
                error_message=ERROR_MESSAGE_BLOCKED,
                blocked=True,
                remaining_attempts=0,
            )

        # 2. Buscar usuário por numero_login
        usuario: Optional[Usuario] = self.usuario_repository.buscar_por_numero_login(
            numero_login
        )

        if usuario is None:
            # Usuário não existe
            logger.info(f"Tentativa de login com numero_login inexistente: {numero_login}")
            self._increment_failed_attempts(numero_login)
            _, remaining = self._check_rate_limit(numero_login)
            return LoginResponseDTO(
                success=False,
                error_message=ERROR_MESSAGE_INVALID_CREDENTIALS,
                blocked=False,
                remaining_attempts=remaining,
            )

        # 3. Validar PIN
        if not usuario.check_password(pin):
            # PIN incorreto
            logger.info(
                f"Tentativa de login com PIN incorreto para numero_login={numero_login}"
            )
            self._increment_failed_attempts(numero_login)
            _, remaining = self._check_rate_limit(numero_login)
            return LoginResponseDTO(
                success=False,
                error_message=ERROR_MESSAGE_INVALID_CREDENTIALS,
                blocked=False,
                remaining_attempts=remaining,
            )

        # 4. Login bem-sucedido: resetar contador
        self._reset_rate_limit(numero_login)
        logger.info(
            f"Login bem-sucedido para numero_login={numero_login}, "
            f"tipo={usuario.tipo.value}"
        )

        return LoginResponseDTO(
            success=True, usuario=usuario, blocked=False, remaining_attempts=None
        )

    def _check_rate_limit(self, numero_login: int) -> tuple[bool, int]:
        """
        Verifica se usuário está bloqueado por rate limiting.

        Args:
            numero_login: Número de login do usuário.

        Returns:
            Tupla (is_blocked, remaining_attempts):
            - is_blocked: True se usuário está bloqueado.
            - remaining_attempts: Tentativas restantes antes de bloqueio.
        """
        redis_key = f"{REDIS_KEY_PREFIX}:{numero_login}"

        try:
            attempts_bytes = self.redis_client.get(redis_key)

            if attempts_bytes is None:
                # Nenhuma tentativa anterior (chave expirou ou não existe)
                return False, MAX_LOGIN_ATTEMPTS

            attempts = int(attempts_bytes)

            if attempts >= MAX_LOGIN_ATTEMPTS:
                # Bloqueado
                return True, 0

            # Não bloqueado ainda
            remaining = MAX_LOGIN_ATTEMPTS - attempts
            return False, remaining

        except Exception as e:
            # Em caso de erro no Redis, permitir tentativa (fail-safe)
            logger.error(
                f"Erro ao verificar rate limit no Redis para numero_login={numero_login}: {e}"
            )
            return False, MAX_LOGIN_ATTEMPTS

    def _increment_failed_attempts(self, numero_login: int) -> None:
        """
        Incrementa contador de tentativas falhas no Redis.

        Args:
            numero_login: Número de login do usuário.

        Comportamento:
        - Incrementa contador no Redis
        - Define TTL de 60 segundos (1 minuto)
        - Se chave não existe, cria com valor 1
        """
        redis_key = f"{REDIS_KEY_PREFIX}:{numero_login}"

        try:
            # Incrementar contador (cria chave com valor 1 se não existir)
            self.redis_client.incr(redis_key)

            # Definir TTL de 60 segundos
            self.redis_client.expire(redis_key, RATE_LIMIT_DURATION_SECONDS)

        except Exception as e:
            # Em caso de erro no Redis, continuar (fail-safe)
            logger.error(
                f"Erro ao incrementar contador de tentativas falhas no Redis "
                f"para numero_login={numero_login}: {e}"
            )

    def _reset_rate_limit(self, numero_login: int) -> None:
        """
        Reseta contador de tentativas falhas (login bem-sucedido).

        Args:
            numero_login: Número de login do usuário.
        """
        redis_key = f"{REDIS_KEY_PREFIX}:{numero_login}"

        try:
            self.redis_client.delete(redis_key)
        except Exception as e:
            # Em caso de erro no Redis, continuar (fail-safe)
            logger.error(
                f"Erro ao resetar rate limit no Redis para numero_login={numero_login}: {e}"
            )
