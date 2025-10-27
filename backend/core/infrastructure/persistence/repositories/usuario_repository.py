# -*- coding: utf-8 -*-
"""
Interface do repositório de usuários.

Fase 5: Criar Modelo de Usuário Customizado (stub para Fase 6)
"""

from abc import ABC, abstractmethod
from typing import Optional

from core.domain.usuario.entities import Usuario


class UsuarioRepositoryInterface(ABC):
    """
    Interface do repositório de usuários.

    Define o contrato para persistência de usuários seguindo o padrão Repository.
    """

    @abstractmethod
    def get_by_id(self, usuario_id: int) -> Optional[Usuario]:
        """
        Busca um usuário por seu ID.

        Args:
            usuario_id: ID do usuário.

        Returns:
            Usuário encontrado ou None se não existir.
        """
        pass

    @abstractmethod
    def buscar_por_numero_login(self, numero_login: int) -> Optional[Usuario]:
        """
        Busca um usuário por seu número de login.

        Args:
            numero_login: Número de login do usuário.

        Returns:
            Usuário encontrado ou None se não existir.
        """
        pass

    @abstractmethod
    def salvar(self, usuario: Usuario) -> Usuario:
        """
        Salva ou atualiza um usuário.

        Args:
            usuario: Usuário a ser salvo.

        Returns:
            Usuário salvo (com ID atualizado se novo).
        """
        pass

    @abstractmethod
    def deletar(self, numero_login: int) -> bool:
        """
        Deleta um usuário por número de login.

        Args:
            numero_login: Número de login do usuário a deletar.

        Returns:
            True se deletado, False se não existia.
        """
        pass

    @abstractmethod
    def listar_todos(self) -> list[Usuario]:
        """
        Lista todos os usuários.

        Returns:
            Lista de todos os usuários.
        """
        pass
