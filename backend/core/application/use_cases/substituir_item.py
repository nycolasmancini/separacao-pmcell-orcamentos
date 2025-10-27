# -*- coding: utf-8 -*-
"""
Caso de uso: Substituir Item por Produto Alternativo.

Permite que o separador substitua um produto faltante por outro similar,
registrando a substituição e marcando automaticamente o item como separado.

Author: PMCELL
Date: 2025-01-27
Fase: 24
"""

import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from django.utils import timezone

logger = logging.getLogger(__name__)


# Mensagens de erro
ERROR_PRODUTO_SUBSTITUTO_VAZIO = "O produto substituto deve ser informado"
ERROR_ITEM_NAO_ENCONTRADO = "Item não encontrado"


@dataclass
class SubstituirItemResponse:
    """
    DTO de resposta do caso de uso SubstituirItem.

    Attributes:
        success: Indica se a substituição foi bem-sucedida
        message: Mensagem descritiva do resultado
        item_id: ID do item substituído (opcional)
    """
    success: bool
    message: str
    item_id: Optional[int] = None


class SubstituirItemUseCase:
    """
    Caso de uso: Substituir Item.

    Marca um item como substituído e automaticamente como separado.
    """

    def execute(
        self,
        item_id: int,
        produto_substituto: str,
        usuario: any  # Usuario entity
    ) -> SubstituirItemResponse:
        """
        Executa a substituição de um item.

        Args:
            item_id: ID do item a ser substituído
            produto_substituto: Nome do produto que substituiu o original
            usuario: Entidade Usuario que está substituindo

        Returns:
            SubstituirItemResponse com resultado da operação

        Raises:
            Nenhuma exceção é lançada, erros são retornados no DTO
        """
        # Validar produto_substituto
        if not produto_substituto or not produto_substituto.strip():
            logger.warning(
                f"Tentativa de substituir item {item_id} sem informar produto substituto"
            )
            return SubstituirItemResponse(
                success=False,
                message=ERROR_PRODUTO_SUBSTITUTO_VAZIO
            )

        # Buscar o item no banco
        from core.models import ItemPedido as ItemPedidoModel

        try:
            item_django = ItemPedidoModel.objects.get(id=item_id)
        except ItemPedidoModel.DoesNotExist:
            logger.error(f"Item {item_id} não encontrado")
            return SubstituirItemResponse(
                success=False,
                message=ERROR_ITEM_NAO_ENCONTRADO
            )

        # Registrar substituição
        produto_original = item_django.produto.descricao
        item_django.substituido = True
        item_django.produto_substituto = produto_substituto.strip()

        # Marcar como separado automaticamente
        item_django.separado = True
        item_django.quantidade_separada = item_django.quantidade_solicitada

        # Buscar usuário Django
        from core.models import Usuario
        usuario_django = Usuario.objects.get(numero_login=usuario.numero_login)

        item_django.separado_por = usuario_django
        item_django.separado_em = timezone.now()

        # Item substituído NÃO está em compra
        item_django.em_compra = False

        item_django.save()

        logger.info(
            f"Item {item_id} substituído: '{produto_original}' → '{produto_substituto}' "
            f"por {usuario.nome}"
        )

        return SubstituirItemResponse(
            success=True,
            message=f"Item substituído com sucesso",
            item_id=item_id
        )
