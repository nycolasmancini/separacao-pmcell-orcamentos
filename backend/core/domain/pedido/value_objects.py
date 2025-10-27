# -*- coding: utf-8 -*-
"""
Value Objects para o domínio de Pedido.

Este módulo define os Value Objects imutáveis usados pela entidade Pedido:
- Logistica: Tipos de logística disponíveis
- Embalagem: Tipos de embalagem permitidos
- StatusPedido: Estados possíveis de um pedido
- MetricasTempo: Métricas de tempo médio de separação

Author: PMCELL
Date: 2025-01-25
"""

from enum import Enum
from typing import Set, Optional
from dataclasses import dataclass


class Logistica(str, Enum):
    """
    Tipos de logística disponíveis para envio de pedidos.

    Attributes:
        CORREIOS: Envio via Correios (aceita apenas CAIXA)
        MELHOR_ENVIO: Envio via Melhor Envio (aceita apenas CAIXA)
        ONIBUS: Envio via ônibus (aceita apenas CAIXA)
        RETIRA_LOJA: Cliente retira na loja (aceita CAIXA ou SACOLA)
        MOTOBOY: Entrega via motoboy (aceita CAIXA ou SACOLA)
    """
    CORREIOS = "CORREIOS"
    MELHOR_ENVIO = "MELHOR_ENVIO"
    ONIBUS = "ONIBUS"
    RETIRA_LOJA = "RETIRA_LOJA"
    MOTOBOY = "MOTOBOY"

    @classmethod
    def requer_caixa(cls, logistica: 'Logistica') -> bool:
        """
        Verifica se a logística exige embalagem tipo CAIXA.

        Args:
            logistica: Tipo de logística a verificar

        Returns:
            True se exige CAIXA, False caso contrário
        """
        return logistica in [cls.CORREIOS, cls.MELHOR_ENVIO, cls.ONIBUS]


class Embalagem(str, Enum):
    """
    Tipos de embalagem disponíveis.

    Attributes:
        CAIXA: Embalagem em caixa (aceito por todas as logísticas)
        SACOLA: Embalagem em sacola (aceito apenas por RETIRA_LOJA e MOTOBOY)
    """
    CAIXA = "CAIXA"
    SACOLA = "SACOLA"


class StatusPedido(str, Enum):
    """
    Estados possíveis de um pedido durante seu ciclo de vida.

    Attributes:
        EM_SEPARACAO: Pedido criado e em processo de separação
        FINALIZADO: Todos os itens foram separados
        CANCELADO: Pedido foi cancelado
    """
    EM_SEPARACAO = "EM_SEPARACAO"
    FINALIZADO = "FINALIZADO"
    CANCELADO = "CANCELADO"


@dataclass(frozen=True)
class MetricasTempo:
    """
    Value Object para métricas de tempo médio de separação de pedidos.

    Este VO encapsula as métricas de performance da equipe de separação,
    permitindo comparar o desempenho de hoje com os últimos 7 dias.

    Attributes:
        tempo_medio_hoje_minutos: Tempo médio (em minutos) dos pedidos finalizados hoje.
                                  None se não houver pedidos finalizados hoje.
        tempo_medio_7dias_minutos: Tempo médio (em minutos) dos pedidos finalizados
                                   nos últimos 7 dias (incluindo hoje).
                                   None se não houver pedidos.
        percentual_diferenca: Percentual de diferença entre hoje e 7 dias.
                             Negativo = melhorou, Positivo = piorou.
                             None se não houver dados suficientes.
        tendencia: Indicador visual de tendência. Valores possíveis:
                  - 'melhorou': Hoje está mais rápido que a média de 7 dias
                  - 'piorou': Hoje está mais lento que a média de 7 dias
                  - 'estavel': Diferença menor que 5%
                  - 'sem_dados': Não há dados suficientes para calcular

    Example:
        >>> metricas = MetricasTempo(
        ...     tempo_medio_hoje_minutos=45.0,
        ...     tempo_medio_7dias_minutos=52.0,
        ...     percentual_diferenca=-13.5,
        ...     tendencia='melhorou'
        ... )
        >>> metricas.tempo_medio_hoje_minutos
        45.0
    """
    tempo_medio_hoje_minutos: Optional[float]
    tempo_medio_7dias_minutos: Optional[float]
    percentual_diferenca: Optional[float]
    tendencia: str  # 'melhorou', 'piorou', 'estavel', 'sem_dados'

    def __post_init__(self):
        """Valida os valores após inicialização."""
        valid_tendencias = {'melhorou', 'piorou', 'estavel', 'sem_dados'}
        if self.tendencia not in valid_tendencias:
            raise ValueError(
                f"Tendência inválida: {self.tendencia}. "
                f"Deve ser uma de: {valid_tendencias}"
            )
