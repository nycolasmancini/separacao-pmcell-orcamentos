# -*- coding: utf-8 -*-
"""
Data Transfer Objects (DTOs) da aplicação.

Este módulo contém os DTOs usados para transferência de dados entre camadas.

Exports:
    Login DTOs:
        - LoginResponseDTO

    Orçamento DTOs:
        - OrcamentoHeaderDTO
        - ProdutoDTO

    Pedido DTOs:
        - CriarPedidoRequestDTO
        - CriarPedidoResponseDTO
"""

from core.application.dtos.login_dtos import LoginResponseDTO
from core.application.dtos.orcamento_dtos import OrcamentoHeaderDTO, ProdutoDTO
from core.application.dtos.pedido_dtos import CriarPedidoRequestDTO, CriarPedidoResponseDTO

__all__ = [
    'LoginResponseDTO',
    'OrcamentoHeaderDTO',
    'ProdutoDTO',
    'CriarPedidoRequestDTO',
    'CriarPedidoResponseDTO',
]
