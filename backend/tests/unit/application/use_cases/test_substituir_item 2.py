# -*- coding: utf-8 -*-
"""
Testes unitários para SubstituirItemUseCase (Fase 24).
"""
import pytest
from datetime import datetime
from core.application.use_cases.substituir_item import SubstituirItemUseCase
from core.domain.pedido.entities import Pedido, ItemPedido, StatusPedido
from core.domain.usuario.entities import Usuario, TipoUsuario


@pytest.fixture
def separador():
    """Fixture: usuário separador."""
    return Usuario(
        numero_login=1001,
        nome="João Separador",
        tipo=TipoUsuario.SEPARADOR
    )


@pytest.fixture
def pedido_com_itens():
    """Fixture: pedido com 3 itens."""
    pedido = Pedido(
        numero_orcamento=30567,
        nome_cliente="Rosana",
        status=StatusPedido.EM_SEPARACAO,
        criado_em=datetime.now()
    )

    # Criar 3 itens
    item1 = ItemPedido(
        pedido=pedido,
        produto="CABO USB-C",
        quantidade=10,
        separado=False
    )
    item2 = ItemPedido(
        pedido=pedido,
        produto="PELÍCULA 3D IP14",
        quantidade=20,
        separado=False
    )
    item3 = ItemPedido(
        pedido=pedido,
        produto="SUPORTE VEICULAR",
        quantidade=5,
        separado=False
    )

    pedido.itens = [item1, item2, item3]
    return pedido


class TestSubstituirItemUseCase:
    """Testes para SubstituirItemUseCase."""

    def test_substituir_item_com_sucesso(self, pedido_com_itens, separador):
        """Testa substituição bem-sucedida de item."""
        use_case = SubstituirItemUseCase()
        item = pedido_com_itens.itens[0]

        result = use_case.execute(
            item_id=item.id,
            produto_substituto="CABO USB-C 2.0 TURBO",
            usuario=separador
        )

        assert result.success is True
        assert item.substituido is True
        assert item.produto_substituto == "CABO USB-C 2.0 TURBO"
        assert item.separado is True  # Item deve ser marcado como separado
        assert item.separado_por == separador
        assert item.separado_em is not None

    def test_substituir_item_marca_como_separado_automaticamente(self, pedido_com_itens, separador):
        """Testa que substituir também marca como separado."""
        use_case = SubstituirItemUseCase()
        item = pedido_com_itens.itens[0]

        # Item ainda não foi separado
        assert item.separado is False

        use_case.execute(
            item_id=item.id,
            produto_substituto="CABO USB TIPO C",
            usuario=separador
        )

        # Após substituição, deve estar separado
        assert item.separado is True
        assert item.substituido is True

    def test_substituir_item_atualiza_progresso_pedido(self, pedido_com_itens, separador):
        """Testa que substituir atualiza o progresso do pedido."""
        use_case = SubstituirItemUseCase()

        # Progresso inicial: 0%
        assert pedido_com_itens.calcular_progresso() == 0

        # Substituir primeiro item
        use_case.execute(
            item_id=pedido_com_itens.itens[0].id,
            produto_substituto="CABO NOVO",
            usuario=separador
        )

        # Progresso: 1/3 = 33.33%
        assert pedido_com_itens.calcular_progresso() == pytest.approx(33.33, rel=0.01)

    def test_substituir_item_sem_produto_substituto_falha(self, pedido_com_itens, separador):
        """Testa que substituir sem informar produto falha."""
        use_case = SubstituirItemUseCase()
        item = pedido_com_itens.itens[0]

        result = use_case.execute(
            item_id=item.id,
            produto_substituto="",  # Vazio
            usuario=separador
        )

        assert result.success is False
        assert "produto substituto deve ser informado" in result.message.lower()

    def test_substituir_item_ja_separado(self, pedido_com_itens, separador):
        """Testa substituir item que já foi separado."""
        use_case = SubstituirItemUseCase()
        item = pedido_com_itens.itens[0]

        # Primeiro: marcar como separado normalmente
        item.marcar_separado(separador)

        # Depois: tentar substituir
        result = use_case.execute(
            item_id=item.id,
            produto_substituto="CABO NOVO",
            usuario=separador
        )

        # Deve permitir (pode querer registrar substituição mesmo após separar)
        assert result.success is True
        assert item.substituido is True

    def test_substituir_item_ja_substituido_sobrescreve(self, pedido_com_itens, separador):
        """Testa substituir item que já foi substituído (sobrescreve)."""
        use_case = SubstituirItemUseCase()
        item = pedido_com_itens.itens[0]

        # Primeira substituição
        use_case.execute(
            item_id=item.id,
            produto_substituto="CABO USB-C 1.0",
            usuario=separador
        )

        assert item.produto_substituto == "CABO USB-C 1.0"

        # Segunda substituição (corrigir)
        use_case.execute(
            item_id=item.id,
            produto_substituto="CABO USB-C 2.0",
            usuario=separador
        )

        # Deve sobrescrever
        assert item.produto_substituto == "CABO USB-C 2.0"

    def test_substituir_item_nao_conta_para_compra(self, pedido_com_itens, separador):
        """Testa que item substituído não está em compra."""
        use_case = SubstituirItemUseCase()
        item = pedido_com_itens.itens[0]

        # Substituir item
        use_case.execute(
            item_id=item.id,
            produto_substituto="CABO NOVO",
            usuario=separador
        )

        # Item NÃO deve estar em compra
        assert item.em_compra is False
        assert item.substituido is True
        assert item.separado is True

    def test_substituir_item_registra_dados_separador(self, pedido_com_itens, separador):
        """Testa que substituir registra quem fez e quando."""
        use_case = SubstituirItemUseCase()
        item = pedido_com_itens.itens[0]

        antes = datetime.now()

        use_case.execute(
            item_id=item.id,
            produto_substituto="CABO NOVO",
            usuario=separador
        )

        depois = datetime.now()

        assert item.separado_por == separador
        assert item.separado_em >= antes
        assert item.separado_em <= depois
