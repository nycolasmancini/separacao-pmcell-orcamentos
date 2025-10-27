# -*- coding: utf-8 -*-
"""
Testes unitários para as entidades Pedido e ItemPedido.

Fase 13: Criar Entidade Pedido
TDD: RED → GREEN → REFACTOR

Author: PMCELL
Date: 2025-01-25
"""

import pytest
from datetime import datetime, timedelta
from decimal import Decimal

from core.domain.pedido.entities import Pedido, ItemPedido, ValidationError
from core.domain.pedido.value_objects import Logistica, Embalagem, StatusPedido
from core.domain.produto.entities import Produto


# ==================== FIXTURES ====================

@pytest.fixture
def produto_exemplo():
    """Cria um produto de exemplo para testes."""
    return Produto(
        codigo="00010",
        descricao="FONE PMCELL",
        quantidade=30,
        valor_unitario=Decimal("3.50"),
        valor_total=Decimal("105.00")
    )


@pytest.fixture
def item_pedido_exemplo(produto_exemplo):
    """Cria um item de pedido de exemplo."""
    return ItemPedido(
        produto=produto_exemplo,
        quantidade_solicitada=30
    )


@pytest.fixture
def pedido_exemplo(item_pedido_exemplo):
    """Cria um pedido de exemplo."""
    pedido = Pedido(
        numero_orcamento="30567",
        codigo_cliente="12345",
        nome_cliente="Rosana de Cassia Sinezio",
        vendedor="Nycolas",
        data="24/10/2025",
        logistica=Logistica.CORREIOS,
        embalagem=Embalagem.CAIXA
    )
    pedido.adicionar_item(item_pedido_exemplo)
    return pedido


# ==================== TESTES ITEMPED IDO ====================

def test_item_pedido_creation(produto_exemplo):
    """
    Teste 1: Testa criação básica de ItemPedido.

    Verifica se um ItemPedido é criado corretamente com valores padrão.
    """
    item = ItemPedido(
        produto=produto_exemplo,
        quantidade_solicitada=10
    )

    assert item.produto == produto_exemplo
    assert item.quantidade_solicitada == 10
    assert item.quantidade_separada == 0
    assert item.separado is False
    assert item.separado_por is None
    assert item.separado_em is None


def test_item_pedido_validacao_quantidade_negativa(produto_exemplo):
    """
    Teste 2: Testa validação de quantidade solicitada negativa.

    Deve lançar ValidationError se quantidade_solicitada <= 0.
    """
    with pytest.raises(ValidationError, match="Quantidade solicitada deve ser maior que zero"):
        ItemPedido(
            produto=produto_exemplo,
            quantidade_solicitada=0
        )

    with pytest.raises(ValidationError, match="Quantidade solicitada deve ser maior que zero"):
        ItemPedido(
            produto=produto_exemplo,
            quantidade_solicitada=-5
        )


def test_item_pedido_marcar_separado(item_pedido_exemplo):
    """
    Teste 3: Testa marcação de item como separado.

    Verifica se o método marcar_separado() atualiza corretamente os campos.
    """
    usuario = "João Silva"
    antes = datetime.now()

    item_pedido_exemplo.marcar_separado(usuario)

    assert item_pedido_exemplo.separado is True
    assert item_pedido_exemplo.quantidade_separada == item_pedido_exemplo.quantidade_solicitada
    assert item_pedido_exemplo.separado_por == usuario
    assert item_pedido_exemplo.separado_em is not None
    assert item_pedido_exemplo.separado_em >= antes


def test_item_pedido_esta_completo(produto_exemplo):
    """
    Teste 4: Testa método esta_completo().

    Verifica se o método retorna True quando quantidade_separada == quantidade_solicitada.
    """
    item = ItemPedido(
        produto=produto_exemplo,
        quantidade_solicitada=10
    )

    # Inicialmente não está completo
    assert item.esta_completo() is False

    # Após marcar como separado, está completo
    item.marcar_separado("Teste")
    assert item.esta_completo() is True


# ==================== TESTES PEDIDO ====================

