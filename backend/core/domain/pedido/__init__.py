# -*- coding: utf-8 -*-
"""
Modulo de dominio para Pedido (Fase 13).

Exports:
    - Pedido: Agregado raiz
    - ItemPedido: Entidade de item
    - Logistica, Embalagem, StatusPedido: Value Objects
    - ValidationError: Excecao de validacao
"""

from core.domain.pedido.entities import Pedido, ItemPedido, ValidationError
from core.domain.pedido.value_objects import Logistica, Embalagem, StatusPedido

__all__ = [
    'Pedido',
    'ItemPedido',
    'Logistica',
    'Embalagem',
    'StatusPedido',
    'ValidationError',
]
