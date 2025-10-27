# -*- coding: utf-8 -*-
"""
Use Case: Finalizar Pedido

Este módulo implementa a lógica de negócio para finalizar um pedido
quando todos os itens foram separados (progresso = 100%).

Responsabilidades:
- Validar se pedido pode ser finalizado (progresso = 100%)
- Chamar método de domínio pedido.finalizar()
- Calcular tempo total de separação
- Persistir mudanças no repositório
- Retornar DTO com resultado da operação

Author: PMCELL
Date: 2025-01-27
"""

import logging
from typing import Optional

from core.application.dtos.pedido_dtos import FinalizarPedidoResponseDTO
from core.infrastructure.persistence.repositories.pedido_repository import (
    PedidoRepositoryInterface
)
from core.domain.pedido.entities import ValidationError

logger = logging.getLogger(__name__)


class FinalizarPedidoUseCase:
    """
    Use Case para finalizar um pedido de separação.

    Um pedido só pode ser finalizado quando:
    - Progresso = 100% (todos os itens separados)
    - Status atual = EM_SEPARACAO

    Attributes:
        pedido_repository: Repositório de acesso a dados de pedidos

    Example:
        >>> repository = DjangoPedidoRepository()
        >>> use_case = FinalizarPedidoUseCase(repository)
        >>> response = use_case.execute(
        ...     pedido_id=123,
        ...     usuario_nome='João Separador'
        ... )
        >>> response.sucesso
        True
    """

    def __init__(self, pedido_repository: PedidoRepositoryInterface):
        """
        Inicializa o use case com suas dependências.

        Args:
            pedido_repository: Repositório para persistência de pedidos
        """
        self.pedido_repository = pedido_repository

    def execute(
        self,
        pedido_id: int,
        usuario_nome: str
    ) -> FinalizarPedidoResponseDTO:
        """
        Executa a finalização de um pedido.

        Args:
            pedido_id: ID do pedido a ser finalizado
            usuario_nome: Nome do usuário que está finalizando

        Returns:
            FinalizarPedidoResponseDTO com resultado da operação

        Example:
            >>> response = use_case.execute(123, 'João Separador')
            >>> if response.sucesso:
            ...     print(f"Pedido finalizado em {response.tempo_total_minutos} minutos")
        """
        logger.info(f"Iniciando finalização do pedido {pedido_id} por {usuario_nome}")

        try:
            # 1. Buscar pedido no repositório
            pedido = self.pedido_repository.get_by_id(pedido_id)

            if not pedido:
                logger.warning(f"Pedido {pedido_id} não encontrado")
                return FinalizarPedidoResponseDTO(
                    sucesso=False,
                    pedido_id=pedido_id,
                    status='',
                    tempo_total_minutos=0.0,
                    mensagem=f'Pedido #{pedido_id} não encontrado'
                )

            # 2. Validar se pode ser finalizado (método de domínio)
            if not pedido.pode_finalizar():
                progresso = pedido.calcular_progresso()
                mensagem = (
                    f'Pedido não pode ser finalizado. '
                    f'Progresso: {progresso}%. '
                    f'É necessário 100% de progresso.'
                )
                logger.warning(
                    f"Tentativa de finalizar pedido {pedido_id} com progresso {progresso}%"
                )
                return FinalizarPedidoResponseDTO(
                    sucesso=False,
                    pedido_id=pedido.id,
                    status=pedido.status.value,
                    tempo_total_minutos=0.0,
                    mensagem=mensagem
                )

            # 3. Finalizar pedido (método de domínio)
            try:
                pedido.finalizar(usuario_nome)
            except ValidationError as e:
                logger.error(f"Erro de validação ao finalizar pedido {pedido_id}: {e}")
                return FinalizarPedidoResponseDTO(
                    sucesso=False,
                    pedido_id=pedido.id,
                    status=pedido.status.value,
                    tempo_total_minutos=0.0,
                    mensagem=str(e)
                )

            # 4. Persistir mudanças (ANTES de calcular tempo, para garantir dados salvos)
            pedido_atualizado = self.pedido_repository.save(pedido)

            # 5. Calcular tempo total (data_finalizacao - data_inicio)
            # Usar pedido_atualizado para pegar timestamps do banco
            if pedido_atualizado.data_finalizacao and pedido_atualizado.data_inicio:
                tempo_total_segundos = (
                    pedido_atualizado.data_finalizacao - pedido_atualizado.data_inicio
                ).total_seconds()
                tempo_total_minutos = tempo_total_segundos / 60
            else:
                tempo_total_minutos = 0.0
                logger.warning(
                    f"Pedido {pedido_id} finalizado mas sem timestamps válidos"
                )

            logger.info(
                f"Pedido {pedido_id} finalizado com sucesso. "
                f"Tempo total: {tempo_total_minutos:.1f} minutos"
            )

            # 6. Retornar resposta de sucesso
            return FinalizarPedidoResponseDTO(
                sucesso=True,
                pedido_id=pedido_atualizado.id,
                status=pedido_atualizado.status.value,
                tempo_total_minutos=round(tempo_total_minutos, 1),
                mensagem=f'Pedido #{pedido.numero_orcamento} finalizado com sucesso! '
                        f'Tempo total: {tempo_total_minutos:.1f} minutos'
            )

        except Exception as e:
            logger.error(
                f"Erro inesperado ao finalizar pedido {pedido_id}: {e}",
                exc_info=True
            )
            return FinalizarPedidoResponseDTO(
                sucesso=False,
                pedido_id=pedido_id,
                status='',
                tempo_total_minutos=0.0,
                mensagem=f'Erro ao finalizar pedido: {str(e)}'
            )