def test_pedido_creation():
    """
    Teste 5: Testa criação básica de Pedido.

    Verifica se um Pedido é criado corretamente com valores padrão.
    """
    pedido = Pedido(
        numero_orcamento="30567",
        codigo_cliente="12345",
        nome_cliente="Rosana de Cassia Sinezio",
        vendedor="Nycolas",
        data="24/10/2025",
        logistica=Logistica.CORREIOS,
        embalagem=Embalagem.CAIXA
    )

    assert pedido.numero_orcamento == "30567"
    assert pedido.codigo_cliente == "12345"
    assert pedido.nome_cliente == "Rosana de Cassia Sinezio"
    assert pedido.vendedor == "Nycolas"
    assert pedido.data == "24/10/2025"
    assert pedido.logistica == Logistica.CORREIOS
    assert pedido.embalagem == Embalagem.CAIXA
    assert pedido.status == StatusPedido.EM_SEPARACAO
    assert len(pedido.itens) == 0
    assert pedido.criado_em is not None
    assert pedido.data_inicio is not None


def test_pedido_adicionar_item(pedido_exemplo, produto_exemplo):
    """
    Teste 6: Testa adição de item ao pedido.

    Verifica se o método adicionar_item() funciona corretamente.
    """
    novo_item = ItemPedido(
        produto=produto_exemplo,
        quantidade_solicitada=20
    )

    quantidade_inicial = len(pedido_exemplo.itens)
    pedido_exemplo.adicionar_item(novo_item)

    assert len(pedido_exemplo.itens) == quantidade_inicial + 1
    assert novo_item in pedido_exemplo.itens


def test_pedido_calcular_progresso(produto_exemplo):
    """
    Teste 7: Testa cálculo de progresso do pedido.

    Verifica se o progresso é calculado corretamente (0%, 33%, 66%, 100%).
    """
    pedido = Pedido(
        numero_orcamento="30568",
        codigo_cliente="12345",
        nome_cliente="Teste Cliente",
        vendedor="Teste Vendedor",
        data="24/10/2025",
        logistica=Logistica.RETIRA_LOJA,
        embalagem=Embalagem.SACOLA
    )

    # Adicionar 3 itens
    for i in range(3):
        item = ItemPedido(
            produto=produto_exemplo,
            quantidade_solicitada=10
        )
        pedido.adicionar_item(item)

    # Progresso inicial: 0%
    assert pedido.calcular_progresso() == 0

    # Separar 1 item: 33%
    pedido.itens[0].marcar_separado("Teste")
    assert pedido.calcular_progresso() == 33

    # Separar 2 itens: 66%
    pedido.itens[1].marcar_separado("Teste")
    assert pedido.calcular_progresso() == 66

    # Separar 3 itens: 100%
    pedido.itens[2].marcar_separado("Teste")
    assert pedido.calcular_progresso() == 100


def test_pedido_validacao_embalagem_correios():
    """
    Teste 8: Testa validação de embalagem para logística CORREIOS.

    CORREIOS, MELHOR_ENVIO e ONIBUS devem aceitar apenas CAIXA.
    """
    # CORREIOS com CAIXA: válido
    pedido_valido = Pedido(
        numero_orcamento="30569",
        codigo_cliente="12345",
        nome_cliente="Teste",
        vendedor="Teste",
        data="24/10/2025",
        logistica=Logistica.CORREIOS,
        embalagem=Embalagem.CAIXA
    )
    assert pedido_valido is not None

    # CORREIOS com SACOLA: inválido
    with pytest.raises(ValidationError, match="aceita apenas embalagem CAIXA"):
        Pedido(
            numero_orcamento="30570",
            codigo_cliente="12345",
            nome_cliente="Teste",
            vendedor="Teste",
            data="24/10/2025",
            logistica=Logistica.CORREIOS,
            embalagem=Embalagem.SACOLA
        )


def test_pedido_validacao_embalagem_melhor_envio():
    """
    Teste 9: Testa validação de embalagem para logística MELHOR_ENVIO.

    MELHOR_ENVIO deve aceitar apenas CAIXA.
    """
    # MELHOR_ENVIO com SACOLA: inválido
    with pytest.raises(ValidationError, match="aceita apenas embalagem CAIXA"):
        Pedido(
            numero_orcamento="30571",
            codigo_cliente="12345",
            nome_cliente="Teste",
            vendedor="Teste",
            data="24/10/2025",
            logistica=Logistica.MELHOR_ENVIO,
            embalagem=Embalagem.SACOLA
        )


