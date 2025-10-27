# -*- coding: utf-8 -*-
"""
DTOs relacionados ao caso de uso de login.

Fase 6: Implementar Caso de Uso de Login
"""

from dataclasses import dataclass
from typing import Optional

from core.domain.usuario.entities import Usuario


@dataclass
class LoginResponseDTO:
    """
    DTO de resposta do caso de uso de login.

    Attributes:
        success (bool): Indica se o login foi bem-sucedido.
        usuario (Optional[Usuario]): Usuário autenticado (None se falhou).
        error_message (Optional[str]): Mensagem de erro (None se sucesso).
        blocked (bool): Indica se o usuário está bloqueado por rate limiting.
        remaining_attempts (Optional[int]): Tentativas restantes antes de bloqueio.
    """

    success: bool
    usuario: Optional[Usuario] = None
    error_message: Optional[str] = None
    blocked: bool = False
    remaining_attempts: Optional[int] = None

    def __post_init__(self):
        """Validações pós-inicialização."""
        # Se sucesso, usuário não pode ser None
        if self.success and self.usuario is None:
            raise ValueError("Usuário não pode ser None quando login é bem-sucedido")

        # Se falha, deve ter mensagem de erro
        if not self.success and not self.error_message:
            raise ValueError("Mensagem de erro é obrigatória quando login falha")

        # Se bloqueado, success deve ser False
        if self.blocked and self.success:
            raise ValueError("Login não pode ser bem-sucedido se usuário está bloqueado")
