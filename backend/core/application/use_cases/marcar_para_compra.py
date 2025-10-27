# -*- coding: utf-8 -*-
"""
Caso de Uso: Marcar Item para Compra (Fase 23).

Este módulo implementa a lógica de marcação de um item como "aguardando compra",
enviando-o para o painel de compras sem alterar o progresso do pedido.

Author: PMCELL
Date: 2025-01-27
"""

import logging
from typing import Optional

from core.application.dtos.marcar_para_compra_dtos import (
    MarcarParaCompraRequestDTO,
    MarcarParaCompraResponseDTO
)
from core.domain.pedido.entities import ValidationError
from core.infrastructure.persistence.repositories.pedido_repository import (
    PedidoRepositoryInterface
)
from core.infrastructure.persistence.repositories.usuario_repository import (
    UsuarioRepositoryInterface
)

logger = logging.getLogger(__name__)


class MarcarParaCompraUseCase:
    """
    Caso de uso para marcar um item para ser enviado ao painel de compras.

    Este use case orquestra o processo de marcação para compra:
    1. Validar que pedido existe
    2. Validar que usuário existe
    3. Validar que item existe no pedido
    4. Marcar item como em_compra (chama método de domínio)
    5. Persistir alterações
    6. Retornar dados do item atualizado

    Attributes:
        pedido_repository: Repositório para acesso a pedidos
        usuario_repository: Repositório para acesso a usuários

    Examples:
        >>> request = MarcarParaCompraRequestDTO(
        ...     pedido_id=100,
        ...     item_id=1,
        ...     usuario_id=42
        ... )
        >>> use_case = MarcarParaCompraUseCase(pedido_repo, usuario_repo)
        >>> response = use_case.execute(request)
        >>> response.success
        True
        >>> response.em_compra
        True
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

    def execute(self, request: MarcarParaCompraRequestDTO) -> MarcarParaCompraResponseDTO:
        """
        Executa o caso de uso de marcar item para compra.

        Args:
            request: DTO com dados da requisição

        Returns:
            DTO com resultado da operação
        """
        logger.info(
            f"Iniciando marcação para compra: pedido={request.pedido_id}, "
            f"item={request.item_id}, usuario={request.usuario_id}"
        )

        # 1. Buscar pedido
        pedido = self.pedido_repository.get_by_id(request.pedido_id)
        if not pedido:
            erro = f"Pedido não encontrado: {request.pedido_id}"
            logger.error(erro)
            return MarcarParaCompraResponseDTO(
                success=False,
                item_id=request.item_id,
                erro=erro
            )

        # 2. Buscar usuário
        usuario = self.usuario_repository.get_by_id(request.usuario_id)
        if not usuario:
            erro = f"Usuário não encontrado: {request.usuario_id}"
            logger.error(erro)
            return MarcarParaCompraResponseDTO(
                success=False,
                item_id=request.item_id,
                erro=erro
            )

        # 3. Buscar item no pedido
        item = None
        for i in pedido.itens:
            if i.id == request.item_id:
                item = i
                break

        if not item:
            erro = f"Item não encontrado no pedido: item_id={request.item_id}"
            logger.error(erro)
            return MarcarParaCompraResponseDTO(
                success=False,
                item_id=request.item_id,
                erro=erro
            )

        # 4. Marcar item para compra (chamando método de domínio)
        try:
            item.marcar_para_compra(usuario.nome)
        except ValidationError as e:
            erro = str(e)
            logger.warning(
                f"Erro ao marcar item para compra: {erro} "
                f"(item_id={request.item_id})"
            )
            return MarcarParaCompraResponseDTO(
                success=False,
                item_id=request.item_id,
                erro=erro
            )

        # 5. Persistir alterações
        try:
            self.pedido_repository.save(pedido)
            logger.info(
                f"Item {request.item_id} marcado para compra com sucesso "
                f"por {usuario.nome}"
            )
        except Exception as e:
            erro = f"Erro ao salvar pedido: {str(e)}"
            logger.error(erro, exc_info=True)
            return MarcarParaCompraResponseDTO(
                success=False,
                item_id=request.item_id,
                erro=erro
            )

        # 6. Retornar resposta de sucesso
        return MarcarParaCompraResponseDTO(
            success=True,
            item_id=item.id,
            em_compra=item.em_compra,
            enviado_para_compra_por=item.enviado_para_compra_por,
            enviado_para_compra_em=item.enviado_para_compra_em
        )
