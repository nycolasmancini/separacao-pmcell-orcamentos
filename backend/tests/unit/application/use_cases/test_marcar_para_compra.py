# -*- coding: utf-8 -*-
"""
Testes para MarcarParaCompraUseCase (Fase 23).

TDD - Fase RED: Testes escritos ANTES da implementação.
"""

import pytest
from datetime import datetime
from unittest.mock import Mock, MagicMock
from decimal import Decimal

from core.application.use_cases.marcar_para_compra import MarcarParaCompraUseCase
from core.application.dtos.marcar_para_compra_dtos import (
    MarcarParaCompraRequestDTO,
    MarcarParaCompraResponseDTO
)
from core.domain.pedido.entities import Pedido, ItemPedido, ValidationError
from core.domain.produto.entities import Produto
from core.domain.pedido.value_objects import Logistica, Embalagem, StatusPedido


@pytest.fixture
def mock_pedido_repository():
    """Mock do repositório de pedidos."""
    return Mock()


@pytest.fixture
def mock_usuario_repository():
    """Mock do repositório de usuários."""
    return Mock()


@pytest.fixture
def produto_mock():
    """Produto mock para testes."""
    return Produto(
        id=1,
        codigo="12345",
        descricao="Capinha iPhone 13",
        quantidade=1,
        valor_unitario=Decimal("59.90"),
        valor_total=Decimal("59.90")
    )


@pytest.fixture
def pedido_com_itens(produto_mock):
    """Pedido com 3 itens não separados."""
    item1 = ItemPedido(
        id=1,
        produto=produto_mock,
        quantidade_solicitada=2,
        quantidade_separada=0,
        separado=False,
        em_compra=False
    )
    item2 = ItemPedido(
        id=2,
        produto=produto_mock,
        quantidade_solicitada=1,
        quantidade_separada=0,
        separado=False,
        em_compra=False
    )
    item3 = ItemPedido(
        id=3,
        produto=produto_mock,
        quantidade_solicitada=3,
        quantidade_separada=0,
        separado=False,
        em_compra=False
    )

    pedido = Pedido(
        id=100,
        numero_orcamento="30567",
        codigo_cliente="CLI001",
        nome_cliente="Rosana",
        vendedor="João Silva",
        data="27/10/2025",
        logistica=Logistica.CORREIOS,
        embalagem=Embalagem.CAIXA,
        status=StatusPedido.EM_SEPARACAO,
        observacoes="Teste",
        itens=[item1, item2, item3]
    )

    return pedido


@pytest.fixture
def usuario_mock():
    """Usuário mock."""
    usuario = Mock()
    usuario.id = 42
    usuario.nome = "Maria Silva"
    return usuario


