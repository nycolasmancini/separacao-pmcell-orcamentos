# -*- coding: utf-8 -*-
"""
Exceções customizadas para a camada de serviços.

Este módulo contém exceções específicas utilizadas pelos serviços de aplicação.
"""


class DuplicatePedidoError(Exception):
    """
    Exceção lançada quando tenta-se criar um pedido com orçamento duplicado.

    Attributes:
        numero_orcamento: Número do orçamento que já existe
        message: Mensagem de erro detalhada

    Example:
        >>> raise DuplicatePedidoError("30703")
    """
    def __init__(self, numero_orcamento: str):
        self.numero_orcamento = numero_orcamento
        self.message = f"Orçamento {numero_orcamento} já existe no sistema"
        super().__init__(self.message)


class VendedorNotFoundError(Exception):
    """
    Exceção lançada quando o vendedor especificado no PDF não é encontrado.

    Attributes:
        nome_vendedor: Nome do vendedor que não foi encontrado
        message: Mensagem de erro detalhada

    Example:
        >>> raise VendedorNotFoundError("NYCOLAS HENDRIGO MANCINI")
    """
    def __init__(self, nome_vendedor: str):
        self.nome_vendedor = nome_vendedor
        self.message = f"Vendedor '{nome_vendedor}' não encontrado no sistema"
        super().__init__(self.message)


class IntegrityValidationError(Exception):
    """
    Exceção lançada quando a validação de integridade matemática falha.

    Ocorre quando a soma dos produtos não bate com o valor total do orçamento.

    Attributes:
        soma_produtos: Soma calculada dos produtos
        valor_total: Valor total declarado no orçamento
        diferenca: Diferença entre soma e total
        message: Mensagem de erro detalhada

    Example:
        >>> raise IntegrityValidationError(
        ...     soma_produtos=Decimal("1405.00"),
        ...     valor_total=Decimal("1500.00")
        ... )
    """
    def __init__(self, soma_produtos, valor_total):
        from decimal import Decimal

        self.soma_produtos = Decimal(str(soma_produtos))
        self.valor_total = Decimal(str(valor_total))
        self.diferenca = abs(self.soma_produtos - self.valor_total)

        self.message = (
            f"Falha na validação de integridade: "
            f"Soma dos produtos (R$ {self.soma_produtos}) ≠ "
            f"Valor total (R$ {self.valor_total}). "
            f"Diferença: R$ {self.diferenca}"
        )
        super().__init__(self.message)
