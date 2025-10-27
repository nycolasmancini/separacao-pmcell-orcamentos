# -*- coding: utf-8 -*-
"""
DTOs para operações relacionadas a Orçamentos.

Este módulo contém Data Transfer Objects utilizados na camada de aplicação
para transportar dados de orçamentos entre as camadas.
"""

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class OrcamentoHeaderDTO:
    """
    DTO para dados do cabeçalho de um orçamento extraído de PDF.

    Attributes:
        numero_orcamento: Número do orçamento (5 dígitos)
        codigo_cliente: Código do cliente (6 dígitos)
        nome_cliente: Nome completo do cliente
        vendedor: Nome do vendedor responsável
        data: Data do orçamento no formato DD/MM/AA
        errors: Lista de campos que falharam na extração

    Examples:
        >>> header = OrcamentoHeaderDTO(
        ...     numero_orcamento="30567",
        ...     codigo_cliente="001007",
        ...     nome_cliente="ROSANA DE CASSIA SINEZIO",
        ...     vendedor="NYCOLAS HENDRIGO MANCINI",
        ...     data="22/10/25"
        ... )
        >>> header.numero_orcamento
        '30567'

    Notes:
        - Se algum campo não for encontrado durante extração, será None
        - Campos faltantes são adicionados à lista 'errors'
        - Não lança exceção para campos faltantes (fail-safe)
    """

    numero_orcamento: Optional[str] = None
    codigo_cliente: Optional[str] = None
    nome_cliente: Optional[str] = None
    vendedor: Optional[str] = None
    data: Optional[str] = None
    errors: List[str] = field(default_factory=list)

    def __post_init__(self):
        """
        Validações pós-inicialização.

        Verifica quais campos obrigatórios estão vazios e adiciona à lista de erros.
        """
        campos_obrigatorios = {
            'numero_orcamento': self.numero_orcamento,
            'codigo_cliente': self.codigo_cliente,
            'nome_cliente': self.nome_cliente,
            'vendedor': self.vendedor,
            'data': self.data
        }

        for campo, valor in campos_obrigatorios.items():
            if not valor:
                if campo not in self.errors:
                    self.errors.append(campo)

    @property
    def is_valid(self) -> bool:
        """
        Verifica se todos os campos obrigatórios foram extraídos.

        Returns:
            True se não há erros, False caso contrário
        """
        return len(self.errors) == 0

    def __str__(self) -> str:
        """Representação em string do DTO."""
        if self.is_valid:
            return f"Orçamento #{self.numero_orcamento} - {self.nome_cliente}"
        return f"Orçamento (incompleto) - {len(self.errors)} campos com erro"


@dataclass
class ProdutoDTO:
    """
    DTO para dados de um produto extraído de PDF.

    Attributes:
        codigo: Código do produto (5 dígitos numéricos)
        descricao: Descrição do produto
        quantidade: Quantidade do produto
        valor_unitario: Valor unitário do produto (Decimal para precisão)
        valor_total: Valor total (quantidade × valor_unitario)
        errors: Lista de erros encontrados durante extração

    Examples:
        >>> from decimal import Decimal
        >>> produto = ProdutoDTO(
        ...     codigo="00010",
        ...     descricao="FO11 --> FONE PMCELL",
        ...     quantidade=30,
        ...     valor_unitario=Decimal("3.50"),
        ...     valor_total=Decimal("105.00")
        ... )
        >>> produto.codigo
        '00010'
        >>> produto.is_valid
        True

    Notes:
        - Validação matemática: quantidade × valor_unitario = valor_total (tolerância 0.01)
        - Se algum campo não for encontrado durante extração, será None
        - Erros de extração são adicionados à lista 'errors'
        - Não lança exceção para campos faltantes (fail-safe)
    """

    codigo: Optional[str] = None
    descricao: Optional[str] = None
    quantidade: Optional[int] = None
    valor_unitario: Optional[object] = None  # Decimal
    valor_total: Optional[object] = None  # Decimal
    errors: List[str] = field(default_factory=list)

    def __post_init__(self):
        """
        Validações pós-inicialização.

        Verifica:
        - Campos obrigatórios presentes
        - Validação matemática (quantidade × valor_unitario = valor_total)
        """
        from decimal import Decimal

        # Validar campos obrigatórios
        campos_obrigatorios = {
            'codigo': self.codigo,
            'descricao': self.descricao,
            'quantidade': self.quantidade,
            'valor_unitario': self.valor_unitario,
            'valor_total': self.valor_total
        }

        for campo, valor in campos_obrigatorios.items():
            if valor is None:
                if campo not in self.errors:
                    self.errors.append(campo)

        # Validar cálculo matemático se todos os campos numéricos estão presentes
        if (self.quantidade is not None and
            self.valor_unitario is not None and
            self.valor_total is not None):

            try:
                calculo_esperado = Decimal(str(self.quantidade)) * Decimal(str(self.valor_unitario))
                diferenca = abs(calculo_esperado - Decimal(str(self.valor_total)))

                # Tolerância de 0.01 para arredondamentos
                if diferenca > Decimal("0.01"):
                    erro_msg = (
                        f'validacao_matematica: {self.quantidade} × {self.valor_unitario} '
                        f'= {calculo_esperado}, mas valor_total é {self.valor_total}'
                    )
                    if erro_msg not in self.errors:
                        self.errors.append(erro_msg)
            except Exception as e:
                erro_msg = f'erro_calculo: {str(e)}'
                if erro_msg not in self.errors:
                    self.errors.append(erro_msg)

    @property
    def is_valid(self) -> bool:
        """
        Verifica se o produto foi extraído corretamente.

        Returns:
            True se não há erros, False caso contrário
        """
        return len(self.errors) == 0

    def to_entity(self):
        """
        Converte DTO para entidade de domínio Produto.

        Returns:
            Produto: Entidade de domínio

        Raises:
            ValueError: Se DTO não for válido
        """
        from core.domain.produto.entities import Produto
        from decimal import Decimal

        if not self.is_valid:
            raise ValueError(f'ProdutoDTO inválido. Erros: {self.errors}')

        return Produto(
            codigo=self.codigo,
            descricao=self.descricao,
            quantidade=self.quantidade,
            valor_unitario=Decimal(str(self.valor_unitario)),
            valor_total=Decimal(str(self.valor_total))
        )

    def __str__(self) -> str:
        """Representação em string do DTO."""
        if self.is_valid:
            return f"Produto({self.codigo} - {self.descricao})"
        return f"Produto(código={self.codigo}, erros={len(self.errors)})"
