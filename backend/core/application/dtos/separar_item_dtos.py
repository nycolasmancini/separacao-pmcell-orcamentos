# -*- coding: utf-8 -*-
"""
DTOs para o caso de uso SepararItem (Fase 22).

Este módulo define os objetos de transferência de dados para
marcar itens como separados no pedido.

Author: PMCELL
Date: 2025-01-27
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class SepararItemRequestDTO:
    """
    DTO de requisição para separar um item.

    Attributes:
        pedido_id: ID do pedido que contém o item
        item_id: ID do item a ser marcado como separado
        usuario_id: ID do usuário que está separando o item
    """
    pedido_id: int
    item_id: int
    usuario_id: int


@dataclass
class SepararItemResponseDTO:
    """
    DTO de resposta após tentar separar um item.

    Attributes:
        success: Indica se a operação foi bem-sucedida
        message: Mensagem de feedback (sucesso ou erro)
        pedido_id: ID do pedido (para referência)
        item_id: ID do item que foi separado
        progresso_percentual: Progresso atualizado do pedido (0-100)
        itens_separados: Quantidade de itens separados
        total_itens: Total de itens no pedido
    """
    success: bool
    message: str
    pedido_id: Optional[int] = None
    item_id: Optional[int] = None
    progresso_percentual: Optional[int] = None
    itens_separados: Optional[int] = None
    total_itens: Optional[int] = None
