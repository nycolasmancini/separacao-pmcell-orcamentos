# -*- coding: utf-8 -*-
"""
Testes para SepararItemUseCase (Fase 22).

TDD - Fase RED: Testes escritos ANTES da implementação.
"""

import pytest
from datetime import datetime
from unittest.mock import Mock, MagicMock

from core.application.use_cases.separar_item import SepararItemUseCase
from core.application.dtos.separar_item_dtos import (
    SepararItemRequestDTO,
    SepararItemResponseDTO
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
    from decimal import Decimal
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
        separado=False
    )
    item2 = ItemPedido(
        id=2,
        produto=produto_mock,
        quantidade_solicitada=1,
        quantidade_separada=0,
        separado=False
    )
    item3 = ItemPedido(
        id=3,
        produto=produto_mock,
        quantidade_solicitada=3,
        quantidade_separada=0,
        separado=False
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
        itens=[item1, item2, item3]
    )

    return pedido


@pytest.fixture
def usuario_mock():
    """Mock de usuário separador."""
    usuario = Mock()
    usuario.id = 42
    usuario.nome = "Carlos Separador"
    return usuario


# ==================== TESTES USE CASE ====================

def test_separar_item_com_sucesso(
    mock_pedido_repository,
    mock_usuario_repository,
    pedido_com_itens,
    usuario_mock
):
    """
    Teste 1: Marcar item como separado com sucesso.

    Verifica que o use case:
    - Busca o pedido corretamente
    - Busca o usuário corretamente
    - Marca o item como separado
    - Persiste as alterações
    - Retorna sucesso
    """
    # Arrange
    mock_pedido_repository.get_by_id.return_value = pedido_com_itens
    mock_usuario_repository.get_by_id.return_value = usuario_mock

    use_case = SepararItemUseCase(mock_pedido_repository, mock_usuario_repository)

    request = SepararItemRequestDTO(
        pedido_id=100,
        item_id=1,
        usuario_id=42
    )

    # Act
    response = use_case.execute(request)

    # Assert
    assert response.success is True
    assert response.message == "Item marcado como separado com sucesso"
    assert mock_pedido_repository.get_by_id.called_with(100)
    assert mock_usuario_repository.get_by_id.called_with(42)

    # Verifica que o item foi marcado
    item = pedido_com_itens.itens[0]
    assert item.separado is True
    assert item.separado_por == "Carlos Separador"
    assert item.separado_em is not None


def test_separar_item_atualiza_usuario_e_timestamp(
    mock_pedido_repository,
    mock_usuario_repository,
    pedido_com_itens,
    usuario_mock
):
    """
    Teste 2: Verifica que usuário e timestamp são registrados.

    Garante rastreabilidade de quem separou e quando.
    """
    # Arrange
    mock_pedido_repository.get_by_id.return_value = pedido_com_itens
    mock_usuario_repository.get_by_id.return_value = usuario_mock

    use_case = SepararItemUseCase(mock_pedido_repository, mock_usuario_repository)
    request = SepararItemRequestDTO(pedido_id=100, item_id=1, usuario_id=42)

    # Capturar timestamp antes da execução
    antes = datetime.now()

    # Act
    response = use_case.execute(request)

    # Capturar timestamp depois da execução
    depois = datetime.now()

    # Assert
    item = pedido_com_itens.itens[0]
    assert item.separado_por == usuario_mock.nome
    assert item.separado_em >= antes
    assert item.separado_em <= depois
    assert item.quantidade_separada == item.quantidade_solicitada


def test_separar_item_atualiza_progresso_pedido(
    mock_pedido_repository,
    mock_usuario_repository,
    pedido_com_itens,
    usuario_mock
):
    """
    Teste 3: Verifica que o progresso do pedido é atualizado.

    Pedido com 3 itens: separar 1 item = 33% de progresso.
    """
    # Arrange
    mock_pedido_repository.get_by_id.return_value = pedido_com_itens
    mock_usuario_repository.get_by_id.return_value = usuario_mock

    use_case = SepararItemUseCase(mock_pedido_repository, mock_usuario_repository)
    request = SepararItemRequestDTO(pedido_id=100, item_id=1, usuario_id=42)

    # Progresso inicial deve ser 0%
    assert pedido_com_itens.calcular_progresso() == 0

    # Act
    response = use_case.execute(request)

    # Assert
    # 1 item separado de 3 = 33%
    assert pedido_com_itens.calcular_progresso() == 33
    assert response.progresso_percentual == 33