class TestMarcarParaCompraUseCase:
    """Testes para o caso de uso MarcarParaCompraUseCase."""

    def test_marcar_item_para_compra_com_sucesso(
        self,
        mock_pedido_repository,
        mock_usuario_repository,
        pedido_com_itens,
        usuario_mock
    ):
        """
        Testa marcação bem-sucedida de item para compra.

        Given: Um pedido com itens não separados
        When: Usuário marca um item para compra
        Then: Item é marcado com em_compra=True e dados do usuário
        """
        # Arrange
        mock_pedido_repository.get_by_id.return_value = pedido_com_itens
        mock_usuario_repository.get_by_id.return_value = usuario_mock

        use_case = MarcarParaCompraUseCase(
            pedido_repository=mock_pedido_repository,
            usuario_repository=mock_usuario_repository
        )

        request = MarcarParaCompraRequestDTO(
            pedido_id=100,
            item_id=1,
            usuario_id=42
        )

        # Act
        response = use_case.execute(request)

        # Assert
        assert response.success is True
        assert response.item_id == 1
        assert response.em_compra is True
        assert response.enviado_para_compra_por == "Maria Silva"
        assert response.enviado_para_compra_em is not None
        assert isinstance(response.enviado_para_compra_em, datetime)

        # Verifica que o repositório salvou o pedido
        mock_pedido_repository.save.assert_called_once_with(pedido_com_itens)

    def test_marcar_item_inexistente(
        self,
        mock_pedido_repository,
        mock_usuario_repository,
        pedido_com_itens,
        usuario_mock
    ):
        """
        Testa erro ao tentar marcar item que não existe.

        Given: Um pedido válido
        When: Tentativa de marcar item com ID inexistente
        Then: Retorna erro "Item não encontrado no pedido"
        """
        # Arrange
        mock_pedido_repository.get_by_id.return_value = pedido_com_itens
        mock_usuario_repository.get_by_id.return_value = usuario_mock

        use_case = MarcarParaCompraUseCase(
            pedido_repository=mock_pedido_repository,
            usuario_repository=mock_usuario_repository
        )

        request = MarcarParaCompraRequestDTO(
            pedido_id=100,
            item_id=999,  # ID inexistente
            usuario_id=42
        )

        # Act
        response = use_case.execute(request)

        # Assert
        assert response.success is False
        assert "Item não encontrado no pedido" in response.erro
        assert response.item_id == 999

        # Não deve salvar nada
        mock_pedido_repository.save.assert_not_called()

    def test_marcar_item_ja_em_compra(
        self,
        mock_pedido_repository,
        mock_usuario_repository,
        pedido_com_itens,
        usuario_mock
    ):
        """
        Testa erro ao tentar marcar item que já está em compra.

        Given: Um item já marcado como em_compra
        When: Tentativa de marcar novamente
        Then: Retorna erro "Item já está marcado para compra"
        """
        # Arrange
        pedido_com_itens.itens[0].em_compra = True
        pedido_com_itens.itens[0].enviado_para_compra_por = "João"

        mock_pedido_repository.get_by_id.return_value = pedido_com_itens
        mock_usuario_repository.get_by_id.return_value = usuario_mock

        use_case = MarcarParaCompraUseCase(
            pedido_repository=mock_pedido_repository,
            usuario_repository=mock_usuario_repository
        )

        request = MarcarParaCompraRequestDTO(
            pedido_id=100,
            item_id=1,
            usuario_id=42
        )

        # Act
        response = use_case.execute(request)

        # Assert
        assert response.success is False
        assert "já está marcado para compra" in response.erro

        # Não deve salvar
        mock_pedido_repository.save.assert_not_called()

    def test_marcar_item_ja_separado_deveria_falhar(
        self,
        mock_pedido_repository,
        mock_usuario_repository,
        pedido_com_itens,
        usuario_mock
    ):
        """
        Testa erro ao tentar marcar item que já foi separado.

        Given: Um item já marcado como separado
        When: Tentativa de marcar para compra
        Then: Retorna erro "Item já foi separado"
        """
        # Arrange
        pedido_com_itens.itens[0].separado = True
        pedido_com_itens.itens[0].separado_por = "João"

        mock_pedido_repository.get_by_id.return_value = pedido_com_itens
        mock_usuario_repository.get_by_id.return_value = usuario_mock

        use_case = MarcarParaCompraUseCase(
            pedido_repository=mock_pedido_repository,
            usuario_repository=mock_usuario_repository
        )

        request = MarcarParaCompraRequestDTO(
            pedido_id=100,
            item_id=1,
            usuario_id=42
        )

        # Act
        response = use_case.execute(request)

        # Assert
        assert response.success is False
        assert "Item já foi separado" in response.erro

        # Não deve salvar
        mock_pedido_repository.save.assert_not_called()

    def test_usuario_e_timestamp_registrados(
        self,
        mock_pedido_repository,
        mock_usuario_repository,
        pedido_com_itens,
        usuario_mock
    ):
        """
        Testa que o usuário e timestamp são registrados corretamente.

        Given: Um item válido para compra
        When: Item é marcado para compra
        Then: Nome do usuário e timestamp são salvos
        """
        # Arrange
        mock_pedido_repository.get_by_id.return_value = pedido_com_itens
        mock_usuario_repository.get_by_id.return_value = usuario_mock

        use_case = MarcarParaCompraUseCase(
            pedido_repository=mock_pedido_repository,
            usuario_repository=mock_usuario_repository
        )

        request = MarcarParaCompraRequestDTO(
            pedido_id=100,
            item_id=1,
            usuario_id=42
        )

        # Act
        before = datetime.now()
        response = use_case.execute(request)
        after = datetime.now()

        # Assert
        assert response.success is True
        assert response.enviado_para_compra_por == "Maria Silva"
        assert response.enviado_para_compra_em >= before
        assert response.enviado_para_compra_em <= after

        # Verifica que o item do domínio foi atualizado
        item = pedido_com_itens.itens[0]
        assert item.em_compra is True
        assert item.enviado_para_compra_por == "Maria Silva"
        assert item.enviado_para_compra_em is not None

    def test_item_em_compra_nao_conta_como_separado(
        self,
        mock_pedido_repository,
        mock_usuario_repository,
        pedido_com_itens,
        usuario_mock
    ):
        """
        Testa que item marcado para compra NÃO conta como separado.

        Given: Um pedido com progresso 0%
        When: Item é marcado para compra
        Then: Item tem em_compra=True mas separado=False
        """
        # Arrange
        mock_pedido_repository.get_by_id.return_value = pedido_com_itens
        mock_usuario_repository.get_by_id.return_value = usuario_mock

        use_case = MarcarParaCompraUseCase(
            pedido_repository=mock_pedido_repository,
            usuario_repository=mock_usuario_repository
        )

        request = MarcarParaCompraRequestDTO(
            pedido_id=100,
            item_id=1,
            usuario_id=42
        )

        # Act
        response = use_case.execute(request)

        # Assert
        assert response.success is True
        assert response.em_compra is True

        # Verifica que o item NÃO está separado
        item = pedido_com_itens.itens[0]
        assert item.em_compra is True
        assert item.separado is False
        assert item.quantidade_separada == 0

    def test_progresso_nao_muda_ao_marcar_para_compra(
        self,
        mock_pedido_repository,
        mock_usuario_repository,
        pedido_com_itens,
        usuario_mock
    ):
        """
        Testa que o progresso do pedido não muda ao marcar item para compra.

        Given: Um pedido com progresso inicial X%
        When: Item é marcado para compra
        Then: Progresso continua X%
        """
        # Arrange
        # Marca 1 item como separado (33% de progresso)
        pedido_com_itens.itens[0].separado = True
        pedido_com_itens.itens[0].quantidade_separada = 2

        progresso_inicial = pedido_com_itens.calcular_progresso()
        assert progresso_inicial == 33  # 1 de 3 itens

        mock_pedido_repository.get_by_id.return_value = pedido_com_itens
        mock_usuario_repository.get_by_id.return_value = usuario_mock

        use_case = MarcarParaCompraUseCase(
            pedido_repository=mock_pedido_repository,
            usuario_repository=mock_usuario_repository
        )

        request = MarcarParaCompraRequestDTO(
            pedido_id=100,
            item_id=2,  # Marca segundo item para compra
            usuario_id=42
        )

        # Act
        response = use_case.execute(request)

        # Assert
        assert response.success is True

        # Progresso deve continuar 33%
        progresso_final = pedido_com_itens.calcular_progresso()
        assert progresso_final == 33

    def test_validacao_pedido_inexistente(
        self,
        mock_pedido_repository,
        mock_usuario_repository,
        usuario_mock
    ):
        """
        Testa erro ao tentar marcar item de pedido inexistente.

        Given: ID de pedido inexistente
        When: Tentativa de marcar item
        Then: Retorna erro "Pedido não encontrado"
        """
        # Arrange
        mock_pedido_repository.get_by_id.return_value = None
        mock_usuario_repository.get_by_id.return_value = usuario_mock

        use_case = MarcarParaCompraUseCase(
            pedido_repository=mock_pedido_repository,
            usuario_repository=mock_usuario_repository
        )

        request = MarcarParaCompraRequestDTO(
            pedido_id=999,  # Pedido inexistente
            item_id=1,
            usuario_id=42
        )

        # Act
        response = use_case.execute(request)

        # Assert
        assert response.success is False
        assert "Pedido não encontrado" in response.erro

        # Não deve salvar
        mock_pedido_repository.save.assert_not_called()
