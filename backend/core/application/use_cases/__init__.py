# -*- coding: utf-8 -*-
"""
Use Cases da aplicação.

Este módulo contém os casos de uso (use cases) que orquestram a lógica de negócio.

Exports:
    - LoginUseCase: Caso de uso de autenticação
    - CriarPedidoUseCase: Caso de uso de criação de pedidos a partir de PDFs
    - SepararItemUseCase: Caso de uso de marcação de item como separado (Fase 22)
"""

from core.application.use_cases.login import LoginUseCase
from core.application.use_cases.criar_pedido import CriarPedidoUseCase
from core.application.use_cases.separar_item import SepararItemUseCase

__all__ = [
    'LoginUseCase',
    'CriarPedidoUseCase',
    'SepararItemUseCase',
]
