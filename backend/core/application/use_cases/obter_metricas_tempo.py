# -*- coding: utf-8 -*-
"""
Use Case: Obter Métricas de Tempo Médio de Separação.
Fase 20: Implementar Métrica de Tempo Médio no Dashboard

Este módulo implementa o caso de uso de obtenção de métricas de tempo médio
de separação de pedidos, comparando o desempenho de hoje com os últimos 7 dias.
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from django.utils import timezone
from core.domain.pedido.value_objects import MetricasTempo
from core.infrastructure.persistence.repositories.pedido_repository import (
    PedidoRepositoryInterface
)

# Configuração de logging
logger = logging.getLogger(__name__)


class ObterMetricasTempoUseCase:
    """
    Use Case para obter métricas de tempo médio de separação.

    Este use case calcula o tempo médio de separação de pedidos finalizados
    em dois períodos (hoje e últimos 7 dias) e determina a tendência de
    performance da equipe.

    Attributes:
        pedido_repository: Repositório para acessar dados de pedidos
    """

    def __init__(self, pedido_repository: PedidoRepositoryInterface):
        """
        Inicializa o use case.

        Args:
            pedido_repository: Repositório de pedidos
        """
        self.pedido_repository = pedido_repository

    def execute(self) -> MetricasTempo:
        """
        Executa o use case para obter métricas de tempo.

        Returns:
            MetricasTempo: Value Object contendo as métricas calculadas

        Raises:
            Exception: Se houver erro ao calcular métricas
        """
        try:
            logger.info("Iniciando cálculo de métricas de tempo médio")

            # Obter timezone de São Paulo
            now = timezone.now()

            # Calcular períodos
            hoje_inicio = now.replace(hour=0, minute=0, second=0, microsecond=0)
            hoje_fim = now

            sete_dias_inicio = hoje_inicio - timedelta(days=6)  # Últimos 7 dias incluindo hoje
            sete_dias_fim = now

            # Calcular tempo médio de hoje
            tempo_medio_hoje = self.pedido_repository.calcular_tempo_medio_finalizacao(
                data_inicio=hoje_inicio,
                data_fim=hoje_fim
            )

            # Calcular tempo médio dos últimos 7 dias
            tempo_medio_7dias = self.pedido_repository.calcular_tempo_medio_finalizacao(
                data_inicio=sete_dias_inicio,
                data_fim=sete_dias_fim
            )

            # Calcular tendência e percentual de diferença
            tendencia, percentual = self._calcular_tendencia(
                tempo_medio_hoje,
                tempo_medio_7dias
            )

            # Criar Value Object
            metricas = MetricasTempo(
                tempo_medio_hoje_minutos=tempo_medio_hoje,
                tempo_medio_7dias_minutos=tempo_medio_7dias,
                percentual_diferenca=percentual,
                tendencia=tendencia
            )

            logger.info(
                f"Métricas calculadas com sucesso: "
                f"Hoje={tempo_medio_hoje}, "
                f"7dias={tempo_medio_7dias}, "
                f"Tendência={tendencia}"
            )

            return metricas

        except Exception as e:
            logger.error(f"Erro ao obter métricas de tempo: {e}")
            raise

    def _calcular_tendencia(
        self,
        tempo_hoje: Optional[float],
        tempo_7dias: Optional[float]
    ) -> tuple:
        """
        Calcula a tendência e o percentual de diferença entre os períodos.

        Args:
            tempo_hoje: Tempo médio de hoje em minutos
            tempo_7dias: Tempo médio dos últimos 7 dias em minutos

        Returns:
            Tupla (tendencia, percentual_diferenca) onde:
            - tendencia: 'melhorou', 'piorou', 'estavel', ou 'sem_dados'
            - percentual_diferenca: Percentual de mudança (negativo = melhora)
        """
        # Caso não haja dados
        if tempo_hoje is None and tempo_7dias is None:
            return ('sem_dados', None)

        # Caso só tenha dados de hoje
        if tempo_7dias is None:
            return ('sem_dados', None)

        # Caso só tenha dados históricos
        if tempo_hoje is None:
            return ('sem_dados', None)

        # Calcular percentual de diferença
        # Fórmula: ((hoje - 7dias) / 7dias) * 100
        # Negativo = melhorou (ficou mais rápido)
        # Positivo = piorou (ficou mais lento)
        diferenca = tempo_hoje - tempo_7dias
        percentual = (diferenca / tempo_7dias) * 100

        # Definir tendência com margem de 5% para considerar estável
        if abs(percentual) < 5:
            return ('estavel', percentual)
        elif percentual < 0:
            return ('melhorou', percentual)
        else:
            return ('piorou', percentual)

    def to_dict(self, metricas: MetricasTempo) -> Dict[str, Any]:
        """
        Converte MetricasTempo para dicionário (útil para templates).

        Args:
            metricas: Value Object MetricasTempo

        Returns:
            Dicionário com as métricas formatadas
        """
        return {
            'tempo_medio_hoje_minutos': metricas.tempo_medio_hoje_minutos,
            'tempo_medio_7dias_minutos': metricas.tempo_medio_7dias_minutos,
            'percentual_diferenca': metricas.percentual_diferenca,
            'tendencia': metricas.tendencia,
            # Formatação humanizada (para templates)
            'tempo_hoje_formatado': self._formatar_tempo(metricas.tempo_medio_hoje_minutos),
            'tempo_7dias_formatado': self._formatar_tempo(metricas.tempo_medio_7dias_minutos),
            'percentual_formatado': self._formatar_percentual(metricas.percentual_diferenca),
        }

    def _formatar_tempo(self, minutos: Optional[float]) -> str:
        """
        Formata tempo em minutos para exibição humanizada.

        Args:
            minutos: Tempo em minutos

        Returns:
            String formatada (ex: "45 min", "1h 30min", "Sem dados")
        """
        if minutos is None:
            return "Sem dados"

        minutos_int = int(round(minutos))

        if minutos_int < 60:
            return f"{minutos_int} min"
        else:
            horas = minutos_int // 60
            mins_resto = minutos_int % 60
            if mins_resto == 0:
                return f"{horas}h"
            else:
                return f"{horas}h {mins_resto}min"

    def _formatar_percentual(self, percentual: Optional[float]) -> str:
        """
        Formata percentual para exibição humanizada.

        Args:
            percentual: Percentual de diferença

        Returns:
            String formatada (ex: "-13%", "+8%", "")
        """
        if percentual is None:
            return ""

        sinal = "+" if percentual > 0 else ""
        return f"{sinal}{percentual:.1f}%"