def test_pedido_validacao_embalagem_onibus():
    """
    Teste 10: Testa validação de embalagem para logística ÔNIBUS.

    ÔNIBUS deve aceitar apenas CAIXA.
    """
    # ÔNIBUS com SACOLA: inválido
    with pytest.raises(ValidationError, match="aceita apenas embalagem CAIXA"):
        Pedido(
            numero_orcamento="30572",
            codigo_cliente="12345",
            nome_cliente="Teste",
            vendedor="Teste",
            data="24/10/2025",
            logistica=Logistica.ONIBUS,
            embalagem=Embalagem.SACOLA
        )


def test_pedido_pode_finalizar(produto_exemplo):
    """
    Teste 11: Testa método pode_finalizar().

    Pedido só pode ser finalizado quando progresso == 100%.
    """
    pedido = Pedido(
        numero_orcamento="30573",
        codigo_cliente="12345",
        nome_cliente="Teste",
        vendedor="Teste",
        data="24/10/2025",
        logistica=Logistica.MOTOBOY,
        embalagem=Embalagem.SACOLA
    )

    item = ItemPedido(produto=produto_exemplo, quantidade_solicitada=10)
    pedido.adicionar_item(item)

    # Inicialmente não pode finalizar
    assert pedido.pode_finalizar() is False

    # Após separar o item, pode finalizar
    item.marcar_separado("Teste")
    assert pedido.pode_finalizar() is True


def test_pedido_finalizar(produto_exemplo):
    """
    Teste 12: Testa método finalizar().

    Verifica se o pedido é finalizado corretamente quando progresso == 100%.
    """
    pedido = Pedido(
        numero_orcamento="30574",
        codigo_cliente="12345",
        nome_cliente="Teste",
        vendedor="Teste",
        data="24/10/2025",
        logistica=Logistica.RETIRA_LOJA,
        embalagem=Embalagem.CAIXA
    )

    item = ItemPedido(produto=produto_exemplo, quantidade_solicitada=10)
    pedido.adicionar_item(item)
    item.marcar_separado("Teste")

    # Finalizar pedido
    usuario = "João Silva"
    antes = datetime.now()
    pedido.finalizar(usuario)

    assert pedido.status == StatusPedido.FINALIZADO
    assert pedido.data_finalizacao is not None
    assert pedido.data_finalizacao >= antes


def test_pedido_tempo_decorrido(produto_exemplo):
    """
    Teste 13: Testa cálculo de tempo decorrido.

    Verifica se o tempo em minutos é calculado corretamente.
    """
    pedido = Pedido(
        numero_orcamento="30575",
        codigo_cliente="12345",
        nome_cliente="Teste",
        vendedor="Teste",
        data="24/10/2025",
        logistica=Logistica.MOTOBOY,
        embalagem=Embalagem.CAIXA
    )

    # Simular pedido criado há 45 minutos
    pedido.data_inicio = datetime.now() - timedelta(minutes=45)

    tempo = pedido.tempo_decorrido_minutos()

    # Tolerância de 1 minuto para execução do teste
    assert 44 <= tempo <= 46


def test_pedido_retira_loja_aceita_sacola():
    """
    Teste 14: Testa que RETIRA_LOJA aceita SACOLA.

    RETIRA_LOJA e MOTOBOY devem aceitar CAIXA ou SACOLA.
    """
    pedido = Pedido(
        numero_orcamento="30576",
        codigo_cliente="12345",
        nome_cliente="Teste",
        vendedor="Teste",
        data="24/10/2025",
        logistica=Logistica.RETIRA_LOJA,
        embalagem=Embalagem.SACOLA
    )
    assert pedido.embalagem == Embalagem.SACOLA


def test_pedido_motoboy_aceita_sacola():
    """
    Teste 15: Testa que MOTOBOY aceita SACOLA.

    MOTOBOY deve aceitar CAIXA ou SACOLA.
    """
    pedido = Pedido(
        numero_orcamento="30577",
        codigo_cliente="12345",
        nome_cliente="Teste",
        vendedor="Teste",
        data="24/10/2025",
        logistica=Logistica.MOTOBOY,
        embalagem=Embalagem.SACOLA
    )
    assert pedido.embalagem == Embalagem.SACOLA
