# -*- coding: utf-8 -*-
"""
DTOs para o caso de uso MarcarParaCompra (Fase 23).

Author: PMCELL
Date: 2025-01-27
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class MarcarParaCompraRequestDTO:
    """
    DTO de requisição para marcar item para compra.

    Attributes:
        pedido_id: ID do pedido
        item_id: ID do item a ser marcado
        usuario_id: ID do usuário que está marcando
    """
    pedido_id: int
    item_id: int
    usuario_id: int

    def __post_init__(self):
        """Valida os dados após inicialização."""
        if not isinstance(self.pedido_id, int) or self.pedido_id <= 0:
            raise ValueError("pedido_id deve ser um inteiro positivo")

        if not isinstance(self.item_id, int) or self.item_id <= 0:
            raise ValueError("item_id deve ser um inteiro positivo")

        if not isinstance(self.usuario_id, int) or self.usuario_id <= 0:
            raise ValueError("usuario_id deve ser um inteiro positivo")


@dataclass
class MarcarParaCompraResponseDTO:
    """
    DTO de resposta do caso de uso MarcarParaCompra.

    Attributes:
        success: Se a operação foi bem-sucedida
        item_id: ID do item marcado
        em_compra: Se o item está marcado para compra
        enviado_para_compra_por: Nome do usuário que marcou
        enviado_para_compra_em: Timestamp de quando foi marcado
        erro: Mensagem de erro (se houver)
    """
    success: bool
    item_id: int
    em_compra: bool = False
    enviado_para_compra_por: Optional[str] = None
    enviado_para_compra_em: Optional[datetime] = None
    erro: Optional[str] = None

    def __post_init__(self):
        """Valida consistência dos dados."""
        if self.success and not self.em_compra:
            raise ValueError("Se success=True, em_compra deve ser True")

        if self.success and not self.enviado_para_compra_por:
            raise ValueError("Se success=True, enviado_para_compra_por é obrigatório")

        if self.success and not self.enviado_para_compra_em:
            raise ValueError("Se success=True, enviado_para_compra_em é obrigatório")

        if not self.success and not self.erro:
            raise ValueError("Se success=False, erro é obrigatório")
