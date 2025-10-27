# -*- coding: utf-8 -*-
"""
Testes para CriarPedidoUseCase.

Este módulo testa o caso de uso de criação de pedidos a partir de PDFs,
incluindo extração, validação e persistência.

Author: PMCELL
Date: 2025-01-25
"""

import pytest
from decimal import Decimal
from pathlib import Path
from unittest.mock import Mock, MagicMock

from core.application.use_cases.criar_pedido import CriarPedidoUseCase
from core.application.dtos.pedido_dtos import CriarPedidoRequestDTO, CriarPedidoResponseDTO
from core.application.dtos.orcamento_dtos import OrcamentoHeaderDTO, ProdutoDTO
from core.domain.pedido.value_objects import Logistica, Embalagem
from core.domain.pedido.entities import Pedido, ItemPedido
from core.domain.produto.entities import Produto


class TestCriarPedidoUseCase:
    """Testes para o caso de uso de criação de pedido."""

    @pytest.fixture
    def mock_pdf_parser(self):
        """Mock do PDFParser."""
        parser = Mock()
        parser.extrair_texto = Mock(return_value="Texto do PDF")
        return parser

    @pytest.fixture
    def mock_header_extractor(self):
        """Mock do PDFHeaderExtractor."""
        extractor = Mock()
        extractor.extrair_header = Mock(return_value=OrcamentoHeaderDTO(
            numero_orcamento="30567",
            codigo_cliente="001007",
            nome_cliente="ROSANA DE CASSIA SINEZIO",
            vendedor="NYCOLAS HENDRIGO MANCINI",
            data="22/10/25"
        ))
        return extractor

    @pytest.fixture
    def mock_product_extractor(self):
        """Mock do PDFProductExtractor."""
        extractor = Mock()
        extractor.extrair_produtos = Mock(return_value=[
            ProdutoDTO(
                codigo="00010",
                descricao="FO11 --> FONE PMCELL",
                quantidade=30,
                valor_unitario=Decimal("3.50"),
                valor_total=Decimal("105.00")
            ),
            ProdutoDTO(
                codigo="00020",
                descricao="CABO USB-C",
                quantidade=10,
                valor_unitario=Decimal("5.00"),
                valor_total=Decimal("50.00")
            )
        ])
        return extractor

    @pytest.fixture
    def mock_pedido_repository(self):
        """Mock do PedidoRepository."""
        repository = Mock()
        repository.save = Mock(return_value=1)  # ID do pedido criado
        return repository

    @pytest.fixture
    def use_case(self, mock_pdf_parser, mock_header_extractor,
                 mock_product_extractor, mock_pedido_repository):
        """Instância do use case com mocks."""
        return CriarPedidoUseCase(
            pdf_parser=mock_pdf_parser,
            header_extractor=mock_header_extractor,
            product_extractor=mock_product_extractor,
            pedido_repository=mock_pedido_repository
        )

    @pytest.fixture
    def valid_request_dto(self):
        """DTO de request válido."""
        return CriarPedidoRequestDTO(
            pdf_path="/path/to/orcamento_30567.pdf",
            logistica=Logistica.CORREIOS,
            embalagem=Embalagem.CAIXA,
            usuario_criador_id=1,
            observacoes="Pedido urgente"
        )

    # ==================== TESTE 1: SUCESSO COM PDF VÁLIDO ====================
    def test_criar_pedido_success_with_valid_pdf(
        self, use_case, valid_request_dto, mock_pedido_repository
    ):
        """
        Testa criação bem-sucedida de pedido a partir de PDF válido.

        Cenário:
        - PDF válido com header e produtos extraídos corretamente
        - Validações matemáticas passam
        - Validações de negócio passam
        - Pedido é persistido com sucesso

        Resultado esperado:
        - ResponseDTO com success=True
        - Pedido criado com dados corretos
        - 2 itens adicionados ao pedido
        - Repositório foi chamado para salvar
        """
        # Act
        response = use_case.execute(valid_request_dto)

        # Assert
        assert response.success is True
        assert response.pedido is not None
        assert response.error_message is None
        assert len(response.validation_errors) == 0

        # Verificar dados do pedido
        assert response.pedido.numero_orcamento == "30567"
        assert response.pedido.nome_cliente == "ROSANA DE CASSIA SINEZIO"
        assert response.pedido.vendedor == "NYCOLAS HENDRIGO MANCINI"
        assert response.pedido.logistica == Logistica.CORREIOS
        assert response.pedido.embalagem == Embalagem.CAIXA
        assert len(response.pedido.itens) == 2

        # Verificar que repositório foi chamado
        mock_pedido_repository.save.assert_called_once()

    # ==================== TESTE 2: VALIDAÇÃO DE HEADER ====================
    def test_criar_pedido_validates_header_extraction(
        self, use_case, valid_request_dto, mock_header_extractor
    ):
        """
        Testa que use case valida extração de header corretamente.

        Cenário:
        - Header incompleto (campo faltando)
        - Extração retorna DTO com erros

        Resultado esperado:
        - ResponseDTO com success=False
        - Mensagem de erro sobre header inválido
        - Erros de validação listados
        - Pedido não foi criado
        """
        # Arrange: Header inválido
        mock_header_extractor.extrair_header.return_value = OrcamentoHeaderDTO(
            numero_orcamento="30567",
            codigo_cliente=None,  # Campo faltando
            nome_cliente="ROSANA",
            vendedor="NYCOLAS",
            data="22/10/25"
        )

        # Act
        response = use_case.execute(valid_request_dto)

        # Assert
        assert response.success is False
        assert "header" in response.error_message.lower()
        assert len(response.validation_errors) > 0
        assert "codigo_cliente" in response.validation_errors

    # ==================== TESTE 3: VALIDAÇÃO DE PRODUTOS ====================
    def test_criar_pedido_validates_products_extraction(
        self, use_case, valid_request_dto, mock_product_extractor
    ):
        """
        Testa que use case valida extração de produtos corretamente.

        Cenário:
        - Produto com erro de extração (campo faltando)
        - Lista de produtos contém DTOs inválidos

        Resultado esperado:
        - ResponseDTO com success=False
        - Mensagem de erro sobre produtos inválidos
        - Erros de validação listados
        """
        # Arrange: Produto inválido
        mock_product_extractor.extrair_produtos.return_value = [
            ProdutoDTO(
                codigo="00010",
                descricao="FONE PMCELL",
                quantidade=None,  # Campo faltando
                valor_unitario=Decimal("3.50"),
                valor_total=Decimal("105.00")
            )
        ]

        # Act
        response = use_case.execute(valid_request_dto)

        # Assert
        assert response.success is False
        assert "produto" in response.error_message.lower()
        assert len(response.validation_errors) > 0

    # ==================== TESTE 4: VALIDAÇÃO MATEMÁTICA ====================
    def test_criar_pedido_validates_mathematical_consistency(
        self, use_case, valid_request_dto, mock_product_extractor
    ):
        """
        Testa validação de consistência matemática dos produtos.

        Cenário:
        - Produto com erro matemático (qtd × valor_unit != valor_total)
        - ProdutoDTO com erro de validação matemática

        Resultado esperado:
        - ResponseDTO com success=False
        - Mensagem de erro sobre validação matemática
        - Erro matemático listado em validation_errors
        """
        # Arrange: Produto com erro matemático
        mock_product_extractor.extrair_produtos.return_value = [
            ProdutoDTO(
                codigo="00010",
                descricao="FONE PMCELL",
                quantidade=30,
                valor_unitario=Decimal("3.50"),
                valor_total=Decimal("999.99")  # Erro matemático
            )
        ]

        # Act
        response = use_case.execute(valid_request_dto)

        # Assert
        assert response.success is False
        assert "produto" in response.error_message.lower()
        assert any("validacao_matematica" in str(erro) for erro in response.validation_errors)

    # ==================== TESTE 5: VALIDAÇÃO DE EMBALAGEM ====================
    def test_criar_pedido_validates_embalagem_rules(
        self, use_case, mock_pedido_repository, mock_pdf_parser,
        mock_header_extractor, mock_product_extractor
    ):
        """
        Testa validação de regras de embalagem.

        Cenário:
        - Logística CORREIOS com embalagem SACOLA (inválido)
        - Regra de negócio: CORREIOS aceita apenas CAIXA

        Resultado esperado:
        - ResponseDTO com success=False
        - Mensagem de erro sobre embalagem incompatível
        """
        # Arrange: Request com embalagem inválida para CORREIOS
        request_dto = CriarPedidoRequestDTO(
            pdf_path="/path/to/orcamento.pdf",
            logistica=Logistica.CORREIOS,
            embalagem=Embalagem.SACOLA,  # Inválido para CORREIOS
            usuario_criador_id=1
        )

        # Act
        response = use_case.execute(request_dto)

        # Assert
        assert response.success is False
        assert "negócio" in response.error_message.lower() or "regras" in response.error_message.lower()

    # ==================== TESTE 6: TRATAMENTO DE ERROS DE PDF ====================
    def test_criar_pedido_handles_pdf_extraction_errors(
        self, use_case, valid_request_dto, mock_pdf_parser
    ):
        """
        Testa tratamento de erros durante extração do PDF.

        Cenário:
        - PDF corrompido ou inacessível
        - PDFParser lança exceção

        Resultado esperado:
        - ResponseDTO com success=False
        - Mensagem de erro sobre falha na extração
        - Exceção capturada e tratada (não propaga)
        """
        # Arrange: Parser lança exceção
        mock_pdf_parser.extrair_texto.side_effect = Exception("Arquivo não encontrado")

        # Act
        response = use_case.execute(valid_request_dto)

        # Assert
        assert response.success is False
        assert "extração" in response.error_message.lower() or "pdf" in response.error_message.lower()

    # ==================== TESTE 7: PERSISTÊNCIA CORRETA ====================
    def test_criar_pedido_persists_correctly(
        self, use_case, valid_request_dto, mock_pedido_repository
    ):
        """
        Testa que pedido é persistido corretamente no repositório.

        Cenário:
        - PDF válido, todas validações passam
        - Repositório deve receber entidade Pedido correta

        Resultado esperado:
        - Repositório.save() chamado com Pedido
        - Pedido contém todos os dados do PDF
        - Pedido contém todos os itens extraídos
        """
        # Act
        response = use_case.execute(valid_request_dto)

        # Assert
        assert response.success is True
        mock_pedido_repository.save.assert_called_once()

        # Verificar que o argumento passado é um Pedido
        call_args = mock_pedido_repository.save.call_args
        pedido_salvo = call_args[0][0]

        assert isinstance(pedido_salvo, Pedido)
        assert pedido_salvo.numero_orcamento == "30567"
        assert len(pedido_salvo.itens) == 2
        assert all(isinstance(item, ItemPedido) for item in pedido_salvo.itens)

    # ==================== TESTE 8: CRONÔMETRO INICIADO ====================
    def test_criar_pedido_inicia_cronometro(
        self, use_case, valid_request_dto
    ):
        """
        Testa que cronômetro do pedido é iniciado automaticamente.

        Cenário:
        - Pedido criado com sucesso
        - Cronômetro deve ser iniciado (data_inicio preenchido)

        Resultado esperado:
        - Pedido.data_inicio não é None
        - Pedido.tempo_decorrido_minutos >= 0
        """
        # Act
        response = use_case.execute(valid_request_dto)

        # Assert
        assert response.success is True
        assert response.pedido.data_inicio is not None
        assert response.pedido.tempo_decorrido_minutos() >= 0
