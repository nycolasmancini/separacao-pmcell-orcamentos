# -*- coding: utf-8 -*-
"""
Caso de Uso: Separar Item do Pedido (Fase 22).

Este módulo implementa a lógica de marcação de um item como separado,
atualizando o progresso do pedido e registrando quem separou.

Author: PMCELL
Date: 2025-01-27
"""

import logging
from typing import Optional

from core.application.dtos.separar_item_dtos import (
    SepararItemRequestDTO,
    SepararItemResponseDTO
)
from core.domain.pedido.entities import ValidationError
from core.infrastructure.persistence.repositories.pedido_repository import (
    PedidoRepositoryInterface
)
from core.infrastructure.persistence.repositories.usuario_repository import (
    UsuarioRepositoryInterface
)

logger = logging.getLogger(__name__)


class SepararItemUseCase:
    """
    Caso de uso para marcar um item como separado.

    Este use case orquestra o processo de separação de um item:
    1. Validar que pedido existe
    2. Validar que usuário existe
    3. Validar que item existe no pedido
    4. Marcar item como separado (chama método de domínio)
    5. Persistir alterações
    6. Calcular e retornar progresso atualizado

    Attributes:
        pedido_repository: Repositório para acesso a pedidos
        usuario_repository: Repositório para acesso a usuários

    Examples:
        >>> request = SepararItemRequestDTO(
        ...     pedido_id=100,
        ...     item_id=1,
        ...     usuario_id=42
        ... )
        >>> use_case = SepararItemUseCase(pedido_repo, usuario_repo)
        >>> response = use_case.execute(request)
        >>> response.success
        True
        >>> response.progresso_percentual
        33
    """

    def __init__(
        self,
        pedido_repository: PedidoRepositoryInterface,
        usuario_repository: UsuarioRepositoryInterface
    ):
        """
        Inicializa o caso de uso.

        Args:
            pedido_repository: Repositório de pedidos
            usuario_repository: Repositório de usuários
        """
        self.pedido_repository = pedido_repository
        self.usuario_repository = usuario_repository

    def execute(self, request: SepararItemRequestDTO) -> SepararItemResponseDTO:
        """
        Executa o caso de uso de separar item.

        Args:
            request: DTO contendo pedido_id, item_id e usuario_id

        Returns:
            SepararItemResponseDTO com resultado da operação

        Examples:
            >>> request = SepararItemRequestDTO(100, 1, 42)
            >>> response = use_case.execute(request)
            >>> response.success
            True
        """
        logger.info(
            f"Iniciando separação de item {request.item_id} "
            f"do pedido {request.pedido_id} pelo usuário {request.usuario_id}"
        )

        # 1. Validar que pedido existe
        pedido = self.pedido_repository.get_by_id(request.pedido_id)
        if not pedido:
            logger.warning(f"Pedido {request.pedido_id} não encontrado")
            return SepararItemResponseDTO(
                success=False,
                message=f"Pedido não encontrado (ID: {request.pedido_id})"
            )

        # 2. Validar que usuário existe
        usuario = self.usuario_repository.get_by_id(request.usuario_id)
        if not usuario:
            logger.warning(f"Usuário {request.usuario_id} não encontrado")
            return SepararItemResponseDTO(
                success=False,
                message=f"Usuário não encontrado (ID: {request.usuario_id})"
            )

        # 3. Validar que item existe no pedido
        item = self._encontrar_item(pedido, request.item_id)
        if not item:
            logger.warning(
                f"Item {request.item_id} não encontrado no pedido {request.pedido_id}"
            )
            return SepararItemResponseDTO(
                success=False,
                message=f"Item não encontrado (ID: {request.item_id})"
            )

        # 4. Marcar item como separado (validações de domínio)
        try:
            item.marcar_separado(usuario.nome)
            logger.info(
                f"Item {request.item_id} marcado como separado por {usuario.nome}"
            )

        except ValidationError as e:
            logger.warning(f"Erro ao marcar item como separado: {str(e)}")
            return SepararItemResponseDTO(
                success=False,
                message=str(e)
            )

        # 5. Persistir alterações
        try:
            self.pedido_repository.save(pedido)
            logger.info(f"Alterações persistidas para pedido {request.pedido_id}")

        except Exception as e:
            logger.error(f"Erro ao persistir alterações: {str(e)}")
            return SepararItemResponseDTO(
                success=False,
                message=f"Erro ao salvar alterações: {str(e)}"
            )

        # 6. Calcular progresso atualizado
        progresso = pedido.calcular_progresso()
        itens_separados = sum(1 for item in pedido.itens if item.separado)
        total_itens = len(pedido.itens)

        logger.info(
            f"Item {request.item_id} separado com sucesso. "
            f"Progresso do pedido: {progresso}% ({itens_separados}/{total_itens})"
        )

        return SepararItemResponseDTO(
            success=True,
            message="Item marcado como separado com sucesso",
            pedido_id=request.pedido_id,
            item_id=request.item_id,
            progresso_percentual=progresso,
            itens_separados=itens_separados,
            total_itens=total_itens
        )

    def _encontrar_item(self, pedido, item_id: int):
        """
        Busca um item específico dentro do pedido.

        Args:
            pedido: Entidade Pedido
            item_id: ID do item a buscar

        Returns:
            ItemPedido se encontrado, None caso contrário
        """
        for item in pedido.itens:
            if item.id == item_id:
                return item
        return None
