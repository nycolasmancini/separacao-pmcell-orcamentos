# -*- coding: utf-8 -*-
"""
Entidades de domínio de usuário.

Fase 5: Criar Modelo de Usuário Customizado (stub para Fase 6)
"""

from enum import Enum
from dataclasses import dataclass
from typing import Optional


class TipoUsuario(str, Enum):
    """Tipos de usuário no sistema."""

    VENDEDOR = "VENDEDOR"
    SEPARADOR = "SEPARADOR"
    COMPRADORA = "COMPRADORA"
    ADMINISTRADOR = "ADMINISTRADOR"


@dataclass
class Usuario:
    """
    Entidade de domínio representando um usuário.

    Attributes:
        numero_login (int): Número de login único (identificador).
        nome (str): Nome completo do usuário.
        tipo (TipoUsuario): Tipo de usuário.
        ativo (bool): Status ativo/inativo.
        pin_hash (Optional[str]): Hash do PIN (interno).
    """

    numero_login: int
    nome: str
    tipo: TipoUsuario
    ativo: bool = True
    pin_hash: Optional[str] = None

    def set_password(self, pin: str) -> None:
        """
        Define o PIN do usuário (hashado).

        Args:
            pin: PIN de 4 dígitos.

        Note:
            Esta é uma implementação simplificada para a Fase 6.
            A Fase 5 completa implementará hash PBKDF2.
        """
        # Implementação simplificada: apenas armazena o PIN
        # TODO: Implementar hash PBKDF2 na Fase 5 completa
        self.pin_hash = pin

    def check_password(self, pin: str) -> bool:
        """
        Verifica se o PIN fornecido está correto.

        Args:
            pin: PIN a ser verificado.

        Returns:
            True se o PIN está correto, False caso contrário.
        """
        if self.pin_hash is None:
            return False
        # Implementação simplificada: comparação direta
        # TODO: Implementar verificação com hash PBKDF2 na Fase 5
        return self.pin_hash == pin
