# -*- coding: utf-8 -*-
"""
Repositórios de persistência.

Exports:
    - Repositórios de Usuario, Produto e Pedido
"""

from core.infrastructure.persistence.repositories.usuario_repository import (
    UsuarioRepositoryInterface
)
from core.infrastructure.persistence.repositories.produto_repository import (
    ProdutoRepositoryInterface,
    DjangoProdutoRepository
)
from core.infrastructure.persistence.repositories.pedido_repository import (
    PedidoRepositoryInterface,
    DjangoPedidoRepository
)

__all__ = [
    'UsuarioRepositoryInterface',
    'ProdutoRepositoryInterface',
    'DjangoProdutoRepository',
    'PedidoRepositoryInterface',
    'DjangoPedidoRepository',
]
