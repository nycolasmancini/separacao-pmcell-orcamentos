# -*- coding: utf-8 -*-
"""
Testes para o Use Case ObterMetricasTempoUseCase.
Fase 20: Implementar Métrica de Tempo Médio no Dashboard

Este módulo testa o cálculo de métricas de tempo médio de separação,
incluindo tendências e formatação humanizada.

Author: PMCELL
Date: 2025-01-27
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, MagicMock
from django.utils import timezone

from core.application.use_cases.obter_metricas_tempo import ObterMetricasTempoUseCase
from core.domain.pedido.value_objects import MetricasTempo


class TestObterMetricasTempoUseCase:
    """Testes para ObterMetricasTempoUseCase."""

    def test_calcular_tempo_medio_quando_ha_pedidos_finalizados_hoje(self):
        """
        Test 1: Deve calcular tempo médio quando há pedidos finalizados hoje.

        Cenário:
        - 2 pedidos finalizados hoje
        - Pedido 1: 30 minutos
        - Pedido 2: 60 minutos
        - Média esperada: 45 minutos
        """
        # Arrange
        mock_repository = Mock()
        mock_repository.calcular_tempo_medio_finalizacao.return_value = 45.0
        use_case = ObterMetricasTempoUseCase(mock_repository)

        # Act
        metricas = use_case.execute()

        # Assert
        assert metricas is not None
        assert isinstance(metricas, MetricasTempo)
        assert metricas.tempo_medio_hoje_minutos == 45.0
        assert mock_repository.calcular_tempo_medio_finalizacao.called

    def test_calcular_tempo_medio_ultimos_7_dias(self):
        """
        Test 2: Deve calcular tempo médio dos últimos 7 dias.

        Cenário:
        - Múltiplos pedidos nos últimos 7 dias
        - Média esperada: 52 minutos
        """
        # Arrange
        mock_repository = Mock()
        # Primeira chamada: hoje (45min), segunda chamada: 7 dias (52min)
        mock_repository.calcular_tempo_medio_finalizacao.side_effect = [45.0, 52.0]
        use_case = ObterMetricasTempoUseCase(mock_repository)

        # Act
        metricas = use_case.execute()

        # Assert
        assert metricas.tempo_medio_7dias_minutos == 52.0
        assert mock_repository.calcular_tempo_medio_finalizacao.call_count == 2

    def test_calcular_tendencia_melhorou_quando_hoje_mais_rapido(self):
        """
        Test 3: Deve calcular tendência 'melhorou' quando hoje está mais rápido.

        Cenário:
        - Hoje: 45 minutos
        - 7 dias: 52 minutos
        - Diferença: -13.5% (melhorou)
        """
        # Arrange
        mock_repository = Mock()
        mock_repository.calcular_tempo_medio_finalizacao.side_effect = [45.0, 52.0]
        use_case = ObterMetricasTempoUseCase(mock_repository)

        # Act
        metricas = use_case.execute()

        # Assert
        assert metricas.tendencia == 'melhorou'
        assert metricas.percentual_diferenca < 0
        # Cálculo: (45 - 52) / 52 * 100 = -13.46%
        assert abs(metricas.percentual_diferenca - (-13.46)) < 0.1

    def test_calcular_tendencia_piorou_quando_hoje_mais_lento(self):
        """
        Test 4: Deve calcular tendência 'piorou' quando hoje está mais lento.

        Cenário:
        - Hoje: 60 minutos
        - 7 dias: 50 minutos
        - Diferença: +20% (piorou)
        """
        # Arrange
        mock_repository = Mock()
        mock_repository.calcular_tempo_medio_finalizacao.side_effect = [60.0, 50.0]
        use_case = ObterMetricasTempoUseCase(mock_repository)

        # Act
        metricas = use_case.execute()

        # Assert
        assert metricas.tendencia == 'piorou'
        assert metricas.percentual_diferenca > 0
        # Cálculo: (60 - 50) / 50 * 100 = 20%
        assert abs(metricas.percentual_diferenca - 20.0) < 0.1

    def test_calcular_tendencia_estavel_quando_diferenca_menor_5_porcento(self):
        """
        Test 5: Deve calcular tendência 'estável' quando diferença < 5%.

        Cenário:
        - Hoje: 50 minutos
        - 7 dias: 51 minutos
        - Diferença: -1.96% (estável)
        """
        # Arrange
        mock_repository = Mock()
        mock_repository.calcular_tempo_medio_finalizacao.side_effect = [50.0, 51.0]
        use_case = ObterMetricasTempoUseCase(mock_repository)

        # Act
        metricas = use_case.execute()

        # Assert
        assert metricas.tendencia == 'estavel'
        assert abs(metricas.percentual_diferenca) < 5

    def test_retornar_sem_dados_quando_nao_ha_pedidos(self):
        """
        Test 6: Deve retornar 'sem_dados' quando não há pedidos finalizados.

        Cenário:
        - Nenhum pedido finalizado hoje
        - Nenhum pedido finalizado nos últimos 7 dias
        """
        # Arrange
        mock_repository = Mock()
        mock_repository.calcular_tempo_medio_finalizacao.side_effect = [None, None]
        use_case = ObterMetricasTempoUseCase(mock_repository)

        # Act
        metricas = use_case.execute()

        # Assert
        assert metricas.tendencia == 'sem_dados'
        assert metricas.tempo_medio_hoje_minutos is None
        assert metricas.tempo_medio_7dias_minutos is None
        assert metricas.percentual_diferenca is None

    def test_formatacao_humanizada_tempo(self):
        """
        Test 7: Deve formatar tempo em minutos de forma humanizada.

        Casos de teste:
        - 45 min -> "45 min"
        - 90 min -> "1h 30min"
        - 60 min -> "1h"
        - None -> "Sem dados"
        """
        # Arrange
        mock_repository = Mock()
        mock_repository.calcular_tempo_medio_finalizacao.side_effect = [45.0, 52.0]
        use_case = ObterMetricasTempoUseCase(mock_repository)

        # Act
        metricas = use_case.execute()
        metricas_dict = use_case.to_dict(metricas)

        # Assert
        assert metricas_dict['tempo_hoje_formatado'] == "45 min"
        assert metricas_dict['tempo_7dias_formatado'] == "52 min"

        # Testar outros formatos
        assert use_case._formatar_tempo(90.0) == "1h 30min"
        assert use_case._formatar_tempo(60.0) == "1h"
        assert use_case._formatar_tempo(120.0) == "2h"
        assert use_case._formatar_tempo(None) == "Sem dados"

    def test_formatacao_percentual(self):
        """
        Test 8: Deve formatar percentual com sinal correto.

        Casos de teste:
        - -13.5 -> "-13.5%"
        - +8.0 -> "+8.0%"
        - None -> ""
        """
        # Arrange
        mock_repository = Mock()
        mock_repository.calcular_tempo_medio_finalizacao.side_effect = [45.0, 52.0]
        use_case = ObterMetricasTempoUseCase(mock_repository)

        # Act
        metricas = use_case.execute()
        metricas_dict = use_case.to_dict(metricas)

        # Assert
        assert '%' in metricas_dict['percentual_formatado']

        # Testar formatação direta
        assert use_case._formatar_percentual(-13.5) == "-13.5%"
        assert use_case._formatar_percentual(8.0) == "+8.0%"
        assert use_case._formatar_percentual(0.0) == "0.0%"  # Zero não precisa de sinal
        assert use_case._formatar_percentual(None) == ""


class TestObterMetricasTempoUseCaseIntegracao:
    """Testes de integração com repository real (via fixtures)."""

    @pytest.mark.django_db
    def test_metricas_com_pedidos_reais_finalizados(self):
        """
        Test de integração: Deve calcular métricas com pedidos reais.

        Este teste será executado quando o repository estiver implementado.
        """
        # Este teste será implementado após o repository estar completo
        # Por enquanto, apenas garante que a estrutura está correta
        pass