def test_separar_item_ja_separado_levanta_erro(
    mock_pedido_repository,
    mock_usuario_repository,
    pedido_com_itens,
    usuario_mock
):
    """
    Teste 4: Tentar marcar item já separado levanta erro.

    Validação de negócio: não pode separar o mesmo item duas vezes.
    """
    # Arrange
    mock_pedido_repository.get_by_id.return_value = pedido_com_itens
    mock_usuario_repository.get_by_id.return_value = usuario_mock

    # Marcar item como já separado
    pedido_com_itens.itens[0].separado = True
    pedido_com_itens.itens[0].separado_por = "Outro Usuário"
    pedido_com_itens.itens[0].separado_em = datetime.now()

    use_case = SepararItemUseCase(mock_pedido_repository, mock_usuario_repository)
    request = SepararItemRequestDTO(pedido_id=100, item_id=1, usuario_id=42)

    # Act
    response = use_case.execute(request)

    # Assert
    assert response.success is False
    assert "já está marcado como separado" in response.message.lower()


def test_separar_item_inexistente_levanta_erro(
    mock_pedido_repository,
    mock_usuario_repository,
    pedido_com_itens,
    usuario_mock
):
    """
    Teste 5: Tentar separar item que não existe no pedido.

    Validação: item_id deve existir no pedido.
    """
    # Arrange
    mock_pedido_repository.get_by_id.return_value = pedido_com_itens
    mock_usuario_repository.get_by_id.return_value = usuario_mock

    use_case = SepararItemUseCase(mock_pedido_repository, mock_usuario_repository)

    # Item ID 999 não existe no pedido
    request = SepararItemRequestDTO(pedido_id=100, item_id=999, usuario_id=42)

    # Act
    response = use_case.execute(request)

    # Assert
    assert response.success is False
    assert "não encontrado" in response.message.lower()


def test_separar_item_retorna_pedido_atualizado(
    mock_pedido_repository,
    mock_usuario_repository,
    pedido_com_itens,
    usuario_mock
):
    """
    Teste 6: Verifica que a resposta contém o pedido atualizado.

    Response deve conter dados atualizados para renderização.
    """
    # Arrange
    mock_pedido_repository.get_by_id.return_value = pedido_com_itens
    mock_usuario_repository.get_by_id.return_value = usuario_mock

    use_case = SepararItemUseCase(mock_pedido_repository, mock_usuario_repository)
    request = SepararItemRequestDTO(pedido_id=100, item_id=1, usuario_id=42)

    # Act
    response = use_case.execute(request)

    # Assert
    assert response.pedido_id == 100
    assert response.item_id == 1
    assert response.progresso_percentual == 33
    assert response.itens_separados == 1
    assert response.total_itens == 3


def test_pedido_inexistente_levanta_erro(
    mock_pedido_repository,
    mock_usuario_repository,
    usuario_mock
):
    """
    Teste 7: Tentar separar item de pedido inexistente.

    Validação: pedido_id deve existir.
    """
    # Arrange
    mock_pedido_repository.get_by_id.return_value = None
    mock_usuario_repository.get_by_id.return_value = usuario_mock

    use_case = SepararItemUseCase(mock_pedido_repository, mock_usuario_repository)
    request = SepararItemRequestDTO(pedido_id=999, item_id=1, usuario_id=42)

    # Act
    response = use_case.execute(request)

    # Assert
    assert response.success is False
    assert "pedido não encontrado" in response.message.lower()


def test_usuario_inexistente_levanta_erro(
    mock_pedido_repository,
    mock_usuario_repository,
    pedido_com_itens
):
    """
    Teste 8: Tentar separar item com usuário inexistente.

    Validação: usuario_id deve existir.
    """
    # Arrange
    mock_pedido_repository.get_by_id.return_value = pedido_com_itens
    mock_usuario_repository.get_by_id.return_value = None

    use_case = SepararItemUseCase(mock_pedido_repository, mock_usuario_repository)
    request = SepararItemRequestDTO(pedido_id=100, item_id=1, usuario_id=999)

    # Act
    response = use_case.execute(request)

    # Assert
    assert response.success is False
    assert "usuário não encontrado" in response.message.lower()
