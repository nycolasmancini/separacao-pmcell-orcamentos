# -*- coding: utf-8 -*-
"""
DTOs para operações relacionadas a Pedidos.

Este módulo contém Data Transfer Objects utilizados na camada de aplicação
para transportar dados de pedidos entre as camadas.

Author: PMCELL
Date: 2025-01-25
"""

from dataclasses import dataclass, field
from typing import Optional, List

from core.domain.pedido.value_objects import Logistica, Embalagem
from core.domain.pedido.entities import Pedido


@dataclass
class CriarPedidoRequestDTO:
    """
    DTO para request de criação de pedido.

    Attributes:
        pdf_path: Caminho completo para o arquivo PDF do orçamento
        logistica: Tipo de logística/envio (Logistica enum)
        embalagem: Tipo de embalagem (Embalagem enum)
        usuario_criador_id: ID do usuário que está criando o pedido
        observacoes: Observações adicionais sobre o pedido (opcional)

    Examples:
        >>> from core.domain.pedido.value_objects import Logistica, Embalagem
        >>> request = CriarPedidoRequestDTO(
        ...     pdf_path="/path/to/orcamento_30567.pdf",
        ...     logistica=Logistica.CORREIOS,
        ...     embalagem=Embalagem.CAIXA,
        ...     usuario_criador_id=1,
        ...     observacoes="Pedido urgente"
        ... )
        >>> request.pdf_path
        '/path/to/orcamento_30567.pdf'

    Notes:
        - pdf_path deve apontar para arquivo existente e legível
        - logistica e embalagem devem ser compatíveis (validado no use case)
        - observacoes é opcional
    """

    pdf_path: str
    logistica: Logistica
    embalagem: Embalagem
    usuario_criador_id: int
    observacoes: Optional[str] = None

    def __post_init__(self):
        """
        Validações pós-inicialização.

        Verifica:
        - pdf_path não está vazio
        - usuario_criador_id é positivo
        - logistica e embalagem são enums válidos
        """
        if not self.pdf_path:
            raise ValueError("pdf_path é obrigatório")

        if not isinstance(self.logistica, Logistica):
            raise ValueError("logistica deve ser uma instância de Logistica enum")

        if not isinstance(self.embalagem, Embalagem):
            raise ValueError("embalagem deve ser uma instância de Embalagem enum")

        if self.usuario_criador_id <= 0:
            raise ValueError("usuario_criador_id deve ser positivo")


@dataclass
class CriarPedidoResponseDTO:
    """
    DTO para response de criação de pedido.

    Attributes:
        success: Indica se a criação foi bem-sucedida
        pedido: Entidade Pedido criada (None se falhou)
        error_message: Mensagem de erro principal (None se sucesso)
        validation_errors: Lista de erros de validação detalhados

    Examples:
        >>> # Sucesso
        >>> response = CriarPedidoResponseDTO(
        ...     success=True,
        ...     pedido=pedido_criado,
        ...     error_message=None,
        ...     validation_errors=[]
        ... )
        >>> response.success
        True

        >>> # Falha
        >>> response = CriarPedidoResponseDTO(
        ...     success=False,
        ...     pedido=None,
        ...     error_message="Falha na extração do PDF",
        ...     validation_errors=["codigo_cliente: campo faltante"]
        ... )
        >>> response.success
        False

    Notes:
        - Se success=True, pedido deve estar preenchido
        - Se success=False, error_message deve explicar o motivo
        - validation_errors contém detalhes técnicos de validações que falharam
    """

    success: bool
    pedido: Optional[Pedido] = None
    error_message: Optional[str] = None
    validation_errors: List[str] = field(default_factory=list)

    def __post_init__(self):
        """
        Validações pós-inicialização.

        Verifica consistência:
        - Se success=True, pedido deve existir
        - Se success=False, error_message deve existir
        """
        if self.success and self.pedido is None:
            raise ValueError(
                "Se success=True, pedido deve ser fornecido"
            )

        if not self.success and not self.error_message:
            raise ValueError(
                "Se success=False, error_message deve ser fornecido"
            )

    def __str__(self) -> str:
        """Representação em string do DTO."""
        if self.success:
            return f"CriarPedidoResponse(success=True, pedido={self.pedido.numero_orcamento})"
        return f"CriarPedidoResponse(success=False, error={self.error_message})"


@dataclass
class FinalizarPedidoResponseDTO:
    """
    DTO para response de finalização de pedido.

    Attributes:
        sucesso: Indica se a finalização foi bem-sucedida
        pedido_id: ID do pedido finalizado
        status: Status final do pedido (FINALIZADO se sucesso)
        tempo_total_minutos: Tempo total de separação em minutos
        mensagem: Mensagem descritiva do resultado

    Examples:
        >>> # Sucesso
        >>> response = FinalizarPedidoResponseDTO(
        ...     sucesso=True,
        ...     pedido_id=123,
        ...     status='FINALIZADO',
        ...     tempo_total_minutos=45.5,
        ...     mensagem='Pedido finalizado com sucesso'
        ... )
        >>> response.sucesso
        True

        >>> # Falha
        >>> response = FinalizarPedidoResponseDTO(
        ...     sucesso=False,
        ...     pedido_id=123,
        ...     status='EM_SEPARACAO',
        ...     tempo_total_minutos=0.0,
        ...     mensagem='Pedido não pode ser finalizado. Progresso: 33%'
        ... )
        >>> response.sucesso
        False

    Notes:
        - tempo_total_minutos é calculado como: (data_finalizacao - data_inicio)
        - Apenas pedidos com 100% de progresso podem ser finalizados
    """

    sucesso: bool
    pedido_id: int
    status: str
    tempo_total_minutos: float
    mensagem: str

    def __post_init__(self):
        """
        Validações pós-inicialização.

        Verifica:
        - pedido_id é positivo
        - tempo_total_minutos não é negativo
        - mensagem não está vazia
        """
        if self.pedido_id <= 0:
            raise ValueError("pedido_id deve ser positivo")

        if self.tempo_total_minutos < 0:
            raise ValueError("tempo_total_minutos não pode ser negativo")

        if not self.mensagem:
            raise ValueError("mensagem é obrigatória")

    def __str__(self) -> str:
        """Representação em string do DTO."""
        if self.sucesso:
            return f"FinalizarPedidoResponse(sucesso=True, pedido_id={self.pedido_id}, tempo={self.tempo_total_minutos:.1f}min)"
        return f"FinalizarPedidoResponse(sucesso=False, pedido_id={self.pedido_id}, mensagem={self.mensagem})"
