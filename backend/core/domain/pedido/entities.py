# -*- coding: utf-8 -*-
"""
Entidades do domínio de Pedido.

Este módulo define as entidades principais:
- ItemPedido: Representa um produto dentro de um pedido
- Pedido: Agregado raiz que contém itens e gerencia o processo de separação

Author: PMCELL
Date: 2025-01-25
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from typing import List, Optional

from core.domain.pedido.value_objects import Logistica, Embalagem, StatusPedido
from core.domain.produto.entities import Produto

# Import timezone utilities
try:
    from django.utils import timezone as django_tz
    def now_with_tz():
        return django_tz.now()
except ImportError:
    # Fallback se não estiver em contexto Django
    def now_with_tz():
        return datetime.now()

logger = logging.getLogger(__name__)


class ValidationError(Exception):
    """Exceção levantada quando há erro de validação de domínio."""
    pass


@dataclass
class ItemPedido:
    """
    Representa um item (produto) dentro de um pedido.

    Attributes:
        id: Identificador único do item (opcional, gerado pelo banco)
        produto: Produto associado a este item
        quantidade_solicitada: Quantidade solicitada no orçamento
        quantidade_separada: Quantidade já separada (padrão: 0)
        separado: Flag indicando se o item está completamente separado
        separado_por: Usuário que marcou o item como separado (opcional)
        separado_em: Timestamp de quando foi marcado como separado (opcional)
        em_compra: Flag indicando se o item foi enviado para compra
        enviado_para_compra_por: Usuário que marcou o item para compra (opcional)
        enviado_para_compra_em: Timestamp de quando foi marcado para compra (opcional)
        substituido: Flag indicando se o item foi substituído por outro produto
        produto_substituto: Nome do produto que substituiu o original (opcional)
    """
    produto: Produto
    quantidade_solicitada: int
    id: Optional[int] = None
    quantidade_separada: int = 0
    separado: bool = False
    separado_por: Optional[str] = None  # Nome do usuário
    separado_em: Optional[datetime] = None
    em_compra: bool = False
    enviado_para_compra_por: Optional[str] = None
    enviado_para_compra_em: Optional[datetime] = None
    substituido: bool = False
    produto_substituto: Optional[str] = None

    def __post_init__(self):
        """Valida os dados do item após inicialização."""
        if self.quantidade_solicitada <= 0:
            raise ValidationError("Quantidade solicitada deve ser maior que zero")

        if self.quantidade_separada < 0:
            raise ValidationError("Quantidade separada não pode ser negativa")

        if self.quantidade_separada > self.quantidade_solicitada:
            raise ValidationError(
                "Quantidade separada não pode ser maior que a quantidade solicitada"
            )

        if self.produto_substituto and not self.substituido:
            raise ValidationError(
                "produto_substituto só pode ser preenchido se substituido=True"
            )

    def marcar_separado(self, usuario: str) -> None:
        """
        Marca o item como completamente separado.

        Args:
            usuario: Nome do usuário que está separando o item

        Raises:
            ValidationError: Se o item já estiver marcado como separado
        """
        if self.separado:
            logger.warning(f"Item {self.id} já está marcado como separado")
            raise ValidationError("Item já está marcado como separado")

        self.separado = True
        self.quantidade_separada = self.quantidade_solicitada
        self.separado_por = usuario
        self.separado_em = now_with_tz()

        logger.info(
            f"Item {self.id} (produto {self.produto.codigo}) marcado como separado "
            f"por {usuario}"
        )

    def esta_completo(self) -> bool:
        """
        Verifica se o item foi completamente separado.

        Returns:
            True se quantidade_separada == quantidade_solicitada, False caso contrário
        """
        return self.quantidade_separada == self.quantidade_solicitada

    def marcar_para_compra(self, usuario: str) -> None:
        """
        Marca o item para ser enviado ao painel de compras.

        Args:
            usuario: Nome do usuário que está marcando o item para compra

        Raises:
            ValidationError: Se o item já estiver separado ou já em compra
        """
        if self.separado:
            logger.warning(
                f"Item {self.id} já foi separado, não pode ser marcado para compra"
            )
            raise ValidationError("Item já foi separado")

        if self.em_compra:
            logger.warning(f"Item {self.id} já está marcado para compra")
            raise ValidationError("Item já está marcado para compra")

        self.em_compra = True
        self.enviado_para_compra_por = usuario
        self.enviado_para_compra_em = now_with_tz()

        logger.info(
            f"Item {self.id} (produto {self.produto.codigo}) marcado para compra "
            f"por {usuario}"
        )


@dataclass
class Pedido:
    """
    Agregado raiz representando um pedido de separação.

    Um pedido é criado a partir de um orçamento em PDF e contém múltiplos itens
    que precisam ser separados pela equipe.

    Attributes:
        numero_orcamento: Número único do orçamento (ex: "30567")
        codigo_cliente: Código do cliente no sistema
        nome_cliente: Nome completo do cliente
        vendedor: Nome do vendedor responsável
        data: Data do orçamento
        logistica: Tipo de logística/envio
        embalagem: Tipo de embalagem
        itens: Lista de itens do pedido
        id: Identificador único do pedido (opcional, gerado pelo banco)
        status: Status atual do pedido (padrão: EM_SEPARACAO)
        observacoes: Observações adicionais (opcional)
        criado_em: Timestamp de criação (gerado automaticamente)
        data_inicio: Timestamp de início da separação (gerado automaticamente)
        data_finalizacao: Timestamp de finalização (opcional)
    """
    numero_orcamento: str
    codigo_cliente: str
    nome_cliente: str
    vendedor: str
    data: str  # Formato: "DD/MM/AAAA"
    logistica: Logistica
    embalagem: Embalagem
    itens: List[ItemPedido] = field(default_factory=list)
    id: Optional[int] = None
    status: StatusPedido = StatusPedido.EM_SEPARACAO
    observacoes: Optional[str] = None
    criado_em: datetime = field(default_factory=now_with_tz)
    data_inicio: datetime = field(default_factory=now_with_tz)
    data_finalizacao: Optional[datetime] = None

    def __post_init__(self):
        """Valida os dados do pedido após inicialização."""
        self._validar_embalagem()

        if not self.numero_orcamento:
            raise ValidationError("Número do orçamento é obrigatório")

        if not self.codigo_cliente:
            raise ValidationError("Código do cliente é obrigatório")

        if not self.nome_cliente:
            raise ValidationError("Nome do cliente é obrigatório")

        if not self.vendedor:
            raise ValidationError("Vendedor é obrigatório")

        logger.info(
            f"Pedido criado: orçamento {self.numero_orcamento}, "
            f"cliente {self.nome_cliente}, {len(self.itens)} itens"
        )

    def _validar_embalagem(self) -> None:
        """
        Valida se a embalagem é compatível com o tipo de logística.

        Regras de negócio:
        - CORREIOS, MELHOR_ENVIO, ONIBUS: apenas CAIXA
        - RETIRA_LOJA, MOTOBOY: CAIXA ou SACOLA

        Raises:
            ValidationError: Se embalagem incompatível com logística
        """
        if Logistica.requer_caixa(self.logistica) and self.embalagem != Embalagem.CAIXA:
            raise ValidationError(
                f"Logística {self.logistica.value} aceita apenas embalagem CAIXA"
            )

    def adicionar_item(self, item: ItemPedido) -> None:
        """
        Adiciona um item ao pedido.

        Args:
            item: Item a ser adicionado

        Raises:
            ValidationError: Se o pedido já estiver finalizado
        """
        if self.status == StatusPedido.FINALIZADO:
            raise ValidationError("Não é possível adicionar itens a um pedido finalizado")

        self.itens.append(item)
        logger.info(
            f"Item adicionado ao pedido {self.numero_orcamento}: "
            f"produto {item.produto.codigo}, qtd {item.quantidade_solicitada}"
        )

    def calcular_progresso(self) -> int:
        """
        Calcula o percentual de progresso da separação.

        Returns:
            Percentual de 0 a 100 representando quantos itens foram separados

        Examples:
            >>> pedido = Pedido(...)
            >>> pedido.calcular_progresso()  # 0 itens separados
            0
            >>> pedido.itens[0].marcar_separado("João")
            >>> pedido.calcular_progresso()  # 1 de 3 itens
            33
        """
        if not self.itens:
            return 0

        itens_separados = sum(1 for item in self.itens if item.separado)
        progresso = (itens_separados / len(self.itens)) * 100

        return int(progresso)

    def pode_finalizar(self) -> bool:
        """
        Verifica se o pedido pode ser finalizado.

        Um pedido pode ser finalizado quando todos os itens foram separados.

        Returns:
            True se progresso == 100%, False caso contrário
        """
        return self.calcular_progresso() == 100

    def iniciar_cronometro(self) -> None:
        """
        Inicia o cronômetro do pedido.

        Chamado automaticamente no __post_init__, mas pode ser usado para reiniciar.
        """
        self.data_inicio = now_with_tz()
        logger.info(f"Cronômetro iniciado para pedido {self.numero_orcamento}")

    def finalizar(self, usuario: str) -> None:
        """
        Finaliza o pedido.

        Args:
            usuario: Nome do usuário que está finalizando

        Raises:
            ValidationError: Se o pedido não pode ser finalizado
        """
        if not self.pode_finalizar():
            raise ValidationError(
                f"Pedido não pode ser finalizado. Progresso: {self.calcular_progresso()}%"
            )

        self.status = StatusPedido.FINALIZADO
        self.data_finalizacao = now_with_tz()

        tempo_total = (self.data_finalizacao - self.data_inicio).total_seconds() / 60

        logger.info(
            f"Pedido {self.numero_orcamento} finalizado por {usuario}. "
            f"Tempo total: {tempo_total:.1f} minutos"
        )

    def tempo_decorrido_minutos(self) -> int:
        """
        Calcula o tempo decorrido desde o início da separação.

        Returns:
            Tempo em minutos
        """
        if self.data_finalizacao:
            fim = self.data_finalizacao
        else:
            fim = datetime.now()

        tempo_segundos = (fim - self.data_inicio).total_seconds()
        return int(tempo_segundos / 60)
