# -*- coding: utf-8 -*-
"""
Entidade de domínio Produto (Fase 9).

Este módulo define a entidade Produto seguindo princípios de DDD.
A entidade possui validação matemática automática: quantidade × valor_unitario = valor_total.
"""

from dataclasses import dataclass
from decimal import Decimal
from typing import Optional


# Constantes
CODIGO_LENGTH = 5


@dataclass
class Produto:
    """
    Entidade de domínio que representa um Produto.

    Attributes:
        codigo (str): Código do produto (5 dígitos numéricos)
        descricao (str): Descrição do produto
        quantidade (int): Quantidade do produto
        valor_unitario (Decimal): Valor unitário do produto
        valor_total (Decimal): Valor total (quantidade × valor_unitario)

    Raises:
        ValueError: Se validações falharem (código inválido, cálculo incorreto)
    """

    codigo: str
    descricao: str
    quantidade: int
    valor_unitario: Decimal
    valor_total: Decimal
    id: Optional[int] = None

    def __post_init__(self):
        """
        Validações executadas após inicialização.

        Valida:
        - Código deve ter exatamente 5 dígitos numéricos
        - Cálculo matemático deve estar correto (quantidade × valor_unitario = valor_total)

        Raises:
            ValueError: Se validações falharem
        """
        self._validar_codigo()
        self._validar_calculo_matematico()

    def _validar_codigo(self):
        """
        Valida que o código tem exatamente 5 dígitos numéricos.

        Raises:
            ValueError: Se código não tiver 5 dígitos numéricos
        """
        if not isinstance(self.codigo, str):
            raise ValueError('Código deve ser uma string')

        if len(self.codigo) != CODIGO_LENGTH:
            raise ValueError(f'Código deve ter exatamente {CODIGO_LENGTH} dígitos')

        if not self.codigo.isdigit():
            raise ValueError(f'Código deve conter apenas dígitos numéricos (5 dígitos)')

    def _validar_calculo_matematico(self):
        """
        Valida que quantidade × valor_unitario = valor_total.

        Usa Decimal para precisão matemática exata.

        Raises:
            ValueError: Se cálculo matemático estiver incorreto
        """
        if not self.validar_calculo():
            raise ValueError(
                f'Falha na validação matemática: '
                f'{self.quantidade} × {self.valor_unitario} = {self.quantidade * self.valor_unitario}, '
                f'mas valor_total fornecido é {self.valor_total}'
            )

    def validar_calculo(self) -> bool:
        """
        Verifica se o cálculo matemático está correto.

        Returns:
            bool: True se quantidade × valor_unitario = valor_total, False caso contrário
        """
        calculo_esperado = Decimal(str(self.quantidade)) * self.valor_unitario
        return calculo_esperado == self.valor_total

    def __str__(self):
        """Representação em string do produto."""
        return f'Produto({self.codigo} - {self.descricao})'

    def __repr__(self):
        """Representação técnica do produto."""
        return (
            f'Produto(codigo={self.codigo!r}, descricao={self.descricao!r}, '
            f'quantidade={self.quantidade}, valor_unitario={self.valor_unitario}, '
            f'valor_total={self.valor_total})'
        )
